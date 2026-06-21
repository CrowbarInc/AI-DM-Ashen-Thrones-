"""BU2-A: pre-terminal layer debug merge consolidation on final_emission_fem_assembly."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_repairs as emission_repairs
import game.final_emission_strict_social_stack as strict_social_stack
from game.final_emission_answer_shape_primacy import merge_answer_shape_primacy_into_emission_debug
from game.final_emission_anti_railroading import merge_anti_railroading_into_emission_debug
from game.final_emission_context_separation import merge_context_separation_into_emission_debug
from game.final_emission_narrative_authority import merge_narrative_authority_into_emission_debug
from game.final_emission_player_facing_narration_purity import (
    merge_player_facing_narration_purity_into_emission_debug,
)
from game.final_emission_scene_state_anchor import _merge_scene_state_anchor_into_emission_debug
from game.final_emission_tone_escalation import merge_tone_escalation_into_emission_debug

pytestmark = pytest.mark.unit


def _sample_layer_metas() -> dict[str, dict[str, Any]]:
    return {
        "ssa_layer_meta": {
            "scene_state_anchor_checked": True,
            "scene_state_anchor_failed": True,
            "scene_state_anchor_repaired": False,
        },
        "te_layer_meta": {
            "tone_escalation_checked": True,
            "tone_escalation_repaired": False,
        },
        "na_layer_meta": {
            "narrative_authority_checked": True,
            "narrative_authority_failed": False,
        },
        "ar_layer_meta": {
            "anti_railroading_checked": True,
            "anti_railroading_repaired": False,
        },
        "cs_layer_meta": {
            "context_separation_checked": True,
            "context_separation_repaired": False,
        },
        "purity_layer_meta": {
            "player_facing_narration_purity_checked": True,
            "player_facing_narration_purity_repaired": False,
        },
        "asp_layer_meta": {
            "answer_shape_primacy_checked": True,
            "answer_shape_primacy_repaired": False,
        },
    }


def _sample_out(**extra: Any) -> dict[str, Any]:
    base = {
        "player_facing_text": "The wind shifts.",
        "tags": [],
        "metadata": {"emission_debug": {"prior_debug_counts": {"x": 1}}},
        "response_policy": {
            "conversational_memory_window": {
                "selected_count": 2,
                "window_size": 4,
            }
        },
    }
    base.update(extra)
    return base


def _inline_pre_terminal_merge(
    out: dict[str, Any],
    resolution: dict[str, Any] | None,
    eff_resolution: dict[str, Any] | None,
    layer_metas: dict[str, dict[str, Any]],
) -> None:
    """Pre-BU2-A inline sequence preserved for equivalence checks."""
    _merge_scene_state_anchor_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["ssa_layer_meta"],
    )
    merge_tone_escalation_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["te_layer_meta"],
        gm_output=out,
    )
    merge_narrative_authority_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["na_layer_meta"],
        gm_output=out,
    )
    merge_anti_railroading_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["ar_layer_meta"],
        gm_output=out,
    )
    merge_context_separation_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["cs_layer_meta"],
    )
    merge_player_facing_narration_purity_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["purity_layer_meta"],
    )
    merge_answer_shape_primacy_into_emission_debug(
        out,
        resolution,
        eff_resolution,
        gate_meta=layer_metas["asp_layer_meta"],
    )
    emission_repairs.merge_conversational_memory_inspection_into_emission_debug(
        out,
        resolution,
        eff_resolution,
    )


def test_merge_pre_terminal_layer_debug_matches_inline_sequence() -> None:
    resolution = {"kind": "observe", "metadata": {"emission_debug": {}}}
    eff_resolution = {"kind": "observe", "metadata": {"emission_debug": {}}}
    layer_metas = _sample_layer_metas()

    inline_out = _sample_out()
    helper_out = _sample_out()

    _inline_pre_terminal_merge(inline_out, resolution, eff_resolution, layer_metas)
    fem_assembly.merge_pre_terminal_layer_debug(
        helper_out,
        resolution,
        eff_resolution,
        **layer_metas,
    )

    assert inline_out == helper_out


def test_merge_pre_terminal_layer_debug_preserves_resolution_metadata_sidecars() -> None:
    resolution = {
        "kind": "question",
        "metadata": {"emission_debug": {"resolution_only": True}},
    }
    eff_resolution = {
        "kind": "question",
        "metadata": {"emission_debug": {"eff_only": True}},
    }
    layer_metas = _sample_layer_metas()
    out = _sample_out()

    fem_assembly.merge_pre_terminal_layer_debug(
        out,
        resolution,
        eff_resolution,
        **layer_metas,
    )

    assert resolution["metadata"]["emission_debug"]["resolution_only"] is True
    assert eff_resolution["metadata"]["emission_debug"]["eff_only"] is True
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("prior_debug_counts") == {"x": 1}
    assert any(str(k).startswith("scene_state_anchor_") for k in em)


def test_bu2a_stacks_delegate_pre_terminal_debug_merge_to_fem_assembly() -> None:
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)

    for src in (ss_src, nss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_scene_state_anchor_into_emission_debug(" not in src
        assert "_merge_tone_escalation_into_emission_debug(" not in src
        assert "_merge_narrative_authority_into_emission_debug(" not in src
        assert "_merge_anti_railroading_into_emission_debug(" not in src
        assert "_merge_context_separation_into_emission_debug(" not in src
        assert "_merge_player_facing_narration_purity_into_emission_debug(" not in src
        assert "_merge_answer_shape_primacy_into_emission_debug(" not in src
        assert "merge_conversational_memory_inspection_into_emission_debug(" not in src

    assert fa_src.index("_merge_scene_state_anchor_into_emission_debug(") < fa_src.index(
        "merge_tone_escalation_into_emission_debug("
    )
    assert fa_src.index("merge_tone_escalation_into_emission_debug(") < fa_src.index(
        "merge_narrative_authority_into_emission_debug("
    )
    assert fa_src.index("merge_narrative_authority_into_emission_debug(") < fa_src.index(
        "merge_anti_railroading_into_emission_debug("
    )
    assert fa_src.index("merge_anti_railroading_into_emission_debug(") < fa_src.index(
        "merge_context_separation_into_emission_debug("
    )
    assert fa_src.index("merge_context_separation_into_emission_debug(") < fa_src.index(
        "merge_player_facing_narration_purity_into_emission_debug("
    )
    assert fa_src.index("merge_player_facing_narration_purity_into_emission_debug(") < fa_src.index(
        "merge_answer_shape_primacy_into_emission_debug("
    )
    assert fa_src.index("merge_answer_shape_primacy_into_emission_debug(") < fa_src.index(
        "merge_conversational_memory_inspection_into_emission_debug("
    )


def test_bu2a_non_strict_stack_still_merges_fallback_behavior_after_ic() -> None:
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert nss_src.index("apply_interaction_continuity_emission_step") < nss_src.index(
        "_apply_fallback_behavior_layer"
    )
    assert nss_src.index("_apply_fallback_behavior_layer") < nss_src.index(
        "merge_fallback_behavior_into_emission_debug"
    )
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
