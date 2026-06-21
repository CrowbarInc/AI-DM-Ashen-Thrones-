"""Canonical orchestration owner for final player-facing emission.

**Orchestration home:** :func:`apply_final_emission_gate` sequences sanitizer integration,
strict-social coordination (via :mod:`game.social_exchange_emission`), shipped contracts
(validators + legality metadata), **C4 narrative-mode output** checks vs shipped ``narrative_mode_contract``
(``validate_narrative_mode_output``; ``narrative_mode_output_*`` FEM), **N4 acceptance-quality floor**
via the single :func:`game.acceptance_quality.validate_and_repair_acceptance_quality` seam (merged under
``acceptance_quality_*`` / ``acceptance_quality_trace`` in FEM), logging, and metadata merges. Semantic sentence repairs for tone,
authority, anti-railroading, context separation, scene anchors, answer-shape primacy, and fast-fallback
composition are **disabled at the boundary** (Objective C2 Block C); violations surface as reason codes
without boundary rewrites.

**Legality vs scoring:** pass/fail is driven by deterministic reason codes and **strip-only** or
upstream-prepared repairs where applicable. Numeric ``*_score`` / overlap metrics inside NA or other
traces are **telemetry or diagnostics** for read-side consumers—not evaluator-style quality enforcement
and not a second legality system. N4 ``acceptance_quality_*`` fields mirror the same legality-shaped
predicates (floor / anti-collapse), not offline evaluator axes or holistic “good narrative” scores.

**Not the canonical owner for:** deterministic validators (:mod:`game.final_emission_validators`),
repair/layer wiring (:mod:`game.final_emission_repairs`), shared text/normalization patterns
(:mod:`game.final_emission_text_formatting`), or ``response_type`` contract resolution
(:mod:`game.response_policy_contracts`). Those modules are imported by extracted stack owners; prefer
importing from their real module for new code — BJ-123/124/128 removed historical test-only re-exports
from this orchestration entrypoint. BJ-129 locks the thin boundary against regrowth.

NA telemetry keys merged into ``_final_emission_meta`` are packaged at write time by
:mod:`game.final_emission_meta` (single schema); the gate remains the **canonical orchestration owner**
that calls layer wiring in :mod:`game.final_emission_repairs`.

**Turn packet vs telemetry:** The turn packet (:mod:`game.turn_packet`) is the canonical
accessor/snapshot layer for contracts on a turn. Stage-diff telemetry
(:mod:`game.stage_diff_telemetry`) records bounded stage transitions for observability only.
:func:`game.turn_packet.resolve_turn_packet_for_gate` is the preferred gate-level packet
resolver. ``_gate_turn_packet_cache`` is set at :func:`apply_final_emission_gate` entry
from :func:`game.turn_packet.get_turn_packet` and popped in
:func:`game.final_emission_finalize.finalize_emission_output`; it must never leak into finalized output. Telemetry is
derived from the packet boundary and does not own it. Neither layer owns engine truth or
narration policy.

**Scene-opening deterministic fallback:** opening prose is composed by
:mod:`game.opening_deterministic_fallback`, packaged upstream by
:mod:`game.upstream_response_repairs` as ``upstream_prepared_opening_fallback``, and selected by this
module through the opening fallback adapter. The gate must not re-author opening prose.

**Last-mile player text:** :func:`game.final_emission_finalize.finalize_emission_output` applies packaging-only normalization
(whitespace / route-illegal stock stripping via :func:`game.final_emission_finalize.strip_appended_route_illegal_contamination_sentences`).
It does **not** decompress, repair participial fragments, or micro-smooth for meaning at the boundary
(Objective C2 Block C). :func:`game.output_sanitizer.sanitize_player_facing_output` remains the
pre-gate scaffold/serialization firewall; final emission is not a planner or semantic repair owner.
"""
from __future__ import annotations

from typing import Any, Dict

