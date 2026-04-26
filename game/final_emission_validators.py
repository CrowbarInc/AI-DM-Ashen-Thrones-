"""Deterministic validators for final emission: ``validate_*``, ``inspect_*``, ``candidate_satisfies_*``.

Pure checks only — no ``apply_*`` / merge orchestration. Callers:
:mod:`game.final_emission_repairs` and :func:`game.final_emission_gate.apply_final_emission_gate`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

from game.final_emission_text import (
    _ACTION_STOPWORDS,
    _ACTION_RESULT_PATTERNS,
    _AGENCY_SUBSTITUTE_PATTERNS,
    _ANSWER_DIRECT_PATTERNS,
    _ANSWER_FILLER_PATTERNS,
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.response_policy_contracts import (
    resolve_answer_completeness_contract as _policy_resolve_answer_completeness_contract,
    resolve_fallback_behavior_contract as _policy_resolve_fallback_behavior_contract,
    resolve_response_delta_contract as _policy_resolve_response_delta_contract,
    resolve_social_response_structure_contract as _policy_resolve_social_response_structure_contract,
)
from game.referent_tracking import REFERENT_TRACKING_ARTIFACT_VERSION
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


def _has_hedge_language(text: str) -> bool:
    """Heuristic hedge detection used for bounded/unknown plan facts (no semantic inference)."""
    t = str(text or "")
    if not t:
        return False
    return bool(
        re.search(
            r"\b(?:might|may|maybe|perhaps|seems|appears|rumor|rumour|hearsay|unclear|not sure|can't say for certain)\b",
            t,
            re.IGNORECASE,
        )
    )


def _mentions_fact_text(emitted_text: str, fact_text: str) -> bool:
    """True when emitted text overlaps meaningfully with a fact string (token overlap, bounded)."""
    et = _normalize_text(emitted_text)
    ft = _normalize_text(fact_text)
    if not et or not ft:
        return False
    # Fast path: direct substring match (case-insensitive) for short facts.
    if len(ft) <= 180 and ft.lower() in et.lower():
        return True
    # Token overlap for longer/looser facts.
    ftoks = _content_tokens(ft)
    if not ftoks:
        return False
    etoks = _content_tokens(et)
    inter = ftoks & etoks
    # Require at least 2 meaningful tokens, or a single long token (names, rare nouns).
    if len(inter) >= 2:
        return True
    return any(len(tok) >= 8 for tok in inter)


def _opening_segment_for_plan(text: str) -> str:
    """Plan-convergence uses the same sentence splitter as answer-completeness."""
    return _opening_segment(_normalize_text(text))


def validate_answer_exposition_plan_convergence(
    emitted_text: str,
    *,
    answer_required: bool,
    answer_exposition_plan: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Deterministic final-emission enforcement for Answer/Exposition Convergence.

    Final emission validates; it does not author missing facts or fallback exposition.
    This validator is intentionally heuristic and fail-closed when required seams are absent.
    """
    base: Dict[str, Any] = {
        "checked": False,
        "plan_present": False,
        "plan_valid": False,
        "passed": True,
        "required_fact_ids": [],
        "failure_reasons": [],
    }
    if not answer_required:
        return base
    base["checked"] = True

    plan = answer_exposition_plan if isinstance(answer_exposition_plan, Mapping) else None
    base["plan_present"] = plan is not None
    if plan is None:
        base["passed"] = False
        base["failure_reasons"] = ["missing_answer_exposition_plan"]
        return base

    # Structural validation: mirror the prompt_context projected validator requirements (strict enough for gate).
    for k in ("enabled", "answer_required"):
        if not isinstance(plan.get(k), bool):
            base["passed"] = False
            base["failure_reasons"] = [f"malformed_plan:missing_or_bad_bool:{k}"]
            return base
    if not isinstance(plan.get("facts"), list):
        base["passed"] = False
        base["failure_reasons"] = ["malformed_plan:facts_not_list"]
        return base
    for req in ("constraints", "voice", "delivery"):
        if not isinstance(plan.get(req), Mapping):
            base["passed"] = False
            base["failure_reasons"] = [f"malformed_plan:missing_{req}"]
            return base
    delivery = plan.get("delivery") if isinstance(plan.get("delivery"), Mapping) else {}
    must_ids = delivery.get("must_include_fact_ids") if isinstance(delivery.get("must_include_fact_ids"), list) else []
    base["required_fact_ids"] = [str(x) for x in must_ids if isinstance(x, str) and str(x).strip()][:16]
    base["plan_valid"] = True

    text = _normalize_text(emitted_text)
    if not text:
        base["passed"] = False
        base["failure_reasons"] = ["empty_emitted_text"]
        return base

    # Enforce answer-first when required by plan delivery.
    answer_first = bool(delivery.get("answer_must_come_first"))
    opening = _opening_segment_for_plan(text)

    # Generic filler/deflection cannot stand in for an answer when answer is required.
    if any(p.search(opening) for p in _ANSWER_FILLER_PATTERNS):
        base["failure_reasons"].append("opening_is_filler_not_answer")
    if any(p.search(opening) for p in _DEFLECTIVE_OPENING_PATTERNS):
        base["failure_reasons"].append("opening_is_deflective")
    if _GENERIC_NONANSWER_SNIPPET.search(opening):
        base["failure_reasons"].append("opening_is_generic_nonanswer")

    facts_raw = plan.get("facts") if isinstance(plan.get("facts"), list) else []
    facts: List[Mapping[str, Any]] = [f for f in facts_raw if isinstance(f, Mapping)][:64]
    id_to_fact: Dict[str, Mapping[str, Any]] = {}
    for f in facts:
        fid = str(f.get("id") or "").strip()
        if fid:
            id_to_fact[fid] = f

    # Required fact ids must be representable where feasible (token overlap heuristic).
    missing_required: List[str] = []
    for fid in base["required_fact_ids"]:
        f = id_to_fact.get(fid)
        if not isinstance(f, Mapping):
            missing_required.append(fid)
            continue
        ftxt = str(f.get("fact") or "").strip()
        if not _mentions_fact_text(text, ftxt):
            missing_required.append(fid)
    if missing_required:
        base["failure_reasons"].append(f"missing_required_fact_ids:{sorted(missing_required)}")

    # Answer-must-come-first: opening should carry at least one required fact (when such facts exist).
    if answer_first and base["required_fact_ids"]:
        open_ok = False
        for fid in base["required_fact_ids"]:
            f = id_to_fact.get(fid)
            if not isinstance(f, Mapping):
                continue
            if _mentions_fact_text(opening, str(f.get("fact") or "")):
                open_ok = True
                break
        if not open_ok:
            base["failure_reasons"].append("answer_must_come_first_violation")

    # Bounded/unknown must not be upgraded to certainty; gated/unknown visibility must not be stated as public truth.
    emitted_tokens = _content_tokens(text)
    for f in facts:
        ftxt = str(f.get("fact") or "").strip()
        if not ftxt:
            continue
        # Mention detection: use the fact string when it matches; otherwise fall back to token overlap.
        mentioned = _mentions_fact_text(text, ftxt)
        if not mentioned:
            ftoks = _content_tokens(ftxt)
            if len(ftoks & emitted_tokens) >= 2:
                mentioned = True
        if not mentioned:
            continue
        certainty = str(f.get("certainty") or "").strip().lower()
        visibility = str(f.get("visibility") or "").strip().lower()

        if certainty in {"bounded", "unknown"} and not _has_hedge_language(text):
            base["failure_reasons"].append(f"bounded_unknown_upgraded_to_certainty:{str(f.get('id') or '')}")
        if visibility in {"gated", "unknown"}:
            # If a gated/unknown fact is mentioned, require explicit gating/uncertainty framing.
            if visibility == "gated" and not re.search(r"\b(?:can't say|cannot say|won't say|not here|not now|under orders|sworn)\b", text, re.IGNORECASE):
                base["failure_reasons"].append(f"gated_fact_stated_as_public_truth:{str(f.get('id') or '')}")
            if visibility == "unknown" and not _has_hedge_language(text):
                base["failure_reasons"].append(f"unknown_fact_stated_as_known:{str(f.get('id') or '')}")

    # Unsupported lore/exposition claims: fail when there is substantial novel token mass not covered by plan facts.
    # This is bounded and intentionally coarse: it permits small connective language, but fails closed on
    # large novelty when the plan provides only small grounded surface area.
    plan_tokens: set[str] = set()
    for f in facts:
        plan_tokens |= _content_tokens(str(f.get("fact") or ""))
    novel = emitted_tokens - plan_tokens
    # Allow a small novelty budget for connective narrative words.
    # If the plan is small, keep the novelty budget small as well (anti-invention).
    if plan_tokens:
        long_novel = [t for t in novel if len(t) >= 7]
        # Conservative: allow light scene color and connective language, but fail on "high-signal" novelty.
        if (len(long_novel) >= 2 and len(novel) >= 3) or len(novel) >= 10:
            base["failure_reasons"].append("unsupported_lore_or_exposition_claims")

    base["failure_reasons"] = list(dict.fromkeys(str(r) for r in base["failure_reasons"] if r))
    base["passed"] = not bool(base["failure_reasons"])
    return base


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


