"""Prompt compression layer for GPT narration.

Builds a concise, structured context from full game state before constructing
the narration prompt. Reduces token usage and keeps narration coherent by
including only relevant elements.

Contract layers (orthogonal concerns):
- **narration_visibility** — which entities and published facts may be referenced.
- **narrative_authority** — what outcome, hidden-truth, and NPC-intent claims may be stated as
  certain (see ``build_narrative_authority_contract``); does not replace visibility rules.
- **scene_state_anchor** — mandatory grounding in present scene/speaker/action anchors.
- **answer_completeness** — direct-answer obligations, voice, and bounded-partial shape.
- **fallback_behavior** — narrow graceful-degradation policy under meaningful uncertainty pressure;
  governs bounded partials, diegetic hedging, and the single-question fallback shape.
- **tone_escalation** — caps interpersonal hostility / escalation in narration from published inputs
  (see ``build_tone_escalation_contract`` in ``game.tone_escalation``).
- **anti_railroading** — player-agency and lead-surfacing policy (inspectable flags and surfaced lead ids;
  see ``build_anti_railroading_contract`` in ``game.anti_railroading``); does not replace lead registry facts.
- **context_separation** — ambient world pressure vs. local interaction focus (see ``build_context_separation_contract``
  in ``game.context_separation``); enforcement reads the shipped contract, not prompt prose alone.
- **player_facing_narration_purity** — forbid planner/UI/engine scaffolding in narration (see
  ``build_player_facing_narration_purity_contract`` in ``game.player_facing_narration_purity``).
- **social_response_structure** — dialogue-turn spoken shape and anti-monologue caps (see
  ``build_social_response_structure_contract`` in ``game.response_policy_contracts``); gate/repairs TBD.
- **narrative_authenticity** — anti-echo between narration and spoken lines, minimum new-signal pressure on
  follow-ups, anti-filler heuristics, and diegetic integrity hints (see ``build_narrative_authenticity_contract``
  in ``game.narrative_authenticity``); gate enforcement in ``game.final_emission_repairs``.
- **interaction_continuity** — preserve conversational thread / interlocutor continuity across turns;
  do not silently drop or switch speakers without a break signal or explicit cue (see
  ``build_interaction_continuity_contract`` in ``game.interaction_continuity``); gate/repairs TBD.
- **conversational_memory_window** — bounded prior-turn selection for prompts (see
  :mod:`game.conversational_memory_window`); ``recent_log`` in the payload is derived from the selector output.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Set
import re

from game.leads import (
    effective_lead_pressure_score,
    filter_pending_leads_for_active_follow_surface,
    get_lead,
    is_lead_terminal,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    list_session_leads,
)
from game.social import (
    _social_turn_counter,
    explicit_player_topic_anchor_state,
    list_recent_npc_lead_discussions,
)
from game.storage import get_scene_state
from game.world import get_world_npc_by_id
from game.interaction_context import build_speaker_selection_contract, response_type_context_snapshot
from game.narration_visibility import _normalize_visibility_text, build_narration_visibility_contract
from game.opening_visible_fact_selection import (
    OPENING_NARRATION_VISIBLE_FACT_MAX,
    select_opening_narration_visible_facts,
)
from game.anti_railroading import build_anti_railroading_contract
from game.context_separation import build_context_separation_contract
from game.player_facing_narration_purity import build_player_facing_narration_purity_contract
from game.scene_state_anchoring import build_scene_state_anchor_contract
from game.narrative_authority import build_narrative_authority_contract
from game.fallback_behavior import build_fallback_behavior_contract
from game.tone_escalation import build_tone_escalation_contract
from game.response_type_gating import derive_response_type_contract
from game.interaction_continuity import build_interaction_continuity_contract
from game.conversational_memory_window import (
    _extract_explicit_reintroductions,
    build_conversational_memory_window_contract,
    select_conversational_memory_window,
)
from game.response_policy_contracts import (
    build_social_response_structure_contract,
    peek_response_type_contract_from_resolution,
)
from game.turn_packet import build_turn_packet

# Configurable limits for deterministic, inspectable compression
MAX_RECENT_LOG = 5
MAX_RECENT_EVENTS = 5
MAX_GM_GUIDANCE = 3
MAX_WORLD_PRESSURES = 3
MAX_LOG_ENTRY_SNIPPET = 200
MAX_FOLLOW_UP_TOPIC_TOKENS = 6
MAX_RECENT_CONTEXTUAL_LEADS = 4
CONVERSATIONAL_MEMORY_SOFT_LIMIT = 12
CONVERSATIONAL_MEMORY_MAX_CANDIDATES = 36
_CONV_MEM_TITLE_TOPIC_RE = re.compile(r"[a-z]{4,}", re.IGNORECASE)

SOCIAL_REPLY_KINDS = frozenset({
    'question',
    'persuade',
    'intimidate',
    'deceive',
    'barter',
    'recruit',
    'social_probe',
})
NPC_REPLY_KIND_VALUES = frozenset({'answer', 'explanation', 'reaction', 'refusal'})

# Single source of truth for narration-rule precedence. Prompting and
# deterministic enforcement both read this so conflicts resolve the same way.
RESPONSE_RULE_PRIORITY: tuple[tuple[str, str], ...] = (
    ("must_answer", "ANSWER THE PLAYER"),
    ("forbid_state_invention", "DO NOT CONTRADICT AUTHORITATIVE STATE"),
    ("forbid_secret_leak", "DO NOT LEAK HIDDEN FACTS / SECRETS"),
    (
        "forbid_unjustified_narrative_authority",
        "DO NOT ASSERT UNRESOLVED OUTCOMES, HIDDEN TRUTHS, OR NPC INTENT AS SETTLED FACT",
    ),
    (
        "preserve_player_agency",
        "PRESERVE PLAYER AGENCY — DO NOT DECIDE ACTIONS OR UPGRADE SURFACED LEADS INTO MANDATORY PATHS",
    ),
    ("allow_partial_answer", "IF FULL CERTAINTY IS UNAVAILABLE, GIVE A BOUNDED PARTIAL ANSWER"),
    (
        "response_delta",
        "WHEN THE PLAYER PRESSES THE SAME TOPIC AGAIN, ADD NET-NEW VALUE RATHER THAN RESTATING",
    ),
    (
        "narrative_authenticity",
        "KEEP NARRATION AND SPOKEN LINES DISTINCT; PREFER NEW SIGNAL OVER GENERIC FILLER; RESPECT FALLBACK BREVITY",
    ),
    ("diegetic_only", "MAINTAIN DIEGETIC VOICE (no validator/system voice)"),
    (
        "player_facing_narration_purity",
        "KEEP NARRATION FREE OF INTERNAL SCAFFOLDS, MENU LABELS, AND ENGINE COACHING",
    ),
    ("prefer_scene_momentum", "PRESERVE SCENE MOMENTUM"),
    ("prefer_specificity", "ADD SPECIFICITY / FLAVOR / POLISH"),
)

RULE_PRIORITY_COMPACT_INSTRUCTION = (
    "When rules conflict, resolve them in this order: answer the player; preserve authoritative "
    "state; avoid leaking hidden facts; avoid unjustified certainty about outcomes, hidden truths, "
    "and NPC intent (defer per narrative authority policy); preserve player agency—do not decide the PC's action "
    "or treat surfaced leads as mandatory plot gravity (see anti_railroading policy); if certainty is incomplete, "
    "give a bounded partial answer; when the player presses the same topic, add net-new value rather than restating; "
    "keep narration and quoted speech from recycling the same surface clauses (narrative_authenticity); "
    "remain diegetic; keep narration free of internal scaffolds, menu-style choice labels, and engine coaching "
    "(see player_facing_narration_purity policy); maintain scene momentum only after agency constraints; then add specificity."
)

# Resolution kinds where follow-up “delta vs repetition” is not meaningful (mechanical / transition turns).
_RESPONSE_DELTA_SUPPRESS_RESOLUTION_KINDS: frozenset[str] = frozenset(
    {
        "attack",
        "combat",
        "cast_spell",
        "roll_initiative",
        "end_turn",
        "scene_transition",
        "travel",
    }
)

_RESPONSE_DELTA_ALLOWED_KINDS: tuple[str, ...] = (
    "new_information",
    "refinement",
    "consequence",
    "clarified_uncertainty",
)

# Bounded-partial justification buckets for machine-readable enforcement (turn-local).
ANSWER_COMPLETENESS_PARTIAL_REASONS: tuple[str, ...] = (
    "uncertainty",
    "lack_of_knowledge",
    "gated_information",
)
EXPECTED_ANSWER_VOICE: tuple[str, ...] = ("npc", "narrator", "either")
EXPECTED_ANSWER_SHAPE: tuple[str, ...] = ("direct", "bounded_partial", "refusal_with_reason")
CONCRETE_PAYLOAD_KINDS: tuple[str, ...] = (
    "name",
    "place",
    "fact",
    "direction",
    "condition",
    "next_lead",
)

_QUESTION_LINE_PATTERN = re.compile(
    r"(^\s*(what|where|when|why|how|who|which|whose)\b)|\?|"
    r"\b(tell me|could you tell|can you tell|do you know|did you see|is it true)\b|"
    r"\b(who is|who was|what's|whats|where's|wheres|how many|how much)\b",
    re.IGNORECASE | re.MULTILINE,
)
NO_VALIDATOR_VOICE_RULE = (
    "Never speak as a validator, analyst, referee of canon, or system. Do not mention what is or "
    "is not established, available to the model, visible to tools, or answerable by the system. "
    "If uncertainty exists, express it as in-world uncertainty from people, circumstances, clues, "
    "distance, darkness, rumor, missing access, or incomplete observation."
)
NO_VALIDATOR_VOICE_PROHIBITIONS: tuple[str, ...] = (
    "canon_validation",
    "evidence_review",
    "system_limitation",
    "tool_access",
    "model_identity",
    "rules_explanation_outside_oc_or_adjudication",
)
UNCERTAINTY_CATEGORIES: tuple[str, ...] = (
    "unknown_identity",
    "unknown_location",
    "unknown_motive",
    "unknown_method",
    "unknown_quantity",
    "unknown_feasibility",
)
UNCERTAINTY_SOURCES: tuple[str, ...] = (
    "npc_ignorance",
    "scene_ambiguity",
    "procedural_insufficiency",
)
UNCERTAINTY_ANSWER_SHAPE: tuple[str, ...] = (
    "known_edge",
    "unknown_edge",
    "next_lead",
)

NARRATION_VISIBILITY_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "VISIBILITY CONTRACT (MANDATORY): Use narration_visibility as the hard scope for entity references and factual assertions.",
    "You MUST NOT reference entities outside narration_visibility.visible_entities.",
    "You MUST NOT assert facts outside narration_visibility.visible_facts; only visible facts may be directly asserted.",
    "You MUST NOT reveal hidden or undiscovered facts.",
    "Discoverable facts may be hinted at (discoverable_hinting is true), but not asserted as confirmed truth.",
    "If uncertain whether something is visible or known, omit or reframe it.",
    "Only visible or addressable entities may act or speak.",
)

FIRST_MENTION_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "FIRST-MENTION CONTRACT (MANDATORY): Visibility scope controls who/what may be referenced; first-mention contract controls how first references are phrased.",
    "The first reference to any entity MUST be explicit.",
    "A first reference MUST use a visible name or a visible descriptor.",
    "A first reference MUST include grounding by location, behavior, or relation.",
    "Pronouns MAY be used only after explicit introduction.",
    "You MUST NOT use unearned familiarity phrases (for example, 'you recognize ...', 'you remember ...', 'you know this is ...') unless supported by narration_visibility.visible_facts.",
)

SCENE_STATE_ANCHOR_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "SCENE STATE ANCHOR (MANDATORY): Every response must visibly ground itself in the present scene through at least one of: "
    "current location, a current actor or speaker allowed by authoritative state (see scene_state_anchor_contract), "
    "or the player's immediate action (turn_summary + mechanical_resolution).",
    "Avoid floating, abstract, or scene-detached narration.",
)

_TOPIC_TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z']{2,}")
_TOPIC_STOPWORDS = frozenset({
    "what", "where", "when", "why", "how", "who", "which",
    "tell", "said", "says", "know", "knew", "think", "heard",
    "about", "again", "still", "really", "actually", "just",
    "there", "here", "them", "they", "their", "then", "than",
    "with", "from", "into", "onto", "over", "under", "near",
    "this", "that", "these", "those", "your", "you're", "youre",
    "have", "has", "had", "can", "could", "would", "should",
    "does", "did", "is", "are", "was", "were", "will",
})
_FOLLOW_UP_PRESS_TOKENS: tuple[str, ...] = (
    "again",
    "still",
    "okay but",
    "ok but",
    "but",
    "be specific",
    "details",
    "name",
    "names",
    "where exactly",
    "who exactly",
)

# Family-level deterministic detectors (strict-social answer-pressure). Prefer patterns over long phrase lists.
_DIRECT_ANSWER_DEMAND_RE = re.compile(
    r"\b("
    r"answer\s+(directly|the\s+question|me)|please\s+answer|just\s+answer|"
    r"give\s+(me\s+)?(a\s+)?straight|tell\s+me\s+straight|"
    r"stop\s+(dodging|deflecting|evading)|quit\s+(dodging|deflecting)|"
    r"enough\s+riddles|cut\s+the\s+crap|the\s+truth\s+now|"
    r"not\s+a\s+hedge|don'?t\s+hedge"
    r")\b",
    re.IGNORECASE,
)
_SPECIFICITY_DEMAND_RE = re.compile(
    r"\b("
    r"be\s+specific|be\s+precise|"
    r"exactly\s+(where|who|what|which|when|how)|"
    r"no,?\s+exactly\s+where|"
    r"which\s+one|what\s+exactly|where\s+exactly|who\s+exactly"
    r")\b",
    re.IGNORECASE,
)
_EXPLANATION_DEMAND_RE = re.compile(
    r"\b("
    r"why\s+not|why\b|how\s+so|"
    r"what\s+do\s+you\s+mean(\s+by\s+that)?|"
    r"(could|can|will)\s+you\s+explain|"
    r"explain\s+(that|this|yourself)\b"
    r")\b",
    re.IGNORECASE,
)
_CONTRADICTION_OR_REFUSAL_CHALLENGE_RE = re.compile(
    r"("
    r"\b(you\s+)?(can'?t|cannot)\s+(tell|say|answer|explain)\b|"
    r"\b(won'?t|will\s+not)\s+(say|tell|explain)\b|"
    r"\b(you\s+)?(don'?t|do\s+not)\s+know\b|"
    r"\bso\s+you\s+(don'?t|do\s+not)\s+know\b|"
    r"\bare(n'?t|\s+not)\s+you\s+going\s+to\s+tell\b|"
    r"\byou(\'re|\s+are)\s+saying\s+you\s+(can'?t|cannot)\b|"
    r"\brefus(e|ing)\s+to\s+(say|tell|explain)\b|"
    r"\bwon'?t\s+explain\b"
    r")",
    re.IGNORECASE,
)
_INSUFFICIENCY_PRESSURE_RE = re.compile(
    r"\b("
    r"that'?s\s+all\??|is\s+that\s+all\??|"
    r"anything\s+more(\s+than\s+that)?|"
    r"what\s+can\s+you\s+actually(\s+confirm|\s+know)?|"
    r"what\s+do\s+you\s+actually\s+know|what\s+do\s+you\s+really\s+know|"
    r"then\s+what\s+can\s+you\s+confirm|what\s+can\s+you\s+confirm"
    r")\b",
    re.IGNORECASE,
)
_CONSEQUENCE_PROBE_RE = re.compile(
    r"\b("
    r"safe\s+how|how\s+is\s+it\s+safe|"
    r"what\s+happens\s+if\s+i\b|what\s+happens\s+if\s+we\b"
    r")\b",
    re.IGNORECASE,
)
_SHORT_INTERROGATIVE_FOLLOWUP_RE = re.compile(
    r"^\s*(why|how|why\s+not|how\s+so)\s*\?\s*$",
    re.IGNORECASE,
)
_BARE_WHAT_INTERROGATIVE_RE = re.compile(
    r"^\s*what\s*\?\s*$",
    re.IGNORECASE,
)

# Player explicitly rejects a non-responsive NPC line and reasserts the intended question (Objective #6).
_CORRECTION_REASK_MISMATCH_RES: tuple[re.Pattern, ...] = (
    re.compile(r"\bi\s+asked\b", re.IGNORECASE),
    re.compile(r"\bi\s+was\s+asking\b", re.IGNORECASE),
    re.compile(r"\bthat\s+didn'?t\s+answer\b", re.IGNORECASE),
    re.compile(r"\bdidn'?t\s+answer\s+(my\s+)?question\b", re.IGNORECASE),
    re.compile(r"\bnot\s+what\s+i\s+asked\b", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+not\s+what\s+i\s+asked\b", re.IGNORECASE),
    re.compile(r"\bi\s+meant\b", re.IGNORECASE),
    re.compile(r"\bno,?\s+i\s+asked\b", re.IGNORECASE),
    re.compile(r"\banswer\s+the\s+question\s+i\s+asked\b", re.IGNORECASE),
)


def _correction_reask_mismatch_hit(player_text: str) -> bool:
    t = str(player_text or "").strip()
    if not t:
        return False
    return any(cre.search(t) for cre in _CORRECTION_REASK_MISMATCH_RES)


def _correction_reask_reassertion_hit(player_text: str, prev_player_line: str) -> bool:
    """Require a visible reassertion target (wh-axis, 'my question', contrast, prior-thread overlap, or long re-ask)."""
    cur = str(player_text or "").strip()
    if not cur:
        return False
    low = cur.lower()
    if re.search(r"\b(why|where|who|what|which|how)\b", low):
        return True
    if "my question" in low:
        return True
    if re.search(r"\bnot\s+[^,\n]{1,32},\s*(why|where|who|what|which)\b", low):
        return True
    if re.search(r"\bi\s+meant\b", low):
        return _overlap_ratio(_topic_tokens(cur), _topic_tokens(prev_player_line)) >= 0.22
    if "i asked" in low and len(cur.split()) >= 5:
        return True
    return False


def _correction_reask_followup_candidate(
    player_text: str,
    *,
    active_target_id: str,
    pair_ok: bool,
    prior_substantive: bool,
    prev_gm: str,
    prev_player: str,
) -> bool:
    if not (
        str(active_target_id or "").strip()
        and pair_ok
        and prior_substantive
        and str(prev_gm or "").strip()
    ):
        return False
    cur = str(player_text or "").strip()
    if not _correction_reask_mismatch_hit(cur):
        return False
    return _correction_reask_reassertion_hit(cur, prev_player)


# Prior GM text suggests guarded / refusal / partial / hedge (follow-up "why?" is meaningful).
_GM_GUARDED_OR_REFUSAL_MARKERS: tuple[str, ...] = (
    "can't",
    "cannot",
    "cant ",
    "won't",
    "wont ",
    "will not",
    "don't know",
    "dont know",
    "dunno",
    "not sure",
    "hard to say",
    "rather not",
    "won't say",
    "can't say",
    "cannot say",
    "no names",
    "too many ears",
    "nothing you can",
    "can't give",
    "won't give",
    "if i tell",
    "not at liberty",
    "classified",
    "rumors",
    "rumour",
    "word is thin",
    "hedge",
    "vague",
    "rather vague",
    "all i can say",
    "as far as i",
    "not much",
    "only know",
    "little i know",
)

# Broader anchors in prior NPC line: refusal, warning, condition, causal framing (short follow-up hook).
_GM_FOLLOWUP_ANCHOR_MARKERS: tuple[str, ...] = _GM_GUARDED_OR_REFUSAL_MARKERS + (
    "because",
    "if you",
    "warning",
    "careful",
    "listen",
    "sealed",
    "after dark",
    "keep your voice",
    "lower your",
    "watch yourself",
    "condition",
    "unless",
    "however",
    "claim",
    "truth is",
)

_GREETING_ONLY_LINE = re.compile(
    r"^\s*(?:hi|hello|hey|good\s+(?:morning|afternoon|evening|day)|greetings)\b[^.!?]{0,40}\.?\s*$",
    re.IGNORECASE,
)
_THANKS_ONLY_LINE = re.compile(
    r"^\s*(?:thanks?|thank you|cheers|much obliged)\b[^.!?]{0,24}\.?\s*$",
    re.IGNORECASE,
)

# Block 2: deterministic anchors from the immediately prior NPC line (no NLP).
_ANCHOR_WORD_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "but",
        "for",
        "with",
        "from",
        "into",
        "onto",
        "over",
        "under",
        "his",
        "her",
        "its",
        "our",
        "your",
        "their",
        "this",
        "that",
        "these",
        "those",
        "some",
        "any",
        "all",
        "very",
        "just",
        "only",
        "too",
        "also",
        "not",
        "yes",
        "no",
        "old",
        "new",
        "few",
        "own",
        "same",
        "other",
        "such",
    }
)
_ANCHOR_TITLE_CASE_SKIP: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "i",
        "we",
        "you",
        "they",
        "he",
        "she",
        "it",
        "if",
        "when",
        "as",
        "but",
        "and",
        "or",
        "so",
        "there",
        "here",
    }
)
# Clue / location / concrete-object heads — not generic venue labels or role nouns (see blocklist below).
_ANCHOR_LEAD_LEXEMES: tuple[str, ...] = (
    "crossroads",
    "graveyard",
    "cemetery",
    "checkpoint",
    "milestone",
    "warehouse",
    "caravan",
    "bastion",
    "drawbridge",
    "gatehouse",
    "shrine",
    "crypt",
    "cellar",
    "tunnel",
    "ruins",
    "patrol",
    "contract",
    "ledger",
    "letter",
    "banner",
    "sigil",
    "bridge",
    "dock",
    "alley",
    "ghost",
    "rumour",
    "rumor",
    "legend",
    "oath",
    "seal",
    "shipment",
    "map",
)
_ANCHOR_LEAD_LEXEMES_SET: frozenset[str] = frozenset(_ANCHOR_LEAD_LEXEMES)
_ANCHOR_LEAD_LEXEMES_BY_LEN: tuple[str, ...] = tuple(
    sorted(set(_ANCHOR_LEAD_LEXEMES), key=lambda s: (-len(s), s))
)
# Standalone suppression: these must not act as explanation-followup anchors unless paired with a clue lexeme
# in the same multiword span (e.g. "tavern checkpoint" may still anchor on "checkpoint").
_ANCHOR_GENERIC_ROLE_TITLE_TOKENS: frozenset[str] = frozenset(
    {
        "captain",
        "guard",
        "guards",
        "runner",
        "crier",
        "lord",
        "lords",
        "stranger",
        "strangers",
        "watcher",
        "watchers",
        "refugee",
        "refugees",
        "corporal",
        "sergeant",
        "lieutenant",
        "soldier",
        "soldiers",
        "merchant",
        "merchants",
        "bartender",
        "innkeeper",
        "envoy",
        "envoys",
        "messenger",
        "messengers",
        "herald",
        "heralds",
        "scout",
        "scouts",
        "sentinel",
        "sentinels",
        "watchman",
        "watchmen",
        "keeper",
        "keepers",
        "tavern",
        "taverns",
        "folk",
        "traveler",
        "travelers",
        "traveller",
        "travellers",
        "sir",
        "madam",
        "maam",
        "milord",
        "master",
        "mistress",
    }
)
_ADJ_BEFORE_STRONG_NOUN_ALT = (
    "old|new|east|west|north|south|central|upper|lower|inner|outer|main|"
    "southern|northern|eastern|western"
)
_CLUE_LEXEME_RE_ALT = "|".join(
    re.escape(x) for x in sorted(set(_ANCHOR_LEAD_LEXEMES), key=lambda s: (-len(s), s))
)
_ADJ_BEFORE_STRONG_NOUN_RE = re.compile(
    rf"\b(?:{_ADJ_BEFORE_STRONG_NOUN_ALT})\s+(?:{_CLUE_LEXEME_RE_ALT})\b"
)
_PREP_HEADED_ANCHOR_PHRASE_RE = re.compile(
    r"\b(?:near|at|by|toward|towards|beside|past|beyond)\s+(?:(?:the|a|an)\s+)?"
    r"([A-Za-z][\w'-]*(?:\s+[A-Za-z][\w'-]*){0,2})\b",
)


def _sentence_start_char_indices(text: str) -> set[int]:
    """Indices where a new sentence (or line) begins after punctuation or newline."""
    starts = {0}
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in ".!?":
            j = i + 1
            while j < n and text[j] in "\"')]}":
                j += 1
            while j < n and text[j].isspace():
                j += 1
            if j < n:
                starts.add(j)
            i = j
            continue
        if ch == "\n":
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            if j < n:
                starts.add(j)
            i = j
            continue
        i += 1
    return starts


def _extract_npc_introduced_anchor_tokens(npc_reply: str) -> List[str]:
    """Return 1–3 anchor-worthy strings from prior NPC text.

    Favors clue/location lexemes and grounded phrases (e.g. ``old milestone``). Does not treat
    generic role/title/address nouns as anchors unless they appear in the same multiword span
    as a clue lexeme (e.g. anchoring on ``checkpoint`` in ``tavern checkpoint``).
    """
    text = str(npc_reply or "").strip()
    if not text:
        return []
    low = " ".join(text.lower().split())
    candidates: List[tuple[int, str]] = []
    seen: set[str] = set()

    def add_at(pos: int, tok: str) -> None:
        t = str(tok or "").strip().lower().strip("'\"")
        if len(t) < 3:
            return
        parts = t.split()
        if any(len(p) < 3 for p in parts):
            return
        if " " not in t and t in _ANCHOR_WORD_STOPWORDS:
            return
        for p in parts:
            if p not in _ANCHOR_GENERIC_ROLE_TITLE_TOKENS:
                continue
            if " " in t and any(x in _ANCHOR_LEAD_LEXEMES_SET for x in parts):
                continue
            return
        if " " in t and not any(p in _ANCHOR_LEAD_LEXEMES_SET for p in parts):
            return
        if " " not in t and t in _ANCHOR_GENERIC_ROLE_TITLE_TOKENS:
            return
        if t not in seen:
            seen.add(t)
            candidates.append((pos, t))

    for clue in _ANCHOR_LEAD_LEXEMES_BY_LEN:
        for m in re.finditer(rf"\b{re.escape(clue)}\b", low):
            add_at(m.start(), clue)

    for m in _ADJ_BEFORE_STRONG_NOUN_RE.finditer(low):
        add_at(m.start(), m.group(0).strip())

    # Prep-headed spans: only keep a multiword anchor when a clue lexeme appears inside the span
    # (do not emit per-word heads — that used to surface ``captain``, ``runner``, etc.).
    for m in _PREP_HEADED_ANCHOR_PHRASE_RE.finditer(text):
        phrase_raw = str(m.group(1) or "")
        phrase_low = " ".join(phrase_raw.lower().split())
        if not any(
            re.search(rf"\b{re.escape(c)}\b", phrase_low) for c in _ANCHOR_LEAD_LEXEMES_SET
        ):
            continue
        words = [w.strip(".,;:'\"—-") for w in phrase_raw.split()]
        content = [w for w in words if w.lower() not in {"the", "a", "an"}]
        if len(content) < 2:
            continue
        joined = " ".join(w.lower() for w in content)
        non_generic = [w for w in joined.split() if w not in _ANCHOR_GENERIC_ROLE_TITLE_TOKENS]
        if not non_generic:
            continue
        if not any(w in _ANCHOR_LEAD_LEXEMES_SET for w in non_generic):
            continue
        add_at(m.start(1), joined)

    sent_starts = _sentence_start_char_indices(text)
    for m in re.finditer(r"\b[A-Z][a-zA-Z']{2,}\b", text):
        if m.start() in sent_starts:
            continue
        w = m.group(0)
        wl = w.lower()
        if wl in _ANCHOR_TITLE_CASE_SKIP:
            continue
        if wl in _ANCHOR_GENERIC_ROLE_TITLE_TOKENS:
            continue
        add_at(m.start(), wl)

    candidates.sort(key=lambda x: x[0])
    out: List[str] = []
    for _pos, t in candidates:
        if t in out:
            continue
        out.append(t)
        if len(out) >= 3:
            break
    return out


def _player_line_matches_anchor_token(player_norm: str, anchor: str) -> bool:
    a = str(anchor or "").strip().lower()
    if len(a) < 3:
        return False
    pl = str(player_norm or "").strip().lower()
    if " " in a:
        parts = a.split()
        return all(bool(re.search(rf"\b{re.escape(p)}s?\b", pl)) for p in parts)
    return bool(re.search(rf"\b{re.escape(a)}s?\b", pl))


def _interrogative_or_explanation_ask_shape(player_text: str) -> bool:
    t = str(player_text or "").strip()
    if not t:
        return False
    if _short_interrogative_followup_line(t):
        return True
    if _bare_what_interrogative_line(t):
        return True
    if question_detected_from_player_text(t):
        return True
    if t.rstrip().endswith("?"):
        return True
    return False


def _anchor_deictic_place_followup(player_text: str, player_norm: str) -> bool:
    t = str(player_text or "").strip()
    pl = str(player_norm or "").strip()
    if not t or not pl:
        return False
    if not re.search(r"\b(there|here)\b", pl):
        return False
    if not re.search(r"\b(what|why|how|who|when|where|which)\b", pl):
        return False
    if len(t) > 56:
        return False
    if len(t.split()) > 10:
        return False
    return True


def _topic_tokens(text: str) -> List[str]:
    low = " ".join(str(text or "").strip().lower().split())
    if not low:
        return []
    toks = [t for t in _TOPIC_TOKEN_PATTERN.findall(low) if len(t) >= 4 and t not in _TOPIC_STOPWORDS]
    seen: set[str] = set()
    out: List[str] = []
    for t in toks:
        if t in seen:
            continue
        out.append(t)
        seen.add(t)
        if len(out) >= MAX_FOLLOW_UP_TOPIC_TOKENS:
            break
    return out


def _overlap_ratio(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    inter = len(sa & sb)
    denom = min(len(sa), len(sb))
    return float(inter) / float(denom or 1)


def _prior_answer_snippet_substantive(gm_snippet: str) -> bool:
    """Heuristic: prior GM text must be enough to compare against (not an empty/effectively non-answer)."""
    s = " ".join(str(gm_snippet or "").strip().split())
    if len(s) < 12:
        return False
    words = s.split()
    if len(words) < 2 and len(s) < 36:
        return False
    low = s.lower()
    if low in {"yes.", "no.", "ok.", "okay.", "nope.", "yeah.", "sure."}:
        return False
    return True


def _compute_follow_up_pressure(recent_log_compact: List[Dict[str, Any]], user_text: str) -> Dict[str, Any] | None:
    """Detect when the player is pressing the same topic over consecutive turns.

    This is intentionally lightweight and prompt-scoped: it uses only the recent
    log slice already passed to the model (no new persistence/memory subsystem).
    """
    if not recent_log_compact:
        return None
    last = recent_log_compact[-1] if isinstance(recent_log_compact[-1], dict) else {}
    prev_player = str(last.get("player_input") or "").strip()
    prev_gm = str(last.get("gm_snippet") or "").strip()
    if not prev_player or not prev_gm:
        return None

    cur = str(user_text or "").strip()
    if not cur:
        return None

    cur_low = cur.lower()
    press_marker = any(tok in cur_low for tok in _FOLLOW_UP_PRESS_TOKENS)
    cur_tokens = _topic_tokens(cur)
    prev_tokens = _topic_tokens(prev_player)
    overlap = _overlap_ratio(cur_tokens, prev_tokens)

    pressed = (overlap >= 0.55 and len(cur_tokens) >= 2) or (press_marker and overlap >= 0.35 and len(cur_tokens) >= 1)
    if not pressed:
        return None

    press_depth = 1
    for entry in reversed(recent_log_compact[:-1]):
        if not isinstance(entry, dict):
            break
        txt = str(entry.get("player_input") or "").strip()
        if not txt:
            break
        if _overlap_ratio(cur_tokens, _topic_tokens(txt)) < 0.35:
            break
        press_depth += 1
        if press_depth >= 3:
            break

    return {
        "pressed": True,
        "press_depth": press_depth,
        "topic_tokens": cur_tokens,
        "previous_player_input": prev_player[:240],
        "previous_answer_snippet": prev_gm[:240],
        "overlap_ratio": round(overlap, 3),
    }


def _normalize_player_line_for_lexical(s: str) -> str:
    t = " ".join(str(s or "").strip().lower().split())
    return re.sub(r"[''`]", "", t)


def _loose_lexical_anchor(player_text: str, haystack: str) -> bool:
    """Any 4+ letter word from player line appears in haystack (handles light morph variance)."""
    h = str(haystack or "").lower()
    if not h:
        return False
    for w in re.findall(r"[a-zA-Z]{4,}", str(player_text or "").lower()):
        if w in h:
            return True
    return False


def _prior_gm_guarded_or_refusal_partial(gm_snippet: str) -> bool:
    low = _normalize_player_line_for_lexical(gm_snippet)
    if not low:
        return False
    return any(m in low for m in _GM_GUARDED_OR_REFUSAL_MARKERS)


def _prior_gm_has_followup_anchor(gm_snippet: str) -> bool:
    low = _normalize_player_line_for_lexical(gm_snippet)
    if not low:
        return False
    return any(m in low for m in _GM_FOLLOWUP_ANCHOR_MARKERS)


# Block 2: prior GM line carries a narrow watch/risk/attention referent (not clue-anchor extraction).
_PRIOR_RECENT_REFERENCE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\beyes?\s+(?:are|were)\s+on\s+you\b", re.I), "eyes_on_you"),
    (re.compile(r"\beye[s']?\s+on\s+you\b", re.I), "eyes_on_you"),
    (re.compile(r"\bthey(?:'re|\s+are)\s+watching\b", re.I), "they_watching"),
    (re.compile(r"\bpeople\s+watching\b", re.I), "people_watching"),
    (re.compile(r"\bsome(?:one|body)\s+watching\b", re.I), "someone_watching"),
    (re.compile(r"\bears\s+listening\b|\blistening\s+ears\b", re.I), "listening_ears"),
    (re.compile(r"\bsome(?:one|body)\s+(?:is\s+)?listen(?:ing)?\b", re.I), "someone_listening"),
    (re.compile(r"\b(?:watched|watching|watchers?)\b", re.I), "watching"),
)

# Short clarification prompts that can resolve those referents (regex-only; order = most specific first).
_RECENT_REF_CLARIFICATION_SHAPES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwhose\s+eyes\b", re.I), "whose_eyes"),
    (re.compile(r"\bwhat\s+eyes\b", re.I), "what_eyes"),
    (re.compile(r"\bwho'?s\s+watching\b", re.I), "whos_watching"),
    (re.compile(r"\bwhat\s+do\s+you\s+mean", re.I), "what_do_you_mean"),
    (re.compile(r"\bwhich\s+ones?\b", re.I), "which_ones"),
    (re.compile(r"^\s*who\s+is\b", re.I), "who_is"),
    (re.compile(r"^\s*whose\s*\?\s*$", re.I), "whose_bare"),
    (re.compile(r"^\s*who\s*\?\s*$", re.I), "who_bare"),
)

_RECENT_REF_EYES_PRIOR_KINDS: frozenset[str] = frozenset({"eyes_on_you"})
_RECENT_REF_WATCH_PRIOR_KINDS: frozenset[str] = frozenset(
    {"they_watching", "people_watching", "someone_watching", "watching"}
)
_RECENT_REF_LISTEN_PRIOR_KINDS: frozenset[str] = frozenset({"listening_ears", "someone_listening"})


def _scan_prior_recent_reference(gm_snippet: str) -> tuple[str | None, str | None]:
    """Return (referent_kind, matched_phrase_snippet) for the first prior-line cue, else (None, None)."""
    low = _normalize_player_line_for_lexical(gm_snippet)
    if not low:
        return None, None
    for cre, kind in _PRIOR_RECENT_REFERENCE_PATTERNS:
        m = cre.search(low)
        if m:
            return kind, str(m.group(0) or "").strip()[:48] or None
    return None, None


def _match_recent_reference_clarification_shape(player_text: str) -> str | None:
    raw = str(player_text or "").strip()
    if not raw:
        return None
    for cre, shape in _RECENT_REF_CLARIFICATION_SHAPES:
        if cre.search(raw):
            return shape
    return None


def _recent_reference_shape_matches_prior(prior_kind: str, shape: str) -> bool:
    if prior_kind in _RECENT_REF_EYES_PRIOR_KINDS:
        return shape in {
            "whose_eyes",
            "what_eyes",
            "whose_bare",
            "what_do_you_mean",
            "who_bare",
            "who_is",
        }
    if prior_kind in _RECENT_REF_WATCH_PRIOR_KINDS:
        return shape in {
            "who_bare",
            "who_is",
            "whos_watching",
            "what_do_you_mean",
            "which_ones",
        }
    if prior_kind in _RECENT_REF_LISTEN_PRIOR_KINDS:
        return shape in {
            "who_bare",
            "who_is",
            "what_do_you_mean",
            "which_ones",
        }
    return False


def _is_short_clarifying_reference_player_line(player_text: str) -> bool:
    """Short, interrogative/clarifying line (bounded; not a general pronoun resolver)."""
    t = str(player_text or "").strip()
    if not t or len(t) > 96:
        return False
    if len(t.split()) > 14:
        return False
    if not (t.rstrip().endswith("?") or question_detected_from_player_text(t)):
        return False
    return True


def _classify_answer_pressure_families(player_text: str) -> Dict[str, bool]:
    raw = str(player_text or "").strip()
    low = _normalize_player_line_for_lexical(raw)
    if not low:
        return {k: False for k in (
            "direct_answer_demand",
            "specificity_demand",
            "explanation_demand",
            "contradiction_or_refusal_challenge",
            "insufficiency_pressure",
            "consequence_probe",
        )}
    return {
        "direct_answer_demand": bool(_DIRECT_ANSWER_DEMAND_RE.search(raw)),
        "specificity_demand": bool(_SPECIFICITY_DEMAND_RE.search(raw)),
        "explanation_demand": bool(_EXPLANATION_DEMAND_RE.search(raw)),
        "contradiction_or_refusal_challenge": bool(_CONTRADICTION_OR_REFUSAL_CHALLENGE_RE.search(raw)),
        "insufficiency_pressure": bool(_INSUFFICIENCY_PRESSURE_RE.search(raw)),
        "consequence_probe": bool(_CONSEQUENCE_PROBE_RE.search(raw)),
    }


def _answer_pressure_lexical_hit(player_text: str) -> bool:
    """True when any family uses a strong, self-sufficient phrase (legacy field ``lexical_pressure``)."""
    fam = _classify_answer_pressure_families(player_text)
    return any(
        fam.get(k)
        for k in (
            "direct_answer_demand",
            "specificity_demand",
            "insufficiency_pressure",
            "consequence_probe",
        )
    )


def _short_interrogative_followup_line(player_text: str) -> bool:
    return bool(_SHORT_INTERROGATIVE_FOLLOWUP_RE.match(str(player_text or "").strip()))


def _bare_what_interrogative_line(player_text: str) -> bool:
    return bool(_BARE_WHAT_INTERROGATIVE_RE.match(str(player_text or "").strip()))


def _is_conversational_color_without_answer_demand(player_text: str) -> bool:
    """Conservative exclusion for answer-pressure detection (greetings, bare thanks, tiny acks)."""
    t = str(player_text or "").strip()
    if not t:
        return True
    if _GREETING_ONLY_LINE.match(t) or _THANKS_ONLY_LINE.match(t):
        return True
    if len(t) < 18 and "?" not in t:
        low = t.lower()
        if low in {"yeah", "yep", "no", "nah", "ok", "okay", "sure", "fine"}:
            return True
    return False


def _last_log_exchange(recent_log_compact: List[Dict[str, Any]] | None) -> tuple[str, str] | None:
    if not recent_log_compact:
        return None
    last = recent_log_compact[-1]
    if not isinstance(last, dict):
        return None
    prev_player = str(last.get("player_input") or "").strip()
    prev_gm = str(last.get("gm_snippet") or "").strip()
    if not prev_player or not prev_gm:
        return None
    return prev_player, prev_gm


def _synthetic_follow_up_pressure_from_log(
    recent_log_compact: List[Dict[str, Any]] | None,
    player_input: str,
) -> Dict[str, Any] | None:
    pair = _last_log_exchange(recent_log_compact)
    if pair is None:
        return None
    prev_player, prev_gm = pair
    cur = str(player_input or "").strip()
    if not cur:
        return None
    cur_tokens = _topic_tokens(cur)
    prev_tokens = _topic_tokens(prev_player)
    overlap = _overlap_ratio(cur_tokens, prev_tokens)
    return {
        "pressed": True,
        "press_depth": 1,
        "topic_tokens": cur_tokens or prev_tokens,
        "previous_player_input": prev_player[:240],
        "previous_answer_snippet": prev_gm[:240],
        "overlap_ratio": round(overlap, 3),
        "synthetic_for_answer_pressure": True,
    }


def _answer_pressure_followup_details(
    *,
    player_input: str,
    recent_log_compact: List[Dict[str, Any]] | None,
    narration_obligations: Dict[str, Any],
    session_view: Dict[str, Any] | None,
    answer_completeness: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic signal: player is pressing the same interlocutor for a substantive answer (strict-social safe)."""
    _ = narration_obligations if isinstance(narration_obligations, dict) else {}
    _ = answer_completeness if isinstance(answer_completeness, dict) else {}

    def _base_false(suppressed: List[str]) -> Dict[str, Any]:
        sb = list(suppressed)
        return {
            "answer_pressure_followup_detected": False,
            "same_interlocutor_followup": False,
            "lexical_pressure": False,
            "question_like": False,
            "prior_answer_substantive": False,
            "topic_overlap_follows_up": False,
            "suppressed_because": sb,
            "answer_pressure_family": None,
            "answer_pressure_anchor_kind": None,
            "contradiction_followup_detected": False,
            "explanation_followup_detected": False,
            "insufficiency_followup_detected": False,
            "short_followup_anchor_detected": False,
            "answer_pressure_reasons": [],
            "answer_pressure_suppressed_because": sb,
            "anchor_tokens_extracted": [],
            "anchor_token_matched": None,
            "anchor_followup_detected": False,
            "explanation_of_recent_anchor_followup": False,
            "recent_reference_clarification_detected": False,
            "recent_reference_kind": None,
            "recent_reference_phrase_matched": None,
            "clarification_prompt_shape": None,
            "correction_reask_followup_detected": False,
        }

    suppressed_because: List[str] = []
    sess = session_view if isinstance(session_view, dict) else {}
    active_target_id = str(sess.get("active_interaction_target_id") or "").strip()

    cur = str(player_input or "").strip()
    if not cur:
        suppressed_because.append("empty_player_input")
        return _base_false(suppressed_because)

    if _is_conversational_color_without_answer_demand(cur):
        suppressed_because.append("conversational_color_only")
        return _base_false(suppressed_because)

    if not active_target_id:
        suppressed_because.append("no_active_interlocutor")

    pair = _last_log_exchange(recent_log_compact)
    prior_substantive = False
    prev_player = ""
    prev_gm = ""
    if pair is None:
        suppressed_because.append("no_prior_log_exchange")
    else:
        prev_player, prev_gm = pair
        prior_substantive = _prior_answer_snippet_substantive(prev_gm)
        if not prior_substantive:
            suppressed_because.append("prior_answer_not_substantive")

    same_interlocutor_followup = bool(active_target_id and pair is not None)

    fam = _classify_answer_pressure_families(cur)
    lexical_pressure = _answer_pressure_lexical_hit(cur)
    player_q = question_detected_from_player_text(cur)
    pressure = _compute_follow_up_pressure(list(recent_log_compact or []), cur)

    topic_overlap_follows_up = False
    if pair and prev_player:
        topic_overlap_follows_up = (
            _overlap_ratio(_topic_tokens(cur), _topic_tokens(prev_player)) >= 0.35
        )

    cur_toks = _topic_tokens(cur)
    gm_toks = _topic_tokens(prev_gm) if prev_gm else []
    gm_token_overlap = bool(cur_toks and gm_toks and len(set(cur_toks) & set(gm_toks)) >= 1)
    gm_loose_anchor = _loose_lexical_anchor(cur, prev_gm) if prev_gm else False
    gm_overlap_signal = gm_token_overlap or gm_loose_anchor

    prior_guarded = _prior_gm_guarded_or_refusal_partial(prev_gm) if prev_gm else False
    prior_anchor = _prior_gm_has_followup_anchor(prev_gm) if prev_gm else False

    correction_reask_followup_detected = _correction_reask_followup_candidate(
        cur,
        active_target_id=active_target_id,
        pair_ok=pair is not None,
        prior_substantive=prior_substantive,
        prev_gm=prev_gm,
        prev_player=prev_player,
    )

    relaxed_continuity = bool(
        pressure is not None
        or topic_overlap_follows_up
        or gm_overlap_signal
        or prior_guarded
    )

    has_question_mark = "?" in cur
    challenge_framed = bool(player_q or has_question_mark)

    insufficiency_hit = bool(fam.get("insufficiency_pressure"))
    contradiction_hit = bool(fam.get("contradiction_or_refusal_challenge"))
    explanation_hit = bool(fam.get("explanation_demand"))
    short_interrogative = _short_interrogative_followup_line(cur)
    bare_what = _bare_what_interrogative_line(cur)

    contradiction_followup_detected = bool(
        contradiction_hit
        and challenge_framed
        and (relaxed_continuity or prior_guarded or gm_loose_anchor)
    )
    explanation_followup_detected = bool(
        explanation_hit
        and not short_interrogative
        and player_q
        and relaxed_continuity
    )
    insufficiency_followup_detected = bool(insufficiency_hit)

    short_followup_anchor_detected = bool(
        short_interrogative
        and prior_substantive
        and prior_guarded
        and prior_anchor
    )

    bare_what_ok = bool(
        bare_what
        and prior_substantive
        and (prior_guarded or topic_overlap_follows_up or gm_overlap_signal)
    )

    cur_lex = _normalize_player_line_for_lexical(cur)
    anchor_tokens_extracted: List[str] = []
    anchor_token_matched: str | None = None
    explanation_of_recent_anchor_followup = False
    if pair is not None and prev_gm.strip():
        anchor_tokens_extracted = _extract_npc_introduced_anchor_tokens(prev_gm)
        # Prefer a single clue lexeme over a longer phrase when both match (stable, readable telemetry).
        for tok in sorted(anchor_tokens_extracted, key=lambda t: (str(t).count(" "), len(str(t)))):
            if _player_line_matches_anchor_token(cur_lex, tok):
                anchor_token_matched = tok
                break
        asks_shape = _interrogative_or_explanation_ask_shape(cur)
        deictic_ok = bool(
            anchor_tokens_extracted
            and _anchor_deictic_place_followup(cur, cur_lex)
        )
        asks_on_anchor = bool(anchor_token_matched and asks_shape)
        # Generic role/title tokens are filtered in _extract_npc_introduced_anchor_tokens; with no
        # anchor-worthy residue, this path must not fire (avoids first-turn false positives).
        explanation_of_recent_anchor_followup = bool(
            active_target_id
            and prior_substantive
            and bool(anchor_tokens_extracted)
            and (asks_on_anchor or (deictic_ok and asks_shape))
        )
    anchor_followup_detected = bool(explanation_of_recent_anchor_followup)

    recent_reference_kind: str | None = None
    recent_reference_phrase_matched: str | None = None
    clarification_prompt_shape: str | None = None
    recent_reference_clarification_detected = False
    if (
        active_target_id
        and pair is not None
        and prior_substantive
        and prev_gm.strip()
    ):
        ref_kind, ref_phrase = _scan_prior_recent_reference(prev_gm)
        clar_shape = _match_recent_reference_clarification_shape(cur)
        if (
            ref_kind
            and clar_shape
            and _is_short_clarifying_reference_player_line(cur)
            and _recent_reference_shape_matches_prior(ref_kind, clar_shape)
        ):
            recent_reference_clarification_detected = True
            recent_reference_kind = ref_kind
            recent_reference_phrase_matched = ref_phrase
            clarification_prompt_shape = clar_shape

    seeking = bool(
        correction_reask_followup_detected
        or lexical_pressure
        or contradiction_followup_detected
        or explanation_followup_detected
        or short_followup_anchor_detected
        or bare_what_ok
        or explanation_of_recent_anchor_followup
        or recent_reference_clarification_detected
        or (
            player_q
            and (pressure is not None or topic_overlap_follows_up)
        )
    )

    detected = bool(
        active_target_id
        and pair is not None
        and prior_substantive
        and same_interlocutor_followup
        and seeking
    )

    answer_pressure_reasons: List[str] = []
    if lexical_pressure:
        if fam.get("direct_answer_demand"):
            answer_pressure_reasons.append("family:direct_answer_demand")
        if fam.get("specificity_demand"):
            answer_pressure_reasons.append("family:specificity_demand")
        if fam.get("insufficiency_pressure"):
            answer_pressure_reasons.append("family:insufficiency_pressure")
        if fam.get("consequence_probe"):
            answer_pressure_reasons.append("family:consequence_probe")
    if contradiction_followup_detected:
        answer_pressure_reasons.append("family:contradiction_or_refusal_challenge")
    if explanation_followup_detected:
        answer_pressure_reasons.append("family:explanation_demand")
    if short_followup_anchor_detected:
        answer_pressure_reasons.append("path:short_interrogative_after_guarded")
    if bare_what_ok:
        answer_pressure_reasons.append("path:bare_what_with_anchor")
    if explanation_of_recent_anchor_followup:
        answer_pressure_reasons.append("path:explanation_of_recent_anchor_followup")
    if recent_reference_clarification_detected:
        answer_pressure_reasons.append("path:clarification_of_recent_reference")
    if correction_reask_followup_detected:
        answer_pressure_reasons.append("path:correction_reask_followup")
    if seeking and pressure is not None:
        answer_pressure_reasons.append("log:follow_up_pressure")
    if seeking and topic_overlap_follows_up:
        answer_pressure_reasons.append("anchor:topic_overlap_prior_player")
    if seeking and gm_overlap_signal:
        answer_pressure_reasons.append("anchor:gm_snippet_overlap")
    if seeking and prior_guarded:
        answer_pressure_reasons.append("anchor:prior_guarded_or_partial")

    answer_pressure_family: str | None = None
    if detected or seeking:
        if correction_reask_followup_detected:
            answer_pressure_family = "correction_reask_followup"
        elif explanation_of_recent_anchor_followup:
            answer_pressure_family = "explanation_of_recent_anchor_followup"
        elif recent_reference_clarification_detected:
            answer_pressure_family = "clarification_of_recent_reference"
        elif contradiction_followup_detected:
            answer_pressure_family = "contradiction_or_refusal_challenge"
        elif fam.get("direct_answer_demand"):
            answer_pressure_family = "direct_answer_demand"
        elif fam.get("specificity_demand"):
            answer_pressure_family = "specificity_demand"
        elif insufficiency_hit:
            answer_pressure_family = "insufficiency_pressure"
        elif explanation_followup_detected:
            answer_pressure_family = "explanation_demand"
        elif fam.get("consequence_probe"):
            answer_pressure_family = "consequence_probe"
        elif short_followup_anchor_detected or bare_what_ok:
            answer_pressure_family = "short_followup_anchor"
        elif player_q and (pressure is not None or topic_overlap_follows_up):
            answer_pressure_family = "direct_question_continuity"

    answer_pressure_anchor_kind: str | None = None
    if correction_reask_followup_detected:
        answer_pressure_anchor_kind = "explicit_question_reassertion"
    elif explanation_of_recent_anchor_followup:
        answer_pressure_anchor_kind = "npc_introduced_anchor_token"
    elif recent_reference_clarification_detected:
        answer_pressure_anchor_kind = "recent_reference_clarification"
    elif short_followup_anchor_detected:
        answer_pressure_anchor_kind = "short_interrogative_guarded_prior"
    elif bare_what_ok:
        answer_pressure_anchor_kind = "bare_what_anchored"
    elif contradiction_followup_detected and gm_loose_anchor:
        answer_pressure_anchor_kind = "challenge_with_gm_lexical_anchor"
    elif contradiction_followup_detected and prior_guarded:
        answer_pressure_anchor_kind = "challenge_with_prior_guarded"
    elif gm_overlap_signal:
        answer_pressure_anchor_kind = "gm_snippet_token_or_lexical"
    elif topic_overlap_follows_up:
        answer_pressure_anchor_kind = "prior_player_topic_overlap"
    elif pressure is not None:
        answer_pressure_anchor_kind = "log_press_continuity"
    elif lexical_pressure and not answer_pressure_anchor_kind:
        answer_pressure_anchor_kind = "phrase_family_strong"

    if not detected and not seeking:
        suppressed_because.append("not_question_or_answer_pressure")

    return {
        "answer_pressure_followup_detected": detected,
        "same_interlocutor_followup": same_interlocutor_followup,
        "lexical_pressure": lexical_pressure,
        "question_like": player_q,
        "prior_answer_substantive": prior_substantive,
        "topic_overlap_follows_up": topic_overlap_follows_up,
        "suppressed_because": suppressed_because,
        "answer_pressure_family": answer_pressure_family,
        "answer_pressure_anchor_kind": answer_pressure_anchor_kind,
        "contradiction_followup_detected": contradiction_followup_detected,
        "explanation_followup_detected": explanation_followup_detected,
        "insufficiency_followup_detected": insufficiency_followup_detected,
        "short_followup_anchor_detected": short_followup_anchor_detected,
        "answer_pressure_reasons": answer_pressure_reasons,
        "answer_pressure_suppressed_because": list(suppressed_because),
        "anchor_tokens_extracted": list(anchor_tokens_extracted),
        "anchor_token_matched": anchor_token_matched,
        "anchor_followup_detected": anchor_followup_detected,
        "explanation_of_recent_anchor_followup": explanation_of_recent_anchor_followup,
        "recent_reference_clarification_detected": recent_reference_clarification_detected,
        "recent_reference_kind": recent_reference_kind,
        "recent_reference_phrase_matched": recent_reference_phrase_matched,
        "clarification_prompt_shape": clarification_prompt_shape,
        "correction_reask_followup_detected": bool(correction_reask_followup_detected),
    }


