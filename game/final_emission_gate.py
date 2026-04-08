from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from game.exploration import NPC_PURSUIT_CONTACT_SESSION_KEY
from game.interaction_context import inspect as inspect_interaction_context
from game.narrative_authority import (
    narrative_authority_prefers_roll_prompt,
    narrative_authority_repair_hints,
    validate_narrative_authority,
    _BRANCH_FRAMING_RE,
    _HIDDEN_FACT_CERTAINTY_RE,
    _INTENT_CERTAINTY_RE,
    _ROLL_PROMPT_RE,
    _mask_dialogue_spans,
    _outcome_assertion_hits,
    _player_asks_intent_or_read,
    _sentence_has_hedge,
    _split_sentences,
    _STRONG_OUTCOME_ASSERTION_RE,
)
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
    _split_visibility_sentences,
)
from game.output_sanitizer import sanitize_player_facing_output
from game.social import (
    SOCIAL_KINDS,
    SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS,
    neutral_reply_speaker_grounding_bridge_line,
)
from game.social_exchange_emission import (
    _has_explicit_interruption_shape,
    build_final_strict_social_response,
    effective_strict_social_resolution_for_emission,
    interruption_cue_present_in_text,
    is_route_illegal_global_or_sanitizer_fallback_text,
    log_final_emission_decision,
    log_final_emission_trace,
    merged_player_prompt_for_gate,
    minimal_social_emergency_fallback_line,
    replacement_is_route_legal_social,
    strict_social_emission_will_apply,
    strict_social_ownership_terminal_fallback,
    strict_social_suppress_non_native_coercion_for_narration_beat,
    _npc_display_name_for_emission,
    _speaker_label,
)
from game.storage import get_scene_runtime
from game.leads import get_lead, normalize_lead
from game.scene_state_anchoring import validate_scene_state_anchoring


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


