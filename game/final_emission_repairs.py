"""Final-emission **legality + packaging** helpers (Objective C2 Block C).

Support-only repair owner for the gate: deterministic strip/remove/substitute and layer wiring only.

Validators and metadata wiring for the gate live here. Final emission is **not** a planner,
semantic repair owner, or contract-shaped prose author: answer/action fallbacks and spoken
refinement cash-out moved to :mod:`game.upstream_response_repairs`; strict-social terminal shaping
stays in :mod:`game.social_exchange_emission`.

This module keeps strip/remove/substitute surfaces, referent-clarity **optional** substitution
(when ``allow_semantic_text_repair=True`` for non–final-gate callers), narrative-authenticity
validation-only at the gate boundary, and observability merges—no reorder-for-meaning or template
synthesis at the boundary.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from game.final_emission_meta import (
    build_narrative_authenticity_emission_trace,
    default_narrative_authenticity_layer_meta,
    merge_narrative_authenticity_into_final_emission_meta,
)
from game.final_emission_text import (
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.final_emission_validators import (
    _text_mentions_forbidden_name,
    _FALLBACK_FABRICATED_AUTHORITY_PATTERNS,
    _FALLBACK_META_VOICE_PATTERNS,
    _FALLBACK_OVERCERTAIN_BY_SOURCE,
    _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS,
    _concrete_payload_for_kinds,
    _contract_bool,
    _looks_like_single_clarifying_question,
    _response_delta_snippet_substantive,
    _split_sentences_answer_complete,
    inspect_social_response_structure,
    validate_answer_completeness,
    validate_answer_exposition_plan_convergence,
    validate_fallback_behavior,
    validate_response_delta,
    validate_referent_clarity,
    validate_social_response_structure,
)
from game.response_policy_contracts import (
    materialize_response_policy_bundle,
    resolve_answer_completeness_contract,
    resolve_fallback_behavior_contract,
    resolve_response_delta_contract,
)
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.turn_packet import TURN_PACKET_METADATA_KEY, resolve_turn_packet_for_gate


def _skip_answer_completeness_layer(
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    """Return skip reason, or None when the layer should run."""
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if isinstance(gm_output, dict):
        tags_ac = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
        tl = [str(t) for t in tags_ac if isinstance(t, str)]
        if "question_retry_fallback" in tl and (
            "known_fact_guard" in tl
            or "social_answer_retry" in tl
        ):
            dbg_ac = gm_output.get("debug_notes") if isinstance(gm_output.get("debug_notes"), str) else ""
            if "retry_fallback_chosen:nonsocial_uncertainty_pool_after_block1_social_out_of_scope" in dbg_ac:
                return None
            return "deterministic_known_fact_retry_fallback"
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


def _apply_answer_completeness_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_answer_completeness_contract(gm_output)
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
        "answer_completeness_boundary_semantic_repair_disabled": True,
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

    extra: List[str] = []
    if not strict_social_path:
        extra.append("answer_completeness_unsatisfied_at_boundary_no_reorder")
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


def _default_answer_exposition_plan_meta() -> Dict[str, Any]:
    return {
        "answer_exposition_plan_checked": False,
        "answer_exposition_plan_present": False,
        "answer_exposition_plan_valid": False,
        "answer_exposition_plan_passed": True,
        "answer_exposition_plan_failure_reasons": [],
        "answer_exposition_plan_required_fact_ids": [],
        "answer_exposition_plan_repair_modes": [],
    }


def _apply_answer_exposition_plan_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
) -> tuple[str, Dict[str, Any], List[str]]:
    """Final-emission enforcement for answer_exposition_plan convergence (deterministic, bounded).

    Runs only when answer_completeness indicates answer_required.
    """
    meta = _default_answer_exposition_plan_meta()
    if response_type_debug.get("response_type_candidate_ok") is False:
        return text, meta, []

    ac = resolve_answer_completeness_contract(gm_output)
    answer_required = bool((ac or {}).get("answer_required")) if isinstance(ac, dict) else False
    plan = (ac or {}).get("answer_exposition_plan") if isinstance(ac, dict) else None

    v0 = validate_answer_exposition_plan_convergence(
        text,
        answer_required=bool(answer_required),
        answer_exposition_plan=plan if isinstance(plan, dict) else None,
    )
    meta["answer_exposition_plan_checked"] = bool(v0.get("checked"))
    meta["answer_exposition_plan_present"] = bool(v0.get("plan_present"))
    meta["answer_exposition_plan_valid"] = bool(v0.get("plan_valid"))
    meta["answer_exposition_plan_passed"] = bool(v0.get("passed"))
    meta["answer_exposition_plan_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["answer_exposition_plan_required_fact_ids"] = list(v0.get("required_fact_ids") or [])

    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    # No inventive repairs: do not generate missing facts or fallback exposition.
    # Reorder is only allowed if boundary contract allows it; use sentence-only permutation.
    reasons = set(str(r) for r in (meta.get("answer_exposition_plan_failure_reasons") or []) if str(r).strip())
    if "answer_must_come_first_violation" in reasons:
        from game.final_emission_validators import _mentions_fact_text  # local import to avoid cycles

        delivery = plan.get("delivery") if isinstance(plan, dict) and isinstance(plan.get("delivery"), dict) else {}
        must_ids = delivery.get("must_include_fact_ids") if isinstance(delivery.get("must_include_fact_ids"), list) else []
        req_ids = [str(x) for x in must_ids if isinstance(x, str) and str(x).strip()][:16]
        facts = plan.get("facts") if isinstance(plan, dict) and isinstance(plan.get("facts"), list) else []
        id_to_fact = {str(f.get("id") or "").strip(): f for f in facts if isinstance(f, dict)}
        sentences = _split_sentences_answer_complete(text)
        if len(sentences) >= 2 and req_ids:
            # Find first sentence that contains any required fact; move it to front.
            idx = None
            for i, s in enumerate(sentences):
                for fid in req_ids:
                    f = id_to_fact.get(fid)
                    if isinstance(f, dict) and _mentions_fact_text(s, str(f.get("fact") or "")):
                        idx = i
                        break
                if idx is not None:
                    break
            if idx is not None and idx > 0:
                candidate = " ".join([sentences[idx]] + [s for i, s in enumerate(sentences) if i != idx])
                candidate = _normalize_text(candidate)
                if candidate and candidate != _normalize_text(text):
                    assert_final_emission_mutation_allowed(
                        "reorder_answer_to_front",
                        source="final_emission_repairs._apply_answer_exposition_plan_layer.safe_sentence_reorder",
                    )
                    # Revalidate; only accept if it now passes without introducing new failures.
                    v1 = validate_answer_exposition_plan_convergence(
                        candidate,
                        answer_required=True,
                        answer_exposition_plan=plan if isinstance(plan, dict) else None,
                    )
                    if bool(v1.get("passed")):
                        meta["answer_exposition_plan_repair_modes"] = ["safe_sentence_reorder_answer_first"]
                        meta["answer_exposition_plan_passed"] = True
                        meta["answer_exposition_plan_failure_reasons"] = []
                        return candidate, meta, []

    # Failure remains: record boundary-only failure without semantic synthesis.
    extra = ["answer_exposition_plan_failed_at_boundary"]
    meta["answer_exposition_plan_passed"] = False
    return text, meta, extra


def _merge_answer_exposition_plan_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "answer_exposition_plan_checked": bool(dbg.get("answer_exposition_plan_checked")),
            "answer_exposition_plan_present": bool(dbg.get("answer_exposition_plan_present")),
            "answer_exposition_plan_valid": bool(dbg.get("answer_exposition_plan_valid")),
            "answer_exposition_plan_passed": bool(dbg.get("answer_exposition_plan_passed")),
            "answer_exposition_plan_failure_reasons": list(dbg.get("answer_exposition_plan_failure_reasons") or []),
            "answer_exposition_plan_required_fact_ids": list(
                dbg.get("answer_exposition_plan_required_fact_ids") or []
            ),
            "answer_exposition_plan_repair_modes": list(dbg.get("answer_exposition_plan_repair_modes") or []),
        }
    )


def _default_response_delta_meta() -> Dict[str, Any]:
    """Canonical **legality** metadata keys for the gate-owned response-delta layer (not NA/evaluator)."""
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
        "response_delta_boundary_semantic_repair_disabled": True,
    }


def _strict_social_answer_pressure_ac_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when prompt_context activated answer-completeness for strict-social answer-pressure (Block 1)."""
    ac = resolve_answer_completeness_contract(gm_output)
    if not isinstance(ac, dict):
        return False
    if not _contract_bool(ac, "enabled") or not _contract_bool(ac, "answer_required"):
        return False
    trace = ac.get("trace") if isinstance(ac.get("trace"), dict) else {}
    return bool(trace.get("strict_social_answer_seek_override"))