def candidate_satisfies_scene_opening_contract(text: str) -> tuple[bool, List[str]]:
    clean = _normalize_text(text)
    if not clean:
        return False, ["scene_opening_empty"]
    low = clean.lower()
    if is_route_illegal_global_or_sanitizer_fallback_text(clean):
        return False, ["scene_opening_generic_fallback_text"]
    if any(p.search(clean) for p in _ANSWER_FILLER_PATTERNS):
        return False, ["scene_opening_generic_fallback_text"]
    if re.search(r"\b(?:the scene holds|voices shift around you|insufficient context|not established)\b", low):
        return False, ["scene_opening_generic_fallback_text"]
    if not re.search(
        r"\b(?:you|gate|district|market|lane|road|square|yard|bridge|dock|pier|tavern|hall|ward|street|"
        r"rain|mist|crowd|guards?|refugees?|wagons?|torchlight|notice board)\b",
        low,
    ):
        return False, ["scene_opening_not_scene_establishing"]
    if clean.endswith("?"):
        return False, ["scene_opening_is_question"]
    return True, []


def _default_response_type_debug(contract: Dict[str, Any] | None, source: str | None) -> Dict[str, Any]:
    return {
        "response_type_required": str((contract or {}).get("required_response_type") or "") or None,
        "response_type_contract_source": source,
        "response_type_candidate_ok": None if not contract else True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
        "opening_generic_action_repair_blocked": False,
        "opening_specific_repair_used": False,
        "opening_validation_failed": False,
        "opening_failure_reasons": [],
        "opening_recovered_via_fallback": False,
        "opening_fallback_context_source": None,
        "opening_fallback_basis_count": 0,
        "opening_fallback_context_missing": False,
        "opening_fallback_failed_closed": False,
        "blocked_repair_kind": None,
        "opening_repair_source": "not_opening",
        "response_type_upstream_prepared_absent": False,
        "upstream_prepared_emission_used": False,
        "upstream_prepared_emission_valid": False,
        "upstream_prepared_emission_source": None,
        "upstream_prepared_emission_reject_reason": None,
        "final_emission_boundary_repair_used": False,
        "final_emission_boundary_semantic_repair_disabled": True,
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
            "opening_generic_action_repair_blocked": bool(debug.get("opening_generic_action_repair_blocked")),
            "opening_specific_repair_used": bool(debug.get("opening_specific_repair_used")),
            "opening_validation_failed": bool(debug.get("opening_validation_failed")),
            "opening_failure_reasons": list(debug.get("opening_failure_reasons") or []),
            "opening_recovered_via_fallback": bool(debug.get("opening_recovered_via_fallback")),
            "opening_fallback_context_source": debug.get("opening_fallback_context_source"),
            "opening_fallback_basis_count": int(debug.get("opening_fallback_basis_count") or 0),
            "opening_fallback_context_missing": bool(debug.get("opening_fallback_context_missing")),
            "opening_fallback_failed_closed": bool(debug.get("opening_fallback_failed_closed")),
            "blocked_repair_kind": debug.get("blocked_repair_kind"),
            "opening_repair_source": debug.get("opening_repair_source"),
            "response_type_upstream_prepared_absent": bool(debug.get("response_type_upstream_prepared_absent")),
            "upstream_prepared_emission_used": bool(debug.get("upstream_prepared_emission_used")),
            "upstream_prepared_emission_valid": bool(debug.get("upstream_prepared_emission_valid")),
            "upstream_prepared_emission_source": debug.get("upstream_prepared_emission_source"),
            "upstream_prepared_emission_reject_reason": debug.get("upstream_prepared_emission_reject_reason"),
            "final_emission_boundary_repair_used": bool(debug.get("final_emission_boundary_repair_used")),
            "final_emission_boundary_semantic_repair_disabled": (
                True
                if debug.get("final_emission_boundary_semantic_repair_disabled") is None
                else bool(debug.get("final_emission_boundary_semantic_repair_disabled"))
            ),
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
        "opening_generic_action_repair_blocked": bool(debug.get("opening_generic_action_repair_blocked")),
        "opening_specific_repair_used": bool(debug.get("opening_specific_repair_used")),
        "opening_validation_failed": bool(debug.get("opening_validation_failed")),
        "opening_failure_reasons": list(debug.get("opening_failure_reasons") or []),
        "opening_recovered_via_fallback": bool(debug.get("opening_recovered_via_fallback")),
        "opening_fallback_context_source": debug.get("opening_fallback_context_source"),
        "opening_fallback_basis_count": int(debug.get("opening_fallback_basis_count") or 0),
        "opening_fallback_context_missing": bool(debug.get("opening_fallback_context_missing")),
        "opening_fallback_failed_closed": bool(debug.get("opening_fallback_failed_closed")),
        "blocked_repair_kind": debug.get("blocked_repair_kind"),
        "opening_repair_source": debug.get("opening_repair_source"),
        "response_type_upstream_prepared_absent": bool(debug.get("response_type_upstream_prepared_absent")),
        "upstream_prepared_emission_used": bool(debug.get("upstream_prepared_emission_used")),
        "upstream_prepared_emission_valid": bool(debug.get("upstream_prepared_emission_valid")),
        "upstream_prepared_emission_source": debug.get("upstream_prepared_emission_source"),
        "upstream_prepared_emission_reject_reason": debug.get("upstream_prepared_emission_reject_reason"),
        "final_emission_boundary_repair_used": bool(debug.get("final_emission_boundary_repair_used")),
        "final_emission_boundary_semantic_repair_disabled": (
            True
            if debug.get("final_emission_boundary_semantic_repair_disabled") is None
            else bool(debug.get("final_emission_boundary_semantic_repair_disabled"))
        ),
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
    """Compatibility residue: canonical accessor now lives in ``game.response_policy_contracts``."""
    return _policy_resolve_answer_completeness_contract(gm_output)


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


# --- Fallback behavior (response_policy.fallback_behavior) -----------------

_FALLBACK_META_VOICE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi don'?t have enough information\b", re.IGNORECASE),
    re.compile(r"\bi can'?t verify that\b", re.IGNORECASE),
    re.compile(r"\binsufficient context\b", re.IGNORECASE),
    re.compile(r"\b(?:the )?(?:model|system|tool) can'?t tell\b", re.IGNORECASE),
    re.compile(r"\bnot established\b", re.IGNORECASE),
    re.compile(r"\bavailable to the model\b", re.IGNORECASE),
    re.compile(r"\bvisible to tools\b", re.IGNORECASE),
    re.compile(r"\banswerable by the system\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+reason|the\s+outcome|the\s+answer)\s+(?:is\s+)?still\s+unclear\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+answer|the\s+outcome)\s+remains\s+unresolved\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+answer|the\s+outcome)\s+is\s+unresolved\b", re.IGNORECASE),
    re.compile(r"\bcannot\s+yet\s+be\s+determined\b", re.IGNORECASE),
    re.compile(r"\b(?:that|this|it)\s+is\s+not\s+settled\b", re.IGNORECASE),
    re.compile(r"\bnot\s+settled\s+until\s+the\s+move\s+(?:plays\s+out|resolves)\b", re.IGNORECASE),
    re.compile(r"\buntil\s+the\s+move\s+(?:plays\s+out|resolves)\b", re.IGNORECASE),
    re.compile(r"\bthat\s+depends\s+on\s+how\s+the\s+move\s+(?:plays\s+out|resolves)\b", re.IGNORECASE),
    re.compile(r"\bthat\s+depends\s+on\s+the\s+roll\b", re.IGNORECASE),
    re.compile(r"\b(?:we|i)\s+don'?t\s+know\s+yet\s+(?:whether|if|who|what|where|why|how)\b", re.IGNORECASE),
)
_FALLBACK_FABRICATED_AUTHORITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi know\b", re.IGNORECASE),
    re.compile(r"\b(?:the )?record(?:s)? show(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bcanon says\b", re.IGNORECASE),
    re.compile(r"\b(?:the )?(?:system|tool|model) says\b", re.IGNORECASE),
    re.compile(r"\b(?:the )?evidence proves\b", re.IGNORECASE),
)
_FALLBACK_OVERCERTAIN_GENERAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bhe definitely\b", re.IGNORECASE),
    re.compile(r"\bshe definitely\b", re.IGNORECASE),
    re.compile(r"\bthey definitely\b", re.IGNORECASE),
    re.compile(r"\bthe answer is\b", re.IGNORECASE),
)
_FALLBACK_OVERCERTAIN_BY_SOURCE: Dict[str, tuple[re.Pattern[str], ...]] = {
    "unknown_identity": (
        re.compile(r"\bit was\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"),
        re.compile(r"\b(?:the culprit|the one) was\b", re.IGNORECASE),
        re.compile(r"\b(?:he|she|they) (?:was|were)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"),
    ),
    "unknown_location": (
        re.compile(r"\b(?:it|he|she|they) (?:is|was|are|were)\s+(?:at|in|inside|under|behind|near|on)\b", re.IGNORECASE),
        re.compile(r"\b(?:the exact )?(?:location|place) is\b", re.IGNORECASE),
    ),
    "unknown_motive": (
        re.compile(r"\b(?:the motive|the reason) was\b", re.IGNORECASE),
        re.compile(r"\b(?:he|she|they) did it because\b", re.IGNORECASE),
    ),
    "unknown_method": (
        re.compile(r"\b(?:the method|the way) was\b", re.IGNORECASE),
        re.compile(r"\b(?:he|she|they) did it by\b", re.IGNORECASE),
        re.compile(r"\bit was done by\b", re.IGNORECASE),
    ),
    "unknown_quantity": (
        re.compile(r"\b(?:exactly|precisely)\s+\d+\b", re.IGNORECASE),
        re.compile(r"\b(?:there (?:is|are)|it was)\s+\d+\b", re.IGNORECASE),
    ),
    "unknown_feasibility": (
        re.compile(r"\bit (?:will|would|can) work\b", re.IGNORECASE),
        re.compile(r"\bit is (?:possible|safe)\b", re.IGNORECASE),
        re.compile(r"\byou can definitely\b", re.IGNORECASE),
    ),
}
_FALLBACK_QUESTION_LEAD_RE = re.compile(
    r"^\s*(?:what|where|when|why|how|who|which|whose|do|did|does|can|could|would|will|is|are|was|were)\b",
    re.IGNORECASE,
)
# Narrator/meta lines that look like a partial but carry no observable anchor + lead (repair must replace).
_BOUNDED_PARTIAL_THIN_SUBSTANCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno name comes clear from what shows\b", re.IGNORECASE),
    re.compile(r"\bnothing is known\b", re.IGNORECASE),
    re.compile(r"\bnothing here names\b", re.IGNORECASE),
    re.compile(r"\bthe moment yields no answer at once\b", re.IGNORECASE),
)