def _sanitize_output_text(text: str) -> str:
    if not text:
        return text

    text = text.replace("<br><br>", "\n\n")
    text = text.replace("<br />", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_terminal_punctuation(text: str) -> str:
    clean = _normalize_text(text).strip(" ,;")
    if not clean:
        return ""
    if not _has_terminal_punctuation(clean):
        clean += "."
    return clean


def _has_terminal_punctuation(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    if clean[-1] in ".!?":
        return True
    if clean[-1] in "\"')]}”’" and len(clean) > 1 and clean[-2] in ".!?":
        return True
    return False


def _capitalize_sentence_fragment(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    chars = list(clean)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.upper()
            break
    return "".join(chars)


_RESPONSE_TYPE_VALUES = {"dialogue", "answer", "action_outcome", "neutral_narration"}
_ANSWER_DIRECT_PATTERNS = (
    re.compile(r"\b(?:yes|no|none|nothing|nowhere|someone|somebody|everyone|nobody)\b", re.IGNORECASE),
    re.compile(r"\b(?:don'?t know|do not know|cannot say|can'?t say|that'?s all i(?:'ve| have) got)\b", re.IGNORECASE),
    re.compile(r"\b(?:requires? a check|calls? for a check|need a more concrete|need a concrete|not established yet)\b", re.IGNORECASE),
    re.compile(r"\b(?:in earshot|nearby npc presence|estimated distance|about \d+\s+feet)\b", re.IGNORECASE),
    re.compile(r"\b(?:is armed|does not appear armed|no one else is clearly in earshot)\b", re.IGNORECASE),
    re.compile(r"\b(?:roll|sleight of hand|stealth|perception|diplomacy|intimidate|bluff)\b", re.IGNORECASE),
    re.compile(r"\b(?:east|west|north|south)\b", re.IGNORECASE),
    re.compile(r"\b(?:road|lane|gate|pier|market|checkpoint|milestone|fold)\b", re.IGNORECASE),
)
_ANSWER_FILLER_PATTERNS = (
    re.compile(r"\bfor a breath\b", re.IGNORECASE),
    re.compile(r"\bthe scene holds\b", re.IGNORECASE),
    re.compile(r"\bvoices shift around you\b", re.IGNORECASE),
    re.compile(r"\brain beads on stone\b", re.IGNORECASE),
    re.compile(r"\bthe truth is still buried\b", re.IGNORECASE),
    re.compile(r"\bnothing in the scene points\b", re.IGNORECASE),
)
_ACTION_RESULT_PATTERNS = (
    re.compile(r"\b(?:find|found|notice|noticed|spot|spotted|discover|discovered|reveal|revealed|turns? up|yields?)\b", re.IGNORECASE),
    re.compile(r"\b(?:arrive|arrives|reach|reaches|move|moves|shift|shifts|change|changes|opens|closes)\b", re.IGNORECASE),
    re.compile(r"\b(?:nothing new|already searched|requires? a check|calls? for a check|meets resistance)\b", re.IGNORECASE),
    re.compile(r"\b(?:fails?|failed|succeeds?|succeeded|result|effect|immediate)\b", re.IGNORECASE),
    re.compile(r"\b(?:clue|trail|mark|trace|scene)\b", re.IGNORECASE),
)
_AGENCY_SUBSTITUTE_PATTERNS = (
    re.compile(r"\byou (?:think|reflect|hesitate|wonder)\b", re.IGNORECASE),
    re.compile(r"\byou merely\b", re.IGNORECASE),
    re.compile(r"\byou only\b", re.IGNORECASE),
)
_NON_HOSTILE_ESCALATION_PATTERNS = (
    re.compile(r"\b(?:attack|strike|stab|shoot|kill|murder|slash|lunge|rush)\b", re.IGNORECASE),
    re.compile(r"\b(?:grab|shove|slam|pin)\b", re.IGNORECASE),
    re.compile(r"\bthreaten(?:s|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bdraw(?:s|ing)?\s+(?:steel|a weapon|his weapon|her weapon|their weapon|a sword|his sword|her sword|their sword)\b", re.IGNORECASE),
)
_ACTION_STOPWORDS = frozenset(
    {
        "the",
        "that",
        "this",
        "with",
        "from",
        "into",
        "over",
        "under",
        "then",
        "your",
        "their",
        "them",
        "they",
        "there",
        "here",
        "about",
        "while",
        "through",
        "would",
        "could",
        "should",
        "just",
        "still",
        "have",
        "been",
        "were",
        "what",
        "where",
        "when",
        "which",
        "who",
    }
)


def _valid_response_type_contract(candidate: Any) -> Dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    required = str(candidate.get("required_response_type") or "").strip().lower()
    if required not in _RESPONSE_TYPE_VALUES:
        return None
    out = dict(candidate)
    out["required_response_type"] = required
    return out


def _resolve_response_type_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    response_policy = (
        gm_output.get("response_policy")
        if isinstance(gm_output, dict) and isinstance(gm_output.get("response_policy"), dict)
        else None
    )
    contract = _valid_response_type_contract((response_policy or {}).get("response_type_contract"))
    if contract:
        return contract, "response_policy"

    metadata = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    contract = _valid_response_type_contract(metadata.get("response_type_contract"))
    if contract:
        return contract, "resolution.metadata"

    debug_candidates: List[Any] = []
    if isinstance(gm_output, dict):
        debug_payload = gm_output.get("debug") if isinstance(gm_output.get("debug"), dict) else {}
        debug_candidates.append(debug_payload.get("response_type_contract"))
        debug_candidates.append(gm_output.get("response_type_contract"))
    if isinstance(session, dict):
        last_action_debug = session.get("last_action_debug") if isinstance(session.get("last_action_debug"), dict) else {}
        debug_candidates.append(last_action_debug.get("response_type_contract"))

    for candidate in debug_candidates:
        contract = _valid_response_type_contract(candidate)
        if contract:
            return contract, "debug"
    return None, None


def _last_player_input(
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    metadata = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    prompt = str(metadata.get("player_input") or "").strip()
    if prompt:
        return prompt
    prompt = str((resolution or {}).get("prompt") or "").strip()
    if prompt:
        return prompt
    lad = session.get("last_action_debug") if isinstance(session, dict) and isinstance(session.get("last_action_debug"), dict) else {}
    prompt = str(lad.get("player_input") or "").strip()
    if prompt:
        return prompt
    rt = get_scene_runtime(session if isinstance(session, dict) else None, scene_id)
    return str((rt or {}).get("last_player_action_text") or "").strip()


def _content_tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z']+", str(text or "").lower())
        if len(tok) >= 4 and tok not in _ACTION_STOPWORDS
    }


def candidate_satisfies_dialogue_contract(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> tuple[bool, List[str]]:
    clean = _normalize_text(text)
    if not clean:
        return False, ["dialogue_empty"]
    # Bracket-only production markers (e.g. "[Narration]") are non-replaced stubs; not generic scene fallback.
    if re.fullmatch(r"\[[^\]]{1,120}\]", clean.strip()):
        return True, []
    if is_route_illegal_global_or_sanitizer_fallback_text(clean):
        return False, ["dialogue_generic_fallback_text"]
    if isinstance(resolution, dict) and replacement_is_route_legal_social(
        clean,
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    ):
        return True, []
    low = clean.lower()
    if '"' in clean or re.search(
        r"\b(?:says|replies|asks|mutters|whispers|frowns|grimaces|shakes their head|starts to answer|glances past you)\b",
        low,
    ):
        return True, []
    return False, ["dialogue_not_in_character"]


def candidate_satisfies_answer_contract(text: str) -> tuple[bool, List[str]]:
    clean = _normalize_text(text)
    if not clean:
        return False, ["answer_empty"]
    low = clean.lower()
    if any(p.search(clean) for p in _ANSWER_FILLER_PATTERNS):
        return False, ["answer_is_scene_prose"]
    if clean.endswith("?"):
        return False, ["answer_is_another_question"]
    if any(p.search(clean) for p in _ANSWER_DIRECT_PATTERNS):
        return True, []
    words = re.findall(r"[A-Za-z']+", clean)
    if len(words) < 4:
        return False, ["answer_too_thin"]
    if '"' in clean and not re.search(r"\b(?:yes|no|know|heard|names|road|lane|gate|check|feet)\b", low):
        return False, ["answer_collapses_into_banter"]
    if re.search(r"\b(?:there is|there are|it is|they are|he is|she is|estimated|about \d+)\b", low):
        return True, []
    if re.search(r"\b(?:east|west|north|south|road|lane|gate|pier|market|checkpoint|milestone|fold)\b", low):
        return True, []
    return False, ["answer_not_direct"]


def candidate_satisfies_action_outcome_contract(
    text: str,
    *,
    player_input: str,
) -> tuple[bool, List[str]]:
    clean = _normalize_text(text)
    if not clean:
        return False, ["action_outcome_empty"]
    low = clean.lower()
    if any(p.search(clean) for p in _ANSWER_FILLER_PATTERNS):
        return False, ["action_outcome_is_scene_prose"]
    if '"' in clean and "you " not in low and "your " not in low:
        return False, ["action_outcome_replaced_by_dialogue"]
    has_ack = bool(re.search(r"\b(?:you|your)\b", low))
    if not has_ack:
        has_ack = bool(_content_tokens(player_input) & _content_tokens(clean))
    if not has_ack:
        return False, ["action_outcome_missing_attempt_acknowledgement"]
    if any(p.search(clean) for p in _AGENCY_SUBSTITUTE_PATTERNS):
        return False, ["action_outcome_substitutes_internal_reflection"]
    if not any(p.search(clean) for p in _ACTION_RESULT_PATTERNS):
        return False, ["action_outcome_missing_result"]
    return True, []


def candidate_violates_non_hostile_escalation_contract(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    return any(p.search(clean) for p in _NON_HOSTILE_ESCALATION_PATTERNS)


def _social_fallback_resolution(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict):
        return resolution
    if not active_interlocutor or not isinstance(world, dict):
        return None
    return {
        "kind": "question",
        "social": {
            "npc_id": active_interlocutor,
            "npc_name": _npc_display_name_for_emission(world, scene_id, active_interlocutor),
            "social_intent_class": "social_exchange",
        },
    }


def _to_second_person_action_clause(player_input: str, resolution: Dict[str, Any] | None) -> str:
    raw = _normalize_text(player_input or str((resolution or {}).get("prompt") or "")).rstrip(".!?")
    if not raw:
        return "You act"
    low = raw.lower()
    if low.startswith("you "):
        return _capitalize_sentence_fragment(raw)
    if low.startswith("i am "):
        return f"You are {raw[5:]}"
    if low.startswith("i'm "):
        return f"You are {raw[4:]}"
    if low.startswith("i "):
        return f"You {raw[2:]}"
    if re.match(
        r"^(?:go|move|travel|investigate|inspect|search|open|close|take|grab|climb|follow|approach|look|examine|head|ask|speak|draw|attack|strike|cast|use|push|pull|listen|wait)\b",
        low,
    ):
        return f"You {raw}"
    return "You act on that move"


def _action_result_summary(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "the scene answers with an immediate change"
    state_changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    check_request = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    kind = str(resolution.get("kind") or "").strip().lower()
    if bool(resolution.get("resolved_transition")) or state_changes.get("scene_transition_occurred") or state_changes.get("arrived_at_scene"):
        return "the scene shifts with that movement"
    if state_changes.get("already_searched"):
        if kind in {"investigate", "observe", "search"}:
            return "the search turns up nothing new"
        return "the attempt turns up nothing new"
    if state_changes.get("clue_revealed") or resolution.get("clue_id") or resolution.get("discovered_clues"):
        return "you turn up a concrete clue"
    if state_changes.get("skill_check_failed"):
        return "the attempt catches and fails to land cleanly"
    if bool(resolution.get("requires_check")) or bool(check_request.get("requires_check")):
        return "the attempt now calls for a check"
    if resolution.get("success") is False:
        return "the attempt meets resistance"
    if resolution.get("success") is True:
        return "the attempt produces an immediate result"
    if kind in {"investigate", "observe"}:
        return "you get an immediate read on what is there"
    if kind in {"travel", "scene_transition"}:
        return "your position in the scene changes"
    return "the situation answers that move right away"


def _minimal_answer_contract_repair(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> str | None:
    social_resolution = _social_fallback_resolution(
        resolution=resolution,
        active_interlocutor=active_interlocutor,
        world=world,
        scene_id=scene_id,
    )
    if isinstance(social_resolution, dict):
        return minimal_social_emergency_fallback_line(social_resolution)
    check_request = resolution.get("check_request") if isinstance(resolution, dict) and isinstance(resolution.get("check_request"), dict) else {}
    prompt = _normalize_terminal_punctuation(str(check_request.get("player_prompt") or "").strip())
    if prompt:
        return prompt
    adjudication = resolution.get("adjudication") if isinstance(resolution, dict) and isinstance(resolution.get("adjudication"), dict) else {}
    answer_type = str(adjudication.get("answer_type") or "").strip().lower()
    if answer_type == "needs_concrete_action":
        return "You need a more concrete in-scene action or target before that can be answered."
    if answer_type == "check_required" or bool((resolution or {}).get("requires_check")):
        return "That cannot be answered cleanly until the required check is resolved."
    return "No direct answer is established from the current state yet."


def _minimal_action_outcome_contract_repair(
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
) -> str:
    action_clause = _to_second_person_action_clause(player_input, resolution)
    result_clause = _action_result_summary(resolution)
    return _normalize_terminal_punctuation(f"{action_clause}, and {result_clause}")


def _default_response_type_debug(contract: Dict[str, Any] | None, source: str | None) -> Dict[str, Any]:
    return {
        "response_type_required": str((contract or {}).get("required_response_type") or "") or None,
        "response_type_contract_source": source,
        "response_type_candidate_ok": None if not contract else True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def _merge_response_type_meta(meta: Dict[str, Any], debug: Dict[str, Any]) -> None:
    meta.update(
        {
            "response_type_required": debug.get("response_type_required"),
            "response_type_contract_source": debug.get("response_type_contract_source"),
            "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
            "response_type_repair_used": debug.get("response_type_repair_used"),
            "response_type_repair_kind": debug.get("response_type_repair_kind"),
            "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
            "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
        }
    )


def _response_type_decision_payload(debug: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "response_type_required": debug.get("response_type_required"),
        "response_type_contract_source": debug.get("response_type_contract_source"),
        "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
        "response_type_repair_used": debug.get("response_type_repair_used"),
        "response_type_repair_kind": debug.get("response_type_repair_kind"),
        "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
        "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
    }


# --- Answer completeness (response_policy.answer_completeness) -----------------

_AMBIENT_OPENING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(?:the\s+)?(?:mist|rain|dawn|dusk|evening|morning|square|crowd|torchlight)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:for\s+a\s+(?:moment|breath))\b", re.IGNORECASE),
    re.compile(r"^\s*voices\s+", re.IGNORECASE),
)
_QUESTION_FIRST_LEAD_PATTERN = re.compile(
    r"^\s*(?:what|where|when|why|how|who|which|whose)\b(?![^?]*\b(?:is|are|was|were)\b[^?]{0,24}\?)",
    re.IGNORECASE,
)
_QUESTION_BACKEND_PATTERN = re.compile(
    r"\b(?:do you|did you|can you|could you|would you|have you|are you)\b",
    re.IGNORECASE,
)
_DEFLECTIVE_OPENING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhy do you ask\b", re.IGNORECASE),
    re.compile(r"\bwho (?:wants|told you)\b", re.IGNORECASE),
    re.compile(r"\bwhat makes you think\b", re.IGNORECASE),
    re.compile(r"\bwhere is this going\b", re.IGNORECASE),
)
_GENERIC_NONANSWER_SNIPPET = re.compile(
    r"\b(?:hard to say|it depends|depends on|maybe|could be anyone|people (?:talk|whisper|say)|who knows)\b",
    re.IGNORECASE,
)
_BOUNDED_PARTIAL_REASON_MARKERS: Dict[str, tuple[re.Pattern[str], ...]] = {
    "uncertainty": (
        re.compile(r"\b(?:unclear|not sure|rumor|hearsay|might be|could be)\b", re.IGNORECASE),
        re.compile(r"\b(?:can'?t pin|can'?t say for certain)\b", re.IGNORECASE),
    ),
    "lack_of_knowledge": (
        re.compile(r"\b(?:don'?t know|do not know|never heard|wasn'?t there|not on duty)\b", re.IGNORECASE),
        re.compile(r"\bno names?\b", re.IGNORECASE),
    ),
    "gated_information": (
        re.compile(r"\b(?:won'?t say|can'?t say here|not (?:here|now)|keep(?:ing)? (?:quiet|mum)|sworn\b|under orders)\b", re.IGNORECASE),
        re.compile(r"\b(?:if you want that|you(?:'|’)ll need)\b", re.IGNORECASE),
    ),
}
_NEXT_LEAD_SNIPPET = re.compile(
    r"\b(?:ask|check|ledger|captain|clerk|report|barracks|watchhouse|notice|commander|sergeant)\b",
    re.IGNORECASE,
)


def _resolve_answer_completeness_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if not isinstance(pol, dict):
        return None
    ac = pol.get("answer_completeness")
    return ac if isinstance(ac, dict) else None


def _split_sentences_answer_complete(text: str) -> List[str]:
    t = _normalize_text(text)
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if p.strip()]


def _opening_segment(text: str) -> str:
    sents = _split_sentences_answer_complete(text)
    return sents[0] if sents else _normalize_text(text)


def _contract_bool(contract: Dict[str, Any], key: str) -> bool:
    return bool(contract.get(key))


def _partial_reason_in_text(
    text: str,
    allowed: List[str],
) -> str | None:
    allowed_set = {str(x).strip().lower() for x in allowed if isinstance(x, str) and str(x).strip()}
    if not allowed_set:
        return None
    for reason, patterns in _BOUNDED_PARTIAL_REASON_MARKERS.items():
        if reason not in allowed_set:
            continue
        if any(p.search(text) for p in patterns):
            return reason
    return None


def _concrete_payload_for_kinds(text: str, kinds: List[str]) -> bool:
    if not kinds:
        return True
    low = str(text or "").lower()
    quotes = bool(re.search(r'["“”][^"”]{3,}["“”]', str(text or "")))
    for kind in kinds:
        k = str(kind or "").strip().lower()
        if k == "name" and (quotes or re.search(r"\b(?:master|captain|sergeant|clerk|guard)\b", low)):
            return True
        if k == "place" and re.search(
            r"\b(?:east|west|north|south|road|lane|gate|market|square|pier|dock|checkpoint|fold|mill)\b",
            low,
        ):
            return True
        if k == "direction" and re.search(r"\b(?:east|west|north|south)\b", low):
            return True
        if k == "fact" and (
            re.search(r"\b(?:there is|there are|it is|they are|he is|she is|was|were)\b", low)
            or re.search(r"\b\d+\s*(?:feet|yards|miles|silver|gold|copper|coppers)\b", low)
        ):
            return True
        if k == "condition" and re.search(
            r"\b(?:if|until|once|unless|after|before|when you|sworn|ordered|quiet)\b",
            low,
        ):
            return True
        if k == "next_lead" and _NEXT_LEAD_SNIPPET.search(str(text or "")):
            return True
    return False


def _npc_voice_substantive_carriage(text: str, *, opening: str, inspect_window: int = 320) -> bool:
    chunk = (str(text or ""))[: max(inspect_window, 1)]
    if re.search(r'["“”][^"”]{6,}["“”]', chunk):
        return True
    if re.search(
        r"\b(?:says|replies|answers|mutters|spits|snaps|answers you)\b",
        chunk,
        re.IGNORECASE,
    ):
        return True
    if '"' in opening and len(opening) >= 12:
        return True
    return False


def _opening_is_question_back(opening: str) -> bool:
    o = str(opening or "").strip()
    if not o:
        return False
    if o.rstrip().endswith("?"):
        return True
    if _QUESTION_FIRST_LEAD_PATTERN.search(o) and not re.search(r"\bwhat i know\b", o, re.IGNORECASE):
        return True
    if _QUESTION_BACKEND_PATTERN.search(o) and o.rstrip().endswith("?"):
        return True
    return False


def _opening_is_scene_color(opening: str) -> bool:
    if any(p.search(str(opening or "")) for p in _AMBIENT_OPENING_PATTERNS):
        return True
    if any(p.search(str(opening or "")) for p in _ANSWER_FILLER_PATTERNS):
        return True
    return False


def _sentence_substantive_for_frontload(sentence: str, *, contract: Dict[str, Any]) -> bool:
    s = str(sentence or "").strip()
    if not s or _opening_is_question_back(s):
        return False
    if any(p.search(s) for p in _ANSWER_FILLER_PATTERNS):
        return False
    ok, _reasons = candidate_satisfies_answer_contract(s)
    if ok:
        return True
    low = s.lower()
    if re.search(r"\b(?:yes|no)\b", low) and len(s.split()) >= 2:
        return True
    if _concrete_payload_for_kinds(s, list(contract.get("concrete_payload_any_of") or [])):
        return True
    if _partial_reason_in_text(s, list(contract.get("allowed_partial_reasons") or [])):
        return True
    return False


def validate_answer_completeness(
    emitted_text: str,
    contract: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic validation against ``response_policy.answer_completeness`` (no LLM)."""
    base: Dict[str, Any] = {
        "checked": False,
        "passed": True,
        "answered_directly": False,
        "bounded_partial": False,
        "partial_reason_detected": None,
        "deflective_opening": False,
        "generic_nonanswer": False,
        "question_first_violation": False,
        "filler_before_answer": False,
        "concrete_payload_present": False,
        "direct_answer_found_later": False,
        "failure_reasons": [],
        "answer_completeness_expected_voice": None,
    }
    if not isinstance(contract, dict):
        return base
    enabled = _contract_bool(contract, "enabled")
    answer_required = _contract_bool(contract, "answer_required")
    base["answer_completeness_expected_voice"] = str(contract.get("expected_voice") or "").strip().lower() or None
    if not enabled or not answer_required:
        return base

    base["checked"] = True
    text = _normalize_text(emitted_text)
    if not text:
        base["passed"] = False
        base["failure_reasons"] = ["empty_emitted_text"]
        return base

    kinds = [str(k) for k in (contract.get("concrete_payload_any_of") or []) if str(k).strip()]
    base["concrete_payload_present"] = _concrete_payload_for_kinds(text, kinds)
    opening = _opening_segment(text)
    sentences = _split_sentences_answer_complete(text)

    must_first = _contract_bool(contract, "answer_must_come_first")
    forbid_deflection = _contract_bool(contract, "forbid_deflection")
    forbid_generic = _contract_bool(contract, "forbid_generic_nonanswer")
    require_payload = _contract_bool(contract, "require_concrete_payload")
    exp_shape = str(contract.get("expected_answer_shape") or "").strip().lower()
    allowed_reasons = [str(x) for x in (contract.get("allowed_partial_reasons") or []) if str(x).strip()]
    partial_detected = _partial_reason_in_text(text, allowed_reasons)

    exp_voice = str(contract.get("expected_voice") or "").strip().lower()
    soc = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    gate_line = str(soc.get("information_gate") or "").strip()
    gated_resolution = bool(soc.get("gated_information")) or bool(gate_line)

    opening_direct_ok, _ = candidate_satisfies_answer_contract(opening) if opening else (False, [])
    if opening_direct_ok:
        base["answered_directly"] = True
    elif exp_shape == "refusal_with_reason" and _partial_reason_in_text(
        opening, ["gated_information", "lack_of_knowledge", "uncertainty"]
    ):
        base["answered_directly"] = True
    elif re.search(r"\b(?:won'?t|refuse|not (?:here|now))\b", opening, re.IGNORECASE) and '"' in opening:
        base["answered_directly"] = True

    bounded = bool(
        partial_detected
        or exp_shape == "bounded_partial"
        or (gated_resolution and _partial_reason_in_text(text, list(allowed_reasons)))
    )
    base["bounded_partial"] = bounded
    base["partial_reason_detected"] = partial_detected

    allowed_lc = {str(x).strip().lower() for x in allowed_reasons if str(x).strip()}

    def opening_ok() -> bool:
        if base["answered_directly"]:
            return True
        if bounded and partial_detected and partial_detected in allowed_lc:
            return True
        if bounded and exp_shape == "refusal_with_reason" and bool(partial_detected):
            return True
        return False

    direct_later = False
    if len(sentences) > 1:
        for sent in sentences[1:]:
            if _sentence_substantive_for_frontload(sent, contract=contract):
                direct_later = True
                break
    base["direct_answer_found_later"] = direct_later

    if must_first:
        ob = opening
        base["question_first_violation"] = _opening_is_question_back(ob)
        base["deflective_opening"] = any(p.search(ob) for p in _DEFLECTIVE_OPENING_PATTERNS)
        base["filler_before_answer"] = _opening_is_scene_color(ob) and not opening_ok()
        if _GENERIC_NONANSWER_SNIPPET.search(ob) and not base["concrete_payload_present"]:
            base["generic_nonanswer"] = True

    if (
        exp_voice == "npc"
        and not _npc_voice_substantive_carriage(text, opening=opening)
        and not base["answered_directly"]
        and not opening_ok()
    ):
        base["failure_reasons"].append("npc_voice_missing_substantive_carriage")

    if (
        gated_resolution
        and _partial_reason_in_text(text, ["gated_information"]) is None
        and re.search(r"\b(?:can'?t say|won'?t say|not (?:here|at liberty))\b", text, re.IGNORECASE)
        and not gate_line
        and not _NEXT_LEAD_SNIPPET.search(text)
    ):
        base["failure_reasons"].append("gated_without_named_boundary")

    if must_first and not opening_ok():
        if base["question_first_violation"]:
            base["failure_reasons"].append("opening_question_before_answer")
        if base["filler_before_answer"]:
            base["failure_reasons"].append("filler_or_ambient_before_answer")
        if forbid_deflection and base["deflective_opening"]:
            base["failure_reasons"].append("deflective_opening")
        if forbid_generic and base["generic_nonanswer"]:
            base["failure_reasons"].append("generic_nonanswer")
        if direct_later:
            base["failure_reasons"].append("direct_answer_not_frontloaded")

    if require_payload and not base["concrete_payload_present"]:
        partial_ok = bool(partial_detected and partial_detected in allowed_lc)
        if not partial_ok and not (bounded and exp_shape == "bounded_partial"):
            base["failure_reasons"].append("missing_concrete_payload")

    if partial_detected and partial_detected not in allowed_lc:
        base["failure_reasons"].append("partial_reason_not_allowed")
        base["bounded_partial"] = False

    if (
        bounded
        and partial_detected
        and partial_detected in allowed_lc
        and require_payload
        and not base["concrete_payload_present"]
        and exp_shape == "bounded_partial"
        and partial_detected != "lack_of_knowledge"
    ):
        base["failure_reasons"].append("bounded_partial_without_concrete_anchor")

    base["failure_reasons"] = list(dict.fromkeys(str(r) for r in base["failure_reasons"] if r))
    base["passed"] = not bool(base["failure_reasons"])
    return base


def inspect_answer_completeness_failure(result: Dict[str, Any]) -> Dict[str, Any]:
    """Structured inspect helper for logging / debugging."""
    if not isinstance(result, dict):
        return {"failed": False}
    if result.get("passed") is not False:
        return {"failed": False}
    return {
        "failed": True,
        "failure_reasons": list(result.get("failure_reasons") or []),
        "partial_reason_detected": result.get("partial_reason_detected"),
        "question_first_violation": bool(result.get("question_first_violation")),
        "deflective_opening": bool(result.get("deflective_opening")),
    }


def _skip_answer_completeness_layer(
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    """Return skip reason, or None when the layer should run."""
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not strict_social_details:
        return None
    if strict_social_details.get("used_internal_fallback"):
        return "strict_social_authoritative_internal_fallback"
    if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
        return "strict_social_ownership_terminal_repair"
    fe = str(strict_social_details.get("final_emitted_source") or "")
    if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
        if _strict_social_answer_pressure_ac_contract_active(gm_output):
            return None
        return "strict_social_structured_or_bridge_source"
    return None


def _repair_answer_completeness_minimal(
    text: str,
    validation: Dict[str, Any],
    contract: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    """Reorder or compress existing sentences only; no new facts."""
    sentences = _split_sentences_answer_complete(text)
    exp_shape = str(contract.get("expected_answer_shape") or "").strip().lower()
    exp_voice = str(contract.get("expected_voice") or "").strip().lower()
    soc = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    gate_line = str(soc.get("information_gate") or "").strip()
    partial_now = validation.get("partial_reason_detected")

    if validation.get("direct_answer_found_later") and len(sentences) > 1:
        pick: str | None = None
        pick_idx = -1
        for idx, sent in enumerate(sentences):
            if idx == 0:
                continue
            if _sentence_substantive_for_frontload(sent, contract=contract):
                pick = sent
                pick_idx = idx
                break
        if pick and pick_idx > 0:
            rest = sentences[:pick_idx] + sentences[pick_idx + 1 :]
            merged = _normalize_terminal_punctuation(pick) + " " + " ".join(
                _normalize_terminal_punctuation(s) for s in rest if s
            )
            return _normalize_text(merged), "frontload_direct_answer"

    reason_sents: List[str] = []
    partial_sents: List[str] = []
    lead_sents: List[str] = []
    for sent in sentences:
        if _partial_reason_in_text(sent, list(contract.get("allowed_partial_reasons") or [])):
            reason_sents.append(sent)
        if _concrete_payload_for_kinds(sent, list(contract.get("concrete_payload_any_of") or [])):
            partial_sents.append(sent)
        if _NEXT_LEAD_SNIPPET.search(sent):
            lead_sents.append(sent)

    if exp_shape in {"bounded_partial", "refusal_with_reason"} or partial_now:
        ordered: List[str] = []
        if partial_sents:
            ordered.append(partial_sents[0])
        if reason_sents:
            ordered.append(reason_sents[0])
        if lead_sents:
            ordered.append(lead_sents[0])
        if len(ordered) >= 2:
            tail_pool = [s for s in sentences if s not in ordered]
            body = " ".join(_normalize_terminal_punctuation(s) for s in ordered + tail_pool if s)
            return _normalize_text(body), "normalize_bounded_partial_order"

    if partial_now == "gated_information" or soc.get("gated_information") or gate_line:
        boundary = gate_line
        if not boundary:
            m = re.search(
                r"\b(?:orders|sworn|quiet|here|now|captain|command)\b[^.!?]{0,80}",
                text,
                re.IGNORECASE,
            )
            if m:
                boundary = _normalize_text(m.group(0))
        nucleus = sentences[0] if sentences else text
        if boundary and nucleus and boundary.lower() not in nucleus.lower():
            glue = _normalize_terminal_punctuation(f"{nucleus} ({boundary}).")
            rest = " ".join(sentences[1:] if len(sentences) > 1 else [])
            if rest:
                return _normalize_text(f"{glue} {rest}"), "surface_gated_boundary"
        if gate_line:
            head = sentences[0] if sentences else text
            return _normalize_text(f"{head.rstrip('.!?')}—{gate_line}."), "inject_resolution_gate_phrase"

    if exp_voice == "npc" and partial_now == "lack_of_knowledge":
        lead = next((s for s in lead_sents), "")
        head0 = sentences[0] if sentences else text
        if lead:
            pack = _normalize_terminal_punctuation(head0) + " " + _normalize_terminal_punctuation(lead)
            return _normalize_text(pack), "npc_ignorance_pair_compress"

    return None, None


def _apply_answer_completeness_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = _resolve_answer_completeness_contract(gm_output)
    skip = _skip_answer_completeness_layer(
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        gm_output=gm_output,
    )
    meta: Dict[str, Any] = {
        "answer_completeness_checked": False,
        "answer_completeness_failed": False,
        "answer_completeness_failure_reasons": [],
        "answer_completeness_repaired": False,
        "answer_completeness_repair_mode": None,
        "answer_completeness_expected_voice": None,
        "answer_completeness_skip_reason": skip,
    }
    if skip or not isinstance(contract, dict):
        return text, meta, []

    v0 = validate_answer_completeness(text, contract, resolution=resolution)
    meta["answer_completeness_checked"] = bool(v0.get("checked"))
    meta["answer_completeness_expected_voice"] = v0.get("answer_completeness_expected_voice")
    if not v0.get("checked"):
        return text, meta, []

    if v0.get("passed"):
        return text, meta, []

    meta["answer_completeness_failed"] = True
    meta["answer_completeness_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_answer_completeness_minimal(
        text,
        v0,
        contract,
        resolution=resolution,
    )
    if repaired:
        v1 = validate_answer_completeness(repaired, contract, resolution=resolution)
        if v1.get("passed"):
            meta["answer_completeness_repaired"] = True
            meta["answer_completeness_repair_mode"] = mode
            meta["answer_completeness_failed"] = False
            meta["answer_completeness_failure_reasons"] = []
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("answer_completeness_unsatisfied_after_repair")
    meta["answer_completeness_failed"] = True
    return text, meta, extra


def _merge_answer_completeness_meta(meta: Dict[str, Any], ac_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "answer_completeness_checked": bool(ac_dbg.get("answer_completeness_checked")),
            "answer_completeness_failed": bool(ac_dbg.get("answer_completeness_failed")),
            "answer_completeness_failure_reasons": list(ac_dbg.get("answer_completeness_failure_reasons") or []),
            "answer_completeness_repaired": bool(ac_dbg.get("answer_completeness_repaired")),
            "answer_completeness_repair_mode": ac_dbg.get("answer_completeness_repair_mode"),
            "answer_completeness_expected_voice": ac_dbg.get("answer_completeness_expected_voice"),
            "answer_completeness_skip_reason": ac_dbg.get("answer_completeness_skip_reason"),
        }
    )


# --- Response delta (response_policy.response_delta) ---------------------------


def _default_response_delta_meta() -> Dict[str, Any]:
    return {
        "response_delta_checked": False,
        "response_delta_failed": False,
        "response_delta_failure_reasons": [],
        "response_delta_repaired": False,
        "response_delta_repair_mode": None,
        "response_delta_kind_detected": None,
        "response_delta_echo_overlap_ratio": None,
        "response_delta_skip_reason": None,
        "response_delta_trigger_source": None,
    }


_RESPONSE_DELTA_STOPWORDS: frozenset[str] = frozenset(
    {
        "what",
        "where",
        "when",
        "why",
        "how",
        "who",
        "which",
        "that",
        "this",
        "these",
        "those",
        "with",
        "from",
        "into",
        "about",
        "there",
        "here",
        "they",
        "them",
        "their",
        "then",
        "than",
        "have",
        "has",
        "had",
        "been",
        "were",
        "was",
        "are",
        "is",
        "not",
        "but",
        "and",
        "for",
        "the",
        "you",
        "your",
        "very",
        "just",
        "only",
        "also",
        "some",
        "such",
        "more",
        "most",
        "much",
        "many",
        "like",
        "well",
        "still",
        "even",
        "back",
        "over",
        "after",
        "before",
        "once",
        "upon",
    }
)

_RD_TOKEN_RE = re.compile(r"[a-z0-9']{4,}")

_CONSEQUENCE_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:so|therefore|which meant|which means|as a result)\b", re.IGNORECASE),
    re.compile(r"\b(?:after that|from that|that left|led to|meant that)\b", re.IGNORECASE),
)
_REFINEMENT_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:exactly|precisely|specifically|at least|at most)\b", re.IGNORECASE),
    re.compile(r"\brather than\b", re.IGNORECASE),
    re.compile(r"\bnot\b.{3,48}\bbut\b", re.IGNORECASE | re.DOTALL),
)
_CLARIFIED_UNCERTAINTY_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:can'?t pin|can'?t say for certain|unclear whether|don'?t know if)\b", re.IGNORECASE),
    re.compile(r"\b(?:might be|could be|as far as (?:i|we) know)\b", re.IGNORECASE),
    re.compile(r"\b(?:no names?\b|never heard\b|wasn'?t on duty)\b", re.IGNORECASE),
)


def _response_delta_snippet_substantive(snippet: str) -> bool:
    """Match ``prompt_context._prior_answer_snippet_substantive`` for defensive skips."""
    s = " ".join(str(snippet or "").strip().split())
    if len(s) < 12:
        return False
    words = s.split()
    if len(words) < 2 and len(s) < 36:
        return False
    low = s.lower()
    if low in {"yes.", "no.", "ok.", "okay.", "nope.", "yeah.", "sure."}:
        return False
    return True


def _response_delta_tokens(text: str) -> List[str]:
    low = re.sub(r"[^a-z0-9'\s]+", " ", str(text or "").lower())
    return [t for t in _RD_TOKEN_RE.findall(low) if t not in _RESPONSE_DELTA_STOPWORDS]


def _response_delta_token_overlap_ratio(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    return float(inter) / float(max(len(sa), len(sb)))


def _resolve_response_delta_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if not isinstance(pol, dict):
        return None
    rd = pol.get("response_delta")
    return rd if isinstance(rd, dict) else None


def _strict_social_answer_pressure_ac_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when prompt_context activated answer-completeness for strict-social answer-pressure (Block 1)."""
    ac = _resolve_answer_completeness_contract(gm_output)
    if not isinstance(ac, dict):
        return False
    if not _contract_bool(ac, "enabled") or not _contract_bool(ac, "answer_required"):
        return False
    trace = ac.get("trace") if isinstance(ac.get("trace"), dict) else {}
    return bool(trace.get("strict_social_answer_seek_override"))


def _strict_social_answer_pressure_rd_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when response_delta is enabled with strict_social_answer_pressure trigger (Block 1)."""
    rd = _resolve_response_delta_contract(gm_output)
    if not isinstance(rd, dict) or not _contract_bool(rd, "enabled"):
        return False
    ts = str(rd.get("trigger_source") or "").strip()
    if ts == "strict_social_answer_pressure":
        return True
    tr = rd.get("trace") if isinstance(rd.get("trace"), dict) else {}
    return str(tr.get("trigger_source") or "").strip() == "strict_social_answer_pressure"


def _clue_text_for_spoken_cash_out(session: Dict[str, Any], clue_id: str | None) -> str:
    if not clue_id or not isinstance(session, dict):
        return ""
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    entry = ck.get(str(clue_id).strip())
    if not isinstance(entry, dict):
        return ""
    t = entry.get("text")
    return str(t).strip()[:400] if isinstance(t, str) and t.strip() else ""


def _lead_row_phrase_for_spoken_cash_out(session: Dict[str, Any], lead_id: str | None) -> str:
    if not lead_id:
        return ""
    row = get_lead(session, lead_id)
    if not isinstance(row, dict):
        return ""
    ld = normalize_lead(dict(row))
    for key in ("next_step", "summary", "title"):
        v = str(ld.get(key) or "").strip()
        if len(v) >= 6:
            return v[:400]
    return ""


def _refinement_phrase_for_lead_or_clue_id(session: Dict[str, Any], lead_or_clue_id: str | None) -> str:
    """Non-inventive phrase: prefer clue text, then registry row, then registry row matched by evidence clue id."""
    cid = str(lead_or_clue_id or "").strip()
    if not cid or not isinstance(session, dict):
        return ""
    t = _clue_text_for_spoken_cash_out(session, cid)
    if t:
        return t
    lp = _lead_row_phrase_for_spoken_cash_out(session, cid)
    if lp:
        return lp
    reg = session.get("lead_registry")
    if not isinstance(reg, dict):
        return ""
    for row in reg.values():
        if not isinstance(row, dict):
            continue
        ev = row.get("evidence_clue_ids") if isinstance(row.get("evidence_clue_ids"), list) else []
        evs = {str(x).strip() for x in ev if x}
        if cid not in evs:
            continue
        ld = normalize_lead(dict(row))
        for key in ("title", "summary", "next_step"):
            v = str(ld.get(key) or "").strip()
            if len(v) >= 6:
                return v[:400]
    return ""


def _topic_press_context_tokens(resolution: Dict[str, Any] | None) -> set[str]:
    toks: set[str] = set()
    if not isinstance(resolution, dict):
        return toks
    toks |= _content_tokens(str(resolution.get("prompt") or "").lower())
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    tr = soc.get("topic_revealed") if isinstance(soc.get("topic_revealed"), dict) else {}
    for key in ("title", "summary", "label", "topic_id"):
        toks |= _content_tokens(str(tr.get(key) or "").lower())
    return {t for t in toks if len(t) >= 4}


def _refinement_relevant_to_answer_pressure(
    resolution: Dict[str, Any] | None,
    refinement: str,
    *,
    enforced_source: str | None,
    enforced_lead_id: str | None,
    promoted_ids: List[str],
) -> bool:
    if not str(refinement or "").strip():
        return False
    res = resolution if isinstance(resolution, dict) else {}
    clue_id = str(res.get("clue_id") or "").strip()
    press = _topic_press_context_tokens(res)
    ref_toks = _content_tokens(str(refinement).lower())
    inter = press & ref_toks

    if str(enforced_source or "").strip() == "extracted_social":
        return True
    if clue_id and enforced_lead_id and clue_id == enforced_lead_id:
        return True
    if clue_id and clue_id in promoted_ids:
        return True
    if enforced_lead_id and enforced_lead_id in promoted_ids:
        return True
    if len(inter) >= 2:
        return True
    if len(inter) == 1 and len(ref_toks) <= 4:
        return True
    src = str(enforced_source or "").strip()
    if src in ("discoverable_clue", "exit", "author_exit"):
        return len(inter) >= 1
    if promoted_ids:
        return len(inter) >= 1
    return False


def _emitted_covers_refinement_spoken(emitted: str, refinement: str) -> bool:
    e = _normalize_text(emitted).lower()
    r = _normalize_text(refinement).lower()
    if not r:
        return True
    if r in e:
        return True
    rtoks = _content_tokens(r)
    etoks = _content_tokens(e)
    if not rtoks:
        return True
    hit = len(rtoks & etoks)
    need = min(2, len(rtoks))
    return hit >= need


def _gm_probe_for_answer_pressure_contracts(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Merge ``session["last_turn_response_policy"]`` when ``gm_output`` lacks ``response_policy`` (API stores policy on session)."""
    pol = gm_output.get("response_policy") if isinstance(gm_output.get("response_policy"), dict) else None
    if isinstance(pol, dict) and pol:
        return gm_output
    if isinstance(session, dict):
        lp = session.get("last_turn_response_policy")
        if isinstance(lp, dict) and lp:
            merged = dict(gm_output)
            merged["response_policy"] = lp
            return merged
    return gm_output


def apply_spoken_state_refinement_cash_out(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """After state promotes a lead/clue, ensure spoken dialogue surfaces that refinement on answer-pressure turns.

    Uses ``response_policy`` on ``gm_output`` when present; otherwise ``session["last_turn_response_policy"]``
    from the narration pipeline (see :func:`game.api._build_gpt_narration_from_authoritative_state`).
    """
    if not isinstance(gm_output, dict) or not isinstance(session, dict):
        return gm_output
    sid = str(scene_id or "").strip()
    if not sid:
        return gm_output
    if not strict_social_emission_will_apply(resolution, session, world, sid):
        return gm_output
    probe = _gm_probe_for_answer_pressure_contracts(gm_output, session)
    if not (
        _strict_social_answer_pressure_ac_contract_active(probe)
        or _strict_social_answer_pressure_rd_contract_active(probe)
    ):
        return gm_output
    if not isinstance(resolution, dict):
        return gm_output

    emitted = str(gm_output.get("player_facing_text") or "")
    if not _normalize_text(emitted):
        return gm_output

    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    mal = meta.get("minimum_actionable_lead") if isinstance(meta.get("minimum_actionable_lead"), dict) else {}
    ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}

    enforced = bool(mal.get("minimum_actionable_lead_enforced"))
    enforced_id = str(mal.get("enforced_lead_id") or "").strip() or None
    enforced_src = str(mal.get("enforced_lead_source") or "").strip() or None

    promoted_raw = ll.get("authoritative_promoted_ids") or []
    promoted_ids = [str(x).strip() for x in promoted_raw if isinstance(x, str) and str(x).strip()]

    if not enforced and not promoted_ids:
        return gm_output

    refinement = ""
    source = ""

    if enforced and enforced_id:
        refinement = _refinement_phrase_for_lead_or_clue_id(session, enforced_id)
        source = enforced_src or "minimum_actionable_lead"

    if not refinement.strip() and promoted_ids:
        pick = None
        res_cid = str(resolution.get("clue_id") or "").strip()
        if res_cid and res_cid in promoted_ids:
            pick = res_cid
        else:
            pick = promoted_ids[0]
        refinement = _refinement_phrase_for_lead_or_clue_id(session, pick)
        source = "authoritative_promotion"

    refinement = _normalize_text(refinement).strip()
    if not refinement:
        return gm_output

    if not _refinement_relevant_to_answer_pressure(
        resolution,
        refinement,
        enforced_source=enforced_src,
        enforced_lead_id=enforced_id,
        promoted_ids=promoted_ids,
    ):
        return gm_output

    if _emitted_covers_refinement_spoken(emitted, refinement):
        return gm_output

    templates = (
        "I can only add this: {ref}.",
        "What I can say is: {ref}.",
        "I don't know more than this: {ref}.",
    )
    idx = len(refinement) % 3
    ref_clean = refinement.rstrip().rstrip(".")
    tail = templates[idx].format(ref=ref_clean)
    new_text = _normalize_text(emitted.rstrip() + " " + tail)
    out = dict(gm_output)
    out["player_facing_text"] = new_text
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"spoken_state_refinement_cash_out:{source}"
    out["_spoken_refinement_cash_out"] = {
        "applied": True,
        "source": source,
        "refinement_preview": refinement[:160],
    }
    return out


def _skip_response_delta_layer(
    *,
    contract: Dict[str, Any] | None,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    if not isinstance(contract, dict):
        return "no_response_delta_contract"
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if bool(answer_completeness_meta.get("answer_completeness_failed")):
        return "answer_completeness_failed"
    if not strict_social_details:
        pass
    else:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            if _strict_social_answer_pressure_rd_contract_active(gm_output):
                return None
            return "strict_social_structured_or_bridge_source"
    if not _contract_bool(contract, "enabled"):
        return "response_delta_disabled"
    if not _contract_bool(contract, "delta_required"):
        return "delta_not_required"
    prev = str(contract.get("previous_answer_snippet") or "").strip()
    if not prev or not _response_delta_snippet_substantive(prev):
        return "previous_answer_snippet_unavailable"
    allowed = [str(x) for x in (contract.get("allowed_delta_kinds") or []) if str(x).strip()]
    if not allowed:
        return "allowed_delta_kinds_empty"
    norm = _normalize_text(emitted_text)
    if not norm:
        return "empty_emitted_text"
    return None


def _detect_delta_kinds_in_text(
    text: str,
    prior_tokens: set[str],
    *,
    allowed: set[str],
) -> set[str]:
    found: set[str] = set()
    toks = _response_delta_tokens(text)
    tok_set = set(toks)
    novel = tok_set - prior_tokens
    if "new_information" in allowed and (
        len(novel) >= 2 or any(len(t) >= 8 for t in novel) or _digit_bearing_new_info(str(text))
    ):
        found.add("new_information")
    if "refinement" in allowed and any(p.search(text) for p in _REFINEMENT_MARKERS):
        found.add("refinement")
    if "consequence" in allowed and any(p.search(text) for p in _CONSEQUENCE_MARKERS):
        found.add("consequence")
    if "clarified_uncertainty" in allowed and any(p.search(text) for p in _CLARIFIED_UNCERTAINTY_MARKERS):
        found.add("clarified_uncertainty")
    if "new_information" in allowed and not found.isdisjoint({"refinement", "consequence", "clarified_uncertainty"}):
        pass
    return found & allowed


def _digit_bearing_new_info(raw_text: str) -> bool:
    return bool(re.search(r"\b\d+\s*(?:feet|yards|miles|men|guards|hours|minutes|silver|gold|copper)\b", raw_text, re.IGNORECASE))


def _opening_carries_allowed_delta(
    opening_text: str,
    prior_token_set: set[str],
    *,
    allowed: set[str],
) -> bool:
    return bool(_detect_delta_kinds_in_text(opening_text, prior_token_set, allowed=allowed))


def _early_window_has_delta(
    sentences: List[str],
    contract: Dict[str, Any],
    prior_token_set: set[str],
    *,
    allowed: set[str],
) -> bool:
    if not sentences:
        return False
    bridge = bool(contract.get("allow_short_bridge_before_delta"))
    first = sentences[0]
    if _opening_carries_allowed_delta(first, prior_token_set, allowed=allowed):
        return True
    if len(sentences) >= 2 and bridge:
        pair = f"{first} {sentences[1]}"
        return bool(_detect_delta_kinds_in_text(pair, prior_token_set, allowed=allowed))
    return False


def validate_response_delta(
    emitted_text: str,
    contract: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Deterministic anti-echo check vs ``previous_answer_snippet`` only (no LLM)."""
    out: Dict[str, Any] = {
        "checked": False,
        "passed": True,
        "failure_reasons": [],
        "delta_kind_detected": None,
        "echo_overlap_ratio": None,
        "early_delta_found": False,
        "direct_restatement_detected": False,
        "previous_answer_available": False,
        "candidate_sentence_count": 0,
    }
    if not isinstance(contract, dict):
        return out
    if not _contract_bool(contract, "enabled") or not _contract_bool(contract, "delta_required"):
        return out
    prev = str(contract.get("previous_answer_snippet") or "").strip()
    out["previous_answer_available"] = bool(prev and _response_delta_snippet_substantive(prev))
    if not out["previous_answer_available"]:
        return out

    allowed_list = [str(x).strip().lower() for x in (contract.get("allowed_delta_kinds") or []) if str(x).strip()]
    allowed_set = set(allowed_list)
    if not allowed_set:
        return out

    text = _normalize_text(emitted_text)
    out["checked"] = True
    if not text:
        out["passed"] = False
        out["failure_reasons"] = ["no_delta_detected"]
        return out

    prior_tokens = _response_delta_tokens(prev)
    prior_token_set = set(prior_tokens)
    emitted_tokens = _response_delta_tokens(text)
    sentences = _split_sentences_answer_complete(text)
    out["candidate_sentence_count"] = len(sentences)

    echo = _response_delta_token_overlap_ratio(emitted_tokens, prior_tokens)
    out["echo_overlap_ratio"] = round(echo, 4)
    opening = _opening_segment(text)
    opening_toks = _response_delta_tokens(opening)
    open_ov = _response_delta_token_overlap_ratio(opening_toks, prior_tokens)
    out["direct_restatement_detected"] = bool(opening_toks and open_ov >= 0.62)

    kinds = _detect_delta_kinds_in_text(text, prior_token_set, allowed=allowed_set)
    if kinds:
        priority = ("new_information", "consequence", "refinement", "clarified_uncertainty")
        for k in priority:
            if k in kinds:
                out["delta_kind_detected"] = k
                break
        if out["delta_kind_detected"] is None:
            out["delta_kind_detected"] = next(iter(kinds))
    else:
        out["delta_kind_detected"] = None

    must_early = bool(contract.get("delta_must_come_early"))
    early_ok = _early_window_has_delta(sentences, contract, prior_token_set, allowed=allowed_set)
    out["early_delta_found"] = bool(early_ok)

    exp_shape = str(contract.get("expected_delta_shape") or "").strip().lower()
    failure_reasons: List[str] = []

    if not kinds:
        failure_reasons.append("no_delta_detected")
    if must_early and kinds and not early_ok:
        failure_reasons.append("follow_up_answer_without_refinement")
    opening_has_delta = _opening_carries_allowed_delta(opening, prior_token_set, allowed=allowed_set)
    if open_ov >= 0.55 and not opening_has_delta and kinds:
        failure_reasons.append("opening_semantic_restatement")
    if echo >= 0.78 and not kinds:
        failure_reasons.append("full_response_semantic_restatement")
    if _GENERIC_NONANSWER_SNIPPET.search(text) and echo >= 0.42 and not kinds:
        failure_reasons.append("repackaged_nonanswer")
    if (
        exp_shape == "bounded_partial_with_delta"
        and echo >= 0.68
        and _partial_reason_in_text(text, ["uncertainty", "lack_of_knowledge", "gated_information"])
        and kinds.isdisjoint({"new_information", "consequence", "refinement", "clarified_uncertainty"})
    ):
        failure_reasons.append("repeated_partial_without_new_boundary")

    out["failure_reasons"] = list(dict.fromkeys(str(r) for r in failure_reasons if r))
    out["passed"] = not bool(out["failure_reasons"])
    return out


def inspect_response_delta_failure(result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict) or result.get("passed") is not False:
        return {"failed": False}
    return {
        "failed": True,
        "failure_reasons": list(result.get("failure_reasons") or []),
        "echo_overlap_ratio": result.get("echo_overlap_ratio"),
        "delta_kind_detected": result.get("delta_kind_detected"),
    }


def _sentence_carries_response_delta(
    sentence: str,
    prior_token_set: set[str],
    *,
    allowed: set[str],
) -> bool:
    return bool(_detect_delta_kinds_in_text(sentence, prior_token_set, allowed=allowed))


def _repair_response_delta_minimal(
    text: str,
    _validation: Dict[str, Any],
    contract: Dict[str, Any],
) -> tuple[str | None, str | None]:
    """Reorder / trim existing sentences only; never invent facts."""
    prev = str(contract.get("previous_answer_snippet") or "").strip()
    prior_token_set = set(_response_delta_tokens(prev))
    allowed_list = [str(x).strip().lower() for x in (contract.get("allowed_delta_kinds") or []) if str(x).strip()]
    allowed = set(allowed_list)
    sentences = _split_sentences_answer_complete(text)
    if len(sentences) < 2:
        return None, None

    # 1) Front-load first later sentence that already carries a valid delta.
    for idx in range(1, len(sentences)):
        if _sentence_carries_response_delta(sentences[idx], prior_token_set, allowed=allowed):
            pick = sentences[idx]
            rest = sentences[:idx] + sentences[idx + 1 :]
            merged = _normalize_terminal_punctuation(pick) + " " + " ".join(
                _normalize_terminal_punctuation(s) for s in rest if s
            )
            candidate = _normalize_text(merged)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "frontload_delta_sentence"

    # 2) Trim echoed opening when the remainder validates.
    open_ov = _response_delta_token_overlap_ratio(_response_delta_tokens(sentences[0]), list(prior_token_set))
    if open_ov >= 0.5 and not _opening_carries_allowed_delta(sentences[0], prior_token_set, allowed=allowed):
        tail = " ".join(_normalize_terminal_punctuation(s) for s in sentences[1:] if s)
        candidate = _normalize_text(tail)
        v2 = validate_response_delta(candidate, contract)
        if v2.get("passed"):
            return candidate, "trim_echo_opening"

    # 3) Prioritize refinement / delta sentence before uncertainty caveat (swap s0/s1).
    if len(sentences) >= 2:
        s0, s1 = sentences[0], sentences[1]
        if _partial_reason_in_text(s0, ["uncertainty", "lack_of_knowledge"]) and _sentence_carries_response_delta(
            s1, prior_token_set, allowed=allowed
        ):
            merged = _normalize_terminal_punctuation(s1) + " " + _normalize_terminal_punctuation(s0)
            candidate = _normalize_text(merged)
            rest = " ".join(_normalize_terminal_punctuation(s) for s in sentences[2:] if s)
            if rest:
                candidate = _normalize_text(candidate + " " + rest)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "prioritize_refinement_before_caveat"

    # 4) Compress: drop duplicate partial opener + keep first delta sentence.
    if len(sentences) >= 2:
        dup_ov = _response_delta_token_overlap_ratio(
            _response_delta_tokens(sentences[0]),
            _response_delta_tokens(sentences[1]),
        )
        if dup_ov >= 0.72:
            trimmed = sentences[1:]
            candidate = _normalize_text(
                " ".join(_normalize_terminal_punctuation(s) for s in trimmed if s)
            )
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "drop_duplicate_partial_prefix"

    # 5) Compress echoed opener + substantive later line (two sentences -> delta first, opener shortened).
    if len(sentences) >= 2:
        for idx in range(1, len(sentences)):
            if not _sentence_carries_response_delta(sentences[idx], prior_token_set, allowed=allowed):
                continue
            delta_s = sentences[idx]
            head = sentences[0]
            rest = [s for i, s in enumerate(sentences) if i not in (0, idx)]
            merged = (
                _normalize_terminal_punctuation(delta_s)
                + " "
                + _normalize_terminal_punctuation(head)
                + (" " + " ".join(_normalize_terminal_punctuation(s) for s in rest if s) if rest else "")
            )
            candidate = _normalize_text(merged)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "compress_echo_plus_delta"

    return None, None


def _apply_response_delta_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = _resolve_response_delta_contract(gm_output)
    meta = _default_response_delta_meta()
    trace = contract.get("trace") if isinstance(contract, dict) else None
    if isinstance(trace, dict):
        meta["response_delta_trigger_source"] = trace.get("trigger_source")
    if isinstance(contract, dict) and contract.get("trigger_source"):
        meta["response_delta_trigger_source"] = contract.get("trigger_source")

    skip = _skip_response_delta_layer(
        contract=contract if isinstance(contract, dict) else None,
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=answer_completeness_meta,
        gm_output=gm_output,
    )
    meta["response_delta_skip_reason"] = skip
    if skip:
        return text, meta, []

    v0 = validate_response_delta(text, contract)
    meta["response_delta_checked"] = bool(v0.get("checked"))
    meta["response_delta_kind_detected"] = v0.get("delta_kind_detected")
    meta["response_delta_echo_overlap_ratio"] = v0.get("echo_overlap_ratio")
    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["response_delta_failed"] = True
    meta["response_delta_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_response_delta_minimal(text, v0, contract)
    if repaired:
        v1 = validate_response_delta(repaired, contract)
        if v1.get("passed"):
            meta["response_delta_repaired"] = True
            meta["response_delta_repair_mode"] = mode
            meta["response_delta_failed"] = False
            meta["response_delta_failure_reasons"] = []
            meta["response_delta_kind_detected"] = v1.get("delta_kind_detected")
            meta["response_delta_echo_overlap_ratio"] = v1.get("echo_overlap_ratio")
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("response_delta_unsatisfied_after_repair")
    meta["response_delta_failed"] = True
    return text, meta, extra


def _merge_response_delta_meta(meta: Dict[str, Any], rd_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "response_delta_checked": bool(rd_dbg.get("response_delta_checked")),
            "response_delta_failed": bool(rd_dbg.get("response_delta_failed")),
            "response_delta_failure_reasons": list(rd_dbg.get("response_delta_failure_reasons") or []),
            "response_delta_repaired": bool(rd_dbg.get("response_delta_repaired")),
            "response_delta_repair_mode": rd_dbg.get("response_delta_repair_mode"),
            "response_delta_kind_detected": rd_dbg.get("response_delta_kind_detected"),
            "response_delta_echo_overlap_ratio": rd_dbg.get("response_delta_echo_overlap_ratio"),
            "response_delta_skip_reason": rd_dbg.get("response_delta_skip_reason"),
            "response_delta_trigger_source": rd_dbg.get("response_delta_trigger_source"),
        }
    )


# --- Narrative authority (response_policy.narrative_authority shipped contract) -----------------


def _is_shipped_full_narrative_authority_contract(candidate: Any) -> bool:
    """True for ``build_narrative_authority_contract`` payloads, not prompt_debug slim summaries."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    if isinstance(candidate.get("debug_flags"), dict) and isinstance(candidate.get("allowed_deferrals"), list):
        return True
    return False


def _coerce_narrative_authority_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_full_narrative_authority_contract(maybe):
        return maybe
    return None


def _resolve_narrative_authority_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer the full narration payload path; never substitute prompt_debug for validation."""
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = _coerce_narrative_authority_contract_dict(pol.get("narrative_authority"))
        if hit:
            return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = _coerce_narrative_authority_contract_dict(pl.get("narrative_authority"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_narrative_authority_contract_dict(md.get("narrative_authority"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_narrative_authority_contract_dict(tr.get("narrative_authority"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    return None


def _narrative_authority_prompt_debug_mirror(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Compact upstream summary only (not valid as a shipped contract)."""
    if not isinstance(gm_output, dict):
        return None
    pd = gm_output.get("prompt_debug")
    if isinstance(pd, dict):
        sl = pd.get("narrative_authority")
        if isinstance(sl, dict):
            return sl
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            sl = em.get("narrative_authority_prompt_debug")
            if isinstance(sl, dict):
                return sl
    return None


def _narrative_authority_policy_disabled(gm_output: Dict[str, Any] | None) -> bool:
    if not isinstance(gm_output, dict):
        return False
    pol = gm_output.get("response_policy")
    if not isinstance(pol, dict):
        return False
    if pol.get("forbid_unjustified_narrative_authority") is False:
        return True
    return False


def _default_narrative_authority_meta() -> Dict[str, Any]:
    return {
        "narrative_authority_checked": False,
        "narrative_authority_failed": False,
        "narrative_authority_failure_reasons": [],
        "narrative_authority_repaired": False,
        "narrative_authority_repair_mode": None,
        "narrative_authority_skip_reason": None,
        "narrative_authority_deferral_mode": None,
        "narrative_authority_assertion_flags": {},
    }


def _merge_narrative_authority_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    if not na_dbg:
        return
    keys = (
        "narrative_authority_checked",
        "narrative_authority_failed",
        "narrative_authority_failure_reasons",
        "narrative_authority_repaired",
        "narrative_authority_repair_mode",
        "narrative_authority_skip_reason",
        "narrative_authority_deferral_mode",
        "narrative_authority_assertion_flags",
    )
    for k in keys:
        if k in na_dbg:
            meta[k] = na_dbg[k]


def _merge_narrative_authority_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("narrative_authority_"):
            continue
        flat[k] = v
    mirror = _narrative_authority_prompt_debug_mirror(gm_output)
    full = _resolve_narrative_authority_contract(gm_output)
    mirror_box: Dict[str, Any] = {}
    if isinstance(mirror, dict) and mirror:
        mirror_box["prompt_debug_mirror_present"] = True
        if isinstance(full, dict) and _is_shipped_full_narrative_authority_contract(full):
            keys = (
                "enabled",
                "authoritative_outcome_available",
                "forbid_unresolved_outcome_assertions",
                "forbid_hidden_fact_assertions",
                "forbid_npc_intent_assertions_without_basis",
            )
            mismatch = any(mirror.get(k) != full.get(k) for k in keys)
            mirror_box["prompt_debug_mirror_mismatch_vs_shipped"] = bool(mismatch)

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        if mirror_box:
            base = em.get("narrative_authority")
            if isinstance(base, dict):
                em["narrative_authority"] = {**base, **mirror_box}
            else:
                em["narrative_authority"] = dict(mirror_box)
        for fk, fv in flat.items():
            em[fk] = fv

    if not flat and not mirror_box:
        return

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def _skip_narrative_authority_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if _narrative_authority_policy_disabled(gm_output):
        return "narrative_authority_policy_disabled"
    if not isinstance(contract, dict):
        return "no_full_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    return None


def _na_outcome_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if not str(msent).strip():
            continue
        if _sentence_has_hedge(sent):
            continue
        if _outcome_assertion_hits(sent, msent):
            return start, end, sent
    return None


def _na_hidden_fact_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if _sentence_has_hedge(sent):
            continue
        if _HIDDEN_FACT_CERTAINTY_RE.search(msent.lower()):
            return start, end, sent
    return None


def _na_intent_sentence_span(
    raw: str,
    *,
    player_text: str | None,
    resolution: Dict[str, Any] | None,
) -> tuple[int, int, str] | None:
    res_prompt = (
        str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, dict) else ""
    )
    player_seeks = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(res_prompt)
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        low = msent.lower()
        if player_seeks and _sentence_has_hedge(sent):
            continue
        if player_seeks and _ROLL_PROMPT_RE.search(low):
            continue
        if _INTENT_CERTAINTY_RE.search(low):
            if player_seeks and (_sentence_has_hedge(sent) or _ROLL_PROMPT_RE.search(low)):
                continue
            return start, end, sent
    return None


def _na_replace_sentence(raw: str, start: int, end: int, replacement: str) -> str:
    rep = str(replacement or "").strip()
    before = raw[:start].rstrip()
    after = raw[end:].lstrip()
    parts = [p for p in (before, rep, after) if p]
    return _normalize_text(" ".join(parts))


def _repair_narrative_authority_narrow(
    text: str,
    validation: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    player_text: str | None,
) -> tuple[str | None, str | None]:
    flags = validation.get("assertion_flags") if isinstance(validation.get("assertion_flags"), dict) else {}
    if not flags or validation.get("passed") is True:
        return None, None

    narrative_authority_repair_hints(validation)

    repaired = str(text or "")
    modes: List[str] = []

    if flags.get("invented_outcome"):
        low_full = repaired.lower()
        if narrative_authority_prefers_roll_prompt(player_text, resolution) and not _ROLL_PROMPT_RE.search(
            low_full
        ):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make a skill check to see how that resolves before you treat the outcome as settled."
            )
            modes.append("invented_outcome_roll_prompt")
        elif _BRANCH_FRAMING_RE.search(low_full):
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "Until the check resolves, leave that beat open rather than stating a result.",
                )
                modes.append("invented_outcome_branch_soften")
        else:
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You attempt it, but the outcome is not settled yet.",
                )
                modes.append("invented_outcome_uncertainty_replace")
            else:
                strong = _STRONG_OUTCOME_ASSERTION_RE.search(repaired)
                if strong:
                    repaired = (
                        repaired[: strong.start()]
                        + "You attempt it, but the outcome is not settled yet."
                        + repaired[strong.end() :]
                    )
                    repaired = _normalize_text(repaired)
                    modes.append("invented_outcome_span_soften")

    if flags.get("invented_hidden_fact"):
        span = _na_hidden_fact_sentence_span(repaired)
        if span:
            start, end, _sent = span
            repaired = _na_replace_sentence(
                repaired,
                start,
                end,
                "From what you can see, you can't pin the hidden cause down yet.",
            )
            modes.append("invented_hidden_fact_downgrade")

    if flags.get("invented_intent"):
        seek = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(
            str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, Mapping) else ""
        )
        prefers = narrative_authority_prefers_roll_prompt(player_text, resolution)
        low_full = repaired.lower()
        if seek and prefers and not _ROLL_PROMPT_RE.search(low_full):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make an Insight check if you want a clearer read on motive—not as a hidden fact."
            )
            modes.append("invented_intent_insight_prompt")
        else:
            span = _na_intent_sentence_span(
                repaired,
                player_text=player_text,
                resolution=resolution if isinstance(resolution, dict) else None,
            )
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You notice timing, posture, and wording—you can't treat that as proof of motive yet.",
                )
                modes.append("invented_intent_observable_cues")

    if not modes:
        return None, None
    return repaired, "|".join(modes)


