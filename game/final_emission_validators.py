"""Deterministic validators for final emission: ``validate_*``, ``inspect_*``, ``candidate_satisfies_*``.

Pure checks only — no ``apply_*`` / merge orchestration. Callers:
:mod:`game.final_emission_repairs` and :func:`game.final_emission_gate.apply_final_emission_gate`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_text import (
    _ACTION_STOPWORDS,
    _ACTION_RESULT_PATTERNS,
    _AGENCY_SUBSTITUTE_PATTERNS,
    _ANSWER_DIRECT_PATTERNS,
    _ANSWER_FILLER_PATTERNS,
    _capitalize_sentence_fragment,
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.social_exchange_emission import (
    is_route_illegal_global_or_sanitizer_fallback_text,
    replacement_is_route_legal_social,
)


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
