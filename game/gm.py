from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import copy
import json
import os
import re
import time
from contextvars import ContextVar
from game.config import get_openai_api_key
from game.model_routing import resolve_model_route
from game.utils import slugify
from game.exploration import EXPLORATION_KINDS
from game.social import (
    SOCIAL_KINDS,
    classify_social_followup_dimension,
    empty_subject_retains_topic_pressure_key,
    explicit_player_topic_anchor_state,
)
from game.prompt_context import (
    NO_VALIDATOR_VOICE_RULE,
    RESPONSE_RULE_PRIORITY,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    _answer_pressure_followup_details,
    _compress_recent_log,
    build_narration_context,
    canonical_interaction_target_npc_id,
)
from game.storage import (
    get_effective_scene,
    load_log,
    get_scene_runtime,
    SCENE_MOMENTUM_KINDS,
    SCENE_MOMENTUM_TAG_PREFIX,
)
from game.diegetic_fallback_narration import render_scene_momentum_diegetic_append
from game.realization_provenance import (
    GPT_BUDGET_OR_PROVIDER_FAILURE,
    attach_realization_fallback_family,
)
from game.clues import get_clue_presentation, get_known_clues_with_presentation
from game.leads import filter_pending_leads_for_active_follow_surface
from game.interaction_context import (
    addressable_scene_npc_id_universe,
    assert_valid_speaker,
    inspect as inspect_interaction_context,
)
from game.social_exchange_fallback_catalog import (
    apply_social_exchange_retry_fallback_gm,
    apply_strict_social_terminal_dialogue_fallback_if_needed,
    minimal_social_emergency_fallback_line,
    repair_strict_social_terminal_dialogue_fallback_if_needed,
    strict_social_terminal_dialogue_fallback_valid,
)
from game.social_exchange_policy import (
    effective_strict_social_resolution_for_emission,
    is_scene_directed_watch_question,
    looks_like_npc_directed_question,
    strict_social_emission_will_apply,
)
from game.social_exchange_validation import is_route_illegal_global_or_sanitizer_fallback_text

COMBAT_KINDS = frozenset({
    'initiative', 'attack', 'spell', 'skill_check',
    'enemy_attack', 'enemy_turn_skipped', 'end_turn',
})

SOCIAL_CHECK_KINDS = frozenset({'persuade', 'intimidate', 'deceive', 'barter', 'recruit'})

def _session_social_authority(session: Dict[str, Any] | None) -> bool:
    """True when a social interlocutor is authoritative for this turn (prompt + sanitization)."""
    if not isinstance(session, dict):
        return False
    ic = inspect_interaction_context(session)
    return (
        str(ic.get("interaction_mode") or "").strip().lower() == "social"
        and bool(str(ic.get("active_interaction_target_id") or "").strip())
    )

_STOCK_WARNING_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bbe careful who you trust\b", re.IGNORECASE), "be careful who you trust"),
    (re.compile(r"\bkeep your wits about you\b", re.IGNORECASE), "keep your wits about you"),
    (re.compile(r"\bthese are dangerous times\b", re.IGNORECASE), "these are dangerous times"),
    (re.compile(r"\bnot everyone is friendly to newcomers\b", re.IGNORECASE), "not everyone is friendly to newcomers"),
)

UNCERTAINTY_CATEGORIES: tuple[str, ...] = (
    "unknown_identity",
    "unknown_location",
    "unknown_motive",
    "unknown_method",
    "unknown_quantity",
    "unknown_feasibility",
)
UNCERTAINTY_SOURCE_MODES: tuple[str, ...] = (
    "npc_ignorance",
    "scene_ambiguity",
    "procedural_insufficiency",
)

_PASSIVE_ACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bhold(?:ing)?\s+position\b", re.IGNORECASE), "hold_position"),
    (re.compile(r"\bremain(?:ing)?\s+silent\b", re.IGNORECASE), "remain_silent"),
    (re.compile(r"\bstay(?:ing)?\s+silent\b", re.IGNORECASE), "remain_silent"),
    (re.compile(r"\bsay(?:ing)?\s+nothing\b", re.IGNORECASE), "remain_silent"),
    (re.compile(r"\bkeep(?:ing)?\s+watch\b", re.IGNORECASE), "watch"),
    (re.compile(r"\blook(?:ing)?\s+around\b", re.IGNORECASE), "observe"),
    (re.compile(r"\bwait(?:ing)?\b", re.IGNORECASE), "wait"),
    (re.compile(r"\bwatch(?:ing)?\b", re.IGNORECASE), "watch"),
    (re.compile(r"\bobserve(?:s|d|ing)?\b", re.IGNORECASE), "observe"),
)
_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"“”'‘’]"),
    re.compile(r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|orders?|interrupts?|thrusts?|hands?|points?)\b", re.IGNORECASE),
)
_SCENE_TENSION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bguard"),
    re.compile(r"\bwatch"),
    re.compile(r"\bsuspicious"),
    re.compile(r"\bmissing patrol"),
    re.compile(r"\brumou?r"),
    re.compile(r"\bnotice board|\bnoticeboard"),
    re.compile(r"\bcurfew"),
    re.compile(r"\btax"),
    re.compile(r"\brefugee"),
)

_RULE_PRIORITY_PROMPT_BLOCK = "\n".join(
    f"{idx}. {label}" for idx, (_, label) in enumerate(RESPONSE_RULE_PRIORITY, start=1)
)
_SYSTEM_PROMPT_HEADER = (
    "You are the game master for a solo Pathfinder 1e inspired browser campaign.\n\n"
    "Rule Priority Hierarchy (higher rules override lower ones):\n"
    f"{_RULE_PRIORITY_PROMPT_BLOCK}\n"
    f"{RULE_PRIORITY_COMPACT_INSTRUCTION}\n\n"
    "Always answer the player. Prefer partial truth over refusal. Never output meta explanations.\n"
    f"{NO_VALIDATOR_VOICE_RULE}\n"
    "Rules explanation belongs only to explicit OC/adjudication lanes owned by the app; never let that voice bleed into standard narration.\n\n"
)


def detect_stock_warning_filler_repetition(player_facing_text: str) -> List[str]:
    """Detect repeated stock warning phrases within a short span (single output).

    This is intentionally small and targeted: it only looks for a few known
    immersion-breaking warnings and triggers only when they cluster/repeat.
    """
    if not isinstance(player_facing_text, str):
        return []
    txt = " ".join(player_facing_text.split())
    if not txt:
        return []

    matches: List[tuple[int, str]] = []
    per_phrase_counts: Dict[str, int] = {}
    for pattern, label in _STOCK_WARNING_PATTERNS:
        for m in pattern.finditer(txt):
            matches.append((int(m.start()), label))
            per_phrase_counts[label] = per_phrase_counts.get(label, 0) + 1

    if not matches:
        return []

    # Trigger when the same stock phrase repeats, or when multiple stock phrases
    # appear close together (cluster) inside one short reply.
    if any(c >= 2 for c in per_phrase_counts.values()):
        return sorted([f"stock_warning_repeat:{k}" for k, v in per_phrase_counts.items() if v >= 2])

    if len(matches) >= 2:
        starts = [pos for pos, _ in matches]
        if (max(starts) - min(starts)) <= 520:
            uniq = sorted({label for _, label in matches})
            return [f"stock_warning_cluster:{u}" for u in uniq]

    return []


def _split_reply_sentences(text: str) -> List[str]:
    """Split paragraphs into sentence-like units for targeted cleanup."""
    if not isinstance(text, str):
        return []
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    return parts



# Linguistic protocol only. It does not grant authority. Canonical acts stay in
# gm_resolution_decision, the decision-facing answer recipe, and response_policy.
EPISTEMIC_REALIZATION_PROTOCOL = (
    "EPISTEMIC REALIZATION: On an interpretation, or when the player offers a hypothesis, "
    "state the authorized observations first. If the decision permits inference, add one "
    "possibility tied to those observations and say explicitly that cause, actor, time, and "
    "history stay unresolved. Do not add a mechanism, setting, maintenance history, or causal "
    "chain the observations do not contain. Do not use certainty wording for inferred or "
    "hypothetical material, and do not attach that wording to the observations in the same "
    "sentence. A player hypothesis stays hypothetical: the visible facts may be compatible "
    "with it, and observation alone does not settle it."
)
_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE = (
    "If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic."
)

SYSTEM_PROMPT = _SYSTEM_PROMPT_HEADER + """The application owns authoritative mechanics, state, and persistence. You realize the supplied turn: narrate within the payload, propose only through the structured lanes, and never invent dice results or override app-supplied resolutions.
Use the shipped response_policy, visibility data, resolution_contract, gm_resolution_decision, and decision_facing_answer_recipe as the operational guide for this turn. The recipe is guidance only; it grants no new authority.
Answer direct questions first. If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic. Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.
Treat player input as an action declaration. resolved_exploration_action; scene_transition_already_occurred; do not restate; third person; quoted in-character speech; do not restate or paraphrase the player's input.
Never speak as a validator, analyst, system, or referee of canon in standard narration. Spoiler safeguard: no hidden_facts, clues, planner labels, JSON, or engine scaffolding.
Specific NPC replies should provide a concrete answer, partial specific, source, or usable next step when the NPC can plausibly know one. Mundane NPC dialogue and low-stakes texture may be bounded incidental realization; unsupported durable facts require the structured lanes.
When app-resolved mechanics, scene transitions, speaker selection, visibility, or narration obligations are present, follow them exactly. Do not choose the player's next action or turn a lead into a mandatory path unless authoritative state already imposes that constraint.
Question resolution rule: direct answer (first sentence). Scene momentum rule: every 2-3 exchanges tag scene_momentum:<kind>, including consequence_or_opportunity.

Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
{
  "declared_claims": [
    {
      "declaration_id": "string",
      "declaration_mode": "realize|propose",
      "source_claim_id": null | "claim_id_from_gm_resolution_decision",
      "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
      "semantic_identity": {},
      "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
      "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
      "modality": "established|possible|hypothetical|unresolved",
      "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
      "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
      "text": "short internal claim text"
    }
  ],
  "narration": "string",
  "player_facing_text": "same string as narration for temporary legacy compatibility",
  "tags": ["string"],
  "improvisation_proposals": null | [
    {
      "kind": "incidental_fact|npc_claim|consequential_proposal",
      "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
      "content": "string",
      "scope": "turn|scene|session",
      "consequence_level": "none|low|incidental",
      "source": "dm_improvisation|npc:<id>|observation",
      "speaker_id": null | "npc_id",
      "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
    }
  ],
  "scene_update": null | {
    "visible_facts_add": ["string"],
    "discoverable_clues_add": ["string"],
    "hidden_facts_add": ["string"],
    "mode": "exploration|combat|social|travel"
  },
  "activate_scene_id": null | "scene_id",
  "new_scene_draft": null | {
    "id": "string",
    "location": "string",
    "summary": "string",
    "mode": "exploration",
    "visible_facts": ["string"],
    "discoverable_clues": ["string"],
    "hidden_facts": ["string"],
    "exits": [{"label":"string","target_scene_id":"string"}],
    "enemies": []
  },
  "world_updates": null | {
    "append_events": ["string"],
    "projects": [],
    "assets": [],
    "factions": [],
    "world_state": { "flags": {}, "counters": {}, "clocks": {} }
  },
  "suggested_action": null | {
    "action_type": "attack|cast_spell|skill_check|freeform|none",
    "attack_id": null,
    "spell_id": null,
    "skill_id": null,
    "target_id": null,
    "modifiers": []
  },
  "debug_notes": "string"
}

STRUCTURED CLAIM DECLARATION RULE:
Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.

BOUNDED IMPROVISATION AUTHORITY:
You may invent ordinary low-consequence details only by expressing them in player_facing_text AND adding a matching improvisation_proposals entry.
Use kind "incidental_fact" for mundane sensory/service/background details such as food composition, mannerisms, local color, ordinary refusals, and low-stakes connective social detail.
Use kind "npc_claim" for something a speaker reports, believes, or speculates; set epistemic_status to rumor/hearsay/uncertain/speculative unless it is grounded in supplied state.
Do not use bounded improvisation for mechanics, inventory changes, clues, hidden facts, secret passages, factions, major geography/history, quest-critical facts, or player decisions. Mark such attempted material as consequential_proposal rather than presenting it as truth.
Accepted bounded improvisation is runtime continuity only; it is not authored world truth.
"""
if SYSTEM_PROMPT.count(_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE) != 1:
    raise RuntimeError("PR-BT abstract epistemic sentence was not found exactly once")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace(_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE, EPISTEMIC_REALIZATION_PROTOCOL, 1)

NARRATION_ONLY_RESPONSE_CONTRACT = (
    "NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: "
    '{"narration": "player-facing response"}. '
    "Do not include other fields. The application will normalize this internally."
)
NARRATION_ONLY_SYSTEM_PROMPT = _SYSTEM_PROMPT_HEADER + """The application owns authoritative mechanics, state, and persistence. You realize the supplied turn as player-facing narration only and never invent dice results or override app-supplied resolutions.
Use the shipped response_policy, visibility data, resolution_contract, gm_resolution_decision, and decision_facing_answer_recipe as the operational guide for this turn. The recipe is guidance only; it grants no new authority.
Answer direct questions first. Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.
Treat player input as an action declaration. resolved_exploration_action; scene_transition_already_occurred; do not restate; third person; quoted in-character speech; do not restate or paraphrase the player's input.
Never speak as a validator, analyst, system, or referee of canon in standard narration. Spoiler safeguard: no hidden_facts, clues, planner labels, JSON, or engine scaffolding.
Specific NPC replies should provide a concrete answer, partial specific, source, or usable next step when the NPC can plausibly know one. Mundane NPC dialogue and low-stakes texture may be bounded incidental realization; unsupported durable facts are not authorized by this provider contract.
When app-resolved mechanics, scene transitions, speaker selection, visibility, or narration obligations are present, follow them exactly. Do not choose the player's next action or turn a lead into a mandatory path unless authoritative state already imposes that constraint.
Question resolution rule: direct answer (first sentence). Scene momentum rule: every 2-3 exchanges tag scene_momentum:<kind>, including consequence_or_opportunity.

""" + NARRATION_ONLY_RESPONSE_CONTRACT


def classify_player_intent(user_text: str) -> Dict[str, Any]:
    """Deterministic rule-based classifier for player intent."""
    text = (user_text or '').strip()
    t = text.lower()
    labels: List[str] = []

    # Adversarial / meta-knowledge queries: do NOT grant clue access.
    adversarial_phrases = (
        'what am i not being told',
        'state the secret motivation',
        'state the secret motive',
        'summarize the hidden reason',
        'summarise the hidden reason',
        'tell me the twist',
        'tell me the secret',
    )
    if any(p in t for p in adversarial_phrases):
        labels.append('general')
        return {
            'raw_text': text,
            'labels': labels or ['general'],
            'allow_discoverable_clues': False,
            'confidence': 'rule_based',
        }

    # Obvious combat cues.
    if any(k in t for k in ('attack', 'strike', 'shoot', 'stab', 'cast ', 'fireball', 'charge')):
        labels.append('combat')

    # Travel / movement cues.
    if any(k in t for k in ('go to ', 'walk to ', 'head to ', 'travel to ', 'move toward', 'move towards', 'journey to ', 'leave for ', 'return to ')):
        labels.append('travel')

    # Downtime cues.
    if any(k in t for k in ('rest', 'sleep', 'make camp', 'set up camp', 'prepare spells', 'study spells', 'craft ', 'train ', 'research ')):
        labels.append('downtime')

    # Social probing / questioning.
    if any(k in t for k in ('question ', 'ask ', 'ask the ', 'ask around', 'interrogate', 'press the', 'probe ', 'chat up', 'talk to', 'speak with', 'gather rumors', 'gather rumours')):
        labels.append('social_probe')

    # Investigative searching / scrutiny.
    if any(k in t for k in (
        'search', 'search the', 'search for', 'inspect', 'examine', 'study ', 'look over', 'look for', 'check for', 'go through', 'rifle through', 'dig through',
        'investigate', 'look under', 'look behind', 'look inside',
    )):
        if 'observation' not in labels:
            labels.append('investigation')

    # Observational descriptions that are more than idle chit-chat.
    if any(k in t for k in (
        'look around', 'scan the', 'scan around', 'survey the', 'take in the room', 'what do i notice', 'what do i see', 'look at the', 'watch the crowd',
        'watch people', 'observe the', 'glance around',
    )):
        labels.append('observation')

    for pattern, _marker in _PASSIVE_ACTION_PATTERNS:
        if pattern.search(text):
            labels.append('passive_pause')
            break

    # Fallback if nothing matched.
    if not labels:
        labels.append('general')

    allow_clues = any(lbl in ('investigation', 'social_probe') for lbl in labels)

    return {
        'raw_text': text,
        'labels': labels,
        'allow_discoverable_clues': allow_clues,
        'confidence': 'rule_based',
    }


def allow_discoverable_clues(user_text: str) -> bool:
    """Backward-compatible wrapper around the new classifier."""
    info = classify_player_intent(user_text)
    return bool(info.get('allow_discoverable_clues'))


def _scene_layers(scene_envelope: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any], List[str]]:
    """Extract public scene, discoverable clues (raw), and hidden facts."""
    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get('visible_facts', []) if isinstance(scene.get('visible_facts'), list) else []
    discoverable = scene.get('discoverable_clues', []) if isinstance(scene.get('discoverable_clues'), list) else []
    hidden = scene.get('hidden_facts', []) if isinstance(scene.get('hidden_facts'), list) else []

    public_scene = {
        'id': scene.get('id'),
        'location': scene.get('location'),
        'summary': scene.get('summary'),
        'mode': scene.get('mode'),
        'visible_facts': visible,
        'opening_seed_facts': scene.get('opening_seed_facts', []),
        'journal_seed_facts': scene.get('journal_seed_facts', []),
        'campaign_spine_opening_facts': scene.get('campaign_spine_opening_facts', []),
        'spine_opening_facts': scene.get('spine_opening_facts', []),
        'campaign_spine': scene.get('campaign_spine', {}),
        'scenario_spine': scene.get('scenario_spine', {}),
        'spine': scene.get('spine', {}),
        'exits': scene.get('exits', []),
        'enemies': scene.get('enemies', []),
    }
    return public_scene, discoverable, hidden


def normalize_clue_record(clue: Any) -> Dict[str, Any]:
    """Normalize a discoverable clue into a dict record.

    Supports legacy string clues and richer dict forms. Structured clues may include:
    - leads_to_scene: scene_id to explore
    - leads_to_npc: NPC to question
    - leads_to_rumor: rumor hook for social probing
    """
    if isinstance(clue, dict):
        text = str(clue.get('text', '')).strip()
        cid = clue.get('id') or slugify(text or 'clue')
        out: Dict[str, Any] = {
            'id': cid,
            'text': text,
            'reveal_requires': list(clue.get('reveal_requires', [])) if isinstance(clue.get('reveal_requires'), list) else [],
            'links_to': list(clue.get('links_to', [])) if isinstance(clue.get('links_to'), list) else [],
        }
        for key in ('leads_to_scene', 'leads_to_npc', 'leads_to_rumor'):
            val = clue.get(key)
            if val is not None and isinstance(val, str) and val.strip():
                out[key] = val.strip()
        return out
    # Legacy string form.
    text = str(clue or '').strip()
    cid = slugify(text or 'clue')
    return {
        'id': cid,
        'text': text,
        'reveal_requires': [],
        'links_to': [],
    }




_ECHO_TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
_DOUBLE_QUOTED_SPEECH_PATTERN = re.compile(r'["\u201c\u201d]([^"\u201c\u201d]{3,240})["\u201c\u201d]')
_SINGLE_QUOTED_SPEECH_PATTERN = re.compile(
    r"(?:(?<=^)|(?<=[\s(\[{]))['\u2018\u2019]([^'\u2018\u2019]{3,240})['\u2018\u2019](?=$|[\s)\]}.,!?;:])"
)
_CAPITALIZED_TOKEN_PATTERN = re.compile(r"\b[A-Z][a-z]{2,}\b")
_CAPITALIZED_NON_ENTITY_WORDS = frozenset(
    {
        "Rumor",
        "Whispers",
        "No",
        "Yes",
        "If",
        "Then",
        "The",
        "They",
        "There",
        "This",
        "That",
        "All",
    }
)
_FOLLOWUP_PRESS_TOKENS: tuple[str, ...] = (
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
_TOPIC_STOPWORDS = frozenset({
    "what", "where", "when", "why", "how", "who", "which",
    "tell", "said", "says", "know", "knew", "think", "heard",
    "about", "again", "still", "really", "actually", "just",
    "there", "here", "them", "they", "their", "then", "than",
    "with", "from", "into", "onto", "over", "under", "near",
    "this", "that", "these", "those", "your", "youre", "you're",
    "have", "has", "had", "can", "could", "would", "should",
    "does", "did", "is", "are", "was", "were", "will",
})
_TOPIC_ALIAS_MAP: dict[str, str] = {
    "patrols": "patrol",
    "report": "report",
    "reports": "report",
    "crossroad": "crossroads",
    "junction": "crossroads",
    "intersections": "crossroads",
    "intersection": "crossroads",
    "figures": "figure",
    "shadowy": "shadow",
    "shadows": "shadow",
    "hooded": "shadow",
    "attacked": "attack",
    "attacker": "attack",
    "attackers": "attack",
    "responsible": "behind",
    "mastermind": "behind",
    "culprit": "behind",
    "planning": "plan",
    "planned": "plan",
    "happened": "happen",
}
_TOPIC_CLUSTER_HINTS: dict[str, tuple[str, ...]] = {
    "missing_patrol": (
        "missing patrol",
        "patrol report",
        "lost patrol",
        "patrol notice",
        "where is the patrol",
    ),
    "shadowy_figures": (
        "shadowy figure",
        "shadow figure",
        "those figures",
        "hooded figure",
        "dark figure",
        "watcher",
    ),
    "responsible_party": (
        "who is behind",
        "who's behind",
        "who attacked",
        "who did this",
        "who is responsible",
        "who ordered",
        "what are they planning",
        "what are they after",
    ),
    "crossroads_incident": (
        "what happened at the crossroads",
        "cross roads",
        "at the crossroads",
        "near the crossroads",
        "crossroads attack",
    ),
}
_TOPIC_CLUSTER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "missing_patrol": ("missing", "patrol", "report", "notice"),
    "shadowy_figures": ("shadow", "figure", "watcher", "hood"),
    "responsible_party": ("behind", "attack", "plan", "order", "responsible"),
    "crossroads_incident": ("crossroads", "happen", "incident", "attack"),
}
_TOPIC_PROGRESS_ACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(ask|press|follow|track|check|inspect|watch|question|speak to|meet|go to|head to|search|read)\b", re.IGNORECASE),
    re.compile(r"\b(now|immediately|before dusk|before dawn|tonight)\b", re.IGNORECASE),
)
_TOPIC_STASIS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(no one knows|nobody knows|unclear|rumou?r says|whispers say|hard to tell)\b", re.IGNORECASE),
    re.compile(r"\b(still don't know|still do not know|can't say|cannot say)\b", re.IGNORECASE),
)
_TOPIC_ESCALATION_CUES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(interrupts?|cuts through|arrives?|rushes in|shouts?)\b", re.IGNORECASE),
    re.compile(r"\b(refuses?|won't answer|will not answer|turns away|goes silent)\b", re.IGNORECASE),
    re.compile(r"\b(hands you|passes you|torn dispatch|fresh clue|new lead)\b", re.IGNORECASE),
    re.compile(r"\b(scene_momentum:)\b", re.IGNORECASE),
)
_TOPIC_PLACE_WORDS = frozenset(
    {
        "gate",
        "road",
        "crossroads",
        "checkpoint",
        "notice",
        "board",
        "tavern",
        "alley",
        "bridge",
        "market",
        "square",
    }
)


def _stem_topic_token(token: str) -> str:
    t = str(token or "").strip().lower()
    if not t:
        return ""
    for suffix in ("ing", "ed", "es", "s"):
        if t.endswith(suffix) and len(t) >= (len(suffix) + 4):
            t = t[: -len(suffix)]
            break
    return _TOPIC_ALIAS_MAP.get(t, t)


def _topic_tokens_for_matching(text: str) -> List[str]:
    low = " ".join(str(text or "").strip().lower().split())
    if not low:
        return []
    out: List[str] = []
    seen: set[str] = set()
    for raw in _ECHO_TOKEN_PATTERN.findall(low):
        tok = _stem_topic_token(raw)
        if len(tok) < 4 or tok in _TOPIC_STOPWORDS:
            continue
        if tok in seen:
            continue
        out.append(tok)
        seen.add(tok)
        if len(out) >= 14:
            break
    return out


