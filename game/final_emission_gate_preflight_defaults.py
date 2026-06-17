"""Default layer-meta initialization for gate entry/preflight (Cycle BN3).

Pure setup data for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact default dict values and call order; no routing or terminal enforcement.
"""
from __future__ import annotations

from typing import Any, Dict, NamedTuple

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
from game.final_emission_tone_escalation import default_tone_escalation_meta


class GatePreflightLayerMetaDefaults(NamedTuple):
    """Layer-meta defaults produced during gate preflight before stack routing."""

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


def initialize_gate_preflight_layer_meta_defaults(
    out: Dict[str, Any],
) -> GatePreflightLayerMetaDefaults:
    """Initialize response-type debug and empty/default layer-meta dicts for gate preflight."""
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
    return GatePreflightLayerMetaDefaults(
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
    )
