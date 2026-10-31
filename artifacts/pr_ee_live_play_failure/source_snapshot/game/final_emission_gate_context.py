"""Gate entry/preflight context initialization for final emission orchestration.

Owned here; :func:`apply_final_emission_gate` calls :func:`initialize_gate_execution_context` directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, NamedTuple

from game.final_emission_gate_preflight_branch_flags import resolve_gate_preflight_branch_flags
from game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults
from game.final_emission_gate_preflight_interaction import resolve_gate_preflight_interaction_metadata
from game.final_emission_gate_preflight_pregate_text import resolve_gate_preflight_pregate_text
from game.final_emission_gate_preflight_strict_social import resolve_gate_preflight_strict_social_routing
from game.final_emission_gate_preflight_telemetry import apply_gate_preflight_telemetry_and_containment
from game.final_emission_gate_preflight_turn_packet import initialize_gate_preflight_turn_packet
from game.final_emission_gate_preflight_upstream import apply_gate_preflight_upstream_attach


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
    out = initialize_gate_preflight_turn_packet(
        out,
        session=session if isinstance(session, dict) else None,
    )
    out = apply_gate_preflight_upstream_attach(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
    )
    pregate_text = resolve_gate_preflight_pregate_text(out)
    pre_gate_text = pregate_text.pre_gate_text
    tag_list = pregate_text.tag_list

    strict_social_routing = resolve_gate_preflight_strict_social_routing(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
        pre_gate_text=pre_gate_text,
        tag_list=tag_list,
    )
    eff_resolution = strict_social_routing.eff_resolution
    strict_social_turn = strict_social_routing.strict_social_turn
    strict_social_suppressed_non_social_turn = strict_social_routing.strict_social_suppressed_non_social_turn
    strict_social_suppression_reason = strict_social_routing.strict_social_suppression_reason
    original_coercion_reason = strict_social_routing.original_coercion_reason
    coercion_reason = strict_social_routing.coercion_reason
    pre_gate_text = strict_social_routing.pre_gate_text
    sid = str(scene_id or "").strip()

    interaction_metadata = resolve_gate_preflight_interaction_metadata(session, eff_resolution)
    inspected = interaction_metadata.inspected
    active_interlocutor = interaction_metadata.active_interlocutor
    npc_id_for_meta = interaction_metadata.npc_id_for_meta
    res_kind = interaction_metadata.res_kind
    social_ic = interaction_metadata.social_ic

    reasons: List[str] = []
    scene_emit_integrity_bundle: Dict[str, Any] | None = None
    normalization_ran = False
    telemetry_result = apply_gate_preflight_telemetry_and_containment(out, pre_gate_text=pre_gate_text)
    pre_gate_text = telemetry_result.pre_gate_text
    text = telemetry_result.text
    layer_defaults = initialize_gate_preflight_layer_meta_defaults(out)
    response_type_debug = layer_defaults.response_type_debug
    ac_layer_meta = layer_defaults.ac_layer_meta
    rd_layer_meta = layer_defaults.rd_layer_meta
    srs_layer_meta = layer_defaults.srs_layer_meta
    nat_layer_meta = layer_defaults.nat_layer_meta
    fb_layer_meta = layer_defaults.fb_layer_meta
    na_layer_meta = layer_defaults.na_layer_meta
    te_layer_meta = layer_defaults.te_layer_meta
    ar_layer_meta = layer_defaults.ar_layer_meta
    cs_layer_meta = layer_defaults.cs_layer_meta
    purity_layer_meta = layer_defaults.purity_layer_meta
    asp_layer_meta = layer_defaults.asp_layer_meta
    ssa_layer_meta = layer_defaults.ssa_layer_meta
    ffnc_layer_meta = layer_defaults.ffnc_layer_meta
    dialogue_plan_trace = layer_defaults.dialogue_plan_trace
    nmo_fem_trace_override = layer_defaults.nmo_fem_trace_override
    dialogue_plan_blocked = layer_defaults.dialogue_plan_blocked
    accepted_scene_opening_text = layer_defaults.accepted_scene_opening_text

    branch_flags = resolve_gate_preflight_branch_flags(
        strict_social_turn=strict_social_turn,
        original_coercion_reason=original_coercion_reason,
        tag_list=tag_list,
    )
    strict_social_active = branch_flags.strict_social_active
    coercion_used = branch_flags.coercion_used
    retry_output = branch_flags.retry_output

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
