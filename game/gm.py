from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json
import re
from game.config import MODEL_NAME
from game.utils import slugify
from game.exploration import EXPLORATION_KINDS
from game.social import SOCIAL_KINDS
from game.prompt_context import (
    NO_VALIDATOR_VOICE_RULE,
    RESPONSE_RULE_PRIORITY,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    build_narration_context,
)
from game.storage import (
    load_scene,
    get_scene_runtime,
    SCENE_MOMENTUM_KINDS,
    SCENE_MOMENTUM_TAG_PREFIX,
)
from game.clues import get_clue_presentation, get_known_clues_with_presentation

COMBAT_KINDS = frozenset({
    'initiative', 'attack', 'spell', 'skill_check',
    'enemy_attack', 'enemy_turn_skipped', 'end_turn',
})

SOCIAL_CHECK_KINDS = frozenset({'persuade', 'intimidate', 'deceive', 'barter', 'recruit'})

_STOCK_WARNING_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bbe careful who you trust\b", re.IGNORECASE), "be careful who you trust"),
    (re.compile(r"\bkeep your wits about you\b", re.IGNORECASE), "keep your wits about you"),
    (re.compile(r"\bthese are dangerous times\b", re.IGNORECASE), "these are dangerous times"),
    (re.compile(r"\bnot everyone is friendly to newcomers\b", re.IGNORECASE), "not everyone is friendly to newcomers"),
)

_FORBIDDEN_GENERIC_PHRASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bin this city\b", re.IGNORECASE), "in_this_city"),
    (re.compile(r"\btimes are tough\b", re.IGNORECASE), "times_are_tough"),
    (re.compile(r"\btrust is hard to come by\b", re.IGNORECASE), "trust_is_hard_to_come_by"),
    (re.compile(r"\byou[’']ll need to prove yourself\b", re.IGNORECASE), "prove_yourself"),
)
_VALIDATOR_VOICE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bi can(?:not|'t)\s+answer that\b", re.IGNORECASE), "cant_answer_that"),
    (re.compile(r"\bbased on what(?:'s| is)\s+established\b", re.IGNORECASE), "based_on_established"),
    (re.compile(r"\bwe can determine\b", re.IGNORECASE), "we_can_determine"),
    (re.compile(r"\bas an ai\b", re.IGNORECASE), "as_an_ai"),
    (re.compile(r"\bas (?:a )?(?:language )?model\b", re.IGNORECASE), "model_identity"),
    (re.compile(r"\bi (?:can(?:not|'t)|do not|don't)\s+(?:access|see|know|verify|check|look up)\b", re.IGNORECASE), "system_limitation"),
    (re.compile(r"\bi (?:do not|don't|can(?:not|'t))\s+have access\b", re.IGNORECASE), "tool_access"),
    (re.compile(r"\bmy (?:system|training data|tools?)\b", re.IGNORECASE), "system_reference"),
    (re.compile(r"\b(?:the evidence|available evidence|the record|canon)\s+(?:suggests|indicates|shows)\b", re.IGNORECASE), "evidence_review"),
    (re.compile(r"\b(?:under|by)\s+the\s+rules\b", re.IGNORECASE), "rules_explanation"),
    (re.compile(r"\b(?:this|that|it)\s+(?:would|will)\s+require\s+(?:a\s+)?(?:roll|check)\b", re.IGNORECASE), "rules_explanation"),
)
UNCERTAINTY_CATEGORIES: tuple[str, ...] = (
    "unknown_identity",
    "unknown_location",
    "unknown_motive",
    "unknown_method",
    "unknown_quantity",
    "unknown_feasibility",
)
RETRY_FAILURE_PRIORITY: dict[str, int] = {
    "unresolved_question": 10,
    "validator_voice": 20,
    "npc_contract_failure": 30,
    "scene_stall": 40,
    "echo_or_repetition": 50,
    "forbidden_generic_phrase": 60,
}
MAX_TARGETED_RETRY_ATTEMPTS = 2

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


def detect_forbidden_generic_phrases(player_facing_text: str) -> List[str]:
    """Detect forbidden stock RPG phrases that must be rewritten when present.

    Unlike detect_stock_warning_filler_repetition(), this triggers on a single
    occurrence because these phrases are considered hard failures.
    """
    if not isinstance(player_facing_text, str):
        return []
    txt = " ".join(player_facing_text.split())
    if not txt:
        return []
    hits: List[str] = []
    for pattern, label in _FORBIDDEN_GENERIC_PHRASE_PATTERNS:
        if pattern.search(txt):
            hits.append(f"forbidden_generic:{label}")
    return hits


def detect_validator_voice(player_facing_text: str) -> List[str]:
    """Detect system/validator tone that breaks in-world narration."""
    if not isinstance(player_facing_text, str):
        return []
    txt = " ".join(player_facing_text.split())
    if not txt:
        return []
    hits: List[str] = []
    for pattern, label in _VALIDATOR_VOICE_PATTERNS:
        if pattern.search(txt):
            hits.append(f"validator_voice:{label}")
    return hits


def _split_reply_sentences(text: str) -> List[str]:
    """Split paragraphs into sentence-like units for targeted cleanup."""
    if not isinstance(text, str):
        return []
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    return parts


