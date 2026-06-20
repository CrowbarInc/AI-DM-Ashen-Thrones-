"""Strict-social composition trunk for final emission gate.

Owned here; :func:`apply_final_emission_gate` calls this entrypoint directly.
Terminal pipeline, finalize, and FEM assembly owners are called directly.
"""
from __future__ import annotations

from typing import Any, Dict, List

import game.final_emission_finalize as emission_finalize
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.dialogue_social_plan import (
    enforce_dialogue_plan_invariant_on_strict_social,
    is_bare_speech_attribution_shell_line,
    strip_dialogue_from_text,
    strict_social_line_matches_terminal_emission_pool,
)
import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_repairs as emission_repairs
import game.final_emission_response_type as response_type
from game.final_emission_meta import (
    PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR,
    stamp_producer_repair_kind,
)
from game.final_emission_sealed_fallback import stamp_sealed_fallback_realization_family
from game.final_emission_fast_fallback_composition import apply_fast_fallback_neutral_composition_layer
from game.final_emission_answer_shape_primacy import (
    apply_answer_shape_primacy_layer,
    merge_answer_shape_primacy_into_emission_debug as _merge_answer_shape_primacy_into_emission_debug,
)
from game.final_emission_scene_state_anchor import (
    _merge_scene_state_anchor_into_emission_debug,
    apply_scene_state_anchor_layer,
)
from game.final_emission_context_separation import (
    apply_context_separation_layer,
    merge_context_separation_into_emission_debug as _merge_context_separation_into_emission_debug,
)
from game.final_emission_player_facing_narration_purity import (
    apply_player_facing_narration_purity_layer,
    merge_player_facing_narration_purity_into_emission_debug as _merge_player_facing_narration_purity_into_emission_debug,
)
from game.final_emission_anti_railroading import (
    apply_anti_railroading_layer,
    merge_anti_railroading_into_emission_debug as _merge_anti_railroading_into_emission_debug,
)
from game.final_emission_tone_escalation import (
    apply_tone_escalation_layer,
    flag_non_hostile_escalation_from_writer_pregate,
    merge_tone_escalation_into_emission_debug as _merge_tone_escalation_into_emission_debug,
)
from game.final_emission_narrative_authority import (
    apply_narrative_authority_layer,
    merge_narrative_authority_into_emission_debug as _merge_narrative_authority_into_emission_debug,
)
from game.final_emission_meta import (
    FINAL_EMISSION_META_KEY,
    infer_accept_path_final_emitted_source,
    response_type_decision_payload,
)
from game.final_emission_scene_emit_integrity import (
    _compute_scene_emit_integrity_assessment,
)
from game.final_emission_text import _normalize_text, _normalize_text_preserve_paragraphs
from game.fallback_provenance_debug import realign_fallback_provenance_selector_to_current_text
from game.speaker_contract_enforcement import (
    _sync_eff_social_to_resolution,
    enforce_emitted_speaker_with_contract,
)
from game.social_exchange_emission import (
    build_final_strict_social_response,
    log_final_emission_decision,
    log_final_emission_trace,
    minimal_social_emergency_fallback_line,
    strict_social_deterministic_fallback_family_token,
)
from game.stage_diff_telemetry import record_stage_snapshot