def _bounded_partial_thin_substance_violation(text: str) -> bool:
    return any(p.search(str(text or "")) for p in _BOUNDED_PARTIAL_THIN_SUBSTANCE_PATTERNS)
_FALLBACK_DIEGETIC_PARTIAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:no one|nobody|none)\s+(?:answers?|commits?|steps in|bites)\s+(?:at once|right away|immediately)\b", re.IGNORECASE),
    re.compile(r"\bdoes not answer(?:\s+(?:at once|right away|directly))?\b", re.IGNORECASE),
    re.compile(r"\bstarts to answer,\s+then\b", re.IGNORECASE),
    re.compile(r"\bgives you nothing(?:\s+\w+){0,4}\b", re.IGNORECASE),
    re.compile(r"\bthey give nothing away about why\b", re.IGNORECASE),
    re.compile(r"\bnothing in plain view shows how it was done\b", re.IGNORECASE),
    re.compile(r"\bnothing in sight pins the place down\b", re.IGNORECASE),
    re.compile(r"\bno clean count shows\b", re.IGNORECASE),
    re.compile(r"\bno one commits themselves at once\b", re.IGNORECASE),
)


def _resolve_fallback_behavior_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Compatibility residue: canonical accessor now lives in ``game.response_policy_contracts``."""
    return _policy_resolve_fallback_behavior_contract(gm_output)


def _contains_meta_fallback_voice(text: str) -> bool:
    return any(p.search(text) for p in _FALLBACK_META_VOICE_PATTERNS)


def _contains_fabricated_authority(text: str) -> bool:
    return any(p.search(text) for p in _FALLBACK_FABRICATED_AUTHORITY_PATTERNS)


def _contains_overcertain_claim(text: str, *, contract: Dict[str, Any]) -> bool:
    if any(p.search(text) for p in _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS):
        return True
    sources = {
        str(src).strip().lower()
        for src in (contract.get("uncertainty_sources") or [])
        if isinstance(src, str) and str(src).strip()
    }
    for source in sources:
        for pattern in _FALLBACK_OVERCERTAIN_BY_SOURCE.get(source, ()):
            if pattern.search(text):
                return True
    return False


def _allowed_hedge_in_text(text: str, *, contract: Dict[str, Any]) -> bool:
    low = str(text or "").lower()
    forms = [
        str(item).strip().lower()
        for item in (contract.get("allowed_hedge_forms") or [])
        if isinstance(item, str) and str(item).strip()
    ]
    return any(form in low for form in forms)


def _count_terminal_questions(text: str) -> int:
    return sum(1 for sentence in _split_sentences_answer_complete(text) if sentence.rstrip().endswith("?"))


def _looks_like_single_clarifying_question(text: str) -> bool:
    sentences = _split_sentences_answer_complete(text)
    question_sentences = [s for s in sentences if s.rstrip().endswith("?")]
    if len(question_sentences) != 1:
        return False
    q = question_sentences[0].strip()
    if not _FALLBACK_QUESTION_LEAD_RE.search(q):
        return False
    if _word_count(q) > 22:
        return False
    non_questions = [s for s in sentences if s.strip() != q and not s.rstrip().endswith("?")]
    if non_questions and any(_word_count(s) >= 8 for s in non_questions):
        return False
    return True


def _contains_diegetic_uncertainty_partial(
    text: str,
    *,
    resolution: Dict[str, Any] | None = None,
) -> bool:
    if any(p.search(text) for p in _FALLBACK_DIEGETIC_PARTIAL_PATTERNS):
        return True
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    social_intent = str(social.get("social_intent_class") or "").strip().lower()
    prompt = str(resolution.get("prompt") or "")
    hint_text = f"{prompt} {text}".lower()
    social_turn = bool(social) or social_intent == "open_call"
    if not social_turn and not re.search(r"\b(?:ask|offer|talk|answer|bystander|crowd|runner|guard|captain)\b", hint_text):
        return False
    return bool(
        re.search(r"\b(?:eyes?|glances?|hesitates?|pauses?|looks tempted|keeps (?:his|her|their) attention on)\b", text, re.IGNORECASE)
        and re.search(
            r"\b(?:does not answer|without answering|instead of answering|no one answers|gives you nothing)\b",
            text,
            re.IGNORECASE,
        )
    )


def _detect_partial_shape(
    text: str,
    *,
    contract: Dict[str, Any],
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, bool]:
    partial_reason = _partial_reason_in_text(
        text,
        ["uncertainty", "lack_of_knowledge", "gated_information"],
    )
    allowed_hedge = _allowed_hedge_in_text(text, contract=contract)
    diegetic_partial = _contains_diegetic_uncertainty_partial(text, resolution=resolution)
    known_edge = _concrete_payload_for_kinds(text, ["name", "place", "direction", "fact", "condition"]) or diegetic_partial
    unknown_edge = bool(partial_reason or allowed_hedge or diegetic_partial)
    next_lead = _concrete_payload_for_kinds(text, ["next_lead"]) or bool(_NEXT_LEAD_SNIPPET.search(text))

    partial_detected = True
    if _contract_bool(contract, "require_partial_to_state_known_edge") and not known_edge:
        partial_detected = False
    if _contract_bool(contract, "require_partial_to_state_unknown_edge") and not unknown_edge:
        partial_detected = False
    if _contract_bool(contract, "require_partial_to_offer_next_lead") and not next_lead:
        partial_detected = False

    if not (
        _contract_bool(contract, "require_partial_to_state_known_edge")
        or _contract_bool(contract, "require_partial_to_state_unknown_edge")
        or _contract_bool(contract, "require_partial_to_offer_next_lead")
    ):
        partial_detected = bool(known_edge and (unknown_edge or next_lead))

    return {
        "partial_information_detected": partial_detected,
        "known_edge_present": known_edge,
        "unknown_edge_present": unknown_edge,
        "next_lead_present": next_lead,
    }


def validate_fallback_behavior(
    emitted_text: str,
    contract: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _ = resolution
    base: Dict[str, Any] = {
        "checked": False,
        "passed": True,
        "uncertainty_active": False,
        "contract_present": isinstance(contract, dict),
        "invented_certainty_detected": False,
        "fabricated_authority_detected": False,
        "meta_fallback_voice_detected": False,
        "allowed_hedge_detected": False,
        "clarifying_question_detected": False,
        "partial_information_detected": False,
        "known_edge_present": False,
        "unknown_edge_present": False,
        "next_lead_present": False,
        "question_count": 0,
        "failure_reasons": [],
        "skip_reason": None,
    }
    if not isinstance(contract, dict):
        base["skip_reason"] = "no_contract"
        return base
    if not bool(contract.get("uncertainty_active")):
        base["skip_reason"] = "uncertainty_inactive"
        return base

    base["uncertainty_active"] = True
    base["checked"] = True

    text = _normalize_text(emitted_text)
    base["question_count"] = _count_terminal_questions(text)
    base["meta_fallback_voice_detected"] = _contains_meta_fallback_voice(text)
    base["fabricated_authority_detected"] = _contains_fabricated_authority(text)
    base["invented_certainty_detected"] = _contains_overcertain_claim(text, contract=contract)
    base["allowed_hedge_detected"] = _allowed_hedge_in_text(text, contract=contract)
    base["clarifying_question_detected"] = _looks_like_single_clarifying_question(text)

    partial_shape = _detect_partial_shape(text, contract=contract, resolution=resolution)
    base.update(partial_shape)

    failure_reasons: List[str] = []
    disallowed = contract.get("disallowed_behaviors") if isinstance(contract.get("disallowed_behaviors"), dict) else {}
    allowed = contract.get("allowed_behaviors") if isinstance(contract.get("allowed_behaviors"), dict) else {}

    if disallowed.get("invented_certainty") and base["invented_certainty_detected"]:
        failure_reasons.append("invented_certainty")
    if disallowed.get("fabricated_authority") and base["fabricated_authority_detected"]:
        failure_reasons.append("fabricated_authority")
    if disallowed.get("meta_system_explanations") and base["meta_fallback_voice_detected"]:
        failure_reasons.append("meta_fallback_voice")

    max_questions = contract.get("max_clarifying_questions")
    if isinstance(max_questions, int) and max_questions >= 0 and base["question_count"] > max_questions:
        failure_reasons.append("too_many_clarifying_questions")

    partial_allowed = bool(allowed.get("provide_partial_information"))
    question_allowed = bool(allowed.get("ask_clarifying_question"))
    hedge_allowed = bool(allowed.get("hedge_appropriately"))

    partial_ok = bool(partial_allowed and base["partial_information_detected"])
    question_ok = bool(question_allowed and base["clarifying_question_detected"])
    hedge_partial_ok = bool(hedge_allowed and base["allowed_hedge_detected"] and base["partial_information_detected"])

    if (
        question_ok
        and bool(contract.get("prefer_partial_over_question"))
        and partial_allowed
        and not (base["known_edge_present"] or base["next_lead_present"])
    ):
        failure_reasons.append("question_used_when_partial_preferred")

    if not (partial_ok or question_ok or hedge_partial_ok):
        failure_reasons.append("missing_allowed_fallback_shape")

    if (
        _contract_bool(contract, "require_partial_to_state_known_edge")
        and _contract_bool(contract, "require_partial_to_offer_next_lead")
        and _bounded_partial_thin_substance_violation(text)
        and not (base["known_edge_present"] and base["next_lead_present"])
    ):
        failure_reasons.append("bounded_partial_insufficient_substance")

    base["failure_reasons"] = list(dict.fromkeys(str(r) for r in failure_reasons if r))
    base["passed"] = not bool(base["failure_reasons"])
    return base


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
    """Compatibility residue: canonical accessor now lives in ``game.response_policy_contracts``."""
    return _policy_resolve_response_delta_contract(gm_output)


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


# --- Social response structure (response_policy.social_response_structure) ---------------

_SOCIAL_STRUCTURE_SNAPSHOT_KEYS: tuple[str, ...] = (
    "enabled",
    "applies_to_response_type",
    "require_spoken_dialogue_shape",
    "discourage_expository_monologue",
    "require_natural_cadence",
    "allow_brief_action_beats",
    "allow_brief_refusal_or_uncertainty",
    "max_contiguous_expository_lines",
    "max_dialogue_paragraphs_before_break",
    "prefer_single_speaker_turn",
    "forbid_bulleted_or_list_like_dialogue",
    "required_response_type",
)

_EXPOSITORY_CONNECTOR_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:therefore|furthermore|moreover|consequently|accordingly|in (?:summary|conclusion|short)|"
        r"notably|importantly|that (?:said|being said)|as (?:a )?result|which (?:meant|means)|"
        r"for instance|for example|in other words|on (?:the )?other hand)\b",
        re.IGNORECASE,
    ),
)
_ABSTRACT_EXPOSITION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:historically|traditionally|generally speaking|it (?:is|was) (?:often|usually|typically)|"
        r"the (?:implication|significance|underlying|broader) (?:issue|meaning|theme))\b",
        re.IGNORECASE,
    ),
)
_UNCERTAINTY_OR_REFUSAL_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:don'?t know|do not know|can'?t say|cannot say|won'?t say|not (?:at liberty|here))\b", re.IGNORECASE),
    re.compile(r"\b(?:not sure|unclear|maybe|perhaps|hard to say|no idea)\b", re.IGNORECASE),
    re.compile(r"\b(?:none of your business|ask someone else|end of discussion)\b", re.IGNORECASE),
)
_SPOKEN_CUE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r'["“”][^"”]{2,}["“”]'),
    re.compile(
        r"\b(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|"
        r"snaps|snapped|asks|asked|spits|spat|grunts|grunted)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\b.{0,120}\?", re.IGNORECASE | re.DOTALL),
)
_BULLET_LINE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*[\-\*•◦]\s+\S", re.MULTILINE),
    re.compile(r"^\s*\d+[\.)]\s+\S", re.MULTILINE),
    re.compile(r"^\s*[a-z]\)\s+\S", re.MULTILINE | re.IGNORECASE),
)
_COLON_LIST_LINE_RE = re.compile(r"^.{6,120}:\s+\S.{3,}$", re.MULTILINE)
_MULTI_SPEAKER_LINE_RE = re.compile(
    r"(?:^|\n)\s*[A-Z][a-zA-Z]{1,18}\s*:\s*[\"“]",
    re.MULTILINE,
)


def _resolve_social_response_structure_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Compatibility residue: canonical accessor now lives in ``game.response_policy_contracts``."""
    return _policy_resolve_social_response_structure_contract(gm_output)