def normalize_topic(player_input: str, scene_context: Dict[str, Any] | None = None) -> str:
    """Normalize semantically similar investigative prompts into a stable topic key."""
    text = " ".join(str(player_input or "").strip().lower().split())
    if not text:
        return "unknown_topic"
    tokens = set(_topic_tokens_for_matching(text))
    scores: dict[str, float] = {}
    for key, phrases in _TOPIC_CLUSTER_HINTS.items():
        score = 0.0
        for phrase in phrases:
            if phrase in text:
                score += 2.2
        for kw in _TOPIC_CLUSTER_KEYWORDS.get(key, ()):
            if kw in tokens:
                score += 1.0
        scores[key] = score
    if scene_context and isinstance(scene_context, dict):
        visible = scene_context.get("visible_facts")
        if isinstance(visible, list):
            visible_low = " ".join(str(v).lower() for v in visible if isinstance(v, str))
            if "missing patrol" in visible_low and "patrol" in tokens:
                scores["missing_patrol"] = scores.get("missing_patrol", 0.0) + 0.6
            if "crossroads" in visible_low and ("crossroads" in tokens or "happen" in tokens):
                scores["crossroads_incident"] = scores.get("crossroads_incident", 0.0) + 0.6
    best_key = max(scores.items(), key=lambda item: item[1])[0]
    if "crossroads" in tokens and best_key == "responsible_party":
        return "crossroads_incident"
    if scores.get(best_key, 0.0) >= 1.6:
        return best_key
    if tokens:
        return "topic:" + slugify("-".join(sorted(tokens)[:3]))
    return "unknown_topic"


def _topic_speaker_key(session: Dict[str, Any], resolution: Dict[str, Any] | None) -> str:
    social = (resolution or {}).get("social") if isinstance((resolution or {}).get("social"), dict) else {}
    speaker_id = str(social.get("npc_id") or "").strip()
    if speaker_id:
        return speaker_id
    interaction = session.get("interaction_context") if isinstance(session.get("interaction_context"), dict) else {}
    active_target = str(interaction.get("active_interaction_target_id") or "").strip()
    return active_target or "__scene__"


def _answer_pressure_topic_bridge(ap: Dict[str, Any] | None) -> bool:
    """True when Block 1 answer-pressure signals say this turn continues the prior answer thread.

    Used to keep ``topic_pressure`` on the same bucket when normalize_topic would fragment
    (e.g. bare ``Why?``) without running a second weak phrase detector.
    """
    if not isinstance(ap, dict) or not ap:
        return False
    if not ap.get("same_interlocutor_followup") or not ap.get("prior_answer_substantive"):
        return False
    return bool(
        ap.get("answer_pressure_followup_detected")
        or ap.get("correction_reask_followup_detected")
        or ap.get("short_followup_anchor_detected")
        or ap.get("contradiction_followup_detected")
        or ap.get("explanation_followup_detected")
        or ap.get("insufficiency_followup_detected")
        or ap.get("anchor_followup_detected")
        or ap.get("explanation_of_recent_anchor_followup")
        or ap.get("recent_reference_clarification_detected")
    )


def register_topic_probe(
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    player_text: str,
    resolution: Dict[str, Any] | None = None,
    recent_log: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Register one player investigative probe for per-topic pressure tracking."""
    player = str(player_text or "").strip()
    if not player or not _is_direct_player_question(player):
        return {"tracked": False}
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return {"tracked": False}
    runtime = get_scene_runtime(session, scene_id)
    topic_key = normalize_topic(player, scene_context=scene)
    previous_topic = str(runtime.get("topic_pressure_last_topic_key") or "").strip()
    anaphora_followup = bool(re.search(r"\b(they|them|this|that|those|it|behind it|planning)\b", player.lower()))
    if explicit_player_topic_anchor_state(player).get("active"):
        anaphora_followup = False
    if previous_topic and topic_key != previous_topic and anaphora_followup:
        topic_key = previous_topic
    if (
        previous_topic
        and topic_key != previous_topic
        and not explicit_player_topic_anchor_state(player).get("active")
        and empty_subject_retains_topic_pressure_key(player)
    ):
        topic_key = previous_topic
    if recent_log is not None and previous_topic and topic_key != previous_topic:
        icx = session.get("interaction_context") if isinstance(session.get("interaction_context"), dict) else {}
        ap_bridge = _answer_pressure_followup_details(
            player_input=player,
            recent_log_compact=_compress_recent_log(recent_log),
            narration_obligations={},
            session_view={"active_interaction_target_id": str(icx.get("active_interaction_target_id") or "").strip()},
        )
        if _answer_pressure_topic_bridge(ap_bridge) and not bool(
            explicit_player_topic_anchor_state(player).get("active")
        ):
            topic_key = previous_topic
    speaker_key = _topic_speaker_key(session, resolution)
    pressure = runtime.get("topic_pressure")
    if not isinstance(pressure, dict):
        pressure = {}
        runtime["topic_pressure"] = pressure
    entry = pressure.get(topic_key)
    if not isinstance(entry, dict):
        entry = {
            "repeat_count": 0,
            "low_progress_streak": 0,
            "progress_score_total": 0.0,
            "last_answer": "",
            "last_turn": 0,
            "speaker_targets": {},
        }
        pressure[topic_key] = entry
    prev_probe_dim = str(entry.get("last_probe_dimension") or "").strip()
    entry["previous_probe_dimension"] = prev_probe_dim
    entry["last_probe_dimension"] = classify_social_followup_dimension(player)
    turn_counter = int(session.get("turn_counter", 0) or 0)
    if int(entry.get("last_turn", 0) or 0) and (turn_counter - int(entry.get("last_turn", 0) or 0) > 6):
        entry["repeat_count"] = 0
        entry["low_progress_streak"] = 0
    entry["repeat_count"] = int(entry.get("repeat_count", 0) or 0) + 1
    entry["last_turn"] = turn_counter
    entry["last_player_input"] = player[:260]
    targets = entry.get("speaker_targets")
    if not isinstance(targets, dict):
        targets = {}
        entry["speaker_targets"] = targets
    s_entry = targets.get(speaker_key)
    if not isinstance(s_entry, dict):
        s_entry = {"repeat_count": 0, "low_progress_streak": 0, "patience": 3, "last_turn": 0}
        targets[speaker_key] = s_entry
    if int(s_entry.get("last_turn", 0) or 0) and (turn_counter - int(s_entry.get("last_turn", 0) or 0) > 6):
        s_entry["repeat_count"] = 0
        s_entry["low_progress_streak"] = 0
    s_entry["repeat_count"] = int(s_entry.get("repeat_count", 0) or 0) + 1
    s_entry["last_turn"] = turn_counter
    last_topic = previous_topic
    if last_topic and last_topic != topic_key:
        for key, val in list(pressure.items()):
            if key == topic_key or not isinstance(val, dict):
                continue
            val["repeat_count"] = max(0, int(val.get("repeat_count", 0) or 0) - 1)
            val["low_progress_streak"] = max(0, int(val.get("low_progress_streak", 0) or 0) - 1)
    runtime["topic_pressure_last_topic_key"] = topic_key
    runtime["topic_pressure_current"] = {
        "topic_key": topic_key,
        "speaker_key": speaker_key,
        "turn": turn_counter,
        "player_text": player[:260],
        "interaction_kind": str((session.get("interaction_context") or {}).get("active_interaction_kind") or "").strip().lower(),
        "interaction_mode": str((session.get("interaction_context") or {}).get("interaction_mode") or "").strip().lower(),
        "social_intent_class": str(((resolution or {}).get("social") or {}).get("social_intent_class") or "").strip().lower(),
        "npc_name": str(((resolution or {}).get("social") or {}).get("npc_name") or "").strip(),
    }
    return {
        "tracked": True,
        "scene_id": scene_id,
        "topic_key": topic_key,
        "speaker_key": speaker_key,
        "repeat_count": int(entry.get("repeat_count", 0) or 0),
        "speaker_repeat_count": int(s_entry.get("repeat_count", 0) or 0),
    }


def _topic_progress_score(reply_text: str, previous_answer: str) -> float:
    reply = str(reply_text or "").strip()
    prev = str(previous_answer or "").strip()
    if not reply:
        return 0.0
    if not prev:
        return 1.5
    score = 0.0
    reply_tokens = set(_topic_tokens_for_matching(reply))
    prev_tokens = set(_topic_tokens_for_matching(prev))
    overlap = _overlap_min_ratio(list(reply_tokens), list(prev_tokens))
    if any(pattern.search(reply) for pattern in _TOPIC_ESCALATION_CUES):
        score += 2.0
    action_now = any(pattern.search(reply) for pattern in _TOPIC_PROGRESS_ACTION_PATTERNS)
    action_prev = any(pattern.search(prev) for pattern in _TOPIC_PROGRESS_ACTION_PATTERNS)
    if action_now and not action_prev:
        score += 0.6
    reply_caps = {cap for cap in _CAPITALIZED_TOKEN_PATTERN.findall(reply) if cap not in _CAPITALIZED_NON_ENTITY_WORDS}
    prev_caps = {cap for cap in _CAPITALIZED_TOKEN_PATTERN.findall(prev) if cap not in _CAPITALIZED_NON_ENTITY_WORDS}
    if any(cap not in prev_caps for cap in reply_caps):
        score += 1.0
    reply_nums = set(re.findall(r"\b\d{1,4}\b", reply))
    prev_nums = set(re.findall(r"\b\d{1,4}\b", prev))
    if any(num not in prev_nums for num in reply_nums):
        score += 0.8
    new_places = [t for t in reply_tokens if t in _TOPIC_PLACE_WORDS and t not in prev_tokens]
    if new_places:
        score += 0.7
    if overlap < 0.45:
        novel = [t for t in reply_tokens if t not in prev_tokens]
        if len(novel) >= 3:
            score += 0.6
    has_stasis = any(pattern.search(reply) for pattern in _TOPIC_STASIS_PATTERNS)
    if has_stasis and overlap >= 0.45 and score < 1.0:
        score = 0.0
    if has_stasis and not action_now and not any(cap not in prev_caps for cap in reply_caps) and not any(num not in prev_nums for num in reply_nums):
        # Reworded uncertainty loops are still low progress even when token overlap drops.
        score = min(score, 0.35)
    return score


def _get_topic_pressure_context(
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return {}
    runtime = get_scene_runtime(session, scene_id)
    current = runtime.get("topic_pressure_current")
    if not isinstance(current, dict):
        return {}
    topic_key = str(current.get("topic_key") or "").strip()
    speaker_key = str(current.get("speaker_key") or "__scene__").strip() or "__scene__"
    if not topic_key:
        return {}
    pressure = runtime.get("topic_pressure")
    if not isinstance(pressure, dict):
        return {}
    entry = pressure.get(topic_key)
    if not isinstance(entry, dict):
        return {}
    targets = entry.get("speaker_targets") if isinstance(entry.get("speaker_targets"), dict) else {}
    s_entry = targets.get(speaker_key) if isinstance(targets, dict) and isinstance(targets.get(speaker_key), dict) else {}
    return {
        "scene_id": scene_id,
        "topic_key": topic_key,
        "speaker_key": speaker_key,
        "runtime": runtime,
        "entry": entry,
        "speaker_entry": s_entry,
    }


def _topic_pressure_snapshot_for_reply(
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    reply_text: str,
) -> Dict[str, Any]:
    ctx = _get_topic_pressure_context(session=session, scene_envelope=scene_envelope)
    if not ctx:
        return {"applies": False, "ok": True, "reasons": []}
    entry = ctx["entry"]
    speaker_entry = ctx["speaker_entry"] if isinstance(ctx.get("speaker_entry"), dict) else {}
    prev_answer = str(entry.get("last_answer") or "").strip()
    progress = _topic_progress_score(reply_text, prev_answer)
    repeat_count = int(entry.get("repeat_count", 0) or 0)
    speaker_repeat_count = int(speaker_entry.get("repeat_count", 0) or 0)
    low_streak = int(entry.get("low_progress_streak", 0) or 0)
    speaker_low_streak = int(speaker_entry.get("low_progress_streak", 0) or 0)
    patience = int(speaker_entry.get("patience", 3) or 3)
    effective_low = max(low_streak, speaker_low_streak) + (1 if progress < 1.0 else 0)
    current = ctx["runtime"].get("topic_pressure_current") if isinstance(ctx.get("runtime"), dict) else {}
    interaction_kind = str((current or {}).get("interaction_kind") or "").strip().lower()
    interaction_mode = str((current or {}).get("interaction_mode") or "").strip().lower()
    social_intent_class = str((current or {}).get("social_intent_class") or "").strip().lower()
    npc_name = str((current or {}).get("npc_name") or "").strip()
    should_escalate = speaker_repeat_count >= 3 and progress < 1.0
    if not should_escalate:
        return {"applies": True, "ok": True, "reasons": [], "progress": progress}
    return {
        "applies": True,
        "ok": False,
        "reasons": [
            f"topic_pressure:topic={ctx['topic_key']}",
            f"topic_pressure:repeat_count={repeat_count}",
            f"topic_pressure:speaker_repeat_count={speaker_repeat_count}",
            f"topic_pressure:effective_low_progress={effective_low}",
            f"topic_pressure:progress_score={round(progress, 3)}",
        ],
        "topic_context": {
            "topic_key": ctx["topic_key"],
            "speaker_key": ctx["speaker_key"],
            "repeat_count": repeat_count,
            "speaker_repeat_count": speaker_repeat_count,
            "progress_score": round(progress, 3),
            "previous_answer_snippet": prev_answer[:240],
            "patience": patience,
            "interaction_kind": interaction_kind,
            "interaction_mode": interaction_mode,
            "social_intent_class": social_intent_class,
            "npc_name": npc_name,
        },
    }



def _topic_tokens_for_repetition(text: str) -> List[str]:
    low = " ".join(str(text or "").strip().lower().split())
    if not low:
        return []
    toks = [t for t in _ECHO_TOKEN_PATTERN.findall(low) if len(t) >= 4 and t not in _TOPIC_STOPWORDS]
    seen: set[str] = set()
    out: List[str] = []
    for t in toks:
        if t in seen:
            continue
        out.append(t)
        seen.add(t)
        if len(out) >= 10:
            break
    return out


def _overlap_min_ratio(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    inter = len(sa & sb)
    denom = min(len(sa), len(sb))
    return float(inter) / float(denom or 1)


def followup_soft_repetition_check(
    *,
    player_text: str,
    reply_text: str,
    session: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect 'same topic' follow-up where the model repeats prior answer content.

    Uses only the immediately previous logged turn as reference (no new subsystem).
    """
    player = str(player_text or "").strip()
    reply = str(reply_text or "").strip()
    if not player or not reply:
        return {"applies": False, "ok": True, "reasons": []}
    if len(reply) < 140:
        return {"applies": False, "ok": True, "reasons": []}
    if not _is_direct_player_question(player):
        return {"applies": False, "ok": True, "reasons": []}

    log = load_log()
    if not isinstance(log, list) or not log:
        return {"applies": False, "ok": True, "reasons": []}
    prev = log[-1] if isinstance(log[-1], dict) else {}
    prev_meta = prev.get("log_meta") if isinstance(prev.get("log_meta"), dict) else {}
    prev_req = prev.get("request") if isinstance(prev.get("request"), dict) else {}
    prev_player = str(prev_meta.get("player_input") or prev_req.get("chat") or "").strip()
    prev_gm = prev.get("gm_output") if isinstance(prev.get("gm_output"), dict) else {}
    prev_answer = str(prev_gm.get("player_facing_text") or "").strip()
    if not prev_player or not prev_answer:
        return {"applies": False, "ok": True, "reasons": []}

    cur_low = player.lower()
    press_marker = any(tok in cur_low for tok in _FOLLOWUP_PRESS_TOKENS)
    cur_topic = _topic_tokens_for_repetition(player)
    prev_topic = _topic_tokens_for_repetition(prev_player)
    topic_overlap = _overlap_min_ratio(cur_topic, prev_topic)
    pressed = (topic_overlap >= 0.55 and len(cur_topic) >= 2) or (press_marker and topic_overlap >= 0.35 and len(cur_topic) >= 1)
    if not pressed:
        return {"applies": False, "ok": True, "reasons": []}

    reply_topic = _topic_tokens_for_repetition(reply)
    prev_reply_topic = _topic_tokens_for_repetition(prev_answer)
    answer_overlap = _overlap_min_ratio(reply_topic, prev_reply_topic)
    if answer_overlap < 0.72:
        return {"applies": True, "ok": True, "reasons": []}

    # Allow repetition if the new reply introduces *new* concrete hooks (names/nums) beyond the prior answer.
    prev_caps = set(_CAPITALIZED_TOKEN_PATTERN.findall(prev_answer))
    curr_caps = set(_CAPITALIZED_TOKEN_PATTERN.findall(reply))
    new_caps = [c for c in curr_caps if c not in prev_caps]
    has_new_number = bool(re.search(r"\b\d{1,4}\b", reply)) and not bool(re.search(r"\b\d{1,4}\b", prev_answer))
    prev_tok = set(prev_reply_topic)
    new_info_tokens = [t for t in reply_topic if t not in prev_tok and len(t) >= 5]
    if new_caps or has_new_number or len(new_info_tokens) >= 2:
        return {"applies": True, "ok": True, "reasons": []}

    active_target = str((session.get("interaction_context") or {}).get("active_interaction_target_id") or "").strip()
    reasons = [
        f"followup_soft_repetition:topic_overlap={round(topic_overlap,3)}",
        f"followup_soft_repetition:answer_overlap={round(answer_overlap,3)}",
        "followup_soft_repetition:no_new_detail_detected",
    ]
    return {
        "applies": True,
        "ok": False,
        "reasons": reasons,
        "followup_context": {
            "topic_tokens": cur_topic[:6],
            "previous_player_input": prev_player[:240],
            "previous_answer_snippet": prev_answer[:240],
            "active_interaction_target_id": active_target or None,
        },
    }


def _extract_player_quoted_segments(user_text: str) -> List[str]:
    """Extract likely in-character quoted speech from player input."""
    if not isinstance(user_text, str):
        return []
    text = user_text.strip()
    if not text:
        return []
    out: List[str] = []
    for pattern in (_DOUBLE_QUOTED_SPEECH_PATTERN, _SINGLE_QUOTED_SPEECH_PATTERN):
        for match in pattern.findall(text):
            seg = str(match or '').strip()
            if seg and seg not in out:
                out.append(seg)
    return out


def _opening_sentence_should_skip_echo_check(first_sentence: str) -> bool:
    """NPC dialogue / attribution-led openings legitimately reuse question words (patrol, missing, etc.)."""
    fs = str(first_sentence or "").strip()
    if not fs:
        return False
    if fs.startswith('"') or fs.startswith("\u201c"):
        return True
    if re.match(
        r"^(?:The\s+)?[\w'.-]+\s+(?:says|mutters|replies|answers|asks|adds|grunts)\s*[,:]?\s*[\"“]",
        fs,
        re.IGNORECASE,
    ):
        return True
    if re.match(
        r"^(?:The\s+)?[\w'.-]+\s+(?:frowns|grimaces|shrugs|nods|hesitates)\s*\.\s*[\"“]",
        fs,
        re.IGNORECASE,
    ):
        return True
    return False


def opening_sentence_echoes_player_input(player_facing_text: str, user_text: str) -> bool:
    """Detect strong overlap between opening sentence and player input."""
    if not isinstance(player_facing_text, str) or not isinstance(user_text, str):
        return False
    gm_text = player_facing_text.strip()
    src = user_text.strip()
    if not gm_text or not src:
        return False

    first_sentence = re.split(r"[.!?\n]", gm_text, maxsplit=1)[0].strip()
    if not first_sentence:
        first_sentence = gm_text
    if _opening_sentence_should_skip_echo_check(first_sentence):
        return False
    gm_tokens = _ECHO_TOKEN_PATTERN.findall(first_sentence.lower())
    if len(gm_tokens) < 3:
        # Handle openings that begin with quoted questions, where sentence splitting
        # can collapse to a single token like "Footman".
        gm_tokens = _ECHO_TOKEN_PATTERN.findall(gm_text.lower())[:25]
    src_tokens = _ECHO_TOKEN_PATTERN.findall(src.lower())
    if not gm_tokens or not src_tokens:
        return False

    # Strong direct restatement: opening starts with the same first 3+ tokens.
    shared_prefix = 0
    for gt, st in zip(gm_tokens, src_tokens):
        if gt != st:
            break
        shared_prefix += 1
    if shared_prefix >= 3:
        return True

    # Heavy overlap threshold for looser paraphrase-like openings.
    gm_unique = set(gm_tokens)
    src_unique = set(src_tokens)
    overlap = len(gm_unique & src_unique)
    min_len = min(len(gm_unique), len(src_unique))
    if overlap >= 4 and min_len > 0 and (overlap / min_len) >= 0.6:
        return True

    return False


def opening_sentence_overlaps_player_quote(player_facing_text: str, user_text: str) -> bool:
    """Detect overlap between opening sentence and quoted player speech."""
    if not isinstance(player_facing_text, str) or not isinstance(user_text, str):
        return False
    gm_text = player_facing_text.strip()
    if not gm_text:
        return False
    quoted_segments = _extract_player_quoted_segments(user_text)
    if not quoted_segments:
        return False

    first_sentence = re.split(r"[.!?\n]", gm_text, maxsplit=1)[0].strip()
    if not first_sentence:
        first_sentence = gm_text
    gm_tokens = _ECHO_TOKEN_PATTERN.findall(first_sentence.lower())
    if len(gm_tokens) < 3:
        # Handle openings that begin with quoted questions, where sentence splitting
        # can collapse to a single token like "Footman".
        gm_tokens = _ECHO_TOKEN_PATTERN.findall(gm_text.lower())[:25]
    if not gm_tokens:
        return False

    for quote in quoted_segments:
        quote_tokens = _ECHO_TOKEN_PATTERN.findall(quote.lower())
        if len(quote_tokens) < 3:
            continue

        shared_prefix = 0
        for gt, qt in zip(gm_tokens, quote_tokens):
            if gt != qt:
                break
            shared_prefix += 1
        if shared_prefix >= 2:
            return True

        gm_unique = set(gm_tokens)
        quote_unique = set(quote_tokens)
        overlap = len(gm_unique & quote_unique)
        min_len = min(len(gm_unique), len(quote_unique))
        if overlap >= 3 and min_len > 0 and (overlap / min_len) >= 0.6:
            return True
    return False




_QUESTION_WORDS: tuple[str, ...] = (
    "who", "what", "where", "when", "why", "how", "which",
    "can", "could", "would", "should", "do", "does", "did", "is", "are", "will",
)
_NPC_CONTRACT_ACTION_TOKENS: tuple[str, ...] = (
    "next step", "you can", "you should", "try", "go to", "head to", "ask", "speak to", "talk to",
    "check", "look for", "bring", "show", "tell", "meet", "return to", "follow",
)
_NPC_CONTRACT_REQUIREMENT_TOKENS: tuple[str, ...] = (
    "must", "need", "needs", "require", "requires", "required", "only if", "unless", "provided that",
)
_NPC_CONTRACT_TIME_TOKENS: tuple[str, ...] = ("dawn", "noon", "midnight", "tonight", "tomorrow")


def _resolve_scene_id(scene_envelope: Dict[str, Any]) -> str:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    return str(scene.get("id") or "").strip()


def _resolve_scene_location(scene_envelope: Dict[str, Any]) -> str:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    return str(scene.get("location") or "").strip()


def _scene_visible_facts(scene_envelope: Dict[str, Any]) -> List[str]:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    return [str(v).strip() for v in visible if isinstance(v, str) and str(v).strip()]


_QUESTION_RESOLUTION_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "do", "does", "did", "for", "from", "how", "i", "if", "in", "into",
    "is", "it", "its", "me", "my", "of", "on", "or", "our", "the", "their",
    "then", "there", "these", "they", "this", "to", "up", "was", "we", "were",
    "what", "when", "where", "which", "who", "why", "with", "would", "you", "your",
    "can", "could", "should", "will",
})
_QUESTION_RESOLUTION_REFUSAL_PHRASES: tuple[str, ...] = (
    "i can't answer",
    "i cannot answer",
    "i don't know",
    "i do not know",
    "not established",
    "isn't established",
    "is not established",
    "unknown",
    "i'm unable",
    "i am unable",
)
_QUESTION_RESOLUTION_ANSWER_STARTERS: tuple[str, ...] = (
    "yes",
    "no",
    "the answer is",
    "it is",
    "it's",
    "they are",
    "there is",
    "there are",
    "you can",
    "you should",
    "go to",
)
_SOCIAL_EXCHANGE_ANSWER_REFUSAL_TOKENS: tuple[str, ...] = (
    "i don't know",
    "i do not know",
    "don't know",
    "do not know",
    "no idea",
    "can't say",
    "cannot say",
    "won't say",
    "will not say",
    "not saying",
    "no names",
    "none yet",
    "shakes his head",
    "shakes her head",
    "shakes their head",
    "shakes his head.",
    "shakes her head.",
    "shakes their head.",
    "shrugs.",
    "shrugs",
)
_SOCIAL_EXCHANGE_ANSWER_UNCERTAINTY_TOKENS: tuple[str, ...] = (
    "as far as i know",
    "from what i heard",
    "from what i saw",
    "from what we know",
    "i've heard",
    "i have heard",
    "heard whispers",
    "whispers",
    "not sure",
    "unclear",
    "might be",
    "may be",
    "seems like",
    "haven't heard",
    "have not heard",
    "beats me",
    "hard to say",
    "couldn't say",
    "could not say",
    "can't swear",
    "cannot swear",
    "won't swear",
    "will swear",
    "no one will",
    "not my place",
    "no witnesses",
    "no names",
    "word is",
    "rumor is",
    "people say",
    "they say",
)
_SOCIAL_EXCHANGE_PRESSURE_TOKENS: tuple[str, ...] = (
    "ask me that again",
    "done talking",
    "i'm done talking",
    "i am done talking",
    "this conversation is over",
    "i walk away",
    "walk away",
    "face tightens",
)
_SOCIAL_EXCHANGE_SPEAKER_VERBS: tuple[str, ...] = (
    "says",
    "said",
    "answers",
    "answered",
    "replies",
    "replied",
    "shakes",
    "shrugs",
    "snaps",
    "mutters",
    "warns",
    "growls",
    "hisses",
    "admits",
    "insists",
    "face tightens",
)