def _apply_narrative_authority_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> tuple[str, Dict[str, Any], List[str]]:
    _ = answer_completeness_meta
    strict_social_path = strict_social_details is not None
    contract = _resolve_narrative_authority_contract(gm_output if isinstance(gm_output, dict) else None)

    meta = _default_narrative_authority_meta()

    skip = _skip_narrative_authority_layer(
        text,
        contract,
        gm_output=gm_output if isinstance(gm_output, dict) else None,
        response_type_debug=response_type_debug,
    )
    meta["narrative_authority_skip_reason"] = skip
    if skip:
        return text, meta, []

    assert contract is not None
    sid = str(scene_id or "").strip()
    player_text = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    if not str(player_text or "").strip():
        player_text = _last_player_input(
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )

    v0 = validate_narrative_authority(
        text,
        contract,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        player_text=player_text,
    )
    meta["narrative_authority_checked"] = bool(v0.get("checked"))
    meta["narrative_authority_deferral_mode"] = v0.get("matched_deferral_mode")
    af = v0.get("assertion_flags")
    meta["narrative_authority_assertion_flags"] = dict(af) if isinstance(af, dict) else {}

    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["narrative_authority_failed"] = True
    meta["narrative_authority_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_narrative_authority_narrow(
        text,
        v0,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        player_text=player_text,
    )
    if repaired:
        v1 = validate_narrative_authority(
            repaired,
            contract,
            resolution=resolution if isinstance(resolution, Mapping) else None,
            player_text=player_text,
        )
        if v1.get("passed"):
            meta["narrative_authority_repaired"] = True
            meta["narrative_authority_repair_mode"] = mode
            meta["narrative_authority_failed"] = False
            meta["narrative_authority_failure_reasons"] = []
            meta["narrative_authority_deferral_mode"] = v1.get("matched_deferral_mode")
            af1 = v1.get("assertion_flags")
            meta["narrative_authority_assertion_flags"] = dict(af1) if isinstance(af1, dict) else {}
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("narrative_authority_unsatisfied_after_repair")
    meta["narrative_authority_failed"] = True
    return text, meta, extra


