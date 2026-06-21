"""Narrative mode output contract read, validation, and FEM trace packaging.

Pure contract read paths, legality assessment, and trace merge helpers for C4
narrative-mode output enforcement. Orchestration timing and hard-replace policy
remain in :mod:`game.final_emission_gate`.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from game.final_emission_meta import (
    NARRATIVE_MODE_OUTPUT_FEM_KEYS,
    default_narrative_mode_output_layer_meta,
    ensure_final_emission_meta_dict,
    merge_narrative_mode_output_into_final_emission_meta,
)
from game.narrative_mode_contract import (
    build_narrative_mode_emission_trace,
    validate_narrative_mode_contract,
    validate_narrative_mode_output,
)


def _shipped_narrative_mode_contract_from_gm_output(gm_output: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    """Return planner-shipped ``narrative_mode_contract`` from the plan / ``prompt_context`` seam only."""
    if not isinstance(gm_output, Mapping):
        return None
    pc = gm_output.get("prompt_context")
    if not isinstance(pc, Mapping):
        return None
    plan = pc.get("narrative_plan")
    if not isinstance(plan, Mapping):
        return None
    raw = plan.get("narrative_mode_contract")
    return dict(raw) if isinstance(raw, dict) else None


def _pack_narrative_mode_output_assessment(
    *,
    validation: Mapping[str, Any],
    contract_for_trace: Mapping[str, Any] | None,
    skip_reason: str | None,
) -> Dict[str, Any]:
    trace = dict(build_narrative_mode_emission_trace(validation, narrative_mode_contract=contract_for_trace))
    if skip_reason:
        trace["narrative_mode_output_skip_reason"] = skip_reason
    elif bool(validation.get("checked")):
        trace["narrative_mode_output_skip_reason"] = None
    enf = bool(validation.get("checked")) and not bool(validation.get("passed"))
    nms = [str(x) for x in (validation.get("failure_reasons") or []) if str(x).strip()] if enf else []
    return {"trace": trace, "non_strict_gate_reasons": nms, "nmo_enforcement_fail": enf}


def _narrative_mode_output_legality_assessment(
    text: str,
    gm_output: Mapping[str, Any] | None,
    *,
    resolution_for_nmo: Mapping[str, Any] | None,
    strict_social_details_flag: bool | None,
) -> Dict[str, Any]:
    """C4 — deterministic narrative-mode output legality vs shipped contract (telemetry + enforcement bits)."""
    rp = gm_output.get("response_policy") if isinstance(gm_output, Mapping) else None
    rp = rp if isinstance(rp, Mapping) else None

    shipped = _shipped_narrative_mode_contract_from_gm_output(gm_output)
    if shipped is None:
        v = validate_narrative_mode_output(
            str(text or ""),
            None,
            resolution=resolution_for_nmo,
            response_policy=rp,
            strict_social_details=strict_social_details_flag,
        )
        return _pack_narrative_mode_output_assessment(
            validation=v,
            contract_for_trace=None,
            skip_reason="narrative_mode_contract_absent",
        )

    ok_shape, shape_reasons = validate_narrative_mode_contract(shipped)
    if not ok_shape:
        v = validate_narrative_mode_output(
            str(text or ""),
            shipped,
            resolution=resolution_for_nmo,
            response_policy=rp,
            strict_social_details=strict_social_details_flag,
        )
        fr0 = str(shape_reasons[0]).strip() if shape_reasons else "narrative_mode_contract_invalid"
        return _pack_narrative_mode_output_assessment(
            validation=v,
            contract_for_trace=None,
            skip_reason=f"narrative_mode_contract_invalid:{fr0}",
        )

    if not bool(shipped.get("enabled", True)):
        v = validate_narrative_mode_output(
            str(text or ""),
            shipped,
            resolution=resolution_for_nmo,
            response_policy=rp,
            strict_social_details=strict_social_details_flag,
        )
        return _pack_narrative_mode_output_assessment(
            validation=v,
            contract_for_trace=shipped,
            skip_reason="narrative_mode_contract_disabled",
        )

    v = validate_narrative_mode_output(
        str(text or ""),
        shipped,
        resolution=resolution_for_nmo,
        response_policy=rp,
        strict_social_details=strict_social_details_flag,
    )
    return _pack_narrative_mode_output_assessment(
        validation=v,
        contract_for_trace=shipped,
        skip_reason=None,
    )


def _merge_narrative_mode_output_trace_into_gate_fem(out: Dict[str, Any], trace: Mapping[str, Any] | None) -> None:
    if not isinstance(out, dict) or not trace:
        return
    fem = ensure_final_emission_meta_dict(out)
    merge_narrative_mode_output_into_final_emission_meta(fem, trace)