# Compatibility re-export: parsing ownership lives in game.emitted_speaker_signature.
from game.emitted_speaker_signature import detect_emitted_speaker_signature
from game.speaker_contract_enforcement import (
    SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES,
    get_speaker_selection_contract,
    validate_emitted_speaker_against_contract,
)
from game.final_emission_non_strict_stack import run_non_strict_layer_stack
from game.final_emission_passive_scene_pressure import (
    apply_observe_passive_scene_concrete_beat_upstream_satisfier,
)
from game.final_emission_generic_exit import (
    run_generic_accept_exit,
    run_generic_replace_exit,
)
from game.final_emission_strict_social_stack import (
    run_strict_social_composition_trunk,
)
from game.final_emission_gate_context import initialize_gate_execution_context
from game.interaction_continuity import (
    apply_interaction_continuity_emission_step,
    attach_interaction_continuity_validation,
)
from game.final_emission_gate_preflight_pregate_text import resolve_gate_preflight_pregate_text


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text.

    Orchestrates in-module policy layers with :mod:`game.final_emission_validators`,
    :mod:`game.final_emission_repairs`, and sanitizer/strict-social integration; see module
    docstring for ownership boundaries.
    """
    if not isinstance(gm_output, dict):
        return gm_output
    _ctx = initialize_gate_execution_context(
        gm_output,
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )
    out = _ctx.out
    pre_gate_text = _ctx.pre_gate_text
    tag_list = _ctx.tag_list
    eff_resolution = _ctx.eff_resolution
    sid = _ctx.sid
    strict_social_turn = _ctx.strict_social_turn
    strict_social_suppressed_non_social_turn = _ctx.strict_social_suppressed_non_social_turn
    strict_social_suppression_reason = _ctx.strict_social_suppression_reason
    original_coercion_reason = _ctx.original_coercion_reason
    coercion_reason = _ctx.coercion_reason
    inspected = _ctx.inspected
    active_interlocutor = _ctx.active_interlocutor
    npc_id_for_meta = _ctx.npc_id_for_meta
    res_kind = _ctx.res_kind
    social_ic = _ctx.social_ic
    reasons = _ctx.reasons
    scene_emit_integrity_bundle = _ctx.scene_emit_integrity_bundle
    normalization_ran = _ctx.normalization_ran
    text = _ctx.text
    response_type_debug = _ctx.response_type_debug
    ac_layer_meta = _ctx.ac_layer_meta
    rd_layer_meta = _ctx.rd_layer_meta
    srs_layer_meta = _ctx.srs_layer_meta
    nat_layer_meta = _ctx.nat_layer_meta
    fb_layer_meta = _ctx.fb_layer_meta
    na_layer_meta = _ctx.na_layer_meta
    te_layer_meta = _ctx.te_layer_meta
    ar_layer_meta = _ctx.ar_layer_meta
    cs_layer_meta = _ctx.cs_layer_meta
    purity_layer_meta = _ctx.purity_layer_meta
    asp_layer_meta = _ctx.asp_layer_meta
    ssa_layer_meta = _ctx.ssa_layer_meta
    ffnc_layer_meta = _ctx.ffnc_layer_meta
    dialogue_plan_trace = _ctx.dialogue_plan_trace
    nmo_fem_trace_override = _ctx.nmo_fem_trace_override
    dialogue_plan_blocked = _ctx.dialogue_plan_blocked
    accepted_scene_opening_text = _ctx.accepted_scene_opening_text
    strict_social_active = _ctx.strict_social_active
    coercion_used = _ctx.coercion_used
    retry_output = _ctx.retry_output

    if strict_social_turn:
        return run_strict_social_composition_trunk(
            out,
            pre_gate_text=pre_gate_text,
            tag_list=tag_list,
            resolution=resolution if isinstance(resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            sid=sid,
            strict_social_turn=strict_social_turn,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            strict_social_suppression_reason=strict_social_suppression_reason,
            coercion_reason=coercion_reason,
            social_ic=social_ic,
            active_interlocutor=active_interlocutor,
            npc_id_for_meta=npc_id_for_meta,
            res_kind=res_kind,
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
            dialogue_plan_blocked=dialogue_plan_blocked,
            strict_social_active=strict_social_active,
            coercion_used=coercion_used,
            retry_output=retry_output,
            scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        )

    # Non-strict layer stack (AN4): response_type.enforce_response_type_contract → policy layers → IC → fallback → NMO pre-assess
    out = apply_observe_passive_scene_concrete_beat_upstream_satisfier(
        out,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=sid,
        res_kind=res_kind,
        strict_social_active=strict_social_active,
    )
    text = resolve_gate_preflight_pregate_text(out).pre_gate_text
    _nss = run_non_strict_layer_stack(
        out,
        text=text,
        reasons=reasons,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        res_kind=res_kind,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_active=strict_social_active,
        active_interlocutor=active_interlocutor,
        response_type_debug=response_type_debug,
        accepted_scene_opening_text=accepted_scene_opening_text,
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        nmo_fem_trace_override=nmo_fem_trace_override,
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
    )
    out = _nss.out
    text = _nss.text
    reasons = _nss.reasons
    response_type_debug = _nss.response_type_debug
    accepted_scene_opening_text = _nss.accepted_scene_opening_text
    scene_emit_integrity_bundle = _nss.scene_emit_integrity_bundle
    nmo_fem_trace_override = _nss.nmo_fem_trace_override
    ac_layer_meta = _nss.ac_layer_meta
    aep_layer_meta = _nss.aep_layer_meta
    rd_layer_meta = _nss.rd_layer_meta
    srs_layer_meta = _nss.srs_layer_meta
    nat_layer_meta = _nss.nat_layer_meta
    fb_layer_meta = _nss.fb_layer_meta
    na_layer_meta = _nss.na_layer_meta
    te_layer_meta = _nss.te_layer_meta
    ar_layer_meta = _nss.ar_layer_meta
    cs_layer_meta = _nss.cs_layer_meta
    purity_layer_meta = _nss.purity_layer_meta
    asp_layer_meta = _nss.asp_layer_meta
    ssa_layer_meta = _nss.ssa_layer_meta
    ffnc_layer_meta = _nss.ffnc_layer_meta

    if not reasons:
        return run_generic_accept_exit(
            out,
            text=text,
            pre_gate_text=pre_gate_text,
            resolution=resolution if isinstance(resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session,
            scene=scene,
            world=world,
            sid=sid,
            strict_social_turn=strict_social_turn,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            strict_social_suppression_reason=strict_social_suppression_reason,
            coercion_reason=coercion_reason,
            social_ic=social_ic,
            active_interlocutor=active_interlocutor,
            npc_id_for_meta=npc_id_for_meta,
            res_kind=res_kind,
            normalization_ran=normalization_ran,
            coercion_used=coercion_used,
            retry_output=retry_output,
            response_type_debug=response_type_debug,
            ac_layer_meta=ac_layer_meta,
            aep_layer_meta=aep_layer_meta,
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
            strict_social_active=strict_social_active,
            accepted_scene_opening_text=accepted_scene_opening_text,
            scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        )

    return run_generic_replace_exit(
        out,
        pre_gate_text=pre_gate_text,
        tag_list=tag_list,
        reasons=reasons,
        resolution=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session,
        scene=scene,
        world=world,
        sid=sid,
        strict_social_turn=strict_social_turn,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_suppression_reason=strict_social_suppression_reason,
        coercion_reason=coercion_reason,
        social_ic=social_ic,
        active_interlocutor=active_interlocutor,
        npc_id_for_meta=npc_id_for_meta,
        res_kind=res_kind,
        normalization_ran=normalization_ran,
        coercion_used=coercion_used,
        response_type_debug=response_type_debug,
        ac_layer_meta=ac_layer_meta,
        aep_layer_meta=aep_layer_meta,
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
        strict_social_active=strict_social_active,
        inspected=inspected,
        nmo_fem_trace_override=nmo_fem_trace_override,
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
    )