def _is_direct_player_question(user_text: str) -> bool:
    """Heuristic: treat '?' or leading question word as direct question."""
    if not isinstance(user_text, str):
        return False
    t = user_text.strip()
    if not t:
        return False
    low = t.lower()
    first_word = (low.replace('"', ' ').replace("'", " ").split() or [""])[0]

    # Fast path: obvious direct question
    if low.rstrip().endswith("?"):
        return True
    if first_word in _QUESTION_WORDS:
        return True

    # Mid-text question marks often appear in action declarations, e.g.:
    # Galinor asks, "Where is the key?" and waits.
    if "?" in low:
        # If there is a quoted question, treat as a direct question.
        for seg in _extract_player_quoted_segments(t):
            seg_low = str(seg or "").strip().lower()
            if not seg_low:
                continue
            if "?" in seg_low:
                return True
            seg_first = (seg_low.replace('"', ' ').replace("'", " ").split() or [""])[0]
            if seg_first in _QUESTION_WORDS:
                return True

        # If the player used explicit question/ask verbs, treat as a direct question.
        if re.search(r"\b(ask|asks|asked|question|query|queries|inquire|inquires|inquired)\b", low):
            return True

        # Otherwise, treat non-terminal '?' as a vocative beat ("Footman?") not a direct question.
        return False

    return False