def _social_response_structure_contract_snapshot(contract: Dict[str, Any]) -> Dict[str, Any]:
    return {k: contract.get(k) for k in _SOCIAL_STRUCTURE_SNAPSHOT_KEYS}


def _social_structure_applicable(contract: Dict[str, Any]) -> bool:
    if not _contract_bool(contract, "enabled"):
        return False
    applies = str(contract.get("applies_to_response_type") or "").strip().lower()
    if applies and applies != "dialogue":
        return False
    req = str(contract.get("required_response_type") or "").strip().lower()
    if req and req != "dialogue":
        return False
    return True


def _raw_lines_preserving_breaks(text: str) -> List[str]:
    raw = str(text or "")
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def _paragraph_blocks(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"\n\s*\n+", raw)
    return [p.strip() for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", str(text or "")))


def _avg_sentence_length_words(sentences: List[str]) -> float:
    if not sentences:
        return 0.0
    lengths = [_word_count(s) for s in sentences]
    return float(sum(lengths)) / float(len(lengths))


def _max_single_sentence_words(sentences: List[str]) -> int:
    if not sentences:
        return 0
    return max(_word_count(s) for s in sentences)


def _connector_hits(text: str, patterns: tuple[re.Pattern[str], ...]) -> int:
    return sum(1 for p in patterns if p.search(text))


def _looks_like_refusal_or_uncertainty(text: str) -> bool:
    return any(p.search(text) for p in _UNCERTAINTY_OR_REFUSAL_RES)


def _first_person_near_you_lead(text: str, *, window: int = 200) -> bool:
    head = str(text or "")[: max(window, 1)].lower()
    if "you" not in head:
        return False
    return bool(re.search(r"\b(i|i'?m|i'?ve|i'?ll|we|we'?re|we'?ve)\b", head))


def _spoken_reply_signals(text: str) -> Dict[str, Any]:
    t = str(text or "")
    low = t.lower()
    return {
        "has_curly_or_straight_quotes": bool(re.search(r'["“”]', t)),
        "spoken_cue_hits": sum(1 for p in _SPOKEN_CUE_RES if p.search(t)),
        "first_person_addresses_you_in_lead": _first_person_near_you_lead(t),
        "has_you": bool(re.search(r"\byou\b", low)),
        "word_count": _word_count(t),
    }


def _has_spoken_dialogue_shape(text: str) -> bool:
    sig = _spoken_reply_signals(text)
    if sig["spoken_cue_hits"] >= 1:
        return True
    if sig.get("first_person_addresses_you_in_lead"):
        return True
    wc = int(sig["word_count"])
    if wc <= 12:
        return True
    if sig["has_you"] and wc <= 36:
        return True
    if sig["has_curly_or_straight_quotes"]:
        return True
    low = str(text or "").lower()
    if re.search(
        r"\b(?:says|replies|asks|mutters|whispers|frowns|grimaces|shakes their head|glances past you)\b",
        low,
    ):
        return True
    return False


def _line_reads_expository(line: str) -> bool:
    s = str(line or "").strip()
    if not s:
        return False
    wc = _word_count(s)
    if wc >= 22 and not re.search(r'["“”]', s):
        return True
    if _connector_hits(s, _EXPOSITORY_CONNECTOR_RES) >= 1 and wc >= 12:
        return True
    if _connector_hits(s, _ABSTRACT_EXPOSITION_RES) >= 1:
        return True
    return False


def _max_contiguous_expository_lines(lines: List[str]) -> int:
    best = 0
    cur = 0
    for ln in lines:
        if _line_reads_expository(ln):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _paragraph_is_brief_action_beat(block: str) -> bool:
    b = str(block or "").strip()
    if not b:
        return False
    wc = _word_count(b)
    if wc <= 10 and not re.search(r'["“”]', b):
        return True
    if wc <= 14 and re.search(r"\b(?:nods?|shrugs?|sighs?|pauses?|leans?|steps?|eyes?|jaw|hand)\b", b, re.IGNORECASE):
        return True
    return False


def _list_like_dialogue_signals(text: str) -> Dict[str, Any]:
    t = str(text or "")
    bullet_lines = sum(len(list(p.finditer(t))) for p in _BULLET_LINE_RES)
    colon_list_lines = len(_COLON_LIST_LINE_RE.findall(t))
    return {
        "bullet_or_numbered_line_hits": bullet_lines,
        "colon_list_line_count": colon_list_lines,
    }


def _looks_list_like_dialogue(text: str) -> bool:
    sig = _list_like_dialogue_signals(text)
    if sig["bullet_or_numbered_line_hits"] >= 1:
        return True
    if sig["colon_list_line_count"] >= 3:
        return True
    if sig["colon_list_line_count"] >= 2 and _word_count(text) <= 120:
        return True
    return False


def _multi_speaker_signals(text: str) -> Dict[str, Any]:
    t = str(text or "")
    name_colon = len(_MULTI_SPEAKER_LINE_RE.findall(t))
    return {"name_colon_quote_opens": name_colon}


def _looks_multi_speaker_turn(text: str) -> bool:
    return _multi_speaker_signals(text)["name_colon_quote_opens"] >= 2


def inspect_social_response_structure(result: Dict[str, Any]) -> Dict[str, Any]:
    """Structured inspect helper for logging / debugging (mirrors ``inspect_*_failure`` style)."""
    if not isinstance(result, dict):
        return {"failed": False}
    if result.get("passed") is not False:
        return {"failed": False}
    return {
        "failed": True,
        "reasons": list(result.get("reasons") or result.get("failure_reasons") or []),
        "failure_reasons": list(result.get("failure_reasons") or []),
        "signals": dict(result.get("signals") or {}),
        "applicable": bool(result.get("applicable")),
    }


def validate_social_response_structure(
    emitted_text: str,
    contract: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic validation for ``response_policy.social_response_structure`` (text inspection only)."""
    base: Dict[str, Any] = {
        "checked": False,
        "applicable": False,
        "passed": True,
        "failure_reasons": [],
        "reasons": [],
        "signals": {},
        "contract_snapshot": None,
    }
    c = contract if isinstance(contract, dict) else None
    if c is None and gm_output is not None:
        c = _resolve_social_response_structure_contract(gm_output)
    if not isinstance(c, dict):
        return base

    base["contract_snapshot"] = _social_response_structure_contract_snapshot(c)
    if not _social_structure_applicable(c):
        return base

    base["applicable"] = True
    base["checked"] = True

    raw = str(emitted_text or "")
    text = _normalize_text(raw)
    lines = _raw_lines_preserving_breaks(raw)
    paragraphs = _paragraph_blocks(raw)
    sentences = _split_sentences_answer_complete(text)

    allow_beat = _contract_bool(c, "allow_brief_action_beats")
    allow_unc = _contract_bool(c, "allow_brief_refusal_or_uncertainty")
    uncertainty_ok = allow_unc and _looks_like_refusal_or_uncertainty(text)

    sig: Dict[str, Any] = {
        **_spoken_reply_signals(text),
        "paragraph_count": len(paragraphs),
        "non_empty_line_count": len(lines),
        "sentence_count": len(sentences),
        "avg_sentence_length_words": round(_avg_sentence_length_words(sentences), 3),
        "max_sentence_words": _max_single_sentence_words(sentences),
        "expository_connector_hits": _connector_hits(text, _EXPOSITORY_CONNECTOR_RES),
        "abstract_exposition_hits": _connector_hits(text, _ABSTRACT_EXPOSITION_RES),
        "max_contiguous_expository_lines_observed": _max_contiguous_expository_lines(lines),
        **_list_like_dialogue_signals(text),
        **_multi_speaker_signals(raw),
        "refusal_or_uncertainty_relaxed": uncertainty_ok,
    }
    base["signals"] = sig

    failure_reasons: List[str] = []

    if not text:
        failure_reasons.append("empty_emitted_text")
        base["failure_reasons"] = list(failure_reasons)
        base["reasons"] = list(failure_reasons)
        base["passed"] = False
        return base

    if _contract_bool(c, "forbid_bulleted_or_list_like_dialogue") and _looks_list_like_dialogue(text):
        failure_reasons.append("list_like_or_bulleted_dialogue")

    if _contract_bool(c, "prefer_single_speaker_turn") and _looks_multi_speaker_turn(raw):
        failure_reasons.append("multi_speaker_turn_formatting")

    max_exp_lines = c.get("max_contiguous_expository_lines")
    if isinstance(max_exp_lines, int) and max_exp_lines >= 0:
        streak = int(sig["max_contiguous_expository_lines_observed"])
        if streak > max_exp_lines:
            failure_reasons.append("too_many_contiguous_expository_lines")

    max_para = c.get("max_dialogue_paragraphs_before_break")
    if isinstance(max_para, int) and max_para >= 0 and paragraphs:
        if allow_beat:
            substantive_paragraphs = [p for p in paragraphs if not _paragraph_is_brief_action_beat(p)]
        else:
            substantive_paragraphs = list(paragraphs)
        if len(substantive_paragraphs) > max_para:
            failure_reasons.append("too_many_dialogue_paragraphs_without_break")

    if _contract_bool(c, "require_spoken_dialogue_shape") and not _has_spoken_dialogue_shape(text):
        failure_reasons.append("missing_spoken_dialogue_shape")

    if _contract_bool(c, "require_natural_cadence"):
        max_w = int(sig["max_sentence_words"])
        n_sent = int(sig["sentence_count"])
        avg_w = float(sig["avg_sentence_length_words"])
        if n_sent == 1 and max_w >= 95:
            failure_reasons.append("unnatural_monoblob_cadence")
        elif n_sent >= 4 and avg_w >= 32:
            failure_reasons.append("heavy_expository_sentence_cadence")

    if _contract_bool(c, "discourage_expository_monologue") and not uncertainty_ok:
        wc = int(sig["word_count"])
        conn = int(sig["expository_connector_hits"]) + int(sig["abstract_exposition_hits"])
        if wc >= 90 and conn >= 2 and not sig.get("has_curly_or_straight_quotes"):
            failure_reasons.append("expository_monologue_density")
        elif wc >= 55 and conn >= 3:
            failure_reasons.append("expository_monologue_density")

    base["failure_reasons"] = list(dict.fromkeys(str(r) for r in failure_reasons if r))
    base["reasons"] = list(base["failure_reasons"])
    base["passed"] = not bool(base["failure_reasons"])
    return base


def candidate_satisfies_social_response_structure(
    text: str,
    *,
    contract: Dict[str, Any] | None = None,
    gm_output: Dict[str, Any] | None = None,
) -> tuple[bool, List[str]]:
    """Tuple helper aligned with ``candidate_satisfies_*`` in this module."""
    r = validate_social_response_structure(text, contract, gm_output=gm_output)
    if not r.get("applicable"):
        return True, []
    return bool(r.get("passed")), list(r.get("failure_reasons") or [])


# --- Referent clarity (prompt ``referent_tracking`` artifact; deterministic) -----------------

_REFERENT_PRONOUN_RE = re.compile(
    r"\b(he|she|they|him|her|them|their|his|hers|theirs)\b",
    re.IGNORECASE,
)
_REFERENT_LEAD_WINDOW = 220
_CLAUSE_AMBIGUITY_RISKY = frozenset({"ambiguous_plural", "ambiguous_singular", "no_anchor"})
_GENDERED_PRONOUN_BUCKETS = frozenset({"he_him", "she_her"})


def _is_full_referent_artifact(obj: Any) -> bool:
    if not isinstance(obj, Mapping):
        return False
    if obj.get("version") != REFERENT_TRACKING_ARTIFACT_VERSION:
        return False
    rac = obj.get("referential_ambiguity_class")
    return rac in ("none", "ambiguous_plural", "ambiguous_singular", "no_anchor")


def _referent_active_entity_names(artifact: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in artifact.get("active_entities") or []:
        if not isinstance(row, Mapping):
            continue
        eid = str(row.get("entity_id") or "").strip()
        nm = str(row.get("display_name") or "").strip()
        if eid and nm:
            out[eid] = nm
    return out


def _referent_forbidden_display_names(artifact: Mapping[str, Any]) -> set[str]:
    """Lowercased display strings tied to forbidden / off-visible ids (observability only)."""
    id_to_name = _referent_active_entity_names(artifact)
    names: set[str] = set()
    for row in artifact.get("forbidden_or_unresolved_patterns") or []:
        if not isinstance(row, Mapping):
            continue
        kind = str(row.get("kind") or "").strip().lower()
        if kind not in {
            "memory_entity_not_visible",
            "ctir_addressed_not_visible",
            "target_id_not_visible",
            "continuity_object_not_visible",
            "interaction_target_drift",
        }:
            continue
        eid = str(
            row.get("entity_id") or row.get("prior_target_id") or row.get("current_target_id") or ""
        ).strip()
        nm = str(row.get("display_name") or "").strip()
        if not nm and eid:
            nm = id_to_name.get(eid, "")
        if nm:
            names.add(nm.lower())
    return names


def _artifact_authorizes_explicit_label(artifact: Mapping[str, Any], label: str) -> bool:
    """True when *label* matches an allow-listed explicit anchor on the full referent artifact."""
    lab = str(label or "").strip().lower()
    if not lab:
        return False
    if lab in _referent_forbidden_display_names(artifact):
        return False
    for row in artifact.get("allowed_named_references") or []:
        if isinstance(row, Mapping) and str(row.get("display_name") or "").strip().lower() == lab:
            return True
    for row in artifact.get("safe_explicit_fallback_labels") or []:
        if isinstance(row, Mapping) and str(row.get("safe_explicit_label") or "").strip().lower() == lab:
            return True
    sue = artifact.get("single_unambiguous_entity")
    if isinstance(sue, Mapping) and str(sue.get("label") or "").strip().lower() == lab:
        return True
    cs = artifact.get("continuity_subject")
    itc = artifact.get("interaction_target_continuity")
    active_tgt = str(artifact.get("active_interaction_target") or "").strip()
    if (
        isinstance(cs, Mapping)
        and isinstance(itc, Mapping)
        and active_tgt
        and str(cs.get("entity_id") or "").strip() == active_tgt
        and bool(itc.get("target_visible"))
        and not bool(itc.get("drift_detected"))
    ):
        if str(cs.get("display_name") or "").strip().lower() == lab:
            return True
    return False


def _referent_allowed_display_tokens(artifact: Mapping[str, Any]) -> set[str]:
    toks: set[str] = set()
    for row in artifact.get("allowed_named_references") or []:
        if not isinstance(row, Mapping):
            continue
        nm = str(row.get("display_name") or "").strip()
        eid = str(row.get("entity_id") or "").strip()
        if nm:
            toks.add(nm.lower())
        if eid:
            toks.add(eid.lower().replace("_", " "))
    for row in artifact.get("safe_explicit_fallback_labels") or []:
        if not isinstance(row, Mapping):
            continue
        lab = str(row.get("safe_explicit_label") or "").strip()
        if lab:
            toks.add(lab.lower())
    sue = artifact.get("single_unambiguous_entity")
    if isinstance(sue, Mapping):
        lab = str(sue.get("label") or "").strip()
        if lab:
            toks.add(lab.lower())
    return toks


def _opening_has_pronoun_risk(text: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return False
    head = t[:_REFERENT_LEAD_WINDOW]
    return bool(_REFERENT_PRONOUN_RE.search(head))


def _text_mentions_forbidden_name(text: str, forbidden_lc: set[str]) -> bool:
    if not forbidden_lc:
        return False
    low = str(text or "").lower()
    for name in forbidden_lc:
        if not name or len(name) < 2:
            continue
        if re.search(rf"(?<![a-z0-9_]){re.escape(name)}(?![a-z0-9_])", low):
            return True
    return False


def _clause_referent_plan_rows(artifact: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    crp = artifact.get("clause_referent_plan")
    if not isinstance(crp, list):
        return []
    return [r for r in crp if isinstance(r, Mapping)]


def _clause_row_has_explicit_anchor_support(row: Mapping[str, Any]) -> bool:
    labs = row.get("allowed_explicit_labels")
    if not isinstance(labs, list):
        return False
    return any(isinstance(x, str) and str(x).strip() for x in labs)


def _clause_row_ambiguity_or_bucket_supports_tightening(row: Mapping[str, Any]) -> bool:
    amb = str(row.get("ambiguity_class") or "").strip().lower()
    if amb in _CLAUSE_AMBIGUITY_RISKY:
        return True
    buckets = row.get("risky_pronoun_buckets") if isinstance(row.get("risky_pronoun_buckets"), list) else []
    for b in buckets:
        if not isinstance(b, str):
            continue
        bk = str(b).strip().lower().replace(" ", "_")
        if bk in _GENDERED_PRONOUN_BUCKETS or bk == "it_its":
            return True
    return False


def _try_clause_referent_plan_repair_label(full: Mapping[str, Any], text: str) -> tuple[str | None, str | None]:
    """Read-side: one repair label from ``clause_referent_plan`` when structural gates fire (gate does not build rows)."""
    if not _opening_has_pronoun_risk(text):
        return None, None
    for row in _clause_referent_plan_rows(full):
        labs_raw = row.get("allowed_explicit_labels") if isinstance(row.get("allowed_explicit_labels"), list) else []
        labs = [str(x).strip() for x in labs_raw if isinstance(x, str) and str(x).strip()]
        if len(labs) != 1:
            continue
        label = labs[0]
        if not _artifact_authorizes_explicit_label(full, label):
            continue
        tss = bool(row.get("target_switch_sensitive"))
        struct_ok = _clause_row_ambiguity_or_bucket_supports_tightening(row) or (
            tss and _unsupported_target_switch_signal(full)
        )
        if not struct_ok:
            continue
        return label, "clause_referent_plan"
    return None, None


def _unsupported_target_switch_signal(artifact: Mapping[str, Any]) -> bool:
    itc = artifact.get("interaction_target_continuity")
    if not isinstance(itc, Mapping):
        return False
    if bool(itc.get("drift_detected")):
        return True
    cur = str(itc.get("current_target_id") or "").strip()
    sig = str(itc.get("signal_target_id") or "").strip()
    if cur and sig and cur != sig:
        return True
    return False


def validate_referent_clarity(
    emitted_text: str,
    *,
    referent_tracking: Dict[str, Any] | None,
    referent_tracking_compact: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Deterministic referent checks using the full prompt artifact when present.

    Read-only over ``referent_tracking`` / ``referent_tracking_compact`` (no in-place mutation).
    When only ``referent_tracking_compact`` exists, records observability and abstains
    from repair-driving violations (no reconstruction of the full artifact).
    """
    base: Dict[str, Any] = {
        "referent_validation_ran": False,
        "referent_validation_input_source": None,
        "referent_violation_categories": [],
        "unresolved_referent_ambiguity": False,
        "referent_repair_allowed_label": None,
        "referent_repair_label_source": None,
    }
    text = _normalize_text(emitted_text)
    if not text:
        base["referent_validation_input_source"] = "missing"
        return base

    full = referent_tracking if _is_full_referent_artifact(referent_tracking) else None
    compact = referent_tracking_compact if isinstance(referent_tracking_compact, Mapping) else None

    if full is not None:
        base["referent_validation_input_source"] = "full_artifact"
    elif compact:
        base["referent_validation_input_source"] = "packet_compact"
    else:
        base["referent_validation_input_source"] = "missing"
        return base

    base["referent_validation_ran"] = True

    if full is None:
        rac = str((compact or {}).get("referential_ambiguity_class") or "").strip().lower() or None
        base["referent_violation_categories"] = []
        base["unresolved_referent_ambiguity"] = rac not in (None, "", "none")
        return base

    categories: List[str] = []
    sue = full.get("single_unambiguous_entity")
    sue_ok = isinstance(sue, Mapping) and bool(str(sue.get("label") or "").strip())
    safe_rows = [r for r in (full.get("safe_explicit_fallback_labels") or []) if isinstance(r, Mapping)]
    exactly_one_safe = len(safe_rows) == 1 and bool(str(safe_rows[0].get("safe_explicit_label") or "").strip())

    if sue_ok:
        base["referent_repair_allowed_label"] = str(sue.get("label") or "").strip()
        base["referent_repair_label_source"] = "single_unambiguous_entity"
    elif exactly_one_safe:
        base["referent_repair_allowed_label"] = str(safe_rows[0].get("safe_explicit_label") or "").strip()
        base["referent_repair_label_source"] = "safe_explicit_fallback_labels"
    else:
        cs = full.get("continuity_subject")
        itc = full.get("interaction_target_continuity")
        active_tgt = str(full.get("active_interaction_target") or "").strip()
        if (
            isinstance(cs, Mapping)
            and isinstance(itc, Mapping)
            and active_tgt
            and str(cs.get("entity_id") or "").strip() == active_tgt
            and bool(itc.get("target_visible"))
            and not bool(itc.get("drift_detected"))
        ):
            lab = str(cs.get("display_name") or "").strip()
            if lab:
                base["referent_repair_allowed_label"] = lab
                base["referent_repair_label_source"] = "active_interaction_target_pinned"

    if not base.get("referent_repair_allowed_label"):
        cl_lab, cl_src = _try_clause_referent_plan_repair_label(full, text)
        if cl_lab and cl_src:
            base["referent_repair_allowed_label"] = cl_lab
            base["referent_repair_label_source"] = cl_src

    rac = str(full.get("referential_ambiguity_class") or "").strip().lower()
    risk = int(full.get("ambiguity_risk") or 0) if isinstance(full.get("ambiguity_risk"), int) else 0
    pr = full.get("pronoun_resolution") if isinstance(full.get("pronoun_resolution"), Mapping) else {}
    strat = str(pr.get("strategy") or "").strip().lower()

    if rac in ("ambiguous_plural", "ambiguous_singular", "no_anchor") and _opening_has_pronoun_risk(text):
        categories.append("ambiguous_pronoun_environment")
    if strat == "unresolved" and _opening_has_pronoun_risk(text):
        categories.append("ambiguous_pronoun_environment")

    if sue_ok and _opening_has_pronoun_risk(text):
        categories.append("explicit_subject_substitution_eligible")

    if (not sue_ok) and (not exactly_one_safe) and _opening_has_pronoun_risk(text):
        categories.append("pronoun_before_anchor")

    if _unsupported_target_switch_signal(full) and _opening_has_pronoun_risk(text):
        categories.append("target_continuity_drift")

    active_tgt = str(full.get("active_interaction_target") or "").strip()
    itc = full.get("interaction_target_continuity") if isinstance(full.get("interaction_target_continuity"), Mapping) else {}
    if (
        active_tgt
        and isinstance(itc, Mapping)
        and bool(itc.get("drift_detected"))
        and sue_ok
        and str((sue or {}).get("entity_id") or "").strip() != active_tgt
    ):
        categories.append("unsupported_target_switch")

    forb_names = _referent_forbidden_display_names(full)
    if forb_names and _text_mentions_forbidden_name(text, forb_names):
        categories.append("disallowed_named_reference_in_text")

    cr_rows = _clause_referent_plan_rows(full)
    if cr_rows and _opening_has_pronoun_risk(text):
        for row in cr_rows:
            if _clause_row_has_explicit_anchor_support(row):
                continue
            tss = bool(row.get("target_switch_sensitive"))
            amb = str(row.get("ambiguity_class") or "").strip().lower()
            bucket_tight = _clause_row_ambiguity_or_bucket_supports_tightening(row)
            if tss and _unsupported_target_switch_signal(full):
                categories.append("clause_target_switch_sensitive_without_authorized_explicit")
            if amb in _CLAUSE_AMBIGUITY_RISKY and bucket_tight:
                categories.append("clause_ambiguous_lane_without_authorized_explicit")

    base["referent_violation_categories"] = list(dict.fromkeys(categories))
    base["unresolved_referent_ambiguity"] = bool(
        categories
        or rac in ("ambiguous_plural", "ambiguous_singular", "no_anchor")
        or risk >= 55
    )
    return base
