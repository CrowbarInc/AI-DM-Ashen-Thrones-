"""Gate entry/preflight context initialization for final emission orchestration.

Owned here; :func:`apply_final_emission_gate` calls :func:`initialize_gate_execution_context` directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, NamedTuple

from game.fallback_provenance_debug import (
    apply_upstream_fallback_pregate_containment,
    record_final_emission_gate_entry,
)
from game.final_emission_anti_railroading import default_anti_railroading_meta
from game.final_emission_answer_shape_primacy import default_answer_shape_primacy_meta
from game.final_emission_context_separation import default_context_separation_meta
from game.final_emission_fast_fallback_composition import default_fast_fallback_neutral_composition_meta
from game.final_emission_meta import (
    default_narrative_authenticity_layer_meta,
    default_response_type_debug,
)
from game.final_emission_narrative_authority import default_narrative_authority_meta
from game.final_emission_player_facing_narration_purity import default_player_facing_narration_purity_meta
from game.final_emission_repairs import (
    _default_fallback_behavior_meta,
    _default_response_delta_meta,
    _default_social_response_structure_meta,
)
from game.final_emission_response_type import (
    _merge_opening_upstream_prepare_attach_observability_into_response_type_debug,
)
from game.final_emission_text import _normalize_text
from game.final_emission_tone_escalation import default_tone_escalation_meta
from game.interaction_context import inspect as inspect_interaction_context
from game.output_sanitizer import sanitize_player_facing_output
from game.response_policy_contracts import materialize_response_policy_bundle
from game.social_exchange_emission import (
    effective_strict_social_resolution_for_emission,
    merged_player_prompt_for_gate,
    strict_social_emission_will_apply,
    strict_social_suppress_non_native_coercion_for_narration_beat,
)
from game.stage_diff_telemetry import (
    diff_turn_stage,
    record_stage_snapshot,
    record_stage_transition,
    snapshot_turn_stage,
)
from game.turn_packet import get_turn_packet
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_EMISSION_KEY,
    maybe_attach_upstream_prepared_opening_fallback_payload,
    merge_upstream_prepared_emission_into_gm_output,
)


class GateExecutionContext(NamedTuple):
    """Gate entry/preflight state produced before strict-social or generic orchestration branches."""

    out: Dict[str, Any]
    pre_gate_text: str
    tag_list: List[str]
    eff_resolution: Dict[str, Any] | None
    sid: str
    strict_social_turn: bool
    strict_social_suppressed_non_social_turn: bool
    strict_social_suppression_reason: str | None
    original_coercion_reason: str
    coercion_reason: str
    inspected: Dict[str, Any]
    active_interlocutor: str
    npc_id_for_meta: str
    res_kind: str
    social_ic: str
    reasons: List[str]
    scene_emit_integrity_bundle: Dict[str, Any] | None
    normalization_ran: bool
    text: str
    response_type_debug: Dict[str, Any]
    ac_layer_meta: Dict[str, Any]
    rd_layer_meta: Dict[str, Any]
    srs_layer_meta: Dict[str, Any]
    nat_layer_meta: Dict[str, Any]
    fb_layer_meta: Dict[str, Any]
    na_layer_meta: Dict[str, Any]
    te_layer_meta: Dict[str, Any]
    ar_layer_meta: Dict[str, Any]
    cs_layer_meta: Dict[str, Any]
    purity_layer_meta: Dict[str, Any]
    asp_layer_meta: Dict[str, Any]
    ssa_layer_meta: Dict[str, Any]
    ffnc_layer_meta: Dict[str, Any]
    dialogue_plan_trace: Dict[str, Any]
    nmo_fem_trace_override: Dict[str, Any] | None
    dialogue_plan_blocked: bool
    accepted_scene_opening_text: str | None
    strict_social_active: bool
    coercion_used: bool
    retry_output: bool


def initialize_gate_execution_context(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> GateExecutionContext:
    """Setup-only preflight for :func:`apply_final_emission_gate` (Cycle AN1).

    Preserves exact call ordering and in-place ``out`` mutations from the former inline block.
    Does not perform accept/replace routing or terminal enforcement.
    """
    out = dict(gm_output)
    out = materialize_response_policy_bundle(out, session if isinstance(session, dict) else None)
    out["_gate_turn_packet_cache"] = get_turn_packet(
        out, out.get("response_policy"), out.get("prompt_context")
    )
    merge_upstream_prepared_emission_into_gm_output(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
    )
    maybe_attach_upstream_prepared_opening_fallback_payload(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
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
                        "sanitizer_boundary_mode": "strip_only",
                        "upstream_prepared_emission": out.get(UPSTREAM_PREPARED_EMISSION_KEY)
                        if isinstance(out.get(UPSTREAM_PREPARED_EMISSION_KEY), dict)
                        else None,
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
    scene_emit_integrity_bundle: Dict[str, Any] | None = None
    normalization_ran = False
    record_final_emission_gate_entry(out)
    record_stage_snapshot(out, "final_emission_gate_entry")
    snap_before_pregate = snapshot_turn_stage(out, "gate_before_pregate_containment")
    if apply_upstream_fallback_pregate_containment(out):
        pre_gate_text = _normalize_text(out.get("player_facing_text"))
        snap_after_pregate = snapshot_turn_stage(out, "gate_after_pregate_containment")
        _pregate_diff = diff_turn_stage(snap_before_pregate, snap_after_pregate)
        if _pregate_diff.get("text_fingerprint_changed") or _pregate_diff.get("route_changed"):
            record_stage_snapshot(out, "final_emission_gate_after_pregate_containment")
            record_stage_transition(
                out,
                "gate_before_pregate_containment",
                "final_emission_gate_after_pregate_containment",
                snap_before_pregate,
                snap_after_pregate,
            )
    text = _normalize_text(out.get("player_facing_text"))
    response_type_debug = default_response_type_debug(None, None)
    _merge_opening_upstream_prepare_attach_observability_into_response_type_debug(out, response_type_debug)
    ac_layer_meta: Dict[str, Any] = {}
    rd_layer_meta: Dict[str, Any] = _default_response_delta_meta()
    srs_layer_meta: Dict[str, Any] = _default_social_response_structure_meta()
    nat_layer_meta: Dict[str, Any] = default_narrative_authenticity_layer_meta()
    fb_layer_meta: Dict[str, Any] = _default_fallback_behavior_meta()
    na_layer_meta: Dict[str, Any] = default_narrative_authority_meta()
    te_layer_meta: Dict[str, Any] = default_tone_escalation_meta()
    ar_layer_meta: Dict[str, Any] = default_anti_railroading_meta()
    cs_layer_meta: Dict[str, Any] = default_context_separation_meta()
    purity_layer_meta: Dict[str, Any] = default_player_facing_narration_purity_meta()
    asp_layer_meta: Dict[str, Any] = default_answer_shape_primacy_meta()
    ssa_layer_meta: Dict[str, Any] = {}
    ffnc_layer_meta: Dict[str, Any] = default_fast_fallback_neutral_composition_meta()
    dialogue_plan_trace: Dict[str, Any] = {}
    nmo_fem_trace_override: Dict[str, Any] | None = None
    dialogue_plan_blocked = False
    accepted_scene_opening_text: str | None = None

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

    return GateExecutionContext(
        out=out,
        pre_gate_text=pre_gate_text,
        tag_list=tag_list,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        sid=sid,
        strict_social_turn=strict_social_turn,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_suppression_reason=strict_social_suppression_reason,
        original_coercion_reason=original_coercion_reason,
        coercion_reason=coercion_reason,
        inspected=inspected,
        active_interlocutor=active_interlocutor,
        npc_id_for_meta=npc_id_for_meta,
        res_kind=res_kind,
        social_ic=social_ic,
        reasons=reasons,
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        normalization_ran=normalization_ran,
        text=text,
        response_type_debug=response_type_debug,
        ac_layer_meta=ac_layer_meta,
        rd_layer_meta=rd_layer_meta,
        srs_layer_meta=srs_layer_meta,
        nat_layer_meta=nat_layer_meta,
        fb_layer_meta=fb_layer_meta,
        na_layer_meta=na_layer_meta,
        te_layer_meta=te_layer_meta,
        ar_layer_meta=ar_layer_meta,
        cs_layer_meta=cs_layer_meta,
        purity_layer_meta=purity_layer_meta,
        asp_layer_meta=asp_layer_meta,
        ssa_layer_meta=ssa_layer_meta,
        ffnc_layer_meta=ffnc_layer_meta,
        dialogue_plan_trace=dialogue_plan_trace,
        nmo_fem_trace_override=nmo_fem_trace_override,
        dialogue_plan_blocked=dialogue_plan_blocked,
        accepted_scene_opening_text=accepted_scene_opening_text,
        strict_social_active=strict_social_active,
        coercion_used=coercion_used,
        retry_output=retry_output,
    )
