"""Acceptance quality (N4) contract resolution, FEM trace packaging, and floor seam.

Pure planner-shipped contract read paths, gate contract resolution, FEM merge
helpers, and :func:`apply_acceptance_quality_n4_floor_seam` orchestration for the
N4 runtime quality floor. Terminal pipeline calls the owner entrypoint directly.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from game.acceptance_quality import (
    build_acceptance_quality_contract,
    validate_and_repair_acceptance_quality,
)
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.final_emission_meta import ensure_final_emission_meta_dict
from game.final_emission_sealed_fallback import (
    finalize_n4_sealed_replace_fem_route_meta,
    select_acceptance_quality_n4_sealed_fallback_line,
)
from game.final_emission_text_formatting import _normalize_text


def _narrative_plan_bundle_present_on_gm_output(gm_output: Mapping[str, Any] | None) -> bool:
    """True when the emission bundle carries a shipped ``prompt_context.narrative_plan`` dict."""
    if not isinstance(gm_output, Mapping):
        return False
    pc = gm_output.get("prompt_context")
    if not isinstance(pc, Mapping):
        return False
    return isinstance(pc.get("narrative_plan"), Mapping)


def _shipped_acceptance_quality_overrides_from_gm_output(
    gm_output: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    """Planner-shipped N4 policy overrides only (same seam as ``narrative_mode_contract``).

    The gate does **not** invent contract fields: unknown ``trailer_phrase_patterns_version`` values
    stay on the merged contract so :mod:`game.acceptance_quality` can surface unresolved-version
    evidence without this layer silently coercing to v1.
    """
    if not isinstance(gm_output, Mapping):
        return None
    pc = gm_output.get("prompt_context")
    if not isinstance(pc, Mapping):
        return None
    plan = pc.get("narrative_plan")
    if not isinstance(plan, Mapping):
        return None
    raw = plan.get("acceptance_quality_contract")
    return dict(raw) if isinstance(raw, dict) else None


def _resolve_acceptance_quality_contract_for_gate(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Resolve N4 contract: default-on **only** when the shipped narrative-plan bundle is present.

    Call sites that invoke the gate without ``prompt_context.narrative_plan`` (legacy harnesses,
    narrow unit tests) keep N4 **disabled** so the floor does not fire without the same planner
    seam that carries ``narrative_mode_contract`` and optional ``acceptance_quality_contract`` overrides.
    """
    if not _narrative_plan_bundle_present_on_gm_output(gm_output):
        return build_acceptance_quality_contract(enabled=False)
    ov = _shipped_acceptance_quality_overrides_from_gm_output(gm_output)
    return build_acceptance_quality_contract(overrides=ov)


def _merge_acceptance_quality_n4_results_into_gate_fem(
    out: Dict[str, Any],
    aq_bundle: Mapping[str, Any],
) -> None:
    """FEM merge for N4: canonical nested trace plus stable flat keys (telemetry / read-side)."""
    if not isinstance(out, dict) or not isinstance(aq_bundle, Mapping):
        return
    fem = ensure_final_emission_meta_dict(out)
    trace = aq_bundle.get("acceptance_quality_emission_trace")
    if isinstance(trace, Mapping):
        fem["acceptance_quality_trace"] = dict(trace)
        for k in (
            "acceptance_quality_version",
            "acceptance_quality_checked",
            "acceptance_quality_passed",
            "acceptance_quality_reason_codes",
            "acceptance_quality_repair_applied",
        ):
            if k in trace:
                fem[k] = trace[k]
        ev = trace.get("acceptance_quality_evidence")
        if isinstance(ev, Mapping):
            fem["acceptance_quality_evidence"] = dict(ev)
    val = aq_bundle.get("validation")
    if isinstance(val, Mapping):
        fem["acceptance_quality_failure_reasons"] = list(val.get("failure_reasons") or [])
    rep = aq_bundle.get("repair")
    if isinstance(rep, Mapping):
        fem["acceptance_quality_repair_modes"] = list(rep.get("repair_modes") or [])