def run_strict_social_composition_trunk(
    out: Dict[str, Any],
    *,
    pre_gate_text: str,
    tag_list: List[str],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
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
    text: str,
    response_type_debug: Dict[str, Any],
    ac_layer_meta: Dict[str, Any],
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
    dialogue_plan_blocked: bool,
    strict_social_active: bool,
    coercion_used: bool,
    retry_output: bool,
    scene_emit_integrity_bundle: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Strict-social trunk: dialogue plan → build → layers → speaker → terminal pipeline → finalize."""
    normalization_ran = True
    # Objective C1-D: check the writer-produced candidate before strict-social normalization rewrites.
    # This must fail closed (no speaker inference / no speaker rewriting).
    pre_gate_text, dsp_trace0 = enforce_dialogue_plan_invariant_on_strict_social(
        pre_gate_text,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        strict_social_active=True,
        response_type_required=None,
    )
    dialogue_plan_trace = dict(dsp_trace0 or {})
    dialogue_plan_blocked = bool(
        dialogue_plan_trace.get("dialogue_plan_required")
        and (dialogue_plan_trace.get("dialogue_plan_valid") is False)
    )
    text, details = build_final_strict_social_response(
        pre_gate_text,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        tags=tag_list,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )
    if (
        dialogue_plan_blocked
        and isinstance(eff_resolution, dict)
        and isinstance(details, dict)
        and str(details.get("final_emitted_source") or "") == "normalized_social_candidate"
        and strict_social_line_matches_terminal_emission_pool(text, eff_resolution)
    ):
        # Telemetry: missing dialogue plan still produced a sealed terminal-class line; attribute as emergency-class.
        details = {**details, "final_emitted_source": "minimal_social_emergency_fallback"}
    text, response_type_debug = response_type.enforce_response_type_contract(
        text,
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        strict_social_turn=True,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )
    response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug(out, response_type_debug)
    if response_type_debug.get("response_type_candidate_ok") is False and isinstance(eff_resolution, dict):
        text = minimal_social_emergency_fallback_line(eff_resolution)
        text, response_type_debug = response_type.enforce_response_type_contract(
            text,
            gm_output=out,
            resolution=eff_resolution,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            strict_social_turn=True,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            active_interlocutor=active_interlocutor,
        )
        response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug(out, response_type_debug)
        details = {
            **details,
            "used_internal_fallback": True,
            "fallback_kind": "response_type_contract_social_emergency",
            "fallback_pool": "response_type_contract",
            "final_emitted_source": "minimal_social_emergency_fallback",
            "realization_fallback_family": strict_social_deterministic_fallback_family_token(),
            "rejection_reasons": list(details.get("rejection_reasons") or [])
            + list(response_type_debug.get("response_type_rejection_reasons") or []),
        }
    scene_emit_integrity_bundle = _compute_scene_emit_integrity_assessment(
        authoritative_resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        res_kind=res_kind,
        response_type_required=str(response_type_debug.get("response_type_required") or ""),
    )
    text, ac_layer_meta, _ = emission_repairs._apply_answer_completeness_layer(
        text,
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        strict_social_details=details,
        response_type_debug=response_type_debug,
        strict_social_path=True,
    )
    text, aep_layer_meta, _ = emission_repairs._apply_answer_exposition_plan_layer(
        text,
        gm_output=out,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
    )
    text, rd_layer_meta, _ = emission_repairs._apply_response_delta_layer(
        text,
        gm_output=out,
        strict_social_details=details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=True,
    )
    text, srs_layer_meta, _ = emission_repairs._apply_social_response_structure_layer(
        text,
        gm_output=out,
        strict_social_details=details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=True,
    )
    text, nat_layer_meta, _ = emission_repairs._apply_narrative_authenticity_layer(
        text,
        gm_output=out,
        strict_social_details=details,
        response_type_debug=response_type_debug,
        strict_social_path=True,
    )
    out["player_facing_text"] = text
    text, te_layer_meta, _ = apply_tone_escalation_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
    )
    if te_layer_meta.get("tone_escalation_violation_before_repair"):
        response_type_debug["non_hostile_escalation_blocked"] = True
    out["player_facing_text"] = text
    text, na_layer_meta, _ = apply_narrative_authority_layer(
        text,
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        strict_social_details=details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
    )
    out["player_facing_text"] = text

    text, _speaker_contract_payload = enforce_emitted_speaker_with_contract(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=sid,
    )
    _sync_eff_social_to_resolution(
        eff_resolution if isinstance(eff_resolution, dict) else None,
        resolution if isinstance(resolution, dict) else None,
    )
    out["player_facing_text"] = text
    text, ar_layer_meta, _ = apply_anti_railroading_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=details,
    )
    out["player_facing_text"] = text
    text, cs_layer_meta, _ = apply_context_separation_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=details,
    )
    out["player_facing_text"] = text
    text, purity_layer_meta, _ = apply_player_facing_narration_purity_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        response_type_debug=response_type_debug,
    )
    out["player_facing_text"] = text
    text, asp_layer_meta, _ = apply_answer_shape_primacy_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=details,
    )
    out["player_facing_text"] = text
    text, ssa_layer_meta = apply_scene_state_anchor_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        strict_social_details=details,
        response_type_debug=response_type_debug,
    )
    out["player_facing_text"] = text
    text, ffnc_layer_meta = apply_fast_fallback_neutral_composition_layer(
        _normalize_text_preserve_paragraphs(text),
        gm_output=out,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        strict_social_active=strict_social_active,
    )
    # If dialogue-plan enforcement blocked earlier, ensure no later repair re-introduced dialogue.
    if dialogue_plan_blocked and not dialogue_plan_trace.get("dialogue_plan_subtractive_strip_deferred"):
        stripped = strip_dialogue_from_text(text)
        if not str(stripped or "").strip():
            # Subtractive strip removed all diegetic text (e.g. quote-only fragment from a prior hint
            # split). Strict-social turns must not collapse to ambient stall prose.
            if isinstance(eff_resolution, dict):
                text = minimal_social_emergency_fallback_line(eff_resolution)
                if isinstance(details, dict):
                    details = {
                        **details,
                        "final_emitted_source": "minimal_social_emergency_fallback",
                        "fallback_kind": "emergency_social_minimal",
                    }
            else:
                text = "The moment passes without an answer."
        elif is_bare_speech_attribution_shell_line(stripped):
            # Do not replace a route-legal quoted NPC reply with an empty attribution shell.
            pass
        elif (
            isinstance(eff_resolution, dict)
            and '"' in str(text or "")
            and '"' not in str(stripped or "")
            and strict_social_line_matches_terminal_emission_pool(str(text or ""), eff_resolution)
        ):
            # Late subtractive strip would erase the only quoted payload from a deterministic
            # strict-social terminal/minimal line matched to this resolution.
            pass
        else:
            text = stripped
    out["player_facing_text"] = text

    record_stage_snapshot(out, "final_emission_gate_after_strict_social_composition")
    if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
        realign_fallback_provenance_selector_to_current_text(
            out,
            text=str(text or ""),
            reason="fast_fallback_neutral_composition",
        )
    _merge_scene_state_anchor_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=ssa_layer_meta,
    )
    _merge_tone_escalation_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=te_layer_meta,
        gm_output=out,
    )
    _merge_narrative_authority_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=na_layer_meta,
        gm_output=out,
    )
    _merge_anti_railroading_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=ar_layer_meta,
        gm_output=out,
    )
    _merge_context_separation_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=cs_layer_meta,
    )
    _merge_player_facing_narration_purity_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=purity_layer_meta,
    )
    _merge_answer_shape_primacy_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=asp_layer_meta,
    )
    emission_repairs.merge_conversational_memory_inspection_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
    )
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id_for_meta = str(sp.get("npc_id") or "").strip()
    final_emitted_source = infer_accept_path_final_emitted_source(
        str(details.get("final_emitted_source") or "unknown_post_gate_writer"),
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

    if not details.get("used_internal_fallback"):
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
                "fallback_pool": str(details.get("fallback_pool") or "none"),
                "fallback_kind": str(details.get("fallback_kind") or "none"),
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
            deterministic_social_fallback_attempted=bool(details.get("deterministic_attempted")),
            deterministic_social_fallback_passed=bool(details.get("deterministic_passed")),
            dialogue_plan_trace=dialogue_plan_trace,
            strict_social_accept_details=details,
            speaker_contract_enforcement_reason=_speaker_contract_payload.get("final_reason_code"),
        )
        flag_non_hostile_escalation_from_writer_pregate(
            pre_gate_text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            response_type_debug=response_type_debug,
        )
        # Re-check against the final text: downstream layers may have replaced/mutated the candidate.
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
        # Block M4 characterization: gate_tag="interaction_continuity"
        # Block M4 characterization: gate_tag="narrative_mode_output"
        out = terminal_pipeline.run_gate_terminal_enforcement_pipeline(
            out,
            profile="strict_accept",
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
            speaker_contract_enforcement=_speaker_contract_payload,
        )
        log_final_emission_trace({**out[FINAL_EMISSION_META_KEY], "stage": "final_emission_gate_accept"})
        return emission_finalize.finalize_emission_output(
            out,
            pre_gate_text=pre_gate_text,
            fast_path=emission_finalize.final_emission_fast_path_eligible(out),
            scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        )

    fb_kind = str(details.get("fallback_kind") or "none")
    deterministic_attempted = bool(details.get("deterministic_attempted"))
    deterministic_passed = bool(details.get("deterministic_passed"))
    fallback_pool = str(details.get("fallback_pool") or "social_deterministic")
    candidate_ok = False
    rejection_reasons = details.get("rejection_reasons") if isinstance(details.get("rejection_reasons"), list) else []
    rejection_reasons = list(rejection_reasons) + list(response_type_debug.get("response_type_rejection_reasons") or [])

    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fb_kind}"]
    if final_emitted_source == "minimal_social_emergency_fallback":
        out["tags"] = list(out["tags"]) + ["terminal_strict_social_emission", "strict_social_terminal_safe"]

    if details.get("route_illegal_intercepted"):
        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        preview = str(details.get("intercepted_preview") or "")
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + f"final_emission_gate:route_illegal_writer_intercepted:{preview[:80]}"
        )

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join([str(r) for r in rejection_reasons[:8] if isinstance(r, str)])
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
            "rejection_reasons": [str(r) for r in rejection_reasons[:12] if isinstance(r, str)],
            "fallback_pool": fallback_pool,
            "fallback_kind": fb_kind,
            **response_type_decision_payload(response_type_debug),
        }
    )
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    post_gate_mutation_detected = pre_gate_text != gate_out_text

    out[FINAL_EMISSION_META_KEY] = fem_assembly.build_gate_replace_fem_base(
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
        dialogue_plan_trace=dialogue_plan_trace,
        strict_social_replace=True,
        details=details,
        rejection_reasons=rejection_reasons,
        speaker_contract_enforcement_reason=_speaker_contract_payload.get("final_reason_code"),
    )
    stamp_sealed_fallback_realization_family(
        out[FINAL_EMISSION_META_KEY],
        final_emitted_source=final_emitted_source,
        strict_social_route=strict_social_active,
    )
    stamp_producer_repair_kind(out[FINAL_EMISSION_META_KEY], PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR)
    flag_non_hostile_escalation_from_writer_pregate(
        pre_gate_text,
        gm_output=out,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
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
        profile="strict_replace",
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
        speaker_contract_enforcement=_speaker_contract_payload,
    )
    log_final_emission_trace({**out[FINAL_EMISSION_META_KEY], "stage": "final_emission_gate_replace"})
    return emission_finalize.finalize_emission_output(
        out,
        pre_gate_text=pre_gate_text,
        fast_path=emission_finalize.final_emission_fast_path_eligible(out),
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
    )