# --- Scene state anchor (scene_state_anchor_contract + validate_scene_state_anchoring) ----------


def _resolve_scene_state_anchor_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Read the shipped contract from *gm_output* / narration payload copies only (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None
    direct = gm_output.get("scene_state_anchor_contract")
    if isinstance(direct, dict):
        return direct
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if isinstance(pl, dict):
            sac = pl.get("scene_state_anchor_contract")
            if isinstance(sac, dict):
                return sac
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        sac = md.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        sac = tr.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    return None


def _resolve_scene_state_anchor_debug(gm_output: Dict[str, Any] | None) -> Dict[str, Any]:
    """Compact upstream summary (e.g. gm emission_debug.scene_state_anchor) for metadata merge."""
    if not isinstance(gm_output, dict):
        return {}
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            dbg = em.get("scene_state_anchor")
            if isinstance(dbg, dict):
                return dict(dbg)
    return {}


def _default_scene_state_anchor_meta(
    skip: str | None,
    upstream_debug: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "scene_state_anchor_checked": False,
        "scene_state_anchor_passed": False,
        "scene_state_anchor_failed": False,
        "scene_state_anchor_skip_reason": skip,
        "scene_state_anchor_matched_kinds": [],
        "scene_state_anchor_failure_reasons": [],
        "scene_state_anchor_repaired": False,
        "scene_state_anchor_repair_mode": None,
        "scene_state_anchor_upstream_debug": dict(upstream_debug),
    }


def _merge_scene_state_anchor_meta(meta: Dict[str, Any], ssa_dbg: Dict[str, Any]) -> None:
    if not ssa_dbg:
        return
    keys = (
        "scene_state_anchor_checked",
        "scene_state_anchor_passed",
        "scene_state_anchor_failed",
        "scene_state_anchor_skip_reason",
        "scene_state_anchor_matched_kinds",
        "scene_state_anchor_failure_reasons",
        "scene_state_anchor_repaired",
        "scene_state_anchor_repair_mode",
        "scene_state_anchor_upstream_debug",
    )
    for k in keys:
        if k in ssa_dbg:
            meta[k] = ssa_dbg[k]


def _merge_scene_state_anchor_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    """Attach gate fields and preserve/merge compact upstream ``scene_state_anchor`` summaries."""
    upstream: Any = None
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("scene_state_anchor_"):
            continue
        if k == "scene_state_anchor_upstream_debug":
            upstream = v
            continue
        flat[k] = v
    if not flat and not (isinstance(upstream, dict) and upstream):
        return

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        base = em.get("scene_state_anchor")
        if isinstance(upstream, dict) and upstream:
            if isinstance(base, dict):
                merged = {**upstream, **base}
            else:
                merged = dict(upstream)
            em["scene_state_anchor"] = merged
        for fk, fv in flat.items():
            em[fk] = fv

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def _skip_scene_state_anchor_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not isinstance(contract, dict):
        return "missing_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            return "strict_social_structured_or_bridge_source"
    return None


def _title_case_anchor_phrase(phrase: str) -> str:
    parts = [p for p in str(phrase or "").strip().split() if p]
    if not parts:
        return ""
    out: List[str] = []
    for w in parts:
        if not w:
            continue
        out.append(w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return " ".join(out)


def _opening_has_token_hint(text: str, token_lower: str) -> bool:
    if not token_lower or not str(text or "").strip():
        return False
    low = str(text).lower()
    head = low[: min(len(low), 280)]
    if " " in token_lower:
        return token_lower in head
    return bool(re.search(rf"(?<!\w){re.escape(token_lower)}(?!\w)", head))


def _pick_actor_token(actor_tokens: Sequence[Any]) -> str | None:
    for raw in actor_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3 and not s.isdigit():
            return s
    return None


def _pick_action_tether_token(player_action_tokens: Sequence[Any]) -> str | None:
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if " " in s and 5 <= len(s) <= 96:
            return s
    skip_one = frozenset({"question", "answer", "observe", "investigate", "action", "kind"})
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 4 and s not in skip_one:
            return s
    return None


def _pick_location_phrase(contract: Mapping[str, Any]) -> str | None:
    lab = str(contract.get("scene_location_label") or "").strip()
    if lab and len(lab) >= 2:
        return lab.lower()
    for raw in contract.get("location_tokens") or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3:
            return s
    return None


def _repair_actor_opening(text: str, actor_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_actor_token(actor_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    display = _title_case_anchor_phrase(tok)
    if not display:
        return None, None
    return _normalize_text(f"{display} {text}"), "actor_rebind"


def _repair_action_tether(text: str, player_action_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_action_tether_token(player_action_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    lead = _title_case_anchor_phrase(tok) if " " in tok else tok.capitalize()
    return _normalize_text(f"{lead} — {text}"), "action_rebind"


def _repair_location_opening(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"At {disp}, {text}"), "location_rebind"


def _repair_narrator_neutral_location(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"Here at {disp}, {text}"), "narrator_neutral_scene_rebind"


def _repair_scene_state_anchor_minimal(
    text: str,
    contract: Mapping[str, Any],
    *,
    strict_social_details: Dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Opening-tether repairs only; uses contract token buckets (no new facts)."""
    _ = strict_social_details
    actors = list(contract.get("actor_tokens") or [])
    actions = list(contract.get("player_action_tokens") or [])
    # Repair ladder: A actor → B action → C location → D narrator-neutral + location.
    r, mode = _repair_actor_opening(text, actors)
    if r:
        return r, mode
    r, mode = _repair_action_tether(text, actions)
    if r:
        return r, mode
    r, mode = _repair_location_opening(text, contract)
    if r:
        return r, mode
    r, mode = _repair_narrator_neutral_location(text, contract)
    if r:
        return r, mode
    return None, None


def _apply_scene_state_anchor_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    contract = _resolve_scene_state_anchor_contract(gm_output)
    upstream = _resolve_scene_state_anchor_debug(gm_output)
    norm = _normalize_text(text).strip()
    tags_ssa = [str(t) for t in (gm_output.get("tags") or []) if isinstance(t, str)]
    dbg_ssa = str(gm_output.get("debug_notes") or "")
    if norm and re.fullmatch(r"\[[^\]]{1,120}\]", norm):
        meta = _default_scene_state_anchor_meta("bracketed_production_stub", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "bracketed_production_stub"
        return text, meta
    if "known_fact_guard" in tags_ssa and "recent_dialogue_continuity" in dbg_ssa:
        meta = _default_scene_state_anchor_meta("known_fact_recent_dialogue_continuity", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "known_fact_recent_dialogue_continuity"
        return text, meta
    skip = _skip_scene_state_anchor_layer(
        text,
        contract,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
    )
    meta = _default_scene_state_anchor_meta(skip, upstream)
    if skip:
        return text, meta

    assert contract is not None
    v0 = validate_scene_state_anchoring(text, contract)
    meta["scene_state_anchor_checked"] = bool(v0.get("checked"))
    meta["scene_state_anchor_passed"] = bool(v0.get("passed"))
    meta["scene_state_anchor_matched_kinds"] = list(v0.get("matched_anchor_kinds") or [])
    meta["scene_state_anchor_failure_reasons"] = list(v0.get("failure_reasons") or [])
    if v0.get("passed"):
        return text, meta

    repaired, mode = _repair_scene_state_anchor_minimal(
        text,
        contract,
        strict_social_details=strict_social_details,
    )
    if repaired:
        v1 = validate_scene_state_anchoring(repaired, contract)
        meta["scene_state_anchor_checked"] = bool(v1.get("checked"))
        meta["scene_state_anchor_passed"] = bool(v1.get("passed"))
        meta["scene_state_anchor_matched_kinds"] = list(v1.get("matched_anchor_kinds") or [])
        meta["scene_state_anchor_failure_reasons"] = list(v1.get("failure_reasons") or [])
        if v1.get("passed"):
            meta["scene_state_anchor_repaired"] = True
            meta["scene_state_anchor_repair_mode"] = mode
            meta["scene_state_anchor_failed"] = False
            return repaired, meta

    meta["scene_state_anchor_failed"] = True
    meta["scene_state_anchor_repaired"] = False
    meta["scene_state_anchor_repair_mode"] = None
    return text, meta


def _enforce_response_type_contract(
    candidate_text: str,
    *,
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    strict_social_turn: bool,
    strict_social_suppressed_non_social_turn: bool,
    active_interlocutor: str,
) -> tuple[str, Dict[str, Any]]:
    contract, source = _resolve_response_type_contract(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    debug = _default_response_type_debug(contract, source)
    if not contract:
        return candidate_text, debug

    required = str(contract.get("required_response_type") or "").strip().lower()
    allow_escalation = bool(contract.get("allow_escalation"))
    player_input = _last_player_input(
        resolution=resolution,
        session=session,
        scene_id=scene_id,
    )
    current = _normalize_text(candidate_text)
    reasons: List[str] = []

    if not allow_escalation and candidate_violates_non_hostile_escalation_contract(current):
        reasons.append("non_hostile_escalation_violation")
        debug["non_hostile_escalation_blocked"] = True

    validator_ok = True
    validator_reasons: List[str] = []
    if required == "dialogue":
        if strict_social_suppressed_non_social_turn:
            debug["response_type_candidate_ok"] = None
            debug["response_type_repair_kind"] = "dialogue_enforcement_skipped_due_to_social_suppression"
            return current, debug
        validator_ok, validator_reasons = candidate_satisfies_dialogue_contract(
            current,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
        )
    elif required == "answer":
        validator_ok, validator_reasons = candidate_satisfies_answer_contract(current)
    elif required == "action_outcome":
        validator_ok, validator_reasons = candidate_satisfies_action_outcome_contract(
            current,
            player_input=player_input,
        )
    reasons.extend(validator_reasons)

    if validator_ok and not reasons:
        debug["response_type_candidate_ok"] = True
        return current, debug

    repaired: str | None = None
    repair_kind: str | None = None
    if required == "dialogue":
        social_resolution = _social_fallback_resolution(
            resolution=resolution,
            active_interlocutor=active_interlocutor,
            world=world,
            scene_id=scene_id,
        )
        if strict_social_turn and isinstance(social_resolution, dict):
            repaired = strict_social_ownership_terminal_fallback(social_resolution)
            repair_kind = "strict_social_dialogue_repair"
        elif isinstance(social_resolution, dict):
            repaired = minimal_social_emergency_fallback_line(social_resolution)
            repair_kind = "dialogue_minimal_repair"
    elif required == "answer":
        repaired = _minimal_answer_contract_repair(
            resolution=resolution,
            active_interlocutor=active_interlocutor,
            world=world,
            scene_id=scene_id,
        )
        if repaired:
            repair_kind = "answer_minimal_repair"
    elif required == "action_outcome":
        repaired = _minimal_action_outcome_contract_repair(
            player_input=player_input,
            resolution=resolution,
        )
        repair_kind = "action_outcome_minimal_repair"

    if repaired:
        repaired = _normalize_text(repaired)
        repaired_reasons: List[str] = []
        if not allow_escalation and candidate_violates_non_hostile_escalation_contract(repaired):
            repaired_reasons.append("non_hostile_escalation_violation")
        if required == "dialogue":
            repaired_ok, validator_reasons = candidate_satisfies_dialogue_contract(
                repaired,
                resolution=resolution,
                session=session,
                scene_id=scene_id,
                world=world,
            )
        elif required == "answer":
            repaired_ok, validator_reasons = candidate_satisfies_answer_contract(repaired)
        elif required == "action_outcome":
            repaired_ok, validator_reasons = candidate_satisfies_action_outcome_contract(
                repaired,
                player_input=player_input,
            )
        else:
            repaired_ok, validator_reasons = (True, [])
        repaired_reasons.extend(validator_reasons)
        if repaired_ok and not repaired_reasons:
            debug["response_type_candidate_ok"] = True
            debug["response_type_repair_used"] = True
            debug["response_type_repair_kind"] = repair_kind
            debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
            return repaired, debug

    debug["response_type_candidate_ok"] = False
    debug["response_type_repair_kind"] = repair_kind
    debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
    return current, debug


_PARTICIPIAL_BASE_VERBS: Dict[str, str] = {
    "intertwining": "intertwine",
    "drawing": "draw",
    "hinting": "hint",
    "suggesting": "suggest",
    "making": "make",
    "indicating": "indicate",
    "offering": "offer",
    "creating": "create",
    "revealing": "reveal",
    "urging": "urge",
    "watching": "watch",
    "cutting": "cut",
}
_PARTICIPIAL_THIRD_PERSON: Dict[str, str] = {
    "intertwining": "intertwines",
    "drawing": "draws",
    "hinting": "hints",
    "suggesting": "suggests",
    "making": "makes",
    "indicating": "indicates",
    "offering": "offers",
    "creating": "creates",
    "revealing": "reveals",
    "urging": "urges",
    "watching": "watches",
    "cutting": "cuts",
}
_IMPLICATION_PARTICIPLES = {"hinting", "indicating", "revealing"}
_MICRO_SMOOTH_MAX_COMBINED_LEN = 140
_MICRO_SMOOTH_SHORT_SENTENCE_LEN = 85
_MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS = (
    ";",
    ":",
    " while ",
    " because ",
    " although ",
    " though ",
    " which ",
    " that ",
    " who ",
)
_MICRO_SMOOTH_BANNED_TAIL_PHRASES = (
    "hinting at",
    "suggesting",
    "implying",
    "revealing",
    "indicating",
)
_MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS = (
    "initiative",
    "attack roll",
    "damage",
    "hit points",
    "armor class",
    "saving throw",
    "spell slot",
    "dc ",
    "roll ",
    "check ",
    "hp",
    "ac",
)
_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"“”'‘’]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)
# Dialogue tag with singular they: "… out loud," they murmur (comma before closing quote) or "…", they say.
_DIALOGUE_ATTRIBUTION_THEY_SPEECH_TAG = re.compile(
    r"(?:"
    r'[""“](.+?),\s*[""”]\s+\b(?:they|them)\b'
    r"|"
    r'[""“](.+?)[""”]\s*,\s+\b(?:they|them)\b'
    r")"
    r"[^.!?\n]{0,200}\b(?:"
    r"murmur|mutters|muttered|say|says|said|asks?|asked|whisper|whispers|whispered|"
    r"reply|replies|replied|add|adds|added"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_THIRD_PERSON_TO_PARTICIPLE: Dict[str, str] = {
    "cuts": "cutting",
    "draws": "drawing",
    "hints": "hinting",
    "suggests": "suggesting",
    "makes": "making",
    "indicates": "indicating",
    "offers": "offering",
    "creates": "creating",
    "reveals": "revealing",
    "urges": "urging",
    "watches": "watching",
    "calls": "calling",
    "shouts": "shouting",
    "scans": "scanning",
    "studies": "studying",
    "gestures": "gesturing",
    "lingers": "lingering",
    "waits": "waiting",
    "stands": "standing",
    "speaks": "speaking",
    "says": "saying",
    "holds": "holding",
    "keeps": "keeping",
    "looks": "looking",
    "glances": "glancing",
    "murmurs": "murmuring",
    "whispers": "whispering",
    "observes": "observing",
    "surveys": "surveying",
    "exchanges": "exchanging",
}


def _looks_like_participial_fragment(text: str) -> bool:
    clean = _normalize_text(text).strip()
    if not clean:
        return False
    core = clean.rstrip(".!?").strip(" ,;")
    if not core:
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]*", core)
    if len(words) < 3 or len(words) > 22:
        return False

    first = words[0].lower()
    if not first.endswith("ing"):
        return False
    if first not in _PARTICIPIAL_BASE_VERBS:
        return False

    # Avoid touching already-complete short clauses.
    early = " ".join(words[:7]).lower()
    finite_markers = (
        " is ",
        " are ",
        " was ",
        " were ",
        " has ",
        " have ",
        " had ",
        " does ",
        " do ",
        " did ",
        " will ",
        " can ",
        " could ",
        " should ",
        " would ",
        " must ",
    )
    early_padded = f" {early} "
    if any(marker in early_padded for marker in finite_markers):
        return False

    if re.match(r"^(?:as|because|if|when|while|although)\b", core, flags=re.IGNORECASE):
        return False
    return True


def _has_single_actor_anchor(previous_sentence: str) -> bool:
    prev = _normalize_text(previous_sentence).rstrip(".!?")
    if not prev:
        return False
    lowered = prev.lower()

    if any(token in lowered for token in (" and ", " both ", " together ", " alongside ", " two ", " several ")):
        return False
    if any(token in lowered for token in (" they ", " we ", " them ", " their ", " voices ")):
        return False

    singular_signal = re.search(
        r"\b(?:is|was|calls|shouts|offers|watches|studies|lingers|gestures|waits|leans|stands|speaks|says)\b",
        lowered,
    )
    plural_signal = re.search(r"\b(?:are|were|call|shout|offer|watch|study|linger|gesture|wait|speak|say)\b", lowered)
    if plural_signal and not singular_signal:
        return False
    return singular_signal is not None


def _departicipialize_clause(fragment_clause: str, *, subject: str, third_person: bool = False) -> str:
    clause = _normalize_text(fragment_clause).strip(" ,;")
    match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", clause, flags=re.IGNORECASE)
    if not match:
        return ""
    participle = match.group(1).lower()
    remainder = _normalize_text(match.group(2))
    verb = _PARTICIPIAL_THIRD_PERSON.get(participle) if third_person else _PARTICIPIAL_BASE_VERBS.get(participle)
    if not verb:
        return ""
    if remainder:
        return _normalize_terminal_punctuation(f"{subject} {verb}{(' ' + remainder) if not remainder.startswith(',') else remainder}")
    return _normalize_terminal_punctuation(f"{subject} {verb}")


def _repair_participial_fragment(previous_sentence: str, fragment: str) -> str | None:
    clean_fragment = _normalize_text(fragment)
    if not _looks_like_participial_fragment(clean_fragment):
        return None

    core = clean_fragment.rstrip(".!?").strip(" ,;")
    if not core:
        return None
    if re.search(r"\b(he|she|him|his)\b", core, flags=re.IGNORECASE):
        return None
    parts = [part.strip(" ,;") for part in core.split(",", 1)]
    head = parts[0] if parts else ""
    tail = parts[1] if len(parts) > 1 else ""
    if not head:
        return None

    if _has_single_actor_anchor(previous_sentence):
        repaired_head = _departicipialize_clause(head, subject="They", third_person=False)
        if not repaired_head:
            return None
        if not tail:
            return repaired_head
        possessive_tail = re.match(
            r"^(their|his|her)\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*ing)\b(.*)$",
            tail,
            flags=re.IGNORECASE,
        )
        if not possessive_tail:
            return repaired_head
        possessive = possessive_tail.group(1).lower()
        noun_phrase = _normalize_text(possessive_tail.group(2))
        participle = possessive_tail.group(3).lower()
        remainder = _normalize_text(possessive_tail.group(4))
        finite_verb = _PARTICIPIAL_THIRD_PERSON.get(participle)
        if not finite_verb:
            return repaired_head
        subject_phrase = f"{possessive.capitalize()} {noun_phrase}"
        second = (
            _normalize_terminal_punctuation(f"{subject_phrase} {finite_verb}{(' ' + remainder) if remainder else ''}")
            if noun_phrase
            else ""
        )
        if second:
            return _normalize_text(f"{repaired_head} {second}")
        return repaired_head

    head_match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", head, flags=re.IGNORECASE)
    if not head_match:
        return None
    head_participle = head_match.group(1).lower()
    if head_participle not in _IMPLICATION_PARTICIPLES:
        return None
    if re.search(r"\b(he|she|they|his|her|their)\b", core, flags=re.IGNORECASE):
        return None
    repaired = _departicipialize_clause(head, subject="It", third_person=True)
    return repaired or None


def _repair_fragmentary_participial_splits(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    repaired_any = False
    rewritten_parts: List[str] = [sentence_parts[0]]
    for index in range(1, len(sentence_parts)):
        previous = rewritten_parts[-1]
        current = sentence_parts[index]
        if _has_terminal_punctuation(previous) and _looks_like_participial_fragment(current):
            repaired = _repair_participial_fragment(previous, current)
            if repaired and _normalize_text(repaired) != _normalize_text(current):
                rewritten_parts.append(repaired)
                repaired_any = True
                continue
        rewritten_parts.append(current)
    return _normalize_text(" ".join(rewritten_parts)), repaired_any


def _sentence_has_dialogue_or_mechanics(sentence: str) -> bool:
    clean = _normalize_text(sentence)
    if not clean:
        return True
    lowered = clean.lower()
    if any(ch in clean for ch in ('"', "“", "”")):
        return True
    if re.search(r"(^|[\s(])'[^']{1,120}'", clean):
        return True
    if clean.startswith("- ") or clean.startswith("—"):
        return True
    return any(marker in lowered for marker in _MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS)


def _can_micro_merge_sentence_pair(first: str, second: str) -> bool:
    first_clean = _normalize_text(first)
    second_clean = _normalize_text(second)
    if not first_clean or not second_clean:
        return False
    if _sentence_has_dialogue_or_mechanics(first_clean) or _sentence_has_dialogue_or_mechanics(second_clean):
        return False

    first_core = first_clean.rstrip(".!?").strip()
    second_core = second_clean.rstrip(".!?").strip()
    if not first_core or not second_core:
        return False
    if len(first_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN or len(second_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN:
        return False

    first_low = f" {first_core.lower()} "
    second_low = f" {second_core.lower()} "
    if any(marker in first_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(marker in second_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(phrase in second_low for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return False
    if re.search(r"\b(he|she|it|you|we|i|him|her|them|our|your|my)\b", second_core, flags=re.IGNORECASE):
        return False
    if not (
        re.match(r"^they\b", first_core, flags=re.IGNORECASE)
        and (
            re.match(r"^they\b", second_core, flags=re.IGNORECASE)
            or re.match(r"^their\s+[A-Za-z][A-Za-z' -]{0,40}\s+[A-Za-z][A-Za-z'-]+\b", second_core, flags=re.IGNORECASE)
        )
    ):
        return False
    return True


def _merge_short_same_anchor_sentences(first: str, second: str) -> str | None:
    if not _can_micro_merge_sentence_pair(first, second):
        return None
    first_core = _normalize_text(first).rstrip(".!?").strip()
    second_core = _normalize_text(second).rstrip(".!?").strip()

    first_they = re.match(r"^(They)\s+(.+)$", first_core, flags=re.IGNORECASE)
    if not first_they:
        return None
    first_subject = first_they.group(1)
    first_predicate = first_they.group(2).strip()
    if not first_predicate:
        return None

    second_they = re.match(r"^(They)\s+(.+)$", second_core, flags=re.IGNORECASE)
    if second_they:
        second_predicate = second_they.group(2).strip()
        if not second_predicate:
            return None
        merged = f"{first_subject} {first_predicate}, then {second_predicate}"
        normalized = _normalize_terminal_punctuation(merged)
        if len(normalized.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
            return None
        if any(phrase in normalized.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
            return None
        return normalized

    second_possessive = re.match(
        r"^Their\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*)\b(.*)$",
        second_core,
        flags=re.IGNORECASE,
    )
    if not second_possessive:
        return None
    noun_phrase = _normalize_text(second_possessive.group(1))
    finite_verb = second_possessive.group(2).lower()
    remainder = _normalize_text(second_possessive.group(3))
    participle = _THIRD_PERSON_TO_PARTICIPLE.get(finite_verb)
    if not noun_phrase or not participle:
        return None

    tail = f"their {noun_phrase} {participle}{(' ' + remainder) if remainder else ''}"
    if any(phrase in tail.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return None
    merged = _normalize_terminal_punctuation(f"{first_subject} {first_predicate}, {tail}")
    if len(merged.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
        return None
    return merged


def _micro_smooth_post_repair_sentences(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    merged_any = False
    rewritten_parts: List[str] = []
    idx = 0
    while idx < len(sentence_parts):
        current = sentence_parts[idx]
        if merged_any or idx >= len(sentence_parts) - 1:
            rewritten_parts.append(current)
            idx += 1
            continue
        nxt = sentence_parts[idx + 1]
        merged = _merge_short_same_anchor_sentences(current, nxt)
        if not merged:
            rewritten_parts.append(current)
            idx += 1
            continue
        rewritten_parts.append(merged)
        merged_any = True
        idx += 2

    return _normalize_text(" ".join(rewritten_parts)), merged_any


def _decompress_overpacked_sentences(text: str) -> str:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text
    if not any(marker in clean_text for marker in (",", ";", " hinting at ", " suggesting ", " which could ", " that could ")):
        return clean_text

    participles = (
        "intertwining",
        "drawing",
        "hinting",
        "suggesting",
        "making",
        "indicating",
        "offering",
        "creating",
        "revealing",
        "urging",
        "watching",
    )
    implication_phrases = (
        "hinting at",
        "suggesting",
        "making a tempting opportunity",
        "which could",
        "that could hold vital implications",
    )
    clause_markers = (" while ", " and ", " but ", ";", ":")
    sentence_parts = re.split(r"(?<=[.!?])\s+", clean_text)
    rewritten_parts: List[str] = []

    for raw_sentence in sentence_parts:
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        core = sentence.rstrip(".!?").strip()
        if not core:
            rewritten_parts.append(sentence)
            continue

        rewritten = False
        punct = sentence[-1] if sentence[-1] in ".!?" else "."

        # Pattern B: semicolon-based explicit alternatives.
        if ";" in core:
            left, right = core.split(";", 1)
            left_clean = _normalize_terminal_punctuation(left)
            right_clean = _normalize_text(right)
            if (
                left_clean
                and right_clean
                and (
                    re.search(r"\bone\s+is\b", right_clean, flags=re.IGNORECASE)
                    or re.search(r"\bone\b[^.]{0,120}\bthe other\b", right_clean, flags=re.IGNORECASE)
                )
            ):
                alternatives = re.split(r",\s*(?=(?:the other|another)\b)", right_clean, maxsplit=1, flags=re.IGNORECASE)
                if len(alternatives) == 2:
                    first_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[0]))
                    second_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[1]))
                    if first_alt and second_alt:
                        rewritten_parts.extend([left_clean, first_alt, second_alt])
                        rewritten = True
                else:
                    right_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(right_clean))
                    if right_sentence:
                        rewritten_parts.extend([left_clean, right_sentence])
                        rewritten = True

        if rewritten:
            continue

        # Pattern A: overpacked participial tail after comma.
        participle_match = re.search(
            rf",\s*((?:{'|'.join(re.escape(p) for p in participles)})\b[^.!?]*)$",
            core,
            flags=re.IGNORECASE,
        )
        if participle_match:
            prefix = core[: participle_match.start()].strip(" ,;")
            tail = participle_match.group(1).strip(" ,;")
            long_or_multi_clause = len(core) > 140 or any(marker in core.lower() for marker in clause_markers)
            if prefix and tail and long_or_multi_clause:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if rewritten:
            continue

        # Pattern C: implication phrase appended to a physical/scene clause.
        lowered_core = core.lower()
        implication_pos = -1
        implication_phrase = ""
        for phrase in implication_phrases:
            token = f" {phrase} "
            idx = lowered_core.find(token)
            if idx == -1:
                idx = lowered_core.find(f", {phrase} ")
            if idx != -1:
                implication_pos = idx + (2 if lowered_core[idx : idx + 2] == ", " else 1)
                implication_phrase = phrase
                break
        if implication_pos > 0 and len(core) > 120:
            prefix = core[:implication_pos].rstrip(" ,;")
            tail = core[implication_pos:].lstrip(" ,;")
            if implication_phrase and prefix and tail:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if not rewritten:
            rewritten_parts.append(sentence if _has_terminal_punctuation(sentence) else f"{core}{punct}")

    return _normalize_text(" ".join(rewritten_parts))


def _finalize_emission_output(out: Dict[str, Any], *, pre_gate_text: str) -> Dict[str, Any]:
    final_text = str(out.get("player_facing_text") or "")
    sanitized_text = _sanitize_output_text(final_text)
    decompressed_text = _decompress_overpacked_sentences(sanitized_text)
    repaired_text = decompressed_text
    fragment_repair_applied = False
    if decompressed_text != sanitized_text:
        repaired_text, fragment_repair_applied = _repair_fragmentary_participial_splits(decompressed_text)
    smoothed_text, sentence_micro_smoothing_applied = _micro_smooth_post_repair_sentences(repaired_text)
    sanitization_applied = sanitized_text != final_text
    sentence_decompression_applied = decompressed_text != sanitized_text
    out["player_facing_text"] = smoothed_text

    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    meta["output_sanitization_applied"] = sanitization_applied
    meta["sentence_decompression_applied"] = sentence_decompression_applied
    meta["sentence_fragment_repair_applied"] = fragment_repair_applied
    meta["sentence_micro_smoothing_applied"] = sentence_micro_smoothing_applied
    gate_out_text = _normalize_text(smoothed_text)
    meta["post_gate_mutation_detected"] = pre_gate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    out["_final_emission_meta"] = meta
    return out


def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return str(
        resolution.get("prompt")
        or resolution.get("label")
        or ((resolution.get("metadata") or {}).get("player_input") if isinstance(resolution.get("metadata"), dict) else "")
        or ""
    ).strip()


def _speaker_label(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if not isinstance(item, str) or not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _lowercase_leading_alpha(text: str) -> str:
    if not text:
        return ""
    chars = list(text)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.lower()
            break
    return "".join(chars)


def _join_entity_clauses(first_clause: str, second_clause: str) -> str:
    first = _normalize_text(first_clause)
    second = _normalize_text(second_clause)
    if not first:
        return second
    if not second:
        return first

    # If first clause already contains "while", avoid stacking it
    if " while " in first.lower():
        return f"{first}, and {second}"
    return f"{first}, while {second}"


def _opening_scene_preference_active(session: Dict[str, Any] | None) -> bool:
    if not isinstance(session, dict):
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    visited_scene_ids = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    return turn_counter <= 1 or (turn_counter == 0 and len(visited_scene_ids) <= 1)


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _augment_scene_with_runtime_visible_leads(
    scene: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if not isinstance(scene, dict):
        return scene
    if not isinstance(session, dict):
        return scene
    sid = str(scene_id or "").strip()
    if not sid:
        return scene
    runtime = get_scene_runtime(session, sid)
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if not isinstance(recent, list) or not recent:
        return scene

    extra_facts: List[str] = []
    for lead in recent[-4:]:
        if not isinstance(lead, dict):
            continue
        kind = str(lead.get("kind") or "").strip()
        if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
            continue
        subject = _normalize_text(lead.get("subject"))
        position = _normalize_text(lead.get("position"))
        if not subject:
            continue
        fact = f"{subject} lingers {position}" if position else f"{subject} lingers nearby"
        extra_facts.append(_output_sentence(fact))

    if not extra_facts:
        return scene

    if isinstance(scene.get("scene"), dict):
        outer = dict(scene)
        inner = dict(scene.get("scene") or {})
        existing = _scene_visible_facts(scene)
        inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
        outer["scene"] = inner
        return outer

    inner = dict(scene)
    existing = _scene_visible_facts(scene)
    inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
    return inner


def _passive_scene_pressure_due_for_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if not sid:
        return False
    runtime = get_scene_runtime(session, sid)
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_player_action_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    if not last_player_action_passive and passive_streak <= 0:
        return False
    visible_low = " ".join(fact.lower() for fact in _scene_visible_facts(scene))
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return bool(
        passive_streak >= 2
        or isinstance(recent, list)
        and any(isinstance(item, dict) for item in recent)
        or "guard" in visible_low
        or "watch" in visible_low
        or "missing patrol" in visible_low
        or "rumor" in visible_low
        or "rumour" in visible_low
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def _passive_scene_pressure_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    if not _passive_scene_pressure_due_for_fallback(session=session, scene=scene, scene_id=scene_id):
        return []

    sid = str(scene_id or "").strip()
    runtime = get_scene_runtime(session, sid) if isinstance(session, dict) and sid else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if isinstance(recent, list):
        for lead in reversed(recent[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                continue
            subject = _normalize_text(lead.get("subject"))
            position = _normalize_text(lead.get("position"))
            if not subject:
                continue
            move_from = f" leaves {position} and" if position else ""
            if passive_streak >= 2:
                return [
                    (
                        _output_sentence(
                            f'{subject}{move_from} comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail."'
                        ),
                        "passive_scene_pressure",
                        "passive_scene_pressure_lead_figure",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure:lead_figure",
                        _first_mention_composition_meta(),
                    )
                ]
            return [
                (
                    _output_sentence(
                        f'{subject}{move_from} cuts through the crowd and stops at your shoulder. "You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."'
                    ),
                    "passive_scene_pressure",
                    "passive_scene_pressure_lead_figure",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure:lead_figure",
                    _first_mention_composition_meta(),
                )
            ]

    visible_facts = _scene_visible_facts(scene)
    visible_low = " ".join(fact.lower() for fact in visible_facts)
    if "guard" in visible_low and "missing patrol" in visible_low:
        if passive_streak >= 2:
            text = (
                'The same guard does not let the silence stand a second time. "No more watching," he says, '
                "closing the distance and jabbing a finger at the east-road line on the notice. "
                '"Either tell me who sent you, or get moving before that trail cools for good."'
            )
        else:
            text = (
                'A guard peels away from the notice board and squares up to you. "Standing still won\'t help that patrol," '
                'he says, stabbing two fingers at the posting. "Tell me what you know, or get on the east-road trail before it dies."'
            )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_guard_rumor",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:guard_rumor",
                _first_mention_composition_meta(),
            )
        ]
    if "guard" in visible_low:
        text = (
            'A guard notices you lingering and comes over at once. "If you\'re waiting on trouble, it already passed the checkpoint," '
            'he says. "Take the east-road report or get clear."'
        )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_visible_figure",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:visible_figure",
                _first_mention_composition_meta(),
            )
        ]
    return [
        (
            _output_sentence(
                'The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. '
                '"Board, runner, or road," he says. "Pick one before the gate swallows the trail."'
            ),
            "passive_scene_pressure",
            "passive_scene_pressure_generic",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure:fallback",
            _first_mention_composition_meta(),
        )
    ]


def _visible_entity_catalog(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = {
        str(item).strip()
        for item in (contract.get("visible_entity_ids") or [])
        if isinstance(item, str) and str(item).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    inner = _scene_inner(scene)
    addressables = inner.get("addressables") if isinstance(inner.get("addressables"), list) else []
    world_npcs = world.get("npcs") if isinstance(world, dict) and isinstance(world.get("npcs"), list) else []
    world_npc_map = {
        str(row.get("id") or "").strip(): row
        for row in world_npcs
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    ordered_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append_row(entity_id: str, row: Dict[str, Any] | None) -> None:
        if not entity_id or entity_id in seen or entity_id not in visible_ids:
            return
        seen.add(entity_id)
        base = row if isinstance(row, dict) else {}
        display_name = str(base.get("name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (base.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        normalized_aliases = alias_map.get(entity_id) if isinstance(alias_map.get(entity_id), list) else []
        ordered_aliases = _dedupe_preserve_order(
            [display_name]
            + aliases
            + [str(alias).strip() for alias in normalized_aliases if isinstance(alias, str) and str(alias).strip()]
        )
        if not display_name and ordered_aliases:
            display_name = ordered_aliases[0].title()
        role_hints = [
            str(role).strip()
            for role in (base.get("address_roles") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        world_row = world_npc_map.get(entity_id)
        if isinstance(world_row, dict):
            world_role = str(world_row.get("role") or "").strip()
            if world_role:
                role_hints.append(world_role)
        ordered_rows.append(
            {
                "entity_id": entity_id,
                "display_name": display_name or entity_id.replace("_", " ").title(),
                "aliases": ordered_aliases,
                "role_hints": _dedupe_preserve_order(role_hints),
            }
        )

    for row in addressables:
        if not isinstance(row, dict):
            continue
        _append_row(str(row.get("id") or "").strip(), row)

    for entity_id in sorted(visible_ids):
        _append_row(entity_id, world_npc_map.get(entity_id))

    return ordered_rows


def _rewrite_visible_fact_as_explicit_intro(display_name: str, fact_text: str, phrases: List[str]) -> str:
    fact = _output_sentence(fact_text)
    if not fact:
        return ""
    if fact.lower().startswith(display_name.lower()):
        return fact
    for phrase in phrases:
        clean_phrase = _normalize_text(phrase).lower()
        if not clean_phrase:
            continue
        for pattern in (
            rf"^(?:A|An|The)\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
            rf"^One\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
        ):
            match = re.match(pattern, fact, flags=re.IGNORECASE)
            if not match:
                continue
            remainder = (match.group(1) or "").strip()
            if not remainder:
                return _output_sentence(display_name)
            return _output_sentence(f"{display_name} {remainder}")
    return ""


def _scene_grounding_clause(visible_facts: List[str], blocked_phrases: List[str]) -> str:
    blocked = [phrase.lower() for phrase in blocked_phrases if phrase]
    for fact in visible_facts:
        if not fact:
            continue
        lowered = fact.lower()
        if any(phrase in lowered for phrase in blocked):
            continue
        return _lowercase_leading_alpha(fact.rstrip(".!?"))
    return ""


def _default_first_mention_composition_layers() -> Dict[str, Any]:
    return {"environment": None, "motion": None, "entities": []}


def _first_mention_composition_meta(
    *,
    used: bool = False,
    environment: str | None = None,
    motion: str | None = None,
    entities: List[str] | None = None,
) -> Dict[str, Any]:
    layers = _default_first_mention_composition_layers()
    if environment:
        layers["environment"] = environment
    if motion:
        layers["motion"] = motion
    if isinstance(entities, list):
        layers["entities"] = [str(entity).strip() for entity in entities if isinstance(entity, str) and str(entity).strip()]
    return {
        "first_mention_composition_used": used,
        "first_mention_composition_layers": layers,
    }


def _fact_matches_keywords(fact: str, keywords: tuple[str, ...]) -> bool:
    lowered = fact.lower()
    return any(keyword in lowered for keyword in keywords)


def _first_fact_matching_keywords(
    visible_facts: List[str],
    keywords: tuple[str, ...],
    *,
    excluded: set[str] | None = None,
) -> str:
    blocked = excluded or set()
    for fact in visible_facts:
        if not fact or fact in blocked:
            continue
        for segment in _fact_segments(fact):
            if segment in blocked:
                continue
            if _fact_matches_keywords(segment, keywords):
                return _output_sentence(segment)
        if _fact_matches_keywords(fact, keywords):
            return fact
    return ""


_ENTITY_COMPOSITION_PREDICATE_STARTS: tuple[tuple[str, str], ...] = (
    ("hangs back", "hangs back"),
    ("calls out", "calls"),
    ("is shouting", "shouts"),
    ("are shouting", "shouts"),
    ("is calling", "calls"),
    ("are calling", "calls"),
    ("is offering", "offers"),
    ("are offering", "offers"),
    ("is watching", "watches"),
    ("are watching", "watches"),
    ("is scanning", "scans"),
    ("are scanning", "scans"),
    ("is studying", "studies"),
    ("are studying", "studies"),
    ("is gesturing", "gestures"),
    ("are gesturing", "gestures"),
    ("is lingering", "lingers"),
    ("are lingering", "lingers"),
    ("is waiting", "waits"),
    ("are waiting", "waits"),
    ("is observing", "observes"),
    ("are observing", "observes"),
    ("is surveying", "surveys"),
    ("are surveying", "surveys"),
    ("is exchanging", "exchanges"),
    ("are exchanging", "exchanges"),
    ("holds", "holds"),
    ("hold", "holds"),
    ("watches", "watches"),
    ("watch", "watches"),
    ("scans", "scans"),
    ("scan", "scans"),
    ("studies", "studies"),
    ("study", "studies"),
    ("shouts", "shouts"),
    ("shout", "shouts"),
    ("calls", "calls"),
    ("call", "calls"),
    ("offers", "offers"),
    ("offer", "offers"),
    ("gestures", "gestures"),
    ("gesture", "gestures"),
    ("lingers", "lingers"),
    ("linger", "lingers"),
    ("waits", "waits"),
    ("wait", "waits"),
    ("observes", "observes"),
    ("observe", "observes"),
    ("surveys", "surveys"),
    ("survey", "surveys"),
    ("exchanges", "exchanges"),
    ("exchange", "exchanges"),
    ("stands", "stands"),
    ("stand", "stands"),
    ("keeps", "keeps"),
    ("keep", "keeps"),
    ("looks", "looks"),
    ("look", "looks"),
    ("glances", "glances"),
    ("glance", "glances"),
    ("murmurs", "murmurs"),
    ("murmur", "murmurs"),
    ("whispers", "whispers"),
    ("whisper", "whispers"),
)
_LOW_INFO_ENTITY_PREDICATE_RE = re.compile(
    r"^(stands|shouts|watches|lingers|waits|scans|gestures)(?:\s+(nearby|there|quietly|silently|still|alone))?$",
    flags=re.IGNORECASE,
)
_ENTITY_DESCRIPTOR_STOPWORDS = {
    "captain",
    "guard",
    "runner",
    "informant",
    "watcher",
    "stranger",
    "refugee",
    "figure",
    "nearby",
    "still",
}
_ENTITY_ROLE_DETAIL_PHRASE_MAP: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("choke", "gate"), "holds the choke at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("line", "gate"), "holds the line at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("crowd",), "scans the crowd at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("gate",), "watches the gate"),
    (("runner", "informant"), ("stew", "rumor"), "calls over the noise with offers of hot stew and rumor"),
    (("runner", "informant"), ("stew",), "calls over the noise with offers of hot stew"),
    (("runner", "informant"), ("crowd",), "calls over the crowd"),
    (("watcher",), ("crowd",), "lingers at the edge of the crowd"),
    (("stranger", "refugee"), ("refugee", "crowd"), "hangs back from the press of refugees"),
    (("stranger", "refugee"), ("crowd",), "hangs back from the crowd"),
)


def _phrase_present(text: str, phrase: str) -> bool:
    clean_text = _normalize_text(text).lower()
    clean_phrase = _normalize_text(phrase).lower()
    if not clean_text or not clean_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(clean_phrase)}(?!\w)", clean_text))


def _entity_descriptor_tokens(display_name: str, aliases: List[str]) -> List[str]:
    tokens: List[str] = []
    for raw in [display_name] + list(aliases):
        for token in re.findall(r"[a-zA-Z][a-zA-Z'-]+", raw.lower()):
            if len(token) < 5 or token in _ENTITY_DESCRIPTOR_STOPWORDS:
                continue
            tokens.append(token)
    return _dedupe_preserve_order(tokens)


def _role_forms(role: str) -> List[str]:
    clean = _normalize_text(role).lower()
    if not clean:
        return []
    forms = [clean]
    if clean.endswith("y") and len(clean) > 1:
        forms.append(f"{clean[:-1]}ies")
    elif clean.endswith(("s", "x", "z", "ch", "sh")):
        forms.append(f"{clean}es")
    else:
        forms.append(f"{clean}s")
    return _dedupe_preserve_order(forms)


def _fact_segments(fact_text: str) -> List[str]:
    clean = _output_sentence(fact_text).rstrip(".!?")
    if not clean:
        return []
    segments = re.split(r"[;:]|(?<=[.!?])\s+", clean)
    return [segment.strip(" ,") for segment in segments if segment.strip(" ,")]


def _extract_leading_subject_and_predicate(segment: str) -> tuple[str, str]:
    clean = _normalize_text(segment)
    if not clean:
        return "", ""
    lowered = clean.lower()
    for predicate_start, _canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        match = re.search(rf"\b{re.escape(predicate_start)}\b", lowered)
        if not match:
            continue
        subject = clean[: match.start()].strip(" ,")
        predicate = clean[match.start() :].strip(" ,")
        if not subject or not predicate:
            continue
        if len(subject.split()) > 9:
            continue
        return subject, predicate
    return "", ""


def _subject_matches_entity(
    subject: str,
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    descriptor_tokens: List[str],
) -> bool:
    lowered_subject = _normalize_text(subject).lower()
    if not lowered_subject:
        return False
    for phrase in _dedupe_preserve_order([display_name] + aliases):
        if _phrase_present(lowered_subject, phrase):
            return True
    for role in role_hints:
        for form in _role_forms(role):
            if _phrase_present(lowered_subject, form):
                return True
    return any(token in lowered_subject for token in descriptor_tokens)


def _singularize_entity_predicate(predicate: str) -> str:
    clean = _normalize_text(predicate)
    if not clean:
        return ""
    lowered = clean.lower()
    replacements = (
        ("are now ", "is now "),
        ("are ", "is "),
        ("hang back", "hangs back"),
        ("hold ", "holds "),
        ("watch ", "watches "),
        ("scan ", "scans "),
        ("study ", "studies "),
        ("shout ", "shouts "),
        ("call ", "calls "),
        ("offer ", "offers "),
        ("gesture ", "gestures "),
        ("linger ", "lingers "),
        ("wait ", "waits "),
        ("observe ", "observes "),
        ("survey ", "surveys "),
        ("exchange ", "exchanges "),
        ("stand ", "stands "),
        ("keep ", "keeps "),
        ("look ", "looks "),
        ("glance ", "glances "),
        ("murmur ", "murmurs "),
        ("whisper ", "whispers "),
    )
    for old, new in replacements:
        if lowered == old.strip():
            return new.strip()
        if lowered.startswith(old):
            return f"{new}{clean[len(old):]}".strip()
    return clean


def _predicate_after_display_name(display_name: str, sentence: str) -> str:
    clean = _output_sentence(sentence).rstrip(".!?")
    if not clean:
        return ""
    lowered_clean = clean.lower()
    lowered_name = display_name.lower()
    if not lowered_clean.startswith(lowered_name):
        return ""
    return clean[len(display_name) :].strip(" ,;:-")


def _entity_predicate_signature(predicate: str) -> tuple[str, bool]:
    clean = _normalize_text(predicate).lower()
    if not clean:
        return "", True
    for predicate_start, canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        if clean == predicate_start or clean.startswith(f"{predicate_start} "):
            return canonical, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))
    first_token = clean.split()[0]
    return first_token, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))


def _composition_candidate(
    *,
    display_name: str,
    predicate: str,
    source_rank: int,
    source_index: int,
    fact_backed: bool,
) -> Dict[str, Any] | None:
    clean_predicate = _normalize_text(predicate).rstrip(".!?")
    if not clean_predicate:
        return None
    verb_key, low_info = _entity_predicate_signature(clean_predicate)
    detail_bonus = 0 if low_info else min(len(clean_predicate.split()), 8)
    return {
        "clause": f"{display_name} {clean_predicate}",
        "verb_key": verb_key,
        "low_info": low_info,
        "fact_backed": fact_backed,
        "score": (source_rank * 100) + detail_bonus,
        "source_index": source_index,
    }


def _generic_entity_intro_predicate(
    *,
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> str:
    signal_text = " ".join(fact.lower() for fact in composition_facts if isinstance(fact, str))
    role_set = {role.lower() for role in role_hints if isinstance(role, str) and role}
    for required_roles, required_tokens, predicate in _ENTITY_ROLE_DETAIL_PHRASE_MAP:
        if role_set.isdisjoint(required_roles):
            continue
        if all(token in signal_text for token in required_tokens):
            return predicate
    if "crowd" in signal_text:
        return "watches the crowd" if slot_index == 0 else "lingers at the edge of the crowd"
    if "gate" in signal_text:
        return "stands at the gate"
    return "watches nearby" if slot_index == 0 else "lingers nearby"


def _entity_clause_candidates(
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> List[Dict[str, Any]]:
    explicit_phrases = _dedupe_preserve_order([display_name] + aliases + role_hints)
    descriptor_tokens = _entity_descriptor_tokens(display_name, aliases)
    candidates: List[Dict[str, Any]] = []
    seen_clauses: set[str] = set()

    for fact_index, fact in enumerate(composition_facts):
        explicit_sentence = ""
        if fact.lower().startswith(display_name.lower()):
            explicit_sentence = fact
        else:
            explicit_sentence = _rewrite_visible_fact_as_explicit_intro(display_name, fact, explicit_phrases)
        if explicit_sentence:
            predicate = _predicate_after_display_name(display_name, explicit_sentence)
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=predicate,
                source_rank=3,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)
        for segment in _fact_segments(fact):
            subject, predicate = _extract_leading_subject_and_predicate(segment)
            if not subject or not predicate:
                continue
            if not _subject_matches_entity(
                subject,
                display_name=display_name,
                aliases=aliases,
                role_hints=role_hints,
                descriptor_tokens=descriptor_tokens,
            ):
                continue
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=_singularize_entity_predicate(predicate),
                source_rank=2,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)

    generic_candidate = _composition_candidate(
        display_name=display_name,
        predicate=_generic_entity_intro_predicate(
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=slot_index,
        ),
        source_rank=1,
        source_index=len(composition_facts),
        fact_backed=False,
    )
    if generic_candidate and generic_candidate["clause"] not in seen_clauses:
        candidates.append(generic_candidate)

    candidates.sort(
        key=lambda item: (
            -int(item.get("score", 0)),
            int(item.get("source_index", 10**6)),
            len(str(item.get("clause") or "")),
        )
    )
    return candidates


def _visible_safe_scene_composition_facts(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[str]:
    inner = _scene_inner(scene)
    raw_candidates: List[str] = list(_scene_visible_facts(scene))
    summary = _output_sentence(str(inner.get("summary") or ""))
    if summary:
        raw_candidates.append(summary)
    raw_journal_seed_facts = inner.get("journal_seed_facts") if isinstance(inner.get("journal_seed_facts"), list) else []
    for item in raw_journal_seed_facts:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            raw_candidates.append(clean)

    visible_safe_facts: List[str] = []
    for candidate in _dedupe_preserve_order(raw_candidates):
        validation = validate_player_facing_visibility(
            candidate,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            visible_safe_facts.append(candidate)
    return visible_safe_facts


def _build_composed_scene_intro(
    narration_visibility: Dict[str, Any],
    visible_entities: List[str],
    composition_facts: List[str],
    scene_context: Dict[str, Any],
) -> str | None:
    scene_context["composition_layers"] = _default_first_mention_composition_layers()
    if not isinstance(narration_visibility, dict) or not composition_facts or not visible_entities:
        return None

    environment = _first_fact_matching_keywords(
        composition_facts,
        (
            "rain",
            "snow",
            "wind",
            "fog",
            "mist",
            "smoke",
            "ash",
            "mud",
            "muddy",
            "stone",
            "gate",
            "wall",
            "square",
            "yard",
            "district",
            "alley",
            "alleyway",
            "tavern",
            "banner",
            "banners",
            "ground",
            "earth",
            "puddle",
            "puddles",
            "crate",
            "crates",
            "path",
            "thicket",
            "milestone",
            "millstone",
            "underbrush",
            "breeze",
        ),
    )
    if not environment:
        return None

    motion = _first_fact_matching_keywords(
        composition_facts,
        (
            "crowd",
            "refugee",
            "refugees",
            "wagon",
            "wagons",
            "traffic",
            "patron",
            "patrons",
            "townsfolk",
            "onlookers",
            "voices",
            "whisper",
            "whispers",
            "murmur",
            "murmurs",
            "shout",
            "shouts",
            "queue",
            "presses",
            "press in",
            "pushes",
            "scan",
            "scans",
            "glance",
            "glances",
            "watch newcomers",
            "tension",
            "tense",
            "agitation",
            "unrest",
            "shift uneasily",
        ),
        excluded={environment},
    )

    entity_rows_by_display_name = (
        scene_context.get("entity_rows_by_display_name")
        if isinstance(scene_context.get("entity_rows_by_display_name"), dict)
        else {}
    )
    visible_entity_ids = {
        str(entity_id).strip()
        for entity_id in (narration_visibility.get("visible_entity_ids") or [])
        if isinstance(entity_id, str) and str(entity_id).strip()
    }
    selected_entity_names: List[str] = []
    for entity_name in visible_entities:
        clean_name = _normalize_text(entity_name)
        if not clean_name or clean_name in selected_entity_names:
            continue
        row = entity_rows_by_display_name.get(clean_name) if isinstance(entity_rows_by_display_name, dict) else None
        entity_id = str((row or {}).get("entity_id") or "").strip() if isinstance(row, dict) else ""
        if visible_entity_ids and entity_id and entity_id not in visible_entity_ids:
            continue
        selected_entity_names.append(clean_name)
    if not selected_entity_names:
        return None

    selected_entity_clauses: List[Dict[str, Any]] = []
    used_verb_keys: set[str] = set()
    for index, entity_name in enumerate(selected_entity_names):
        row = entity_rows_by_display_name.get(entity_name) if isinstance(entity_rows_by_display_name, dict) else {}
        aliases = [
            str(alias).strip()
            for alias in ((row or {}).get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in ((row or {}).get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        clause_candidates = _entity_clause_candidates(
            display_name=entity_name,
            aliases=aliases,
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=index,
        )
        chosen_candidate: Dict[str, Any] | None = None
        for candidate in clause_candidates:
            verb_key = str(candidate.get("verb_key") or "")
            if not selected_entity_clauses:
                chosen_candidate = candidate
                break
            if verb_key and verb_key in used_verb_keys and bool(candidate.get("low_info")):
                continue
            if len(selected_entity_clauses) >= 1 and not bool(candidate.get("fact_backed")):
                continue
            chosen_candidate = candidate
            break
        if not chosen_candidate:
            continue
        selected_entity_clauses.append(
            {
                "entity_name": entity_name,
                "clause": str(chosen_candidate.get("clause") or ""),
                "verb_key": str(chosen_candidate.get("verb_key") or ""),
                "fact_backed": bool(chosen_candidate.get("fact_backed")),
                "low_info": bool(chosen_candidate.get("low_info")),
            }
        )
        verb_key = str(chosen_candidate.get("verb_key") or "")
        if verb_key:
            used_verb_keys.add(verb_key)
        if len(selected_entity_clauses) >= 2:
            break
    if not selected_entity_clauses:
        return None

    entity_sentence = selected_entity_clauses[0]["clause"]
    if len(selected_entity_clauses) > 1:
        first_clause = selected_entity_clauses[0]
        second_clause = selected_entity_clauses[1]
        if (
            first_clause["verb_key"]
            and second_clause["verb_key"]
            and first_clause["verb_key"] != second_clause["verb_key"]
            and not second_clause["low_info"]
        ):
            entity_sentence = _join_entity_clauses(
                first_clause["clause"],
                second_clause["clause"],
            )

    scene_sentence = environment.rstrip(".!?")
    if motion:
        scene_sentence = f"{scene_sentence} while {_lowercase_leading_alpha(motion.rstrip('.!?'))}"

    scene_context["composition_layers"] = {
        "environment": environment,
        "motion": motion or None,
        "entities": [str(item.get("entity_name") or "") for item in selected_entity_clauses if str(item.get("entity_name") or "")],
    }
    return f"{_output_sentence(scene_sentence)} {_output_sentence(entity_sentence)}".strip()


def _grounded_scene_intro_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    active_interlocutor: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    visible_facts = _scene_visible_facts(scene)
    composition_facts = _visible_safe_scene_composition_facts(session=session, scene=scene, world=world)
    entity_rows = _visible_entity_catalog(session=session, scene=scene, world=world)
    if not entity_rows and not composition_facts and not visible_facts:
        return []

    narration_visibility = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    inner = _scene_inner(scene)
    scene_location = str(inner.get("location") or inner.get("id") or "").strip()
    prioritized_entities: List[Dict[str, Any]] = []
    if active_interlocutor:
        for row in entity_rows:
            if str(row.get("entity_id") or "").strip() == active_interlocutor:
                prioritized_entities.append(row)
                break
    for row in entity_rows:
        if row not in prioritized_entities:
            prioritized_entities.append(row)

    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    composed_scene_context: Dict[str, Any] = {
        "scene_location": scene_location,
        "entity_rows_by_display_name": {
            str(row.get("display_name") or "").strip(): row
            for row in prioritized_entities
            if isinstance(row, dict) and str(row.get("display_name") or "").strip()
        },
    }
    composed_scene_intro = _build_composed_scene_intro(
        narration_visibility,
        [str(row.get("display_name") or "").strip() for row in prioritized_entities if str(row.get("display_name") or "").strip()],
        composition_facts,
        composed_scene_context,
    )
    composed_layers = composed_scene_context.get("composition_layers")
    if composed_scene_intro and isinstance(composed_layers, dict):
        fallback_candidates.append(
            (
                composed_scene_intro,
                "visible_scene_composed_intro",
                "first_mention_composed_scene_intro",
                "composed_visible_scene_intro",
                "composed_visible_scene_intro",
                "visible_scene_composed_intro",
                _first_mention_composition_meta(
                    used=True,
                    environment=str(composed_layers.get("environment") or "") or None,
                    motion=str(composed_layers.get("motion") or "") or None,
                    entities=composed_layers.get("entities") if isinstance(composed_layers.get("entities"), list) else [],
                ),
            )
        )

    for row in prioritized_entities:
        entity_id = str(row.get("entity_id") or "").strip()
        display_name = str(row.get("display_name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (row.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in (row.get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        subject_phrases = _dedupe_preserve_order(aliases + role_hints)

        explicit_fact_intro = ""
        for fact in visible_facts:
            explicit_fact_intro = _rewrite_visible_fact_as_explicit_intro(display_name, fact, subject_phrases)
            if explicit_fact_intro:
                break
        if explicit_fact_intro:
            fallback_candidates.append(
                (
                    explicit_fact_intro,
                    "visible_scene_explicit_intro",
                    "first_mention_explicit_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    f"visible_entity:{entity_id}",
                    _first_mention_composition_meta(),
                )
            )

        grounding_clause = _scene_grounding_clause(visible_facts, subject_phrases)
        if scene_location and grounding_clause:
            generic_intro = f"{display_name} stands in {scene_location} while {grounding_clause}."
        elif scene_location:
            generic_intro = f"{display_name} stands in {scene_location}."
        elif grounding_clause:
            generic_intro = f"{display_name} stands nearby while {grounding_clause}."
        else:
            generic_intro = f"{display_name} stands nearby."
        fallback_candidates.append(
            (
                _output_sentence(generic_intro),
                "visible_scene_explicit_intro",
                "first_mention_explicit_scene_intro",
                "explicit_visible_entity_scene_intro",
                "explicit_visible_entity_scene_intro",
                f"visible_entity:{entity_id}",
                _first_mention_composition_meta(),
            )
        )

    for index, fact in enumerate(visible_facts):
        fallback_candidates.append(
            (
                fact,
                "visible_scene_fact_intro",
                "first_mention_visible_fact_intro",
                "visible_fact_scene_intro",
                "visible_fact_scene_intro",
                f"visible_fact:{index}",
                _first_mention_composition_meta(),
            )
        )

    deduped_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    seen_candidates = set()
    for candidate in fallback_candidates:
        candidate_key = candidate[:6]
        if candidate_key in seen_candidates:
            continue
        seen_candidates.add(candidate_key)
        deduped_candidates.append(candidate)
    return deduped_candidates


def _build_visibility_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "matched_entity_id": violation.get("matched_entity_id"),
                "matched_fact": violation.get("matched_fact"),
            }
        )
    return sample


def _build_referential_clarity_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "candidate_entity_ids": list(violation.get("candidate_entity_ids") or []),
                "candidate_aliases": list(violation.get("candidate_aliases") or []),
                "sentence_text": str(violation.get("sentence_text") or ""),
                "offset": violation.get("offset"),
            }
        )
    return sample


_LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS = frozenset(
    {"he", "she", "they", "him", "her", "them"}
)
_REF_REPAIR_PERSON_LIKE_KINDS = frozenset({"npc", "scene_actor", "creature", "humanoid", "person"})


def _strict_social_answer_payload_signals(clean: str) -> bool:
    """True when dialogue carries bounded answer, refusal-with-reason, clue, or concrete direction."""
    if candidate_satisfies_answer_contract(clean)[0]:
        return True
    if any(p.search(clean) for p in _ANSWER_DIRECT_PATTERNS):
        return True
    low = clean.lower()
    if re.search(
        r"\b(?:can'?t|cannot|won'?t|not (?:here|safe)|no names|won'?t name|too risky|wrong place)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(?:east|west|north|south|gate|road|lane|checkpoint|pier|market|dock|wharf)\b",
        low,
    ):
        return True
    if re.search(r"\b(?:if you (?:want|need)|check (?:the|with)|ask (?:at|about))\b", low):
        return True
    if re.search(r"\b(?:patrol|watch(?:ers)?|sentries|crowd|ears (?:are )?open|listening)\b", low):
        return True
    if re.search(r"\b(?:note|letter|slips? you|hands? you)\b", low):
        return True
    return False


def _strict_social_dialogue_substantive_for_local_ref_repair(text: str) -> bool:
    """Conservative gate: repair only when the line already carries a useful answer payload."""
    clean = _normalize_text(text)
    if len(clean) < 28:
        return False
    if re.search(r"\bstarts to answer\b", clean, re.IGNORECASE):
        return False
    if is_route_illegal_global_or_sanitizer_fallback_text(clean):
        return False
    return _strict_social_answer_payload_signals(clean)


def _strict_social_eff_npc_id_matches_interlocutor(
    eff_resolution: Dict[str, Any] | None, active_interlocutor: str
) -> bool:
    aid = str(active_interlocutor or "").strip()
    if not aid:
        return False
    if not isinstance(eff_resolution, dict):
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    nid = str(soc.get("npc_id") or "").strip()
    if nid and nid != aid:
        return False
    return True


def _active_interlocutor_visible_person_like(
    active_interlocutor: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> bool:
    aid = str(active_interlocutor or "").strip()
    if not aid:
        return False
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = [
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    if aid not in visible_ids:
        return False
    kinds = contract.get("visible_entity_kinds") if isinstance(contract.get("visible_entity_kinds"), dict) else {}
    kind = str(kinds.get(aid) or "").strip().lower()
    return kind in _REF_REPAIR_PERSON_LIKE_KINDS


def _grounded_speaker_phrase_for_pronoun_substitution(
    *,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
    pronoun_surface: str,
) -> str:
    label = (
        _speaker_label(eff_resolution)
        if isinstance(eff_resolution, dict)
        else _npc_display_name_for_emission(world, scene_id, active_interlocutor)
    )
    base = str(label or "").strip()
    if not base:
        base = _npc_display_name_for_emission(world, scene_id, active_interlocutor)
    core = base
    low = core.lower()
    if low.startswith("the "):
        core = core[4:].lstrip()
    phrase = f"the {core}".strip()
    if pronoun_surface[:1].isupper():
        return phrase[:1].upper() + phrase[1:]
    return phrase


def _violations_eligible_for_strict_social_local_pronoun_repair(violations: List[Dict[str, Any]]) -> bool:
    if len(violations) != 1:
        return False
    v = violations[0]
    if not isinstance(v, dict):
        return False
    if str(v.get("kind") or "").strip() != "ambiguous_entity_reference":
        return False
    cids = v.get("candidate_entity_ids")
    if isinstance(cids, list) and len(cids) > 1:
        return False
    return True


def _pronoun_violation_candidate_ids_align_with_interlocutor(
    violation: Dict[str, Any], active_interlocutor: str
) -> bool:
    aid = str(active_interlocutor or "").strip()
    cids = violation.get("candidate_entity_ids")
    if not isinstance(cids, list) or len(cids) == 0:
        return True
    if len(cids) == 1:
        return str(cids[0]).strip() == aid
    return False


def _try_strict_social_local_pronoun_substitution_repair(
    candidate_text: str,
    *,
    violations: List[Dict[str, Any]],
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
) -> tuple[str | None, Dict[str, Any]]:
    """Replace one ambiguous pronoun with the grounded interlocutor label; no clause moves or paraphrase."""
    dbg: Dict[str, Any] = {
        "referential_clarity_local_substitution_attempted": False,
        "referential_clarity_local_substitution_applied": False,
        "referential_clarity_local_substitution_token": None,
        "referential_clarity_local_substitution_replacement": None,
        "referential_clarity_fallback_avoided": False,
        "referential_clarity_fallback_after_failed_local_repair": False,
    }
    if not candidate_text.strip():
        return None, dbg
    if not _violations_eligible_for_strict_social_local_pronoun_repair(violations):
        return None, dbg
    v0 = violations[0]
    if not _pronoun_violation_candidate_ids_align_with_interlocutor(v0, active_interlocutor):
        return None, dbg
    token = str(v0.get("token") or "").strip().lower()
    if token not in _LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS:
        return None, dbg
    sens = _split_visibility_sentences(candidate_text)
    if len(sens) != 1:
        return None, dbg
    try:
        pat = re.compile(rf"(?<!\w){re.escape(token)}(?!\w)", re.IGNORECASE)
    except re.error:
        return None, dbg
    matches = list(pat.finditer(candidate_text))
    if len(matches) != 1:
        return None, dbg
    m = matches[0]
    if not _strict_social_eff_npc_id_matches_interlocutor(eff_resolution, active_interlocutor):
        return None, dbg
    if not _active_interlocutor_visible_person_like(
        active_interlocutor, session=session, scene=scene, world=world
    ):
        return None, dbg
    if not _strict_social_dialogue_substantive_for_local_ref_repair(candidate_text):
        return None, dbg
    replacement = _grounded_speaker_phrase_for_pronoun_substitution(
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
        pronoun_surface=m.group(0),
    )
    repaired = pat.sub(replacement, candidate_text, count=1)
    if repaired == candidate_text:
        return None, dbg
    dbg["referential_clarity_local_substitution_attempted"] = True
    dbg["referential_clarity_local_substitution_token"] = m.group(0)
    dbg["referential_clarity_local_substitution_replacement"] = replacement
    sess = session if isinstance(session, dict) else None
    sc = scene if isinstance(scene, dict) else None
    w = world if isinstance(world, dict) else None
    ref2 = validate_player_facing_referential_clarity(repaired, session=sess, scene=sc, world=w)
    if ref2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    fm2 = validate_player_facing_first_mentions(repaired, session=sess, scene=sc, world=w)
    if fm2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    vis2 = validate_player_facing_visibility(repaired, session=sess, scene=sc, world=w)
    if vis2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    dbg["referential_clarity_local_substitution_applied"] = True
    dbg["referential_clarity_fallback_avoided"] = True
    return repaired, dbg


def _apply_default_referential_clarity_meta(meta: Dict[str, Any], *, passed: bool | None) -> None:
    meta["referential_clarity_validation_passed"] = passed
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = []
    meta["referential_clarity_checked_entities"] = []
    meta["referential_clarity_violation_sample"] = []
    meta["referential_clarity_local_substitution_attempted"] = False
    meta["referential_clarity_local_substitution_applied"] = False
    meta["referential_clarity_local_substitution_token"] = None
    meta["referential_clarity_local_substitution_replacement"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False


def _standard_visibility_safe_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    enforce_first_mentions: bool = False,
    enforce_referential_clarity: bool = False,
    prefer_grounded_scene_intro: bool = False,
) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    validation_scene = _augment_scene_with_runtime_visible_leads(
        scene,
        session=session if isinstance(session, dict) else None,
        scene_id=scene_id,
    )
    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []

    if strict_social_active and isinstance(eff_resolution, dict):
        social_fallback = minimal_social_emergency_fallback_line(eff_resolution)
        fallback_candidates.append(
            (
                social_fallback,
                "strict_social_visibility_minimal",
                "visibility_minimal_social_fallback",
                "minimal_social_emergency_fallback",
                "standard_safe_fallback",
                "minimal_social_emergency_fallback",
                _first_mention_composition_meta(),
            )
        )
    else:
        fallback_candidates.extend(
            _passive_scene_pressure_fallback_candidates(
                session=session if isinstance(session, dict) else None,
                scene=scene,
                scene_id=scene_id,
            )
        )
        if prefer_grounded_scene_intro:
            fallback_candidates.extend(
                _grounded_scene_intro_fallback_candidates(
                    session=session,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene,
                    world=world,
                    active_interlocutor=active_interlocutor,
                )
            )

    sid = str(scene_id or "").strip()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
        and not strict_social_active
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_candidates.append(
            (
                minimal_social_emergency_fallback_line(mini_res),
                "social_active_interlocutor_minimal",
                "social_interlocutor_fallback",
                "social_interlocutor_minimal_fallback",
                "standard_safe_fallback",
                "social_interlocutor_minimal_fallback",
                _first_mention_composition_meta(),
            )
        )

    if _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
        fallback_candidates.append(
            (
                "Nothing confirms progress toward that lead yet—the moment stays unresolved.",
                "npc_pursuit_fail_closed_neutral",
                "npc_pursuit_neutral_nonprogress",
                "npc_pursuit_neutral_fallback",
                "standard_safe_fallback",
                "npc_pursuit_neutral_fallback",
                _first_mention_composition_meta(),
            )
        )
    elif not strict_social_active and not _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    ):
        fallback_candidates.append(
            (
                "For a breath, the scene holds while voices shift around you.",
                "global_scene_narrative",
                "narrative_safe_fallback",
                "global_scene_fallback",
                "standard_safe_fallback",
                "global_scene_fallback",
                _first_mention_composition_meta(),
            )
        )

    for (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) in fallback_candidates:
        if not _normalize_text(fallback_text):
            continue
        validation = validate_player_facing_visibility(
            fallback_text,
            session=session if isinstance(session, dict) else None,
            scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            if enforce_first_mentions:
                first_mention_validation = validate_player_facing_first_mentions(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if first_mention_validation.get("ok") is not True:
                    continue
            if enforce_referential_clarity:
                referential_clarity_validation = validate_player_facing_referential_clarity(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if referential_clarity_validation.get("ok") is not True:
                    continue
            return (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                fallback_strategy,
                fallback_candidate_source,
                composition_meta,
            )

    if strict_social_active and isinstance(eff_resolution, dict):
        return (
            minimal_social_emergency_fallback_line(eff_resolution),
            "strict_social_visibility_minimal",
            "visibility_minimal_social_fallback",
            "minimal_social_emergency_fallback",
            "standard_safe_fallback",
            "minimal_social_emergency_fallback",
            _first_mention_composition_meta(),
        )

    passive_candidates = _passive_scene_pressure_fallback_candidates(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    )
    if passive_candidates:
        fallback_text, fallback_pool, fallback_kind, final_emitted_source, fallback_strategy, fallback_candidate_source, composition_meta = passive_candidates[0]
        return (
            fallback_text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            fallback_strategy,
            fallback_candidate_source,
            composition_meta,
        )

    return (
        "For a breath, the scene holds while voices shift around you.",
        "global_scene_narrative",
        "narrative_safe_fallback",
        "global_scene_fallback",
        "standard_safe_fallback",
        "global_scene_fallback",
        _first_mention_composition_meta(),
    )


def _apply_first_mention_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_first_mentions(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    leading_pronoun_detected = bool(validation.get("leading_pronoun_detected"))
    first_explicit_entity_offset = validation.get("first_explicit_entity_offset")
    if not isinstance(first_explicit_entity_offset, int):
        first_explicit_entity_offset = None

    meta["first_mention_validation_passed"] = validation.get("ok") is True
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = violation_kinds
    meta["first_mention_checked_entities"] = checked_entities
    meta["first_mention_leading_pronoun_detected"] = leading_pronoun_detected
    meta["first_mention_first_explicit_entity_offset"] = first_explicit_entity_offset
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    _apply_default_referential_clarity_meta(meta, passed=None)
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_referential_clarity_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        meta["first_mention_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    opening_scene_preference_used = _opening_scene_preference_active(session)
    prefer_grounded_scene_intro = True

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
        prefer_grounded_scene_intro=prefer_grounded_scene_intro,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "first_mention_enforcement_replaced"]
        + [f"first_mention_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:first_mention_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["first_mention_validation_passed"] = False
    meta["first_mention_replacement_applied"] = True
    meta["first_mention_fallback_strategy"] = fallback_strategy
    meta["first_mention_fallback_candidate_source"] = fallback_candidate_source
    meta["opening_scene_first_mention_preference_used"] = opening_scene_preference_used
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_first_mention",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_first_mention_replace"})
    return _apply_referential_clarity_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )


def _referential_clarity_violations_have_multi_entity_candidates(violations: List[Dict[str, Any]]) -> bool:
    for v in violations:
        if not isinstance(v, dict):
            continue
        cids = v.get("candidate_entity_ids")
        if isinstance(cids, list) and len(cids) > 1:
            return True
    return False


def _referential_clarity_violations_only_dialogue_attribution_they(violations: List[Dict[str, Any]]) -> bool:
    if not violations:
        return False
    for v in violations:
        if not isinstance(v, dict):
            return False
        if str(v.get("kind") or "").strip() != "ambiguous_entity_reference":
            return False
        st = str(v.get("sentence_text") or "").strip()
        if not st or not _DIALOGUE_ATTRIBUTION_THEY_SPEECH_TAG.search(st):
            return False
    return True


def _apply_referential_clarity_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_referential_clarity(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    meta["referential_clarity_validation_passed"] = validation.get("ok") is True
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = violation_kinds
    meta["referential_clarity_checked_entities"] = checked_entities
    meta["referential_clarity_violation_sample"] = _build_referential_clarity_violation_sample(violations)
    meta["referential_clarity_local_substitution_attempted"] = False
    meta["referential_clarity_local_substitution_applied"] = False
    meta["referential_clarity_local_substitution_token"] = None
    meta["referential_clarity_local_substitution_replacement"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return out

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        if not violations:
            meta["referential_clarity_validation_passed"] = None
            out["_final_emission_meta"] = meta
            return out
        if not _referential_clarity_violations_have_multi_entity_candidates(violations) and (
            _referential_clarity_violations_only_dialogue_attribution_they(violations)
        ):
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            out["_final_emission_meta"] = meta
            return out

    response_type_req = str(meta.get("response_type_required") or "").strip().lower()
    if (
        strict_social_active
        and response_type_req == "dialogue"
        and not strict_social_suppressed_non_social_turn
    ):
        repaired, subst_dbg = _try_strict_social_local_pronoun_substitution_repair(
            candidate_text,
            violations=[v for v in violations if isinstance(v, dict)],
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
        )
        for k, val in subst_dbg.items():
            meta[k] = val
        if repaired is not None:
            out["player_facing_text"] = repaired
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            tags = out.get("tags") if isinstance(out.get("tags"), list) else []
            out["tags"] = _dedupe_preserve_order(
                [str(t) for t in tags if isinstance(t, str)] + ["referential_clarity_local_substitution"]
            )
            gate_out_text = _normalize_text(out.get("player_facing_text"))
            meta["post_gate_mutation_detected"] = bool(meta.get("post_gate_mutation_detected")) or (
                candidate_text != gate_out_text
            )
            meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
            out["_final_emission_meta"] = meta
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate_referential_clarity",
                    "social_route": strict_social_active,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": "referential_clarity_local_substitution",
                    "fallback_kind": "none",
                    "active_interlocutor": active_interlocutor or None,
                }
            )
            log_final_emission_trace(
                {**meta, "stage": "final_emission_gate_referential_clarity_local_substitution"}
            )
            return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "referential_clarity_enforcement_replaced"]
        + [f"referential_clarity_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:referential_clarity_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["referential_clarity_validation_passed"] = False
    meta["referential_clarity_replacement_applied"] = True
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_referential_clarity",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
            "referential_clarity_fallback_after_failed_local_repair": bool(
                meta.get("referential_clarity_fallback_after_failed_local_repair")
            ),
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_referential_clarity_replace"})
    return out


def _apply_visibility_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_visibility(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = (
        validation.get("visibility_checked_entities")
        if isinstance(validation.get("visibility_checked_entities"), list)
        else []
    )
    checked_facts = (
        validation.get("visibility_checked_facts")
        if isinstance(validation.get("visibility_checked_facts"), list)
        else []
    )
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )

    meta["first_mention_validation_passed"] = None
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = []
    meta["first_mention_checked_entities"] = []
    meta["first_mention_leading_pronoun_detected"] = False
    meta["first_mention_first_explicit_entity_offset"] = None
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    _apply_default_referential_clarity_meta(meta, passed=None)
    meta["visibility_validation_passed"] = validation.get("ok") is True
    meta["visibility_replacement_applied"] = False
    meta["visibility_violation_kinds"] = violation_kinds
    meta["visibility_violation_sample"] = _build_visibility_violation_sample(violations)
    meta["visibility_checked_entities"] = checked_entities
    meta["visibility_checked_facts"] = checked_facts
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_first_mention_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )

    tag_list_gate = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    dbg_gate = str(out.get("debug_notes") or "")
    if (
        "known_fact_guard" in tag_list_gate
        and "recent_dialogue_continuity" in dbg_gate
        and violation_kinds == ["unseen_entity_reference"]
    ):
        meta["visibility_validation_passed"] = True
        meta["visibility_replacement_applied"] = False
        meta["visibility_continuity_lead_exemption"] = True
        out["_final_emission_meta"] = meta
        return _apply_first_mention_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )

    if not checked_entities and not checked_facts and _reply_already_has_concrete_interaction(candidate_text):
        meta["visibility_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "visibility_enforcement_replaced"]
        + [f"visibility_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:visibility_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["visibility_validation_passed"] = False
    meta["visibility_replacement_applied"] = True
    meta["visibility_fallback_pool"] = fallback_pool
    meta["visibility_fallback_kind"] = fallback_kind
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_visibility",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_visibility_replace"})
    return out


def _should_use_neutral_nonprogress_fallback_instead_of_global_stock(
    session: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> bool:
    """Parser-built NPC-target pursuit turns without grounded contact must not get the stock 'voices shift' line."""
    if not isinstance(session, dict):
        return False
    ctx = session.get(NPC_PURSUIT_CONTACT_SESSION_KEY)
    if not isinstance(ctx, dict):
        return False
    if str(ctx.get("commitment_source") or "").strip() != "explicit_player_pursuit":
        return False
    if not isinstance(eff_resolution, dict):
        return False
    rk = str(eff_resolution.get("kind") or "").strip().lower()
    if rk not in SOCIAL_KINDS:
        return False
    target = str(ctx.get("target_npc_id") or "").strip()
    if not target:
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    if soc.get("offscene_target"):
        return True
    gs = str(soc.get("grounded_speaker_id") or "").strip()
    if gs and gs == target:
        return False
    if soc.get("target_resolved") is True and str(soc.get("npc_id") or "").strip() == target:
        return False
    return True


# --- Speaker selection contract (Block 1 authority) — validation + repair at final emission ---

_SPEAKER_REASON_SPEAKER_CONTRACT_MATCH = "speaker_contract_match"
_SPEAKER_REASON_SPEAKER_BINDING_MISMATCH = "speaker_binding_mismatch"
_SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER = "forbidden_generic_fallback_speaker"
_SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH = "unjustified_speaker_switch"
_SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT = "interruption_without_contract_support"
_SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH = "interruption_justified_switch"
_SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR = "continuity_locked_speaker_repair"
_SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE = "canonical_speaker_rewrite"
_SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER = "narrator_neutral_no_allowed_speaker"

SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES: tuple[str, ...] = (
    _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
    _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
    _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
    _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
    _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
    _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
    _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR,
    _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE,
    _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
)

_SPEECH_VERB_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|asks|asked|adds|added)\b",
    re.IGNORECASE,
)
_BEAT_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
# Leading "…" dialogue + pronoun + attribution verb: label is the pronoun only (not the quoted span).
_QUOTED_THEN_PRONOUN_SPEECH_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|"
    r"asks|asked|adds|added|insists|insisted)\b",
    re.IGNORECASE,
)
_QUOTED_THEN_PRONOUN_BEAT_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
_NON_NAME_ATTRIBUTION_PREFIXES = frozenset(
    {
        "he",
        "she",
        "they",
        "it",
        "someone",
        "a voice",
        "the voice",
        "another voice",
    }
)


def _empty_speaker_selection_contract() -> Dict[str, Any]:
    return {
        "primary_speaker_id": None,
        "primary_speaker_name": None,
        "allowed_speaker_ids": [],
        "continuity_locked": False,
        "continuity_lock_reason": None,
        "speaker_switch_allowed": True,
        "speaker_switch_reason": None,
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "generic_fallback_forbidden": False,
        "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": True},
    }


def get_speaker_selection_contract(
    resolution: Dict[str, Any] | None,
    metadata: Dict[str, Any] | None = None,
    trace: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Load Block 1 speaker contract: metadata emission_debug first, then resolution/trace copies."""
    empty = _empty_speaker_selection_contract()

    def _from_emission_debug(em: Any) -> Dict[str, Any] | None:
        if not isinstance(em, dict):
            return None
        c = em.get("speaker_selection_contract")
        return c if isinstance(c, dict) and c else None

    if isinstance(metadata, dict):
        hit = _from_emission_debug(metadata.get("emission_debug"))
        if hit is not None:
            return hit

    if isinstance(resolution, dict):
        md = resolution.get("metadata")
        if isinstance(md, dict):
            hit = _from_emission_debug(md.get("emission_debug"))
            if hit is not None:
                return hit

    if isinstance(trace, dict):
        tc = trace.get("speaker_selection_contract")
        if isinstance(tc, dict) and tc:
            return tc
        hit = _from_emission_debug(trace.get("emission_debug"))
        if hit is not None:
            return hit

    return empty


def detect_emitted_speaker_signature(
    text: str,
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Infer opening attribution / dialogue-ownership cues from emitted text."""
    t = _normalize_text(text)
    speaker_label: str | None = None
    speaker_name: str | None = None
    is_explicit = False
    confidence: str = "low"

    mq = _QUOTED_THEN_PRONOUN_SPEECH_RE.match(t)
    if not mq:
        mq = _QUOTED_THEN_PRONOUN_BEAT_RE.match(t)
    if mq:
        raw = str(mq.group(1) or "").strip()
        low = raw.lower()
        speaker_label = raw
        if low and low not in _NON_NAME_ATTRIBUTION_PREFIXES:
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            confidence = "medium"
        forbidden = list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
        is_generic_fb = False
        if speaker_label:
            sl = speaker_label.strip().lower()
            for fb in forbidden:
                fbl = str(fb or "").strip().lower()
                if fbl and (fbl == sl or fbl in sl or sl in fbl):
                    is_generic_fb = True
                    break
        intr = bool(interruption_cue_present_in_text(t) or _has_explicit_interruption_shape(t))
        return {
            "speaker_name": speaker_name,
            "speaker_label": speaker_label,
            "is_explicitly_attributed": is_explicit,
            "is_generic_fallback_label": is_generic_fb,
            "has_interruption_framing": intr,
            "confidence": confidence,
        }

    m = _SPEECH_VERB_ATTRIBUTION_RE.match(t)
    if not m:
        m = _BEAT_ATTRIBUTION_RE.match(t)
    if m:
        raw = str(m.group(1) or "").strip()
        low = raw.lower()
        if raw and low not in _NON_NAME_ATTRIBUTION_PREFIXES and not low.startswith(
            tuple(p + " " for p in _NON_NAME_ATTRIBUTION_PREFIXES)
        ):
            speaker_label = raw
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            speaker_label = raw
            confidence = "medium"

    forbidden = list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
    is_generic_fb = False
    if speaker_label:
        sl = speaker_label.strip().lower()
        for fb in forbidden:
            fbl = fb.strip().lower()
            if fbl == sl or fbl in sl or sl in fbl:
                is_generic_fb = True
                break

    intr = bool(interruption_cue_present_in_text(t) or _has_explicit_interruption_shape(t))

    return {
        "speaker_name": speaker_name,
        "speaker_label": speaker_label,
        "is_explicitly_attributed": is_explicit,
        "is_generic_fallback_label": is_generic_fb,
        "has_interruption_framing": intr,
        "confidence": confidence,
    }


def _display_from_npc_id(npc_id: str | None) -> str:
    s = str(npc_id or "").strip()
    if not s:
        return ""
    return s.replace("_", " ").replace("-", " ").title()


def _label_matches_primary_speaker(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    if not str(label or "").strip():
        return False
    low = label.strip().lower()
    pn = str(contract.get("primary_speaker_name") or "").strip().lower()
    pid = str(contract.get("primary_speaker_id") or "").strip()
    pid_disp = _display_from_npc_id(pid).lower()
    if pn and low == pn:
        return True
    if pid_disp and low == pid_disp:
        return True
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        rn = str(soc.get("npc_name") or "").strip().lower()
        rid = _display_from_npc_id(str(soc.get("npc_id") or "")).lower()
        if rn and low == rn:
            return True
        if rid and low == rid:
            return True
    return False


def _label_in_allowed_speaker_ids(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    allowed = contract.get("allowed_speaker_ids")
    if not isinstance(allowed, list) or not allowed:
        return False
    low = label.strip().lower()
    for aid in allowed:
        disp = _display_from_npc_id(str(aid or "").strip()).lower()
        if disp and low == disp:
            return True
    pid = str(contract.get("primary_speaker_id") or "").strip()
    if pid in allowed and _label_matches_primary_speaker(label, contract, resolution):
        return True
    return False


def _emitted_invents_dialogue_ownership(text: str) -> bool:
    t = _normalize_text(text)
    if not t:
        return False
    if '"' in t:
        return True
    return bool(
        re.search(
            r"\b(?:says|replies|answers|mutters|whispers|asks|shakes|shrugs|frowns|grimaces)\b",
            t,
            re.IGNORECASE,
        )
    )


def _explicit_interruption_scene_event_framing(text: str) -> bool:
    return bool(_has_explicit_interruption_shape(_normalize_text(text)))


def validate_emitted_speaker_against_contract(
    text: str,
    speaker_selection: Dict[str, Any],
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Contract-first validation of final text vs Block 1 speaker_selection_contract."""
    c = speaker_selection if isinstance(speaker_selection, dict) else {}
    res = resolution if isinstance(resolution, dict) else None
    details: Dict[str, Any] = {"signature": detect_emitted_speaker_signature(text, res)}

    if isinstance(c.get("debug"), dict) and c["debug"].get("contract_missing"):
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": c.get("primary_speaker_id"),
            "canonical_speaker_name": c.get("primary_speaker_name"),
            "repair_mode": "none",
            "details": {**details, "skipped": "no_contract"},
        }

    allowed = [str(x).strip() for x in (c.get("allowed_speaker_ids") or []) if str(x).strip()]
    primary_id = str(c.get("primary_speaker_id") or "").strip() or None
    primary_name = str(c.get("primary_speaker_name") or "").strip() or None
    continuity_locked = bool(c.get("continuity_locked"))
    gen_ff = bool(c.get("generic_fallback_forbidden"))
    sw_ok = bool(c.get("speaker_switch_allowed"))
    intr_ok = bool(c.get("interruption_allowed"))
    intr_scene = bool(c.get("interruption_requires_scene_event"))
    offscene_forbid = bool(c.get("offscene_speakers_forbidden"))

    sig = details["signature"]
    label = str(sig.get("speaker_label") or "").strip()
    explicit = bool(sig.get("is_explicitly_attributed"))
    intr = bool(sig.get("has_interruption_framing"))
    explicit_scene = _explicit_interruption_scene_event_framing(text)

    canonical_id = primary_id
    canonical_name = primary_name
    if not canonical_name and res is not None:
        soc0 = res.get("social") if isinstance(res.get("social"), dict) else {}
        canonical_name = str(soc0.get("npc_name") or "").strip() or None
    if not canonical_name and primary_id:
        canonical_name = _display_from_npc_id(primary_id)

    # (b) Generic fallback speaker
    if gen_ff:
        flist = (
            c.get("forbidden_fallback_labels")
            if isinstance(c.get("forbidden_fallback_labels"), list)
            else list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
        )
        low_lab = label.lower() if label else ""
        hit = bool(sig.get("is_generic_fallback_label"))
        if explicit and low_lab and not hit:
            for fb in flist:
                fbs = str(fb or "").strip().lower()
                if fbs and (fbs == low_lab or fbs in low_lab or low_lab in fbs):
                    hit = True
                    break
        if hit:
            rm = "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral"
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "generic_fallback_forbidden"},
            }

    # Interruption policy (third-party / scene break)
    if intr:
        if not (sw_ok and intr_ok):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_not_permitted"},
            }
        # Continuity-locked strict-social: require explicit join only when dialogue ownership
        # is present (quoted speech or clear attribution), matching mixed-blob rejection policy.
        tnorm = _normalize_text(text)
        if intr_scene and not explicit_scene and ('"' in tnorm or explicit):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_requires_scene_event"},
            }

    # (e) No speaker allowed but dialogue ownership invented
    if not allowed:
        if _emitted_invents_dialogue_ownership(text):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
                "canonical_speaker_id": None,
                "canonical_speaker_name": None,
                "repair_mode": "narrator_neutral",
                "details": {**details, "rule": "no_allowed_speaker_dialogue"},
            }
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    # (a) Continuity locked + wrong explicit speaker
    if continuity_locked and explicit and label:
        if not _label_in_allowed_speaker_ids(label, c, res):
            if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
                return {
                    "ok": True,
                    "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                    "canonical_speaker_id": canonical_id,
                    "canonical_speaker_name": canonical_name,
                    "repair_mode": "none",
                    "details": {**details, "rule": "interruption_overrides_explicit_mismatch"},
                }
            salvage = bool(re.search(r"\"[^\"]{2,}\"", _normalize_text(text)))
            rm = "local_rebind" if (canonical_name and salvage) else ("canonical_rewrite" if canonical_id else "narrator_neutral")
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "continuity_locked_explicit_mismatch"},
            }

    # (c) New speaker not permitted
    if explicit and label and not _label_in_allowed_speaker_ids(label, c, res):
        if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
            return {
                "ok": True,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "none",
                "details": {**details, "rule": "switch_permitted_interruption"},
            }
        if not sw_ok:
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
                "details": {**details, "rule": "speaker_switch_disallowed"},
            }
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "unlisted_explicit_speaker"},
        }

    if offscene_forbid and explicit and label and not _label_in_allowed_speaker_ids(label, c, res) and not intr:
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "offscene_speakers_forbidden"},
        }

    if intr:
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    return {
        "ok": True,
        "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
        "canonical_speaker_id": canonical_id,
        "canonical_speaker_name": canonical_name,
        "repair_mode": "none",
        "details": details,
    }


