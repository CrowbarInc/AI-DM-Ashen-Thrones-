"""Late gate terminal enforcement pipeline (visibility through IC attach).

Shared accept/replace exit tail owned here. Exit stacks call
:func:`run_gate_terminal_enforcement_pipeline` directly. Visibility enforcement is
owned by :mod:`game.final_emission_visibility_fallback` and called directly here.
N4 floor seam is owned by :mod:`game.final_emission_acceptance_quality` and called directly here.
Layer entrypoints resolve through their extracted owner modules (Cycle BJ); BN2 removed
the stale lazy ``feg`` namespace — no live monkeypatch seams remain in this file.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Literal

from game.final_emission_acceptance_quality import apply_acceptance_quality_n4_floor_seam
from game.interaction_continuity import (
    apply_interaction_continuity_emission_step,
    attach_interaction_continuity_validation,
)
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.final_emission_meta import (
    FINAL_EMISSION_META_KEY,
    PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR,
    ensure_final_emission_meta_dict,
    stamp_producer_repair_kind,
)
from game.final_emission_narration_constraint_debug import merge_narration_constraint_debug_into_outputs
import game.final_emission_opening_fallback as opening_fallback
from game.final_emission_sealed_fallback import stamp_sealed_fallback_realization_family
from game.final_emission_narrative_mode_output import (
    _merge_narrative_mode_output_trace_into_gate_fem,
    _narrative_mode_output_legality_assessment,
)
from game.final_emission_referential_clarity import (
    _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id,
)
from game.final_emission_repairs import (
    _apply_fallback_behavior_layer,
    _apply_referent_clarity_emission_layer,
    _merge_fallback_behavior_meta,
    _merge_referent_clarity_meta,
    merge_fallback_behavior_into_emission_debug,
)
from game.final_emission_text import _normalize_text
from game.final_emission_visibility_fallback import apply_visibility_enforcement
from game.social_exchange_emission import (
    minimal_social_emergency_fallback_line,
    stamp_strict_social_deterministic_fallback_family,
)

GateTerminalEnforcementProfile = Literal[
    "strict_accept",
    "strict_replace",
    "generic_accept",
    "generic_replace",
]


def _patch_fem_text_fingerprint(out: Dict[str, Any], *, pre_gate_text: str) -> None:
    fem = out.get(FINAL_EMISSION_META_KEY)
    if not isinstance(fem, dict):
        return
    gtxt = _normalize_text(out.get("player_facing_text"))
    fem["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
    fem["post_gate_mutation_detected"] = pre_gate_text != gtxt


def apply_strict_social_emergency_fallback_patch(
    out: Dict[str, Any],
    *,
    fallback_text: str,
    pre_gate_text: str,
    gate_tag: str,
    final_route: str | None = None,
    candidate_validation_passed: bool | None = None,
) -> None:
    """Apply already-authored strict-social emergency fallback text and stamp FEM metadata."""
    out["player_facing_text"] = fallback_text
    out["tags"] = list(out.get("tags") or []) + [
        "final_emission_gate_replaced",
        f"final_emission_gate:{gate_tag}",
    ]
    fem = out.get(FINAL_EMISSION_META_KEY)
    if not isinstance(fem, dict):
        return
    if final_route is not None:
        fem["final_route"] = final_route
    if candidate_validation_passed is not None:
        fem["candidate_validation_passed"] = candidate_validation_passed
    fem["final_emitted_source"] = "minimal_social_emergency_fallback"
    stamp_strict_social_deterministic_fallback_family(fem)
    stamp_sealed_fallback_realization_family(
        fem,
        final_emitted_source="minimal_social_emergency_fallback",
        strict_social_route=True,
    )
    stamp_producer_repair_kind(fem, PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR)
    _patch_fem_text_fingerprint(out, pre_gate_text=pre_gate_text)


def _apply_referent_clarity_pre_finalize(out: Dict[str, Any], *, pre_gate_text: str) -> None:
    """Prompt-artifact referent clarity: last safe text pass before narration-constraint meta sealing."""
    if not isinstance(out, dict):
        return
    text_in = str(out.get("player_facing_text") or "")
    text_out, dbg, _ = _apply_referent_clarity_emission_layer(
        text_in,
        gm_output=out,
        allow_semantic_text_repair=False,
    )
    assert_final_emission_mutation_allowed(
        "preserve_candidate_text",
        source="gate._apply_referent_clarity_pre_finalize",
    )
    out["player_facing_text"] = text_out
    fem = ensure_final_emission_meta_dict(out)
    _merge_referent_clarity_meta(fem, dbg)
    gtxt = _normalize_text(text_out)
    if gtxt:
        fem["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
        fem["post_gate_mutation_detected"] = _normalize_text(pre_gate_text) != gtxt


def run_gate_terminal_enforcement_pipeline(
    out: Dict[str, Any],
    *,
    profile: GateTerminalEnforcementProfile,
    pre_gate_text: str,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    res_kind: str,
    response_type_debug: Dict[str, Any],
    speaker_contract_enforcement: Mapping[str, Any] | None = None,
    nmo_fem_trace_override: Dict[str, Any] | None = None,
    accepted_scene_opening_text: str | None = None,
) -> Dict[str, Any]:
    """Late gate enforcement tail shared by accept/replace exit paths (Cycle AN6)."""
    sid = str(scene_id or "").strip()
    eff_res = eff_resolution if isinstance(eff_resolution, dict) else None
    auth_res = resolution if isinstance(resolution, dict) else None
    sess = session if isinstance(session, dict) else None

    grounded_fm_exempt = _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_res,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
    )
    out = apply_visibility_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_res,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        grounded_speaker_first_mention_exemption_entity_id=grounded_fm_exempt,
        emit_integrity_authoritative_resolution=auth_res,
        emit_integrity_res_kind=res_kind,
        emit_integrity_response_type_required=str(response_type_debug.get("response_type_required") or ""),
    )

    strict_social_path = profile in ("strict_accept", "strict_replace")
    nmo_strict_flag = True if strict_social_path else None
    resolution_for_nmo = eff_res if strict_social_path else auth_res
    resolution_for_ic_contracts = eff_res if strict_social_path else auth_res

    if profile == "strict_accept":
        ic_strict_text, _, ic_strict_fb = apply_interaction_continuity_emission_step(
            out,
            text=_normalize_text(out.get("player_facing_text")),
            resolution_for_contracts=eff_res,
            eff_resolution=eff_res,
            session=sess,
            validate_only=True,
            strict_social_path=True,
            strict_fallback_resolution=eff_res,
        )
        assert_final_emission_mutation_allowed(
            "interaction_continuity_validation_attach",
            source="gate.apply_final_emission_gate.strict_social.ic_validate_only",
        )
        out["player_facing_text"] = ic_strict_text
        if ic_strict_fb:
            apply_strict_social_emergency_fallback_patch(
                out,
                fallback_text=ic_strict_text,
                pre_gate_text=pre_gate_text,
                gate_tag="interaction_continuity",
            )

    if strict_social_path:
        fb_text, fb_layer_meta, _ = _apply_fallback_behavior_layer(
            _normalize_text(out.get("player_facing_text")),
            gm_output=out,
            resolution=eff_res,
            strict_social_path=True,
            session=sess,
            scene_id=sid,
        )
        fb_source = (
            "gate.apply_final_emission_gate.strict_social.fallback_behavior_text"
            if profile == "strict_accept"
            else "gate.apply_final_emission_gate.strict_social_replace_path.fallback_behavior_text"
        )
        assert_final_emission_mutation_allowed(
            "normalize_whitespace",
            source=fb_source,
        )
        out["player_facing_text"] = fb_text
        merge_fallback_behavior_into_emission_debug(
            out,
            auth_res,
            eff_res,
            gate_meta=fb_layer_meta,
        )
        fem_patch = out.get("_final_emission_meta")
        if isinstance(fem_patch, dict):
            _merge_fallback_behavior_meta(fem_patch, fb_layer_meta)
            gtxt = _normalize_text(fb_text)
            fem_patch["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
            fem_patch["post_gate_mutation_detected"] = pre_gate_text != gtxt
            if fb_layer_meta.get("fallback_behavior_repaired"):
                fem_patch["final_emitted_source"] = str(
                    fb_layer_meta.get("fallback_behavior_repair_mode") or "fallback_behavior_repair"
                )

    _apply_referent_clarity_pre_finalize(out, pre_gate_text=pre_gate_text)

    if profile == "generic_replace" and nmo_fem_trace_override is not None:
        _merge_narrative_mode_output_trace_into_gate_fem(out, nmo_fem_trace_override)
    else:
        nmo_result = _narrative_mode_output_legality_assessment(
            str(out.get("player_facing_text") or ""),
            out,
            resolution_for_nmo=resolution_for_nmo,
            strict_social_details_flag=nmo_strict_flag,
        )
        _merge_narrative_mode_output_trace_into_gate_fem(out, nmo_result["trace"])
        if profile == "strict_accept" and nmo_result["nmo_enforcement_fail"]:
            em_fb = minimal_social_emergency_fallback_line(eff_res)
            assert_final_emission_mutation_allowed(
                "hard_replace_illegal_output_with_sealed_fallback",
                source="gate.apply_final_emission_gate.strict_social.nmo_emergency",
            )
            apply_strict_social_emergency_fallback_patch(
                out,
                fallback_text=em_fb,
                pre_gate_text=pre_gate_text,
                gate_tag="narrative_mode_output",
                final_route="replaced",
                candidate_validation_passed=False,
            )
            nmo_post_fb = _narrative_mode_output_legality_assessment(
                str(out.get("player_facing_text") or ""),
                out,
                resolution_for_nmo=eff_res,
                strict_social_details_flag=True,
            )
            _merge_narrative_mode_output_trace_into_gate_fem(out, nmo_post_fb["trace"])

    apply_acceptance_quality_n4_floor_seam(
        out,
        gm_output_for_contract=out,
        candidate_text=str(out.get("player_facing_text") or ""),
        strict_social_path=strict_social_path,
        eff_resolution=eff_res,
        resolution=auth_res,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        res_kind=res_kind,
        response_type_required=str(response_type_debug.get("response_type_required") or ""),
        pre_gate_text=pre_gate_text,
    )

    if profile == "strict_accept":
        attach_interaction_continuity_validation(
            out,
            resolution_for_contracts=eff_res,
            eff_resolution=eff_res,
            session=sess,
            preserve_existing_validation=True,
        )
    else:
        attach_interaction_continuity_validation(
            out,
            resolution_for_contracts=resolution_for_ic_contracts,
            eff_resolution=eff_res,
            session=sess,
        )

    merge_narration_constraint_debug_into_outputs(
        out,
        auth_res,
        eff_res,
        session=session,
        scene=scene,
        world=world,
        response_type_debug=response_type_debug,
        speaker_contract_enforcement=speaker_contract_enforcement
        if profile in ("strict_accept", "strict_replace")
        else None,
    )

    if profile == "generic_accept":
        opening_fallback.reassert_scene_opening_accepted_candidate(
            out,
            accepted_scene_opening_text=accepted_scene_opening_text,
            source="gate.apply_final_emission_gate.scene_opening_accept_return",
        )

    return out
