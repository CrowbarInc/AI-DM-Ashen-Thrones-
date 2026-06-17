"""Generic (non–strict-social) pre-fork layer stack for final emission gate.

Owned here; :func:`apply_final_emission_gate` calls this entrypoint directly.
Layer entrypoints that tests patch on ``feg`` are resolved at call time through the gate module.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, NamedTuple

from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.fallback_provenance_debug import realign_fallback_provenance_selector_to_current_text
from game.final_emission_finalize import patch_scene_opening_candidate_emission_debug
from game.final_emission_repairs import (
    _apply_answer_completeness_layer,
    _apply_answer_exposition_plan_layer,
    _apply_fallback_behavior_layer,
    _apply_narrative_authenticity_layer,
    _apply_response_delta_layer,
    _apply_social_response_structure_layer,
    merge_conversational_memory_inspection_into_emission_debug,
    merge_fallback_behavior_into_emission_debug,
)
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
    merge_tone_escalation_into_emission_debug as _merge_tone_escalation_into_emission_debug,
)
from game.final_emission_narrative_authority import (
    apply_narrative_authority_layer,
    merge_narrative_authority_into_emission_debug as _merge_narrative_authority_into_emission_debug,
)
from game.interaction_continuity import apply_interaction_continuity_emission_step
import game.final_emission_opening_fallback as opening_fallback
import game.final_emission_response_type as response_type
from game.final_emission_passive_scene_pressure import (
    _passive_scene_pressure_due_for_fallback,
)
from game.final_emission_narrative_mode_output import (
    _narrative_mode_output_legality_assessment,
)
from game.final_emission_scene_emit_integrity import (
    _compute_scene_emit_integrity_assessment,
)
from game.final_emission_text import _normalize_text


def _gate_module():
    import game.final_emission_gate as feg

    return feg


_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"“”'‘’]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


class NonStrictLayerStackResult(NamedTuple):
    """Outputs from the generic (non–strict-social) pre-fork layer stack (Cycle AN4)."""

    out: Dict[str, Any]
    text: str
    reasons: List[str]
    response_type_debug: Dict[str, Any]
    accepted_scene_opening_text: str | None
    scene_emit_integrity_bundle: Dict[str, Any] | None
    nmo_fem_trace_override: Dict[str, Any] | None
    ac_layer_meta: Dict[str, Any]
    aep_layer_meta: Dict[str, Any]
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


def run_non_strict_layer_stack(
    out: Dict[str, Any],
    *,
    text: str,
    reasons: List[str],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    res_kind: str,
    strict_social_suppressed_non_social_turn: bool,
    strict_social_active: bool,
    active_interlocutor: str,
    response_type_debug: Dict[str, Any],
    accepted_scene_opening_text: str | None,
    scene_emit_integrity_bundle: Dict[str, Any] | None,
    nmo_fem_trace_override: Dict[str, Any] | None,
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
) -> NonStrictLayerStackResult:
    """Generic trunk layer ordering before accept/replace fork; mutates ``out`` and ``reasons`` in place."""
    feg = _gate_module()
    sid = str(scene_id or "").strip()
    auth_res = resolution if isinstance(resolution, dict) else None
    eff_res = eff_resolution if isinstance(eff_resolution, dict) else None
    sess = session if isinstance(session, dict) else None

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    if _passive_scene_pressure_due_for_fallback(
        session=sess,
        scene=scene,
        scene_id=sid,
    ) and not _reply_already_has_concrete_interaction(text):
        reasons.append("passive_scene_pressure_missing_concrete_beat")

    text, response_type_debug = response_type.enforce_response_type_contract(
        text,
        gm_output=out,
        resolution=auth_res,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )
    response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug(out, response_type_debug)
    if opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate(response_type_debug):
        accepted_scene_opening_text = _normalize_text(text)
        out["player_facing_text"] = accepted_scene_opening_text
        response_type_debug["scene_opening_accepted_candidate_promoted"] = True
        patch_scene_opening_candidate_emission_debug(
            out,
            accepted_scene_opening_text=accepted_scene_opening_text,
        )
    scene_emit_integrity_bundle = _compute_scene_emit_integrity_assessment(
        authoritative_resolution=auth_res,
        session=sess,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        res_kind=res_kind,
        response_type_required=str(response_type_debug.get("response_type_required") or ""),
    )
    if response_type_debug.get("response_type_candidate_ok") is False:
        reasons.extend(
            [str(r) for r in (response_type_debug.get("response_type_rejection_reasons") or []) if isinstance(r, str)]
        )

    text, ac_layer_meta, ac_reasons = _apply_answer_completeness_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        strict_social_path=False,
    )
    reasons.extend(ac_reasons)

    text, aep_layer_meta, aep_reasons = _apply_answer_exposition_plan_layer(
        text,
        gm_output=out,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
    )
    reasons.extend(aep_reasons)

    text, rd_layer_meta, rd_reasons = _apply_response_delta_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=False,
    )
    reasons.extend(rd_reasons)

    text, srs_layer_meta, srs_reasons = _apply_social_response_structure_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=False,
    )
    reasons.extend(srs_reasons)

    text, nat_layer_meta, nat_reasons = _apply_narrative_authenticity_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        strict_social_path=False,
    )
    reasons.extend(nat_reasons)

    text, te_layer_meta, te_reasons = apply_tone_escalation_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        session=sess,
        scene_id=sid,
        response_type_debug=response_type_debug,
    )
    if te_layer_meta.get("tone_escalation_violation_before_repair"):
        response_type_debug["non_hostile_escalation_blocked"] = True
    if (
        response_type_debug.get("response_type_required") == "scene_opening"
        and response_type_debug.get("opening_fallback_skipped") is True
        and response_type_debug.get("response_type_repair_used") is False
    ):
        te_reasons = [
            str(r)
            for r in te_reasons
            if str(r) != "tone_escalation_unsatisfied_at_boundary_no_rewrite"
        ]
    reasons.extend(te_reasons)

    text, na_layer_meta, na_reasons = apply_narrative_authority_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        session=sess,
        scene_id=sid,
    )
    reasons.extend(na_reasons)

    text, ar_layer_meta, ar_reasons = apply_anti_railroading_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        session=sess,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(ar_reasons)

    text, cs_layer_meta, cs_reasons = apply_context_separation_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        session=sess,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(cs_reasons)

    text, purity_layer_meta, purity_extra = apply_player_facing_narration_purity_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        response_type_debug=response_type_debug,
    )
    reasons.extend(purity_extra)

    text, asp_layer_meta, asp_extra = apply_answer_shape_primacy_layer(
        text,
        gm_output=out,
        resolution=auth_res,
        session=sess,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(asp_extra)

    text, ssa_layer_meta = apply_scene_state_anchor_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
    )
    out["player_facing_text"] = _normalize_text(text)
    text, ffnc_layer_meta = apply_fast_fallback_neutral_composition_layer(
        _normalize_text(text),
        gm_output=out,
        session=sess,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        strict_social_active=strict_social_active,
    )
    out["player_facing_text"] = _normalize_text(text)
    if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
        realign_fallback_provenance_selector_to_current_text(
            out,
            text=str(out.get("player_facing_text") or ""),
            reason="fast_fallback_neutral_composition",
        )
    _merge_scene_state_anchor_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=ssa_layer_meta,
    )
    _merge_tone_escalation_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=te_layer_meta,
        gm_output=out,
    )
    _merge_narrative_authority_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=na_layer_meta,
        gm_output=out,
    )
    _merge_anti_railroading_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=ar_layer_meta,
        gm_output=out,
    )
    _merge_context_separation_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=cs_layer_meta,
    )
    _merge_player_facing_narration_purity_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=purity_layer_meta,
    )
    _merge_answer_shape_primacy_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=asp_layer_meta,
    )
    merge_conversational_memory_inspection_into_emission_debug(
        out,
        auth_res,
        eff_res,
    )

    ic_text, ic_extra_reasons, _ic_strict_fb = apply_interaction_continuity_emission_step(
        out,
        text=_normalize_text(text),
        resolution_for_contracts=auth_res,
        eff_resolution=eff_res,
        session=sess,
        validate_only=True,
        strict_social_path=False,
    )
    assert_final_emission_mutation_allowed(
        "interaction_continuity_validation_attach",
        source="gate.apply_final_emission_gate.pre_candidate.ic_validate_only",
    )
    reasons.extend(ic_extra_reasons)
    text = ic_text
    out["player_facing_text"] = _normalize_text(text)
    text, fb_layer_meta, fb_extra = _apply_fallback_behavior_layer(
        _normalize_text(text),
        gm_output=out,
        resolution=auth_res,
        strict_social_path=False,
        session=sess,
        scene_id=sid,
    )
    reasons.extend(fb_extra)
    out["player_facing_text"] = _normalize_text(text)
    merge_fallback_behavior_into_emission_debug(
        out,
        auth_res,
        eff_res,
        gate_meta=fb_layer_meta,
    )

    _nmo_pre = _narrative_mode_output_legality_assessment(
        str(out.get("player_facing_text") or ""),
        out,
        resolution_for_nmo=auth_res,
        strict_social_details_flag=None,
    )
    reasons.extend(_nmo_pre["non_strict_gate_reasons"])
    if _nmo_pre["non_strict_gate_reasons"]:
        nmo_fem_trace_override = dict(_nmo_pre["trace"])

    return NonStrictLayerStackResult(
        out=out,
        text=text,
        reasons=reasons,
        response_type_debug=response_type_debug,
        accepted_scene_opening_text=accepted_scene_opening_text,
        scene_emit_integrity_bundle=scene_emit_integrity_bundle,
        nmo_fem_trace_override=nmo_fem_trace_override,
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
    )