def _try_local_rebind_opening_speaker(text: str, *, wrong_label: str, canonical_name: str) -> str | None:
    t = _normalize_text(text)
    w = str(wrong_label or "").strip()
    if not w or not canonical_name:
        return None
    if '"' in w or "“" in w or "”" in w:
        return None
    low_t = t.lower()
    low_w = w.lower()
    if low_t.startswith(low_w + " ") or low_t.startswith(low_w + ","):
        rest = t[len(w) :].lstrip()
        return _normalize_text(f"{canonical_name} {rest}")
    return None


def _apply_speaker_contract_repairs(
    text: str,
    validation: Dict[str, Any],
    *,
    contract: Dict[str, Any],
    eff_resolution: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> tuple[str, str, Dict[str, Any]]:
    """Returns (new_text, final_reason_code, repair_debug)."""
    dbg: Dict[str, Any] = {"initial_repair_mode": validation.get("repair_mode")}
    mode = str(validation.get("repair_mode") or "none")
    reason = str(validation.get("reason_code") or "")
    cid = validation.get("canonical_speaker_id")
    cname = str(validation.get("canonical_speaker_name") or "").strip()

    if mode == "local_rebind" and eff_resolution is not None:
        sig = (validation.get("details") or {}).get("signature") or {}
        wl = str(sig.get("speaker_label") or "").strip()
        if wl and cname:
            attempt = _try_local_rebind_opening_speaker(text, wrong_label=wl, canonical_name=cname)
            if attempt:
                dbg["local_rebind_applied"] = True
                if isinstance(eff_resolution.get("social"), dict):
                    soc = eff_resolution["social"]
                    if cid:
                        soc["npc_id"] = str(cid).strip()
                    soc["npc_name"] = cname
                return attempt, _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR, dbg

    if mode == "canonical_rewrite":
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = dict(eff_resolution["social"])
            if cid:
                soc["npc_id"] = str(cid).strip()
            if cname:
                soc["npc_name"] = cname
            elif cid:
                soc["npc_name"] = _npc_display_name_for_emission(
                    world if isinstance(world, dict) else {},
                    str(scene_id or "").strip(),
                    str(cid).strip(),
                )
            soc.pop("reply_speaker_grounding_neutral_bridge", None)
            eff_resolution["social"] = soc
            line = strict_social_ownership_terminal_fallback(eff_resolution)
            dbg["canonical_rewrite_applied"] = True
            return line, _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE, dbg
        line = _normalize_text(text)
        dbg["canonical_rewrite_failed_resolution"] = True
        return line, reason, dbg

    if mode == "narrator_neutral":
        seed = f"{scene_id}|{cid or ''}|{hash(_normalize_text(text)) % 10000}"
        line = neutral_reply_speaker_grounding_bridge_line(seed=seed)
        dbg["narrator_neutral_applied"] = True
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = eff_resolution["social"]
            soc["reply_speaker_grounding_neutral_bridge"] = True
            soc.pop("npc_id", None)
            soc.pop("npc_name", None)
        return line, _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER, dbg

    return text, reason, dbg


def _sync_eff_social_to_resolution(
    eff_resolution: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> None:
    """Copy speaker fields from effective resolution back to the caller's resolution dict when distinct."""
    if not isinstance(eff_resolution, dict) or not isinstance(resolution, dict):
        return
    if resolution is eff_resolution:
        return
    src = eff_resolution.get("social")
    if not isinstance(src, dict):
        return
    dst = resolution.get("social")
    if not isinstance(dst, dict):
        resolution["social"] = {}
        dst = resolution["social"]
    if src.get("reply_speaker_grounding_neutral_bridge"):
        dst["reply_speaker_grounding_neutral_bridge"] = True
        dst.pop("npc_id", None)
        dst.pop("npc_name", None)
        return
    if "npc_id" in src:
        dst["npc_id"] = src.get("npc_id")
    if "npc_name" in src:
        dst["npc_name"] = src.get("npc_name")


def _merge_speaker_enforcement_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    enforcement_payload: Dict[str, Any],
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["speaker_contract_enforcement"] = enforcement_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["speaker_contract_enforcement"] = enforcement_payload

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["speaker_contract_enforcement"] = enforcement_payload


def enforce_emitted_speaker_with_contract(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> tuple[str, Dict[str, Any]]:
    """Validate *text* against stored contract; repair if needed. Mutates *eff_resolution* social on repair paths."""
    trace = gm_output.get("trace") if isinstance(gm_output.get("trace"), dict) else None
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else None
    contract = get_speaker_selection_contract(
        eff_resolution if isinstance(eff_resolution, dict) else None,
        metadata=md,
        trace=trace,
    )
    val = validate_emitted_speaker_against_contract(
        text,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    payload: Dict[str, Any] = {
        "contract_present": not (
            isinstance(contract.get("debug"), dict) and contract["debug"].get("contract_missing")
        ),
        "validation": val,
    }

    if val.get("ok") is True:
        payload["final_reason_code"] = val.get("reason_code")
        _merge_speaker_enforcement_into_outputs(gm_output, resolution, eff_resolution, enforcement_payload=payload)
        return text, payload

    repaired, final_rc, rdbg = _apply_speaker_contract_repairs(
        text,
        val,
        contract=contract,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        scene_id=scene_id,
        world=world,
    )
    payload["repair"] = rdbg
    payload["final_reason_code"] = final_rc
    payload["post_validation"] = validate_emitted_speaker_against_contract(
        repaired,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    _merge_speaker_enforcement_into_outputs(gm_output, resolution, eff_resolution, enforcement_payload=payload)
    return repaired, payload


def _reply_kind(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    sp = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(sp.get("reply_kind") or "").strip().lower()


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text."""
    if not isinstance(gm_output, dict):
        return gm_output
    out = dict(gm_output)
    pre_gate_text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]

    eff_resolution, _effective_social_route, coercion_reason = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    sid = str(scene_id or "").strip()
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    )
    merged_for_suppress = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    strict_social_suppressed_non_social_turn = False
    strict_social_suppression_reason: str | None = None
    original_coercion_reason = coercion_reason
    if strict_social_turn:
        do_suppress, sup_reason = strict_social_suppress_non_native_coercion_for_narration_beat(
            resolution if isinstance(resolution, dict) else None,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            sid,
            coercion_reason=coercion_reason,
            merged_player_prompt=merged_for_suppress,
        )
        if do_suppress:
            strict_social_suppressed_non_social_turn = True
            strict_social_suppression_reason = sup_reason
            strict_social_turn = False
            pre_gate_text = _normalize_text(
                sanitize_player_facing_output(
                    pre_gate_text,
                    {
                        "resolution": resolution if isinstance(resolution, dict) else None,
                        "include_resolution": True,
                        "session": session if isinstance(session, dict) else None,
                        "scene_id": sid,
                        "world": world if isinstance(world, dict) else None,
                        "tags": tag_list,
                    },
                )
            )
            eff_resolution = resolution if isinstance(resolution, dict) else None
            coercion_reason = f"{original_coercion_reason}|suppressed_non_social_narration:{sup_reason}"
            out["player_facing_text"] = pre_gate_text

    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_interlocutor = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    npc_id_for_meta = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id_for_meta = str(sp.get("npc_id") or "").strip()

    res_kind = str((eff_resolution or {}).get("kind") or "").strip().lower() if isinstance(eff_resolution, dict) else ""
    social_ic = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        social_ic = str(sp.get("social_intent_class") or "").strip().lower()

    reasons: List[str] = []
    normalization_ran = False
    text = pre_gate_text
    response_type_debug = _default_response_type_debug(None, None)
    ac_layer_meta: Dict[str, Any] = {}
    rd_layer_meta: Dict[str, Any] = _default_response_delta_meta()
    na_layer_meta: Dict[str, Any] = _default_narrative_authority_meta()
    ssa_layer_meta: Dict[str, Any] = {}

    strict_social_active = bool(strict_social_turn)
    coercion_used = (
        "|" in original_coercion_reason
        or "synthetic" in original_coercion_reason
        or "npc_directed_guard" in original_coercion_reason
    )
    retry_output = any(
        isinstance(t, str) and ("question_retry_fallback" in t or "social_exchange_retry_fallback" in t)
        for t in tag_list
    )

    if strict_social_turn:
        normalization_ran = True
        text, details = build_final_strict_social_response(
            pre_gate_text,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            tags=tag_list,
            session=session if isinstance(session, dict) else None,
            scene_id=str(scene_id or "").strip(),
            world=world if isinstance(world, dict) else None,
        )
        text, response_type_debug = _enforce_response_type_contract(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            strict_social_turn=True,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            active_interlocutor=active_interlocutor,
        )
        if response_type_debug.get("response_type_candidate_ok") is False and isinstance(eff_resolution, dict):
            text = minimal_social_emergency_fallback_line(eff_resolution)
            text, response_type_debug = _enforce_response_type_contract(
                text,
                gm_output=out,
                resolution=eff_resolution,
                session=session if isinstance(session, dict) else None,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                strict_social_turn=True,
                strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
                active_interlocutor=active_interlocutor,
            )
            details = {
                **details,
                "used_internal_fallback": True,
                "fallback_kind": "response_type_contract_social_emergency",
                "fallback_pool": "response_type_contract",
                "final_emitted_source": "minimal_social_emergency_fallback",
                "rejection_reasons": list(details.get("rejection_reasons") or [])
                + list(response_type_debug.get("response_type_rejection_reasons") or []),
            }
        text, ac_layer_meta, _ = _apply_answer_completeness_layer(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            strict_social_path=True,
        )
        text, rd_layer_meta, _ = _apply_response_delta_layer(
            text,
            gm_output=out,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            answer_completeness_meta=ac_layer_meta,
            strict_social_path=True,
        )
        text, na_layer_meta, _ = _apply_narrative_authority_layer(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            answer_completeness_meta=ac_layer_meta,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )
        out["player_facing_text"] = text
        text, _speaker_contract_payload = enforce_emitted_speaker_with_contract(
            _normalize_text(text),
            gm_output=out,
            resolution=resolution if isinstance(resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=sid,
        )
        _sync_eff_social_to_resolution(
            eff_resolution if isinstance(eff_resolution, dict) else None,
            resolution if isinstance(resolution, dict) else None,
        )
        out["player_facing_text"] = text
        text, ssa_layer_meta = _apply_scene_state_anchor_layer(
            _normalize_text(text),
            gm_output=out,
            strict_social_details=details,
            response_type_debug=response_type_debug,
        )
        out["player_facing_text"] = text
        _merge_scene_state_anchor_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=ssa_layer_meta,
        )
        _merge_narrative_authority_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=na_layer_meta,
            gm_output=out,
        )
        if isinstance(eff_resolution, dict):
            sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
            npc_id_for_meta = str(sp.get("npc_id") or "").strip()
        final_emitted_source = str(details.get("final_emitted_source") or "unknown_post_gate_writer")
        if response_type_debug.get("response_type_repair_used"):
            final_emitted_source = str(
                response_type_debug.get("response_type_repair_kind") or "response_type_contract_repair"
            )
        if retry_output:
            final_emitted_source = "retry_output"
        if ac_layer_meta.get("answer_completeness_repaired"):
            final_emitted_source = str(
                ac_layer_meta.get("answer_completeness_repair_mode") or "answer_completeness_repair"
            )
        if rd_layer_meta.get("response_delta_repaired"):
            final_emitted_source = str(
                rd_layer_meta.get("response_delta_repair_mode") or "response_delta_repair"
            )
        if na_layer_meta.get("narrative_authority_repaired"):
            final_emitted_source = str(
                na_layer_meta.get("narrative_authority_repair_mode") or "narrative_authority_repair"
            )
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        if not details.get("used_internal_fallback"):
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate",
                    "social_route": strict_social_turn,
                    "coercion_reason": coercion_reason,
                    "resolution_kind": res_kind,
                    "social_intent_class": social_ic,
                    "active_interlocutor": active_interlocutor or None,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": str(details.get("fallback_pool") or "none"),
                    "fallback_kind": str(details.get("fallback_kind") or "none"),
                    **_response_type_decision_payload(response_type_debug),
                }
            )
            out["_final_emission_meta"] = {
                "final_route": "accept_candidate",
                "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
                "strict_social_active": strict_social_active,
                "coercion_used": coercion_used,
                "active_interlocutor_id": active_interlocutor or None,
                "npc_id": npc_id_for_meta or None,
                "normalization_ran": normalization_ran,
                "candidate_validation_passed": True,
                "deterministic_social_fallback_attempted": bool(details.get("deterministic_attempted")),
                "deterministic_social_fallback_passed": bool(details.get("deterministic_passed")),
                "final_emitted_source": final_emitted_source,
                "post_gate_mutation_detected": post_gate_mutation_detected,
                "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
                "coercion_reason": coercion_reason,
                "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
                "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
                "resolved_answer_source": details.get("resolved_answer_source"),
                "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
                "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
                "strict_social_suppression_reason": strict_social_suppression_reason,
                "social_emission_integrity_replaced": bool(details.get("social_emission_integrity_replaced")),
                "social_emission_integrity_reasons": details.get("social_emission_integrity_reasons"),
                "social_emission_integrity_fallback_kind": details.get("social_emission_integrity_fallback_kind"),
                "speaker_contract_enforcement_reason": _speaker_contract_payload.get("final_reason_code"),
            }
            _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
            _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
            _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
            _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
            _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
            out = _apply_visibility_enforcement(
                out,
                session=session,
                scene=scene,
                world=world,
                scene_id=sid,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                active_interlocutor=active_interlocutor,
                strict_social_active=strict_social_active,
                strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            )
            log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
            return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

        fb_kind = str(details.get("fallback_kind") or "none")
        deterministic_attempted = bool(details.get("deterministic_attempted"))
        deterministic_passed = bool(details.get("deterministic_passed"))
        fallback_pool = str(details.get("fallback_pool") or "social_deterministic")
        candidate_ok = False
        rejection_reasons = details.get("rejection_reasons") if isinstance(details.get("rejection_reasons"), list) else []
        rejection_reasons = list(rejection_reasons) + list(response_type_debug.get("response_type_rejection_reasons") or [])

        out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fb_kind}"]
        if final_emitted_source == "minimal_social_emergency_fallback":
            out["tags"] = list(out["tags"]) + ["terminal_strict_social_emission", "strict_social_terminal_safe"]

        if details.get("route_illegal_intercepted"):
            dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
            preview = str(details.get("intercepted_preview") or "")
            out["debug_notes"] = (
                (dbg + " | " if dbg else "")
                + f"final_emission_gate:route_illegal_writer_intercepted:{preview[:80]}"
            )

        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + "final_emission_gate:replaced:"
            + ",".join([str(r) for r in rejection_reasons[:8] if isinstance(r, str)])
        )
        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": candidate_ok,
                "rejection_reasons": [str(r) for r in rejection_reasons[:12] if isinstance(r, str)],
                "fallback_pool": fallback_pool,
                "fallback_kind": fb_kind,
                **_response_type_decision_payload(response_type_debug),
            }
        )
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        out["_final_emission_meta"] = {
            "final_route": "replaced",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": False,
            "deterministic_social_fallback_attempted": deterministic_attempted,
            "deterministic_social_fallback_passed": deterministic_passed,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "rejection_reasons_sample": [str(r) for r in rejection_reasons[:8] if isinstance(r, str)],
            "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
            "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
            "resolved_answer_source": details.get("resolved_answer_source"),
            "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
            "speaker_contract_enforcement_reason": _speaker_contract_payload.get("final_reason_code"),
        }
        _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
        _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
        _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
        _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
        _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
        return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    if _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=sid,
    ) and not _reply_already_has_concrete_interaction(text):
        reasons.append("passive_scene_pressure_missing_concrete_beat")

    text, response_type_debug = _enforce_response_type_contract(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )
    if response_type_debug.get("response_type_candidate_ok") is False:
        reasons.extend(
            [str(r) for r in (response_type_debug.get("response_type_rejection_reasons") or []) if isinstance(r, str)]
        )

    text, ac_layer_meta, ac_reasons = _apply_answer_completeness_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        strict_social_path=False,
    )
    reasons.extend(ac_reasons)

    text, rd_layer_meta, rd_reasons = _apply_response_delta_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=False,
    )
    reasons.extend(rd_reasons)

    text, na_layer_meta, na_reasons = _apply_narrative_authority_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
    )
    reasons.extend(na_reasons)

    text, ssa_layer_meta = _apply_scene_state_anchor_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
    )
    out["player_facing_text"] = _normalize_text(text)
    _merge_scene_state_anchor_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=ssa_layer_meta,
    )
    _merge_narrative_authority_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=na_layer_meta,
        gm_output=out,
    )

    candidate_ok = not bool(reasons)
    fallback_pool = "none"
    fallback_kind = "none"
    deterministic_attempted = False
    deterministic_passed = False
    final_emitted_source = "unknown_post_gate_writer"

    if not reasons:
        out["player_facing_text"] = text
        final_emitted_source = "generated_candidate"
        if response_type_debug.get("response_type_repair_used"):
            final_emitted_source = str(
                response_type_debug.get("response_type_repair_kind") or "response_type_contract_repair"
            )
        if retry_output:
            final_emitted_source = "retry_output"
        if ac_layer_meta.get("answer_completeness_repaired"):
            final_emitted_source = str(
                ac_layer_meta.get("answer_completeness_repair_mode") or "answer_completeness_repair"
            )
        if rd_layer_meta.get("response_delta_repaired"):
            final_emitted_source = str(
                rd_layer_meta.get("response_delta_repair_mode") or "response_delta_repair"
            )
        if na_layer_meta.get("narrative_authority_repaired"):
            final_emitted_source = str(
                na_layer_meta.get("narrative_authority_repair_mode") or "narrative_authority_repair"
            )

        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": True,
                "rejection_reasons": [],
                "fallback_pool": fallback_pool,
                "fallback_kind": fallback_kind,
                **_response_type_decision_payload(response_type_debug),
            }
        )
        out["_final_emission_meta"] = {
            "final_route": "accept_candidate",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": True,
            "deterministic_social_fallback_attempted": False,
            "deterministic_social_fallback_passed": False,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
        }
        _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
        _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
        _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
        _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
        _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
        return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

    # Non-social replace path only (strict-social replacement is handled in build_final_strict_social_response).
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_pool = "social_active_interlocutor_minimal"
        fallback_text = minimal_social_emergency_fallback_line(mini_res)
        fallback_kind = "social_interlocutor_fallback"
        final_emitted_source = "social_interlocutor_minimal_fallback"
    else:
        passive_candidates = _passive_scene_pressure_fallback_candidates(
            session=session if isinstance(session, dict) else None,
            scene=scene,
            scene_id=sid,
        )
        if passive_candidates:
            (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                _fallback_strategy,
                _fallback_candidate_source,
                _composition_meta,
            ) = passive_candidates[0]
        elif _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
            fallback_pool = "npc_pursuit_fail_closed_neutral"
            fallback_text = "Nothing confirms progress toward that lead yet—the moment stays unresolved."
            fallback_kind = "npc_pursuit_neutral_nonprogress"
            final_emitted_source = "npc_pursuit_neutral_fallback"
        else:
            fallback_pool = "global_scene_narrative"
            fallback_text = "For a breath, the scene holds while voices shift around you."
            fallback_kind = "narrative_safe_fallback"
            final_emitted_source = "global_scene_fallback"
    deterministic_attempted = False
    deterministic_passed = False

    out["player_facing_text"] = fallback_text
    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fallback_kind}"]

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join(reasons[:8])
    )
    log_final_emission_decision(
        {
            "stage": "final_emission_gate",
            "social_route": strict_social_turn,
            "coercion_reason": coercion_reason,
            "resolution_kind": res_kind,
            "social_intent_class": social_ic,
            "active_interlocutor": active_interlocutor or None,
            "candidate_ok": candidate_ok,
            "rejection_reasons": reasons[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            **_response_type_decision_payload(response_type_debug),
        }
    )
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    post_gate_mutation_detected = pre_gate_text != gate_out_text

    out["_final_emission_meta"] = {
        "final_route": "replaced",
        "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
        "strict_social_active": strict_social_active,
        "coercion_used": coercion_used,
        "active_interlocutor_id": active_interlocutor or None,
        "npc_id": npc_id_for_meta or None,
        "normalization_ran": normalization_ran,
        "candidate_validation_passed": False,
        "deterministic_social_fallback_attempted": deterministic_attempted,
        "deterministic_social_fallback_passed": deterministic_passed,
        "final_emitted_source": final_emitted_source,
        "post_gate_mutation_detected": post_gate_mutation_detected,
        "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
        "coercion_reason": coercion_reason,
        "rejection_reasons_sample": reasons[:8],
        "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
        "strict_social_suppression_reason": strict_social_suppression_reason,
    }
    _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
    _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
    _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
    _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
    _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
    out = _apply_visibility_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )
    log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
    return _finalize_emission_output(out, pre_gate_text=pre_gate_text)