def _patch_n4_floor_text_fingerprint(out: Dict[str, Any], *, pre_gate_text: str) -> None:
    fem = ensure_final_emission_meta_dict(out)
    gtxt = _normalize_text(out.get("player_facing_text"))
    fem["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
    fem["post_gate_mutation_detected"] = pre_gate_text != gtxt


def apply_acceptance_quality_n4_floor_seam(
    out: Dict[str, Any],
    *,
    gm_output_for_contract: Mapping[str, Any] | None,
    candidate_text: str,
    strict_social_path: bool,
    eff_resolution: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    res_kind: str,
    response_type_required: str,
    pre_gate_text: str,
) -> None:
    """Objective N4 — **single** orchestration call into :mod:`game.acceptance_quality`.

    Why one seam: ``validate_and_repair_acceptance_quality`` owns validate → bounded subtractive repair
    → fresh re-validate → compact trace assembly. The gate must not duplicate that loop or hand-seal
    pass/fail from stale dicts.

    N4 is a **runtime quality floor** (anti-collapse / thin grounding / trailer-style terminals), not
    evaluator scoring and not a second Narrative Authenticity layer—NA still owns echo/follow-up
    heuristics earlier in the stack.

    Repairs stay **subtractive** (whitespace normalize; optional terminal sentence drop only for the
    narrow trailer/abstract codes). The gate does not broaden repair authority or semantic-rewrite a
    failed candidate into “better” prose.

    Unresolved ``trailer_phrase_patterns_version`` values are **observed** via contract + validator
    evidence only; this integration does not coerce unknown versions to v1.

    N4 enforcement defaults **off** unless ``prompt_context.narrative_plan`` is present on the
    emission dict (same bundle seam as shipped ``narrative_mode_contract``); optional
    ``acceptance_quality_contract`` inside that plan toggles or overrides policy.

    If the floor still fails after the shipped repair budget, the gate swaps to an existing
    deterministic sealed fallback line (strict-social emergency or scene-integrity global tuple)—same
    class of terminal handling as other hard replace paths, not silent acceptance of the failing
    candidate.
    """
    contract = _resolve_acceptance_quality_contract_for_gate(gm_output_for_contract)
    aq1 = validate_and_repair_acceptance_quality(str(candidate_text or ""), contract)
    text1 = str(aq1.get("text") or candidate_text)
    val1 = aq1.get("validation") if isinstance(aq1.get("validation"), Mapping) else {}
    passed = bool(val1.get("passed"))
    _merge_acceptance_quality_n4_results_into_gate_fem(out, aq1)
    if passed:
        assert_final_emission_mutation_allowed(
            "normalize_whitespace",
            source="gate._apply_acceptance_quality_n4_floor_seam.pass",
        )
        out["player_facing_text"] = _normalize_text(text1)
        _patch_n4_floor_text_fingerprint(out, pre_gate_text=pre_gate_text)
        return

    fb_line = select_acceptance_quality_n4_sealed_fallback_line(
        strict_social_path=strict_social_path,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=str(scene_id or "").strip(),
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=res_kind,
        response_type_required=response_type_required,
    )
    fem = ensure_final_emission_meta_dict(out)
    fem["acceptance_quality_gate_replaced_candidate"] = True
    fem["acceptance_quality_rejected_reason_codes"] = list(val1.get("reason_codes") or [])
    assert_final_emission_mutation_allowed(
        "hard_replace_illegal_output_with_sealed_fallback",
        source="gate._apply_acceptance_quality_n4_floor_seam",
    )
    aq2 = validate_and_repair_acceptance_quality(str(fb_line or ""), contract)
    text2 = str(aq2.get("text") or fb_line)
    _merge_acceptance_quality_n4_results_into_gate_fem(out, aq2)
    assert_final_emission_mutation_allowed(
        "normalize_whitespace",
        source="gate._apply_acceptance_quality_n4_floor_seam.replace_normalized",
    )
    out["player_facing_text"] = _normalize_text(text2)
    out["tags"] = list(out.get("tags") or []) + [
        "final_emission_gate_replaced",
        "final_emission_gate:acceptance_quality",
    ]
    finalize_n4_sealed_replace_fem_route_meta(fem, strict_social_path=strict_social_path)
    _patch_n4_floor_text_fingerprint(out, pre_gate_text=pre_gate_text)
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    codes = ",".join(str(c) for c in (val1.get("reason_codes") or [])[:8])
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"final_emission_gate:acceptance_quality_replaced:{codes}"