def _first_sentence(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    first = re.split(r"[.!?\n]", t, maxsplit=1)[0].strip()
    return first or t


def _split_leading_sentences(text: str, max_sentences: int = 2) -> List[str]:
    """First one or two sentence-like units (strict-social contract scope)."""
    t = str(text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    out: List[str] = []
    for p in parts:
        s = p.strip()
        if s:
            out.append(s)
        if len(out) >= max_sentences:
            break
    return out


_SHORT_NPC_BEAT_FIRST: re.Pattern[str] = re.compile(
    r"^(?:The\s+)?(?:[\w'.-]+\s+){0,4}"
    r"(?:frowns|grimaces|shrugs|nods|mutters|hesitates|laughs|sighs|looks\s+away|glances\s+away|"
    r"shakes\s+(?:their|his|her)\s+head|lowers\s+(?:their|his|her)\s+voice|raises\s+(?:their|his|her)\s+voice)"
    r"\s*\.?\s*$",
    re.IGNORECASE,
)


def _is_short_npc_beat_opener(sentence: str) -> bool:
    s = str(sentence or "").strip()
    if not s or len(s) > 140:
        return False
    return bool(_SHORT_NPC_BEAT_FIRST.match(s))


def _social_exchange_contract_scope(reply: str) -> str:
    """Text used for speaker/answer-shape checks: first sentence, or beat + second sentence."""
    parts = _split_leading_sentences(reply, 2)
    if not parts:
        return ""
    first = parts[0]
    if len(parts) >= 2 and _is_short_npc_beat_opener(first):
        return f"{first} {parts[1]}".strip()
    return first


def _npc_grounding_tokens_for_social(social: Dict[str, Any]) -> List[str]:
    """Significant name/id words (e.g. runner from Tavern Runner / tavern_runner)."""
    name = str(social.get("npc_name") or "").strip().lower()
    npc_id = str(social.get("npc_id") or "").strip().lower()
    chunks: List[str] = []
    if name:
        chunks.append(name)
    if npc_id:
        chunks.extend(re.split(r"[_\s-]+", npc_id.replace("-", " ")))
    out: List[str] = []
    for chunk in chunks:
        for w in re.split(r"\s+", chunk):
            wd = re.sub(r"[^a-z0-9]", "", w)
            if len(wd) >= 4:
                out.append(wd)
    seen: set[str] = set()
    uniq: List[str] = []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


def _first_sentence_opens_with_attributed_dialogue(sentence: str) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if s.startswith('"') or s.startswith("\u201c"):
        return True
    return bool(
        re.match(
            r"^(?:The\s+)?[\w'.-]+\s+(?:says|mutters|replies|answers|asks)\s*[,:]?\s*[\"“]",
            s,
            re.IGNORECASE,
        )
    )


_SOCIAL_SUBSTANTIVE_MOVE_RE = re.compile(
    r"\b(?:saw|heard|heard\s+of|was\s+told|were\s+told|went|left|returned|lost|found|knew|know|"
    r"dead|alive|still|never|came|riders|patrol|patrols|attacked|attack|ambush|witness|witnesses|"
    r"rumor|rumors|word|names|named|missing|happened|bodies|body)\b",
    re.IGNORECASE,
)

# Cinematic / stock padding: not a usable in-character answer (first substantive sentence).
_SOCIAL_ANSWER_NONANSWER_FILLER_RE = re.compile(
    r"\b(?:"
    r"starts\s+to\s+answer|"
    r"about\s+to\s+answer|"
    r"glances\s+past\s+you|"
    r"looks\s+away\s+without\s+answering|"
    r"pauses\s+as\b[^.!?]{0,80}\bbreaks\s+out\b|"
    r"for\s+a\s+moment[^.!?]{0,40}\bscene\s+holds\b|"
    r"\bthe\s+scene\s+holds\b|"
    r"truth\s+is\s+still\s+buried|"
    r"buried\s+beneath\s+rumor|"
    r"no\s+certain\s+answer\s+presents|"
    r"nothing\s+in\s+the\s+scene\s+points|"
    r"answer\s+has\s+not\s+formed|"
    r"small\s+details\s+sharpen\s+into\s+clues"
    r")\b",
    re.IGNORECASE,
)

# Natural warnings, directions, and concrete pointers (not limited to rigid answer templates).
_SOCIAL_SUBSTANTIVE_WARNING_OR_POINTER_RE = re.compile(
    r"\b(?:"
    r"keep\s+clear\s+of|stay\s+(?:away|clear)\s+from|watch\s+out\s+for|steer\s+clear\s+of|"
    r"best\s+not\s+(?:cross|ask|go|speak|poke)|"
    r"avoid\s+(?:the\s+)?[\w'.-]+|"
    r"don'?t\s+trust\b|"
    r"if\s+you\s+value\s+your\s+(?:skin|neck|life|head)\b|"
    r"there(?:'s|\s+is|\s+are)\s+\S+|"
    r"people\s+vanish(?:\s+(?:near|around|by))?|"
    r"house\s+[\w'.-]+\'?s?\s+men\b|"
    r"[\w'.-]+\'?s?\s+(?:men|soldiers|riders|crew|lot|people)\b"
    r")\b",
    re.IGNORECASE,
)

# Concrete factual / situational content (exclude vague "rumor" alone — paired with stock phrases above).
_SOCIAL_SUBSTANTIVE_CONTENT_RE = re.compile(
    r"\b(?:"
    r"saw|heard(?:\s+of)?|was\s+told|were\s+told|"
    r"know|knew|named|names\b|witness|witnesses|"
    r"dead|bodies|missing|vanished|happened|"
    r"patrol|riders|attacked|attack|ambush|"
    r"never\s+(?:came|came\s+back|returned|left)|"
    r"came\s+back|returned|left|went|found|lost|"
    r"from\s+the\s+[\w'.-]+"
    r")\b",
    re.IGNORECASE,
)


def _social_answer_substance_sentence(reply: str, *, first_sentence_speaker_grounded: bool = False) -> str:
    """First sentence that should carry the answer (skip a leading short NPC beat or grounded stage-beat)."""
    parts = _split_leading_sentences(reply, 2)
    if not parts:
        return ""
    first = parts[0].strip()
    if len(parts) >= 2 and _is_short_npc_beat_opener(first):
        return parts[1].strip()
    if (
        len(parts) >= 2
        and first_sentence_speaker_grounded
        and (not is_valid_social_answer_first_sentence(first))
        and is_valid_social_answer_first_sentence(parts[1].strip())
    ):
        return parts[1].strip()
    return first


def _social_answer_nonanswer_filler_hit(low: str) -> bool:
    return bool(_SOCIAL_ANSWER_NONANSWER_FILLER_RE.search(low))


def is_valid_social_answer_first_sentence(first_sentence: str) -> bool:
    """True when the opening carries a substantive social answer, not cinematic stall or empty air."""
    s = str(first_sentence or "").strip()
    if not s:
        return False
    low = s.lower()
    if _social_answer_nonanswer_filler_hit(low):
        return False
    if any(tok in low for tok in _SOCIAL_EXCHANGE_ANSWER_REFUSAL_TOKENS):
        return True
    if any(tok in low for tok in _SOCIAL_EXCHANGE_ANSWER_UNCERTAINTY_TOKENS):
        return True
    if any(tok in low for tok in _SOCIAL_EXCHANGE_PRESSURE_TOKENS):
        return True
    if "couldn't tell" in low or "could not tell" in low:
        return True
    if any(low.startswith(p) for p in _QUESTION_RESOLUTION_ANSWER_STARTERS):
        return True
    if _SOCIAL_SUBSTANTIVE_WARNING_OR_POINTER_RE.search(low):
        return True
    if _SOCIAL_SUBSTANTIVE_CONTENT_RE.search(low):
        return True
    if _SOCIAL_SUBSTANTIVE_MOVE_RE.search(low) and not re.search(
        r"\b(?:rumors?|word)\b.{0,40}\b(?:rain|scene|truth)\b", low
    ):
        return True
    if (s.startswith('"') or s.startswith("\u201c")) and len(s) >= 10:
        inner = re.split(r"[\"“”]", s, maxsplit=2)
        chunk = inner[1].strip() if len(inner) >= 2 else ""
        if len(chunk) >= 6 and not _social_answer_nonanswer_filler_hit(chunk.lower()):
            return True
    return False


def _is_social_exchange_question_turn(player_text: str, resolution: Dict[str, Any] | None) -> bool:
    if is_scene_directed_watch_question(player_text):
        return False
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if str(social.get("social_intent_class") or "").strip().lower() != "social_exchange":
        return False
    if not (_is_direct_player_question(player_text) or looks_like_npc_directed_question(player_text)):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    engine_questionish = kind in {"question", "social_probe"} or bool(social.get("npc_reply_expected"))
    if engine_questionish:
        return True
    return bool(looks_like_npc_directed_question(player_text))


def _social_exchange_first_sentence_contract(
    *,
    player_text: str,
    gm_reply_text: str,
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Enforce a substantive first answer for NPC-directed social_exchange question turns.

    This guard runs before broad prose sanitization so social_exchange replies
    cannot open with cinematic stall or ambient padding and still pass retry checks.
    """
    if not _is_social_exchange_question_turn(player_text, resolution):
        return {"applies": False, "ok": True, "reasons": []}
    reply = str(gm_reply_text or "").strip()
    if not reply:
        return {
            "applies": True,
            "ok": False,
            "reasons": ["question_rule:social_exchange_empty_reply"],
            "social_answer_validation_mode": "substantive_content",
            "first_sentence_substantive": False,
            "rejected_as_cinematic_nonanswer": False,
        }

    first = _first_sentence(reply)
    first_low = first.lower()
    social = (resolution or {}).get("social") if isinstance((resolution or {}).get("social"), dict) else {}
    npc_name = str(social.get("npc_name") or "").strip().lower()
    npc_id = str(social.get("npc_id") or "").strip().lower()
    npc_id_name = npc_id.replace("_", " ").replace("-", " ")
    scope = _social_exchange_contract_scope(reply)
    scope_low = scope.lower()
    q_tokens = _question_content_tokens(player_text)
    grounding_tokens = _npc_grounding_tokens_for_social(social)

    speaker_grounded = False
    if npc_name and npc_name in first_low:
        speaker_grounded = True
    if npc_id_name and npc_id_name in first_low:
        speaker_grounded = True
    if any(tok and tok in scope_low for tok in grounding_tokens):
        speaker_grounded = True
    if re.search(r"\bthe\s+\w+\s+(?:says|said|answers|answered|replies|replied)\b", first_low):
        speaker_grounded = True
    if re.search(r"\bthe\s+\w+\s+(?:shakes|shrugs|snaps|mutters|warns|growls|hisses)\b", first_low):
        speaker_grounded = True
    if any(verb in first_low for verb in _SOCIAL_EXCHANGE_SPEAKER_VERBS):
        if re.search(r"\b(?:the|this|that)\s+\w+\b", first_low) or npc_name or npc_id_name:
            speaker_grounded = True
    if _first_sentence_opens_with_attributed_dialogue(first):
        speaker_grounded = True
    if re.search(r"[\"“]", first):
        speaker_grounded = True

    substance_sentence = _social_answer_substance_sentence(
        reply, first_sentence_speaker_grounded=speaker_grounded
    )
    substance_low = substance_sentence.lower()

    rejected_filler = _social_answer_nonanswer_filler_hit(substance_low)
    helper_substantive = is_valid_social_answer_first_sentence(substance_sentence)
    token_overlap = bool(q_tokens) and any(tok in substance_low for tok in q_tokens)
    starter_hit = any(substance_low.startswith(p) for p in _QUESTION_RESOLUTION_ANSWER_STARTERS)
    bounded_refusal = bool(
        "do not know enough to answer" not in substance_low
        and "don't know enough to answer" not in substance_low
        and re.search(
            r"\b(?:i|we)\s+(?:cannot|can't|could not|couldn't|do not|don't)\s+"
            r"(?:tell|confirm|name|identify|verify|answer)\b",
            substance_low,
        )
    )
    substantive_opening = bool(
        (not rejected_filler) and (helper_substantive or token_overlap or starter_hit or bounded_refusal)
    )

    reasons: List[str] = []
    if not speaker_grounded:
        reasons.append("question_rule:social_exchange_first_sentence_not_speaker_grounded")
    if not substantive_opening:
        reasons.append("question_rule:social_exchange_first_sentence_not_substantive_answer")
    ok = bool(speaker_grounded and substantive_opening)
    return {
        "applies": True,
        "ok": ok,
        "reasons": reasons,
        "social_answer_validation_mode": "substantive_content",
        "first_sentence_substantive": substantive_opening,
        "rejected_as_cinematic_nonanswer": rejected_filler,
    }


def _question_content_tokens(user_text: str) -> List[str]:
    low = str(user_text or "").lower()
    tokens = [t for t in _ECHO_TOKEN_PATTERN.findall(low) if len(t) >= 4]
    out: List[str] = []
    for tok in tokens:
        if tok in _QUESTION_RESOLUTION_STOPWORDS:
            continue
        if tok in _QUESTION_WORDS:
            continue
        if tok not in out:
            out.append(tok)
    return out[:10]


def _classify_uncertainty_category(player_text: str) -> str:
    low = str(player_text or "").strip().lower()
    if not low:
        return "unknown_method"
    if any(phrase in low for phrase in ("how many", "how much", "how long", "how often", "what number", "what count")):
        return "unknown_quantity"
    if low.startswith(("who ", "whose ")) or re.search(r"\bwho\b", low):
        return "unknown_identity"
    if low.startswith("where ") or re.search(r"\bwhere\b", low):
        return "unknown_location"
    if low.startswith("why ") or any(
        phrase in low
        for phrase in ("what do they want", "what does he want", "what does she want", "what are they after", "what is driving")
    ):
        return "unknown_motive"
    if low.startswith(("can ", "could ", "would ", "should ", "is it possible", "is this possible", "is that possible")):
        return "unknown_feasibility"
    if any(phrase in low for phrase in ("feasible", "possible", "can i", "could i", "would it work", "will it work", "can this work")):
        return "unknown_feasibility"
    if any(phrase in low for phrase in ("how far", "how tall", "how deep", "how wide")):
        return "unknown_quantity"
    if low.startswith("how "):
        return "unknown_method"
    return "unknown_method"


def _clean_scene_detail(text: str, *, max_len: int = 120) -> str:
    detail = " ".join(str(text or "").strip().split()).rstrip(".")
    if len(detail) <= max_len:
        return detail
    return detail[: max_len - 3].rstrip(" ,;:") + "..."


def _normalize_speaker_identity(speaker_identity: Dict[str, Any] | str | None) -> Dict[str, str]:
    if isinstance(speaker_identity, dict):
        name = str(speaker_identity.get("name") or speaker_identity.get("label") or "").strip()
        speaker_id = str(speaker_identity.get("id") or "").strip()
        role = str(speaker_identity.get("role") or "").strip().lower()
        if role not in {"npc", "narrator"}:
            role = "npc" if name or speaker_id else "narrator"
        return {"role": role, "id": speaker_id, "name": name}
    if isinstance(speaker_identity, str) and speaker_identity.strip():
        return {"role": "npc", "id": "", "name": speaker_identity.strip()}
    return {"role": "", "id": "", "name": ""}


def _resolve_uncertainty_speaker(
    *,
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any],
    scene_id: str,
    speaker_identity: Dict[str, Any] | str | None,
    scene_envelope: Dict[str, Any] | None = None,
) -> Dict[str, str]:
    universe = addressable_scene_npc_id_universe(
        session if isinstance(session, dict) else None,
        scene_envelope if isinstance(scene_envelope, dict) else None,
        world if isinstance(world, dict) else None,
    )
    strict_presence_scope = bool(universe)
    explicit = _normalize_speaker_identity(speaker_identity)
    explicit_id = str(explicit.get("id") or "").strip()
    if explicit.get("role") == "npc" and (explicit.get("name") or explicit_id):
        if explicit_id and not assert_valid_speaker(
            explicit_id,
            session,
            scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
            world=world if isinstance(world, dict) else None,
        ) and strict_presence_scope:
            return {"role": "narrator", "id": "", "name": ""}
        return explicit
    if explicit.get("role") == "narrator":
        return explicit

    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip() or _active_interaction_target_id(session)
    if npc_id and not assert_valid_speaker(
        npc_id,
        session,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        world=world if isinstance(world, dict) else None,
    ) and strict_presence_scope:
        return {"role": "narrator", "id": "", "name": ""}
    npc_name = str(social.get("npc_name") or "").strip() or _resolve_npc_name(world, npc_id, scene_id)
    if npc_name or npc_id:
        return {"role": "npc", "id": npc_id, "name": npc_name}
    return {"role": "narrator", "id": "", "name": ""}


def _build_uncertainty_scene_snapshot(
    *,
    scene_envelope: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    location: str,
    speaker_name: str,
    scene_snapshot: Dict[str, Any] | None,
) -> Dict[str, Any]:
    explicit = dict(scene_snapshot) if isinstance(scene_snapshot, dict) else {}
    visible = explicit.get("visible_facts")
    if not isinstance(visible, list):
        visible = _scene_visible_facts(scene_envelope)
    visible_clean = [str(v).strip() for v in visible if isinstance(v, str) and str(v).strip()]
    visible_low = " ".join(v.lower() for v in visible_clean)
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    exits_raw = explicit.get("exits")
    if not isinstance(exits_raw, list):
        exits_raw = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_label = ""
    if exits_raw:
        first_exit = exits_raw[0]
        if isinstance(first_exit, dict):
            exit_label = str(first_exit.get("label") or "").strip()
        else:
            exit_label = str(first_exit or "").strip()
    first_visible = _clean_scene_detail(visible_clean[0]) if visible_clean else ""
    other_npcs = [
        name for name in _in_scene_npc_names(world, scene_id)
        if name and name != speaker_name
    ]
    return {
        "scene_id": str(explicit.get("scene_id") or scene_id or "").strip(),
        "location": str(explicit.get("location") or location or "").strip(),
        "visible_facts": visible_clean,
        "first_visible_detail": str(explicit.get("first_visible_detail") or first_visible or "").strip(),
        "exit_label": str(explicit.get("exit_label") or exit_label or "").strip(),
        "other_npc_names": other_npcs,
        "has_notice_board": bool(("notice board" in visible_low) or ("noticeboard" in visible_low)),
        "has_tavern_runner": bool(
            ("tavern runner" in visible_low)
            or ("tavern" in visible_low and "runner" in visible_low)
            or ("rumor" in visible_low)
            or ("rumour" in visible_low)
        ),
        "has_refugees": "refugee" in visible_low,
        "has_gate_or_checkpoint": bool(
            ("gate" in visible_low)
            or ("checkpoint" in visible_low)
            or ("road" in visible_low)
            or ("approach" in visible_low)
        ),
        "has_missing_patrol": "missing patrol" in visible_low,
        "has_tax_or_curfew": bool(("tax" in visible_low) or ("curfew" in visible_low)),
    }


def _build_uncertainty_turn_context(
    *,
    player_text: str,
    session: Dict[str, Any],
    resolution: Dict[str, Any],
    turn_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    base = dict(turn_context) if isinstance(turn_context, dict) else {}
    interaction = session.get("interaction_context") if isinstance(session, dict) else {}
    interaction = interaction if isinstance(interaction, dict) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    check = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    adjudication = resolution.get("adjudication") if isinstance(resolution.get("adjudication"), dict) else {}
    skill = str(base.get("check_skill") or check.get("skill") or "").strip().replace("_", " ")
    reason = str(base.get("check_reason") or check.get("reason") or "").strip()
    return {
        "player_text": str(player_text or "").strip(),
        "question_focus": list(base.get("question_focus") or _question_content_tokens(player_text)),
        "conversation_privacy": str(base.get("conversation_privacy") or interaction.get("conversation_privacy") or "").strip(),
        "engagement_level": str(base.get("engagement_level") or interaction.get("engagement_level") or "").strip(),
        "interaction_mode": str(base.get("interaction_mode") or interaction.get("interaction_mode") or "").strip(),
        "reply_kind": str(base.get("reply_kind") or social.get("reply_kind") or "").strip(),
        "check_skill": skill,
        "check_reason": reason,
        "is_direct_question": bool(base.get("is_direct_question") if "is_direct_question" in base else _is_direct_player_question(player_text)),
        "resolution_kind": str(base.get("resolution_kind") or resolution.get("kind") or "").strip().lower(),
        "social_intent_class": str(base.get("social_intent_class") or social.get("social_intent_class") or "").strip().lower(),
        "requires_check": bool(
            base.get("requires_check")
            if "requires_check" in base
            else (bool(check.get("requires_check")) or bool(resolution.get("requires_check")))
        ),
        "adjudication_answer_type": str(base.get("adjudication_answer_type") or adjudication.get("answer_type") or "").strip().lower(),
    }


_LEAD_HISTORY_LIMIT = 6
_LEAD_FOLLOW_UP_PRONOUN_TOKENS: tuple[str, ...] = (
    "that person",
    "that one",
    "that woman",
    "that man",
    "them",
    "him",
    "her",
    "the one you mentioned",
)
_LEAD_FIND_REQUEST_TOKENS: tuple[str, ...] = (
    "where do i find",
    "where can i find",
    "where is",
    "where are",
    "how do i find",
    "take me to",
)
_LEAD_NAME_PATTERN = re.compile(
    r"\b((?:Lady|Lord|Captain|Sergeant|Master|Mistress|Dame|Sir)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
_LEAD_POSITION_PATTERN = re.compile(
    r"\b((?:Lady|Lord|Captain|Sergeant|Master|Mistress|Dame|Sir)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+"
    r"(?:(?:waits?|stands?|lingers?|watches?|sits?|leans?|rests?|is|are)\s+)?"
    r"(near|by|at|outside|inside|beside|under)\s+([^.,;!?]+)",
    re.IGNORECASE,
)
_LEAD_GENERIC_POSITION_PHRASES: tuple[str, ...] = (
    "near the tavern entrance",
    "by the gate",
    "at the gate",
    "by the board",
    "near the board",
    "at the board",
    "in the refugee line",
    "by the refugee line",
)
_VISIBLE_FIGURE_TOKENS: tuple[str, ...] = (
    "watcher",
    "onlooker",
    "stranger",
    "figure",
    "runner",
    "guard",
    "guards",
    "refugee",
    "merchant",
    "traveler",
    "rider",
    "woman",
    "man",
    "noble",
)
_SUSPICIOUS_FIGURE_TOKENS: tuple[str, ...] = (
    "watcher",
    "watching",
    "suspicious",
    "tattered",
    "well-dressed",
    "rough-looking",
    "lingering",
    "loitering",
)
_LEAD_SUBJECT_CLEAN_PREFIX = re.compile(r"^(?:a|an|the)\s+", re.IGNORECASE)
_LEAD_SUBJECT_VERB_MARKERS: tuple[str, ...] = (
    " approaches ",
    " approach ",
    " leans ",
    " lean ",
    " packs ",
    " pack ",
    " packing ",
    " keeps ",
    " keep ",
    " stands ",
    " stand ",
    " waits ",
    " wait ",
    " lingers ",
    " linger ",
    " watches ",
    " watch ",
    " reacts ",
    " react ",
    " barks ",
    " bark ",
    " argues ",
    " argue ",
    " is ",
    " are ",
)
_LEAD_OBSERVER_FRAME_PREFIXES: tuple[str, ...] = (
    "as you ",
    "while you ",
    "when you ",
    "looking ",
    "from where you stand",
)
_LEAD_PLAYER_OBSERVATION_PREFIX = re.compile(
    r"^(?:you\s+)?(?:notice|see|spot|watch)\s+",
    re.IGNORECASE,
)
_LEAD_LEADING_POSITION_PATTERN = re.compile(
    r"^(near|by|at|outside|inside|beside|under)\s+([^,.;!?]+),\s+(.+)$",
    re.IGNORECASE,
)
_LEAD_INVALID_SUBJECT_PREFIXES: tuple[str, ...] = (
    "as you",
    "while you",
    "when you",
    "you",
    "looking around",
    "looking across",
    "watching the scene",
    "from where you stand",
    "no ",
    "nothing",
    "nobody",
    "no one",
    "absent ",
    "rumor ",
    "rumour ",
)
_KNOWN_SCENE_LOCATION_PROMPTS: tuple[str, ...] = (
    "where am i",
    "where are we",
    "where is this",
    "what location",
    "which location",
    "what district",
    "which district",
)


def _recent_contextual_leads(session: Dict[str, Any], scene_id: str) -> List[Dict[str, Any]]:
    if not scene_id:
        return []
    runtime = get_scene_runtime(session, scene_id)
    raw = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[-_LEAD_HISTORY_LIMIT:]:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        subject = str(item.get("subject") or "").strip()
        if not key or not subject:
            continue
        out.append(
            {
                "key": key,
                "kind": str(item.get("kind") or "").strip(),
                "subject": subject,
                "position": str(item.get("position") or "").strip(),
                "named": bool(item.get("named")),
                "positioned": bool(item.get("positioned")),
                "mentions": int(item.get("mentions", 1) or 1),
                "last_turn": int(item.get("last_turn", 0) or 0),
            }
        )
    return out


def _lead_key(subject: str, *, kind: str = "", position: str = "") -> str:
    return slugify(" ".join(part for part in (kind, subject, position) if part).strip()) or slugify(subject) or "lead"


def _clean_lead_subject(subject: str) -> str:
    clean = " ".join(str(subject or "").strip().split()).rstrip(" .,:;")
    clean = _LEAD_SUBJECT_CLEAN_PREFIX.sub("", clean).strip()
    return clean


def _lead_subject_is_invalid(subject: str) -> bool:
    low = str(subject or "").strip().lower()
    if not low:
        return True
    return any(low == prefix or low.startswith(prefix) for prefix in _LEAD_INVALID_SUBJECT_PREFIXES)


def _strip_visible_figure_observer_frame(text: str) -> tuple[str, str]:
    clean = " ".join(str(text or "").strip().split()).strip(" ,.;:")
    if not clean:
        return "", ""
    position = ""
    leading_position = _LEAD_LEADING_POSITION_PATTERN.match(clean)
    if leading_position:
        position = _clean_lead_position(f"{leading_position.group(1).lower()} {leading_position.group(2).strip()}")
        clean = leading_position.group(3).strip(" ,.;:")
    low = clean.lower()
    if "," in clean and any(low.startswith(prefix) for prefix in _LEAD_OBSERVER_FRAME_PREFIXES):
        clean = clean.split(",", 1)[1].strip(" ,.;:")
    clean = _LEAD_PLAYER_OBSERVATION_PREFIX.sub("", clean).strip(" ,.;:")
    return clean, position


def _clean_lead_position(position: str) -> str:
    clean = " ".join(str(position or "").strip().split()).rstrip(" .,:;")
    low = clean.lower()
    for marker in (",", " while ", " and ", " who ", " which ", " as ", " but "):
        idx = low.find(marker)
        if idx > 0:
            clean = clean[:idx].strip(" ,.;:")
            low = clean.lower()
    return clean


def _lead_subject_matches_prompt(subject: str, player_prompt: str) -> bool:
    subject_low = str(subject or "").strip().lower()
    prompt_low = str(player_prompt or "").strip().lower()
    if not subject_low or not prompt_low:
        return False
    if subject_low in prompt_low:
        return True
    subject_tokens = [tok for tok in _ECHO_TOKEN_PATTERN.findall(subject_low) if len(tok) >= 4]
    return any(tok in prompt_low for tok in subject_tokens[:3])


def _looks_like_follow_up_find_request(player_prompt: str) -> bool:
    low = str(player_prompt or "").strip().lower()
    if not low:
        return False
    if any(token in low for token in _LEAD_FIND_REQUEST_TOKENS):
        return True
    return any(token in low for token in _LEAD_FOLLOW_UP_PRONOUN_TOKENS)


def _render_candidate_reference(candidate: Dict[str, Any]) -> str:
    subject = str(candidate.get("subject") or "").strip()
    if not subject:
        return ""
    position = str(candidate.get("position") or "").strip()
    if position:
        return f"{subject} {position}".strip()
    return subject


def _lead_text_for_candidate(category: str, candidate: Dict[str, Any]) -> str:
    kind = str(candidate.get("kind") or "").strip()
    ref = _render_candidate_reference(candidate)
    subject = str(candidate.get("subject") or "").strip() or "that lead"
    if kind in {"engaged_npc", "scene_npc"}:
        if category == "unknown_identity":
            return f"Press {subject} for the name, badge, or title tied to it."
        if category == "unknown_location":
            return f"Ask {subject} for the last confirmed sighting and the landmark attached to it."
        if category == "unknown_motive":
            return f"Ask {subject} who profits if this pressure keeps building."
        if category == "unknown_quantity":
            return f"Ask {subject} for the smallest count they will stand behind."
        if category == "unknown_feasibility":
            return f"Ask {subject} what would make it possible tonight."
        return f"Ask {subject} what changed first and who noticed."
    if kind in {"recent_named_figure", "visible_named_figure", "visible_suspicious_figure"}:
        if category == "unknown_location":
            return f"Find {ref} and lock down where they were last seen speaking to anyone."
        if category == "unknown_identity":
            return f"Start with {ref} and force the next name behind them into the open."
        if category == "unknown_motive":
            return f"Watch {ref} closely and see who they avoid, favor, or report to."
        if category == "unknown_quantity":
            return f"Use {ref} to bracket who else is moving in the same pattern."
        if category == "unknown_feasibility":
            return f"Reach {ref} and see what barrier or permission they keep pointing back to."
        return f"Shadow {ref} and pin down who they meet next."
    if kind == "pending_clue":
        if category == "unknown_location":
            return f"Follow the clue about {subject} and pin down the last solid place it names."
        if category == "unknown_identity":
            return f"Work the clue about {subject} until it yields one concrete name."
        return f"Push on the clue about {subject} until it narrows to one usable lead."
    if kind == "active_event":
        if category == "unknown_location":
            return f"Watch {subject} and see where the pressure is pushing people next."
        if category == "unknown_identity":
            return f"Press into {subject} until one face or voice stands out as central."
        if category == "unknown_motive":
            return f"Lean on {subject} and see who benefits from keeping it hot."
        if category == "unknown_quantity":
            return f"Use {subject} to get a floor and ceiling instead of waiting for a perfect count."
        if category == "unknown_feasibility":
            return f"Test whether {subject} opens or closes the path you want."
        return f"Stay with {subject} until it gives you one concrete turn."
    if kind in {"scene_object", "notice_board", "scene_exit"}:
        if "notice" in kind or "notice" in subject.lower() or "board" in subject.lower():
            if category == "unknown_identity":
                return "Pull names off the missing patrol notice and watch who keeps coming back to it."
            if category == "unknown_location":
                return "Start at the missing patrol notice and pin down the last sighting tied to it."
            if category == "unknown_motive":
                return "Read the taxes, curfews, and missing patrol posting together and see who profits from all three."
            if category == "unknown_quantity":
                return "Use the missing patrol posting as your floor, then ask who came back short."
            return "Compare what changed around the missing patrol notice before chasing the whole story."
        if kind == "scene_exit":
            return f"Take the route toward {subject} and lock down the last confirmed sighting along it."
        return f"Inspect {subject} for the concrete detail everyone else is skimming past."

    if category == "unknown_identity":
        return f"Chase the one name tied to {subject} before it gets washed out."
    if category == "unknown_location":
        return f"Lock down one direction from {subject} before you go hunting for the final door."
    if category == "unknown_motive":
        return f"Track who profits or tightens control around {subject}."
    if category == "unknown_quantity":
        return f"Use {subject} to bracket the scale with a floor and a ceiling."
    if category == "unknown_feasibility":
        return f"Test the condition tied to {subject} instead of guessing."
    return f"Inspect what changed around {subject}."


def _score_recent_repetition(candidate: Dict[str, Any], recent_leads: List[Dict[str, Any]]) -> int:
    key = str(candidate.get("key") or "").strip()
    if not key or not recent_leads:
        return 0
    penalty = 0
    recent_keys = [str(item.get("key") or "").strip() for item in recent_leads[-3:]]
    if recent_keys and recent_keys[-1] == key:
        penalty += 45
    penalty += 12 * sum(1 for seen in recent_keys if seen == key)
    return penalty


def _extract_visible_figure_candidate(fact: str) -> Dict[str, Any] | None:
    text = " ".join(str(fact or "").strip().split()).rstrip(".")
    if not text:
        return None
    low = text.lower()
    named = _LEAD_NAME_PATTERN.search(text)
    position = ""
    for match in _LEAD_GENERIC_POSITION_PHRASES:
        if match in low:
            position = match
            break
    if named:
        subject = named.group(1).strip()
        positioned_match = _LEAD_POSITION_PATTERN.search(text)
        if positioned_match:
            position = _clean_lead_position(
                f"{positioned_match.group(2).lower()} {positioned_match.group(3).strip()}".strip()
            )
        return {
            "key": _lead_key(subject, kind="named_figure", position=position),
            "kind": "visible_named_figure",
            "subject": subject,
            "position": position,
            "named": True,
            "positioned": bool(position),
        }
    text, framed_position = _strip_visible_figure_observer_frame(text)
    if framed_position:
        position = framed_position
    low = text.lower()
    if not text:
        return None
    if not any(token in low for token in _VISIBLE_FIGURE_TOKENS):
        return None
    subject = text
    for marker in _LEAD_SUBJECT_VERB_MARKERS:
        idx = low.find(marker)
        if idx > 0:
            subject = text[:idx]
            break
    if not position:
        for marker in (" near ", " by ", " at ", " outside ", " beside ", " under "):
            idx = low.find(marker)
            if idx > 0:
                position = _clean_lead_position(text[idx:].strip(" ,.;:"))
                break
    if position and position.lower() in subject.lower():
        subject = subject[:subject.lower().find(position.lower())].strip(" ,.;:")
    subject = _clean_lead_subject(subject)
    if _lead_subject_is_invalid(subject):
        return None
    return {
        "key": _lead_key(subject, kind="visible_figure", position=position),
        "kind": "visible_suspicious_figure" if any(token in low for token in _SUSPICIOUS_FIGURE_TOKENS) else "active_event",
        "subject": subject.lower(),
        "position": position.lower() if position else "",
        "named": False,
        "positioned": bool(position),
    }


def choose_contextual_lead(
    scene_context: Dict[str, Any],
    recent_leads: List[Dict[str, Any]],
    current_speaker: Dict[str, Any] | None,
    player_prompt: str,
) -> Dict[str, Any]:
    category = str(scene_context.get("category") or "unknown_method").strip()
    snapshot = scene_context.get("scene_snapshot") if isinstance(scene_context.get("scene_snapshot"), dict) else {}
    turn_context = scene_context.get("turn_context") if isinstance(scene_context.get("turn_context"), dict) else {}
    speaker = current_speaker if isinstance(current_speaker, dict) else {}
    recent = [dict(item) for item in recent_leads if isinstance(item, dict)]
    candidates: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _push(base_score: int, reason: str, candidate: Dict[str, Any]) -> None:
        key = str(candidate.get("key") or "").strip()
        subject = str(candidate.get("subject") or "").strip()
        if not key or not subject or key in seen:
            return
        item = dict(candidate)
        score = int(base_score)
        prompt_low = str(player_prompt or "").strip().lower()
        if _lead_subject_matches_prompt(subject, prompt_low):
            score += 38
        if item.get("position") and _looks_like_follow_up_find_request(prompt_low):
            score += 15
        score -= _score_recent_repetition(item, recent)
        item["score"] = score
        item["reason"] = reason
        item["lead_text"] = _lead_text_for_candidate(category, item)
        candidates.append(item)
        seen.add(key)

    speaker_name = str(speaker.get("name") or "").strip()
    speaker_role = str(speaker.get("role") or "").strip().lower()
    if speaker_role == "npc" and speaker_name:
        _push(
            118,
            "currently_engaged_npc",
            {
                "key": _lead_key(speaker_name, kind="engaged_npc"),
                "kind": "engaged_npc",
                "subject": speaker_name,
                "position": "",
                "named": True,
                "positioned": False,
            },
        )

    for prior in reversed(recent[-3:]):
        subject = str(prior.get("subject") or "").strip()
        if not subject:
            continue
        base = 104 if (prior.get("named") or prior.get("positioned")) else 76
        if _looks_like_follow_up_find_request(player_prompt) and (prior.get("named") or prior.get("positioned")):
            base += 65
        _push(
            base,
            "recent_live_lead",
            {
                "key": str(prior.get("key") or _lead_key(subject, kind="recent")),
                "kind": "recent_named_figure" if prior.get("named") or prior.get("positioned") else str(prior.get("kind") or "active_event"),
                "subject": subject,
                "position": str(prior.get("position") or "").strip(),
                "named": bool(prior.get("named")),
                "positioned": bool(prior.get("positioned")),
            },
        )

    for name in (snapshot.get("other_npc_names") or [])[:3]:
        clean = str(name).strip()
        if clean and clean != speaker_name and (speaker_role == "npc" or _lead_subject_matches_prompt(clean, player_prompt)):
            _push(
                86,
                "other_scene_npc",
                {
                    "key": _lead_key(clean, kind="scene_npc"),
                    "kind": "scene_npc",
                    "subject": clean,
                    "position": "",
                    "named": True,
                    "positioned": False,
                },
            )

    for fact in (snapshot.get("visible_facts") or [])[:8]:
        candidate = _extract_visible_figure_candidate(str(fact))
        if candidate is None:
            continue
        kind = str(candidate.get("kind") or "")
        base = 95 if kind == "visible_named_figure" else (92 if kind == "visible_suspicious_figure" else 64)
        _push(base, "visible_scene_figure", candidate)

    for lead in (snapshot.get("pending_leads") or [])[:4]:
        if not isinstance(lead, dict):
            continue
        subject = str(lead.get("text") or lead.get("leads_to_npc") or lead.get("leads_to_scene") or "").strip()
        if not subject:
            continue
        _push(
            79,
            "discovered_pending_clue",
            {
                "key": _lead_key(subject, kind="pending_clue"),
                "kind": "pending_clue",
                "subject": subject,
                "position": "",
                "named": bool(_LEAD_NAME_PATTERN.search(subject)),
                "positioned": False,
            },
        )

    exit_label = str(snapshot.get("exit_label") or "").strip()
    if exit_label:
        _push(
            58,
            "scene_exit",
            {
                "key": _lead_key(exit_label, kind="scene_exit"),
                "kind": "scene_exit",
                "subject": exit_label,
                "position": "",
                "named": False,
                "positioned": False,
            },
        )
    if snapshot.get("has_missing_patrol"):
        _push(
            68,
            "active_public_tension",
            {
                "key": "missing_patrol_rumor",
                "kind": "active_event",
                "subject": "the guards reacting to the missing patrol rumor",
                "position": "",
                "named": False,
                "positioned": False,
            },
        )
    if snapshot.get("has_refugees"):
        _push(
            62,
            "active_public_tension",
            {
                "key": "refugee_line",
                "kind": "active_event",
                "subject": "the refugee line under pressure",
                "position": "",
                "named": False,
                "positioned": False,
            },
        )
    if snapshot.get("has_tax_or_curfew"):
        _push(
            60,
            "active_public_tension",
            {
                "key": "tax_curfew_crackdown",
                "kind": "active_event",
                "subject": "the new taxes and curfews squeezing the gate",
                "position": "",
                "named": False,
                "positioned": False,
            },
        )
    if snapshot.get("has_notice_board"):
        _push(
            44,
            "notice_board_fallback",
            {
                "key": "notice_board",
                "kind": "notice_board",
                "subject": "the notice board",
                "position": "",
                "named": False,
                "positioned": False,
            },
        )

    if not candidates:
        fallback_subject = str(snapshot.get("first_visible_detail") or snapshot.get("location") or "the scene").strip()
        candidates.append(
            {
                "key": _lead_key(fallback_subject, kind="fallback"),
                "kind": "scene_object",
                "subject": fallback_subject,
                "position": "",
                "named": False,
                "positioned": False,
                "score": 20,
                "reason": "fallback_visible_detail",
                "lead_text": _lead_text_for_candidate(category, {"kind": "scene_object", "subject": fallback_subject}),
            }
        )

    candidates.sort(
        key=lambda item: (
            int(item.get("score", 0)),
            1 if item.get("named") else 0,
            1 if item.get("positioned") else 0,
            -len(str(item.get("subject") or "")),
        ),
        reverse=True,
    )
    selected = dict(candidates[0])
    selected["alternatives"] = [
        {
            "key": str(item.get("key") or ""),
            "kind": str(item.get("kind") or ""),
            "subject": str(item.get("subject") or ""),
            "position": str(item.get("position") or ""),
            "score": int(item.get("score", 0)),
        }
        for item in candidates[1:4]
    ]
    return selected


def extract_contextual_leads_from_text(player_facing_text: str) -> List[Dict[str, Any]]:
    text = str(player_facing_text or "").strip()
    if not text:
        return []
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _add(kind: str, subject: str, *, position: str = "", named: bool = False) -> None:
        clean_subject = _clean_lead_subject(subject)
        clean_position = _clean_lead_position(position)
        if not clean_subject:
            return
        key = _lead_key(clean_subject, kind=kind, position=clean_position)
        if key in seen:
            return
        seen.add(key)
        out.append(
            {
                "key": key,
                "kind": kind,
                "subject": clean_subject,
                "position": clean_position,
                "named": bool(named),
                "positioned": bool(clean_position),
            }
        )

    for match in _LEAD_POSITION_PATTERN.finditer(text):
        _add(
            "recent_named_figure",
            match.group(1),
            position=f"{match.group(2).lower()} {match.group(3).strip()}",
            named=True,
        )
    for match in _LEAD_NAME_PATTERN.finditer(text):
        _add("recent_named_figure", match.group(1), named=True)

    for sentence in _split_reply_sentences(text):
        candidate = _extract_visible_figure_candidate(sentence)
        if candidate is None:
            continue
        _add(
            str(candidate.get("kind") or "active_event"),
            str(candidate.get("subject") or ""),
            position=str(candidate.get("position") or ""),
            named=bool(candidate.get("named")),
        )

    low = text.lower()
    if "missing patrol notice" in low:
        _add("notice_board", "the missing patrol notice")
    elif "notice board" in low or "noticeboard" in low:
        _add("notice_board", "the notice board")
    if "tavern runner" in low:
        _add("scene_npc", "Tavern Runner", named=True)
    if "refugee line" in low:
        _add("active_event", "the refugee line under pressure")
    if "missing patrol" in low and "notice" not in low:
        _add("active_event", "the missing patrol rumor")
    return out[:_LEAD_HISTORY_LIMIT]


def _merge_lead_subject_prefer_richer(old: str, new: str) -> str:
    """When extraction re-matches an existing key, keep the more specific subject (e.g. article + noun)."""
    o, n = str(old or "").strip(), str(new or "").strip()
    if not n:
        return o
    if not o:
        return n
    ol, nl = o.lower(), n.lower()
    if nl in ol and len(o) > len(n):
        return o
    if ol in nl and len(n) > len(o):
        return n
    return n


def _merge_lead_position_prefer_canonical(old: str, new: str) -> str:
    """Prefer shorter contained position when one string embeds the other (avoids duplicate verb junk)."""
    o, n = str(old or "").strip(), str(new or "").strip()
    if not n:
        return o
    if not o:
        return n
    ol, nl = o.lower(), n.lower()
    if ol in nl and len(o) < len(n):
        return o
    if nl in ol and len(n) < len(o):
        return n
    return n


def _primary_narration_block_for_lead_extraction(player_facing_text: str) -> str:
    """First \\n\\n-separated block only — ignores deterministic policy appendices after the GM primary."""
    t = str(player_facing_text or "").strip()
    if not t:
        return ""
    first = t.split("\n\n")[0].strip()
    return first if first else t


def remember_recent_contextual_leads(
    session: Dict[str, Any],
    scene_id: str,
    player_facing_text: str,
) -> List[Dict[str, Any]]:
    if not scene_id:
        return []
    discovered = extract_contextual_leads_from_text(_primary_narration_block_for_lead_extraction(player_facing_text))
    runtime = get_scene_runtime(session, scene_id)
    existing = _recent_contextual_leads(session, scene_id)
    turn_counter = int(session.get("turn_counter", 0) or 0)
    merged: List[Dict[str, Any]] = [dict(item) for item in existing]
    for lead in discovered:
        key = str(lead.get("key") or "").strip()
        if not key:
            continue
        matched = next((item for item in merged if str(item.get("key") or "").strip() == key), None)
        if matched is not None:
            merged_subject = _merge_lead_subject_prefer_richer(
                str(matched.get("subject") or ""),
                str(lead.get("subject") or ""),
            )
            merged_position = _merge_lead_position_prefer_canonical(
                str(matched.get("position") or ""),
                str(lead.get("position") or ""),
            )
            matched.update(
                {
                    "kind": str(lead.get("kind") or matched.get("kind") or "").strip(),
                    "subject": merged_subject,
                    "position": merged_position,
                    "named": bool(lead.get("named") or matched.get("named")),
                    "positioned": bool(lead.get("positioned") or matched.get("positioned")),
                    "mentions": int(matched.get("mentions", 1) or 1) + 1,
                    "last_turn": turn_counter,
                }
            )
            merged = [item for item in merged if str(item.get("key") or "").strip() != key] + [matched]
            continue
        merged.append(
            {
                "key": key,
                "kind": str(lead.get("kind") or "").strip(),
                "subject": str(lead.get("subject") or "").strip(),
                "position": str(lead.get("position") or "").strip(),
                "named": bool(lead.get("named")),
                "positioned": bool(lead.get("positioned")),
                "mentions": 1,
                "last_turn": turn_counter,
            }
        )
    runtime["recent_contextual_leads"] = merged[-_LEAD_HISTORY_LIMIT:]
    return list(runtime["recent_contextual_leads"])


def build_uncertainty_render_context(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
    turn_context: Dict[str, Any] | None = None,
    speaker_identity: Dict[str, Any] | str | None = None,
    scene_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    scene_env = scene_envelope if isinstance(scene_envelope, dict) else {}
    session_data = session if isinstance(session, dict) else {}
    world_data = world if isinstance(world, dict) else {}
    resolution_data = resolution if isinstance(resolution, dict) else {}
    scene_id = _resolve_scene_id(scene_env)
    location = _resolve_scene_location(scene_env)
    speaker = _resolve_uncertainty_speaker(
        session=session_data,
        world=world_data,
        resolution=resolution_data,
        scene_id=scene_id,
        speaker_identity=speaker_identity,
        scene_envelope=scene_env if isinstance(scene_env, dict) else None,
    )
    snapshot = _build_uncertainty_scene_snapshot(
        scene_envelope=scene_env,
        world=world_data,
        scene_id=scene_id,
        location=location,
        speaker_name=str(speaker.get("name") or "").strip(),
        scene_snapshot=scene_snapshot,
    )
    rt0 = get_scene_runtime(session_data, scene_id) if scene_id else {}
    raw_pending0 = list(rt0.get("pending_leads") or []) if scene_id else []
    snapshot["pending_leads"] = (
        filter_pending_leads_for_active_follow_surface(session_data, raw_pending0)
        if scene_id and isinstance(session_data, dict)
        else raw_pending0
    )
    snapshot["recent_contextual_leads"] = _recent_contextual_leads(session_data, scene_id)
    turn = _build_uncertainty_turn_context(
        player_text=player_text,
        session=session_data,
        resolution=resolution_data,
        turn_context=turn_context,
    )
    return {
        "speaker": speaker,
        "turn_context": turn,
        "scene_snapshot": snapshot,
        "recent_leads": list(snapshot.get("recent_contextual_leads") or []),
    }


def _speaker_delivery(turn_context: Dict[str, Any], category: str) -> str:
    privacy = str(turn_context.get("conversation_privacy") or "").strip().lower()
    engagement = str(turn_context.get("engagement_level") or "").strip().lower()
    base = {
        "unknown_identity": "studies the crowd before answering",
        "unknown_location": "jerks their chin toward the road",
        "unknown_motive": "taps the nearest solid point in sight",
        "unknown_method": "glances over the chokepoints",
        "unknown_quantity": "sweeps a look across the bodies in motion",
        "unknown_feasibility": "measures the barriers and the people around them",
    }.get(category, "answers after a short pause")
    if privacy in {"lowered_voice", "private", "whisper", "hushed"}:
        return f"lowers their voice and {base}"
    if engagement in {"guarded", "wary", "tense"}:
        return f"keeps it guarded and {base}"
    if engagement in {"hostile", "cold"}:
        return f"answers in a clipped tone and {base}"
    return base


def _classify_uncertainty_source(
    *,
    category: str,
    speaker_identity: Dict[str, Any],
    turn_context: Dict[str, Any],
) -> str:
    role = str((speaker_identity or {}).get("role") or "").strip().lower()
    resolution_kind = str(turn_context.get("resolution_kind") or "").strip().lower()
    social_intent_class = str(turn_context.get("social_intent_class") or "").strip().lower()
    adjudication_answer_type = str(turn_context.get("adjudication_answer_type") or "").strip().lower()
    requires_check = bool(turn_context.get("requires_check"))
    has_procedural_gate = bool(
        turn_context.get("check_skill")
        or turn_context.get("check_reason")
        or adjudication_answer_type in {"needs_concrete_action", "check_required"}
        or resolution_kind == "adjudication_query"
    )
    if requires_check or has_procedural_gate:
        return "procedural_insufficiency"
    if social_intent_class == "social_exchange" and bool(turn_context.get("is_direct_question")):
        return "npc_ignorance"
    if role == "npc" and bool(turn_context.get("is_direct_question")):
        return "npc_ignorance"
    if category == "unknown_feasibility" and has_procedural_gate:
        return "procedural_insufficiency"
    return "scene_ambiguity"


def _build_source_specific_edges(
    *,
    source: str,
    category: str,
    anchor: str,
    known_edge: str,
    unknown_edge: str,
    next_lead: str,
    turn_context: Dict[str, Any],
) -> Dict[str, str]:
    if source == "npc_ignorance":
        npc_known = {
            "unknown_identity": f"I have heard rumor around {anchor}, not names.",
            "unknown_location": f"I can point you toward {anchor}, not to a final door.",
            "unknown_motive": f"I can tell you where pressure is building around {anchor}, not who gives the orders.",
            "unknown_quantity": f"I can give you a rough sense from {anchor}, not a clean count.",
            "unknown_feasibility": f"I cannot promise it yet from {anchor}; one condition still decides it.",
            "unknown_method": f"I can tell what changed around {anchor}, not the full method behind it.",
        }.get(category, known_edge)
        npc_unknown = {
            "unknown_identity": "No one has given me a name they will stand behind.",
            "unknown_location": "After that, everyone points in different directions.",
            "unknown_motive": "The motive is still secondhand talk.",
            "unknown_quantity": "Any exact number shifts with every retelling.",
            "unknown_feasibility": "Until that condition is tested, I would be guessing.",
            "unknown_method": "The rest is fragments and crossed stories.",
        }.get(category, unknown_edge)
        return {"known_edge": npc_known, "unknown_edge": npc_unknown, "next_lead": next_lead}

    if source == "procedural_insufficiency":
        condition = str(turn_context.get("check_reason") or "").strip()
        if not condition:
            condition = str(turn_context.get("check_skill") or "").strip()
        proc_known = "No answer presents itself from here."
        proc_unknown = (
            f"Until someone tests {condition}, the answer does not exist yet."
            if condition
            else "Until the scene is pushed with a concrete action, the answer does not exist yet."
        )
        lead_text = str(next_lead or "").strip()
        proc_lead = f"The only lead is this: {lead_text}" if lead_text else "Only one lead remains visible right now."
        return {"known_edge": proc_known, "unknown_edge": proc_unknown, "next_lead": proc_lead}

    scene_known = {
        "unknown_identity": f"Nothing around {anchor} confirms a culprit yet.",
        "unknown_location": f"Nothing visible around {anchor} confirms the final destination yet.",
        "unknown_motive": f"The pressure around {anchor} is visible, but intent is not.",
        "unknown_quantity": f"The movement around {anchor} shows scale, not a firm count.",
        "unknown_feasibility": f"From this vantage, {anchor} does not settle whether it can be done yet.",
        "unknown_method": f"The signs around {anchor} show disruption, not a complete method.",
    }.get(category, known_edge)
    scene_unknown = {
        "unknown_identity": "Every account is still partial.",
        "unknown_location": "Beyond the visible markers, the trail breaks apart.",
        "unknown_motive": "No visible conclusion ties those pieces to one motive yet.",
        "unknown_quantity": "Any precise tally remains unverified.",
        "unknown_feasibility": "The deciding condition has not surfaced in clear form.",
        "unknown_method": "The remaining steps are still out of sight.",
    }.get(category, unknown_edge)
    return {"known_edge": scene_known, "unknown_edge": scene_unknown, "next_lead": next_lead}


def _scene_anchor_phrase(scene_snapshot: Dict[str, Any], *, category: str) -> str:
    if scene_snapshot.get("has_notice_board") and scene_snapshot.get("has_missing_patrol"):
        if category == "unknown_identity":
            return "the faces lingering over the missing patrol notice"
        if category == "unknown_motive":
            return "the new taxes, curfews, and the missing patrol posting"
        return "the missing patrol notice on the board"
    if scene_snapshot.get("has_tavern_runner"):
        return "the tavern runner hawking rumors for coin"
    if scene_snapshot.get("has_gate_or_checkpoint"):
        return "the checkpoint and muddy approach road"
    if scene_snapshot.get("has_refugees"):
        return "the refugee line pressed up against the road"
    first_visible = str(scene_snapshot.get("first_visible_detail") or "").strip()
    if first_visible:
        return first_visible.lower()
    location = str(scene_snapshot.get("location") or "").strip()
    if location:
        return f"what is visible in {location}"
    return "what is visible here"


def _scene_handle_candidates(
    *,
    scene_snapshot: Dict[str, Any],
    turn_context: Dict[str, Any],
    speaker_name: str,
) -> List[Dict[str, str]]:
    other_npcs = [
        str(name).strip()
        for name in (scene_snapshot.get("other_npc_names") or [])
        if isinstance(name, str) and str(name).strip()
    ]
    exit_label = str(scene_snapshot.get("exit_label") or "").strip()
    location = str(scene_snapshot.get("location") or "").strip()
    check_skill = str(turn_context.get("check_skill") or "").strip()
    check_reason = str(turn_context.get("check_reason") or "").strip()
    handles: List[Dict[str, str]] = []

    if check_reason or check_skill:
        handles.append(
            {
                "kind": "condition",
                "check_reason": check_reason,
                "check_skill": check_skill,
            }
        )
    if scene_snapshot.get("has_notice_board") and scene_snapshot.get("has_missing_patrol"):
        handles.append({"kind": "notice_board", "subject": "the missing patrol notice"})
    if scene_snapshot.get("has_tavern_runner"):
        handles.append({"kind": "tavern_runner", "subject": "the tavern runner"})
    if exit_label:
        handles.append({"kind": "exit", "subject": exit_label})
    if scene_snapshot.get("has_gate_or_checkpoint"):
        handles.append({"kind": "checkpoint", "subject": "the checkpoint"})
    if scene_snapshot.get("has_refugees"):
        handles.append({"kind": "refugee_line", "subject": "the refugee line"})
    if other_npcs:
        handles.append({"kind": "other_npc", "subject": other_npcs[0]})
    if speaker_name:
        handles.append({"kind": "speaker", "subject": speaker_name})
    if location:
        handles.append({"kind": "location", "subject": location})
    return handles


def _best_scene_lead(category: str, *, speaker_name: str, scene_snapshot: Dict[str, Any], turn_context: Dict[str, Any]) -> str:
    selected = choose_contextual_lead(
        {
            "category": category,
            "scene_snapshot": scene_snapshot,
            "turn_context": turn_context,
        },
        list(scene_snapshot.get("recent_contextual_leads") or []),
        {"role": "npc", "name": speaker_name} if speaker_name else {"role": "narrator", "name": ""},
        str(turn_context.get("player_text") or ""),
    )
    return str(selected.get("lead_text") or "")


def _build_known_edge(
    category: str,
    *,
    anchor: str,
    scene_snapshot: Dict[str, Any],
    speaker_role: str,
    turn_context: Dict[str, Any],
) -> str:
    if category == "unknown_identity":
        if scene_snapshot.get("has_tavern_runner"):
            return f"You can narrow it to the buyers circling {anchor}, but not to a sure name."
        return f"You can narrow it to the pattern around {anchor}, not to a single face."
    if category == "unknown_location":
        if scene_snapshot.get("has_gate_or_checkpoint"):
            return f"You can get a direction that runs past {anchor}, but not all the way to a final door."
        return f"You can pin down a last sighting at {anchor}, not the true destination."
    if category == "unknown_motive":
        return f"You can see the pressure gathering around {anchor}, not the heart of why."
    if category == "unknown_quantity":
        return f"{anchor.capitalize()} gives a rough sense of scale, not a clean count."
    if category == "unknown_feasibility":
        check_reason = str(turn_context.get("check_reason") or "").strip()
        if check_reason:
            return f"It mostly depends on {check_reason}."
        return f"It mostly depends on one local condition around {anchor}."
    return f"You can trace what happened around {anchor}, but the responsible hand is still unclear."


def _build_unknown_edge(category: str, *, speaker_role: str, scene_snapshot: Dict[str, Any]) -> str:
    if category == "unknown_identity":
        return "No name or badge anyone would trust has surfaced yet."
    if category == "unknown_location":
        return "Beyond that, everything dissolves into rumor."
    if category == "unknown_motive":
        return "What drives it is still tucked behind secondhand behavior."
    if category == "unknown_quantity":
        if scene_snapshot.get("has_refugees"):
            return "The crush keeps any exact tally slippery."
        return "No one has a clean count they will stand behind."
    if category == "unknown_feasibility":
        return "Until that condition is tested, the answer stays unsettled."
    return "Only fragments of the method are visible."


def _ensure_terminal_punctuation(text: str) -> str:
    line = str(text or "").strip()
    if not line:
        return ""
    return line if line[-1] in ".!?" else f"{line}."


def _quoted_sentence(text: str) -> str:
    line = _ensure_terminal_punctuation(text)
    return f'"{line}"' if line else ""


def _render_uncertainty_lines(
    uncertainty_type: str,
    *,
    turn_context: Dict[str, Any],
    speaker_identity: Dict[str, Any],
    scene_snapshot: Dict[str, Any],
) -> Dict[str, str]:
    category = uncertainty_type if uncertainty_type in UNCERTAINTY_CATEGORIES else "unknown_method"
    speaker_role = str(speaker_identity.get("role") or "narrator").strip().lower()
    speaker_name = str(speaker_identity.get("name") or "").strip() or "The voice answering you"
    source = _classify_uncertainty_source(
        category=category,
        speaker_identity=speaker_identity,
        turn_context=turn_context,
    )
    anchor = _scene_anchor_phrase(scene_snapshot, category=category)
    delivery = _speaker_delivery(turn_context, category)
    known_edge = _build_known_edge(
        category,
        anchor=anchor,
        scene_snapshot=scene_snapshot,
        speaker_role=speaker_role,
        turn_context=turn_context,
    )
    unknown_edge = _build_unknown_edge(
        category,
        speaker_role=speaker_role,
        scene_snapshot=scene_snapshot,
    )
    selected_lead = choose_contextual_lead(
        {
            "category": category,
            "scene_snapshot": scene_snapshot,
            "turn_context": turn_context,
        },
        list(scene_snapshot.get("recent_contextual_leads") or []),
        speaker_identity,
        str(turn_context.get("player_text") or ""),
    )
    next_lead = str(selected_lead.get("lead_text") or "")
    source_edges = _build_source_specific_edges(
        source=source,
        category=category,
        anchor=anchor,
        known_edge=known_edge,
        unknown_edge=unknown_edge,
        next_lead=next_lead,
        turn_context=turn_context,
    )
    return {
        "category": category,
        "source": source,
        "known_edge": str(source_edges.get("known_edge") or known_edge),
        "unknown_edge": str(source_edges.get("unknown_edge") or unknown_edge),
        "next_lead": str(source_edges.get("next_lead") or next_lead),
        "what_can_be_said_now": str(source_edges.get("known_edge") or known_edge),
        "what_is_not_nailed_down_yet": str(source_edges.get("unknown_edge") or unknown_edge),
        "best_current_lead": str(source_edges.get("next_lead") or next_lead),
        "selected_lead": selected_lead,
        "lead_candidates": list(selected_lead.get("alternatives") or []),
        "speaker_role": speaker_role,
        "speaker_name": speaker_name,
        "delivery": delivery,
    }


def _known_fact_response_text(*, subject: str = "", position: str = "", fact_text: str = "") -> str:
    fact = str(fact_text or "").strip()
    if fact:
        return _ensure_terminal_punctuation(fact)
    clean_subject = str(subject or "").strip()
    clean_position = str(position or "").strip().rstrip(".")
    if clean_subject and clean_position:
        return _ensure_terminal_punctuation(f"{clean_subject} is {clean_position}")
    if clean_subject:
        return _ensure_terminal_punctuation(clean_subject)
    if clean_position:
        return _ensure_terminal_punctuation(clean_position)
    return ""


def _known_fact_from_recent_leads(player_text: str, recent_leads: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    prompt_low = str(player_text or "").strip().lower()
    if not prompt_low:
        return None
    category = _classify_uncertainty_category(player_text)
    follow_up_find = _looks_like_follow_up_find_request(prompt_low)
    follow_up_identity = any(token in prompt_low for token in _LEAD_FOLLOW_UP_PRONOUN_TOKENS)
    for lead in reversed(recent_leads[-3:]):
        if not isinstance(lead, dict):
            continue
        subject = str(lead.get("subject") or "").strip()
        position = str(lead.get("position") or "").strip()
        if not subject:
            continue
        if category == "unknown_location" and position:
            if follow_up_find or _lead_subject_matches_prompt(subject, prompt_low):
                return {
                    "text": _known_fact_response_text(subject=subject, position=position),
                    "source": "recent_dialogue_continuity",
                    "subject": subject,
                    "position": position,
                }
        if category == "unknown_identity" and (lead.get("named") or _lead_subject_matches_prompt(subject, prompt_low)):
            if follow_up_identity or _lead_subject_matches_prompt(subject, prompt_low):
                return {
                    "text": _ensure_terminal_punctuation(f"You recognize them as {subject}"),
                    "source": "recent_dialogue_continuity",
                    "subject": subject,
                    "position": position,
                }
    return None


def _known_fact_from_scene_location(player_text: str, scene_snapshot: Dict[str, Any]) -> Dict[str, Any] | None:
    prompt_low = str(player_text or "").strip().lower()
    location = str(scene_snapshot.get("location") or "").strip()
    if not location or not prompt_low:
        return None
    if any(token in prompt_low for token in _KNOWN_SCENE_LOCATION_PROMPTS):
        return {
            "text": _ensure_terminal_punctuation(f"You are in {location}"),
            "source": "current_scene_state",
            "subject": location,
            "position": "",
        }
    return None


def _known_fact_from_visible_figures(player_text: str, scene_snapshot: Dict[str, Any]) -> Dict[str, Any] | None:
    prompt_low = str(player_text or "").strip().lower()
    if not prompt_low:
        return None
    category = _classify_uncertainty_category(player_text)
    follow_up_find = _looks_like_follow_up_find_request(prompt_low)
    follow_up_identity = any(token in prompt_low for token in _LEAD_FOLLOW_UP_PRONOUN_TOKENS)
    candidates: List[tuple[str, Dict[str, Any]]] = []
    for fact in (scene_snapshot.get("visible_facts") or [])[:8]:
        candidate = _extract_visible_figure_candidate(str(fact))
        if candidate is None:
            continue
        candidates.append((str(fact).strip(), candidate))
    if not candidates:
        return None

    single_live_figure = len(
        [1 for _fact, candidate in candidates if candidate.get("named") or candidate.get("positioned")]
    ) == 1
    for fact, candidate in candidates:
        subject = str(candidate.get("subject") or "").strip()
        position = str(candidate.get("position") or "").strip()
        if not subject:
            continue
        if category == "unknown_location" and position:
            if _lead_subject_matches_prompt(subject, prompt_low) or (follow_up_find and single_live_figure):
                return {
                    "text": _known_fact_response_text(subject=subject, position=position),
                    "source": "visible_entity_descriptor",
                    "subject": subject,
                    "position": position,
                    "fact_text": fact,
                }
        if category == "unknown_identity" and candidate.get("named"):
            if _lead_subject_matches_prompt(subject, prompt_low) or (follow_up_identity and single_live_figure):
                return {
                    "text": _ensure_terminal_punctuation(f"You recognize them as {subject}"),
                    "source": "visible_entity_descriptor",
                    "subject": subject,
                    "position": position,
                    "fact_text": fact,
                }
    return None


def _known_fact_from_visible_scene_fact(player_text: str, scene_snapshot: Dict[str, Any]) -> Dict[str, Any] | None:
    category = _classify_uncertainty_category(player_text)
    if category in {"unknown_quantity", "unknown_feasibility", "unknown_motive"}:
        return None
    question_tokens = _question_content_tokens(player_text)
    if not question_tokens:
        return None
    best_fact = ""
    best_overlap: List[str] = []
    for fact in (scene_snapshot.get("visible_facts") or [])[:8]:
        fact_text = str(fact).strip()
        if not fact_text:
            continue
        fact_low = fact_text.lower()
        overlap = [tok for tok in question_tokens if tok in fact_low]
        if len(overlap) > len(best_overlap):
            best_fact = fact_text
            best_overlap = overlap
    if not best_fact:
        return None
    if category == "unknown_location":
        best_low = best_fact.lower()
        has_location_cue = bool(
            re.search(r"\b(near|by|at|outside|inside|beside|under|along|toward|across|behind|beyond|around|road|entrance|gate|checkpoint)\b", best_low)
            or " crowd " in best_low
            or " crowds " in best_low
            or " waits " in best_low
            or " stands " in best_low
            or " lingers " in best_low
            or " watches " in best_low
        )
        if not has_location_cue:
            return None
    if len(best_overlap) >= 2 or any(len(tok) >= 7 for tok in best_overlap):
        return {
            "text": _ensure_terminal_punctuation(best_fact),
            "source": "observable_scene_fact",
            "subject": best_fact,
            "position": "",
            "matched_tokens": best_overlap,
        }
    return None


def _resolve_known_fact_from_context(player_text: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    if not _is_direct_player_question(player_text):
        return None
    scene_snapshot = context.get("scene_snapshot") if isinstance(context.get("scene_snapshot"), dict) else {}
    recent_leads = scene_snapshot.get("recent_contextual_leads") if isinstance(scene_snapshot.get("recent_contextual_leads"), list) else []
    if _looks_like_follow_up_find_request(str(player_text or "")):
        lead_first = _known_fact_from_recent_leads(player_text, recent_leads)
        if isinstance(lead_first, dict):
            t0 = str(lead_first.get("text") or "").strip()
            if t0 and _is_valid_player_facing_fallback_answer(
                t0,
                player_text=player_text,
                known_fact=lead_first,
                failure_class="unresolved_question",
            ):
                return lead_first
    candidates: List[Dict[str, Any] | None] = [
        _known_fact_from_recent_leads(player_text, recent_leads),
        _known_fact_from_scene_location(player_text, scene_snapshot),
        _known_fact_from_visible_figures(player_text, scene_snapshot),
        _known_fact_from_visible_scene_fact(player_text, scene_snapshot),
    ]
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        t = str(cand.get("text") or "").strip()
        if not t:
            continue
        if _is_valid_player_facing_fallback_answer(
            t,
            player_text=player_text,
            known_fact=cand,
            failure_class="unresolved_question",
        ):
            return cand
    return None


def _fallback_known_fact_answer_locally_relevant(
    answer: str,
    player_text: str,
    known_fact: Dict[str, Any] | None,
    *,
    failure_class: str = "",
) -> bool:
    """Loose token/anchor overlap so continuity snippets are not reused across unrelated questions."""
    al = answer.lower()
    player_low = str(player_text or "").strip().lower()
    fc = str(failure_class or "").strip()
    if fc == "answer":
        qtok = _question_content_tokens(player_text)
        if not qtok:
            return True
        return any(tok in al for tok in qtok)

    if any(
        al.startswith(prefix)
        for prefix in ("you are in ", "you're in ", "you are at ", "you're at ")
    ):
        if "where" in player_low or any(t in player_low for t in _KNOWN_SCENE_LOCATION_PROMPTS):
            return True

    if al.startswith("you recognize them as "):
        if re.search(r"\bwho\b", player_low) or "they" in player_low or "them" in player_low:
            return True

    if isinstance(known_fact, dict):
        src = str(known_fact.get("source") or "").strip()
        if src == "recent_dialogue_continuity":
            subj = str(known_fact.get("subject") or "").strip().lower()
            if subj and subj in al:
                if _looks_like_follow_up_find_request(player_low):
                    return True
                if any(t in player_low for t in _LEAD_FOLLOW_UP_PRONOUN_TOKENS):
                    return True

    qtok = _question_content_tokens(player_text)
    for tok in qtok:
        if tok in al:
            return True

    if isinstance(known_fact, dict):
        for key in ("subject", "position", "fact_text"):
            chunk = str(known_fact.get(key) or "").strip().lower()
            if not chunk:
                continue
            if chunk in player_low:
                return True
            for w in chunk.split():
                w2 = re.sub(r"[^\w]+", "", w)
                if len(w2) >= 4 and w2 in player_low:
                    return True
    return False


def _is_valid_player_facing_fallback_answer(
    text: str,
    *,
    player_text: str = "",
    known_fact: Dict[str, Any] | None = None,
    failure_class: str = "",
) -> bool:
    """True when *text* is safe to emit or embed as established continuity (not planner residue or malformed glue)."""
    raw = str(text or "").strip()
    if len(raw) < 6 or len(raw) > 600:
        return False
    low = raw.lower()
    if detect_validator_voice(raw):
        return False

    planner_markers = (
        "concrete turn",
        "gives you one",
        "until it gives",
        "retry target",
        "rule priority hierarchy",
        "rule priority",
        "json shape",
        "correct only this failure",
        "same json shape",
        "best lead",
        "selected_lead",
        "validator voice",
        "system prompt",
        "as an ai",
        "established in current scene state or dialogue continuity",
    )
    for m in planner_markers:
        if m in low:
            return False
    if re.search(r"\bstay with\b.+\buntil\b", low):
        return False
    if re.search(r"\b(stay|wait|hold)\b.+\buntil\b.+\b(concrete|turn|beat)\b", low):
        return False

    if re.search(r"\byou should\b", low) or re.search(r"\byou could\b", low):
        return False
    if re.search(r"\btry to\b", low) or re.search(r"\bconsider (doing|trying)\b", low):
        return False

    mrec = re.match(r"^you recognize them as\s+(.+)$", low)
    if mrec:
        tail = mrec.group(1)
        if re.search(r"\b(stay|until|gives you|concrete|reacting)\b", tail):
            return False
        if "rumor" in tail and re.search(r"\b(missing|until|stay|patrol|reacting)\b", tail):
            return False
        if tail.count(",") > 4:
            return False

    words = re.findall(r"[a-zA-Z']+", raw)
    if len(words) >= 6:
        long_ratio = sum(1 for w in words if len(w) > 16) / len(words)
        if long_ratio > 0.2:
            return False

    pl = str(player_text or "").strip().lower()
    if pl and not _fallback_known_fact_answer_locally_relevant(
        raw,
        player_text,
        known_fact,
        failure_class=failure_class,
    ):
        return False
    return True


def _question_resolution_exempt_for_resolved_observe(resolution: Dict[str, Any] | None) -> bool:
    """Executed observe already answered a perception request; interrogative form is not leftover."""
    if not isinstance(resolution, dict):
        return False
    return str(resolution.get("kind") or "").strip().lower() == "observe"


def _question_resolution_exempt_for_resolved_adjudication(resolution: Dict[str, Any] | None) -> bool:
    """Executed adjudication already answered a procedural question; interrogative form is not leftover."""
    if not isinstance(resolution, dict):
        return False
    if str(resolution.get("kind") or "").strip().lower() != "adjudication_query":
        return False
    adjudication = resolution.get("adjudication")
    if not isinstance(adjudication, dict):
        return False
    return bool(str(adjudication.get("player_facing_text") or "").strip())


def _question_resolution_exempt_for_open_crowd_social(resolution: Dict[str, Any] | None) -> bool:
    """Crowd / open-call social turns are not one-to-one question-resolution contracts."""
    if not isinstance(resolution, dict):
        return False
    soc = resolution.get("social")
    if not isinstance(soc, dict):
        return False
    if str(soc.get("social_intent_class") or "").strip().lower() == "open_call":
        return True
    if soc.get("open_social_solicitation") and soc.get("npc_reply_expected") is not True:
        return True
    return False


def resolve_known_fact_before_uncertainty(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
    turn_context: Dict[str, Any] | None = None,
    speaker_identity: Dict[str, Any] | str | None = None,
    scene_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any] | None:
    context = build_uncertainty_render_context(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
        turn_context=turn_context,
        speaker_identity=speaker_identity,
        scene_snapshot=scene_snapshot,
    )
    known = _resolve_known_fact_from_context(player_text, context)
    if not isinstance(known, dict):
        return None
    known["speaker"] = dict(context.get("speaker") or {})
    known["turn_context"] = dict(context.get("turn_context") or {})
    known["scene_snapshot"] = dict(context.get("scene_snapshot") or {})
    return known


def question_resolution_rule_check(
    *,
    player_text: str,
    gm_reply_text: str,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Check the Question Resolution Rule for direct player questions.

    Returns:
      {applies: bool, ok: bool, reasons: [str], optional social answer debug keys when social_exchange applies}
    """
    player = str(player_text or "").strip()
    reply = str(gm_reply_text or "").strip()
    applies = _is_direct_player_question(player)
    if not applies:
        return {"applies": False, "ok": True, "reasons": []}
    if is_scene_directed_watch_question(player):
        return {"applies": False, "ok": True, "reasons": []}
    if _question_resolution_exempt_for_resolved_observe(resolution):
        return {"applies": False, "ok": True, "reasons": []}
    if _question_resolution_exempt_for_resolved_adjudication(resolution):
        return {"applies": False, "ok": True, "reasons": []}
    if _question_resolution_exempt_for_open_crowd_social(resolution):
        return {"applies": False, "ok": True, "reasons": []}
    if not reply:
        return {"applies": True, "ok": False, "reasons": ["question_rule:empty_reply"]}

    social_contract = _social_exchange_first_sentence_contract(
        player_text=player,
        gm_reply_text=reply,
        resolution=resolution,
    )

    def _with_social_answer_metadata(result: Dict[str, Any]) -> Dict[str, Any]:
        if not social_contract.get("applies"):
            return result
        out = dict(result)
        for k in ("social_answer_validation_mode", "first_sentence_substantive", "rejected_as_cinematic_nonanswer"):
            if k in social_contract:
                out[k] = social_contract[k]
        return out

    if social_contract.get("applies") and not social_contract.get("ok"):
        return _with_social_answer_metadata(
            {
                "applies": True,
                "ok": False,
                "reasons": list(social_contract.get("reasons") or []),
            }
        )

    first = _first_sentence(reply)
    first_low = first.lower()
    reasons: List[str] = []

    if "?" in first:
        reasons.append("question_rule:asked_question_before_answer")

    has_refusal = any(p in first_low for p in _QUESTION_RESOLUTION_REFUSAL_PHRASES)
    has_starter = any(first_low.startswith(p) for p in _QUESTION_RESOLUTION_ANSWER_STARTERS)
    q_tokens = _question_content_tokens(player)
    has_token_overlap = any(tok in first_low for tok in q_tokens) if q_tokens else False

    if has_refusal and not social_contract.get("applies"):
        reasons.append("question_rule:refusal_or_meta_disallowed")

    ok = bool(
        ("?" not in first)
        and ((not has_refusal) or bool(social_contract.get("applies")))
        and (has_starter or has_token_overlap or bool(social_contract.get("applies")))
    )
    if not ok and not reasons:
        reasons.append("question_rule:first_sentence_not_explicit_answer")
    return _with_social_answer_metadata({"applies": True, "ok": ok, "reasons": reasons})


def classify_uncertainty(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
    turn_context: Dict[str, Any] | None = None,
    speaker_identity: Dict[str, Any] | str | None = None,
    scene_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Classify unresolved answers into a compact, inspectable uncertainty shape."""
    context = build_uncertainty_render_context(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
        turn_context=turn_context,
        speaker_identity=speaker_identity,
        scene_snapshot=scene_snapshot,
    )
    known_fact = _resolve_known_fact_from_context(player_text, context)
    if isinstance(known_fact, dict):
        ktxt = str(known_fact.get("text") or "").strip()
        if ktxt and _is_valid_player_facing_fallback_answer(
            ktxt,
            player_text=player_text,
            known_fact=known_fact,
            failure_class="unresolved_question",
        ):
            return {
                "category": "",
                "known_fact": known_fact,
                "known_edge": ktxt,
                "unknown_edge": "",
                "next_lead": "",
                "speaker": context["speaker"],
                "turn_context": context["turn_context"],
                "scene_snapshot": context["scene_snapshot"],
                "speaker_role": str((context.get("speaker") or {}).get("role") or "narrator").strip().lower(),
                "speaker_name": str((context.get("speaker") or {}).get("name") or "").strip(),
                "delivery": "",
            }
    category = _classify_uncertainty_category(player_text)
    rendered = _render_uncertainty_lines(
        category,
        turn_context=context["turn_context"],
        speaker_identity=context["speaker"],
        scene_snapshot=context["scene_snapshot"],
    )
    rendered["speaker"] = context["speaker"]
    rendered["turn_context"] = context["turn_context"]
    rendered["scene_snapshot"] = context["scene_snapshot"]
    return rendered


def render_uncertainty_response(
    uncertainty: Dict[str, Any] | None = None,
    *,
    uncertainty_type: str | None = None,
    turn_context: Dict[str, Any] | None = None,
    speaker_identity: Dict[str, Any] | None = None,
    scene_snapshot: Dict[str, Any] | None = None,
    player_text: str = "",
) -> str:
    """Render a bounded answer with a known edge, uncertainty edge, and lead."""
    if not isinstance(uncertainty, dict):
        if not uncertainty_type:
            return ""
        uncertainty = _render_uncertainty_lines(
            uncertainty_type,
            turn_context=turn_context if isinstance(turn_context, dict) else {},
            speaker_identity=speaker_identity if isinstance(speaker_identity, dict) else {"role": "narrator", "id": "", "name": ""},
            scene_snapshot=scene_snapshot if isinstance(scene_snapshot, dict) else {},
        )
    known_fact = uncertainty.get("known_fact") if isinstance(uncertainty.get("known_fact"), dict) else {}
    known_fact_text = str(known_fact.get("text") or "").strip()
    if known_fact_text and _is_valid_player_facing_fallback_answer(
        known_fact_text,
        player_text=str(player_text or ""),
        known_fact=known_fact,
        failure_class="unresolved_question",
    ):
        return _ensure_terminal_punctuation(known_fact_text)
    category = str(uncertainty.get("category") or uncertainty_type or "").strip()
    source = str(uncertainty.get("source") or "").strip()
    if source not in UNCERTAINTY_SOURCE_MODES:
        if speaker_role := str(
            uncertainty.get("speaker_role")
            or ((speaker_identity or {}).get("role") if isinstance(speaker_identity, dict) else "")
            or ((uncertainty.get("speaker") or {}).get("role") if isinstance(uncertainty.get("speaker"), dict) else "")
            or "narrator"
        ).strip().lower():
            source = "npc_ignorance" if speaker_role == "npc" else "scene_ambiguity"
        else:
            source = "scene_ambiguity"
    known_edge = str(
        uncertainty.get("known_edge")
        or uncertainty.get("what_can_be_said_now")
        or ""
    ).strip()
    unknown_edge = str(
        uncertainty.get("unknown_edge")
        or uncertainty.get("what_is_not_nailed_down_yet")
        or ""
    ).strip()
    next_lead = str(
        uncertainty.get("next_lead")
        or uncertainty.get("best_current_lead")
        or ""
    ).strip()
    speaker_role = str(
        uncertainty.get("speaker_role")
        or ((speaker_identity or {}).get("role") if isinstance(speaker_identity, dict) else "")
        or ((uncertainty.get("speaker") or {}).get("role") if isinstance(uncertainty.get("speaker"), dict) else "")
        or "narrator"
    ).strip().lower()
    speaker_name = str(
        uncertainty.get("speaker_name")
        or ((speaker_identity or {}).get("name") if isinstance(speaker_identity, dict) else "")
        or ((uncertainty.get("speaker") or {}).get("name") if isinstance(uncertainty.get("speaker"), dict) else "")
        or "The voice answering you"
    ).strip()
    delivery = str(uncertainty.get("delivery") or "").strip()

    if source == "npc_ignorance" and speaker_role == "npc":
        intro = _ensure_terminal_punctuation(f"{speaker_name} {delivery}".strip())
        quoted = [
            _quoted_sentence(" ".join(p for p in (known_edge, unknown_edge) if p)),
            _quoted_sentence(next_lead),
        ]
        return " ".join(part for part in [intro, *quoted] if part).strip()

    if source == "procedural_insufficiency":
        parts = [
            _ensure_terminal_punctuation(known_edge),
            _ensure_terminal_punctuation(unknown_edge),
            _ensure_terminal_punctuation(next_lead),
        ]
        return " ".join(part for part in parts if part).strip()

    if category in {"unknown_location", "unknown_feasibility"}:
        parts = [
            _ensure_terminal_punctuation(known_edge),
            _ensure_terminal_punctuation(" ".join(p for p in (unknown_edge, next_lead) if p)),
        ]
    elif category in {"unknown_identity", "unknown_method"}:
        parts = [
            _ensure_terminal_punctuation(" ".join(p for p in (known_edge, unknown_edge) if p)),
            _ensure_terminal_punctuation(next_lead),
        ]
    else:
        parts = [
            _ensure_terminal_punctuation(known_edge),
            _ensure_terminal_punctuation(unknown_edge),
            _ensure_terminal_punctuation(next_lead),
        ]
    return " ".join(part for part in parts if part).strip()


def _apply_uncertainty_to_gm(
    gm: Dict[str, Any],
    *,
    uncertainty: Dict[str, Any],
    reason: str,
    replace_text: bool = False,
    player_text: str = "",
) -> Dict[str, Any]:
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    unc = dict(uncertainty) if isinstance(uncertainty, dict) else {}
    kf = unc.get("known_fact") if isinstance(unc.get("known_fact"), dict) else {}
    ktxt = str(kf.get("text") or "").strip()
    if ktxt and not _is_valid_player_facing_fallback_answer(
        ktxt,
        player_text=str(player_text or ""),
        known_fact=kf,
        failure_class="unresolved_question",
    ):
        unc.pop("known_fact", None)
        ke = str(unc.get("known_edge") or "").strip()
        if ke == ktxt:
            unc.pop("known_edge", None)
            unc.pop("what_can_be_said_now", None)
    known_fact = unc.get("known_fact") if isinstance(unc.get("known_fact"), dict) else {}
    rendered = render_uncertainty_response(unc, player_text=str(player_text or ""))
    if not rendered:
        return gm
    existing = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    gm["player_facing_text"] = rendered if replace_text or not existing.strip() else (rendered + "\n\n" + existing.strip()).strip()
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    if known_fact:
        gm["tags"] = list(tags) + ["known_fact_guard"]
    else:
        category = str(uncertainty.get("category") or "").strip()
        uncertainty_tag = f"uncertainty:{category}" if category else "uncertainty"
        source = str(uncertainty.get("source") or "").strip()
        source_tag = f"uncertainty_source:{source}" if source else ""
        gm["tags"] = list(tags) + [t for t in (uncertainty_tag, source_tag) if t]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    if known_fact:
        source = str(known_fact.get("source") or "known_fact").strip()
        gm["debug_notes"] = (dbg + " | " if dbg else "") + f"{reason}:known_fact_guard:{source}"
    else:
        category = str(uncertainty.get("category") or "").strip()
        source = str(uncertainty.get("source") or "").strip()
        suffix = f"{category or 'unknown'}:{source}" if source else f"{category or 'unknown'}"
        gm["debug_notes"] = (dbg + " | " if dbg else "") + f"{reason}:{suffix}"
    return gm


def _bounded_spoiler_safe_text(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> str:
    """Return a safe in-world fallback that still answers when secrets must stay hidden."""
    if _is_direct_player_question(player_text):
        known_fact = resolve_known_fact_before_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        if isinstance(known_fact, dict) and str(known_fact.get("text") or "").strip():
            kt = str(known_fact.get("text") or "").strip()
            if _is_valid_player_facing_fallback_answer(
                kt,
                player_text=player_text,
                known_fact=known_fact,
                failure_class="unresolved_question",
            ):
                return kt
        return render_uncertainty_response(
            classify_uncertainty(
                player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            )
        )
    return (
        "You notice small, telling details in the crowd and the way people watch one another, "
        "but nothing resolves into a clear answer yet. If you investigate more closely or question locals, "
        "you may uncover more."
    )


def _validator_voice_world_fallback(
    *,
    scene_envelope: Dict[str, Any],
    player_text: str,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> str:
    """Rebuild leaked validator voice as in-world uncertainty."""
    if _is_direct_player_question(player_text):
        known_fact = resolve_known_fact_before_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        if isinstance(known_fact, dict) and str(known_fact.get("text") or "").strip():
            kt = str(known_fact.get("text") or "").strip()
            if _is_valid_player_facing_fallback_answer(
                kt,
                player_text=player_text,
                known_fact=known_fact,
                failure_class="unresolved_question",
            ):
                return kt
        return render_uncertainty_response(
            classify_uncertainty(
                player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            )
        )
    location = _resolve_scene_location(scene_envelope)
    visible = _scene_visible_facts(scene_envelope)
    anchor = _clean_scene_detail(visible[0]).lower() if visible else "the immediate scene"
    loc_phrase = f" in {location}" if location else ""
    return (
        f"You only get fragments{loc_phrase}: {anchor}. The rest stays blurred until you push harder on something specific."
    )


def _active_interaction_target_id(session: Dict[str, Any]) -> str:
    interaction = session.get("interaction_context") if isinstance(session, dict) else None
    if not isinstance(interaction, dict):
        return ""
    return str(interaction.get("active_interaction_target_id") or "").strip()


def _resolve_npc_name(world: Dict[str, Any], npc_id: str, scene_id: str) -> str:
    if not npc_id:
        return ""
    npcs = world.get("npcs") if isinstance(world, dict) else None
    if not isinstance(npcs, list):
        return ""
    nid_low = npc_id.lower()
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid or nid.lower() != nid_low:
            continue
        loc = str(npc.get("location") or npc.get("scene_id") or "").strip()
        if scene_id and loc and loc != scene_id:
            continue
        return str(npc.get("name") or "").strip()
    return ""


def _world_faction_names(world: Dict[str, Any]) -> List[str]:
    factions = world.get("factions") if isinstance(world, dict) else None
    if not isinstance(factions, list):
        return []
    out: List[str] = []
    for f in factions:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name") or "").strip()
        if name:
            out.append(name)
    return out


def _in_scene_npc_names(world: Dict[str, Any], scene_id: str) -> List[str]:
    npcs = world.get("npcs") if isinstance(world, dict) else None
    if not isinstance(npcs, list):
        return []
    out: List[str] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        loc = str(npc.get("location") or npc.get("scene_id") or "").strip()
        if scene_id and loc and loc != scene_id:
            continue
        name = str(npc.get("name") or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def _structured_contract_failure(
    form: str,
    reason: str,
    *,
    provider_response_contract: str = "structured_realization",
) -> Dict[str, Any]:
    """Model text that is not a claim envelope. It is not narration."""
    normalized = form if form in {"plain", "malformed", "structured"} else "malformed"
    return {
        'player_facing_text': '',
        'tags': ['structured_output_rejected', 'structured_contract_failure'],
        'scene_update': None,
        'activate_scene_id': None,
        'new_scene_draft': None,
        'world_updates': None,
        'suggested_action': None,
        'debug_notes': 'Structured realization envelope required.',
        'metadata': {
            'output_form': normalized,
            'structured_output_rejected': True,
            'structured_contract_failure': True,
            'structured_contract_reason': reason,
            'provider_response_contract': provider_response_contract,
            'legacy_fallback': False,
        },
    }


def _safe_json(
    text: str,
    *,
    require_structured_claims: bool = False,
    provider_response_contract: str = "structured_realization",
) -> Dict[str, Any]:
    """Parse model text into a safe, normalized GM response dict.

    A structured response contributes only its player-facing text. The raw
    envelope is never narration. An unparseable or incomplete envelope is
    rejected so a later seal cannot publish it.

    ``require_structured_claims`` is the live generation path. Plain prose and
    legacy player-facing JSON are structured-contract failures there. Direct
    unit tests may still parse the older shapes.
    """
    if provider_response_contract == "narration_only":
        raw = str(text or "").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return _structured_contract_failure(
                "malformed",
                "malformed_narration_only_envelope",
                provider_response_contract=provider_response_contract,
            )
        if not isinstance(parsed, dict):
            return _structured_contract_failure(
                "malformed",
                "malformed_narration_only_envelope",
                provider_response_contract=provider_response_contract,
            )
        keys = {str(key) for key in parsed}
        if keys != {"narration"}:
            if "declared_claims" in keys:
                reason = "unexpected_declared_claims"
            elif "narration" not in keys:
                reason = "missing_narration"
            else:
                reason = "unexpected_narration_only_field"
            return _structured_contract_failure(
                "structured",
                reason,
                provider_response_contract=provider_response_contract,
            )
        prose = parsed.get("narration")
        if not isinstance(prose, str) or not prose.strip():
            return _structured_contract_failure(
                "structured",
                "missing_narration" if prose is None else "invalid_narration",
                provider_response_contract=provider_response_contract,
            )
        from game.structured_player_output import text_contains_response_envelope

        if text_contains_response_envelope(prose):
            return _structured_contract_failure(
                "structured",
                "nested_response_envelope",
                provider_response_contract=provider_response_contract,
            )
        narration = prose.strip()
        return {
            'player_facing_text': narration,
            'tags': [],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Parsed narration-only model output.',
            'metadata': {
                'output_form': 'structured',
                'provider_response_contract': provider_response_contract,
                'realization_envelope': {
                    'schema_version': 1,
                    'provider_response_contract': provider_response_contract,
                    'declared_claims': [],
                    'narration': narration,
                    'structured_contract_present': True,
                    'legacy_fallback': False,
                    'normalized_empty_declarations': True,
                    'declaration_authorship': False,
                },
            },
        }

    from game.structured_player_output import classify_model_output

    classified = classify_model_output(text)
    form = str(classified.get("form") or "")
    if form == "malformed":
        if require_structured_claims:
            return _structured_contract_failure(
                "malformed",
                "malformed_envelope",
                provider_response_contract=provider_response_contract,
            )
        return {
            'player_facing_text': '',
            'tags': ['structured_output_rejected'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Rejected structured model envelope.',
            'metadata': {'output_form': 'malformed', 'structured_output_rejected': True},
        }
    if form == "plain":
        if require_structured_claims:
            return _structured_contract_failure(
                "plain",
                "missing_structured_envelope",
                provider_response_contract=provider_response_contract,
            )
        prose = str(classified.get("player_facing_text") or "")
        return {
            'player_facing_text': prose or 'No narration provided.',
            'tags': ['fallback'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Non-JSON response fallback.',
            'metadata': {'output_form': 'plain', 'legacy_fallback': True},
        }

    parsed = classified.get("fields") if isinstance(classified.get("fields"), dict) else {}
    prose = str(classified.get("player_facing_text") or "")
    declared_claims = parsed.get("declared_claims") if isinstance(parsed.get("declared_claims"), list) else None
    if require_structured_claims and declared_claims is None:
        return _structured_contract_failure(
            "structured",
            "missing_declared_claims",
            provider_response_contract=provider_response_contract,
        )
    proposals = parsed.get("improvisation_proposals") if isinstance(parsed.get("improvisation_proposals"), list) else None
    out: Dict[str, Any] = {
        'player_facing_text': prose,
        'tags': parsed.get('tags') if isinstance(parsed.get('tags'), list) else [],
        'scene_update': parsed.get('scene_update') if isinstance(parsed.get('scene_update'), dict) else None,
        'activate_scene_id': parsed.get('activate_scene_id') if isinstance(parsed.get('activate_scene_id'), str) else None,
        'new_scene_draft': parsed.get('new_scene_draft') if isinstance(parsed.get('new_scene_draft'), dict) else None,
        'world_updates': parsed.get('world_updates') if isinstance(parsed.get('world_updates'), dict) else None,
        'suggested_action': parsed.get('suggested_action') if isinstance(parsed.get('suggested_action'), dict) else None,
        'debug_notes': parsed.get('debug_notes') if isinstance(parsed.get('debug_notes'), str) else 'Parsed model output.',
        'metadata': {
            'output_form': 'structured',
            'provider_response_contract': provider_response_contract,
            'realization_envelope': {
                'schema_version': 1,
                'provider_response_contract': provider_response_contract,
                'declared_claims': declared_claims,
                'narration': prose,
                'structured_contract_present': declared_claims is not None,
                'legacy_fallback': False if require_structured_claims else declared_claims is None,
            },
        },
    }
    if proposals is not None:
        out["improvisation_proposals"] = proposals
    return out


def _social_escalation_prompt_instruction(se: Dict[str, Any]) -> str:
    """Single instruction line derived from :func:`game.social.determine_social_escalation_outcome`."""
    parts = [
        "SOCIAL TOPIC ESCALATION (engine-locked): The player is repeating a tracked topic with this NPC. "
        f"escalation_level={se.get('escalation_level')}; reason={se.get('escalation_reason')}; effect={se.get('escalation_effect')}."
    ]
    if se.get("topic_exhausted"):
        parts.append(
            "The NPC has no further engine-known specifics on this thread: state that clearly. "
            "Do not imply undisclosed insider facts; give one concrete redirect (person to ask, place to go, or notice/object to check)."
        )
    if se.get("force_partial_answer"):
        parts.append(
            "Provide at least one new partial detail this NPC could credibly know, "
            "or a redirected lead tied to an in-scene source—do not recycle the same vague refusal."
        )
    if se.get("force_actionable_lead"):
        parts.append(
            "Deliver an actionable next step or an explicit condition/cost for more (time, risk, favor, privacy, coin)."
        )
    if se.get("convert_refusal_to_conditioned_offer"):
        parts.append(
            "If pushing back, frame it as a conditioned offer: what would change the answer (where/when/who else/what proof)."
        )
    if se.get("trigger_scene_momentum"):
        parts.append(
            "Show a visible social consequence (suspicion, public attention, irritation, withdrawal). "
            "Include a scene_momentum tag when the beat warrants it."
        )
    return " ".join(parts)


def collect_narration_context_call_kwargs(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None = None,
    scene_runtime: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
) -> Dict[str, Any]:
    """Collect keyword arguments for :func:`game.prompt_context.build_narration_context` (shared with API bundle seam)."""
    active_id = (session.get("active_scene_id") or "").strip()
    if active_id:
        scene = get_effective_scene(session, active_id)

    if session.get("chat_history") == []:
        recent_log_for_prompt: List[Dict[str, Any]] = []
        session.pop("chat_history", None)
        print("[PROMPT] fresh campaign prompt constructed")
    else:
        recent_log_for_prompt = recent_log[-8:]

    public_scene, discoverable_raw, hidden = _scene_layers(scene)
    intent = classify_player_intent(user_text)
    allow_disc = bool(intent.get("allow_discoverable_clues"))
    social_authority = _session_social_authority(session)
    known_answer_hint = (
        resolve_known_fact_before_uncertainty(
            user_text,
            scene_envelope=scene,
            session=session,
            world=world,
            resolution=resolution,
        )
        if _is_direct_player_question(user_text)
        else None
    )
    uncertainty_hint = None
    if (
        not social_authority
        and _is_direct_player_question(user_text)
        and not known_answer_hint
    ):
        uncertainty_hint = classify_uncertainty(
            user_text,
            scene_envelope=scene,
            session=session,
            world=world,
            resolution=resolution,
        )

    normalized_clues = [normalize_clue_record(c) for c in discoverable_raw]
    runtime_for_scene = scene_runtime or {}
    discovered_texts = {s for s in runtime_for_scene.get("discovered_clues", []) if isinstance(s, str)}
    discovered = [c for c in normalized_clues if c["text"] in discovered_texts]
    undiscovered = [c for c in normalized_clues if c["text"] not in discovered_texts]

    def _with_presentation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for rec in records:
            cid = str(rec.get("id") or "").strip() or None
            txt = str(rec.get("text") or "").strip() or None
            presentation = get_clue_presentation(session, clue_id=cid, clue_text=txt, default="implicit")
            enriched = dict(rec)
            enriched["presentation"] = presentation
            enriched["actionable"] = presentation == "actionable"
            out.append(enriched)
        return out

    discovered = _with_presentation(discovered)
    undiscovered = _with_presentation(undiscovered)
    response_mode = session.get("response_mode", "standard")
    mode_instructions = {
        "terse": "Narration mode: terse. Use short, minimal sentences focused on clear outcomes.",
        "standard": "Narration mode: standard. Use 1-4 concise paragraphs with a balance of description and pacing.",
        "vivid": "Narration mode: vivid. Emphasize sensory detail and mood while staying within 1-4 paragraphs.",
        "tactical": "Narration mode: tactical. Emphasize positions, options, risks, and consequences in the scene.",
        "investigative": "Narration mode: investigative. Emphasize clues, leads, and what careful observation reveals.",
    }
    mode_instruction = mode_instructions.get(response_mode, mode_instructions["standard"])

    def _build_world_state_prompt_view(w: Dict[str, Any]) -> Dict[str, Any]:
        ws = w.get("world_state") or {}
        if not isinstance(ws, dict):
            return {"flags": {}, "counters": {}, "clocks_summary": []}
        flags = {k: v for k, v in (ws.get("flags") or {}).items() if isinstance(k, str) and not k.startswith("_")}
        counters = {k: v for k, v in (ws.get("counters") or {}).items() if isinstance(k, str) and not k.startswith("_")}
        from game.schema_contracts import world_clock_row_summary_line

        clocks_raw = ws.get("clocks") or {}
        clocks_summary: List[str] = []
        for k, c in clocks_raw.items():
            if not isinstance(k, str) or k.startswith("_") or not isinstance(c, dict):
                continue
            seg = world_clock_row_summary_line(k, c)
            if seg:
                clocks_summary.append(seg)
        return {"flags": flags, "counters": counters, "clocks_summary": clocks_summary}

    world_state_view = _build_world_state_prompt_view(world)
    return {
        "campaign": campaign,
        "world": world,
        "session": session,
        "character": character,
        "scene": scene,
        "combat": combat,
        "recent_log": recent_log,
        "user_text": user_text,
        "resolution": resolution,
        "scene_runtime": scene_runtime,
        "public_scene": public_scene,
        "discoverable_clues": [c["text"] for c in undiscovered] if allow_disc else [],
        "gm_only_hidden_facts": hidden,
        "gm_only_discoverable_locked": [c["text"] for c in undiscovered] if not allow_disc else [],
        "discovered_clue_records": discovered,
        "undiscovered_clue_records": undiscovered,
        "pending_leads": filter_pending_leads_for_active_follow_surface(
            session, list(runtime_for_scene.get("pending_leads") or [])
        ),
        "intent": intent,
        "world_state_view": world_state_view,
        "mode_instruction": mode_instruction,
        "recent_log_for_prompt": recent_log_for_prompt,
        "uncertainty_hint": uncertainty_hint,
        "prompt_profile": prompt_profile,
        "known_answer_hint": known_answer_hint,
    }


def _provider_response_contract_from_payload(payload: Dict[str, Any]) -> str:
    """Select model-facing envelope from existing decision projection only."""
    try:
        from game.gm_resolution_decision import (
            PROVIDER_ENVELOPE_NARRATION_ONLY,
            select_provider_response_envelope,
        )
    except Exception:
        return "structured_realization"
    decision = payload.get("gm_resolution_decision") if isinstance(payload.get("gm_resolution_decision"), dict) else None
    contract = payload.get("resolution_contract") if isinstance(payload.get("resolution_contract"), dict) else None
    selected = select_provider_response_envelope(decision, contract)
    envelope = str(selected.get("selected_envelope") or "")
    return PROVIDER_ENVELOPE_NARRATION_ONLY if envelope == PROVIDER_ENVELOPE_NARRATION_ONLY else "structured_realization"


def _provider_response_contract_from_messages(messages: List[Dict[str, str]] | None) -> str:
    if not isinstance(messages, list) or not messages:
        return "structured_realization"
    system = str((messages[0] or {}).get("content") or "")
    return "narration_only" if NARRATION_ONLY_RESPONSE_CONTRACT in system else "structured_realization"


# Top-level provider fields that mirror a response_policy child. The smaller
# interaction_continuity snapshot is intentionally absent: it is not equal to
# response_policy.interaction_continuity.
EXACT_PROVIDER_CONTRACT_MIRRORS: Tuple[Tuple[str, str], ...] = (
    ("anti_railroading_contract", "anti_railroading"),
    ("context_separation_contract", "context_separation"),
    ("player_facing_narration_purity_contract", "player_facing_narration_purity"),
    ("social_response_structure_contract", "social_response_structure"),
    ("interaction_continuity_contract", "interaction_continuity"),
    ("fallback_behavior", "fallback_behavior"),
    ("conversational_memory_window", "conversational_memory_window"),
)


def _json_value_equal(left: Any, right: Any) -> bool:
    try:
        return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(
            right, ensure_ascii=False, sort_keys=True
        )
    except (TypeError, ValueError):
        return False


_PROVIDER_CALL_STAMP: ContextVar[dict | None] = ContextVar("ashen_provider_call_stamp", default=None)


def provider_timeout_seconds() -> float:
    """Bound a single provider wait. The SDK default is several minutes."""
    raw = os.environ.get("ASHEN_PROVIDER_TIMEOUT_SECONDS", "45")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 45.0
    return min(120.0, max(5.0, value))


def omit_duplicate_turn_packet_policy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Drop provider-payload packet fields already present on the root policy.

    Gate and retry code keep their own packet. This projection is serialized
    to the model only. Unequal policy is retained. The input mapping is not mutated.
    """
    if not isinstance(payload, dict):
        return payload
    policy = payload.get("response_policy")
    packet = payload.get("turn_packet")
    if not isinstance(policy, dict) or not isinstance(packet, dict):
        return payload
    nested = packet.get("response_policy")
    contracts = packet.get("contracts")
    drop_policy = isinstance(nested, dict) and bool(nested) and all(
        key in policy and _json_value_equal(nested.get(key), policy.get(key)) for key in nested
    )
    kept_contracts = contracts
    if isinstance(contracts, dict):
        kept_contracts = {
            key: value
            for key, value in contracts.items()
            if not (key in policy and _json_value_equal(value, policy.get(key)))
        }
    contracts_changed = isinstance(contracts, dict) and kept_contracts != contracts
    if not drop_policy and not contracts_changed:
        return payload
    projected = dict(payload)
    packet_copy = dict(packet)
    if drop_policy:
        packet_copy.pop("response_policy", None)
    if contracts_changed:
        packet_copy["contracts"] = kept_contracts
    projected["turn_packet"] = packet_copy
    return projected


def omit_exact_duplicate_provider_contracts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Omit top-level provider copies that are JSON-equal to a response_policy child.

    The policy child stays in the serialized payload. Unequal values are retained.
    The input mapping is not mutated, and no diagnostic field is added.
    """
    if not isinstance(payload, dict):
        return payload
    policy = payload.get("response_policy")
    if not isinstance(policy, dict):
        return payload
    removable: List[str] = []
    for top_key, policy_key in EXACT_PROVIDER_CONTRACT_MIRRORS:
        if top_key not in payload or policy_key not in policy:
            continue
        if _json_value_equal(payload.get(top_key), policy.get(policy_key)):
            removable.append(top_key)
    if not removable:
        return payload
    projected = dict(payload)
    for top_key in removable:
        projected.pop(top_key, None)
    return projected


def _dedupe_provider_payload_instructions(payload: Dict[str, Any], system_prompt: str) -> Dict[str, Any]:
    """Remove provider-payload instruction lines already carried verbatim by system prompt."""
    instructions = payload.get("instructions")
    if not isinstance(instructions, list) or not isinstance(system_prompt, str) or not system_prompt:
        return payload
    deduped: List[Any] = []
    removed: List[str] = []
    for item in instructions:
        if isinstance(item, str) and item.strip() and item in system_prompt:
            removed.append(item)
            continue
        deduped.append(item)
    if not removed:
        return payload
    payload = dict(payload)
    payload["instructions"] = deduped
    prompt_debug = payload.get("prompt_debug")
    if isinstance(prompt_debug, dict):
        payload["prompt_debug"] = {
            **prompt_debug,
            "provider_instruction_deduplication": {
                "mode": "exact_system_substring",
                "removed_count": len(removed),
                "removed_sha256": [_sha256_text(text) for text in removed],
            },
        }
    return payload


def _social_projection_nonempty(value: Any) -> bool:
    if value in (None, "", [], {}):
        return False
    if isinstance(value, dict):
        return any(_social_projection_nonempty(v) for v in value.values())
    if isinstance(value, list):
        return any(_social_projection_nonempty(v) for v in value)
    return True


def _social_projection_empty_combat(value: Any) -> bool:
    if value in (None, {}, []):
        return True
    if not isinstance(value, dict):
        return False
    return not any(_social_projection_nonempty(v) for v in value.values())


def _compact_social_turn_packet(packet: Any) -> Dict[str, Any] | None:
    if not isinstance(packet, dict):
        return None
    out: Dict[str, Any] = {}
    for key in (
        "version",
        "turn_id",
        "scene_id",
        "player_text",
        "resolution_kind",
        "route",
        "continuity",
        "contracts",
        "fallback",
        "referent_tracking_compact",
    ):
        if key in packet:
            out[key] = copy.deepcopy(packet.get(key))
    return out or None


def _compact_social_mechanical_resolution(resolution: Any) -> Dict[str, Any] | None:
    if not isinstance(resolution, dict):
        return None
    out: Dict[str, Any] = {}
    for key in (
        "kind",
        "action_id",
        "label",
        "prompt",
        "success",
        "resolved_transition",
        "target_scene_id",
        "clue_id",
        "discovered_clues",
        "world_updates",
        "state_changes",
        "social",
    ):
        if key in resolution:
            out[key] = copy.deepcopy(resolution.get(key))
    metadata = resolution.get("metadata")
    if isinstance(metadata, dict):
        compact_meta: Dict[str, Any] = {}
        for key in (
            "selected_resolver",
            "active_interaction_target_id",
            "ordinary_contract_established",
            "semantic_owner",
            "response_type_contract",
            "interaction_obligation",
            "social_turn_contract",
        ):
            if key in metadata:
                compact_meta[key] = copy.deepcopy(metadata.get(key))
        if compact_meta:
            out["metadata"] = compact_meta
    return out or None


def _compact_social_narrative_plan(plan: Any) -> Dict[str, Any] | None:
    if not isinstance(plan, dict):
        return None
    out: Dict[str, Any] = {}
    for key in (
        "version",
        "narrative_mode",
        "role_allocation",
        "scene_anchors",
        "active_pressures",
        "allowable_entity_references",
        "narrative_mode_contract",
    ):
        if key in plan:
            out[key] = copy.deepcopy(plan.get(key))
    answer_plan = plan.get("answer_exposition_plan")
    if isinstance(answer_plan, dict):
        out["answer_exposition_plan"] = copy.deepcopy(answer_plan)
    return out or None


def _project_harmless_social_provider_context(
    payload: Dict[str, Any],
    *,
    provider_response_contract: str,
) -> Dict[str, Any]:
    """Narrow provider-context projection for harmless incidental NPC dialogue.

    The resolver, authoritative decision, validators, and state are unchanged. This only
    trims model-facing scaffolding after the ordinary social/narration-only envelope is
    already selected.
    """
    if not isinstance(payload, dict):
        return payload
    if provider_response_contract != "narration_only":
        return payload

    recipe = payload.get("decision_facing_answer_recipe")
    turn_operation = recipe.get("turn_operation") if isinstance(recipe, dict) else None
    decision = payload.get("gm_resolution_decision")
    contract = payload.get("resolution_contract")
    response_policy = payload.get("response_policy")
    speaker_selection = payload.get("speaker_selection")
    active_interlocutor = payload.get("active_interlocutor")
    dialogue_plan = payload.get("dialogue_social_plan")
    scene = payload.get("scene")
    permitted_inference = recipe.get("permitted_inference") if isinstance(recipe, dict) else None
    combat = payload.get("combat")
    mechanical = payload.get("mechanical_resolution")
    metadata = mechanical.get("metadata") if isinstance(mechanical, dict) else None
    social = mechanical.get("social") if isinstance(mechanical, dict) else None

    if not (
        isinstance(recipe, dict)
        and isinstance(turn_operation, dict)
        and turn_operation.get("response_operation") == "incidental_dialogue"
        and turn_operation.get("declaration_expectation") == "reply_not_required"
        and isinstance(decision, dict)
        and decision.get("permitted_state_mutations") == []
        and decision.get("unresolved_qualifiers") == []
        and not recipe.get("unresolved_content")
        and isinstance(permitted_inference, dict)
        and permitted_inference.get("allowed") is False
        and isinstance(contract, dict)
        and str(contract.get("operation") or "").strip().lower() == "ask"
        and str(contract.get("target") or "").strip()
        and isinstance(response_policy, dict)
        and isinstance(scene, dict)
        and isinstance(dialogue_plan, dict)
        and isinstance(speaker_selection, dict)
        and isinstance(speaker_selection.get("allowed_speaker_ids"), list)
        and len(speaker_selection["allowed_speaker_ids"]) == 1
        and isinstance(active_interlocutor, dict)
        and str(active_interlocutor.get("npc_id") or "").strip()
        and speaker_selection["allowed_speaker_ids"] == [active_interlocutor["npc_id"]]
        and speaker_selection.get("primary_speaker_id") == active_interlocutor["npc_id"]
        and contract.get("interlocutor") == active_interlocutor["npc_id"]
        and isinstance(metadata, dict)
        and metadata.get("selected_resolver") == "social"
        and metadata.get("ordinary_contract_established") is True
        and isinstance(social, dict)
        and social.get("npc_id") == active_interlocutor["npc_id"]
        and social.get("target_resolved") is True
        and social.get("reply_plan_kind") == "harmless_subjective_response_permitted"
        and social.get("incidental_subjective_allowed") is True
        and social.get("objective_world_fact_authority") == "none"
        and social.get("npc_speech_authority") == "claim_only"
        and social.get("durable_state_mutation_allowed") is False
        and not social.get("topic_revealed")
        and not social.get("skill_check")
        and mechanical.get("requires_check") is False
        and not mechanical.get("state_changes")
        and not mechanical.get("world_updates")
        and not mechanical.get("discovered_clues")
        and not mechanical.get("resolved_transition")
        and isinstance(combat, dict)
        and combat.get("in_combat") is False
    ):
        return payload

    # Missing or contradictory authority metadata always keeps the full context.
    opening = payload.get("opening_narration_obligations")
    advancement = payload.get("scene_advancement")
    if (
        not isinstance(opening, dict)
        or opening.get("opening_mode") is not False
        or not isinstance(advancement, dict)
        or any(advancement.values())
    ):
        return payload

    omitted: List[str] = []
    compacted: List[str] = []
    projected = dict(payload)

    for key in (
        "opening_narration_obligations",
        "opening_scene_realization",
        "opening_inputs_are_curated",
        "opening_selector_source_used",
        "opening_selector_selected_facts",
        "opening_curated_facts",
        "opening_fact_telemetry",
        "transition",
        "scene_advancement",
        "world_progression_summary",
    ):
        if key in projected:
            projected.pop(key, None)
            omitted.append(key)

    if _social_projection_empty_combat(projected.get("combat")):
        projected.pop("combat", None)
        omitted.append("combat")

    for key in ("lead_context", "interlocutor_lead_context", "interlocutor_lead_behavior_hints"):
        if key in projected and not _social_projection_nonempty(projected.get(key)):
            projected.pop(key, None)
            omitted.append(key)

    compact_turn_packet = _compact_social_turn_packet(projected.get("turn_packet"))
    if compact_turn_packet is not None:
        projected["turn_packet"] = compact_turn_packet
        compacted.append("turn_packet")

    compact_mechanical = _compact_social_mechanical_resolution(projected.get("mechanical_resolution"))
    if compact_mechanical is not None:
        projected["mechanical_resolution"] = compact_mechanical
        compacted.append("mechanical_resolution")

    compact_plan = _compact_social_narrative_plan(projected.get("narrative_plan"))
    if compact_plan is not None:
        projected["narrative_plan"] = compact_plan
        compacted.append("narrative_plan")

    projected["provider_context_projection"] = {
        "mode": "harmless_social_incidental_dialogue_v1",
        "selected": True,
        "reason": "ordinary social ask uses narration-only incidental_dialogue with one grounded addressee and no authorized state mutation",
        "retained_authority_surfaces": [
            "player_input",
            "scene",
            "active_interlocutor",
            "dialogue_social_plan",
            "speaker_selection",
            "selected_conversational_memory",
            "recent_log",
            "response_policy",
            "resolution_contract",
            "gm_resolution_decision",
            "decision_facing_answer_recipe",
            "narration_visibility",
        ],
        "omitted_sections": sorted(dict.fromkeys(omitted)),
        "compacted_sections": sorted(dict.fromkeys(compacted)),
    }
    return projected


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_messages(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None = None,
    scene_runtime: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
    narration_context_call_kwargs: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    """When *narration_context_call_kwargs* is set, use it as the single prelude for ``build_narration_context`` (API/bundle seam)."""
    if narration_context_call_kwargs is not None:
        nc_kwargs = dict(narration_context_call_kwargs)
    else:
        nc_kwargs = collect_narration_context_call_kwargs(
            campaign,
            world,
            session,
            character,
            scene,
            combat,
            recent_log,
            user_text,
            resolution=resolution,
            scene_runtime=scene_runtime,
            prompt_profile=prompt_profile,
        )
    known_answer_hint = nc_kwargs.pop("known_answer_hint", None)
    public_scene = nc_kwargs["public_scene"]
    intent = nc_kwargs["intent"]
    runtime_for_scene = nc_kwargs.get("scene_runtime") or {}
    social_authority = _session_social_authority(session)
    payload = build_narration_context(**nc_kwargs)

    # C1-D prompt projection: for CTIR-backed social turns, forward only structural
    # dialogue/social plan fields to the model (no validator/version/applies scaffolding).
    dsp = payload.get("dialogue_social_plan")
    # Preserve the full shipped plan for downstream deterministic validation (final-emission gate).
    # This is trace-only; do not mutate or infer missing fields here.
    if isinstance(resolution, dict) and isinstance(dsp, dict):
        md = resolution.setdefault("metadata", {})
        em = md.setdefault("emission_debug", {})
        if "dialogue_social_plan" not in em:
            em["dialogue_social_plan"] = dict(dsp)
    if social_authority and isinstance(dsp, dict):
        allowed_keys = (
            "speaker_id",
            "speaker_name",
            "speaker_source",
            "dialogue_intent",
            "reply_kind",
            "pressure_state",
            "relationship_codes",
            "tone_bounds",
            "prohibited_content_codes",
            "derivation_codes",
            "allowed_pregate_speaker_labels",
            "writer_attribution_label",
            "speaker_alias_resolution_source",
        )
        payload["dialogue_social_plan"] = {k: dsp.get(k) for k in allowed_keys if k in dsp}
    if isinstance(resolution, dict):
        sac = payload.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            md = resolution.setdefault("metadata", {})
            em = md.setdefault("emission_debug", {})
            em["scene_state_anchor"] = {
                "enabled": sac.get("enabled"),
                "scene_id": sac.get("scene_id"),
                "counts": {
                    "location": len(sac.get("location_tokens") or []),
                    "actor": len(sac.get("actor_tokens") or []),
                    "player_action": len(sac.get("player_action_tokens") or []),
                },
            }
        csep = payload.get("context_separation_contract")
        if isinstance(csep, dict):
            md = resolution.setdefault("metadata", {})
            em = md.setdefault("emission_debug", {})
            _cdf = csep.get("debug_flags")
            if not isinstance(_cdf, dict):
                _cdf = {}
            em["context_separation"] = {
                "enabled": csep.get("enabled"),
                "interaction_kind": csep.get("interaction_kind"),
                "pressure_focus_allowed": _cdf.get("pressure_focus_allowed"),
                "debug_reason": csep.get("debug_reason"),
            }
        cmw = payload.get("conversational_memory_window")
        if isinstance(cmw, dict):
            md = resolution.setdefault("metadata", {})
            em = md.setdefault("emission_debug", {})
            em["conversational_memory_window"] = dict(cmw)
            scm = payload.get("selected_conversational_memory")
            if isinstance(scm, list):
                em["selected_conversational_memory"] = list(scm)
            pdbg = payload.get("prompt_debug")
            if isinstance(pdbg, dict) and isinstance(pdbg.get("conversational_memory"), dict):
                em["conversational_memory"] = dict(pdbg["conversational_memory"])
            elif isinstance(scm, list):
                # Model-facing narration payloads omit ``prompt_debug``; preserve a minimal mirror.
                em["conversational_memory"] = {"selected_count": len(scm)}
        _soc_esc = (resolution.get("social") or {}).get("social_escalation")
        if isinstance(_soc_esc, dict) and int(_soc_esc.get("escalation_level") or 0) >= 2:
            payload["instructions"] = list(payload.get("instructions", [])) + [
                _social_escalation_prompt_instruction(_soc_esc),
            ]
    passive_streak = int(runtime_for_scene.get("passive_action_streak", 0) or 0)
    passive_pause = "passive_pause" in [str(label).strip().lower() for label in intent.get("labels", []) if isinstance(label, str)]
    visible_low = " ".join(str(v).lower() for v in public_scene.get("visible_facts", []) if isinstance(v, str))
    active_runtime_pending = filter_pending_leads_for_active_follow_surface(
        session, list(runtime_for_scene.get("pending_leads") or [])
    )
    passive_scene_pressure_due = (
        not social_authority
        and passive_pause
        and (
            passive_streak >= 2
            or bool(active_runtime_pending)
            or bool(runtime_for_scene.get("recent_contextual_leads"))
            or ("guard" in visible_low)
            or ("watch" in visible_low)
            or ("missing patrol" in visible_low)
            or ("rumor" in visible_low)
            or ("rumour" in visible_low)
        )
    )
    if passive_scene_pressure_due:
        payload["passive_scene_pressure"] = {
            "current_action_is_passive": True,
            "passive_action_streak": passive_streak,
            "recent_player_actions": list(runtime_for_scene.get("recent_player_actions") or []),
        }
        payload["instructions"] = list(payload.get("instructions", [])) + [
            "The player is pausing or holding position. Realize the currently visible scene.",
            "Do not invent a person, confrontation, whispered hook, inscription, clue, or route that is not already in the provided scene evidence.",
        ]
    if known_answer_hint:
        payload["known_answer_hint"] = known_answer_hint
        payload["instructions"] = list(payload.get("instructions", [])) + [
            "If known_answer_hint is present, answer with that established fact directly in the first sentence. Do not reroute known scene facts into uncertainty.",
        ]
    known_clues = get_known_clues_with_presentation(session)
    payload["clues"] = {
        "known": known_clues,
        "implicit": [c for c in known_clues if c.get("presentation") == "implicit"],
        "explicit": [c for c in known_clues if c.get("presentation") == "explicit"],
        "actionable": [c for c in known_clues if c.get("presentation") == "actionable"],
    }

    # Action-outcome mode: prompt_context ships plan-owned ``mechanical_resolution.action_outcome`` and
    # intentionally blocks raw prose-like resolution scaffolding (hint/prompt/label) from becoming a narration bypass.
    # Keep GM-side convenience hints for continuation mode, but do not forward them into the model payload here.
    action_outcome_mode = False
    mech = payload.get("mechanical_resolution")
    if isinstance(mech, dict) and "action_outcome" in mech:
        action_outcome_mode = True
    else:
        np = payload.get("narrative_plan")
        if isinstance(np, dict) and str(np.get("narrative_mode") or "").strip().lower() == "action_outcome":
            action_outcome_mode = True

    # Add resolved exploration context when the app has already determined the action.
    if not action_outcome_mode and resolution and isinstance(resolution, dict):
        res_kind = resolution.get('kind')
        if res_kind and res_kind in EXPLORATION_KINDS:
            resolved_action = {
                'id': resolution.get('action_id'),
                'label': resolution.get('label'),
                'type': res_kind,
                'prompt': resolution.get('prompt'),
                'target_scene_id': resolution.get('target_scene_id'),
            }
            scene_transition_already_occurred = bool(resolution.get('resolved_transition'))
            payload['resolved_exploration_action'] = resolved_action
            payload['resolution_kind'] = res_kind
            payload['resolution_summary'] = (
                f"Scene transition to {resolution.get('target_scene_id')} completed."
                if scene_transition_already_occurred
                else f"{res_kind.replace('_', ' ').title()} in current scene."
            )
            payload['scene_transition_already_occurred'] = scene_transition_already_occurred
            if resolution.get('originating_scene_id'):
                payload['originating_scene_id'] = resolution['originating_scene_id']

            # Compact hint when player has repeated the same action.
            rep_count = runtime_for_scene.get('repeated_action_count', 0) or 0
            if rep_count > 1:
                payload['action_repetition_hint'] = f"Same action repeated {rep_count} times in this scene; vary the outcome."

            # Exploration-specific instructions when action was resolved by the app.
            instructions_add = [
                'If resolved_exploration_action is present: narrate the outcome of that resolved action; do not restate the previous scene.',
                'If scene_transition_already_occurred: the current scene is the destination; narrate arrival and what the player sees there; do not override with activate_scene_id or new_scene_draft.',
                'For observe/investigate/interact: reveal new information, consequence, tension, or a narrower decision; avoid generic filler unless paired with a concrete lead, obstacle, cost, or pressure.',
                'Never repeat the same observation twice in a row for the same scene and action.',
            ]
            if resolution.get('skill_check'):
                payload['skill_check'] = resolution['skill_check']
                instructions_add.append(
                    'The skill check was already resolved by the app (roll, modifier, total, dc, success in mechanical_resolution.skill_check). '
                    'Do not invent dice results or roll outcomes; narrate the authoritative result given.'
                )
            payload['instructions'] = list(payload.get('instructions', [])) + instructions_add
        elif res_kind and res_kind in COMBAT_KINDS:
            payload['resolved_combat_action'] = {
                'kind': res_kind,
                'action_id': resolution.get('action_id'),
                'label': resolution.get('label'),
                'prompt': resolution.get('prompt'),
                'success': resolution.get('success'),
                'combat': resolution.get('combat'),
            }
            payload['resolution_kind'] = res_kind
            payload['resolution_summary'] = f"Combat action: {res_kind.replace('_', ' ').title()}"
            payload['instructions'] = list(payload.get('instructions', [])) + [
                'The mechanical_resolution contains resolved_combat_action with authoritative dice rolls and outcomes. '
                'Narrate the combat outcome based on the resolved result; do not invent dice rolls or override app-side resolutions.',
            ]
        else:
            # Social or other: pass skill_check when present; GPT must only narrate, never decide success/failure
            if resolution.get('skill_check'):
                from game.social import SOCIAL_KINDS
                if res_kind and res_kind in SOCIAL_KINDS:
                    payload['skill_check'] = resolution['skill_check']
                    payload['instructions'] = list(payload.get('instructions', [])) + [
                        'The skill check was already resolved by the app (skill, roll, modifier, total, difficulty, success). '
                        'NEVER decide success or failure yourself. ONLY narrate the authoritative result given.',
                    ]

    if not action_outcome_mode and resolution and isinstance(resolution, dict) and resolution.get('hint'):
        payload['instructions'] = list(payload['instructions']) + [resolution['hint']]
    provider_response_contract = _provider_response_contract_from_payload(payload)
    system_prompt = NARRATION_ONLY_SYSTEM_PROMPT if provider_response_contract == "narration_only" else SYSTEM_PROMPT
    payload = _dedupe_provider_payload_instructions(payload, system_prompt)
    payload = _project_harmless_social_provider_context(
        payload,
        provider_response_contract=provider_response_contract,
    )
    payload = omit_exact_duplicate_provider_contracts(payload)
    payload = omit_duplicate_turn_packet_policy(payload)
    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
    ]


def _status_code_from_upstream_error(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status
    return None


def _error_code_from_upstream_error(exc: Exception) -> str | None:
    for attr in ("code", "error_code"):
        raw = getattr(exc, attr, None)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            raw = err.get("code")
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
    return None


def _classify_upstream_gpt_error(exc: Exception) -> Dict[str, Any]:
    class_name = type(exc).__name__.lower()
    message = str(exc or "").strip()
    message_low = message.lower()
    status_code = _status_code_from_upstream_error(exc)
    error_code = _error_code_from_upstream_error(exc)
    error_code_low = str(error_code or "").strip().lower()

    failure_class = "unknown_api_error"
    retryable = False

    # Hard client / account / model failures: never treat as content-quality retry candidates.
    _nonretry_error_codes = {
        "insufficient_quota",
        "invalid_api_key",
        "invalid_api_key_provided",
        "account_deactivated",
        "billing_not_active",
        "billing_hard_limit_reached",
        "model_not_found",
        "model_removed",
        "model_not_available",
        "invalid_model",
        "unsupported_model",
        "unsupported_value",
        "context_length_exceeded",
        "invalid_request_error",
        "content_policy_violation",
    }
    if error_code_low in _nonretry_error_codes:
        failure_class = error_code_low if error_code_low != "invalid_request_error" else "invalid_request"
        retryable = False
        return {
            "failure_class": failure_class,
            "retryable": retryable,
            "status_code": status_code,
            "error_code": error_code,
            "message_excerpt": message[:240],
        }

    if "insufficient_quota" in message_low or error_code_low == "insufficient_quota":
        failure_class = "insufficient_quota"
        retryable = False
    elif any(
        phrase in message_low
        for phrase in (
            "incorrect api key",
            "invalid api key",
            "invalid authentication",
            "authenticationerror",
            "api key provided",
        )
    ):
        failure_class = "invalid_api_key"
        retryable = False
    elif any(
        phrase in message_low
        for phrase in (
            "does not exist or you do not have access",
            "model not found",
            "unknown model",
            "unsupported model",
            "invalid model",
            "no such model",
        )
    ) or ("model" in message_low and "does not exist" in message_low):
        failure_class = "model_not_found"
        retryable = False
    elif status_code == 429:
        failure_class = "rate_limit"
        retryable = True
    elif status_code in (400, 404, 409, 413, 414, 415, 422):
        failure_class = "invalid_request"
        retryable = False
    elif status_code in (401, 403):
        failure_class = "auth_failure"
        retryable = False
    elif status_code is not None and status_code >= 500:
        failure_class = "server_error"
        retryable = True
    elif "timeout" in class_name or "timeout" in message_low:
        failure_class = "timeout"
        retryable = True
    elif "connection" in class_name or "connect" in message_low:
        failure_class = "connection_error"
        retryable = True
    elif "ratelimit" in class_name or "rate limit" in message_low:
        failure_class = "rate_limit"
        retryable = "insufficient_quota" not in message_low
    elif "authentication" in class_name or "permission" in class_name:
        failure_class = "auth_failure"
        retryable = False

    return {
        "failure_class": failure_class,
        "retryable": retryable,
        "status_code": status_code,
        "error_code": error_code,
        "message_excerpt": message[:240],
    }


def _attach_model_route_metadata(
    gm: Dict[str, Any],
    *,
    selected_model: str,
    route_reason: str,
    route_family: str,
    purpose: str,
    retry_attempt: int,
    retry_reason: str | None = None,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> Dict[str, Any]:
    normalized_purpose = str(purpose or "primary_turn").strip() or "primary_turn"
    normalized_retry_reason = str(retry_reason or "").strip()
    escalation_trigger = _resolve_model_escalation_trigger(
        purpose=normalized_purpose,
        retry_attempt=retry_attempt,
        retry_reason=normalized_retry_reason or None,
        strict_social=strict_social,
        force_high_precision=force_high_precision,
    )
    escalated = escalation_trigger is not None
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    stamp = _PROVIDER_CALL_STAMP.get()
    provider_call = None
    if isinstance(stamp, dict):
        provider_call = {
            "purpose": stamp.get("purpose"),
            "sent": bool(stamp.get("sent")),
            "latency_ms": stamp.get("latency_ms"),
            "input_tokens": stamp.get("input_tokens"),
            "output_tokens": stamp.get("output_tokens"),
        }
    gm["metadata"] = {
        **md,
        "selected_model": selected_model,
        "model_route_reason": route_reason,
        "model_route_family": route_family,
        "model_route_purpose": normalized_purpose,
        "model_retry_attempt": int(retry_attempt or 0),
        "model_escalated": escalated,
        "model_escalation_trigger": escalation_trigger,
        **({"provider_call": provider_call} if provider_call is not None else {}),
    }
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    token = f"model_route:{route_family}:{route_reason}:{selected_model}"
    gm["debug_notes"] = (dbg + " | " if dbg else "") + token
    if escalated and escalation_trigger:
        gm["debug_notes"] += f" | model_escalated:{escalation_trigger}"
    return gm


def _resolve_model_escalation_trigger(
    *,
    purpose: str,
    retry_attempt: int,
    retry_reason: str | None = None,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> str | None:
    normalized_purpose = str(purpose or "primary_turn").strip() or "primary_turn"
    normalized_retry_reason = str(retry_reason or "").strip()
    if force_high_precision:
        return "force_high_precision"
    if strict_social or normalized_purpose == "strict_social":
        return "strict_social"
    if normalized_purpose != "retry_escalation":
        return None
    if normalized_retry_reason in {
        "unresolved_question",
        "npc_contract_failure",
        "validator_voice",
        "followup_soft_repetition",
        "echo_or_repetition",
    }:
        return f"retry_reason:{normalized_retry_reason}"
    if int(retry_attempt or 0) >= 1:
        return "retry_attempt"
    return None


def _log_model_route(
    *,
    selected_model: str,
    route_family: str,
    purpose: str,
    retry_attempt: int,
    retry_reason: str | None = None,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> None:
    normalized_purpose = str(purpose or "primary_turn").strip() or "primary_turn"
    escalation_trigger = _resolve_model_escalation_trigger(
        purpose=normalized_purpose,
        retry_attempt=retry_attempt,
        retry_reason=retry_reason,
        strict_social=strict_social,
        force_high_precision=force_high_precision,
    )
    escalated = "true" if escalation_trigger is not None else "false"
    print(
        f"[MODEL ROUTE] purpose={normalized_purpose} "
        f"selected={selected_model} "
        f"family={route_family} "
        f"retry={int(retry_attempt or 0)} "
        f"escalated={escalated}"
    )


def call_gpt(
    messages: List[Dict[str, str]],
    *,
    purpose: str = "primary_turn",
    response_policy: Optional[Dict[str, Any]] = None,
    segmented_turn: Optional[Dict[str, Any]] = None,
    retry_attempt: int = 0,
    retry_reason: Optional[str] = None,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> Dict[str, Any]:
    # Wrap the OpenAI call so network/API/model errors do not crash gameplay.
    route = resolve_model_route(
        purpose=purpose,
        response_policy=response_policy,
        segmented_turn=segmented_turn,
        retry_attempt=retry_attempt,
        strict_social=strict_social,
        force_high_precision=force_high_precision,
    )
    from game.provider_budget import (
        accounting_active,
        begin_request,
        finish_request,
        provider_retries_disabled,
    )

    if provider_retries_disabled() and int(retry_attempt or 0) > 0:
        return _attach_model_route_metadata(
            {
                "player_facing_text": (
                    "The action stands, and no further narration request was sent."
                ),
                "tags": ["provider_retry_disabled", "deterministic_fallback"],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "provider_retry_disabled",
                "metadata": {"provider_retry_disabled": True},
            },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    if os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS", "").strip().lower() in {"1", "true", "yes", "on"}:
        metadata = {
            "provider_calls_disabled": True,
            "provider_accounting": {
                "model": route.selected_model,
                "request_count": 0,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": None,
                "usage_unavailable": True,
            },
        }
        return _attach_model_route_metadata({
            "player_facing_text": (
                "Provider calls are disabled for this run, so no live narration was generated."
            ),
            "tags": ["provider_calls_disabled", "deterministic_fallback"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": f"provider_calls_disabled:purpose={purpose}",
            "metadata": metadata,
        },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    _PROVIDER_CALL_STAMP.set(
        {
            "purpose": str(purpose or "primary_turn"),
            "sent": False,
            "latency_ms": None,
            "input_tokens": None,
            "output_tokens": None,
            "started": time.perf_counter(),
        }
    )
    pinned_model = os.environ.get("ASHEN_PIN_PROVIDER_MODEL", "").strip()
    selected_model = pinned_model or route.selected_model
    narration_cap = int(os.environ.get("ASHEN_NARRATION_MAX_OUTPUT_TOKENS", "600") or "600")
    if accounting_active():
        blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
        estimated_input = max(1, (len(blob) // 3) + 64)
        refusal = begin_request(purpose=purpose or "narration", estimated_input=estimated_input, max_output=narration_cap)
        if refusal:
            finish_request(
                {
                    "purpose": purpose or "narration",
                    "sent": False,
                    "model": selected_model,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "refusal": refusal,
                }
            )
            return _attach_model_route_metadata(
                {
                    "player_facing_text": (
                        "The action was resolved, but live narration was not requested because it would exceed the provider budget."
                    ),
                    "tags": ["provider_budget_refused", "deterministic_fallback"],
                    "scene_update": None,
                    "activate_scene_id": None,
                    "new_scene_draft": None,
                    "world_updates": None,
                    "suggested_action": None,
                    "debug_notes": f"provider_budget_refused:{refusal}",
                    "metadata": {"provider_budget_refusal": refusal},
                },
                selected_model=selected_model,
                route_reason=route.route_reason,
                route_family=route.route_family,
                purpose=purpose,
                retry_attempt=retry_attempt,
                retry_reason=retry_reason,
                strict_social=strict_social,
                force_high_precision=force_high_precision,
            )
    request_sent = False
    try:
        from openai import OpenAI
        client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
        _log_model_route(
            selected_model=selected_model,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
        create_kwargs = {"model": selected_model, "input": messages}
        if accounting_active():
            create_kwargs["max_output_tokens"] = narration_cap
        request_sent = True
        stamp = _PROVIDER_CALL_STAMP.get()
        if isinstance(stamp, dict):
            stamp["sent"] = True
            stamp["started"] = time.perf_counter()
        resp = client.responses.create(**create_kwargs)
        if isinstance(stamp, dict):
            stamp["latency_ms"] = max(0, int(round((time.perf_counter() - float(stamp.get("started") or time.perf_counter())) * 1000)))
        text = getattr(resp, 'output_text', None)
        if text is None:
            # Fallback to stringifying the response if expected attribute missing.
            text = str(resp)
        usage = getattr(resp, "usage", None)
        incoming = getattr(usage, "input_tokens", None) if usage is not None else None
        outgoing = getattr(usage, "output_tokens", None) if usage is not None else None
        total = getattr(usage, "total_tokens", None) if usage is not None else None
        if isinstance(stamp, dict):
            stamp["input_tokens"] = None if incoming is None else int(incoming)
            stamp["output_tokens"] = None if outgoing is None else int(outgoing)
        if accounting_active():
            returned_model = str(getattr(resp, "model", "") or "")
            finish_request(
                {
                    "purpose": purpose or "narration",
                    "sent": True,
                    "configured_model": selected_model,
                    "model": returned_model,
                    "request_id": getattr(resp, "id", None),
                    "input_tokens": None if incoming is None else int(incoming),
                    "output_tokens": None if outgoing is None else int(outgoing),
                    "total_tokens": None if total is None else int(total),
                    "max_output_tokens": narration_cap,
                    "model_mismatch": bool(pinned_model and returned_model and not returned_model.startswith(pinned_model)),
                }
            )
        provider_response_contract = _provider_response_contract_from_messages(messages)
        return _attach_model_route_metadata(
            _safe_json(
                text.strip(),
                require_structured_claims=True,
                provider_response_contract=provider_response_contract,
            ),
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    except Exception as e:
        stamp = _PROVIDER_CALL_STAMP.get()
        if isinstance(stamp, dict):
            stamp["sent"] = bool(request_sent)
            started = stamp.get("started")
            if isinstance(started, float):
                stamp["latency_ms"] = max(0, int(round((time.perf_counter() - started) * 1000)))
        if accounting_active() and request_sent:
            finish_request(
                {
                    "purpose": purpose or "narration",
                    "sent": True,
                    "model": selected_model,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "error": type(e).__name__,
                }
            )
        err = _classify_upstream_gpt_error(e)
        # Return a safe fallback response that preserves the expected schema so
        # callers can continue without special-casing exceptions.
        fallback_metadata = {
            'upstream_api_error': err,
        }
        attach_realization_fallback_family(fallback_metadata, GPT_BUDGET_OR_PROVIDER_FAILURE)
        return _attach_model_route_metadata({
            'player_facing_text': 'The game master is temporarily unavailable. Please try again.',
            'tags': [
                'error',
                f"gpt_api_error:{err['failure_class']}",
                'gpt_api_error_retryable' if err['retryable'] else 'gpt_api_error_nonretryable',
            ],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': re.sub(
                r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+",
                "[REDACTED]",
                (
                    f"call_gpt error: {repr(e)} | "
                    f"api_error_class={err['failure_class']}:retryable={err['retryable']}"
                ),
                flags=re.IGNORECASE,
            ),
            'metadata': fallback_metadata,
        },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )


def normalize_scene_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    scene_id = draft.get('id') or slugify(draft.get('location', 'new_scene'))
    return {
        'scene': {
            'id': scene_id,
            'location': draft.get('location', 'Unnamed Scene'),
            'summary': draft.get('summary', ''),
            'mode': draft.get('mode', 'exploration'),
            'visible_facts': draft.get('visible_facts', []),
            'discoverable_clues': draft.get('discoverable_clues', []),
            'hidden_facts': draft.get('hidden_facts', []),
            'exits': draft.get('exits', []),
            'enemies': draft.get('enemies', [])
        }
    }


def _normalize_clue_match_text(s: str) -> str:
    """Lightweight normalization for clue-in-narration matching: lower, trim, collapse whitespace, normalize quotes."""
    if not s or not isinstance(s, str):
        return ""
    t = s.lower().strip()
    t = " ".join(t.split())
    # Normalize common quote/apostrophe variants to ASCII for matching
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return t


def detect_surfaced_clues(player_text: str, scene_envelope: Dict[str, Any]) -> List[str]:
    """Best-effort detection of which discoverable clues appeared in narration."""
    _, discoverable_raw, _ = _scene_layers(scene_envelope)
    if not discoverable_raw:
        return []
    txt_norm = _normalize_clue_match_text(player_text or "")
    found: List[str] = []
    for raw in discoverable_raw:
        rec = normalize_clue_record(raw)
        clue_text = rec["text"]
        if not (clue_text and clue_text.strip()):
            continue
        clue_norm = _normalize_clue_match_text(clue_text)
        if not clue_norm:
            continue
        if clue_norm in txt_norm:
            found.append(clue_text)
    return found


def _scene_momentum_due(session: Dict[str, Any], scene_id: str) -> bool:
    rt = get_scene_runtime(session, scene_id)
    exchanges_since = int(rt.get("momentum_exchanges_since", 0) or 0)
    next_due_in = int(rt.get("momentum_next_due_in", 2) or 2)
    if next_due_in not in (2, 3):
        next_due_in = 2
    due_threshold = max(1, min(2, next_due_in - 1))
    # Hard ceiling: cannot exceed 3 exchanges without momentum.
    if exchanges_since >= 2:
        return True
    return exchanges_since >= due_threshold


def _extract_scene_momentum_kind(gm: Dict[str, Any]) -> str:
    tags = gm.get("tags") if isinstance(gm, dict) else None
    if not isinstance(tags, list):
        return ""
    for t in tags:
        if not isinstance(t, str):
            continue
        s = t.strip()
        if not s.startswith(SCENE_MOMENTUM_TAG_PREFIX):
            continue
        kind = s[len(SCENE_MOMENTUM_TAG_PREFIX):].strip()
        if kind in SCENE_MOMENTUM_KINDS:
            return kind
    return ""



from game.response_policy_enforcement import (
    GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED,
    _apply_diegetic_validator_voice_enforcement,
    _apply_escalate_passive_scene_enforcement,
    _apply_forbid_secret_leak_guard,
    _apply_forbid_state_invention_validation,
    _apply_must_answer_question_resolution_enforcement,
    _apply_prefer_specificity_text_enforcement,
    _apply_scene_momentum_enforcement,
    _apply_topic_pressure_escalation_enforcement,
    _commit_topic_progress,
    _commit_topic_progress_after_enforcement,
    _init_response_policy_enforcement_state,
    _mark_response_policy_enforcement_applied,
    _normalize_response_policy_input,
    _project_fallback_behavior_contract_metadata,
    _scene_id_from_scene_envelope,
    _snapshot_response_policy_and_project_fallback_contract,
    apply_response_policy_enforcement,
    detect_forbidden_generic_phrases,
    detect_validator_voice,
    enforce_forbidden_generic_phrases,
    enforce_no_validator_voice,
    enforce_npc_response_contract,
    enforce_question_resolution_rule,
    npc_response_contract_check,
    guard_gm_output,
    sanitize_player_facing_text,
    enforce_topic_pressure_escalation,
    enforce_scene_momentum,
    escalate_passive_scene,
    validate_gm_state_update,
)

from game.gm_retry import (
    MAX_TARGETED_RETRY_ATTEMPTS,
    RETRY_FAILURE_PRIORITY,
    resolution_is_open_crowd_social,
    _retry_allows_hostile_escalation,
    _FINAL_EMISSION_META_CONTINUITY_KEYS,
    _NONSOCIAL_EMPTY_REPAIR_HARD_LINE,
    _NON_SOCIAL_TERMINAL_FINAL_ROUTES,
    _PLACEHOLDER_LITERAL_PLAYER_TEXT,
    _SOCIAL_EMPTY_REPAIR_HARD_LINE,
    _SOCIAL_EXCLUSIVE_FINAL_ROUTES_FOR_NONSOCIAL_REPAIR,
    _SOCIAL_FORCE_ANSWER_CANDIDATE_KINDS,
    _WEAK_REPAIR_STALL_PHRASES,
    _contextual_nonsocial_repair_line,
    _contextual_social_repair_line,
    _gm_has_usable_player_facing_text,
    _is_placeholder_only_player_facing_text,
    _is_social_continuity_slot_empty,
    _minimal_repair_context,
    _nonsocial_forced_retry_progress_line,
    _nonsocial_minimal_resolution_line,
    _player_facing_text_same_line,
    _preserve_social_continuity_fields,
    _repair_prose_has_weak_stall_wording,
    _stable_u32_from_seed,
    _strip_double_quoted_spans_for_generic_scan,
    _strict_social_speaker_led_opening_for_retry,
    _social_answer_fallback_in_scope,
    apply_deterministic_retry_fallback,
    build_retry_prompt_for_failure,
    choose_retry_strategy,
    detect_retry_failures,
    ensure_minimal_nonsocial_resolution,
    ensure_minimal_social_resolution,
    force_terminal_retry_fallback,
    inspect_retry_social_answer_fallback_scope,
    prioritize_retry_failures_for_social_answer_candidate,
    scene_stall_check,
)