def _is_answer_pressure_followup(
    player_input: str,
    recent_log_compact: List[Dict[str, Any]] | None,
    narration_obligations: Dict[str, Any],
    answer_completeness: Dict[str, Any] | None = None,
    *,
    session_view: Dict[str, Any] | None = None,
) -> bool:
    return bool(
        _answer_pressure_followup_details(
            player_input=player_input,
            recent_log_compact=recent_log_compact,
            narration_obligations=narration_obligations,
            session_view=session_view,
            answer_completeness=answer_completeness,
        ).get("answer_pressure_followup_detected")
    )


def question_detected_from_player_text(player_text: str) -> bool:
    """Deterministic direct-question detection for turn-local answer contracts."""
    t = str(player_text or "").strip()
    if not t:
        return False
    return bool(_QUESTION_LINE_PATTERN.search(t))


def _uncertainty_hint_suggests_partial(hint: Dict[str, Any] | None) -> bool:
    if not isinstance(hint, dict) or not hint:
        return False
    cat = str(hint.get("category") or "").strip()
    if cat:
        return True
    for k in ("unknown_edge", "known_edge", "next_lead"):
        v = hint.get(k)
        if isinstance(v, str) and v.strip():
            return True
    return False


def _resolution_suggests_gated_information(resolution: Dict[str, Any] | None) -> bool:
    res = resolution if isinstance(resolution, dict) else {}
    soc = res.get("social") if isinstance(res.get("social"), dict) else {}
    if soc.get("gated_information") is True:
        return True
    if str(soc.get("information_gate") or "").strip():
        return True
    return False


