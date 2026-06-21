"""BU2-B: narration-constraint debug merge owner extraction."""

from __future__ import annotations

import copy
import inspect
from typing import Any

import pytest

import game.final_emission_narration_constraint_debug as narration_constraint_debug
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.final_emission_meta import build_narration_constraint_debug, merge_narration_constraint_debug_meta
from game.narration_visibility import build_narration_visibility_contract
from game.speaker_contract_enforcement import get_speaker_selection_contract

pytestmark = pytest.mark.unit


def _sample_out(**extra: Any) -> dict[str, Any]:
    base = {
        "player_facing_text": "Tavern Runner says, \"East lanes.\"",
        "tags": [],
        "_final_emission_meta": {"visibility_validation_passed": True},
        "metadata": {
            "emission_debug": {
                "interaction_continuity_speaker_binding_bridge": {
                    "speaker_reason_code": "speaker_contract_match",
                }
            }
        },
        "trace": {"stage": "final_emission_gate"},
    }
    base.update(extra)
    return base


def _inline_merge_narration_constraint_debug_into_outputs(
    out: dict[str, Any],
    resolution: dict[str, Any] | None,
    eff_resolution: dict[str, Any] | None,
    *,
    session: dict[str, Any] | None,
    scene: dict[str, Any] | None,
    world: dict[str, Any] | None,
    response_type_debug: dict[str, Any] | None,
    speaker_contract_enforcement: dict[str, Any] | None = None,
) -> None:
    """Pre-BU2-B inline body preserved for equivalence checks."""
    md_out = out.setdefault("metadata", {})
    if not isinstance(md_out, dict):
        return

    visibility_meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    speaker_selection_contract = get_speaker_selection_contract(
        eff_resolution if isinstance(eff_resolution, dict) else resolution,
        metadata=md_out,
        trace=out.get("trace") if isinstance(out.get("trace"), dict) else None,
    )

    def _resolve_visibility_contract() -> dict[str, Any]:
        try:
            contract = build_narration_visibility_contract(
                session=session if isinstance(session, dict) else None,
                scene=scene if isinstance(scene, dict) else None,
                world=world if isinstance(world, dict) else None,
            )
        except Exception:
            return {}
        return contract if isinstance(contract, dict) else {}

    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
    bridge = em.get("interaction_continuity_speaker_binding_bridge")
    speaker_binding_bridge = bridge if isinstance(bridge, dict) else {}

    payload = build_narration_constraint_debug(
        response_type_debug=response_type_debug,
        narration_visibility=_resolve_visibility_contract(),
        visibility_meta=visibility_meta,
        speaker_selection_contract=speaker_selection_contract,
        speaker_contract_enforcement=speaker_contract_enforcement,
        speaker_binding_bridge=speaker_binding_bridge,
    )
    merge_narration_constraint_debug_meta(md_out, payload)

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            merge_narration_constraint_debug_meta(md_r, payload)

    if eff_resolution is not None and eff_resolution is not resolution:
        md_eff = eff_resolution.setdefault("metadata", {})
        if isinstance(md_eff, dict):
            merge_narration_constraint_debug_meta(md_eff, payload)


def test_merge_narration_constraint_debug_into_outputs_matches_inline_sequence() -> None:
    session: dict[str, Any] = {}
    scene: dict[str, Any] = {}
    world: dict[str, Any] = {}
    resolution = {"kind": "question", "metadata": {"emission_debug": {}}}
    eff_resolution = {"kind": "question", "metadata": {"emission_debug": {"eff_only": True}}}
    response_type_debug = {
        "response_type_required": "dialogue",
        "response_type_candidate_ok": True,
        "response_type_contract_source": "response_policy",
    }
    speaker_contract_enforcement = {"final_reason_code": "speaker_contract_match"}

    inline_out = _sample_out()
    inline_resolution = copy.deepcopy(resolution)
    inline_eff = copy.deepcopy(eff_resolution)
    _inline_merge_narration_constraint_debug_into_outputs(
        inline_out,
        inline_resolution,
        inline_eff,
        session=session,
        scene=scene,
        world=world,
        response_type_debug=response_type_debug,
        speaker_contract_enforcement=speaker_contract_enforcement,
    )

    helper_out = _sample_out()
    helper_resolution = copy.deepcopy(resolution)
    helper_eff = copy.deepcopy(eff_resolution)
    narration_constraint_debug.merge_narration_constraint_debug_into_outputs(
        helper_out,
        helper_resolution,
        helper_eff,
        session=session,
        scene=scene,
        world=world,
        response_type_debug=response_type_debug,
        speaker_contract_enforcement=speaker_contract_enforcement,
    )

    assert inline_out == helper_out
    assert inline_resolution == helper_resolution
    assert inline_eff == helper_eff


def test_terminal_pipeline_delegates_narration_constraint_debug_merge() -> None:
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "merge_narration_constraint_debug_into_outputs(" in tp_src
    assert "build_narration_visibility_contract" not in tp_src
    assert "get_speaker_selection_contract" not in tp_src
    assert "build_narration_constraint_debug(" not in tp_src
    assert tp_src.index("attach_interaction_continuity_validation(") < tp_src.index(
        "merge_narration_constraint_debug_into_outputs("
    )


def test_terminal_pipeline_preserves_enforcement_order_before_narration_debug() -> None:
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert tp_src.index("apply_visibility_enforcement(") < tp_src.index(
        "_apply_referent_clarity_pre_finalize("
    )
    assert tp_src.index("_apply_referent_clarity_pre_finalize(") < tp_src.index(
        "apply_acceptance_quality_n4_floor_seam("
    )
    assert tp_src.index("apply_acceptance_quality_n4_floor_seam(") < tp_src.index(
        "attach_interaction_continuity_validation("
    )
    assert tp_src.index("attach_interaction_continuity_validation(") < tp_src.index(
        "merge_narration_constraint_debug_into_outputs("
    )