def choose_retry_strategy(failures: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Pick the highest-priority retry target from inspectable failures."""
    ranked: List[Dict[str, Any]] = []
    for failure in failures or []:
        if not isinstance(failure, dict):
            continue
        failure_class = str(failure.get("failure_class") or "").strip()
        if not failure_class:
            continue
        ranked.append(
            {
                **failure,
                "failure_class": failure_class,
                "priority": int(failure.get("priority") or RETRY_FAILURE_PRIORITY.get(failure_class, 999)),
            }
        )
    if not ranked:
        return None
    ranked.sort(key=lambda item: (int(item.get("priority", 999)), str(item.get("failure_class") or "")))
    return ranked[0]


def build_retry_prompt_for_failure(
    failure: Dict[str, Any],
    *,
    response_policy: Dict[str, Any] | None = None,
) -> str:
    """Build a narrowly scoped retry instruction for one failure class only."""
    failure_class = str((failure or {}).get("failure_class") or "").strip()
    reasons = [str(r).strip() for r in ((failure or {}).get("reasons") or []) if isinstance(r, str) and str(r).strip()]
    priority_order = (
        list((response_policy or {}).get("rule_priority_order") or [])
        if isinstance((response_policy or {}).get("rule_priority_order"), list)
        else [label for _, label in RESPONSE_RULE_PRIORITY]
    )
    shared = (
        f"Rule Priority Hierarchy: {priority_order}. "
        f"{RULE_PRIORITY_COMPACT_INSTRUCTION} "
        f"Retry target: {failure_class}. Correct only this failure class. Return the same JSON shape."
    )

    if failure_class == "validator_voice":
        return (
            f"{shared} Rewrite the reply into diegetic, world-facing phrasing only. "
            f"{NO_VALIDATOR_VOICE_RULE} "
            "Remove validator, system, limitation, tool-access, model-identity, and rules-explanation language from standard narration."
        )

    if failure_class == "unresolved_question":
        uncertainty_category = str((failure or {}).get("uncertainty_category") or "").strip()
        category_hint = f" Uncertainty category: {uncertainty_category}." if uncertainty_category else ""
        return (
            f"{shared} The player's direct question still lacks a bounded answer. "
            "Answer it in the first sentence. Do not refuse, deflect, or explain limitations. "
            "If certainty is incomplete, give the best grounded partial answer and one concrete lead tied to the current scene or NPC."
            f"{category_hint}"
        )

    if failure_class == "echo_or_repetition":
        return (
            f"{shared} Semantically rewrite the reply so it does not echo the player's wording or quoted speech. "
            "Change sentence structure and phrasing, and react with new information or consequence instead of restating the input."
        )

    if failure_class == "npc_contract_failure":
        missing = [str(x).strip() for x in ((failure or {}).get("missing") or []) if isinstance(x, str) and str(x).strip()]
        missing_hint = f" Missing contract elements: {missing}." if missing else ""
        return (
            f"{shared} Produce a direct NPC answer, reaction, or refusal consistent with the current target. "
            "Include at least one concrete person, place, faction, next step, or directly usable condition, time, or location."
            f"{missing_hint}"
        )

    if failure_class == "scene_stall":
        return (
            f"{shared} Advance the scene by one concrete development now. "
            "Introduce one actionable reveal, answer, consequence, opportunity, environmental change, or new pressure so the exchange does not remain static. "
            "Include exactly one matching scene momentum tag in tags: scene_momentum:<kind>."
        )

    if failure_class == "forbidden_generic_phrase":
        return (
            f"{shared} Rewrite only the offending generic phrase or sentence into scene-anchored specifics. "
            "Keep the rest of the reply intact where possible and avoid flattening the whole response."
        )

    reason_text = f" Reasons: {reasons}." if reasons else ""
    return f"{shared} Rewrite narrowly to resolve this failure.{reason_text}"


SYSTEM_PROMPT = _SYSTEM_PROMPT_HEADER + """The application owns authoritative mechanics and persistence. You narrate, propose updates, and draft scenes.
You must not invent dice results or override mechanical resolutions supplied by the app.
You may propose structured updates that the app may auto-apply.
When introducing new names or factions, include a source (rumor, NPC claim, notice, or observation).
Treat player input as an action declaration. Default action style is third person (for example: "Galinor examines the gate records.").
Quoted in-character speech is valid inside the declaration (for example: "Galinor asks, \\"Who signed this order?\\""), and you should preserve the player's expression format rather than rewriting it.
Do not restate or lightly paraphrase the player's action declaration as your opening sentence unless exact wording is needed for disambiguation. Prefer continuing from authoritative resolved state, consequences, and NPC intent.
Do not restate or paraphrase the player's input. Always continue forward with new information.
Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.
Forbidden generic phrases (rewrite if they appear): "In this city...", "Times are tough...", "Trust is hard to come by...", "You'll need to prove yourself..."
SCENE MOMENTUM RULE (HARD RULE):
Every 2–3 exchanges, the GM MUST introduce one of:
- new information
- a new actor entering
- environmental change
- time pressure
- consequence or opportunity
The scene MUST NOT remain static conversation.
FAILURE CONDITION:
If the scene remains unchanged after 3 exchanges, it is invalid.
Tagging contract for enforcement:
When you introduce the momentum beat, include exactly one tag in tags:
scene_momentum:<kind>
Where <kind> is one of: new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity.
QUESTION RESOLUTION RULE (HARD RULE):
Every direct player question MUST be answered explicitly before any additional dialogue.
Structure:
1. Direct answer (first sentence)
2. Optional elaboration
3. Optional hook
The GM/NPC MUST NOT deflect, generalize, or ask a new question before answering.
If the player asks a direct question, you must answer it concretely. If full certainty is unavailable, provide the best grounded partial answer and state uncertainty in-character through rumor, witness limits, distance, darkness, missing access, or incomplete observation. Do not repeat prior information.
Never speak as a validator, analyst, referee of canon, or system in standard narration. Do not mention what is or is not established, answerable, visible to tools, or available to the model.
When answering a player question, give a direct answer first. Do not replace the answer with narrative description.
If an interaction is underway with an active NPC in the payload, prioritize the immediate exchange and that interlocutor over re-stating base scene summary. Use environmental details only when newly relevant, requested, or needed for a transition beat.

NPC RESPONSE CONTRACT (HARD RULE):
When an NPC is asked a question, the NPC reply MUST include at least one of:
- a specific person, place, or faction
- a concrete next step the player can take
- a directly usable piece of information (time, location, condition, requirement)
The NPC MUST NOT respond with only general advice, philosophy, vague warnings, or social commentary.
If the NPC lacks full information, they must provide partial specifics OR direct the player to a concrete source (named person/place/document).

PERCEPTION / INTENT ADJUDICATION RULE (HARD RULE):
When the player asks for behavioral insight about an NPC (e.g., nervous, lying, controlled):
- Choose a single dominant state (not mixed; do not say "mix of" or "seems like both")
- Provide 1–2 concrete tells (physical or behavioral)
- Optionally map to a skill interpretation (Sense Motive, etc.)
Failure conditions:
- Vague blends ("mix of", "seems like both")
- Pure emotional summaries without observable cues
Example: "He’s controlled, but strained—his jaw tightens when you press him, and he avoids eye contact when mentioning the patrol."

Scene information has three layers. Respect them strictly:
- visible_facts: you may narrate these directly; the player already sees or knows them.
- discoverable_clues: reveal ONLY when the player investigates, searches, observes closely, or meaningfully interacts (e.g. searching a body, questioning someone, examining an object). Do not mention them in narration until the player has done such an action.
- hidden_facts: never state these in player_facing_text. Use them only to influence NPC behavior, atmosphere, tension, and indirect clues. Let the player infer; do not explain secrets outright.
When secrets exist in a scene, reveal them gradually through behavior, rumor, suspicious activity, or environmental detail. Do not explain secrets outright. Let the player infer them.
Spoiler safeguard: never put hidden_facts or undiscovered discoverable_clues into player_facing_text.

Resolved exploration actions: When mechanical_resolution contains resolved_exploration_action, the app has already determined the action and any scene transition. The current scene in the payload is authoritative. Narrate the outcome of that resolved action—do not restate the previous scene. If scene_transition_already_occurred is true, narrate the destination scene and arrival; do not override app-side transitions with activate_scene_id or new_scene_draft. For observe/investigate/interact, reveal new information, consequence, tension, or a narrowed decision; avoid filler unless paired with a concrete lead or obstacle. Never repeat the same observation twice in a row for the same scene and action.

Return valid JSON only with this shape:
{
  "player_facing_text": "string",
  "tags": ["string"],
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
"""


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


def sanitize_player_facing_text(player_text: str, scene_envelope: Dict[str, Any], user_text: str, discovered_clues: List[str] | None = None) -> Dict[str, Any]:
    """Deterministic leak guard against obvious hidden-fact disclosure.

    This is intentionally simple: it catches exact/near-exact reuse of distinctive
    hidden-fact phrasing and a few high-signal keywords.
    """
    public_scene, discoverable, hidden = _scene_layers(scene_envelope)
    _ = public_scene  # kept for future extensions; not used yet

    txt = player_text or ''
    low = txt.lower()

    intent = classify_player_intent(user_text)
    allow_disc = bool(intent.get('allow_discoverable_clues'))
    discovered_set = {s.lower().strip() for s in (discovered_clues or []) if isinstance(s, str)}

    # Hidden fact phrase reuse (exact / near-exact tokens).
    hit_reasons: List[str] = []
    for hf in hidden:
        if not isinstance(hf, str) or not hf.strip():
            continue
        hf_low = hf.lower().strip()
        # If the model repeats most of a hidden fact verbatim, treat as a leak.
        if hf_low in low:
            hit_reasons.append('spoiler_guard:hidden_fact_exact')
            break

    # High-signal frontier_gate regression keywords (and general obvious leaks).
    keyword_leaks = ('noble house', 'smuggler', 'magical talent')
    if any(k in low for k in keyword_leaks):
        hit_reasons.append('spoiler_guard:hidden_fact_keyword')

    # Discoverable clues must not appear unless player justified investigation,
    # except if they were already discovered previously.
    if discoverable:
        for raw_clue in discoverable:
            rec = normalize_clue_record(raw_clue)
            clue_low = rec['text'].lower().strip()
            if not clue_low:
                continue
            if clue_low in low:
                if clue_low in discovered_set:
                    # Already discovered: always allowed.
                    continue
                if not allow_disc:
                    hit_reasons.append('spoiler_guard:undiscovered_clue_without_investigation')
                    break

    if not hit_reasons:
        return {'text': txt, 'did_sanitize': False, 'reasons': []}

    uncertainty = classify_uncertainty(user_text, scene_envelope=scene_envelope) if _is_direct_player_question(user_text) else None
    safe = _bounded_spoiler_safe_text(user_text, scene_envelope=scene_envelope)
    return {'text': safe, 'did_sanitize': True, 'reasons': hit_reasons, 'uncertainty': uncertainty}


_ECHO_TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
_DOUBLE_QUOTED_SPEECH_PATTERN = re.compile(r'["\u201c\u201d]([^"\u201c\u201d]{3,240})["\u201c\u201d]')
_SINGLE_QUOTED_SPEECH_PATTERN = re.compile(
    r"(?:(?<=^)|(?<=[\s(\[{]))['\u2018\u2019]([^'\u2018\u2019]{3,240})['\u2018\u2019](?=$|[\s)\]}.,!?;:])"
)


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


def guard_gm_output(gm: Dict[str, Any], scene_envelope: Dict[str, Any], user_text: str, discovered_clues: List[str] | None = None) -> Dict[str, Any]:
    """Apply leak guard and annotate debug_notes/tags without breaking schema."""
    if not isinstance(gm, dict):
        return gm
    # Avoid mutating caller-owned dicts (easier to test and safer for reuse).
    gm = dict(gm)
    pft = gm.get('player_facing_text') if isinstance(gm.get('player_facing_text'), str) else ''
    res = sanitize_player_facing_text(pft, scene_envelope, user_text, discovered_clues)
    if not res['did_sanitize']:
        return gm

    tags = gm.get('tags') if isinstance(gm.get('tags'), list) else []
    uncertainty = res.get('uncertainty') if isinstance(res.get('uncertainty'), dict) else {}
    category = str(uncertainty.get('category') or '').strip()
    uncertainty_tags = [f'uncertainty:{category}'] if category else []
    gm['tags'] = list(tags) + ['spoiler_guard'] + uncertainty_tags
    gm['player_facing_text'] = res['text']
    dbg = gm.get('debug_notes') if isinstance(gm.get('debug_notes'), str) else ''
    gm['debug_notes'] = (dbg + ' | ' if dbg else '') + f'spoiler_guard: {res["reasons"]}'
    return gm


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


def question_resolution_rule_check(*, player_text: str, gm_reply_text: str) -> Dict[str, Any]:
    """Check the Question Resolution Rule for direct player questions.

    Returns:
      {applies: bool, ok: bool, reasons: [str]}
    """
    player = str(player_text or "").strip()
    reply = str(gm_reply_text or "").strip()
    applies = _is_direct_player_question(player)
    if not applies:
        return {"applies": False, "ok": True, "reasons": []}
    if not reply:
        return {"applies": True, "ok": False, "reasons": ["question_rule:empty_reply"]}

    first = _first_sentence(reply)
    first_low = first.lower()
    reasons: List[str] = []

    if "?" in first:
        reasons.append("question_rule:asked_question_before_answer")

    has_refusal = any(p in first_low for p in _QUESTION_RESOLUTION_REFUSAL_PHRASES)
    has_starter = any(first_low.startswith(p) for p in _QUESTION_RESOLUTION_ANSWER_STARTERS)
    q_tokens = _question_content_tokens(player)
    has_token_overlap = any(tok in first_low for tok in q_tokens) if q_tokens else False

    if has_refusal:
        reasons.append("question_rule:refusal_or_meta_disallowed")

    ok = bool(("?" not in first) and (not has_refusal) and (has_starter or has_token_overlap))
    if not ok and not reasons:
        reasons.append("question_rule:first_sentence_not_explicit_answer")
    return {"applies": True, "ok": ok, "reasons": reasons}


def classify_uncertainty(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, str]:
    """Classify unresolved answers into a compact, inspectable uncertainty shape."""
    category = _classify_uncertainty_category(player_text)
    scene_env = scene_envelope if isinstance(scene_envelope, dict) else {}
    session_data = session if isinstance(session, dict) else {}
    world_data = world if isinstance(world, dict) else {}
    resolution_data = resolution if isinstance(resolution, dict) else {}
    location = _resolve_scene_location(scene_env)
    scene_id = _resolve_scene_id(scene_env)
    visible = _scene_visible_facts(scene_env)
    visible_low = " ".join(v.lower() for v in visible)
    npc_id = _active_interaction_target_id(session_data)
    npc_name = _resolve_npc_name(world_data, npc_id, scene_id)
    scene = (scene_env or {}).get("scene", {}) if isinstance(scene_env, dict) else {}
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_label = ""
    if exits and isinstance(exits[0], dict):
        exit_label = str(exits[0].get("label") or "").strip()

    def _lead_from_scene(default_text: str) -> str:
        if "notice board" in visible_low or "noticeboard" in visible_low:
            return "Best lead: work the notice board for one concrete detail you can test right away."
        if exit_label:
            return f"Best lead: follow the route toward {exit_label} and press the next witness there."
        if location:
            return f"Best lead: press for one concrete handle in {location} rather than the whole answer at once."
        return default_text

    if category == "unknown_identity":
        return {
            "category": category,
            "what_can_be_said_now": "No one here will hang a single name on it yet, but the field can be narrowed.",
            "what_is_not_nailed_down_yet": "The true name is still in shadow here.",
            "best_current_lead": (
                f"Best lead: ask {npc_name} who fits, who does not, and whose name keeps surfacing."
                if npc_name
                else _lead_from_scene("Best lead: ask who fits the role, who does not, and which name keeps surfacing.")
            ),
        }
    if category == "unknown_location":
        return {
            "category": category,
            "what_can_be_said_now": "No one here can pin it to a single doorstep yet; you have a last-known trail, not a final point.",
            "what_is_not_nailed_down_yet": "The exact place is still blurred by distance, rumor, or missing detail.",
            "best_current_lead": (
                f"Best lead: ask {npc_name} for the last sighting, the route taken, or who handles access there."
                if npc_name
                else _lead_from_scene("Best lead: pull the last sighting, route, or gatekeeper from the scene before chasing the final location.")
            ),
        }
    if category == "unknown_motive":
        return {
            "category": category,
            "what_can_be_said_now": "No one here is naming the heart of it yet, but the pressure around it can still be read.",
            "what_is_not_nailed_down_yet": "The real reason is still being kept close to the chest.",
            "best_current_lead": (
                f"Best lead: ask {npc_name} who profits, who is under pressure, or what changed just before this."
                if npc_name
                else _lead_from_scene("Best lead: ask who gains, who is cornered, or what changed just before this turned.")
            ),
        }
    if category == "unknown_quantity":
        return {
            "category": category,
            "what_can_be_said_now": "No one here will swear to a clean count yet; you have a rough scale, not precision.",
            "what_is_not_nailed_down_yet": "The exact number is still loose in the telling.",
            "best_current_lead": (
                f"Best lead: ask {npc_name} for the smallest and largest count they would swear to."
                if npc_name
                else _lead_from_scene("Best lead: pin down a lower and upper count from what is visible, posted, or witnessed.")
            ),
        }
    if category == "unknown_feasibility":
        check = resolution_data.get("check_request") if isinstance(resolution_data.get("check_request"), dict) else {}
        skill = str(check.get("skill") or "").strip().replace("_", " ")
        reason = str(check.get("reason") or "").strip()
        lead = ""
        if skill and reason:
            lead = f"Best lead: the deciding condition is {reason}; test it with {skill} instead of guessing."
        elif skill:
            lead = f"Best lead: test the deciding condition with {skill} instead of guessing."
        elif npc_name:
            lead = f"Best lead: ask {npc_name} what would make them say yes, then meet that condition."
        else:
            lead = _lead_from_scene("Best lead: ask what condition would make it possible here, then test that condition directly.")
        return {
            "category": category,
            "what_can_be_said_now": "No one here can promise it will work yet; success turns on one deciding condition.",
            "what_is_not_nailed_down_yet": "Whether it can be done is not settled until that condition is tested.",
            "best_current_lead": lead,
        }
    return {
        "category": "unknown_method",
        "what_can_be_said_now": "No one here can lay out the exact trick yet; the effect is plain enough.",
        "what_is_not_nailed_down_yet": "The means are still obscured by the aftermath and half-seen tells.",
        "best_current_lead": (
            f"Best lead: ask {npc_name} what was touched, forced, moved, or bypassed."
            if npc_name
            else _lead_from_scene("Best lead: inspect what was touched, forced, moved, or bypassed before chasing the whole explanation.")
        ),
    }


def render_uncertainty_response(uncertainty: Dict[str, Any]) -> str:
    """Render a bounded answer with a known edge, uncertainty edge, and lead."""
    if not isinstance(uncertainty, dict):
        return ""
    parts = [
        str(uncertainty.get("what_can_be_said_now") or "").strip(),
        str(uncertainty.get("what_is_not_nailed_down_yet") or "").strip(),
        str(uncertainty.get("best_current_lead") or "").strip(),
    ]
    rendered: List[str] = []
    for part in parts:
        if not part:
            continue
        if part[-1] not in ".!?":
            part += "."
        rendered.append(part)
    return " ".join(rendered).strip()


def _apply_uncertainty_to_gm(
    gm: Dict[str, Any],
    *,
    uncertainty: Dict[str, Any],
    reason: str,
    replace_text: bool = False,
) -> Dict[str, Any]:
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    rendered = render_uncertainty_response(uncertainty)
    if not rendered:
        return gm
    existing = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    gm["player_facing_text"] = rendered if replace_text or not existing.strip() else (rendered + "\n\n" + existing.strip()).strip()
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    category = str(uncertainty.get("category") or "").strip()
    uncertainty_tag = f"uncertainty:{category}" if category else "uncertainty"
    gm["tags"] = list(tags) + [uncertainty_tag]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + f"{reason}:{category or 'unknown'}"
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


def _validator_voice_world_fallback(*, scene_envelope: Dict[str, Any], player_text: str) -> str:
    """Rebuild leaked validator voice as in-world uncertainty."""
    if _is_direct_player_question(player_text):
        return render_uncertainty_response(
            classify_uncertainty(
                player_text,
                scene_envelope=scene_envelope,
            )
        )
    location = _resolve_scene_location(scene_envelope)
    loc_phrase = f" in {location}" if location else ""
    return (
        f"No one gives you the whole shape of it{loc_phrase} yet; what you have are fragments, reactions, "
        "and room to press for one concrete lead."
    )


def enforce_question_resolution_rule(
    gm: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Last-resort deterministic compliance with Question Resolution Rule.

    If the player asked a direct question and the reply doesn't start with an explicit
    answer, prepend a grounded uncertain answer plus a concrete next step.
    """
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    reply = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    chk = question_resolution_rule_check(player_text=player_text, gm_reply_text=reply)
    if not chk.get("applies") or chk.get("ok"):
        return gm

    out = _apply_uncertainty_to_gm(
        gm,
        uncertainty=classify_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        ),
        reason=f"question_resolution_rule:enforced:{chk.get('reasons')}",
        replace_text=False,
    )
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(tags) + ["question_resolution_rule"]
    return out


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


def npc_response_contract_check(
    *,
    player_text: str,
    npc_reply_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Check the NPC response contract for direct questions to an NPC.

    Returns:
      {applies: bool, ok: bool, reasons: [str], missing: [str]}
    """
    player = str(player_text or "").strip()
    reply = str(npc_reply_text or "").strip()
    low_player = player.lower()
    low_reply = reply.lower()

    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)

    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    if not npc_id:
        npc_id = _active_interaction_target_id(session)
    has_npc_target = bool(npc_id)

    # "Asked a question" heuristic: direct question mark or leading question word.
    first_word = (low_player.replace('"', ' ').replace("'", " ").split() or [""])[0]
    is_question = ("?" in low_player) or (first_word in _QUESTION_WORDS)

    applies = bool(has_npc_target and is_question)
    if not applies:
        return {"applies": False, "ok": True, "reasons": [], "missing": []}

    npc_name = str(social.get("npc_name") or "").strip() or _resolve_npc_name(world, npc_id, scene_id)
    faction_names = _world_faction_names(world)
    other_npc_names = _in_scene_npc_names(world, scene_id)

    specific_tokens: List[str] = []
    if npc_name:
        specific_tokens.append(npc_name)
    if location:
        specific_tokens.append(location)
    specific_tokens.extend(faction_names)
    specific_tokens.extend(other_npc_names)
    specific_tokens = [t for t in specific_tokens if isinstance(t, str) and t.strip()]

    has_specific = any(t.lower() in low_reply for t in specific_tokens if len(t) >= 4)
    has_next_step = any(tok in low_reply for tok in _NPC_CONTRACT_ACTION_TOKENS)
    has_requirement = any(tok in low_reply for tok in _NPC_CONTRACT_REQUIREMENT_TOKENS)
    has_time = any(tok in low_reply for tok in _NPC_CONTRACT_TIME_TOKENS) or bool(re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", low_reply))
    has_usable_info = bool(has_requirement or has_time or (" at " in low_reply and len(low_reply) >= 30))

    ok = bool(has_specific or has_next_step or has_usable_info)

    missing: List[str] = []
    if not has_specific:
        missing.append("specific_person_place_or_faction")
    if not has_next_step:
        missing.append("concrete_next_step")
    if not has_usable_info:
        missing.append("usable_info")

    reasons: List[str] = []
    if not reply:
        reasons.append("npc_contract:empty_reply")
    if not ok:
        reasons.append("npc_contract:missing_required_specificity")
    return {"applies": True, "ok": ok, "reasons": reasons, "missing": missing}


def _contract_fallback_next_step(scene_envelope: Dict[str, Any], *, npc_name: str, location: str) -> str:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    visible_low = " ".join(str(v).lower() for v in visible if isinstance(v, str))

    if "notice board" in visible_low or "noticeboard" in visible_low:
        loc_phrase = f" in {location}" if location else ""
        return f"Next step: check the notice board{loc_phrase} for the posted names, times, and requirements."
    if exits and isinstance(exits[0], dict) and str(exits[0].get("label") or "").strip():
        label = str(exits[0].get("label") or "").strip()
        return f"Next step: take the exit labeled “{label}” and follow up there."
    if npc_name:
        loc_phrase = f" here in {location}" if location else " here"
        return f"Next step: press {npc_name}{loc_phrase} for a name, a place, or a condition—something you can act on immediately."
    if location:
        return f"Next step: pick a concrete lead in {location} (a posted notice, a guard post, or a shopfront) and ask one targeted question."
    return "Next step: ask a targeted follow-up question that names a person or place, or seek a specific posted notice."


def enforce_npc_response_contract(
    gm: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Ensure NPC replies to questions contain concrete specificity.

    This is a last-resort, deterministic patch: it never adds hidden facts.
    """
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    reply = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    chk = npc_response_contract_check(
        player_text=player_text,
        npc_reply_text=reply,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    if not chk.get("applies") or chk.get("ok"):
        return gm

    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)
    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip() or _active_interaction_target_id(session)
    npc_name = str(social.get("npc_name") or "").strip() or _resolve_npc_name(world, npc_id, scene_id)
    addition = _contract_fallback_next_step(scene_envelope, npc_name=npc_name, location=location)

    txt = reply.strip()
    if txt and not txt.endswith((".", "!", "?", "…")):
        txt += "."
    txt = (txt + ("\n\n" if txt else "") + addition).strip()
    gm["player_facing_text"] = txt

    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    gm["tags"] = list(tags) + ["npc_response_contract"]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + f"npc_response_contract:enforced:{chk.get('missing')}"
    return gm


def _safe_json(text: str) -> Dict[str, Any]:
    """Parse model text into a safe, normalized GM response dict.

    Ensures the returned value always has the expected keys with safe defaults
    so callers can rely on a stable schema even when the model output is
    malformed or missing fields.
    """
    try:
        parsed = json.loads(text)
    except Exception:
        return {
            'player_facing_text': text or 'No narration provided.',
            'tags': ['fallback'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Non-JSON response fallback.'
        }

    # If the model returned a non-dict, treat entire text as narration.
    if not isinstance(parsed, dict):
        return {
            'player_facing_text': str(parsed),
            'tags': ['fallback'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Parsed JSON was not an object.'
        }

    # Build normalized response, validating types and providing defaults.
    out: Dict[str, Any] = {
        'player_facing_text': parsed.get('player_facing_text') if isinstance(parsed.get('player_facing_text'), str) else (str(parsed)[:1000] if parsed else ''),
        'tags': parsed.get('tags') if isinstance(parsed.get('tags'), list) else [],
        'scene_update': parsed.get('scene_update') if isinstance(parsed.get('scene_update'), dict) else None,
        'activate_scene_id': parsed.get('activate_scene_id') if isinstance(parsed.get('activate_scene_id'), str) else None,
        'new_scene_draft': parsed.get('new_scene_draft') if isinstance(parsed.get('new_scene_draft'), dict) else None,
        'world_updates': parsed.get('world_updates') if isinstance(parsed.get('world_updates'), dict) else None,
        'suggested_action': parsed.get('suggested_action') if isinstance(parsed.get('suggested_action'), dict) else None,
        'debug_notes': parsed.get('debug_notes') if isinstance(parsed.get('debug_notes'), str) else 'Parsed model output.'
    }

    return out


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
) -> List[Dict[str, str]]:
    # Always load scene from session to ensure correct context (no cached/stale scene variable)
    active_id = (session.get('active_scene_id') or '').strip()
    if active_id:
        scene = load_scene(active_id)
    # else: use passed scene for backward compatibility (e.g. tests with incomplete session)

    # Fresh campaign: do not inject prior chat logs or cached conversation history
    if session.get("chat_history") == []:
        recent_log_for_prompt = []
        session.pop("chat_history", None)
        print("[PROMPT] fresh campaign prompt constructed")
    else:
        recent_log_for_prompt = recent_log[-8:]

    public_scene, discoverable_raw, hidden = _scene_layers(scene)
    intent = classify_player_intent(user_text)
    allow_disc = bool(intent.get('allow_discoverable_clues'))
    uncertainty_hint = classify_uncertainty(
        user_text,
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    ) if _is_direct_player_question(user_text) else None

    normalized_clues = [normalize_clue_record(c) for c in discoverable_raw]
    runtime_for_scene = scene_runtime or {}
    discovered_texts = {
        s for s in runtime_for_scene.get('discovered_clues', []) if isinstance(s, str)
    }
    discovered = [c for c in normalized_clues if c['text'] in discovered_texts]
    undiscovered = [c for c in normalized_clues if c['text'] not in discovered_texts]

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
    response_mode = session.get('response_mode', 'standard')
    mode_instructions = {
        'terse': 'Narration mode: terse. Use short, minimal sentences focused on clear outcomes.',
        'standard': 'Narration mode: standard. Use 1-4 concise paragraphs with a balance of description and pacing.',
        'vivid': 'Narration mode: vivid. Emphasize sensory detail and mood while staying within 1-4 paragraphs.',
        'tactical': 'Narration mode: tactical. Emphasize positions, options, risks, and consequences in the scene.',
        'investigative': 'Narration mode: investigative. Emphasize clues, leads, and what careful observation reveals.',
    }
    mode_instruction = mode_instructions.get(response_mode, mode_instructions['standard'])

    def _build_world_state_prompt_view(w: Dict[str, Any]) -> Dict[str, Any]:
        """Build a sanitized world_state view for the prompt. Keys starting with _ are hidden."""
        ws = w.get('world_state') or {}
        if not isinstance(ws, dict):
            return {'flags': {}, 'counters': {}, 'clocks_summary': []}
        flags = {k: v for k, v in (ws.get('flags') or {}).items() if isinstance(k, str) and not k.startswith('_')}
        counters = {k: v for k, v in (ws.get('counters') or {}).items() if isinstance(k, str) and not k.startswith('_')}
        clocks_raw = ws.get('clocks') or {}
        clocks_summary = [
            f"{k}: {int(c.get('progress', 0))}/{int(c.get('max', 10))}"
            for k, c in clocks_raw.items()
            if isinstance(k, str) and not k.startswith('_') and isinstance(c, dict)
        ]
        return {'flags': flags, 'counters': counters, 'clocks_summary': clocks_summary}

    world_state_view = _build_world_state_prompt_view(world)
    payload = build_narration_context(
        campaign, world, session, character, scene, combat, recent_log, user_text,
        resolution, scene_runtime,
        public_scene=public_scene,
        discoverable_clues=[c['text'] for c in undiscovered] if allow_disc else [],
        gm_only_hidden_facts=hidden,
        gm_only_discoverable_locked=[c['text'] for c in undiscovered] if not allow_disc else [],
        discovered_clue_records=discovered,
        undiscovered_clue_records=undiscovered,
        pending_leads=list(runtime_for_scene.get('pending_leads') or []),
        intent=intent,
        world_state_view=world_state_view,
        mode_instruction=mode_instruction,
        recent_log_for_prompt=recent_log_for_prompt,
        uncertainty_hint=uncertainty_hint,
    )
    known_clues = get_known_clues_with_presentation(session)
    payload["clues"] = {
        "known": known_clues,
        "implicit": [c for c in known_clues if c.get("presentation") == "implicit"],
        "explicit": [c for c in known_clues if c.get("presentation") == "explicit"],
        "actionable": [c for c in known_clues if c.get("presentation") == "actionable"],
    }

    # Add resolved exploration context when the app has already determined the action.
    if resolution and isinstance(resolution, dict):
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

    if resolution and isinstance(resolution, dict) and resolution.get('hint'):
        payload['instructions'] = list(payload['instructions']) + [resolution['hint']]
    return [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
    ]


def call_gpt(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    # Wrap the OpenAI call so network/API/model errors do not crash gameplay.
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.responses.create(model=MODEL_NAME, input=messages)
        text = getattr(resp, 'output_text', None)
        if text is None:
            # Fallback to stringifying the response if expected attribute missing.
            text = str(resp)
        return _safe_json(text.strip())
    except Exception as e:
        # Return a safe fallback response that preserves the expected schema so
        # callers can continue without special-casing exceptions.
        return {
            'player_facing_text': 'The game master is temporarily unavailable. Please try again.',
            'tags': ['error'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': f'call_gpt error: {repr(e)}'
        }


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


def validate_gm_state_update(gm: Dict[str, Any], session: Dict[str, Any], scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize GM-proposed state updates.

    - Enforces allowlisted keys for scene_update/world_updates/new_scene_draft.
    - Clamps text lengths.
    - Prevents hidden facts from being promoted into visible_facts.
    """
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)

    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}
    existing_hidden = {
        str(h).strip()
        for h in scene.get('hidden_facts', [])
        if isinstance(h, str) and h.strip()
    }

    def _norm_str_list(val: Any, max_len: int = 500, max_items: int = 16) -> List[str]:
        out: List[str] = []
        if isinstance(val, list):
            for item in val:
                if not isinstance(item, str):
                    continue
                s = item.strip()
                if not s:
                    continue
                if len(s) > max_len:
                    s = s[:max_len]
                if s not in out:
                    out.append(s)
                if len(out) >= max_items:
                    break
        return out

    debug_reasons: List[str] = []

    su = gm.get('scene_update')
    if isinstance(su, dict):
        cleaned: Dict[str, Any] = {}
        vis_add = _norm_str_list(su.get('visible_facts_add'))
        # Block promotion: do not allow exact hidden facts to become visible via update.
        filtered_vis = []
        for v in vis_add:
            if v in existing_hidden:
                debug_reasons.append('validator:hidden_fact_promotion_blocked')
                continue
            filtered_vis.append(v)
        if filtered_vis:
            cleaned['visible_facts_add'] = filtered_vis

        disc_add = _norm_str_list(su.get('discoverable_clues_add'))
        if disc_add:
            cleaned['discoverable_clues_add'] = disc_add

        hid_add = _norm_str_list(su.get('hidden_facts_add'))
        if hid_add:
            cleaned['hidden_facts_add'] = hid_add

        mode = su.get('mode')
        if isinstance(mode, str) and mode in {'exploration', 'combat', 'social', 'travel'}:
            cleaned['mode'] = mode

        gm['scene_update'] = cleaned or None

    wu = gm.get('world_updates')
    if isinstance(wu, dict):
        cleaned_wu: Dict[str, Any] = {}
        events = _norm_str_list(wu.get('append_events'), max_len=500, max_items=32)
        if events:
            cleaned_wu['append_events'] = events
        # Pass through projects/assets/factions only if they are lists; leave structure unchanged.
        for key in ('projects', 'assets', 'factions'):
            val = wu.get(key)
            if isinstance(val, list):
                cleaned_wu[key] = val
        # world_state: flags, counters, clocks — keys starting with _ are internal and dropped.
        ws_up = wu.get('world_state')
        if isinstance(ws_up, dict):
            out_ws: Dict[str, Any] = {}
            for sub in ('flags', 'counters', 'clocks'):
                raw = ws_up.get(sub)
                if not isinstance(raw, dict):
                    continue
                out_ws[sub] = {k: v for k, v in raw.items() if isinstance(k, str) and k.strip() and not k.startswith('_')}
            if out_ws:
                cleaned_wu['world_state'] = out_ws
        gm['world_updates'] = cleaned_wu or None

    nd = gm.get('new_scene_draft')
    if isinstance(nd, dict):
        # Normalize minimal allowed shape.
        draft = {
            'id': nd.get('id'),
            'location': str(nd.get('location', '') or '').strip()[:200],
            'summary': str(nd.get('summary', '') or '').strip()[:800],
            'mode': nd.get('mode', 'exploration'),
            'visible_facts': _norm_str_list(nd.get('visible_facts')),
            'discoverable_clues': _norm_str_list(nd.get('discoverable_clues')),
            'hidden_facts': _norm_str_list(nd.get('hidden_facts')),
            'exits': nd.get('exits') if isinstance(nd.get('exits'), list) else [],
            'enemies': nd.get('enemies') if isinstance(nd.get('enemies'), list) else [],
        }
        # Sanitize/derive id.
        draft['id'] = draft['id'] or slugify(draft['location'] or 'new_scene')
        gm['new_scene_draft'] = draft

    if debug_reasons:
        dbg = gm.get('debug_notes')
        if not isinstance(dbg, str):
            dbg = ''
        reason_text = ','.join(debug_reasons)
        gm['debug_notes'] = (dbg + ' | ' if dbg else '') + reason_text

    return gm


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


def enforce_scene_momentum(gm: Dict[str, Any], *, session: Dict[str, Any], scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic enforcement of the Scene Momentum Rule.

    If a momentum beat is due but the model did not tag it, append a safe
    consequence/opportunity beat grounded in existing visible facts/exits.
    """
    if not isinstance(gm, dict):
        return gm
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return gm

    if not _scene_momentum_due(session, scene_id):
        return gm

    if _extract_scene_momentum_kind(gm):
        return gm

    gm = dict(gm)
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    kind = "consequence_or_opportunity"
    gm["tags"] = list(tags) + [f"{SCENE_MOMENTUM_TAG_PREFIX}{kind}"]

    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    loc = str(scene.get("location") or "").strip()

    options: list[str] = []
    if exits and isinstance(exits[0], dict):
        label = str(exits[0].get("label") or "").strip()
        if label:
            options.append(f"take the exit labeled “{label}”")
    for v in visible:
        if not isinstance(v, str):
            continue
        low = v.lower()
        if "notice board" in low or "noticeboard" in low:
            options.append("read the notice board closely for names, times, and requirements")
            break
    for v in visible:
        if not isinstance(v, str):
            continue
        low = v.lower()
        if "tavern" in low or "runner" in low or "rumor" in low or "rumour" in low:
            options.append("pull the tavern runner aside and buy one specific rumor")
            break
    if not options and visible:
        options.append("pick one detail in the scene and investigate it up close")
    if not options:
        options.append("choose a concrete next step and press it immediately")

    loc_phrase = f" in {loc}" if loc else ""
    opportunity = (
        "Consequence / Opportunity: the moment doesn’t wait for more small talk—"
        f"commit to one concrete move{loc_phrase}: "
        + "; or ".join(options[:2])
        + "."
    )
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    gm["player_facing_text"] = (txt.strip() + ("\n\n" if txt.strip() else "") + opportunity).strip()

    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + "scene_momentum:enforced_fallback"
    return gm


def _generic_phrase_replacement_sentence(
    *,
    label: str,
    location: str,
    npc_name: str,
    scene_visible_facts: List[str],
) -> str:
    loc = (location or "").strip()
    npc = (npc_name or "").strip()
    who = npc or "The local voice"
    loc_phrase = f" in {loc}" if loc else ""

    visible_low = " ".join(str(v).lower() for v in (scene_visible_facts or []) if isinstance(v, str))
    has_notice = ("notice board" in visible_low) or ("noticeboard" in visible_low)
    has_missing_patrol = "missing patrol" in visible_low
    has_tavern_runner = (
        ("tavern runner" in visible_low)
        or ("tavern" in visible_low and "runner" in visible_low)
        or ("rumor" in visible_low)
        or ("rumour" in visible_low)
    )
    has_refugees = "refugee" in visible_low

    if label == "in_this_city":
        if has_notice and has_missing_patrol:
            return f"{who}{loc_phrase} gestures to the notice board: taxes, curfews, and the missing patrol posting are the only things anyone is taking seriously."
        if has_notice:
            return f"{who}{loc_phrase} points you at the notice board—the posted taxes and curfews are the rules that actually matter here."
        return f"{who}{loc_phrase} keeps it specific: names, postings, and witnesses decide what happens next—not vague warnings."

    if label == "times_are_tough":
        if has_notice:
            return f"{who}{loc_phrase} doesn’t bother with platitudes—new taxes and curfews are posted, and enforcement is immediate."
        return f"{who}{loc_phrase} skips the sermon and looks for something actionable: a name, a place, or a consequence."

    if label == "trust_is_hard_to_come_by":
        leads: List[str] = []
        if has_notice:
            leads.append("a name off the notice board")
        if has_refugees:
            leads.append("a witness from the refugee line")
        if has_tavern_runner:
            leads.append("one specific rumor bought from the tavern runner")
        lead_phrase = "; or ".join(leads[:2]) if leads else "a named person or posted notice"
        return f"{who}{loc_phrase} makes it procedural, not moral: bring {lead_phrase}, and they can act without guessing."

    if label == "prove_yourself":
        leads2: List[str] = []
        if has_notice:
            leads2.append("a name off the notice board")
        if has_missing_patrol:
            leads2.append("a concrete detail tied to the missing patrol notice")
        if has_tavern_runner:
            leads2.append("one rumor with a source")
        if has_refugees:
            leads2.append("a witness who’ll say it out loud")
        lead_phrase2 = "; or ".join(leads2[:2]) if leads2 else "a concrete lead with a name and place"
        return f"{who}{loc_phrase} sets a clear bar: return with {lead_phrase2}, and the conversation changes immediately."

    # Fallback (should not happen).
    return f"{who}{loc_phrase} replaces the vague line with something concrete the player can act on right now."


def enforce_forbidden_generic_phrases(
    gm: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministically rewrite forbidden generic phrases into scene-anchored specificity.

    This pass rewrites only sentences that contain forbidden phrases, using
    existing visible facts + known NPC names. It never introduces hidden facts.
    """
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    hits = detect_forbidden_generic_phrases(txt)
    if not hits:
        return gm

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)
    npc_id = _active_interaction_target_id(session)
    npc_name = _resolve_npc_name(world, npc_id, scene_id)

    # Rewrite at sentence granularity to avoid awkward partial substitutions.
    paragraphs = [p for p in str(txt or "").split("\n\n")]
    rewritten_paras: List[str] = []
    for para in paragraphs:
        sents = [s for s in re.split(r"(?<=[.!?])\s+", para.strip()) if s]
        out_sents: List[str] = []
        for s in sents:
            matched_labels: List[str] = []
            for pattern, label in _FORBIDDEN_GENERIC_PHRASE_PATTERNS:
                if pattern.search(s):
                    matched_labels.append(label)
            if not matched_labels:
                out_sents.append(s)
                continue
            rep = _generic_phrase_replacement_sentence(
                label=matched_labels[0],
                location=location,
                npc_name=npc_name,
                scene_visible_facts=[str(v) for v in visible if isinstance(v, str)],
            )
            if rep and not rep.endswith((".", "!", "?", "…")):
                rep += "."
            out_sents.append(rep)
        rewritten_paras.append(" ".join(out_sents).strip())
    new_txt = "\n\n".join([p for p in rewritten_paras if p]).strip()

    if new_txt and new_txt != txt:
        gm["player_facing_text"] = new_txt
        tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
        gm["tags"] = list(tags) + ["forbidden_generic_rewrite"]
        dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
        gm["debug_notes"] = (dbg + " | " if dbg else "") + f"forbidden_generic_rewrite:{hits}"
    return gm


def enforce_no_validator_voice(
    gm: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any],
    player_text: str,
) -> Dict[str, Any]:
    """Deterministically remove system/validator wording from player-facing text."""
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    if not txt.strip():
        return gm

    hits = detect_validator_voice(txt)
    if not hits:
        return gm

    if _is_direct_player_question(player_text):
        gm = _apply_uncertainty_to_gm(
            gm,
            uncertainty=classify_uncertainty(player_text, scene_envelope=scene_envelope),
            reason=f"validator_voice_rewrite:{hits}",
            replace_text=True,
        )
        tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
        gm["tags"] = list(tags) + ["validator_voice_rewrite"]
        return gm

    clean_sentences = [
        sentence for sentence in _split_reply_sentences(txt)
        if not detect_validator_voice(sentence)
    ]
    rewritten = " ".join(clean_sentences).strip()
    if not rewritten or detect_validator_voice(rewritten):
        rewritten = _validator_voice_world_fallback(
            scene_envelope=scene_envelope,
            player_text=player_text,
        )

    gm["player_facing_text"] = rewritten.strip()
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    gm["tags"] = list(tags) + ["validator_voice_rewrite"]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + f"validator_voice_rewrite:{hits}"
    return gm


def scene_stall_check(
    *,
    gm_reply: Dict[str, Any],
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect when scene momentum is due but the reply leaves the scene static."""
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return {"applies": False, "ok": True, "reasons": []}
    if not _scene_momentum_due(session, scene_id):
        return {"applies": False, "ok": True, "reasons": []}
    if _extract_scene_momentum_kind(gm_reply):
        return {"applies": True, "ok": True, "reasons": []}
    return {
        "applies": True,
        "ok": False,
        "reasons": ["scene_stall:momentum_due_without_progress"],
    }


def detect_retry_failures(
    *,
    player_text: str,
    gm_reply: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    """Collect inspectable retry failures before deterministic enforcement."""
    if not isinstance(gm_reply, dict):
        return []
    reply_text = gm_reply.get("player_facing_text") if isinstance(gm_reply.get("player_facing_text"), str) else ""
    failures: List[Dict[str, Any]] = []

    validator_hits = detect_validator_voice(reply_text)
    if validator_hits:
        failures.append(
            {
                "failure_class": "validator_voice",
                "priority": RETRY_FAILURE_PRIORITY["validator_voice"],
                "reasons": validator_hits,
            }
        )

    question_rule = question_resolution_rule_check(player_text=player_text, gm_reply_text=reply_text)
    if question_rule.get("applies") and not question_rule.get("ok"):
        uncertainty_hint = classify_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        failures.append(
            {
                "failure_class": "unresolved_question",
                "priority": RETRY_FAILURE_PRIORITY["unresolved_question"],
                "reasons": list(question_rule.get("reasons") or []),
                "uncertainty_category": str(uncertainty_hint.get("category") or "").strip(),
            }
        )

    echo_reasons: List[str] = []
    if opening_sentence_echoes_player_input(reply_text, player_text):
        echo_reasons.append("echo_or_repetition:opening_overlap")
    if opening_sentence_overlaps_player_quote(reply_text, player_text):
        echo_reasons.append("echo_or_repetition:quoted_speech_overlap")
    echo_reasons.extend(detect_stock_warning_filler_repetition(reply_text))
    if echo_reasons:
        failures.append(
            {
                "failure_class": "echo_or_repetition",
                "priority": RETRY_FAILURE_PRIORITY["echo_or_repetition"],
                "reasons": echo_reasons,
            }
        )

    npc_contract = npc_response_contract_check(
        player_text=player_text,
        npc_reply_text=reply_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    if npc_contract.get("applies") and not npc_contract.get("ok"):
        failures.append(
            {
                "failure_class": "npc_contract_failure",
                "priority": RETRY_FAILURE_PRIORITY["npc_contract_failure"],
                "reasons": list(npc_contract.get("reasons") or []),
                "missing": list(npc_contract.get("missing") or []),
            }
        )

    scene_stall = scene_stall_check(gm_reply=gm_reply, session=session, scene_envelope=scene_envelope)
    if scene_stall.get("applies") and not scene_stall.get("ok"):
        failures.append(
            {
                "failure_class": "scene_stall",
                "priority": RETRY_FAILURE_PRIORITY["scene_stall"],
                "reasons": list(scene_stall.get("reasons") or []),
            }
        )

    forbidden_generic_hits = detect_forbidden_generic_phrases(reply_text)
    if forbidden_generic_hits:
        failures.append(
            {
                "failure_class": "forbidden_generic_phrase",
                "priority": RETRY_FAILURE_PRIORITY["forbidden_generic_phrase"],
                "reasons": forbidden_generic_hits,
            }
        )

    return failures


def apply_response_policy_enforcement(
    gm: Dict[str, Any],
    *,
    response_policy: Dict[str, Any],
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    discovered_clues: List[str] | None = None,
) -> Dict[str, Any]:
    """Apply deterministic post-generation enforcement in documented priority order."""
    if not isinstance(gm, dict):
        return gm

    out = dict(gm)
    policy = response_policy if isinstance(response_policy, dict) else {}

    for policy_key, _rule_name in RESPONSE_RULE_PRIORITY:
        if policy_key == "must_answer" and policy.get(policy_key, True):
            out = enforce_question_resolution_rule(
                out,
                player_text=player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            )
            continue

        if policy_key == "forbid_state_invention" and policy.get(policy_key, True):
            out = validate_gm_state_update(out, session, scene_envelope)
            continue

        if policy_key == "forbid_secret_leak" and policy.get(policy_key, True):
            out = guard_gm_output(out, scene_envelope, player_text, discovered_clues)
            continue

        if policy_key == "allow_partial_answer":
            continue

        if (
            policy_key == "diegetic_only"
            and policy.get(policy_key, True)
            and bool((policy.get("no_validator_voice") or {}).get("enabled", True))
        ):
            out = enforce_no_validator_voice(out, scene_envelope=scene_envelope, player_text=player_text)
            continue

        if policy_key == "prefer_scene_momentum" and policy.get(policy_key, True):
            out = enforce_scene_momentum(out, session=session, scene_envelope=scene_envelope)
            continue

        if policy_key == "prefer_specificity" and policy.get(policy_key, True):
            out = enforce_npc_response_contract(
                out,
                player_text=player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            )
            out = enforce_forbidden_generic_phrases(
                out,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
            )

    return out
