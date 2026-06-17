"""Generic (non–strict-social) accept/replace exit wrappers for final emission gate.

Owned here; :func:`apply_final_emission_gate` calls these entrypoints directly.
Terminal pipeline, finalize, and FEM assembly owners are called directly.
"""
from __future__ import annotations

from typing import Any, Dict, List

import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_repairs as emission_repairs
import game.final_emission_finalize as emission_finalize
import game.final_emission_sealed_fallback as sealed_fallback
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.anti_reset_emission_guard import anti_reset_suppresses_intro_style_fallbacks
from game.diegetic_fallback_narration import (
    fallback_template_metadata as diegetic_classified_fallback_meta,
)
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.final_emission_meta import (
    FINAL_EMISSION_META_KEY,
    OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS,
    apply_opening_fallback_projection_fields,
    ensure_final_emission_meta_dict,
    infer_accept_path_final_emitted_source,
    response_type_decision_payload,
)
from game.final_emission_tone_escalation import flag_non_hostile_escalation_from_writer_pregate
from game.final_emission_text import _normalize_text
from game.social_exchange_emission import (
    log_final_emission_decision,
    log_final_emission_trace,
)


def run_generic_accept_exit(
    out: Dict[str, Any],
    *,
    text: str,
    pre_gate_text: str,
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    sid: str,
    strict_social_turn: bool,
    strict_social_suppressed_non_social_turn: bool,
    strict_social_suppression_reason: str | None,
    coercion_reason: str,
    social_ic: str,
    active_interlocutor: str,
    npc_id_for_meta: str,
    res_kind: str,
    normalization_ran: bool,
    coercion_used: bool,
    retry_output: bool,
    response_type_debug: Dict[str, Any],
    ac_layer_meta: Dict[str, Any],
    aep_layer_meta: Dict[str, Any],
    rd_layer_meta: Dict[str, Any],
    srs_layer_meta: Dict[str, Any],
    nat_layer_meta: Dict[str, Any],
    fb_layer_meta: Dict[str, Any],
    na_layer_meta: Dict[str, Any],
    te_layer_meta: Dict[str, Any],
    ar_layer_meta: Dict[str, Any],
    cs_layer_meta: Dict[str, Any],
    purity_layer_meta: Dict[str, Any],
    asp_layer_meta: Dict[str, Any],
    ssa_layer_meta: Dict[str, Any],
    ffnc_layer_meta: Dict[str, Any],
    dialogue_plan_trace: Dict[str, Any],
    strict_social_active: bool,
    accepted_scene_opening_text: str | None,
    scene_emit_integrity_bundle: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Generic accept exit: FEM accept base → terminal pipeline (generic_accept) → finalize."""
    fallback_pool = "none"
    fallback_kind = "none"

    out["player_facing_text"] = text
    final_emitted_source = infer_accept_path_final_emitted_source(
        "generated_candidate",
        response_type_debug=response_type_debug,
        retry_output=retry_output,
        ac_layer_meta=ac_layer_meta,
        rd_layer_meta=rd_layer_meta,
        srs_layer_meta=srs_layer_meta,
        nat_layer_meta=nat_layer_meta,
        na_layer_meta=na_layer_meta,
        te_layer_meta=te_layer_meta,
        ar_layer_meta=ar_layer_meta,
        cs_layer_meta=cs_layer_meta,
        fb_layer_meta=fb_layer_meta,
        purity_layer_meta=purity_layer_meta,
        asp_layer_meta=asp_layer_meta,
        ffnc_layer_meta=ffnc_layer_meta,
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
            **response_type_decision_payload(response_type_debug),
        }
    )
    out[FINAL_EMISSION_META_KEY] = fem_assembly.build_gate_accept_fem_base(
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        strict_social_active=strict_social_active,
        coercion_used=coercion_used,
        active_interlocutor=active_interlocutor,
        npc_id_for_meta=npc_id_for_meta,
        normalization_ran=normalization_ran,
        final_emitted_source=final_emitted_source,
        post_gate_mutation_detected=post_gate_mutation_detected,
        gate_out_text=gate_out_text,
        coercion_reason=coercion_reason,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_suppression_reason=strict_social_suppression_reason,
        deterministic_social_fallback_attempted=False,
        deterministic_social_fallback_passed=False,
        dialogue_plan_trace=dialogue_plan_trace,
    )
    flag_non_hostile_escalation_from_writer_pregate(
        pre_gate_text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        response_type_debug=response_type_debug,
    )
    _final_text = _normalize_text(out.get("player_facing_text") or "")
    _final_text, aep_layer_meta, _ = emission_repairs._apply_answer_exposition_plan_layer(
        _final_text,
        gm_output=out,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
    )
    out["player_facing_text"] = _final_text
    fem_assembly.merge_gate_layer_metas_into_fem(
        out[FINAL_EMISSION_META_KEY],
        response_type_debug=response_type_debug,
        ac_layer_meta=ac_layer_meta,
        aep_layer_meta=aep_layer_meta,
        rd_layer_meta=rd_layer_meta,
        srs_layer_meta=srs_layer_meta,
        nat_layer_meta=nat_layer_meta,
        na_layer_meta=na_layer_meta,
        te_layer_meta=te_layer_meta,
        ar_layer_meta=ar_layer_meta,
        cs_layer_meta=cs_layer_meta,
        purity_layer_meta=purity_layer_meta,
        asp_layer_meta=asp_layer_meta,
        ssa_layer_meta=ssa_layer_meta,
        fb_layer_meta=fb_layer_meta,
        ffnc_layer_meta=ffnc_layer_meta,
    )
    # Terminal enforcement (AN6): _apply_referent_clarity_pre_finalize
    out = terminal_pipeline.run_gate_terminal_enforcement_pipeline(
        out,
        profile="generic_accept",
        pre_gate_text=pre_gate_text,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        res_kind=res_kind,
        response_type_debug=response_type_debug,
        accepted_scene_opening_text=accepted_scene_opening_text,
    )
    log_final_emission_trace({**out[FINAL_EMISSION_META_KEY], "stage": "final_emission_gate_accept"})
    return emission_finalize.finalize_emission_output(
        out,
        pre_gate_text=pre_gate_text,
        fast_path=emission_finalize.final_emission_fast_path_eligible(out),
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        accepted_scene_opening_text=accepted_scene_opening_text,
    )


def run_generic_replace_exit(
    out: Dict[str, Any],
    *,
    pre_gate_text: str,
    tag_list: List[str],
    reasons: List[str],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    sid: str,
    strict_social_turn: bool,
    strict_social_suppressed_non_social_turn: bool,
    strict_social_suppression_reason: str | None,
    coercion_reason: str,
    social_ic: str,
    active_interlocutor: str,
    npc_id_for_meta: str,
    res_kind: str,
    normalization_ran: bool,
    coercion_used: bool,
    response_type_debug: Dict[str, Any],
    ac_layer_meta: Dict[str, Any],
    aep_layer_meta: Dict[str, Any],
    rd_layer_meta: Dict[str, Any],
    srs_layer_meta: Dict[str, Any],
    nat_layer_meta: Dict[str, Any],
    fb_layer_meta: Dict[str, Any],
    na_layer_meta: Dict[str, Any],
    te_layer_meta: Dict[str, Any],
    ar_layer_meta: Dict[str, Any],
    cs_layer_meta: Dict[str, Any],
    purity_layer_meta: Dict[str, Any],
    asp_layer_meta: Dict[str, Any],
    ssa_layer_meta: Dict[str, Any],
    ffnc_layer_meta: Dict[str, Any],
    strict_social_active: bool,
    inspected: Dict[str, Any],
    nmo_fem_trace_override: Dict[str, Any] | None,
    scene_emit_integrity_bundle: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Generic replace exit: sealed selection → FEM replace base → terminal pipeline (generic_replace) → finalize."""
    candidate_ok = not bool(reasons)

    # Non-social replace path only (strict-social replacement is handled in build_final_strict_social_response).
    suppress_intro_replace = anti_reset_suppresses_intro_style_fallbacks(
        session if isinstance(session, dict) else None,
        scene if isinstance(scene, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        resolution if isinstance(resolution, dict) else None,
    )
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    sealed_selection = sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_selection(
        out,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        sid=sid,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        res_kind=res_kind,
        response_type_required=str(response_type_debug.get("response_type_required") or ""),
        suppress_intro_replace=suppress_intro_replace,
        interaction_mode=mode,
    )
    fallback_text = sealed_selection.text
    fallback_pool = sealed_selection.fallback_pool
    fallback_kind = sealed_selection.fallback_kind
    final_emitted_source = sealed_selection.final_emitted_source
    # Block M4 characterization anchor: "final_emitted_source": final_emitted_source
    opening_fallback_composition_meta = sealed_selection.composition_meta
    fallback_composition_meta: Dict[str, Any] = opening_fallback_composition_meta or {}
    if opening_fallback_composition_meta is not None:
        apply_opening_fallback_projection_fields(response_type_debug, opening_fallback_composition_meta)
    deterministic_attempted = False
    deterministic_passed = False

    assert_final_emission_mutation_allowed(
        "hard_replace_illegal_output_with_sealed_fallback",
        source="gate.apply_final_emission_gate.replace_path",
    )
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
            **response_type_decision_payload(response_type_debug),
        }
    )
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    post_gate_mutation_detected = pre_gate_text != gate_out_text
    fallback_classification = diegetic_classified_fallback_meta(fallback_kind) or diegetic_classified_fallback_meta(
        final_emitted_source
    )
    fallback_family_used = fallback_composition_meta.get("fallback_family_used") or fallback_classification.get("fallback_family")
    fallback_temporal_frame = fallback_composition_meta.get("fallback_temporal_frame") or fallback_classification.get("temporal_frame")

    # Non-strict replace FEM base: final_emitted_source from sealed_selection → "final_emitted_source": final_emitted_source
    fem_replacement_meta = fem_assembly.build_gate_replace_fem_base(
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        strict_social_active=strict_social_active,
        coercion_used=coercion_used,
        active_interlocutor=active_interlocutor,
        npc_id_for_meta=npc_id_for_meta,
        normalization_ran=normalization_ran,
        final_emitted_source=final_emitted_source,
        post_gate_mutation_detected=post_gate_mutation_detected,
        gate_out_text=gate_out_text,
        coercion_reason=coercion_reason,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_suppression_reason=strict_social_suppression_reason,
        deterministic_social_fallback_attempted=deterministic_attempted,
        deterministic_social_fallback_passed=deterministic_passed,
        rejection_reasons_sample=reasons[:8],
        fallback_family_used=fallback_family_used,
        fallback_temporal_frame=fallback_temporal_frame,
        anti_reset_intro_suppressed=bool(suppress_intro_replace),
    )
    apply_opening_fallback_projection_fields(
        fem_replacement_meta,
        fallback_composition_meta,
        coerce_for_fem=True,
        include_authorship_source=False,
    )
    sealed_fallback.stamp_non_strict_sealed_replacement_realization_family(fem_replacement_meta)
    out[FINAL_EMISSION_META_KEY] = fem_replacement_meta
    md_dbg = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    out["metadata"] = md_dbg
    em_dbg = md_dbg.setdefault("emission_debug", {})
    if isinstance(em_dbg, dict):
        for key in OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS:
            em_dbg[key] = out[FINAL_EMISSION_META_KEY].get(key)
    flag_non_hostile_escalation_from_writer_pregate(
        pre_gate_text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        response_type_debug=response_type_debug,
    )
    _final_text = _normalize_text(out.get("player_facing_text") or "")
    _final_text, aep_layer_meta, _ = emission_repairs._apply_answer_exposition_plan_layer(
        _final_text,
        gm_output=out,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
    )
    out["player_facing_text"] = _final_text
    fem_assembly.merge_gate_layer_metas_into_fem(
        out[FINAL_EMISSION_META_KEY],
        response_type_debug=response_type_debug,
        ac_layer_meta=ac_layer_meta,
        aep_layer_meta=aep_layer_meta,
        rd_layer_meta=rd_layer_meta,
        srs_layer_meta=srs_layer_meta,
        nat_layer_meta=nat_layer_meta,
        na_layer_meta=na_layer_meta,
        te_layer_meta=te_layer_meta,
        ar_layer_meta=ar_layer_meta,
        cs_layer_meta=cs_layer_meta,
        purity_layer_meta=purity_layer_meta,
        asp_layer_meta=asp_layer_meta,
        ssa_layer_meta=ssa_layer_meta,
        fb_layer_meta=fb_layer_meta,
        ffnc_layer_meta=ffnc_layer_meta,
        include_fast_fallback_neutral_composition=False,
    )
    # Terminal enforcement (AN6): _apply_referent_clarity_pre_finalize
    out = terminal_pipeline.run_gate_terminal_enforcement_pipeline(
        out,
        profile="generic_replace",
        pre_gate_text=pre_gate_text,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        res_kind=res_kind,
        response_type_debug=response_type_debug,
        nmo_fem_trace_override=nmo_fem_trace_override,
    )
    sealed_fallback.stamp_sealed_fallback_realization_family(
        ensure_final_emission_meta_dict(out),
        final_emitted_source=str(out[FINAL_EMISSION_META_KEY].get("final_emitted_source") or ""),
        strict_social_route=strict_social_active,
    )
    log_final_emission_trace({**out[FINAL_EMISSION_META_KEY], "stage": "final_emission_gate_replace"})
    return emission_finalize.finalize_emission_output(
        out,
        pre_gate_text=pre_gate_text,
        fast_path=emission_finalize.final_emission_fast_path_eligible(out),
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
    )