def _strict_social_answer_pressure_rd_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when response_delta is enabled with strict_social_answer_pressure trigger (Block 1)."""
    rd = resolve_response_delta_contract(gm_output)
    if not isinstance(rd, dict) or not _contract_bool(rd, "enabled"):
        return False
    ts = str(rd.get("trigger_source") or "").strip()
    if ts == "strict_social_answer_pressure":
        return True
    tr = rd.get("trace") if isinstance(rd.get("trace"), dict) else {}
    return str(tr.get("trigger_source") or "").strip() == "strict_social_answer_pressure"


def _repair_probe_for_answer_pressure_policy(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Compatibility residue: canonical bundle read-side helper lives in ``game.response_policy_contracts``."""
    return materialize_response_policy_bundle(gm_output, session)


# Compatibility residue: older repair/gate imports may still use the earlier helper name.
def _gm_probe_for_answer_pressure_contracts(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    return _repair_probe_for_answer_pressure_policy(gm_output, session)


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


def _apply_response_delta_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_response_delta_contract(gm_output)
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

    extra: List[str] = []
    if not strict_social_path:
        extra.append("response_delta_unsatisfied_at_boundary_no_reorder")
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


def _flatten_list_like_dialogue(text: str) -> str:
    """Strip list/bullet/numbered prefixes and join lines into prose (no new list items)."""
    lines = [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
    if not lines:
        return _normalize_text(text or "")
    out: List[str] = []
    for ln in lines:
        s = ln
        s = re.sub(r"^\s*[\-\*•◦]\s+", "", s)
        s = re.sub(r"^\s*\d+[\.)]\s+", "", s)
        s = re.sub(r"^\s*[a-z]\)\s+", "", s, flags=re.IGNORECASE)
        if re.match(r"^.{6,120}:\s+\S", s):
            s = re.sub(r"^(.{6,120}):\s+", r"\1 — ", s, count=1)
        out.append(s.strip())
    return _normalize_text(" ".join(out))


def _collapse_multi_speaker_formatting(text: str) -> str:
    """Keep a single quoted reply body when multiple Name: \"...\" blocks appear."""
    pat = re.compile(
        r"(?:^|\n)\s*[A-Z][a-zA-Z]{1,18}\s*:\s*[\"“]([^\"”]{1,1200})[\"”]",
        re.MULTILINE,
    )
    matches = list(pat.finditer(str(text or "")))
    if len(matches) < 2:
        return text
    best = max((m.group(1).strip() for m in matches), key=len)
    return _normalize_text(best) if best else _normalize_text(text or "")


def _collapse_soft_line_breaks(text: str) -> str:
    """Turn single newlines into spaces; keeps blank-line paragraph boundaries."""
    t = str(text or "")
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    return _normalize_text(t)


def apply_social_response_structure_repair(
    text: str,
    *,
    failure_reasons: List[str],
    gm_output: Dict[str, Any] | None = None,
) -> tuple[str, str | None]:
    """Packaging-only fixes (bullets → prose, soft line breaks). No cadence/density/opening authorship."""
    _ = gm_output
    reasons = [str(r) for r in (failure_reasons or []) if str(r).strip()]
    if not reasons:
        return text, None
    rset = set(reasons)
    t = str(text or "")
    modes: List[str] = []

    if "list_like_or_bulleted_dialogue" in rset:
        t2 = _flatten_list_like_dialogue(t)
        if t2 != _normalize_text(t):
            t = t2
            modes.append("flatten_list_like_dialogue")

    if "too_many_contiguous_expository_lines" in rset:
        t2 = _collapse_soft_line_breaks(t)
        if t2 != t:
            t = t2
            modes.append("collapse_soft_line_breaks_only")

    t = _normalize_text(t)
    if not modes:
        return text, None
    return t, "+".join(modes)


def _default_social_response_structure_meta() -> Dict[str, Any]:
    return {
        "social_response_structure_checked": False,
        "social_response_structure_applicable": False,
        "social_response_structure_passed": True,
        "social_response_structure_failure_reasons": [],
        "social_response_structure_repair_applied": False,
        "social_response_structure_repair_changed_text": False,
        "social_response_structure_repair_passed": None,
        "social_response_structure_repair_mode": None,
        "social_response_structure_skip_reason": None,
        "social_response_structure_inspect": None,
        "social_response_structure_boundary_semantic_repair_disabled": False,
    }


def _skip_social_response_structure_layer(
    *,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    """Orchestration skips only; applicability remains owned by the validator."""
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if bool(answer_completeness_meta.get("answer_completeness_failed")):
        return "answer_completeness_failed"
    if not _normalize_text(emitted_text or ""):
        return "empty_emitted_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            if _strict_social_answer_pressure_rd_contract_active(gm_output):
                return None
            return "strict_social_structured_or_bridge_source"
    return None


def _apply_social_response_structure_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    """Dialogue-shape enforcement: depends on prior contracts (response type, answer completeness, delta).

    Runs before downstream policy layers so terminal fallbacks are not asked to preserve bad social form
    when a minimal structural repair can satisfy ``validate_social_response_structure``.
    """
    meta = _default_social_response_structure_meta()
    skip = _skip_social_response_structure_layer(
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=answer_completeness_meta,
        gm_output=gm_output,
    )
    meta["social_response_structure_skip_reason"] = skip
    if skip:
        return text, meta, []

    v0 = validate_social_response_structure(text, None, gm_output=gm_output)
    meta["social_response_structure_checked"] = bool(v0.get("checked"))
    meta["social_response_structure_applicable"] = bool(v0.get("applicable"))
    meta["social_response_structure_passed"] = bool(v0.get("passed"))
    meta["social_response_structure_failure_reasons"] = list(v0.get("failure_reasons") or [])

    if not v0.get("checked") or not v0.get("applicable"):
        return text, meta, []

    if v0.get("passed"):
        return text, meta, []

    # Block C: list→prose / cadence / structural dialogue repairs are SEMANTIC_DISALLOWED at final emission;
    # record validation only — upstream (``upstream_response_repairs``, social emission) owns repairs.
    meta["social_response_structure_boundary_semantic_repair_disabled"] = True
    meta["social_response_structure_passed"] = False
    meta["social_response_structure_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["social_response_structure_repair_applied"] = False
    meta["social_response_structure_repair_changed_text"] = False
    meta["social_response_structure_repair_passed"] = False
    meta["social_response_structure_repair_mode"] = None
    meta["social_response_structure_inspect"] = inspect_social_response_structure(v0)
    return text, meta, []


def _merge_social_response_structure_meta(meta: Dict[str, Any], srs_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "social_response_structure_checked": bool(srs_dbg.get("social_response_structure_checked")),
            "social_response_structure_applicable": bool(srs_dbg.get("social_response_structure_applicable")),
            "social_response_structure_passed": bool(srs_dbg.get("social_response_structure_passed")),
            "social_response_structure_failure_reasons": list(srs_dbg.get("social_response_structure_failure_reasons") or []),
            "social_response_structure_repair_applied": bool(srs_dbg.get("social_response_structure_repair_applied")),
            "social_response_structure_repair_changed_text": bool(srs_dbg.get("social_response_structure_repair_changed_text")),
            "social_response_structure_repair_passed": srs_dbg.get("social_response_structure_repair_passed"),
            "social_response_structure_repair_mode": srs_dbg.get("social_response_structure_repair_mode"),
            "social_response_structure_skip_reason": srs_dbg.get("social_response_structure_skip_reason"),
            "social_response_structure_inspect": srs_dbg.get("social_response_structure_inspect"),
            "social_response_structure_boundary_semantic_repair_disabled": bool(
                srs_dbg.get("social_response_structure_boundary_semantic_repair_disabled")
            ),
        }
    )


def _default_narrative_authenticity_meta() -> Dict[str, Any]:
    """Compatibility residue wrapper derived from :mod:`game.final_emission_meta` defaults."""
    return default_narrative_authenticity_layer_meta()


def _merge_narrative_authenticity_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    """Compatibility residue wrapper; metadata schema ownership stays in :mod:`game.final_emission_meta`."""
    merge_narrative_authenticity_into_final_emission_meta(meta, na_dbg)


def _skip_narrative_authenticity_layer(
    *,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not _normalize_text(emitted_text or ""):
        return "empty_emitted_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            return "strict_social_structured_or_bridge_source"
    if isinstance(gm_output, dict):
        tags = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
        tl = [str(t) for t in tags if isinstance(t, str)]
        if "question_retry_fallback" in tl and ("known_fact_guard" in tl or "social_answer_retry" in tl):
            return "deterministic_known_fact_retry_fallback"
    return None


def _apply_narrative_authenticity_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    """NA layer runs **after** ``_apply_response_delta_layer``; NA repairs must not subsume delta repair."""
    from game.narrative_authenticity import (
        resolve_narrative_authenticity_contract,
        validate_narrative_authenticity,
    )

    contract = resolve_narrative_authenticity_contract(gm_output)
    meta = _default_narrative_authenticity_meta()
    skip = _skip_narrative_authenticity_layer(
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        gm_output=gm_output,
    )
    meta["narrative_authenticity_skip_reason"] = skip
    if skip:
        meta.update(
            build_narrative_authenticity_emission_trace(
                {"skip_reason": skip, "checked": False, "passed": True},
                contract=contract if isinstance(contract, dict) else None,
            )
        )
        return text, meta, []
    if not isinstance(contract, dict):
        meta["narrative_authenticity_skip_reason"] = "no_contract"
        meta.update(
            build_narrative_authenticity_emission_trace(
                {"skip_reason": "no_contract", "checked": False, "passed": True},
                contract=None,
            )
        )
        return text, meta, []

    v0 = validate_narrative_authenticity(text, contract, gm_output=gm_output)
    meta["narrative_authenticity_checked"] = bool(v0.get("checked"))
    if v0.get("skip_reason"):
        meta["narrative_authenticity_skip_reason"] = v0.get("skip_reason")
    if not v0.get("checked"):
        meta.update(build_narrative_authenticity_emission_trace(v0, contract=contract))
        return text, meta, []

    if v0.get("passed"):
        meta.update(
            build_narrative_authenticity_emission_trace(
                v0, contract=contract, repaired=False, repair_failed=False
            )
        )
        return text, meta, []

    meta["narrative_authenticity_failed"] = True
    meta["narrative_authenticity_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["narrative_authenticity_boundary_semantic_repair_disabled"] = True
    meta["narrative_authenticity_repaired"] = False
    meta["narrative_authenticity_repair_applied"] = False
    meta["narrative_authenticity_repair_mode"] = None
    meta["narrative_authenticity_repair_failure_reason"] = "semantic_repair_must_occur_upstream"
    meta.update(
        build_narrative_authenticity_emission_trace(v0, contract=contract, repaired=False, repair_failed=True)
    )

    extra: List[str] = []
    if not strict_social_path:
        extra.append("narrative_authenticity_unsatisfied_after_repair")
    return text, meta, extra


def _default_fallback_behavior_meta() -> Dict[str, Any]:
    return {
        "fallback_behavior_contract_present": False,
        "fallback_behavior_checked": False,
        "fallback_behavior_skip_reason": None,
        "fallback_behavior_uncertainty_active": False,
        "fallback_behavior_failed": False,
        "fallback_behavior_failure_reasons": [],
        "fallback_behavior_repaired": False,
        "fallback_behavior_repair_mode": "none",
        "fallback_behavior_clarifying_question_used": False,
        "fallback_behavior_partial_used": False,
        "fallback_behavior_known_edge_preserved": False,
        "fallback_behavior_unknown_edge_added": False,
        "fallback_behavior_next_lead_added": False,
        "fallback_behavior_meta_voice_stripped": False,
        "fallback_behavior_boundary_semantic_synthesis_skipped": False,
        "final_emission_boundary_semantic_repair_disabled": False,
        "final_emission_semantic_repair_skipped": False,
        "final_emission_semantic_repair_skip_reason": None,
    }


def _merge_fallback_behavior_meta(meta: Dict[str, Any], fb_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "fallback_behavior_contract_present": bool(fb_dbg.get("fallback_behavior_contract_present")),
            "fallback_behavior_checked": bool(fb_dbg.get("fallback_behavior_checked")),
            "fallback_behavior_skip_reason": fb_dbg.get("fallback_behavior_skip_reason"),
            "fallback_behavior_uncertainty_active": bool(fb_dbg.get("fallback_behavior_uncertainty_active")),
            "fallback_behavior_failed": bool(fb_dbg.get("fallback_behavior_failed")),
            "fallback_behavior_failure_reasons": list(fb_dbg.get("fallback_behavior_failure_reasons") or []),
            "fallback_behavior_repaired": bool(fb_dbg.get("fallback_behavior_repaired")),
            "fallback_behavior_repair_mode": fb_dbg.get("fallback_behavior_repair_mode"),
            "fallback_behavior_clarifying_question_used": bool(
                fb_dbg.get("fallback_behavior_clarifying_question_used")
            ),
            "fallback_behavior_partial_used": bool(fb_dbg.get("fallback_behavior_partial_used")),
            "fallback_behavior_known_edge_preserved": bool(
                fb_dbg.get("fallback_behavior_known_edge_preserved")
            ),
            "fallback_behavior_unknown_edge_added": bool(
                fb_dbg.get("fallback_behavior_unknown_edge_added")
            ),
            "fallback_behavior_next_lead_added": bool(fb_dbg.get("fallback_behavior_next_lead_added")),
            "fallback_behavior_meta_voice_stripped": bool(
                fb_dbg.get("fallback_behavior_meta_voice_stripped")
            ),
            "fallback_behavior_boundary_semantic_synthesis_skipped": bool(
                fb_dbg.get("fallback_behavior_boundary_semantic_synthesis_skipped")
            ),
            "final_emission_boundary_semantic_repair_disabled": bool(
                fb_dbg.get("final_emission_boundary_semantic_repair_disabled")
            ),
            "final_emission_semantic_repair_skipped": bool(fb_dbg.get("final_emission_semantic_repair_skipped")),
            "final_emission_semantic_repair_skip_reason": fb_dbg.get("final_emission_semantic_repair_skip_reason"),
        }
    )


def _fallback_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", str(text or "")))


def _fallback_sentences(text: str) -> List[str]:
    return [s for s in _split_sentences_answer_complete(text) if str(s).strip()]


def _strip_patterns_from_text(
    text: str,
    *,
    patterns: Tuple[re.Pattern[str], ...],
) -> str:
    out: List[str] = []
    for sentence in _fallback_sentences(text):
        candidate = sentence
        for pattern in patterns:
            candidate = pattern.sub("", candidate)
        candidate = re.sub(r"\s+", " ", candidate).strip(" ,;:-")
        candidate = re.sub(r"\s+([,.!?;:])", r"\1", candidate).strip()
        if _fallback_word_count(candidate) >= 2:
            out.append(_normalize_terminal_punctuation(candidate))
    return _normalize_text(" ".join(out))


def _sentence_matches_overcertain_source(sentence: str, contract: Dict[str, Any]) -> bool:
    if any(p.search(sentence) for p in _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS):
        return True
    for source in [
        str(item).strip().lower()
        for item in (contract.get("uncertainty_sources") or [])
        if isinstance(item, str) and str(item).strip()
    ]:
        if any(p.search(sentence) for p in _FALLBACK_OVERCERTAIN_BY_SOURCE.get(source, ())):
            return True
    return False


def _strip_meta_fallback_voice(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    cleaned = _strip_patterns_from_text(text, patterns=_FALLBACK_META_VOICE_PATTERNS)
    forbidden = [
        re.compile(re.escape(str(item).strip()), re.IGNORECASE)
        for item in ((contract or {}).get("forbidden_hedge_forms") or [])
        if isinstance(item, str) and str(item).strip()
    ]
    if forbidden:
        cleaned = _strip_patterns_from_text(cleaned or text, patterns=tuple(forbidden))
    return cleaned


def _remove_fabricated_authority(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    _ = contract
    return _strip_patterns_from_text(text, patterns=_FALLBACK_FABRICATED_AUTHORITY_PATTERNS)


def _downgrade_overcertain_claims(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    ctr = contract if isinstance(contract, dict) else {}
    kept: List[str] = []
    for sentence in _fallback_sentences(text):
        if not _sentence_matches_overcertain_source(sentence, ctr):
            kept.append(_normalize_terminal_punctuation(sentence))
            continue
        trimmed = sentence
        for pattern in _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS:
            trimmed = pattern.sub("", trimmed)
        trimmed = re.sub(r"\bdefinitely\b", "", trimmed, flags=re.IGNORECASE)
        trimmed = re.sub(r"\s+", " ", trimmed).strip(" ,;:-")
        trimmed = re.sub(r"\s+([,.!?;:])", r"\1", trimmed).strip()
        if _concrete_payload_for_kinds(trimmed, ["next_lead"]) and _fallback_word_count(trimmed) >= 3:
            kept.append(_normalize_terminal_punctuation(trimmed))
            continue
        if (
            _concrete_payload_for_kinds(trimmed, ["name", "place", "direction", "fact", "condition"])
            and not _sentence_matches_overcertain_source(trimmed, ctr)
            and _fallback_word_count(trimmed) >= 3
        ):
            kept.append(_normalize_terminal_punctuation(trimmed))
    return _normalize_text(" ".join(kept))


# C2_OWNER_AUDIT: move-upstream — template synthesis / shape construction should converge out of final emission; see docs/final_emission_ownership_convergence.md.
def repair_fallback_behavior(
    emitted_text: str,
    contract: Dict[str, Any] | None,
    validation: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
    strict_social_path: bool = False,
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> Tuple[str, Dict[str, Any], List[str]]:
    _ = strict_social_path, resolution, session, scene_id
    meta = _default_fallback_behavior_meta()
    ctr = contract if isinstance(contract, dict) else {}
    val = validation if isinstance(validation, dict) else {}
    original = _normalize_text(emitted_text)
    working = original
    modes: List[str] = []

    if val.get("meta_fallback_voice_detected"):
        stripped = _strip_meta_fallback_voice(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            assert_final_emission_mutation_allowed(
                "strip_meta_fallback_voice_surfaces",
                source="final_emission_repairs.repair_fallback_behavior.strip_meta_voice",
            )
            working = stripped
            meta["fallback_behavior_meta_voice_stripped"] = True
            modes.append("strip_meta_voice")

    if val.get("fabricated_authority_detected"):
        stripped = _remove_fabricated_authority(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            assert_final_emission_mutation_allowed(
                "strip_fabricated_authority_surfaces",
                source="final_emission_repairs.repair_fallback_behavior.remove_fabricated_authority",
            )
            working = stripped
            modes.append("remove_fabricated_authority")

    if val.get("invented_certainty_detected"):
        stripped = _downgrade_overcertain_claims(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            assert_final_emission_mutation_allowed(
                "trim_overcertain_claim_spans",
                source="final_emission_repairs.repair_fallback_behavior.downgrade_invented_certainty",
            )
            working = stripped
            modes.append("downgrade_invented_certainty")

    meta["fallback_behavior_boundary_semantic_synthesis_skipped"] = True
    meta["final_emission_boundary_semantic_repair_disabled"] = True
    meta["final_emission_semantic_repair_skipped"] = True
    meta["final_emission_semantic_repair_skip_reason"] = "repair_fallback_behavior_strip_only_no_template_synthesis"

    final_text = _normalize_text(working or original)
    if _looks_like_single_clarifying_question(final_text):
        meta["fallback_behavior_clarifying_question_used"] = True
    if _normalize_text(final_text) != _normalize_text(original):
        meta["fallback_behavior_repaired"] = True
    if modes:
        meta["fallback_behavior_repair_mode"] = "+".join(dict.fromkeys(modes))
    return final_text, meta, []


def _apply_fallback_behavior_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_path: bool,
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> Tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_fallback_behavior_contract(gm_output)
    meta = _default_fallback_behavior_meta()
    meta["fallback_behavior_contract_present"] = isinstance(contract, dict)

    tags = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
    tag_set = {str(t) for t in tags if isinstance(t, str)}
    if "known_fact_guard" in tag_set and "question_retry_fallback" in tag_set:
        meta["fallback_behavior_skip_reason"] = "deterministic_known_fact_retry_answer"
        return text, meta, []

    v0 = validate_fallback_behavior(text, contract, resolution=resolution)
    meta["fallback_behavior_checked"] = bool(v0.get("checked"))
    meta["fallback_behavior_skip_reason"] = v0.get("skip_reason")
    meta["fallback_behavior_uncertainty_active"] = bool(v0.get("uncertainty_active"))
    if not v0.get("checked"):
        return text, meta, []
    if v0.get("passed"):
        return text, meta, []

    meta["fallback_behavior_failed"] = True
    meta["fallback_behavior_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired_text, repair_meta, _ = repair_fallback_behavior(
        text,
        contract,
        v0,
        resolution=resolution,
        strict_social_path=strict_social_path,
        session=session,
        scene_id=scene_id,
    )
    _merge_fallback_behavior_meta(meta, repair_meta)

    candidate = repaired_text if _normalize_text(repaired_text) else text
    v1 = validate_fallback_behavior(candidate, contract, resolution=resolution)
    meta["fallback_behavior_checked"] = bool(v1.get("checked"))
    meta["fallback_behavior_skip_reason"] = v1.get("skip_reason")
    meta["fallback_behavior_uncertainty_active"] = bool(v1.get("uncertainty_active"))
    if v1.get("passed"):
        meta["fallback_behavior_failed"] = False
        meta["fallback_behavior_failure_reasons"] = []
        return candidate, meta, []

    meta["fallback_behavior_failed"] = bool(v1.get("checked") and not v1.get("passed"))
    meta["fallback_behavior_failure_reasons"] = list(v1.get("failure_reasons") or v0.get("failure_reasons") or [])
    if _normalize_text(candidate) != _normalize_text(text):
        return candidate, meta, []
    extra: List[str] = []
    if not strict_social_path:
        extra.append("fallback_behavior_unsatisfied_after_repair")
    return text, meta, extra


# --- Referent clarity (full prompt artifact; compact packet observability only) ----------
# N5: ``clause_referent_plan`` is read in ``validate_referent_clarity`` only; this module does not
# construct it. Repairs: existing single pronoun → explicit label path only. Spec:
# ``docs/clause_level_referent_tracking.md``.

_REFERENT_REPLACE_PRONOUN_RE = re.compile(
    r"\b(he|she|they|him|her|them)\b",
    re.IGNORECASE,
)


def _default_referent_clarity_layer_meta() -> Dict[str, Any]:
    return {
        "referent_validation_ran": False,
        "referent_validation_input_source": None,
        "referent_violation_categories": [],
        "referent_repair_allowed_label": None,
        "referent_repair_label_source": None,
        "referent_repair_applied": False,
        "referent_repair_strategy": None,
        "referent_repair_skipped_reason": None,
        "unresolved_referent_ambiguity": False,
        "referent_boundary_semantic_repair_disabled": False,
    }


def _merge_referent_clarity_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "referent_validation_ran": bool(dbg.get("referent_validation_ran")),
            "referent_validation_input_source": dbg.get("referent_validation_input_source"),
            "referent_violation_categories": list(dbg.get("referent_violation_categories") or []),
            "referent_repair_allowed_label": dbg.get("referent_repair_allowed_label"),
            "referent_repair_label_source": dbg.get("referent_repair_label_source"),
            "referent_repair_applied": bool(dbg.get("referent_repair_applied")),
            "referent_repair_strategy": dbg.get("referent_repair_strategy"),
            "referent_repair_skipped_reason": dbg.get("referent_repair_skipped_reason"),
            "unresolved_referent_ambiguity": bool(dbg.get("unresolved_referent_ambiguity")),
            "referent_boundary_semantic_repair_disabled": bool(dbg.get("referent_boundary_semantic_repair_disabled")),
        }
    )


def _resolve_referent_tracking_compact(gm_output: Dict[str, Any]) -> Dict[str, Any] | None:
    tp = resolve_turn_packet_for_gate(gm_output)
    if isinstance(tp, dict):
        c = tp.get("referent_tracking_compact")
        if isinstance(c, dict):
            return c
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        nested = md.get(TURN_PACKET_METADATA_KEY)
        if isinstance(nested, dict):
            c = nested.get("referent_tracking_compact")
            if isinstance(c, dict):
                return c
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        nested = pc.get("turn_packet") or pc.get(TURN_PACKET_METADATA_KEY)
        if isinstance(nested, dict):
            c = nested.get("referent_tracking_compact")
            if isinstance(c, dict):
                return c
    cached = gm_output.get("_gate_turn_packet_cache")
    if isinstance(cached, dict):
        c = cached.get("referent_tracking_compact")
        if isinstance(c, dict):
            return c
    return None


def _resolve_referent_tracking_inputs(gm_output: Dict[str, Any]) -> tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    pc = gm_output.get("prompt_context") if isinstance(gm_output.get("prompt_context"), dict) else None
    full: Dict[str, Any] | None = None
    if pc:
        rt = pc.get("referent_tracking")
        if isinstance(rt, dict):
            full = rt
    compact = _resolve_referent_tracking_compact(gm_output)
    return full, compact


def _referent_forbidden_name_lc_set(artifact: Dict[str, Any]) -> set[str]:
    from game.final_emission_validators import _referent_forbidden_display_names

    return _referent_forbidden_display_names(artifact)


def _referent_insert_label_allowed(artifact: Dict[str, Any], label: str) -> bool:
    lab = str(label or "").strip().lower()
    if not lab:
        return False
    if lab in _referent_forbidden_name_lc_set(artifact):
        return False
    for row in artifact.get("allowed_named_references") or []:
        if isinstance(row, dict) and str(row.get("display_name") or "").strip().lower() == lab:
            return True
    for row in artifact.get("safe_explicit_fallback_labels") or []:
        if isinstance(row, dict) and str(row.get("safe_explicit_label") or "").strip().lower() == lab:
            return True
    sue = artifact.get("single_unambiguous_entity")
    if isinstance(sue, dict) and str(sue.get("label") or "").strip().lower() == lab:
        return True
    cs = artifact.get("continuity_subject")
    if isinstance(cs, dict) and str(cs.get("display_name") or "").strip().lower() == lab:
        eid = str(cs.get("entity_id") or "").strip()
        active = str(artifact.get("active_interaction_target") or "").strip()
        itc = artifact.get("interaction_target_continuity") if isinstance(artifact.get("interaction_target_continuity"), dict) else {}
        if eid and active and eid == active and bool(itc.get("target_visible")) and not bool(itc.get("drift_detected")):
            return True
    return False


def _repair_referent_clarity_minimal(
    text: str,
    validation: Dict[str, Any],
    artifact: Dict[str, Any],
) -> tuple[str | None, str | None]:
    cats = {str(c) for c in (validation.get("referent_violation_categories") or []) if str(c).strip()}
    if "disallowed_named_reference_in_text" in cats or "unsupported_target_switch" in cats:
        return None, None
    label = str(validation.get("referent_repair_allowed_label") or "").strip()
    if not label or not _referent_insert_label_allowed(artifact, label):
        return None, None
    if not cats.intersection(
        {
            "pronoun_before_anchor",
            "ambiguous_pronoun_environment",
            "target_continuity_drift",
            "explicit_subject_substitution_eligible",
        }
    ):
        return None, None
    if "target_continuity_drift" in cats and validation.get("referent_repair_label_source") != "active_interaction_target_pinned":
        if artifact.get("single_unambiguous_entity") is None:
            return None, None
    t = str(text or "")
    m = _REFERENT_REPLACE_PRONOUN_RE.search(t)
    if not m:
        return None, None
    merged = t[: m.start()] + label + t[m.end() :]
    return _normalize_text(merged), "replace_first_risky_pronoun_with_explicit_label"


def _apply_referent_clarity_emission_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    allow_semantic_text_repair: bool = True,
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = _default_referent_clarity_layer_meta()
    full, compact = _resolve_referent_tracking_inputs(gm_output)
    v0 = validate_referent_clarity(
        text,
        referent_tracking=full,
        referent_tracking_compact=compact,
    )
    meta["referent_validation_ran"] = bool(v0.get("referent_validation_ran"))
    meta["referent_validation_input_source"] = v0.get("referent_validation_input_source")
    meta["referent_violation_categories"] = list(v0.get("referent_violation_categories") or [])
    meta["referent_repair_allowed_label"] = v0.get("referent_repair_allowed_label")
    meta["referent_repair_label_source"] = v0.get("referent_repair_label_source")
    meta["unresolved_referent_ambiguity"] = bool(v0.get("unresolved_referent_ambiguity"))

    src = str(v0.get("referent_validation_input_source") or "")
    if src == "missing":
        meta["referent_repair_skipped_reason"] = "no_referent_inputs"
        return text, meta, []
    if src == "packet_compact":
        meta["referent_repair_skipped_reason"] = "limited_input_no_full_artifact"
        return text, meta, []

    if not isinstance(full, dict):
        meta["referent_repair_skipped_reason"] = "no_full_artifact"
        return text, meta, []

    if not v0.get("referent_violation_categories"):
        return text, meta, []

    if not allow_semantic_text_repair:
        meta["referent_boundary_semantic_repair_disabled"] = True
        meta["referent_repair_skipped_reason"] = "semantic_repair_must_occur_upstream"
        return text, meta, []

    repaired, mode = _repair_referent_clarity_minimal(text, v0, full)
    if not repaired or not mode:
        meta["referent_repair_skipped_reason"] = "no_safe_deterministic_repair"
        return text, meta, []

    v1 = validate_referent_clarity(
        repaired,
        referent_tracking=full,
        referent_tracking_compact=compact,
    )
    v1_cats = set(v1.get("referent_violation_categories") or [])
    if "disallowed_named_reference_in_text" in v1_cats:
        meta["referent_repair_skipped_reason"] = "repair_introduced_or_retained_forbidden_reference"
        return text, meta, []
    forb = _referent_forbidden_name_lc_set(full)
    if forb and _text_mentions_forbidden_name(repaired, forb):
        meta["referent_repair_skipped_reason"] = "post_repair_forbidden_name_signal"
        return text, meta, []

    meta["referent_repair_applied"] = _normalize_text(repaired) != _normalize_text(text)
    meta["referent_repair_strategy"] = mode
    return repaired, meta, []