def build_response_delta_contract(
    *,
    player_input: str,
    recent_log_compact: List[Dict[str, Any]] | None,
    narration_obligations: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    answer_completeness: Dict[str, Any],
    uncertainty_hint: Dict[str, Any] | None = None,
    session_view: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Turn-local contract: when the player presses the same topic, require net-new value.

    Deterministic and recent-log-scoped. Uses `_compute_follow_up_pressure` for topic-continuity
    detection; strict-social (``suppress_non_social_emitters``) no longer disables this contract
    when :func:`_answer_pressure_followup_details` detects an answer-seeking follow-up.
    "Refinement" is an allowed delta kind when the reply narrows or sharpens an earlier answer
    (tighter identity, place, qualifier, or uncertainty boundary)—not when it only paraphrases.
    """
    obligations = narration_obligations if isinstance(narration_obligations, dict) else {}
    res = resolution if isinstance(resolution, dict) else {}
    sess = session_view if isinstance(session_view, dict) else {}
    ac = answer_completeness if isinstance(answer_completeness, dict) else {}

    social_lock = bool(obligations.get("suppress_non_social_emitters"))
    active_target_id = str(sess.get("active_interaction_target_id") or "").strip() or None
    answer_required = bool(ac.get("answer_required"))
    player_q = question_detected_from_player_text(player_input)

    ap_details = _answer_pressure_followup_details(
        player_input=player_input,
        recent_log_compact=list(recent_log_compact or []),
        narration_obligations=obligations,
        session_view=sess,
        answer_completeness=ac,
    )
    answer_pressure_followup = bool(ap_details.get("answer_pressure_followup_detected"))
    strict_social_answer_seek_override = bool(social_lock and answer_pressure_followup)
    social_lock_suppresses = bool(social_lock and not strict_social_answer_seek_override)

    explanatory_turn = bool(answer_required or player_q or answer_pressure_followup)

    res_kind = str(res.get("kind") or "").strip().lower()
    suppress_resolution_kind = res_kind in _RESPONSE_DELTA_SUPPRESS_RESOLUTION_KINDS
    must_advance_scene = bool(obligations.get("must_advance_scene"))
    opening_scene = bool(obligations.get("is_opening_scene"))

    pressure = _compute_follow_up_pressure(list(recent_log_compact or []), player_input)
    if pressure is None and answer_pressure_followup:
        pressure = _synthetic_follow_up_pressure_from_log(recent_log_compact, player_input)
    prior_snippet = str(pressure.get("previous_answer_snippet") or "").strip() if pressure else ""
    prior_substantive = bool(prior_snippet and _prior_answer_snippet_substantive(prior_snippet))
    hint_partial = _uncertainty_hint_suggests_partial(
        uncertainty_hint if isinstance(uncertainty_hint, dict) else None
    )

    fail_reasons: List[str] = []
    if pressure is None:
        fail_reasons.append("no_follow_up_pressure")
    if pressure is not None and not prior_substantive:
        fail_reasons.append("prior_answer_not_substantive")
    if not explanatory_turn:
        fail_reasons.append("not_answer_seeking_turn")
    if social_lock_suppresses:
        fail_reasons.append("social_lock")
    if suppress_resolution_kind:
        fail_reasons.append("resolution_kind_suppressed")
    if must_advance_scene:
        fail_reasons.append("scene_advancement_turn")
    if opening_scene:
        fail_reasons.append("opening_scene")

    activated = (
        pressure is not None
        and prior_substantive
        and explanatory_turn
        and not social_lock_suppresses
        and not suppress_resolution_kind
        and not must_advance_scene
        and not opening_scene
    )

    if activated and strict_social_answer_seek_override:
        trigger_source = "strict_social_answer_pressure"
    elif activated and player_q:
        trigger_source = "same_topic_direct_question"
    elif activated:
        trigger_source = "follow_up_pressure"
    else:
        trigger_source = "none"

    exp_shape_ac = str(ac.get("expected_answer_shape") or "").strip()
    if not activated:
        expected_delta_shape = "none"
    elif exp_shape_ac == "bounded_partial" or hint_partial:
        expected_delta_shape = "bounded_partial_with_delta"
    else:
        expected_delta_shape = "direct_delta"

    topic_tokens: List[str] = list(pressure.get("topic_tokens") or []) if pressure else []
    press_depth = int(pressure.get("press_depth") or 0) if pressure else 0
    overlap_ratio = pressure.get("overlap_ratio") if pressure else None
    if overlap_ratio is not None and isinstance(overlap_ratio, (int, float)):
        overlap_ratio = float(overlap_ratio)
    else:
        overlap_ratio = None

    prev_in = pressure.get("previous_player_input") if pressure else None
    prev_ans = pressure.get("previous_answer_snippet") if pressure else None

    trace: Dict[str, Any] = {
        "question_detected_from_player_text": bool(player_q),
        "follow_up_pressure_detected": pressure is not None,
        "follow_up_press_depth": press_depth,
        "follow_up_overlap_ratio": overlap_ratio,
        "prior_answer_available": bool(prior_substantive),
        "answer_completeness_required": bool(answer_required),
        "social_lock": bool(social_lock),
        "active_target_id": active_target_id,
        "answer_pressure_followup_detected": answer_pressure_followup,
        "strict_social_answer_seek_override": strict_social_answer_seek_override,
        "same_interlocutor_followup": bool(ap_details.get("same_interlocutor_followup")),
        "answer_pressure_suppressed_because": list(ap_details.get("suppressed_because") or []),
        "answer_pressure_family": ap_details.get("answer_pressure_family"),
        "answer_pressure_anchor_kind": ap_details.get("answer_pressure_anchor_kind"),
        "contradiction_followup_detected": bool(ap_details.get("contradiction_followup_detected")),
        "explanation_followup_detected": bool(ap_details.get("explanation_followup_detected")),
        "insufficiency_followup_detected": bool(ap_details.get("insufficiency_followup_detected")),
        "short_followup_anchor_detected": bool(ap_details.get("short_followup_anchor_detected")),
        "anchor_tokens_extracted": list(ap_details.get("anchor_tokens_extracted") or []),
        "anchor_token_matched": ap_details.get("anchor_token_matched"),
        "anchor_followup_detected": bool(ap_details.get("anchor_followup_detected")),
        "explanation_of_recent_anchor_followup": bool(ap_details.get("explanation_of_recent_anchor_followup")),
        "recent_reference_clarification_detected": bool(
            ap_details.get("recent_reference_clarification_detected")
        ),
        "recent_reference_kind": ap_details.get("recent_reference_kind"),
        "recent_reference_phrase_matched": ap_details.get("recent_reference_phrase_matched"),
        "clarification_prompt_shape": ap_details.get("clarification_prompt_shape"),
        "correction_reask_followup_detected": bool(ap_details.get("correction_reask_followup_detected")),
        "answer_pressure_reasons": list(ap_details.get("answer_pressure_reasons") or []),
        "trigger_source": trigger_source,
        "resolution_kind": res_kind or None,
        "uncertainty_suggests_partial": bool(hint_partial),
        "suppressed_because": list(fail_reasons) if fail_reasons else [],
    }

    allowed_kinds = list(_RESPONSE_DELTA_ALLOWED_KINDS) if activated else []

    return {
        "enabled": bool(activated),
        "delta_required": bool(activated),
        "delta_must_come_early": bool(activated),
        "trigger_source": trigger_source,
        "topic_tokens": topic_tokens,
        "press_depth": press_depth,
        "previous_player_input": (str(prev_in).strip() or None) if prev_in else None,
        "previous_answer_snippet": (str(prev_ans).strip() or None) if prev_ans else None,
        "overlap_ratio": overlap_ratio,
        "allowed_delta_kinds": allowed_kinds,
        "forbid_semantic_restatement": bool(activated),
        "forbid_repackaged_nonanswer": bool(activated),
        "allow_short_bridge_before_delta": bool(activated),
        "require_delta_when_answer_required": bool(activated and answer_required),
        "expected_delta_shape": expected_delta_shape,
        "trace": trace,
    }


def build_answer_completeness_contract(
    *,
    player_input: str,
    narration_obligations: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session_view: Dict[str, Any] | None,
    uncertainty_hint: Dict[str, Any] | None,
    allow_partial_answer: bool = True,
    recent_log_compact: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Derive an inspectable, turn-local answer contract from engine state only."""
    obligations = narration_obligations if isinstance(narration_obligations, dict) else {}
    sess = session_view if isinstance(session_view, dict) else {}
    res = resolution if isinstance(resolution, dict) else {}

    player_q = question_detected_from_player_text(player_input)
    social_lock = bool(obligations.get("suppress_non_social_emitters"))
    npc_expected = bool(obligations.get("active_npc_reply_expected"))
    reply_kind = obligations.get("active_npc_reply_kind")
    reply_kind_str = str(reply_kind).strip().lower() if reply_kind is not None else ""
    if reply_kind_str not in NPC_REPLY_KIND_VALUES:
        reply_kind_str = ""

    refusal_turn = reply_kind_str == "refusal"
    substantive_npc_qa = npc_expected and reply_kind_str in ("answer", "explanation")
    should_npc = bool(obligations.get("should_answer_active_npc"))

    ap_details = _answer_pressure_followup_details(
        player_input=player_input,
        recent_log_compact=list(recent_log_compact or []),
        narration_obligations=obligations,
        session_view=sess,
        answer_completeness=None,
    )
    answer_pressure_seek = bool(ap_details.get("answer_pressure_followup_detected"))

    if refusal_turn:
        answer_required = True
    elif player_q:
        answer_required = True
    elif answer_pressure_seek:
        answer_required = True
    elif substantive_npc_qa:
        answer_required = True
    else:
        answer_required = False

    hint_partial = _uncertainty_hint_suggests_partial(uncertainty_hint)
    gated = _resolution_suggests_gated_information(res)

    partial_permitted = bool(answer_required and not refusal_turn and allow_partial_answer)
    allowed_reasons: List[str] = list(ANSWER_COMPLETENESS_PARTIAL_REASONS) if partial_permitted else []

    if refusal_turn:
        expected_shape = "refusal_with_reason"
    elif answer_required and (hint_partial or gated):
        expected_shape = "bounded_partial"
    elif answer_required:
        expected_shape = "direct"
    else:
        expected_shape = "direct"

    active_target_id = str(sess.get("active_interaction_target_id") or "").strip()
    if social_lock or (
        active_target_id
        and (should_npc or npc_expected)
        and answer_required
    ):
        expected_voice = "npc"
    elif answer_required:
        expected_voice = "narrator"
    else:
        expected_voice = "either"

    if refusal_turn:
        trigger_source = "active_npc_refusal"
    elif player_q:
        trigger_source = "player_direct_question"
    elif answer_pressure_seek:
        trigger_source = "answer_pressure_followup"
    elif substantive_npc_qa:
        trigger_source = "active_npc_answer_obligation"
    elif npc_expected:
        trigger_source = "active_npc_exchange"
    else:
        trigger_source = "none"

    enabled = bool(answer_required)
    answer_must_come_first = bool(answer_required)
    forbid_deflection = bool(answer_required)
    forbid_generic_nonanswer = bool(answer_required)
    require_concrete_payload = bool(answer_required)
    concrete_kinds = list(CONCRETE_PAYLOAD_KINDS) if require_concrete_payload else []

    trace = {
        "trigger_source": trigger_source,
        "active_target_id": active_target_id or None,
        "active_npc_reply_kind": reply_kind_str or None,
        "question_detected_from_player_text": bool(player_q),
        "answer_pressure_followup_detected": answer_pressure_seek,
        "strict_social_answer_seek_override": bool(social_lock and answer_pressure_seek),
        "same_interlocutor_followup": bool(ap_details.get("same_interlocutor_followup")),
        "answer_pressure_suppressed_because": list(ap_details.get("suppressed_because") or []),
        "answer_pressure_family": ap_details.get("answer_pressure_family"),
        "answer_pressure_anchor_kind": ap_details.get("answer_pressure_anchor_kind"),
        "contradiction_followup_detected": bool(ap_details.get("contradiction_followup_detected")),
        "explanation_followup_detected": bool(ap_details.get("explanation_followup_detected")),
        "insufficiency_followup_detected": bool(ap_details.get("insufficiency_followup_detected")),
        "short_followup_anchor_detected": bool(ap_details.get("short_followup_anchor_detected")),
        "anchor_tokens_extracted": list(ap_details.get("anchor_tokens_extracted") or []),
        "anchor_token_matched": ap_details.get("anchor_token_matched"),
        "anchor_followup_detected": bool(ap_details.get("anchor_followup_detected")),
        "explanation_of_recent_anchor_followup": bool(ap_details.get("explanation_of_recent_anchor_followup")),
        "recent_reference_clarification_detected": bool(
            ap_details.get("recent_reference_clarification_detected")
        ),
        "recent_reference_kind": ap_details.get("recent_reference_kind"),
        "recent_reference_phrase_matched": ap_details.get("recent_reference_phrase_matched"),
        "clarification_prompt_shape": ap_details.get("clarification_prompt_shape"),
        "correction_reask_followup_detected": bool(ap_details.get("correction_reask_followup_detected")),
        "answer_pressure_reasons": list(ap_details.get("answer_pressure_reasons") or []),
        "partial_answer_permitted": bool(partial_permitted),
    }

    if expected_voice not in EXPECTED_ANSWER_VOICE:
        expected_voice = "either"
    if expected_shape not in EXPECTED_ANSWER_SHAPE:
        expected_shape = "direct"

    return {
        "enabled": enabled,
        "trace": trace,
        "player_direct_question": bool(player_q),
        "answer_required": bool(answer_required),
        "answer_must_come_first": answer_must_come_first,
        "expected_voice": expected_voice,
        "expected_answer_shape": expected_shape,
        "allowed_partial_reasons": allowed_reasons,
        "forbid_deflection": forbid_deflection,
        "forbid_generic_nonanswer": forbid_generic_nonanswer,
        "require_concrete_payload": require_concrete_payload,
        "concrete_payload_any_of": concrete_kinds,
    }


def build_response_policy(
    *,
    narration_obligations: Dict[str, Any] | None = None,
    player_text: str | None = None,
    resolution: Dict[str, Any] | None = None,
    session_view: Dict[str, Any] | None = None,
    uncertainty_hint: Dict[str, Any] | None = None,
    recent_log_compact: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build the inspectable response policy for the current turn.

    This keeps the precedence ladder explicit in one place so prompt assembly
    and post-generation enforcement can share it instead of re-encoding order.
    """
    obligations = narration_obligations if isinstance(narration_obligations, dict) else {}
    suppress = bool(obligations.get("suppress_non_social_emitters"))
    answer_completeness = build_answer_completeness_contract(
        player_input=str(player_text or ""),
        narration_obligations=obligations,
        resolution=resolution,
        session_view=session_view if isinstance(session_view, dict) else {},
        uncertainty_hint=uncertainty_hint,
        allow_partial_answer=True,
        recent_log_compact=list(recent_log_compact or []),
    )
    response_delta = build_response_delta_contract(
        player_input=str(player_text or ""),
        recent_log_compact=recent_log_compact,
        narration_obligations=obligations,
        resolution=resolution,
        answer_completeness=answer_completeness,
        uncertainty_hint=uncertainty_hint,
        session_view=session_view if isinstance(session_view, dict) else None,
    )
    return {
        "rule_priority_order": [label for _, label in RESPONSE_RULE_PRIORITY],
        "must_answer": True,
        "forbid_state_invention": True,
        "forbid_secret_leak": True,
        "allow_partial_answer": True,
        "response_delta": response_delta,
        "diegetic_only": True,
        "prefer_scene_momentum": not suppress,
        "prefer_specificity": True,
        "no_validator_voice": {
            "enabled": True,
            "applies_to": "standard_narration",
            "rule": NO_VALIDATOR_VOICE_RULE,
            "prohibited_perspectives": list(NO_VALIDATOR_VOICE_PROHIBITIONS),
            "rules_explanation_only_in": ["oc", "adjudication"],
        },
        "scene_momentum_due": False if suppress else bool(obligations.get("scene_momentum_due")),
        "uncertainty": {
            "enabled": not suppress,
            "categories": list(UNCERTAINTY_CATEGORIES),
            "sources": list(UNCERTAINTY_SOURCES),
            "answer_shape": list(UNCERTAINTY_ANSWER_SHAPE),
            "context_inputs": ["turn_context", "speaker", "scene_snapshot"],
        },
        "answer_completeness": answer_completeness,
    }


def _tone_escalation_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of tone_escalation contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    reasons = c.get("justification_reasons")
    if not isinstance(reasons, list):
        reasons = []
    return {
        "enabled": c.get("enabled"),
        "active_speaker_id": c.get("active_speaker_id"),
        "base_tone": c.get("base_tone"),
        "max_allowed_tone": c.get("max_allowed_tone"),
        "allow_guarded_refusal": c.get("allow_guarded_refusal"),
        "allow_verbal_pressure": c.get("allow_verbal_pressure"),
        "allow_explicit_threat": c.get("allow_explicit_threat"),
        "allow_physical_hostility": c.get("allow_physical_hostility"),
        "allow_combat_initiation": c.get("allow_combat_initiation"),
        "justification_reasons": [str(x) for x in reasons if isinstance(x, str)],
    }


def _context_separation_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of context_separation contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    df = c.get("debug_flags")
    if not isinstance(df, dict):
        df = {}
    pt = c.get("primary_topics")
    if not isinstance(pt, tuple):
        pt = ()
    return {
        "enabled": c.get("enabled"),
        "interaction_kind": c.get("interaction_kind"),
        "pressure_focus_allowed": df.get("pressure_focus_allowed"),
        "player_seeks_world_danger_info": df.get("player_seeks_world_danger_info"),
        "scene_summary_crisis": df.get("scene_summary_crisis"),
        "interaction_kind_worldish": df.get("interaction_kind_worldish"),
        "authoritative_or_consequence_relevant": df.get("authoritative_or_consequence_relevant"),
        "primary_topic_count": len(pt),
        "ambient_pressure_topic_count": len(c.get("ambient_pressure_topics") or ()),
    }


def _player_facing_narration_purity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of player_facing_narration_purity contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    return {
        "enabled": c.get("enabled"),
        "diegetic_only": c.get("diegetic_only"),
        "interaction_kind": c.get("interaction_kind"),
        "forbid_scaffold_headers": c.get("forbid_scaffold_headers"),
        "forbid_coaching_language": c.get("forbid_coaching_language"),
        "forbid_engine_choice_framing": c.get("forbid_engine_choice_framing"),
        "forbid_non_diegetic_action_prompting": c.get("forbid_non_diegetic_action_prompting"),
    }


def _social_response_structure_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of social_response_structure contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    return {
        "enabled": c.get("enabled"),
        "applies_to_response_type": c.get("applies_to_response_type"),
        "require_spoken_dialogue_shape": c.get("require_spoken_dialogue_shape"),
        "max_contiguous_expository_lines": c.get("max_contiguous_expository_lines"),
        "max_dialogue_paragraphs_before_break": c.get("max_dialogue_paragraphs_before_break"),
        "prefer_single_speaker_turn": c.get("prefer_single_speaker_turn"),
        "forbid_bulleted_or_list_like_dialogue": c.get("forbid_bulleted_or_list_like_dialogue"),
    }


def _narrative_authenticity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of narrative_authenticity for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    tr = c.get("trace") if isinstance(c.get("trace"), Mapping) else {}
    rr = c.get("rumor_realism") if isinstance(c.get("rumor_realism"), Mapping) else {}
    return {
        "enabled": c.get("enabled"),
        "version": c.get("version"),
        "mode": c.get("mode"),
        "response_delta_contract_active": tr.get("response_delta_contract_active"),
        "topic_follow_up_active": tr.get("topic_follow_up_active"),
        "dialogue_shape_expected": tr.get("dialogue_shape_expected"),
        "rumor_realism_enabled": rr.get("enabled"),
        "rumor_turn_active": tr.get("rumor_turn_active"),
        "rumor_trigger_spans": list(tr.get("rumor_trigger_spans") or [])[:6],
    }


def _interaction_continuity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of interaction_continuity contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    dbg = c.get("debug") if isinstance(c.get("debug"), dict) else {}
    return {
        "enabled": c.get("enabled"),
        "continuity_strength": c.get("continuity_strength"),
        "anchored_interlocutor_id": c.get("anchored_interlocutor_id"),
        "drop_interlocutor_requires_explicit_break": c.get("drop_interlocutor_requires_explicit_break"),
        "speaker_switch_requires_explicit_cue": c.get("speaker_switch_requires_explicit_cue"),
        "source_of_anchor": dbg.get("source_of_anchor"),
        "scene_scope_validated": dbg.get("scene_scope_validated"),
    }


def canonical_interaction_target_npc_id(session: Dict[str, Any] | None, raw_target_id: str | None) -> str:
    """Map session interaction target to promoted world NPC id when ``promoted_actor_npc_map`` binds it."""
    raw = str(raw_target_id or "").strip()
    if not raw or not isinstance(session, dict):
        return raw
    st = get_scene_state(session)
    pmap = st.get("promoted_actor_npc_map")
    if not isinstance(pmap, dict):
        return raw
    mapped = pmap.get(raw)
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw


def _resolve_active_interaction_target_name(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
    *,
    npc_id: str | None = None,
) -> str | None:
    """Resolve interaction target (or explicit *npc_id*) to a display name; prefers world row, then in-scene match."""
    tid = str(npc_id or "").strip()
    if not tid:
        interaction_ctx = session.get('interaction_context') or {}
        if not isinstance(interaction_ctx, dict):
            return None
        tid = str(interaction_ctx.get('active_interaction_target_id') or '').strip()
    if not tid:
        return None

    w = world if isinstance(world, dict) else {}
    row = get_world_npc_by_id(w, tid)
    if isinstance(row, dict):
        nm = str(row.get("name") or "").strip()
        if nm:
            return nm

    scene_id = str(public_scene.get('id') or '').strip()
    npcs = w.get('npcs') or []
    if not isinstance(npcs, list):
        return None

    target_id_low = tid.lower()
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get('id') or '').strip()
        if not nid or nid.lower() != target_id_low:
            continue
        npc_loc = str(npc.get('location') or npc.get('scene_id') or '').strip()
        if scene_id and npc_loc != scene_id:
            continue
        npc_name = str(npc.get('name') or '').strip()
        return npc_name or None
    return None


def build_active_interlocutor_export(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> Dict[str, Any] | None:
    """Engine-authored active speaker profile for prompts (canonical ``npc_id`` when promoted)."""
    if not isinstance(session, dict):
        return None
    ic = session.get("interaction_context") or {}
    if not isinstance(ic, dict):
        return None
    raw = str(ic.get("active_interaction_target_id") or "").strip()
    if not raw:
        return None
    npc_id = canonical_interaction_target_npc_id(session, raw)
    w = world if isinstance(world, dict) else {}
    npc = get_world_npc_by_id(w, npc_id)
    name = _resolve_active_interaction_target_name(session, w, public_scene, npc_id=npc_id) or ""
    base: Dict[str, Any] = {
        "npc_id": npc_id,
        "raw_interaction_target_id": raw,
        "display_name": name,
    }
    if not isinstance(npc, dict):
        return {**base, "origin_kind": None, "stance_toward_player": None, "knowledge_scope": [],
                "information_reliability": None, "affiliation": None, "current_agenda": None,
                "promoted_from_actor_id": None}
    return {
        **base,
        "origin_kind": str(npc.get("origin_kind") or "").strip() or None,
        "stance_toward_player": str(npc.get("stance_toward_player") or "").strip() or None,
        "knowledge_scope": list(npc.get("knowledge_scope") or []) if isinstance(npc.get("knowledge_scope"), list) else [],
        "information_reliability": str(npc.get("information_reliability") or "").strip() or None,
        "affiliation": str(npc.get("affiliation") or "").strip() or None,
        "current_agenda": str(npc.get("current_agenda") or "").strip() or None,
        "promoted_from_actor_id": str(npc.get("promoted_from_actor_id") or "").strip() or None,
    }


def build_social_interlocutor_profile(interlocutor: Dict[str, Any] | None) -> Dict[str, Any]:
    """Deterministic ``social_context.interlocutor_profile`` payload (engine fields only)."""
    if not isinstance(interlocutor, dict) or not str(interlocutor.get("npc_id") or "").strip():
        return {
            "npc_is_promoted": False,
            "stance": None,
            "reliability": None,
            "knowledge_scope": [],
            "agenda": None,
            "affiliation": None,
        }
    pfa = str(interlocutor.get("promoted_from_actor_id") or "").strip()
    ks = interlocutor.get("knowledge_scope")
    scope_list = [str(x).strip() for x in ks if isinstance(x, str) and str(x).strip()] if isinstance(ks, list) else []
    return {
        "npc_is_promoted": bool(pfa),
        "stance": interlocutor.get("stance_toward_player"),
        "reliability": interlocutor.get("information_reliability"),
        "knowledge_scope": scope_list,
        "agenda": interlocutor.get("current_agenda"),
        "affiliation": interlocutor.get("affiliation"),
    }


def deterministic_interlocutor_answer_style_hints(
    interlocutor: Dict[str, Any] | None,
    *,
    scene_id: str,
) -> List[str]:
    """Fixed strings derived only from engine reliability + knowledge_scope (+ scene id)."""
    if not isinstance(interlocutor, dict) or not str(interlocutor.get("npc_id") or "").strip():
        return []
    rel = str(interlocutor.get("information_reliability") or "").strip().lower()
    if rel not in ("truthful", "partial", "misleading"):
        rel = "partial"
    ks_raw = interlocutor.get("knowledge_scope")
    scopes = sorted(
        {str(x).strip() for x in ks_raw if isinstance(x, str) and str(x).strip()}
        if isinstance(ks_raw, list)
        else set()
    )
    sid = str(scene_id or "").strip()
    scope_note = (
        f"Engine knowledge_scope tokens (direct professional/local anchors): {', '.join(scopes)}."
        if scopes
        else "Engine knowledge_scope is empty: treat direct private knowledge as narrow unless grounded in visible role, scene, or prior established exchanges."
    )
    out = [
        "INTERLOCUTOR KNOWLEDGE GATE (engine): Answer as this specific NPC. "
        "Use knowledge_scope as the boundary for what they know firsthand. "
        "Topics outside those anchors must be hearsay, uncertainty, deflection, or an honest 'I don't know'—not omniscient facts.",
        scope_note,
    ]
    if sid:
        needle = f"scene:{sid.lower()}"
        if any(s.lower() == needle for s in scopes):
            out.append(
                f"This NPC's scope includes the current scene token ({needle}): patrol layout, gate procedures, and crowd-level "
                "local knowledge may be stated directly when consistent with reliability."
            )
    if rel == "truthful":
        out.append(
            "INFORMATION_RELIABILITY truthful (engine): Within knowledge_scope, state what they know directly and clearly; "
            "do not add hidden omniscient details outside scope."
        )
    elif rel == "partial":
        out.append(
            "INFORMATION_RELIABILITY partial (engine): Within knowledge_scope, answers are incomplete, selective, or hedged; "
            "do not present full certainty or insider completeness they would not have."
        )
    else:
        out.append(
            "INFORMATION_RELIABILITY misleading (engine): Within knowledge_scope, replies may distort, omit, or deflect; "
            "lies stay plausible for this person—never omniscient fabrication or perfect hidden plots."
        )
    ok_origin = str(interlocutor.get("origin_kind") or "").strip().lower() in {"scene_actor", "crowd_actor"}
    has_pfa = bool(str(interlocutor.get("promoted_from_actor_id") or "").strip())
    if ok_origin and not has_pfa:
        out.append(
            "INCIDENTAL SCENE ACTOR (engine row without promotion linkage): keep characterization to this scene's role; "
            "do not invent a recurring named persona, secret dossier, or stable off-screen biography unless engine state already provides it."
        )
    return out


def _compress_campaign(campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize campaign to essential narration context. No hidden/secret fields."""
    if not campaign or not isinstance(campaign, dict):
        return {'title': '', 'premise': '', 'character_role': '', 'gm_guidance': [], 'world_pressures': []}

    gm_guidance = campaign.get('gm_guidance') or []
    if isinstance(gm_guidance, list):
        gm_guidance = gm_guidance[:MAX_GM_GUIDANCE]
    else:
        gm_guidance = []

    world_pressures = campaign.get('world_pressures') or []
    if isinstance(world_pressures, list):
        world_pressures = world_pressures[:MAX_WORLD_PRESSURES]
    else:
        world_pressures = []

    return {
        'title': str(campaign.get('title', '') or '')[:200],
        'premise': str(campaign.get('premise', '') or '')[:500],
        'tone': str(campaign.get('tone', '') or '')[:200],
        'character_role': str(campaign.get('character_role', '') or '')[:300],
        'gm_guidance': gm_guidance,
        'world_pressures': world_pressures,
        'magic_style': str(campaign.get('magic_style', '') or '')[:300],
    }


def _compress_world(world: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize world: world_state + recent events + faction names. No full dumps."""
    if not world or not isinstance(world, dict):
        return {'world_state': {'flags': {}, 'counters': {}, 'clocks_summary': []}, 'recent_events': [], 'faction_names': []}

    ws = world.get('world_state') or {}
    if not isinstance(ws, dict):
        ws = {}
    flags = {k: v for k, v in (ws.get('flags') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    counters = {k: v for k, v in (ws.get('counters') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    clocks_raw = ws.get('clocks') or {}
    clocks_summary = [
        f"{k}: {int(c.get('progress', 0))}/{int(c.get('max', 10))}"
        for k, c in clocks_raw.items()
        if isinstance(k, str) and not k.startswith('_') and isinstance(c, dict)
    ]
    world_state_view = {'flags': flags, 'counters': counters, 'clocks_summary': clocks_summary}

    event_log = world.get('event_log') or []
    recent_events: List[str] = []
    if isinstance(event_log, list):
        for entry in event_log[-MAX_RECENT_EVENTS:]:
            if isinstance(entry, dict) and isinstance(entry.get('text'), str):
                recent_events.append(entry['text'][:200])
            elif isinstance(entry, str):
                recent_events.append(entry[:200])

    factions = world.get('factions') or []
    faction_names: List[str] = []
    if isinstance(factions, list):
        for f in factions[:10]:
            if isinstance(f, dict) and isinstance(f.get('name'), str):
                faction_names.append(f['name'])

    return {
        'world_state': world_state_view,
        'recent_events': recent_events,
        'faction_names': faction_names,
    }


def _compress_session(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> Dict[str, Any]:
    """Summarize session to minimal fields. No chat_history, debug_traces, etc."""
    if not session or not isinstance(session, dict):
        return {'active_scene_id': '', 'response_mode': 'standard', 'turn_counter': 0}

    visited = session.get('visited_scene_ids') or []
    visited_count = len(visited) if isinstance(visited, list) else 0
    interaction_ctx = session.get('interaction_context') or {}
    if not isinstance(interaction_ctx, dict):
        interaction_ctx = {}

    active_target = interaction_ctx.get('active_interaction_target_id')
    raw_tgt = str(active_target).strip() if isinstance(active_target, str) and active_target.strip() else None
    canonical_tgt = canonical_interaction_target_npc_id(session, raw_tgt) if raw_tgt else None
    eff_tgt = canonical_tgt or raw_tgt
    active_kind = interaction_ctx.get('active_interaction_kind')
    interaction_mode = interaction_ctx.get('interaction_mode')
    engagement_level = interaction_ctx.get('engagement_level')
    convo_privacy = interaction_ctx.get('conversation_privacy')
    position_ctx = interaction_ctx.get('player_position_context')

    return {
        'active_scene_id': str(session.get('active_scene_id', '') or ''),
        'response_mode': str(session.get('response_mode', 'standard') or 'standard'),
        'turn_counter': int(session.get('turn_counter', 0) or 0),
        'visited_scene_count': visited_count,
        'active_interaction_target_id': eff_tgt,
        'active_interaction_target_name': _resolve_active_interaction_target_name(session, world, public_scene, npc_id=eff_tgt) if eff_tgt else None,
        'active_interaction_kind': str(active_kind).strip() if isinstance(active_kind, str) and active_kind.strip() else None,
        'interaction_mode': str(interaction_mode).strip() if isinstance(interaction_mode, str) and interaction_mode.strip() else 'none',
        'engagement_level': str(engagement_level).strip() if isinstance(engagement_level, str) and engagement_level.strip() else 'none',
        'conversation_privacy': str(convo_privacy).strip() if isinstance(convo_privacy, str) and convo_privacy.strip() else None,
        'player_position_context': str(position_ctx).strip() if isinstance(position_ctx, str) and position_ctx.strip() else None,
    }


def _compress_recent_log(recent_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Trim log entries to player input + short GM snippet. Take last N only."""
    if not recent_log or not isinstance(recent_log, list):
        return []

    trimmed: List[Dict[str, Any]] = []
    for entry in recent_log[-MAX_RECENT_LOG:]:
        if not isinstance(entry, dict):
            continue
        log_meta = entry.get('log_meta') or {}
        player_input = str(log_meta.get('player_input', '') or entry.get('request', {}).get('chat', '') or '')[:300]
        gm_output = entry.get('gm_output') or {}
        gm_text = gm_output.get('player_facing_text', '') if isinstance(gm_output, dict) else ''
        if isinstance(gm_text, str):
            gm_snippet = gm_text[:MAX_LOG_ENTRY_SNIPPET]
        else:
            gm_snippet = ''
        trimmed.append({'player_input': player_input, 'gm_snippet': gm_snippet})
    return trimmed


def _infer_log_entry_source_turn(
    entry: Dict[str, Any],
    *,
    index_in_window: int,
    window_len: int,
    current_turn: int,
) -> int | None:
    """Best-effort turn index for a log entry; falls back to position vs session turn_counter."""
    lm = entry.get("log_meta") if isinstance(entry.get("log_meta"), dict) else {}
    for key in ("turn_counter", "turn", "session_turn_counter"):
        raw = lm.get(key)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    res = entry.get("resolution")
    if isinstance(res, dict):
        for key in ("turn_counter", "turn"):
            raw = res.get(key)
            if raw is not None:
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    pass
    if current_turn > 0 and window_len > 0:
        return int(current_turn) - int(window_len) + int(index_in_window)
    return None


def _memory_window_title_topic_tokens(title: str) -> List[str]:
    """Conservative tokens from a lead/title string (no invented entities)."""
    raw = str(title or "").strip().lower()
    if not raw:
        return []
    toks = [m.group(0).lower() for m in _CONV_MEM_TITLE_TOPIC_RE.finditer(raw)]
    out: List[str] = []
    seen: Set[str] = set()
    for t in toks:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= 8:
            break
    return out


def _memory_window_focus_topic_tokens(active_topic_anchor: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(active_topic_anchor, Mapping):
        return []
    focus = str(active_topic_anchor.get("focus_fragment") or "").strip()
    if not focus:
        return []
    return _memory_window_title_topic_tokens(focus)


def _collect_interlocutor_lead_candidate_rows(
    interlocutor_lead_context: Mapping[str, Any] | None,
    *,
    max_rows: int,
) -> List[Dict[str, Any]]:
    if not isinstance(interlocutor_lead_context, Mapping):
        return []
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for key in ("introduced_by_npc", "unacknowledged_from_npc", "recently_discussed_with_npc"):
        part = interlocutor_lead_context.get(key)
        if not isinstance(part, list):
            continue
        for row in part:
            if not isinstance(row, dict):
                continue
            lid = str(row.get("lead_id") or "").strip()
            if lid:
                if lid in seen:
                    continue
                seen.add(lid)
            out.append(row)
            if len(out) >= max_rows:
                return out
    return out


def _assemble_conversational_memory_candidates(
    *,
    recent_log_for_prompt: List[Dict[str, Any]],
    current_turn: int,
    runtime_compressed: Mapping[str, Any] | None,
    interlocutor_lead_context: Mapping[str, Any] | None,
    active_npc_id: str | None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build selector candidates + parallel extras (for legacy recent_log shape). Order: recent turns, leads, runtime."""
    candidates: List[Dict[str, Any]] = []
    extras: List[Dict[str, Any]] = []

    entries = (
        recent_log_for_prompt[-MAX_RECENT_LOG:]
        if isinstance(recent_log_for_prompt, list) and recent_log_for_prompt
        else []
    )
    window_len = len(entries)
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        log_meta = entry.get("log_meta") if isinstance(entry.get("log_meta"), dict) else {}
        player_input = str(log_meta.get("player_input", "") or entry.get("request", {}).get("chat", "") or "")[:300]
        gm_output = entry.get("gm_output") or {}
        gm_text = gm_output.get("player_facing_text", "") if isinstance(gm_output, dict) else ""
        gm_snippet = str(gm_text)[:MAX_LOG_ENTRY_SNIPPET] if isinstance(gm_text, str) else ""
        st = _infer_log_entry_source_turn(
            entry,
            index_in_window=idx,
            window_len=window_len,
            current_turn=current_turn,
        )
        text = f"P: {player_input} | G: {gm_snippet}"
        if len(text) > 520:
            text = text[:520]
        candidates.append(
            {
                "kind": "recent_turn",
                "entity_ids": [],
                "topic_tokens": [],
                "source_turn": st,
                "text": text,
            }
        )
        extras.append({"player_input": player_input, "gm_snippet": gm_snippet})

    npc_id = str(active_npc_id or "").strip()
    for row in _collect_interlocutor_lead_candidate_rows(
        interlocutor_lead_context,
        max_rows=8,
    ):
        title = str(row.get("title") or "").strip()
        lid = str(row.get("lead_id") or "").strip()
        disc = str(row.get("disclosure_level") or "").strip().lower() or "hinted"
        st_raw = row.get("last_discussed_turn")
        st: int | None
        try:
            st = int(st_raw) if st_raw is not None else None
        except (TypeError, ValueError):
            st = None
        if st is None:
            ft = row.get("first_discussed_turn")
            try:
                st = int(ft) if ft is not None else None
            except (TypeError, ValueError):
                st = None
        text = f"Lead {lid}: {title} ({disc})" if lid else f"Lead: {title} ({disc})"
        ent: List[str] = [npc_id] if npc_id else []
        candidates.append(
            {
                "kind": "npc_lead_discussion",
                "entity_ids": ent,
                "topic_tokens": _memory_window_title_topic_tokens(title),
                "source_turn": st,
                "text": text[:520],
            }
        )
        extras.append({"player_input": "", "gm_snippet": text})

    rt = runtime_compressed if isinstance(runtime_compressed, Mapping) else {}
    raw_ctx = rt.get("recent_contextual_leads")
    if isinstance(raw_ctx, list):
        for item in raw_ctx[-MAX_RECENT_CONTEXTUAL_LEADS:]:
            if not isinstance(item, dict):
                continue
            subject = str(item.get("subject") or "").strip()
            key = str(item.get("key") or "").strip()
            if not subject and not key:
                continue
            try:
                lt = int(item.get("last_turn", 0) or 0)
            except (TypeError, ValueError):
                lt = 0
            st2: int | None = lt if lt > 0 else None
            text2 = f"{subject} [{key}]".strip() if key else subject
            candidates.append(
                {
                    "kind": "contextual_thread",
                    "entity_ids": [],
                    "topic_tokens": _memory_window_title_topic_tokens(subject),
                    "source_turn": st2,
                    "text": text2[:520],
                }
            )
            extras.append({"player_input": "", "gm_snippet": text2[:MAX_LOG_ENTRY_SNIPPET]})

    while len(candidates) > CONVERSATIONAL_MEMORY_MAX_CANDIDATES:
        candidates.pop()
        extras.pop()

    return candidates, extras


def _recent_log_payload_from_selected_memory(
    selected: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    extras: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Map selected items to legacy recent_log rows (player_input + gm_snippet)."""
    out: List[Dict[str, Any]] = []
    for sel in selected:
        matched_i: int | None = None
        for i, c in enumerate(candidates):
            if (
                c.get("kind") == sel.get("kind")
                and c.get("source_turn") == sel.get("source_turn")
                and c.get("text") == sel.get("text")
            ):
                matched_i = i
                break
        if matched_i is None:
            out.append(
                {
                    "player_input": "",
                    "gm_snippet": str(sel.get("text") or "")[:MAX_LOG_ENTRY_SNIPPET],
                }
            )
            continue
        ex = extras[matched_i] if matched_i < len(extras) else {}
        if not isinstance(ex, dict):
            ex = {}
        pi = str(ex.get("player_input") or "")
        gm = str(ex.get("gm_snippet") or "")
        out.append({"player_input": pi, "gm_snippet": gm})
    return out


def _compress_combat(combat: Dict[str, Any]) -> Dict[str, Any] | None:
    """Include combat only when active; otherwise minimal/null."""
    if not combat or not isinstance(combat, dict):
        return None
    if not combat.get('in_combat'):
        return {'in_combat': False}
    return combat


def _compress_scene_runtime(runtime: Dict[str, Any], session: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Keep only essential runtime fields to avoid bloat."""
    if not runtime or not isinstance(runtime, dict):
        return {}
    recent_contextual_leads: List[Dict[str, Any]] = []
    raw_leads = runtime.get("recent_contextual_leads")
    if isinstance(raw_leads, list):
        for item in raw_leads[-MAX_RECENT_CONTEXTUAL_LEADS:]:
            if not isinstance(item, dict):
                continue
            subject = str(item.get("subject") or "").strip()
            key = str(item.get("key") or "").strip()
            if not subject or not key:
                continue
            recent_contextual_leads.append(
                {
                    "key": key,
                    "kind": str(item.get("kind") or "").strip(),
                    "subject": subject,
                    "position": str(item.get("position") or "").strip(),
                    "named": bool(item.get("named")),
                    "mentions": int(item.get("mentions", 1) or 1),
                    "last_turn": int(item.get("last_turn", 0) or 0),
                }
            )
    raw_pending = list(runtime.get('pending_leads', []) or [])
    pending_view = (
        filter_pending_leads_for_active_follow_surface(session, raw_pending)
        if isinstance(session, dict)
        else raw_pending
    )
    return {
        'discovered_clues': list(runtime.get('discovered_clues', []) or [])[:20],
        'pending_leads': pending_view,
        'recent_contextual_leads': recent_contextual_leads,
        'repeated_action_count': runtime.get('repeated_action_count', 0) or 0,
        'last_exploration_action_key': runtime.get('last_exploration_action_key'),
        'momentum_exchanges_since': int(runtime.get('momentum_exchanges_since', 0) or 0),
        'momentum_next_due_in': int(runtime.get('momentum_next_due_in', 2) or 2),
        'momentum_last_kind': runtime.get('momentum_last_kind'),
    }


def derive_narration_obligations(
    session_view: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
    recent_log_for_prompt: List[Dict[str, Any]] | None,
    scene_runtime: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Derive compact, engine-owned narration obligations for this turn."""
    turn_counter = int(session_view.get('turn_counter', 0) or 0)
    visited_scene_count = int(session_view.get('visited_scene_count', 0) or 0)
    recent_turns = len(recent_log_for_prompt or [])
    is_opening_scene = (
        turn_counter <= 1
        or (turn_counter == 0 and visited_scene_count <= 1 and recent_turns == 0)
    )

    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip().lower()
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_transition_occurred = bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred"))
    arrived_at_scene = bool(state_changes.get("arrived_at_scene"))
    new_scene_context_available = bool(state_changes.get("new_scene_context_available"))
    must_advance_scene = bool(scene_transition_occurred or arrived_at_scene or new_scene_context_available)

    active_target_id = str(session_view.get('active_interaction_target_id') or '').strip()
    active_kind = str(session_view.get('active_interaction_kind') or '').strip().lower()
    interaction_mode = str(session_view.get('interaction_mode') or '').strip().lower()
    has_active_target = bool(active_target_id)
    should_answer_active_npc = has_active_target and (
        interaction_mode == 'social'
        or active_kind in SOCIAL_REPLY_KINDS
        or active_kind == 'social'
    )

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels_low = {str(label).strip().lower() for label in labels if isinstance(label, str) and label.strip()}
    has_social_resolution = isinstance(res.get('social'), dict) or res_kind in SOCIAL_REPLY_KINDS
    social_payload = res.get('social') if isinstance(res.get('social'), dict) else {}
    explicit_reply_expected = social_payload.get('npc_reply_expected') if isinstance(social_payload.get('npc_reply_expected'), bool) else None
    explicit_reply_kind_raw = str(social_payload.get('reply_kind') or '').strip().lower()
    explicit_reply_kind = explicit_reply_kind_raw if explicit_reply_kind_raw in NPC_REPLY_KIND_VALUES else None

    has_pending_check_prompt = bool(
        res.get('requires_check')
        and not isinstance(res.get('skill_check'), dict)
        and isinstance(res.get('check_request'), dict)
    )
    # Ongoing social exchange (engine-established target + social mode) expects an NPC reply
    # even when this turn has no structured resolution.social (e.g. chat/wait while engaged).
    active_npc_reply_expected_fallback = should_answer_active_npc and (
        has_social_resolution
        or 'social_probe' in labels_low
        or interaction_mode == 'social'
    )
    # Authoritative social mode: always expect an NPC reply unless a check prompt blocks narration.
    if interaction_mode == 'social' and has_active_target:
        active_npc_reply_expected = not has_pending_check_prompt
    else:
        active_npc_reply_expected = (
            False
            if has_pending_check_prompt
            else (explicit_reply_expected if explicit_reply_expected is not None else active_npc_reply_expected_fallback)
        )
    active_npc_reply_kind = explicit_reply_kind
    if active_npc_reply_expected and active_npc_reply_kind is None:
        if res_kind in {'persuade', 'intimidate', 'deceive', 'barter', 'recruit'}:
            active_npc_reply_kind = 'reaction'
        elif res_kind in {'question', 'social_probe'}:
            active_npc_reply_kind = 'answer'
        else:
            active_npc_reply_kind = 'reaction'
    if not active_npc_reply_expected:
        active_npc_reply_kind = None

    rt = scene_runtime if isinstance(scene_runtime, dict) else {}
    exchanges_since = int(rt.get("momentum_exchanges_since", 0) or 0)
    next_due_in = int(rt.get("momentum_next_due_in", 2) or 2)
    if next_due_in not in (2, 3):
        next_due_in = 2
    # If last momentum was 1 exchange ago and next_due_in=2, momentum is due now.
    # This ensures a strict "every 2–3 exchanges" cadence with a hard ceiling of 3.
    due_threshold = (next_due_in - 1)
    if due_threshold < 1:
        due_threshold = 1
    if due_threshold > 2:
        due_threshold = 2
    suppress_non_social_emitters = interaction_mode == 'social' and has_active_target
    scene_momentum_due = False if suppress_non_social_emitters else (exchanges_since >= due_threshold)

    return {
        'is_opening_scene': bool(is_opening_scene),
        'must_advance_scene': bool(must_advance_scene),
        'should_answer_active_npc': bool(should_answer_active_npc),
        'avoid_input_echo': True,
        'avoid_player_action_restatement': True,
        'prefer_structured_turn_summary': True,
        'active_npc_reply_expected': bool(active_npc_reply_expected),
        'active_npc_reply_kind': active_npc_reply_kind,
        'scene_momentum_due': bool(scene_momentum_due),
        'scene_momentum_exchanges_since': exchanges_since,
        'scene_momentum_next_due_in': next_due_in,
        'suppress_non_social_emitters': bool(suppress_non_social_emitters),
    }


def _build_turn_summary(
    user_text: str,
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Build a compact, structured summary of this turn for narration anchoring."""
    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip()
    res_label = str(res.get('label') or '').strip()
    res_action_id = str(res.get('action_id') or '').strip()
    res_prompt = str(res.get('prompt') or '').strip()

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels = [str(label).strip() for label in labels if isinstance(label, str) and str(label).strip()]

    if res_kind:
        descriptor = res_label or res_kind.replace('_', ' ')
    elif labels:
        descriptor = labels[0].replace('_', ' ')
    else:
        descriptor = 'general_action'

    return {
        'action_descriptor': descriptor,
        'resolution_kind': res_kind or None,
        'action_id': res_action_id or None,
        'resolved_prompt': res_prompt or None,
        'intent_labels': labels,
        'raw_player_input': str(user_text or ''),
        'raw_player_input_usage': (
            'Retain for exact wording and disambiguation only. '
            'Prefer action_descriptor + resolution_kind + mechanical_resolution for narration framing.'
        ),
    }


MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT = 5
MANUAL_PLAY_COMPACT_MEMORY_LIMIT = 6
MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT = 4


def _should_use_manual_play_compact_prompt(
    *,
    prompt_profile: str,
    narration_obligations: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    uncertainty_hint: Mapping[str, Any] | None,
    follow_up_pressure: Mapping[str, Any] | None,
    active_topic_anchor: Mapping[str, Any] | None,
) -> bool:
    if prompt_profile == "manual_play_compact":
        return True
    if prompt_profile != "manual_play_auto":
        return False
    obligations = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    res = resolution if isinstance(resolution, Mapping) else {}
    if obligations.get("is_opening_scene") or obligations.get("must_advance_scene"):
        return False
    if res.get("requires_check") or res.get("resolved_transition"):
        return False
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), Mapping) else {}
    if any(
        bool(state_changes.get(key))
        for key in ("scene_transition_occurred", "arrived_at_scene", "new_scene_context_available")
    ):
        return False
    if isinstance(uncertainty_hint, Mapping) and uncertainty_hint:
        return False
    if isinstance(active_topic_anchor, Mapping) and active_topic_anchor.get("active"):
        return False
    if isinstance(follow_up_pressure, Mapping) and follow_up_pressure:
        return False
    return True


def _compact_manual_play_instructions(
    *,
    mode_instruction: str,
    narration_obligations: Mapping[str, Any] | None,
    response_policy: Mapping[str, Any] | None,
    has_active_interlocutor: bool,
    social_authority: bool,
    has_scene_change_context: bool,
    naming_line: str | None,
    answer_style_hints: List[str],
) -> List[str]:
    obligations = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    policy = response_policy if isinstance(response_policy, Mapping) else {}
    out: List[str] = [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        "Always answer the player first. Prefer a grounded partial answer over refusal. Never output meta explanations.",
        NO_VALIDATOR_VOICE_RULE,
        "Follow response_policy.rule_priority_order strictly. Use response_policy as the full authority for answer shape, continuity, and safety boundaries.",
    ]
    if has_active_interlocutor:
        out.append("Keep the active conversation primary over general scene recap.")
    if social_authority:
        out.append(
            "SOCIAL INTERACTION LOCK: The active interlocutor must carry the substantive reply. Do not replace the answer with ambient scene narration."
        )
    if obligations.get("active_npc_reply_expected"):
        out.append("If narration_obligations.active_npc_reply_expected is true, complete that NPC's substantive reply now.")
    if obligations.get("should_answer_active_npc"):
        out.append("Prioritize the active interlocutor's answer over broad scene description.")
    if obligations.get("avoid_input_echo") or obligations.get("avoid_player_action_restatement"):
        out.append("Do not restate or lightly paraphrase player_input. Continue forward with new information.")
    if has_scene_change_context:
        out.append("When transitioning scenes, include a brief bridge from the prior location before describing the new one.")
    ac = policy.get("answer_completeness") if isinstance(policy.get("answer_completeness"), Mapping) else {}
    if ac.get("answer_required"):
        out.append("ANSWER COMPLETENESS: When response_policy.answer_completeness.answer_required is true, lead with the substantive answer in the first sentence.")
    rd = policy.get("response_delta") if isinstance(policy.get("response_delta"), Mapping) else {}
    if rd.get("enabled"):
        out.append("RESPONSE DELTA: Add net-new value. Do not merely restate the prior answer.")
    na = policy.get("narrative_authenticity") if isinstance(policy.get("narrative_authenticity"), Mapping) else {}
    if na.get("enabled"):
        out.append(
            "NARRATIVE AUTHENTICITY: Do not recycle the same surface clause from narration into quoted speech; "
            "prefer new signal on follow-ups; stay diegetic."
        )
    if naming_line:
        out.append(naming_line)
    if answer_style_hints:
        out.extend(list(answer_style_hints[:2]))
    out.append(
        "CONVERSATIONAL MEMORY WINDOW: Treat selected_conversational_memory as the active thread for this turn and do not revive omitted stale threads unless the player re-grounds them."
    )
    out.append(
        "POLICY TAIL: Obey response_policy.narrative_authority, narrative_authenticity, tone_escalation, anti_railroading, context_separation, player_facing_narration_purity, and scene anchoring without re-explaining them in narration."
    )
    out.append(mode_instruction)
    return out


def build_narration_context(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
) -> Dict[str, Any]:
    """Build a compressed narration context payload for GPT.

    Caller must precompute scene layers (public_scene, clues, hidden, etc.)
    and pass them in. This avoids duplicating _scene_layers logic and ensures
    hidden facts stay in gm_only only.

    Returns a dict suitable for JSON serialization as the user message content.

    Narration contracts are layered: visibility (reference scope), narrative_authority (certainty
    and assertion boundaries), scene_state_anchor (grounding), answer_completeness
    (answer-shape obligations), fallback_behavior (narrow uncertainty fallback shape),
    tone_escalation (interpersonal intensity caps), anti_railroading (player agency vs surfaced leads),
    context_separation (ambient pressure vs local exchange), and player_facing_narration_purity
    (no scaffold/menu/engine coaching in prose),
    and social_response_structure (dialogue-turn spoken shape when response type requires dialogue),
    narrative_authenticity (anti-echo / signal-density / diegetic-shape pressure shipped on response_policy),
    and interaction_continuity (thread / interlocutor anchoring snapshot for enforcement layers);
    see module docstring.
    """
    # Interlocutor lead contract (maintenance): interlocutor_lead_context is the NPC-scoped export from
    # discussion tracking + authoritative lead rows; interlocutor_lead_behavior_hints are derived only
    # from that dict. Keep both separate from lead_context and pending_leads. Synthetic regression targets
    # this export for continuity / repeat suppression—not fixed narration wording.
    active_pending_leads = (
        filter_pending_leads_for_active_follow_surface(session, pending_leads)
        if isinstance(session, dict)
        else list(pending_leads or [])
    )
    runtime = _compress_scene_runtime(scene_runtime or {}, session=session if isinstance(session, dict) else None)
    session_view = _compress_session(session, world, public_scene)
    narration_obligations = derive_narration_obligations(
        session_view=session_view,
        resolution=resolution,
        intent=intent,
        recent_log_for_prompt=recent_log_for_prompt,
        scene_runtime=runtime,
    )
    social_authority = bool(narration_obligations.get("suppress_non_social_emitters"))
    eff_uncertainty_hint = None if social_authority else uncertainty_hint
    recent_log_compact = (
        _compress_recent_log(recent_log_for_prompt) if recent_log_for_prompt else []
    )
    response_policy = build_response_policy(
        narration_obligations=narration_obligations,
        player_text=str(user_text or ""),
        resolution=resolution,
        session_view=session_view,
        uncertainty_hint=eff_uncertainty_hint,
        recent_log_compact=recent_log_compact,
    )
    res = resolution if isinstance(resolution, dict) else {}
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_advancement = {
        "scene_transition_occurred": bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred")),
        "arrived_at_scene": bool(state_changes.get("arrived_at_scene")),
        "new_scene_context_available": bool(state_changes.get("new_scene_context_available")),
    }
    has_scene_change_context = any(bool(v) for v in scene_advancement.values())
    interaction_continuity = {
        'active_interaction_target_id': session_view.get('active_interaction_target_id'),
        'active_interaction_target_name': session_view.get('active_interaction_target_name'),
        'active_interaction_kind': session_view.get('active_interaction_kind'),
        'interaction_mode': session_view.get('interaction_mode'),
        'engagement_level': session_view.get('engagement_level'),
        'conversation_privacy': session_view.get('conversation_privacy'),
        'player_position_context': session_view.get('player_position_context'),
    }
    has_active_interlocutor = bool(str(interaction_continuity.get('active_interaction_target_id') or '').strip())
    scene_pub_id = str((public_scene or {}).get("id") or "").strip()
    interlocutor_export = build_active_interlocutor_export(session, world, public_scene)
    answer_style_hints_list = deterministic_interlocutor_answer_style_hints(
        interlocutor_export, scene_id=scene_pub_id
    )

    clue_records_all: List[Dict[str, Any]] = list(discovered_clue_records) + list(undiscovered_clue_records)
    clue_visibility = {
        'implicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'implicit'],
        'explicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'explicit'],
        'actionable': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'actionable'],
    }

    visibility_contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_facts_for_prompt = list(visibility_contract.get("visible_fact_strings") or [])
    if narration_obligations.get("is_opening_scene") and isinstance(public_scene, Mapping):
        curated_opening = select_opening_narration_visible_facts(public_scene)
        if curated_opening:
            visible_facts_for_prompt = curated_opening
        else:
            visible_facts_for_prompt = visible_facts_for_prompt[:OPENING_NARRATION_VISIBLE_FACT_MAX]
    res_for_vis = resolution if isinstance(resolution, dict) else {}
    res_md_vis = res_for_vis.get("metadata") if isinstance(res_for_vis.get("metadata"), dict) else {}
    if res_md_vis.get("human_adjacent_intent_family") in {"listen", "approach_listen", "observe_group"}:
        from game.human_adjacent_focus import prioritize_visible_facts_for_human_adjacent

        visible_facts_for_prompt = prioritize_visible_facts_for_human_adjacent(
            visible_facts_for_prompt,
            player_text=str(user_text or ""),
            implicit_focus_resolution=str(res_md_vis.get("implicit_focus_resolution") or ""),
            human_adjacent_intent_family=str(res_md_vis.get("human_adjacent_intent_family") or ""),
        )
    # Opening curation may return display-preserved strings; minimal narration_visibility export
    # matches build_narration_visibility_contract (normalized, deduped).
    _seen_visible_fact: Set[str] = set()
    visible_facts_export: List[str] = []
    for _vf in visible_facts_for_prompt:
        if not isinstance(_vf, str):
            continue
        _n = _normalize_visibility_text(_vf)
        if not _n or _n in _seen_visible_fact:
            continue
        _seen_visible_fact.add(_n)
        visible_facts_export.append(_n)
    narration_visibility: Dict[str, Any] = {
        "visible_entities": list(visibility_contract.get("visible_entity_names") or []),
        "active_interlocutor_id": visibility_contract.get("active_interlocutor_id"),
        "visible_facts": visible_facts_export,
        "rules": {
            "no_unseen_entities": True,
            "no_hidden_facts": True,
            "no_undiscovered_facts": True,
        },
    }
    scene_state_anchor_contract = build_scene_state_anchor_contract(
        session if isinstance(session, dict) else None,
        scene if isinstance(scene, dict) else None,
        world if isinstance(world, dict) else None,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    prompt_debug_anchor = {
        "scene_state_anchor": {
            "enabled": bool(scene_state_anchor_contract.get("enabled")),
            "scene_id": scene_state_anchor_contract.get("scene_id"),
            "counts": {
                "location": len(scene_state_anchor_contract.get("location_tokens") or []),
                "actor": len(scene_state_anchor_contract.get("actor_tokens") or []),
                "player_action": len(scene_state_anchor_contract.get("player_action_tokens") or []),
            },
        }
    }
    first_mention_contract: Dict[str, Any] = {
        "enabled": True,
        "requires_explicit_intro": True,
        "requires_grounding": True,
        "disallow_pronoun_first_reference": True,
        "disallow_unearned_familiarity": True,
    }

    instructions: List[str] = (
        [
            'Prioritize the active conversation over general scene recap.',
            'Do not fall back to base scene description unless the location materially changes, a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat.',
        ]
        if has_active_interlocutor
        else []
    ) + [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        'Always answer the player. Prefer partial truth over refusal. Never output meta explanations.',
        NO_VALIDATOR_VOICE_RULE,
        'Follow response_policy.rule_priority_order strictly. Higher-priority rules override later ones.',
        'Treat response_policy.no_validator_voice as a hard narration-lane rule for standard narration.',
        (
            "ANSWER COMPLETENESS CONTRACT (MANDATORY): Obey response_policy.answer_completeness. "
            "When answer_required is true, answer_must_come_first requires the first sentence to deliver the substantive reply "
            "aligned with expected_answer_shape (direct, bounded_partial using an in-world limit from allowed_partial_reasons, "
            "or refusal_with_reason). Bounded partials must name the limiting reason in-character (uncertainty, lack_of_knowledge, or gated_information). "
            "When forbid_deflection or forbid_generic_nonanswer are true, evasive replies, scene filler before the core reply, and answering-with-a-question are invalid. "
            "When require_concrete_payload is true, include at least one handle from concrete_payload_any_of. "
            "Incomplete or hedged replies must still provide a usable specific or next_lead the player can pursue now."
        ),
        (
            "When response_policy.answer_completeness.expected_voice is npc, keep the turn NPC-carried for the substantive reply "
            "per active interlocutor; when narrator, still lead with the answer in the first sentence when answer_required is true."
        ),
        (
            "When response_policy.response_delta.enabled is true, the player is pressing the same topic again: do not merely restate "
            "the prior answer. Add net-new value via allowed_delta_kinds (new_information, refinement that narrows the prior claim, "
            "consequence, or clarified uncertainty—not paraphrase)."
        ),
        *NARRATION_VISIBILITY_MANDATORY_INSTRUCTIONS,
        *FIRST_MENTION_MANDATORY_INSTRUCTIONS,
        *SCENE_STATE_ANCHOR_MANDATORY_INSTRUCTIONS,
        (
            "SCENE MOMENTUM RULE (HARD RULE): Every 2–3 exchanges, you MUST introduce exactly one of: "
            "new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity. "
            "When you do, include exactly one tag in tags: "
            "scene_momentum:<kind> where kind is one of those five identifiers. "
            "If narration_obligations.scene_momentum_due is true, this turn MUST include a momentum beat and MUST include that tag."
        ),
        'Use campaign and world state to keep political and strategic continuity.',
        'Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.',
        'Forbidden generic phrases are disallowed: "In this city...", "Times are tough...", "Trust is hard to come by...", "You\'ll need to prove yourself..." — rewrite into specific names/locations/events.',
        'QUESTION RESOLUTION RULE (HARD RULE): Every direct player question MUST be answered explicitly before any additional dialogue. Structure: (1) Direct answer (first sentence), (2) Optional elaboration, (3) Optional hook. The GM/NPC MUST NOT deflect, generalize, or ask a new question before answering.',
        'If certainty is incomplete, classify the uncertainty with response_policy.uncertainty.categories and response_policy.uncertainty.sources, then compose it from response_policy.uncertainty.answer_shape: known_edge, unknown_edge, next_lead.',
        'Ground uncertainty with response_policy.uncertainty.context_inputs: uncertainty_hint.turn_context, uncertainty_hint.speaker, and uncertainty_hint.scene_snapshot.',
        'If uncertainty_hint.speaker.role is npc, keep the reply attributable to that NPC and limited to what they could plausibly know, hear, point to, or direct the player toward.',
        'If there is no active NPC speaker, keep uncertainty in diegetic narrator voice but anchor it to visible scene circumstances rather than generic omniscient wording.',
        'If social_intent_class remains social_exchange on an NPC-directed question, keep uncertainty speaker-grounded (npc_ignorance) instead of drifting into scene ambiguity.',
        'Frame uncertainty as world-facing limits only: who knows, what can be seen, what distance, darkness, rumor, missing witnesses, or incomplete clues prevent right now.',
        'Vary sentence count and cadence naturally; do not stamp the same three-sentence rhythm onto every uncertain answer.',
        'If no strong next lead exists, choose the strongest visible handle already in scene rather than giving generic investigative advice.',
        'PERCEPTION / INTENT ADJUDICATION RULE (HARD RULE): When the player asks for behavioral insight (e.g., nervous, lying, controlled), choose ONE dominant state (not mixed), give 1–2 concrete observable tells, and optionally map to a skill interpretation (Sense Motive, etc.). Failure: "mix of"/"seems like both" or pure emotional summary with no cues.',
        'If the player meaningfully moves to a new location, you may provide a new_scene_draft and/or activate_scene_id.',
        'If the player meaningfully changes the world, you may provide world_updates.',
        'If the player text implies a clear mechanical action, suggested_action may be filled for UI assistance, but narration remains primary.',
        'When interaction_continuity has an active target, treat that NPC as the default conversational counterpart.',
        'Non-addressed NPCs should not casually interject; if they interrupt, present it as a notable event with scene justification.',
        'If conversation_privacy or player_position_context implies private exchange (for example lowered_voice), reduce casual eavesdropping/interjection unless scene facts justify otherwise.',
        'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
        'Treat player input as an action declaration: default to third-person phrasing and preserve the user\'s expression format instead of rewriting it.',
        'Quoted in-character dialogue is valid inside an action declaration (for example: Galinor says, "Keep your voice down."); do not treat the quote alone as the entire action when surrounding action context exists.',
        'Follow narration_obligations as output requirements only: they shape wording and focus, but never grant authority to mutate state or decide mechanics.',
        'If narration_obligations.is_opening_scene is true, establish immediate environment plus actionable social/world hooks the player can engage now.',
        'If narration_obligations.must_advance_scene is true, do not stop at movement text alone; narrate arrival, changed state, and at least one concrete opportunity or pressure in the destination context.',
        'If narration_obligations.active_npc_reply_expected is true, complete the active NPC\'s substantive in-turn reply now unless a pending engine check prompt already takes precedence, or authoritative state indicates refusal/evasion/interruption/inability.',
        'If narration_obligations.should_answer_active_npc is true, prioritize the active interlocutor\'s reply and the immediate exchange over general scene recap.',
        'Use narration_obligations.active_npc_reply_kind as a compact reply-shape hint (answer, explanation, reaction, refusal).',
        'If narration_obligations.active_npc_reply_kind is refusal, make it substantive (clear boundary, brief reason, redirect, or consequence) rather than empty stalling.',
        'If the player asks a direct question, answer concretely (name, place, fact, or direction); if certainty is incomplete, provide the best grounded partial answer and state uncertainty in-character through witnesses, conditions, rumor, access, or incomplete observation; do not repeat prior information.',
        'NPC response contract: when an NPC is asked a question, include at least one of: (a) a specific person/place/faction, (b) a concrete next step the player can take, (c) directly usable info (time/location/condition/requirement). If the NPC lacks full information, give partial specifics or direct the player to a concrete source.',
        'When answering a player question, give a direct answer first. Do not replace the answer with narrative description.',
        'Use turn_summary and mechanical_resolution as primary narration anchors; treat player_input as supporting evidence for disambiguation, not as the sentence structure to mirror.',
        "Do not restate or paraphrase the player's input. Always continue forward with new information.",
        "Do not repeat the player's spoken line. React to it instead.",
        'If narration_obligations.avoid_input_echo or narration_obligations.avoid_player_action_restatement is true, do not restate or lightly paraphrase player_input (for example, "Galinor asks...") unless wording is required to disambiguate the target, quote, or procedural request.',
        'If narration_obligations.prefer_structured_turn_summary is true, continue from resolved world state, scene advancement, and NPC intent/reply obligations rather than narrating that "the player asks/says X."',
        'Keep the narration to 1-4 concise paragraphs.',
        mode_instruction,
    ]
    if has_scene_change_context:
        instructions.append(
            'When transitioning scenes, include a brief bridge from the prior location before describing the new one.'
        )

    if social_authority:
        _skip_instr = (
            "SCENE MOMENTUM RULE",
            "uncertainty_hint",
            "response_policy.uncertainty",
            "classify the uncertainty",
            "Ground uncertainty with",
            "Frame uncertainty as",
            "If uncertainty_hint",
        )
        instructions = [line for line in instructions if not any(m in line for m in _skip_instr)]
        instructions.append(
            "SOCIAL INTERACTION LOCK: Do not use ambient scene narration, scene-wide uncertainty pools, or momentum/pressure "
            "beats as the main voice. The active interlocutor must carry this turn (substantive reply, reaction, or refusal)."
        )

    follow_up_log_pressure = _compute_follow_up_pressure(recent_log_compact, user_text)
    ap_for_prompt = _answer_pressure_followup_details(
        player_input=str(user_text or ""),
        recent_log_compact=list(recent_log_compact or []),
        narration_obligations=narration_obligations,
        session_view=session_view,
        answer_completeness=None,
    )
    if follow_up_log_pressure is None and ap_for_prompt.get("answer_pressure_followup_detected"):
        follow_up_log_pressure = _synthetic_follow_up_pressure_from_log(
            recent_log_compact, str(user_text or "")
        )
    if social_authority and not ap_for_prompt.get("answer_pressure_followup_detected"):
        follow_up_log_pressure = None

    active_topic_anchor = explicit_player_topic_anchor_state(str(user_text or ""))

    active_npc_id: str | None = None
    if isinstance(public_scene, Mapping):
        if isinstance(interlocutor_export, dict):
            _nid = str(interlocutor_export.get("npc_id") or "").strip()
            if _nid:
                active_npc_id = _nid
        if active_npc_id is None:
            _tid = session_view.get("active_interaction_target_id")
            if _tid and str(_tid).strip():
                active_npc_id = str(_tid).strip()

    lead_context = build_authoritative_lead_prompt_context(
        session=session,
        world=world,
        public_scene=public_scene,
        runtime=runtime,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_context = build_interlocutor_lead_discussion_context(
        session=session,
        world=world,
        public_scene=public_scene,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_behavior_hints = deterministic_interlocutor_lead_behavior_hints(
        interlocutor_lead_context
    )
    from_leads_pressure = lead_context.get("follow_up_pressure_from_leads")
    if not isinstance(from_leads_pressure, dict):
        from_leads_pressure = {
            "has_pursued": False,
            "has_stale": False,
            "npc_has_relevant": False,
            "has_escalated_threat": False,
            "has_newly_unlocked": False,
            "has_supersession_cleanup": False,
        }

    if follow_up_log_pressure:
        instructions = list(instructions) + [
            (
                "FOLLOW-UP ESCALATION RULE (HARD RULE): The player is pressing the same topic again (see follow_up_pressure). "
                "Do NOT recycle the same core lead from the previous answer. Escalate by doing AT LEAST TWO of the following: "
                "(1) add one new concrete detail (time, place, condition, count, or observable), "
                "(2) introduce a named person/place/faction/witness tied to the topic (with an in-world source), "
                "(3) narrow the boundary of the unknown (what is ruled out; what is now most likely; what would confirm it), "
                "(4) produce a more actionable immediate next step that uses the new detail. "
                "Preserve uncertainty, but uncertainty must evolve. Preserve speaker grounding."
            ),
            "Allowed repetition: one short anchor clause for continuity. Not allowed: re-stating the same underlying lead as the whole answer.",
        ]

    lead_instr: List[str] = [
        "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
        "Turn compact rows into light, actionable nudges (what could matter next), not recap.",
        "When the player is clearly continuing an existing investigation thread, prefer lead_context.currently_pursued_lead as the primary thread anchor when it is non-null.",
        "When interaction_continuity names an active NPC, use lead_context.npc_relevant_leads to tie the exchange to registry-linked threads that list that NPC—without fabricating details beyond those rows.",
        "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
        "Use lead_context.recent_lead_changes for continuity with the latest registry state shifts (status, next_step, touches)—do not restate full buckets or dump all leads.",
        "follow_up_pressure.from_leads is boolean-only: has_pursued, has_stale, npc_has_relevant, has_escalated_threat, has_newly_unlocked, has_supersession_cleanup. Do not treat it as prose; use the matching lead_context lists/objects for specifics.",
        "If follow_up_pressure.from_leads.has_pursued is true, bias narration toward continuing that pursued thread when it fits the player's action.",
        "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
        "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
        "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
        "If follow_up_pressure.from_leads.has_newly_unlocked is true, you may acknowledge a thread becoming available or unblocked when it fits the scene—grounded in unlocked_by_lead_id / recent_lead_changes only.",
        "If follow_up_pressure.from_leads.has_supersession_cleanup is true, avoid treating superseded obsoleted threads as primary pressure unless the player returns to them; prefer current non-terminal rows.",
    ]
    instructions = list(instructions) + lead_instr

    if social_authority and active_topic_anchor.get("active"):
        instructions = list(instructions) + [
            "ACTIVE TOPIC ANCHOR (HARD RULE): The player explicitly corrected or narrowed the conversational subject "
            "this turn. Answer that subject first in the active interlocutor's voice. Do not pivot back to "
            "lead_context.currently_pursued_lead, urgent_or_stale_leads, or unrelated registry mystery threads "
            "for convenience. Registry salience alone is not sufficient to override the clarified subject. "
            "A redirect is allowed only after a substantive answer—or honest refusal, evasion, or ignorance—on the "
            "asked subject.",
        ]

    if social_authority:
        if follow_up_log_pressure is not None:
            follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
        else:
            follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    elif follow_up_log_pressure is not None:
        follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
    elif any(from_leads_pressure.values()):
        follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    else:
        follow_up_pressure = None

    naming_line: str | None = None
    if interlocutor_export and str(interlocutor_export.get("npc_id") or "").strip():
        nid = str(interlocutor_export.get("npc_id") or "").strip()
        dn = str(interlocutor_export.get("display_name") or "").strip()
        naming_line = (
            f"NAMING CONTINUITY (engine): Active interlocutor canonical id is {nid!r}"
            + (f", display name {dn!r}" if dn else "")
            + ". Keep this name/title stable across turns unless engine state changes it; "
            "do not regress to generic unnamed incidental-crowd wording for this id."
        )
        instructions = list(instructions) + list(answer_style_hints_list) + [naming_line]

    soc_profile = build_social_interlocutor_profile(interlocutor_export)

    scene_id_for_speaker = scene_pub_id or (
        str((session.get("scene_state") or {}).get("active_scene_id") or "").strip()
        if isinstance(session, dict)
        else ""
    )
    speaker_selection = build_speaker_selection_contract(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id_for_speaker,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    tone_escalation_build_error: str | None = None
    try:
        tone_escalation_contract = build_tone_escalation_contract(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=str(scene_id_for_speaker or "").strip(),
            resolution=resolution if isinstance(resolution, dict) else None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
            narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
            recent_log=list(recent_log_for_prompt or []),
        )
    except Exception as exc:
        tone_escalation_build_error = f"{type(exc).__name__}: {exc}"
        tone_escalation_contract = build_tone_escalation_contract(
            session=None,
            world=None,
            scene_id="",
            resolution=None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=None,
            narration_visibility=None,
            recent_log=None,
        )
        tone_escalation_contract["scene_id"] = str(scene_id_for_speaker or "").strip()
        tone_escalation_contract["debug_reason"] = (
            f"prompt_context_tone_escalation_build_failed:{type(exc).__name__}"
        )
        _te_df = tone_escalation_contract.get("debug_flags")
        tone_escalation_contract["debug_flags"] = {
            **(_te_df if isinstance(_te_df, dict) else {}),
            "exception": str(exc),
        }
    response_policy["tone_escalation"] = tone_escalation_contract
    _te_dbg = _tone_escalation_prompt_debug_anchor(tone_escalation_contract)
    if tone_escalation_build_error is not None:
        _te_dbg = {**_te_dbg, "build_error": tone_escalation_build_error[:500]}
    prompt_debug_anchor["tone_escalation"] = _te_dbg

    _psid = str((speaker_selection or {}).get("primary_speaker_id") or "").strip()
    _allowed_ids = [
        str(x).strip()
        for x in ((speaker_selection or {}).get("allowed_speaker_ids") or [])
        if isinstance(x, str) and str(x).strip()
    ]
    _switch_ok = bool((speaker_selection or {}).get("speaker_switch_allowed"))
    _gff = bool((speaker_selection or {}).get("generic_fallback_forbidden"))
    _labels_preview = ", ".join(
        repr(x) for x in ((speaker_selection or {}).get("forbidden_fallback_labels") or [])[:8]
    )
    _speaker_contract_instr: List[str] = [
        "SPEAKER SELECTION CONTRACT (HARD RULE): Obey the top-level `speaker_selection` object. "
        "When `primary_speaker_id` is non-null, treat that NPC as the default voice for substantive quoted dialogue "
        "and in-character answers for this turn.",
    ]
    if not _allowed_ids:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `allowed_speaker_ids` is empty — do not attribute quoted speech to any NPC; "
            "remain narrator-neutral. Do not invent incidental speakers or crowd voices to answer for a missing interlocutor."
        )
    else:
        _speaker_contract_instr.append(
            f"SPEAKER SELECTION CONTRACT (HARD RULE): Only these NPC ids may carry quoted NPC dialogue this turn: {_allowed_ids!r}. "
            "Do not give spoken lines to anyone else (including newly invented characters)."
        )
        if not _switch_ok:
            _speaker_contract_instr.append(
                "SPEAKER SELECTION CONTRACT (HARD RULE): `speaker_switch_allowed` is false — do not move the substantive reply "
                "to a different NPC mid-turn. If `interruption_allowed` is true, a single explicit scene-event interruption may cut "
                "off the current speaker per `interruption_requires_scene_event`."
            )
    if _gff:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `generic_fallback_forbidden` is true — do not use generic unnamed stand-ins "
            f"(for example {_labels_preview}) as the answer source."
        )
    instructions = list(instructions) + _speaker_contract_instr

    # Machine-readable boundary only; exhaustive checks live outside this module (e.g. emission gate).
    # narration_visibility= full ``build_narration_visibility_contract`` snapshot (not the slim prompt export).
    narrative_authority_contract = build_narrative_authority_contract(
        resolution=resolution if isinstance(resolution, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        session_view=session_view if isinstance(session_view, dict) else None,
    )
    response_policy["narrative_authority"] = narrative_authority_contract
    response_policy["forbid_unjustified_narrative_authority"] = True

    prompt_debug_anchor["narrative_authority"] = {
        "enabled": narrative_authority_contract.get("enabled"),
        "authoritative_outcome_available": narrative_authority_contract.get("authoritative_outcome_available"),
        "success_state_available": narrative_authority_contract.get("success_state_available"),
        "mechanical_result_available": narrative_authority_contract.get("mechanical_result_available"),
        "forbid_unresolved_outcome_assertions": narrative_authority_contract.get(
            "forbid_unresolved_outcome_assertions"
        ),
        "forbid_hidden_fact_assertions": narrative_authority_contract.get("forbid_hidden_fact_assertions"),
        "forbid_npc_intent_assertions_without_basis": narrative_authority_contract.get(
            "forbid_npc_intent_assertions_without_basis"
        ),
        "preferred_deferral_order": list(narrative_authority_contract.get("preferred_deferral_order") or []),
    }

    follow_surface = session.get("follow_surface") if isinstance(session, dict) else None
    anti_railroading_contract = build_anti_railroading_contract(
        resolution=resolution if isinstance(resolution, dict) else None,
        narration_obligations=narration_obligations,
        session_view=session_view if isinstance(session_view, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        narrative_authority_contract=narrative_authority_contract if isinstance(narrative_authority_contract, dict) else None,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
        player_text=str(user_text or ""),
    )
    response_policy["anti_railroading"] = anti_railroading_contract

    prompt_debug_anchor["anti_railroading"] = {
        "enabled": bool(anti_railroading_contract.get("enabled")),
        "surfaced_lead_count": len(anti_railroading_contract.get("surfaced_lead_ids") or []),
        "allow_directional_language_from_resolved_transition": anti_railroading_contract.get(
            "allow_directional_language_from_resolved_transition"
        ),
        "allow_exclusivity_from_authoritative_resolution": anti_railroading_contract.get(
            "allow_exclusivity_from_authoritative_resolution"
        ),
        "allow_commitment_language_when_player_explicitly_committed": anti_railroading_contract.get(
            "allow_commitment_language_when_player_explicitly_committed"
        ),
    }

    turn_summary_struct = _build_turn_summary(user_text, resolution, intent)
    _ts_parts = [
        str(turn_summary_struct.get("action_descriptor") or "").strip(),
        str(turn_summary_struct.get("resolution_kind") or "").strip(),
    ]
    _labels_ts = turn_summary_struct.get("intent_labels")
    if isinstance(_labels_ts, list) and _labels_ts:
        _ts_parts.append(", ".join(str(x).strip() for x in _labels_ts if isinstance(x, str) and str(x).strip()))
    turn_summary_for_contract = " ".join(p for p in _ts_parts if p).strip() or None

    scene_summary_for_contract: str | None = None
    if isinstance(public_scene, dict):
        scene_summary_for_contract = str(public_scene.get("summary") or "").strip() or None
    if not scene_summary_for_contract and isinstance(scene, dict):
        _inner = scene.get("scene")
        if isinstance(_inner, dict):
            scene_summary_for_contract = str(_inner.get("summary") or "").strip() or None

    session_view_for_separation: Dict[str, Any] = dict(session_view)
    if isinstance(world_state_view, dict):
        for _k in (
            "compressed_world_pressures",
            "world_pressures",
            "ambient_pressures",
            "surfaced_pressures",
            "surfaced_leads",
            "prompt_leads",
            "active_pending_leads",
            "leads_for_prompt",
        ):
            if _k in world_state_view and _k not in session_view_for_separation:
                session_view_for_separation[_k] = world_state_view[_k]

    compressed_world_pressures_arg: List[str] | None = None
    if isinstance(campaign, dict):
        _cwp_c = campaign.get("world_pressures")
        if isinstance(_cwp_c, list) and _cwp_c:
            compressed_world_pressures_arg = [
                str(x).strip() for x in _cwp_c if isinstance(x, str) and str(x).strip()
            ][:MAX_WORLD_PRESSURES]
    if compressed_world_pressures_arg is None and isinstance(world_state_view, dict):
        for _k in ("compressed_world_pressures", "world_pressures"):
            _raw_wp = world_state_view.get(_k)
            if isinstance(_raw_wp, list) and _raw_wp:
                compressed_world_pressures_arg = [
                    str(x).strip() for x in _raw_wp if isinstance(x, str) and str(x).strip()
                ][:MAX_WORLD_PRESSURES]
                break

    context_separation_contract = build_context_separation_contract(
        resolution=resolution if isinstance(resolution, dict) else None,
        player_text=str(user_text or ""),
        session_view=session_view_for_separation,
        scene_envelope=scene if isinstance(scene, dict) else None,
        scene_summary=scene_summary_for_contract,
        turn_summary=turn_summary_for_contract,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        tone_escalation_contract=tone_escalation_contract if isinstance(tone_escalation_contract, dict) else None,
        compressed_world_pressures=compressed_world_pressures_arg,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
    )
    response_policy["context_separation"] = context_separation_contract
    prompt_debug_anchor["context_separation"] = _context_separation_prompt_debug_anchor(context_separation_contract)

    _pfnp_ik = session_view.get("active_interaction_kind")
    player_facing_narration_purity_contract = build_player_facing_narration_purity_contract(
        interaction_kind=str(_pfnp_ik).strip() if isinstance(_pfnp_ik, str) and str(_pfnp_ik).strip() else None,
        debug_inputs={"scene_id": scene_pub_id or None},
    )
    response_policy["player_facing_narration_purity"] = player_facing_narration_purity_contract
    prompt_debug_anchor["player_facing_narration_purity"] = _player_facing_narration_purity_prompt_debug_anchor(
        player_facing_narration_purity_contract
    )

    rtc_peeked = peek_response_type_contract_from_resolution(resolution)
    rtc_source = "resolution.metadata" if rtc_peeked is not None else "derived"
    rtc_for_social_structure = rtc_peeked or derive_response_type_contract(
        segmented_turn=None,
        normalized_action=None,
        resolution=resolution if isinstance(resolution, dict) else None,
        interaction_context=response_type_context_snapshot(session if isinstance(session, dict) else None),
        directed_social_entry=None,
        route_choice=None,
        raw_player_text=str(user_text or ""),
    ).to_dict()
    social_response_structure_contract = build_social_response_structure_contract(
        rtc_for_social_structure,
        debug_inputs={"scene_id": scene_pub_id or None, "response_type_contract_source": rtc_source},
    )
    response_policy["social_response_structure"] = social_response_structure_contract
    prompt_debug_anchor["social_response_structure"] = _social_response_structure_prompt_debug_anchor(
        social_response_structure_contract
    )

    interaction_continuity_contract = build_interaction_continuity_contract(
        session if isinstance(session, dict) else None,
        scene_id=scene_pub_id or None,
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
    )
    response_policy["interaction_continuity"] = interaction_continuity_contract
    prompt_debug_anchor["interaction_continuity"] = _interaction_continuity_prompt_debug_anchor(
        interaction_continuity_contract
    )

    fallback_behavior_contract = build_fallback_behavior_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        recent_log=recent_log_compact,
        turn_summary=turn_summary_struct,
        mechanical_resolution=resolution if isinstance(resolution, dict) else None,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        answer_completeness_contract=response_policy.get("answer_completeness"),
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )
    response_policy["fallback_behavior"] = fallback_behavior_contract
    prompt_debug_anchor["fallback_behavior"] = {
        "enabled": bool(fallback_behavior_contract.get("enabled")),
        "uncertainty_active": bool(fallback_behavior_contract.get("uncertainty_active")),
        "uncertainty_mode": fallback_behavior_contract.get("uncertainty_mode"),
        "uncertainty_sources": list(fallback_behavior_contract.get("uncertainty_sources") or []),
    }

    from game.narrative_authenticity import build_narrative_authenticity_contract

    narrative_authenticity_contract = build_narrative_authenticity_contract(
        response_delta=response_policy.get("response_delta"),
        answer_completeness=response_policy.get("answer_completeness"),
        fallback_behavior=fallback_behavior_contract,
        social_response_structure=social_response_structure_contract,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        recent_log_compact=recent_log_compact,
        player_text=str(user_text or ""),
    )
    response_policy["narrative_authenticity"] = narrative_authenticity_contract
    prompt_debug_anchor["narrative_authenticity"] = _narrative_authenticity_prompt_debug_anchor(
        narrative_authenticity_contract
    )

    _ic_dbg = interaction_continuity_contract.get("debug")
    _ic_dbg_map = _ic_dbg if isinstance(_ic_dbg, dict) else {}
    _source_of_activity_anchor = str(_ic_dbg_map.get("source_of_anchor") or "").strip()
    _vis_ids_raw = visibility_contract.get("visible_entity_ids") if isinstance(visibility_contract, dict) else []
    _active_scene_entity_ids = [
        str(x).strip() for x in (_vis_ids_raw if isinstance(_vis_ids_raw, list) else []) if isinstance(x, str) and str(x).strip()
    ]
    _alias_map = visibility_contract.get("visible_entity_aliases") if isinstance(visibility_contract, dict) else None
    if not isinstance(_alias_map, dict):
        _alias_map = {}
    _re_ent, _re_top, _re_dbg = _extract_explicit_reintroductions(
        str(user_text or ""),
        entity_alias_map=_alias_map,
        topic_anchor_tokens=_memory_window_focus_topic_tokens(active_topic_anchor),
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
    )
    conversational_memory_window = build_conversational_memory_window_contract(
        enabled=True,
        recent_turn_window=6,
        soft_memory_limit=CONVERSATIONAL_MEMORY_SOFT_LIMIT,
        stale_after_turns=18,
        active_scene_entity_ids=_active_scene_entity_ids,
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
        explicit_reintroduced_entity_ids=_re_ent,
        explicit_reintroduced_topics=_re_top,
        selection_debug=dict(_re_dbg) if isinstance(_re_dbg, dict) else {},
        source_of_activity_anchor=_source_of_activity_anchor or "interaction_continuity",
        source_of_recentness="session.turn_counter",
        source_of_reintroductions="player_text+visibility_aliases",
    )
    _mem_cands, _mem_extras = _assemble_conversational_memory_candidates(
        recent_log_for_prompt=list(recent_log_for_prompt or []),
        current_turn=int(session_view.get("turn_counter") or 0),
        runtime_compressed=runtime,
        interlocutor_lead_context=interlocutor_lead_context,
        active_npc_id=active_npc_id,
    )
    selected_conversational_memory = select_conversational_memory_window(
        _mem_cands,
        conversational_memory_window,
        current_turn=int(session_view.get("turn_counter") or 0),
    )
    recent_log_for_payload = _recent_log_payload_from_selected_memory(
        selected_conversational_memory,
        _mem_cands,
        _mem_extras,
    )
    prompt_debug_anchor["conversational_memory"] = {
        "candidate_count": len(_mem_cands),
        "selected_count": len(selected_conversational_memory),
    }
    # Shipped policy mirror for downstream inspection (same object as payload; no second selector).
    response_policy["conversational_memory_window"] = conversational_memory_window
    instructions = list(instructions) + [
        "CONVERSATIONAL MEMORY WINDOW: Treat `selected_conversational_memory` as the bounded active conversational thread for this turn—prioritize it over older or omitted chat material. "
        "Do not revive stale side threads unless the player explicitly re-grounds them (see `conversational_memory_window.explicit_reintroduced_*`). "
        "Omitted older material is background only—not an active unresolved obligation.",
    ]

    _narrative_authority_instr = [
        "NARRATIVE AUTHORITY (POLICY): Obey response_policy.narrative_authority for assertion boundaries; deterministic enforcement is authoritative. "
        "Do not assert unresolved outcomes as settled fact. "
        "Do not assert hidden causes or hidden truths as confirmed without basis in published visible/engine state. "
        "Do not assert NPC motives or intentions as fact without explicit basis. "
        "When certainty is unavailable, defer via a roll/check request, bounded uncertainty, or conditional/branch framing. "
        "Observable visible cues are allowed; omniscient conclusions are not.",
    ]
    _fallback_behavior_instr = [
        "FALLBACK BEHAVIOR (MANDATORY): When `fallback_behavior.uncertainty_active` is true, do not invent certainty and do not fabricate authority. "
        "Either give a bounded partial answer or, only when `fallback_behavior.allowed_behaviors.ask_clarifying_question` is true and a partial would mislead, ask one brief clarifying question. "
        "Keep uncertainty diegetic, state the strongest grounded known edge plus the unknown edge, and offer a natural next lead when possible.",
    ]
    _tone_escalation_instr = [
        "TONE / ESCALATION (POLICY): Obey response_policy.tone_escalation for interpersonal intensity; that object is the authority—do not override it from general scene mood. "
        "Do not introduce hostility, explicit threats, physical violence, or combat initiation unless the contract's allowances and published state support it. "
        "When a higher escalation tier is not allowed, prefer guarded refusal, scrutiny, urgency, consequence framing, or concrete social or procedural pressure. "
        "Topic pressure or conversational friction alone does not justify threats or violence.",
    ]
    _anti_railroading_instr = [
        "ANTI-RAILROADING (POLICY): Obey top-level anti_railroading_contract and response_policy.anti_railroading. "
        "Do not decide the player character's action for them. "
        "Do not turn a surfaced lead into a required path: leads may create options, pressure, urgency, or opportunities; "
        "they do not create main-plot gravity, destiny, or a single mandatory thread. "
        "Avoid mandatory-path phrasing such as 'only way,' 'must go,' or 'the story pulls you' unless authoritative state "
        "truly supports it (see allow_exclusivity_from_authoritative_resolution and allow_directional_language_from_resolved_transition on the contract). "
        "Differentiate: HARD WORLD CONSTRAINT — state a fixed situation or barrier plainly without selecting the player's next move; "
        "SALIENT LEAD — highlight as option, rumor, pressure, or opportunity, not fate; "
        "FORCED PLAYER DIRECTION — never narrate the PC's decision, compulsion to one destination, or one true path without basis. "
        "A hard world constraint may narrow what is possible; it must not auto-pick the player's response. "
        "Preserve momentum through consequences, openings, reactions, and constraints—not by seizing player action. "
        "Precedence (compact): player agency outranks momentum polish; authoritative constraints may narrow possibilities but must not choose the player's next move; "
        "surfaced leads may be highlighted without being made mandatory. "
        "Directional language is not globally banned—only unjustified forced direction. "
        "When anti_railroading_contract.allow_commitment_language_when_player_explicitly_committed is true, narration that follows "
        "the player's explicit commitment in player_input (movement or intent they stated) is allowed and expected where appropriate.",
    ]
    _context_separation_instr = [
        "CONTEXT SEPARATION (POLICY): Obey response_policy.context_separation for ambient world pressure versus local interaction focus; deterministic enforcement uses that shipped object. "
        "Keep the current interaction intent primary: answer or react to the local exchange first. "
        "Ambient background pressure may briefly color wording or add an optional hook; it must not replace the substantive reply, hijack topic, or substitute vague instability for a direct answer. "
        "Background tension alone must not harden interpersonal tone beyond what tone_escalation already allows. "
        "Letting broader ambient pressure lead the reply is allowed only when the player text, scene framing, a resolved consequence, or published pressure inputs make that focus immediately relevant—not from generic scene mood alone.",
    ]
    _player_facing_narration_purity_instr = [
        "PLAYER-FACING NARRATION PURITY (POLICY): Obey response_policy.player_facing_narration_purity; deterministic enforcement uses that shipped object. "
        "Speak only in player-facing diegetic prose. "
        "Do not expose internal consequence/opportunity labels, planner headings, or engine-facing scaffolding as narration. "
        "Do not present action coaching, prompts, or engine/UI guidance as if it were in-world text. "
        "Do not mention exits or choices as menu labels (for example 'the exit labeled …', 'your options are …', or bulleted/numbered choice lists). "
        "When branching paths exist, render them as what the character can see, hear, or infer in the moment—not as explicit instructions to the player.",
    ]
    _anchoring_polish_instr = [
        "SCENE ANCHORING (POLICY): After context separation and narration-purity constraints, keep grounding tight: use scene_state_anchor_contract tokens when tightening wording; do not use anchoring to smuggle extra ambient pressure.",
    ]
    _social_response_structure_instr = [
        "SOCIAL RESPONSE STRUCTURE (POLICY): When response_policy.social_response_structure.enabled is true, obey that object; deterministic enforcement will use it later. "
        "NPC/social lines should sound spoken, not essay-like: answer first, then at most one short supporting detail if needed; avoid stacked explanatory clauses. "
        "Brief action beats are allowed; keep quoted speech primary. Uncertainty or refusal stays conversational and in-world. "
        "No bullet-like or numbered-list dialogue.",
    ]
    _narrative_authenticity_instr = [
        "NARRATIVE AUTHENTICITY (POLICY): Obey response_policy.narrative_authenticity. "
        "Keep narrator-color beats from being pasted into quoted speech; at most one short continuity anchor if needed. "
        "On follow-up pressure turns, change stance, detail, uncertainty boundary, reaction, or next step—without inventing facts. "
        "Avoid generic non-answers when a substantive or bounded-partial reply is available; when fallback_behavior.uncertainty_active is true, brevity and honest limits override polish. "
        "When rumor_realism applies (see trace.rumor_turn_active), do not recycle recent narration or scene setup as quoted rumor without a hearsay realism signal (source limit, uncertainty, bias, or net-new detail).",
    ]
    _policy_tail: List[str] = (
        list(_tone_escalation_instr)
        + _narrative_authority_instr
        + _fallback_behavior_instr
        + _anti_railroading_instr
        + _context_separation_instr
        + _player_facing_narration_purity_instr
        + _anchoring_polish_instr
        + _narrative_authenticity_instr
    )
    if social_response_structure_contract.get("enabled"):
        _policy_tail = list(_policy_tail) + _social_response_structure_instr
    instructions = list(instructions) + _policy_tail

    use_manual_play_compact = _should_use_manual_play_compact_prompt(
        prompt_profile=prompt_profile,
        narration_obligations=narration_obligations,
        resolution=resolution if isinstance(resolution, dict) else None,
        uncertainty_hint=eff_uncertainty_hint if isinstance(eff_uncertainty_hint, Mapping) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        active_topic_anchor=active_topic_anchor if isinstance(active_topic_anchor, Mapping) else None,
    )
    public_scene_for_prompt = dict(public_scene) if isinstance(public_scene, dict) else {}
    if use_manual_play_compact:
        selected_conversational_memory = list(selected_conversational_memory[:MANUAL_PLAY_COMPACT_MEMORY_LIMIT])
        recent_log_for_payload = _recent_log_payload_from_selected_memory(
            selected_conversational_memory,
            _mem_cands,
            _mem_extras,
        )
        recent_log_for_payload = list(recent_log_for_payload[:MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT])
        visible_facts_export = list(visible_facts_export[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT])
        if isinstance(public_scene_for_prompt.get("visible_facts"), list):
            public_scene_for_prompt["visible_facts"] = list(
                public_scene_for_prompt.get("visible_facts")[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT]
            )
        instructions = _compact_manual_play_instructions(
            mode_instruction=mode_instruction,
            narration_obligations=narration_obligations,
            response_policy=response_policy,
            has_active_interlocutor=has_active_interlocutor,
            social_authority=social_authority,
            has_scene_change_context=has_scene_change_context,
            naming_line=naming_line if isinstance(naming_line, str) else None,
            answer_style_hints=list(answer_style_hints_list),
        )
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": True,
            "profile": "manual_play_compact",
            "visible_fact_limit": MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT,
            "selected_memory_limit": MANUAL_PLAY_COMPACT_MEMORY_LIMIT,
            "recent_log_limit": MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT,
            "selected_memory_count": len(selected_conversational_memory),
            "recent_log_count": len(recent_log_for_payload),
        }
    else:
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": False,
            "profile": "full",
        }

    # Canonical snapshot for retry / gate contract lookup (not authoritative engine state).
    _turn_packet = build_turn_packet(
        response_policy=response_policy,
        scene_id=scene_pub_id or None,
        player_text=str(user_text or ""),
        resolution=resolution if isinstance(resolution, dict) else None,
        interaction_continuity=interaction_continuity,
        narration_obligations=narration_obligations,
        last_human_adjacent_continuity=(
            runtime.get("last_human_adjacent_continuity") if isinstance(runtime, dict) else None
        ),
        response_type=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        sources_used=["prompt_context.build_compressed_narration_context"],
    )

    payload: Dict[str, Any] = {
        'instructions': instructions,
        'speaker_selection': speaker_selection,
        'active_topic_anchor': active_topic_anchor,
        'interaction_continuity': interaction_continuity,
        'active_interlocutor': interlocutor_export,
        'social_context': {
            'interlocutor_profile': soc_profile,
            'answer_style_hints': list(answer_style_hints_list),
        },
        'turn_summary': turn_summary_struct,
        'recent_log': recent_log_for_payload,
        'conversational_memory_window': conversational_memory_window,
        'selected_conversational_memory': selected_conversational_memory,
        'player_input': str(user_text or ''),
        'follow_up_pressure': follow_up_pressure,
        'lead_context': lead_context,
        'interlocutor_lead_context': interlocutor_lead_context,
        'interlocutor_lead_behavior_hints': interlocutor_lead_behavior_hints,
        'response_policy': response_policy,
        'turn_packet': _turn_packet,
        'fallback_behavior': fallback_behavior_contract,
        'uncertainty_hint': eff_uncertainty_hint,
        'narration_obligations': narration_obligations,
        'narration_visibility': narration_visibility,
        'scene_state_anchor_contract': scene_state_anchor_contract,
        'anti_railroading_contract': anti_railroading_contract,
        'context_separation_contract': context_separation_contract,
        'player_facing_narration_purity_contract': player_facing_narration_purity_contract,
        'social_response_structure_contract': social_response_structure_contract,
        'interaction_continuity_contract': interaction_continuity_contract,
        'prompt_debug': prompt_debug_anchor,
        'first_mention_contract': first_mention_contract,
        'discoverable_hinting': True,
        'mechanical_resolution': resolution,
        'scene_advancement': scene_advancement,
        'session': session_view,
        'character': {
            'name': str(character.get('name', '') or ''),
            'role': str(campaign.get('character_role', '') or ''),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'conditions': character.get('conditions', []),
            'attacks': character.get('attacks', []),
            'spells': character.get('spells', {}),
            'skills': character.get('skills', {}),
        }
        if character and isinstance(character, dict)
        else {'name': '', 'role': '', 'hp': {}, 'ac': {}, 'conditions': [], 'attacks': [], 'spells': {}, 'skills': {}},
        'combat': _compress_combat(combat),
        'world_state': world_state_view,
        'world': _compress_world(world),
        'campaign': _compress_campaign(campaign),
        'scene': {
            'public': public_scene_for_prompt if public_scene_for_prompt else public_scene,
            'discoverable_clues': discoverable_clues,
            'gm_only': {
                'hidden_facts': gm_only_hidden_facts,
                'discoverable_clues_locked': gm_only_discoverable_locked,
            },
            'clue_records': {'discovered': discovered_clue_records, 'undiscovered': undiscovered_clue_records},
            'visible_clues': discovered_clue_records,
            'discovered_clues': discovered_clue_records,
            'clue_visibility': clue_visibility,
            'pending_leads': active_pending_leads,
            'runtime': runtime,
            'intent': intent,
            'layering_rules': {
                'visible_facts': 'Only visible facts may be directly asserted; align with narration_visibility.visible_facts.',
                'discoverable_clues': 'Reveal only when player investigates/searches/questions/observes closely; with discoverable_hinting, hint without asserting as confirmed truth.',
                'hidden_facts': 'Never reveal directly; use only for implications, NPC behavior, atmosphere, indirect clues.',
            },
        },
        'player_expression_contract': {
            'default_action_style': 'third_person',
            'quoted_speech_allowed': True,
            'preserve_user_expression_format': True,
            'example': 'Galinor asks, "What changed at the north gate?" while examining the notice board.',
        },
    }
    if use_manual_play_compact:
        for key in (
            'fallback_behavior',
            'anti_railroading_contract',
            'context_separation_contract',
            'player_facing_narration_purity_contract',
            'social_response_structure_contract',
            'interaction_continuity_contract',
            'first_mention_contract',
        ):
            payload.pop(key, None)
    return payload

from game.prompt_context_leads import (
    INTERLOCUTOR_DISCUSSION_RECENCY_WINDOW,
    _lead_get,
    _lead_status_value,
    _lead_lifecycle_value,
    _lead_int,
    _lead_type_value,
    _lead_pressure_sort_key,
    _recent_change_signal_rank,
    _recent_lead_changes_sort_key,
    _compact_lead_row,
    build_authoritative_lead_prompt_context,
    _interlocutor_discussion_sort_key,
    _discussion_row_recently_discussed,
    build_interlocutor_lead_discussion_context,
    deterministic_interlocutor_lead_behavior_hints,
)

