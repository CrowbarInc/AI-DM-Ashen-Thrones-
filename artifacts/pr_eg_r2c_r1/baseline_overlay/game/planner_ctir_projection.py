"""Planner-owned CTIR projection, obligation derivation, and response-policy prep for the head/bundle seam.

Moved from :mod:`game.prompt_context` so :mod:`game.planner_head_state` and the narration bundle can depend on
planner-local helpers without lazy-importing the full prompt packager. :mod:`game.prompt_context` re-exports
these names for backward compatibility.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Set

from game.leads import filter_pending_leads_for_active_follow_surface
from game.narrative_plan_upstream import SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY
from game.storage import get_scene_state
from game.world import get_world_npc_by_id
from game.world_progression import (
    build_prompt_world_progression_hints,
    compose_ctir_world_progression_slice,
    merge_progression_changed_node_signals,
)

# Compression caps — keep aligned with ``game.prompt_context`` (shared constants).
MAX_RECENT_LOG = 5
MAX_LOG_ENTRY_SNIPPET = 200
MAX_FOLLOW_UP_TOPIC_TOKENS = 6
MAX_RECENT_CONTEXTUAL_LEADS = 4
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

# Classifier-owned intent keys not duplicated into CTIR; preserve from caller for payload only.
_CLASSIFIER_ONLY_INTENT_KEYS: frozenset[str] = frozenset({"allow_discoverable_clues"})

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


def _promote_ctir_resolution_for_engine_reads(resolution_block: dict[str, Any]) -> dict[str, Any]:
    """Copy CTIR ``resolution`` and promote common authoritative_outputs keys for legacy readers."""
    out = dict(resolution_block)
    auth = out.get("authoritative_outputs")
    if isinstance(auth, dict):
        for k in ("resolved_transition", "target_scene_id", "action_id", "originating_scene_id", "clue_id"):
            if k in auth and k not in out:
                out[k] = auth[k]
    return out


def _ctir_to_prompt_semantics(ctir_obj: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map CTIR sections to prompt-local semantics (read-only; never mutates *ctir_obj*)."""
    if not isinstance(ctir_obj, dict):
        return {}
    raw_res = ctir_obj.get("resolution") if isinstance(ctir_obj.get("resolution"), dict) else {}
    resolution_engine = _promote_ctir_resolution_for_engine_reads(raw_res)
    nc_block = ctir_obj.get("noncombat") if isinstance(ctir_obj.get("noncombat"), dict) else {}
    nc_narr = nc_block.get("narration_constraints") if isinstance(nc_block.get("narration_constraints"), dict) else {}
    if nc_narr:
        # Passthrough only: map engine-authored ``narration_constraints`` into the legacy
        # ``resolution.social`` slots read by obligation helpers—no free-text inference.
        soc = dict(resolution_engine.get("social") or {}) if isinstance(resolution_engine.get("social"), dict) else {}
        for k in ("npc_reply_expected", "reply_kind", "information_gate", "gated_information"):
            if k in nc_narr:
                soc[k] = nc_narr[k]
        resolution_engine = {**resolution_engine, "social": soc}
    intent_block = ctir_obj.get("intent") if isinstance(ctir_obj.get("intent"), dict) else {}
    interaction_block = ctir_obj.get("interaction") if isinstance(ctir_obj.get("interaction"), dict) else {}
    world_block = ctir_obj.get("world") if isinstance(ctir_obj.get("world"), dict) else {}
    anchors_block = ctir_obj.get("narrative_anchors") if isinstance(ctir_obj.get("narrative_anchors"), dict) else {}
    return {
        "intent": dict(intent_block),
        "resolution": resolution_engine,
        "noncombat": dict(nc_block),
        "interaction": dict(interaction_block),
        "world": dict(world_block),
        "narrative_anchors": dict(anchors_block),
    }


def _session_view_overlay_from_ctir_interaction(
    session_view: dict[str, Any],
    interaction_sem: Mapping[str, Any] | None,
    *,
    session: dict[str, Any] | None,
    world: Mapping[str, Any] | None,
    public_scene: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Apply CTIR ``interaction`` over compressed session_view for turn-local semantics."""
    if not isinstance(interaction_sem, dict) or not interaction_sem:
        return session_view
    out = dict(session_view)
    at = str(interaction_sem.get("active_target_id") or "").strip()
    if at and session is not None:
        # CTIR intentionally does not own roster canonicalization; reading canonical state
        canon = canonical_interaction_target_npc_id(session, at)
        eff = canon or at
        out["active_interaction_target_id"] = eff
        out["active_interaction_target_name"] = (
            _resolve_active_interaction_target_name(session, world or {}, public_scene or {}, npc_id=eff)
            if eff
            else None
        )
    mode = interaction_sem.get("interaction_mode")
    if isinstance(mode, str) and mode.strip():
        out["interaction_mode"] = str(mode).strip()
    ikind = interaction_sem.get("interaction_kind")
    if isinstance(ikind, str) and ikind.strip():
        out["active_interaction_kind"] = str(ikind).strip()
    return out

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

    **Ownership:** this function **materializes the shipped contract shape** for prompts and downstream
    readers (planner/structure). Authoritative post-generation checks, bounded repairs, and
    ``response_delta_*`` legality metadata are owned by the gate stack
    (``response_delta_enforcement_and_repair`` in :mod:`game.validation_layer_contracts`), not by
    prompt assembly.
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
    This module remains the canonical prompt-contract bundling home; downstream
    consumers should read the shipped bundle rather than redefine it elsewhere.
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
def _world_progression_projection_for_prompt(
    *,
    ctir_obj: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> tuple[Dict[str, Any] | None, List[str]]:
    """Prefer CTIR ``world.progression``; else bounded backbone export (not a second authority)."""
    prog: Dict[str, Any] | None = None
    if ctir_obj is not None:
        wb = ctir_obj.get("world") if isinstance(ctir_obj.get("world"), dict) else {}
        pr = wb.get("progression") if isinstance(wb.get("progression"), dict) else None
        if pr:
            prog = dict(pr)
    if prog is None and isinstance(world, dict):
        merged = merge_progression_changed_node_signals(
            resolution=resolution if isinstance(resolution, dict) else None,
            world=world,
            session=session if isinstance(session, dict) else None,
        )
        prog = compose_ctir_world_progression_slice(world, changed_node_ids=merged)
    lines = build_prompt_world_progression_hints(prog)
    return prog, lines


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

    out_sv = {
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
    if bool(session.get(SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY)):
        out_sv['resume_entry'] = True
    return out_sv


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
    # Block B: prompt_context must not infer transitions (time/location/scene movement)
    # from resolution semantics, state_changes, or CTIR-derived target_scene_id deltas.
    # Transition requirements are consumed only from narrative_plan.transition_node (root-level),
    # applied downstream in build_narration_context as a pass-through / traceable seam.
    must_advance_scene = False

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
