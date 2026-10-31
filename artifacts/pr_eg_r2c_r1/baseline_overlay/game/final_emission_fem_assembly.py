"""FEM base assembly for final emission gate accept/replace paths.

Callers: :mod:`game.final_emission_generic_exit` and
:mod:`game.final_emission_strict_social_stack` invoke these helpers directly.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict

from game.final_emission_answer_shape_primacy import (
    merge_answer_shape_primacy_into_emission_debug,
    merge_answer_shape_primacy_meta,
)
from game.final_emission_anti_railroading import (
    merge_anti_railroading_into_emission_debug,
    merge_anti_railroading_meta,
)
from game.final_emission_context_separation import (
    merge_context_separation_into_emission_debug,
    merge_context_separation_meta,
)
from game.final_emission_meta import (
    merge_narrative_authenticity_into_final_emission_meta,
    merge_response_type_meta,
)
from game.final_emission_narrative_authority import (
    merge_narrative_authority_into_emission_debug,
    merge_narrative_authority_meta,
)
from game.final_emission_player_facing_narration_purity import (
    merge_player_facing_narration_purity_into_emission_debug,
    merge_player_facing_narration_purity_meta,
)
from game.final_emission_repairs import (
    _merge_answer_completeness_meta,
    _merge_answer_exposition_plan_meta,
    _merge_fallback_behavior_meta,
    _merge_response_delta_meta,
    _merge_social_response_structure_meta,
    merge_conversational_memory_inspection_into_emission_debug,
)
from game.final_emission_scene_state_anchor import (
    _merge_scene_state_anchor_into_emission_debug,
    _merge_scene_state_anchor_meta,
)
from game.final_emission_tone_escalation import (
    merge_tone_escalation_into_emission_debug,
    merge_tone_escalation_meta,
)
from game.social_exchange_projection import project_strict_social_replace_realization_family


def _reply_kind(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    sp = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(sp.get("reply_kind") or "").strip().lower()


def build_gate_accept_fem_base(
    *,
    eff_resolution: Dict[str, Any] | None,
    strict_social_active: bool,
    coercion_used: bool,
    active_interlocutor: str,
    npc_id_for_meta: str,
    normalization_ran: bool,
    final_emitted_source: str,
    post_gate_mutation_detected: bool,
    gate_out_text: str,
    coercion_reason: str,
    strict_social_suppressed_non_social_turn: bool,
    strict_social_suppression_reason: str | None,
    deterministic_social_fallback_attempted: bool,
    deterministic_social_fallback_passed: bool,
    dialogue_plan_trace: Dict[str, Any] | None = None,
    strict_social_accept_details: Mapping[str, Any] | None = None,
    speaker_contract_enforcement_reason: Any = None,
) -> Dict[str, Any]:
    """Base FEM payload for accept_candidate paths (Cycle AN3)."""
    fem: Dict[str, Any] = {
        "final_route": "accept_candidate",
        "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
        "strict_social_active": strict_social_active,
        "coercion_used": coercion_used,
        "active_interlocutor_id": active_interlocutor or None,
        "npc_id": npc_id_for_meta or None,
        "normalization_ran": normalization_ran,
        "candidate_validation_passed": True,
    }
    fem.update(dict(dialogue_plan_trace or {}))
    fem["deterministic_social_fallback_attempted"] = deterministic_social_fallback_attempted
    fem["deterministic_social_fallback_passed"] = deterministic_social_fallback_passed
    fem["final_emitted_source"] = final_emitted_source
    fem["post_gate_mutation_detected"] = post_gate_mutation_detected
    fem["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    fem["coercion_reason"] = coercion_reason
    if strict_social_accept_details is not None:
        fem["candidate_quality_degraded"] = bool(strict_social_accept_details.get("candidate_quality_degraded"))
        fem["resolved_answer_preferred"] = bool(strict_social_accept_details.get("resolved_answer_preferred"))
        fem["resolved_answer_source"] = strict_social_accept_details.get("resolved_answer_source")
        fem["resolved_answer_preference_reason"] = strict_social_accept_details.get(
            "resolved_answer_preference_reason"
        )
    fem["strict_social_suppressed_non_social_turn"] = strict_social_suppressed_non_social_turn
    fem["strict_social_suppression_reason"] = strict_social_suppression_reason
    if strict_social_accept_details is not None:
        fem["social_emission_integrity_replaced"] = bool(
            strict_social_accept_details.get("social_emission_integrity_replaced")
        )
        fem["social_emission_integrity_reasons"] = strict_social_accept_details.get("social_emission_integrity_reasons")
        fem["social_emission_integrity_fallback_kind"] = strict_social_accept_details.get(
            "social_emission_integrity_fallback_kind"
        )
        fem["speaker_contract_enforcement_reason"] = speaker_contract_enforcement_reason
    return fem


def build_gate_replace_fem_base(
    *,
    eff_resolution: Dict[str, Any] | None,
    strict_social_active: bool,
    coercion_used: bool,
    active_interlocutor: str,
    npc_id_for_meta: str,
    normalization_ran: bool,
    final_emitted_source: str,
    post_gate_mutation_detected: bool,
    gate_out_text: str,
    coercion_reason: str,
    strict_social_suppressed_non_social_turn: bool,
    strict_social_suppression_reason: str | None,
    deterministic_social_fallback_attempted: bool,
    deterministic_social_fallback_passed: bool,
    dialogue_plan_trace: Dict[str, Any] | None = None,
    strict_social_replace: bool = False,
    details: Mapping[str, Any] | None = None,
    rejection_reasons: Sequence[Any] | None = None,
    speaker_contract_enforcement_reason: Any = None,
    rejection_reasons_sample: Sequence[Any] | None = None,
    fallback_family_used: Any = None,
    fallback_temporal_frame: Any = None,
    anti_reset_intro_suppressed: bool = False,
) -> Dict[str, Any]:
    """Base FEM payload for replaced paths before path-specific projection/stamps (Cycle AN3)."""
    fem: Dict[str, Any] = {
        "final_route": "replaced",
        "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
        "strict_social_active": strict_social_active,
        "coercion_used": coercion_used,
        "active_interlocutor_id": active_interlocutor or None,
        "npc_id": npc_id_for_meta or None,
        "normalization_ran": normalization_ran,
        "candidate_validation_passed": False,
    }
    fem.update(dict(dialogue_plan_trace or {}))
    fem["deterministic_social_fallback_attempted"] = deterministic_social_fallback_attempted
    fem["deterministic_social_fallback_passed"] = deterministic_social_fallback_passed
    fem["final_emitted_source"] = final_emitted_source
    if strict_social_replace:
        details_map = details if isinstance(details, Mapping) else {}
        fem["realization_fallback_family"] = project_strict_social_replace_realization_family(
            details_map.get("realization_fallback_family")
            if isinstance(details_map.get("realization_fallback_family"), str)
            else None
        )
    fem["post_gate_mutation_detected"] = post_gate_mutation_detected
    fem["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    fem["coercion_reason"] = coercion_reason
    if strict_social_replace:
        details_map = details if isinstance(details, Mapping) else {}
        fem["rejection_reasons_sample"] = [
            str(r) for r in (rejection_reasons or [])[:8] if isinstance(r, str)
        ]
        fem["candidate_quality_degraded"] = bool(details_map.get("candidate_quality_degraded"))
        fem["resolved_answer_preferred"] = bool(details_map.get("resolved_answer_preferred"))
        fem["resolved_answer_source"] = details_map.get("resolved_answer_source")
        fem["resolved_answer_preference_reason"] = details_map.get("resolved_answer_preference_reason")
        fem["strict_social_suppressed_non_social_turn"] = strict_social_suppressed_non_social_turn
        fem["strict_social_suppression_reason"] = strict_social_suppression_reason
        fem["speaker_contract_enforcement_reason"] = speaker_contract_enforcement_reason
    else:
        fem["fallback_family_used"] = fallback_family_used
        fem["fallback_temporal_frame"] = fallback_temporal_frame
        fem["rejection_reasons_sample"] = list(rejection_reasons_sample or [])
        fem["strict_social_suppressed_non_social_turn"] = strict_social_suppressed_non_social_turn
        fem["strict_social_suppression_reason"] = strict_social_suppression_reason
        fem["anti_reset_intro_suppressed"] = bool(anti_reset_intro_suppressed)
    return fem


def merge_pre_terminal_layer_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    ssa_layer_meta: Dict[str, Any],
    te_layer_meta: Dict[str, Any],
    na_layer_meta: Dict[str, Any],
    ar_layer_meta: Dict[str, Any],
    cs_layer_meta: Dict[str, Any],
    purity_layer_meta: Dict[str, Any],
    asp_layer_meta: Dict[str, Any],
) -> None:
    """Merge post-composition layer debug into ``metadata.emission_debug`` before FEM/terminal fork.

    Shared by strict-social and non-strict stacks; order matches the pre-BU2-A inline sequence.
    """
    _merge_scene_state_anchor_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=ssa_layer_meta,
    )
    merge_tone_escalation_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=te_layer_meta,
        gm_output=out,
    )
    merge_narrative_authority_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=na_layer_meta,
        gm_output=out,
    )
    merge_anti_railroading_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=ar_layer_meta,
        gm_output=out,
    )
    merge_context_separation_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=cs_layer_meta,
    )
    merge_player_facing_narration_purity_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=purity_layer_meta,
    )
    merge_answer_shape_primacy_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=asp_layer_meta,
    )
    merge_conversational_memory_inspection_into_emission_debug(
        out,
        resolution,
        eff_resolution,
    )


def _merge_fast_fallback_neutral_composition_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "fast_fallback_neutral_composition_checked": bool(
                dbg.get("fast_fallback_neutral_composition_checked")
            ),
            "fast_fallback_neutral_composition_applicable": bool(
                dbg.get("fast_fallback_neutral_composition_applicable")
            ),
            "fast_fallback_neutral_composition_malformed_detected": bool(
                dbg.get("fast_fallback_neutral_composition_malformed_detected")
            ),
            "fast_fallback_neutral_composition_failure_reasons": list(
                dbg.get("fast_fallback_neutral_composition_failure_reasons") or []
            ),
            "fast_fallback_neutral_composition_repaired": bool(
                dbg.get("fast_fallback_neutral_composition_repaired")
            ),
            "fast_fallback_neutral_composition_repair_mode": dbg.get(
                "fast_fallback_neutral_composition_repair_mode"
            ),
        }
    )


def merge_gate_layer_metas_into_fem(
    fem: Dict[str, Any],
    *,
    response_type_debug: Dict[str, Any],
    ac_layer_meta: Dict[str, Any],
    aep_layer_meta: Dict[str, Any],
    rd_layer_meta: Dict[str, Any],
    srs_layer_meta: Dict[str, Any],
    nat_layer_meta: Dict[str, Any],
    na_layer_meta: Dict[str, Any],
    te_layer_meta: Dict[str, Any],
    ar_layer_meta: Dict[str, Any],
    cs_layer_meta: Dict[str, Any],
    purity_layer_meta: Dict[str, Any],
    asp_layer_meta: Dict[str, Any],
    ssa_layer_meta: Dict[str, Any],
    fb_layer_meta: Dict[str, Any],
    ffnc_layer_meta: Dict[str, Any],
    include_fast_fallback_neutral_composition: bool = True,
) -> None:
    """Merge gate layer debug into ``fem`` in the fixed post-AEP-second-pass order (Cycle AN2)."""
    merge_response_type_meta(fem, response_type_debug)
    _merge_answer_completeness_meta(fem, ac_layer_meta)
    _merge_answer_exposition_plan_meta(fem, aep_layer_meta)
    _merge_response_delta_meta(fem, rd_layer_meta)
    _merge_social_response_structure_meta(fem, srs_layer_meta)
    merge_narrative_authenticity_into_final_emission_meta(fem, nat_layer_meta)
    merge_narrative_authority_meta(fem, na_layer_meta)
    merge_tone_escalation_meta(fem, te_layer_meta)
    merge_anti_railroading_meta(fem, ar_layer_meta)
    merge_context_separation_meta(fem, cs_layer_meta)
    merge_player_facing_narration_purity_meta(fem, purity_layer_meta)
    merge_answer_shape_primacy_meta(fem, asp_layer_meta)
    _merge_scene_state_anchor_meta(fem, ssa_layer_meta)
    _merge_fallback_behavior_meta(fem, fb_layer_meta)
    if include_fast_fallback_neutral_composition:
        _merge_fast_fallback_neutral_composition_meta(fem, ffnc_layer_meta)
