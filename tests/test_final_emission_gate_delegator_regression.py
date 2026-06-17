"""Historical BJ thin-boundary/delegator/re-export regression locks for final emission gate.

This file owns mostly static ``inspect``/source-shape coverage that guards against
gate-module regrowth: removed delegators, collapsed re-exports, and harness patch seams.

Behavioral orchestration tests (layer order, selector snapshots, N4 placement) remain in
``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import inspect

import pytest

import game.dialogue_social_plan as dialogue_social_plan
import game.final_emission_acceptance_quality as acceptance_quality_gate
import game.final_emission_fast_fallback_composition as fast_fallback_composition
import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_finalize as emission_finalize
import game.final_emission_gate as feg
import game.final_emission_gate_context as gate_context
import game.final_emission_generic_exit as generic_exit
import game.final_emission_narrative_authority as narrative_authority
import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_repairs as emission_repairs
import game.final_emission_response_type as response_type
import game.final_emission_sealed_fallback as sealed_fallback
import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_terminal_pipeline as terminal_pipeline
import game.final_emission_tone_escalation as tone_escalation
import game.final_emission_visibility_fallback as visibility_fallback
from game.final_emission_meta import read_final_emission_meta_dict
from game.final_emission_text import _normalize_text

pytestmark = pytest.mark.unit


def test_bj41_finalize_emission_output_strips_appended_stock_and_packages_sidecar() -> None:
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    out = {
        "player_facing_text": selector,
        "_final_emission_meta": {"final_route": "accept_candidate"},
        "tags": [],
        "metadata": {},
        "debug_notes": "dbg",
    }
    pre = _normalize_text(selector)
    finalized = emission_finalize.finalize_emission_output(out, pre_gate_text=pre, fast_path=True)
    pft = (finalized.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
    assert "internal_state" in finalized
    fem = read_final_emission_meta_dict(finalized) or {}
    assert fem.get("finalize_route_illegal_strip_applied") is True
    lineage = fem.get("final_emission_mutation_lineage")
    assert "finalize_route_illegal_strip" in lineage
    assert "finalize_packaging" in lineage


def test_bj69_terminal_finalize_fast_path_gate_delegators_removed() -> None:
    """BJ-69: terminal pipeline, finalize, and fast-path gate delegators removed; exit stacks call owners."""
    assert not hasattr(feg, "_run_gate_terminal_enforcement_pipeline")
    assert not hasattr(feg, "_finalize_emission_output")
    assert not hasattr(feg, "_final_emission_fast_path_eligible")
    assert callable(getattr(terminal_pipeline, "run_gate_terminal_enforcement_pipeline", None))
    assert callable(getattr(emission_finalize, "finalize_emission_output", None))
    assert callable(getattr(emission_finalize, "final_emission_fast_path_eligible", None))


def test_bj69_exit_stacks_terminal_finalize_fast_path_call_owners_directly() -> None:
    """BJ-69: generic and strict-social exit stacks call terminal/finalize owners directly."""
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    for src in (ge_accept_src, ge_replace_src, ss_src):
        assert "terminal_pipeline.run_gate_terminal_enforcement_pipeline" in src
        assert "emission_finalize.finalize_emission_output" in src
        assert "emission_finalize.final_emission_fast_path_eligible" in src
        assert "feg._run_gate_terminal_enforcement_pipeline" not in src
        assert "feg._finalize_emission_output" not in src
        assert "feg._final_emission_fast_path_eligible" not in src


def test_bj71_non_strict_layer_stack_gate_delegator_removed() -> None:
    """BJ-71: non-strict layer stack gate delegator removed; apply_final_emission_gate calls owner directly."""
    assert not hasattr(feg, "_run_non_strict_layer_stack")
    assert callable(getattr(non_strict_stack, "run_non_strict_layer_stack", None))


def test_bj71_apply_final_emission_gate_calls_non_strict_stack_owner_directly() -> None:
    """BJ-71: gate orchestration calls non_strict_stack owner directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src


def test_bj70_exit_stack_gate_delegators_removed() -> None:
    """BJ-70: exit/stack gate delegators removed; apply_final_emission_gate calls owners directly."""
    assert not hasattr(feg, "_run_strict_social_composition_trunk")
    assert not hasattr(feg, "_run_generic_accept_exit")
    assert not hasattr(feg, "_run_generic_replace_exit")
    assert callable(getattr(strict_social_stack, "run_strict_social_composition_trunk", None))
    assert callable(getattr(generic_exit, "run_generic_accept_exit", None))
    assert callable(getattr(generic_exit, "run_generic_replace_exit", None))


def test_bj70_apply_final_emission_gate_calls_exit_stack_owners_directly() -> None:
    """BJ-70: gate orchestration calls generic/strict-social exit owners directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_strict_social_composition_trunk(" in gate_src
    assert "run_generic_accept_exit(" in gate_src
    assert "run_generic_replace_exit(" in gate_src
    assert "_run_strict_social_composition_trunk" not in gate_src
    assert "_run_generic_accept_exit" not in gate_src
    assert "_run_generic_replace_exit" not in gate_src


def test_bj63_fem_assembly_gate_delegators_collapsed() -> None:
    """Cycle BJ-63: FEM assembly gate delegators removed; exit stacks call owner directly."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg

    for name in (
        "_build_gate_accept_fem_base",
        "_build_gate_replace_fem_base",
        "_merge_gate_layer_metas_into_fem",
    ):
        assert not hasattr(feg, name), name
    for name in (
        "build_gate_accept_fem_base",
        "build_gate_replace_fem_base",
        "merge_gate_layer_metas_into_fem",
    ):
        assert callable(getattr(fa, name, None)), name


def test_bj64_opening_rt_accept_path_promotion_gate_alias_removed() -> None:
    """BJ-64: opening RT accept-path promotion alias removed; non_strict_stack calls owner."""
    assert not hasattr(feg, "_scene_opening_rt_contract_accept_path_promotes_candidate")
    src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate" in src
    assert "_scene_opening_rt_contract_accept_path_promotes_candidate" not in src


def test_bj65_opening_upstream_prepare_observability_merge_gate_alias_removed() -> None:
    """BJ-65: opening upstream-prepare observability merge alias removed; stacks call response_type owner."""
    assert not hasattr(feg, "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug")
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    marker = "response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in nss_src
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in ss_src


def test_bj66_dead_opening_fallback_gate_imports_removed() -> None:
    """BJ-66: gate no longer re-exports unused opening-fallback normalization helpers."""
    gate_source = inspect.getsource(feg)
    assert "final_emission_opening_fallback" not in gate_source
    assert not hasattr(feg, "_gm_output_normalized_for_opening_context")
    assert not hasattr(feg, "_opening_curated_facts_schema_ok")


def test_bj67_stacks_response_type_enforcement_calls_owner_directly() -> None:
    """BJ-67: stacks call response_type owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    marker = "response_type.enforce_response_type_contract"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._enforce_response_type_contract" not in nss_src
    assert "feg._enforce_response_type_contract" not in ss_src


def test_bj68_response_type_enforcement_gate_delegator_removed() -> None:
    """BJ-68: gate no longer re-exports enforce_response_type_contract; harnesses call owner."""
    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness

    assert not hasattr(feg, "_enforce_response_type_contract")
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert "response_type.enforce_response_type_contract" in ob_src
    assert "feg._enforce_response_type_contract" not in ob_src
    assert "final_emission_response_type" in smoke_fn_src
    assert "final_emission_gate" not in smoke_fn_src
    assert callable(getattr(response_type, "enforce_response_type_contract", None))


def test_bj86_fast_fallback_neutral_composition_layer_gate_delegator_removed() -> None:
    """BJ-86: FFNC layer gate delegator removed; stacks call owner directly."""
    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")
    assert callable(getattr(fast_fallback_composition, "apply_fast_fallback_neutral_composition_layer", None))


def test_bj86_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src


def test_bj87_answer_completeness_layer_gate_reexport_removed() -> None:
    """BJ-87: answer completeness layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_answer_completeness_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_completeness_layer", None))


def test_bj87_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_answer_completeness_layer(" in nss_src
    assert "feg._apply_answer_completeness_layer" not in nss_src
    assert "emission_repairs._apply_answer_completeness_layer(" in ss_src
    assert "feg._apply_answer_completeness_layer" not in ss_src


def test_bj88_answer_exposition_plan_layer_gate_reexport_removed() -> None:
    """BJ-88: answer exposition plan layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_answer_exposition_plan_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_exposition_plan_layer", None))


def test_bj88_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """BJ-88: stacks call final_emission_repairs answer exposition plan directly (3 strict-social sites)."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack)
    assert "_apply_answer_exposition_plan_layer(" in nss_src
    assert "feg._apply_answer_exposition_plan_layer" not in nss_src
    assert ss_src.count("emission_repairs._apply_answer_exposition_plan_layer(") == 3
    assert "feg._apply_answer_exposition_plan_layer" not in ss_src


def test_bj89_response_delta_layer_gate_reexport_removed() -> None:
    """BJ-89: response delta layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_response_delta_layer")
    assert callable(getattr(emission_repairs, "_apply_response_delta_layer", None))


def test_bj89_stacks_call_response_delta_repairs_owner_directly() -> None:
    """BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_response_delta_layer(" in nss_src
    assert "feg._apply_response_delta_layer" not in nss_src
    assert "emission_repairs._apply_response_delta_layer(" in ss_src
    assert "feg._apply_response_delta_layer" not in ss_src


def test_bj90_social_response_structure_layer_gate_reexport_removed() -> None:
    """BJ-90: social response structure layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_social_response_structure_layer")
    assert callable(getattr(emission_repairs, "_apply_social_response_structure_layer", None))


def test_bj90_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_social_response_structure_layer(" in nss_src
    assert "feg._apply_social_response_structure_layer" not in nss_src
    assert "emission_repairs._apply_social_response_structure_layer(" in ss_src
    assert "feg._apply_social_response_structure_layer" not in ss_src


def test_bj91_narrative_authenticity_layer_gate_reexport_removed() -> None:
    """BJ-91: narrative authenticity layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_narrative_authenticity_layer")
    assert callable(getattr(emission_repairs, "_apply_narrative_authenticity_layer", None))


def test_bj91_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_narrative_authenticity_layer(" in nss_src
    assert "feg._apply_narrative_authenticity_layer" not in nss_src
    assert "emission_repairs._apply_narrative_authenticity_layer(" in ss_src
    assert "feg._apply_narrative_authenticity_layer" not in ss_src


def test_bj92_fallback_behavior_layer_gate_reexport_removed() -> None:
    """BJ-92: fallback behavior layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_fallback_behavior_layer")
    assert callable(getattr(emission_repairs, "_apply_fallback_behavior_layer", None))


def test_bj92_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "_apply_fallback_behavior_layer(" in nss_src
    assert "feg._apply_fallback_behavior_layer" not in nss_src
    assert "_apply_fallback_behavior_layer(" in tp_src
    assert "feg._apply_fallback_behavior_layer" not in tp_src


def test_bj93_fallback_behavior_debug_merge_gate_reexports_removed() -> None:
    """BJ-93: fallback behavior debug/meta merge helpers no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_merge_fallback_behavior_into_emission_debug")
    assert not hasattr(feg, "_merge_fallback_behavior_meta")
    assert callable(getattr(emission_repairs, "merge_fallback_behavior_into_emission_debug", None))
    assert callable(getattr(emission_repairs, "_merge_fallback_behavior_meta", None))


def test_bj93_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """BJ-93: non_strict_stack and terminal_pipeline call repairs fallback debug/meta merge directly."""
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in nss_src
    assert "merge_fallback_behavior_into_emission_debug(" in tp_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in tp_src
    assert "_merge_fallback_behavior_meta(" in tp_src
    assert "feg._merge_fallback_behavior_meta" not in tp_src


def test_bj94_conversational_memory_inspection_debug_merge_gate_reexport_removed() -> None:
    """BJ-94: conversational memory inspection debug merge no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_merge_conversational_memory_inspection_into_emission_debug")
    assert callable(
        getattr(emission_repairs, "merge_conversational_memory_inspection_into_emission_debug", None)
    )


def test_bj94_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BJ-94: strict and non-strict stacks call repairs conversational memory debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "merge_conversational_memory_inspection_into_emission_debug(" in nss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in nss_src
    assert "emission_repairs.merge_conversational_memory_inspection_into_emission_debug(" in ss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in ss_src


def test_bj95_scene_state_anchor_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-95: scene state anchor emission_debug merge no longer re-exported through gate."""
    import game.final_emission_scene_state_anchor as scene_state_anchor

    assert not hasattr(feg, "_merge_scene_state_anchor_into_emission_debug")
    assert callable(getattr(scene_state_anchor, "_merge_scene_state_anchor_into_emission_debug", None))


def test_bj95_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BJ-95: strict and non-strict stacks call scene_state_anchor emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_scene_state_anchor_into_emission_debug(" in nss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in nss_src
    assert "_merge_scene_state_anchor_into_emission_debug(" in ss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in ss_src


def test_bj96_tone_escalation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-96: tone escalation emission_debug merge no longer re-exported through gate."""
    import game.final_emission_tone_escalation as tone_escalation

    assert not hasattr(feg, "_merge_tone_escalation_into_emission_debug")
    assert callable(getattr(tone_escalation, "merge_tone_escalation_into_emission_debug", None))


def test_bj96_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BJ-96: strict and non-strict stacks call tone_escalation emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_tone_escalation_into_emission_debug(" in nss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in nss_src
    assert "_merge_tone_escalation_into_emission_debug(" in ss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in ss_src


def test_bj97_narrative_authority_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-97: narrative authority emission_debug merge no longer re-exported through gate."""
    import game.final_emission_narrative_authority as narrative_authority

    assert not hasattr(feg, "_merge_narrative_authority_into_emission_debug")
    assert callable(getattr(narrative_authority, "merge_narrative_authority_into_emission_debug", None))


def test_bj97_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BJ-97: strict and non-strict stacks call narrative_authority emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_narrative_authority_into_emission_debug(" in nss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in nss_src
    assert "_merge_narrative_authority_into_emission_debug(" in ss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in ss_src


def test_bj98_anti_railroading_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-98: anti-railroading emission_debug merge no longer re-exported through gate."""
    import game.final_emission_anti_railroading as anti_railroading

    assert not hasattr(feg, "_merge_anti_railroading_into_emission_debug")
    assert callable(getattr(anti_railroading, "merge_anti_railroading_into_emission_debug", None))


def test_bj98_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BJ-98: strict and non-strict stacks call anti_railroading emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_anti_railroading_into_emission_debug(" in nss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in nss_src
    assert "_merge_anti_railroading_into_emission_debug(" in ss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in ss_src


def test_bj99_context_separation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-99: context separation emission_debug merge no longer re-exported through gate."""
    import game.final_emission_context_separation as context_separation

    assert not hasattr(feg, "_merge_context_separation_into_emission_debug")
    assert callable(getattr(context_separation, "merge_context_separation_into_emission_debug", None))


def test_bj99_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BJ-99: strict and non-strict stacks call context_separation emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_context_separation_into_emission_debug(" in nss_src
    assert "feg._merge_context_separation_into_emission_debug" not in nss_src
    assert "_merge_context_separation_into_emission_debug(" in ss_src
    assert "feg._merge_context_separation_into_emission_debug" not in ss_src


def test_bj100_narration_purity_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-100: narration purity emission_debug merge no longer re-exported through gate."""
    import game.final_emission_player_facing_narration_purity as narration_purity

    assert not hasattr(feg, "_merge_player_facing_narration_purity_into_emission_debug")
    assert callable(
        getattr(narration_purity, "merge_player_facing_narration_purity_into_emission_debug", None)
    )


def test_bj100_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BJ-100: strict and non-strict stacks call narration_purity emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in nss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in nss_src
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in ss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in ss_src


def test_bj101_answer_shape_primacy_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-101: answer-shape primacy emission_debug merge no longer re-exported through gate."""
    import game.final_emission_answer_shape_primacy as answer_shape_primacy

    assert not hasattr(feg, "_merge_answer_shape_primacy_into_emission_debug")
    assert callable(getattr(answer_shape_primacy, "merge_answer_shape_primacy_into_emission_debug", None))


def test_bj101_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BJ-101: strict and non-strict stacks call answer_shape_primacy emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_answer_shape_primacy_into_emission_debug(" in nss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in nss_src
    assert "_merge_answer_shape_primacy_into_emission_debug(" in ss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in ss_src


def test_bj102_tone_escalation_pregate_flag_gate_reexport_removed() -> None:
    """BJ-102: non-hostile escalation pregate flag no longer re-exported through gate."""
    import game.final_emission_tone_escalation as tone_escalation

    assert not hasattr(feg, "_flag_non_hostile_escalation_from_writer_pregate")
    assert callable(getattr(tone_escalation, "flag_non_hostile_escalation_from_writer_pregate", None))


def test_bj102_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "flag_non_hostile_escalation_from_writer_pregate(" in ss_src
    assert "feg._flag_non_hostile_escalation_from_writer_pregate" not in ss_src


def test_bj103_scene_emit_integrity_assessment_gate_reexport_removed() -> None:
    """BJ-103: scene emit integrity assessment no longer re-exported through gate."""
    import game.final_emission_scene_emit_integrity as scene_emit_integrity

    assert not hasattr(feg, "_compute_scene_emit_integrity_assessment")
    assert callable(getattr(scene_emit_integrity, "_compute_scene_emit_integrity_assessment", None))


def test_bj103_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_compute_scene_emit_integrity_assessment(" in nss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in nss_src
    assert "_compute_scene_emit_integrity_assessment(" in ss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in ss_src


def test_bj104_passive_scene_pressure_due_check_gate_reexport_removed() -> None:
    """BJ-104: passive scene pressure due-check no longer re-exported through gate."""
    import game.final_emission_passive_scene_pressure as passive_scene_pressure

    assert not hasattr(feg, "_passive_scene_pressure_due_for_fallback")
    assert callable(getattr(passive_scene_pressure, "_passive_scene_pressure_due_for_fallback", None))


def test_bj104_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "_passive_scene_pressure_due_for_fallback(" in nss_src
    assert "feg._passive_scene_pressure_due_for_fallback" not in nss_src


def test_bj105_narrative_mode_output_assessment_gate_reexport_removed() -> None:
    """BJ-105: narrative mode output legality assessment no longer re-exported through gate."""
    import game.final_emission_narrative_mode_output as narrative_mode_output

    assert not hasattr(feg, "_narrative_mode_output_legality_assessment")
    assert callable(getattr(narrative_mode_output, "_narrative_mode_output_legality_assessment", None))


def test_bj105_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "_narrative_mode_output_legality_assessment(" in nss_src
    assert "feg._narrative_mode_output_legality_assessment" not in nss_src


def test_bj106_response_type_decision_payload_gate_reexport_removed() -> None:
    """BJ-106: response_type decision payload no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "_response_type_decision_payload")
    assert callable(getattr(emission_meta, "response_type_decision_payload", None))


def test_bj106_callers_use_response_type_decision_payload_owner_directly() -> None:
    """BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "response_type_decision_payload(" in ss_src
    assert "feg._response_type_decision_payload" not in ss_src
    assert "response_type_decision_payload(" in ge_accept_src
    assert "feg._response_type_decision_payload" not in ge_accept_src
    assert "response_type_decision_payload(" in ge_replace_src
    assert "feg._response_type_decision_payload" not in ge_replace_src


def test_bj107_infer_accept_path_final_emitted_source_gate_reexport_removed() -> None:
    """BJ-107: accept-path final_emitted_source inference no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "infer_accept_path_final_emitted_source")
    assert callable(getattr(emission_meta, "infer_accept_path_final_emitted_source", None))


def test_bj107_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    assert "infer_accept_path_final_emitted_source(" in ss_src
    assert "feg.infer_accept_path_final_emitted_source" not in ss_src
    assert "infer_accept_path_final_emitted_source(" in ge_accept_src
    assert "feg.infer_accept_path_final_emitted_source" not in ge_accept_src


def test_bj108_opening_fallback_projection_gate_reexports_removed() -> None:
    """BJ-108: opening fallback projection helpers no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "apply_opening_fallback_projection_fields")
    assert not hasattr(feg, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")
    assert callable(getattr(emission_meta, "apply_opening_fallback_projection_fields", None))
    assert hasattr(emission_meta, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")


def test_bj108_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "apply_opening_fallback_projection_fields(" in ge_replace_src
    assert "feg.apply_opening_fallback_projection_fields" not in ge_replace_src
    assert "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" in ge_replace_src
    assert "feg.OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" not in ge_replace_src


def test_bj109_final_emission_meta_key_gate_reexport_removed() -> None:
    """BJ-109: FINAL_EMISSION_META_KEY no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "FINAL_EMISSION_META_KEY")
    assert hasattr(emission_meta, "FINAL_EMISSION_META_KEY")
    assert emission_meta.FINAL_EMISSION_META_KEY == "_final_emission_meta"


def test_bj109_callers_use_final_emission_meta_key_owner_directly() -> None:
    """BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "FINAL_EMISSION_META_KEY" in ss_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ss_src
    assert "FINAL_EMISSION_META_KEY" in ge_accept_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_accept_src
    assert "FINAL_EMISSION_META_KEY" in ge_replace_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_replace_src


def test_bj110_assert_final_emission_mutation_allowed_gate_reexport_removed() -> None:
    """BJ-110: boundary mutation assertion no longer re-exported through gate."""
    import game.final_emission_boundary_contract as boundary_contract

    assert not hasattr(feg, "assert_final_emission_mutation_allowed")
    assert callable(getattr(boundary_contract, "assert_final_emission_mutation_allowed", None))


def test_bj110_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "assert_final_emission_mutation_allowed(" in ge_replace_src
    assert "feg.assert_final_emission_mutation_allowed" not in ge_replace_src


def test_bj111_normalize_text_gate_reexport_removed() -> None:
    """BJ-111: _normalize_text no longer re-exported through gate."""
    import game.final_emission_text as emission_text

    assert not hasattr(feg, "_normalize_text")
    assert callable(getattr(emission_text, "_normalize_text", None))


def test_bj111_callers_use_normalize_text_owner_directly() -> None:
    """BJ-111: stack/exit callers use final_emission_text._normalize_text directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "_normalize_text(" in nss_src
    assert "feg._normalize_text(" not in nss_src
    assert "_normalize_text(" in ss_src
    assert "feg._normalize_text(" not in ss_src
    assert "_normalize_text(" in ge_accept_src
    assert "feg._normalize_text(" not in ge_accept_src
    assert "_normalize_text(" in ge_replace_src
    assert "feg._normalize_text(" not in ge_replace_src


def test_bj112_normalize_text_preserve_paragraphs_gate_reexport_removed() -> None:
    """BJ-112: _normalize_text_preserve_paragraphs no longer re-exported through gate."""
    import game.final_emission_text as emission_text

    assert not hasattr(feg, "_normalize_text_preserve_paragraphs")
    assert callable(getattr(emission_text, "_normalize_text_preserve_paragraphs", None))


def test_bj112_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """BJ-112: strict_social_stack calls final_emission_text._normalize_text_preserve_paragraphs directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_normalize_text_preserve_paragraphs(" in ss_src
    assert "feg._normalize_text_preserve_paragraphs" not in ss_src


def test_bj113_diegetic_classified_fallback_meta_gate_reexport_removed() -> None:
    """BJ-113: diegetic_classified_fallback_meta no longer re-exported through gate."""
    import game.diegetic_fallback_narration as diegetic_fallback_narration

    assert not hasattr(feg, "diegetic_classified_fallback_meta")
    assert callable(getattr(diegetic_fallback_narration, "fallback_template_metadata", None))


def test_bj113_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "diegetic_classified_fallback_meta(" in ge_replace_src
    assert "feg.diegetic_classified_fallback_meta" not in ge_replace_src


def test_bj114_anti_reset_suppresses_intro_style_fallbacks_gate_reexport_removed() -> None:
    """BJ-114: anti_reset_suppresses_intro_style_fallbacks no longer re-exported through gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard

    assert not hasattr(feg, "anti_reset_suppresses_intro_style_fallbacks")
    assert callable(getattr(anti_reset_emission_guard, "anti_reset_suppresses_intro_style_fallbacks", None))


def test_bj114_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "anti_reset_suppresses_intro_style_fallbacks(" in ge_replace_src
    assert "feg.anti_reset_suppresses_intro_style_fallbacks" not in ge_replace_src


def test_bj115_log_final_emission_logging_gate_reexports_removed() -> None:
    """BJ-115: final emission logging helpers no longer re-exported through gate."""
    import game.social_exchange_emission as social_exchange_emission

    assert not hasattr(feg, "log_final_emission_decision")
    assert not hasattr(feg, "log_final_emission_trace")
    assert callable(getattr(social_exchange_emission, "log_final_emission_decision", None))
    assert callable(getattr(social_exchange_emission, "log_final_emission_trace", None))


def test_bj115_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "log_final_emission_decision(" in ge_accept_src
    assert "log_final_emission_trace(" in ge_accept_src
    assert "feg.log_final_emission_decision" not in ge_accept_src
    assert "feg.log_final_emission_trace" not in ge_accept_src
    assert "log_final_emission_decision(" in ge_replace_src
    assert "log_final_emission_trace(" in ge_replace_src
    assert "feg.log_final_emission_decision" not in ge_replace_src
    assert "feg.log_final_emission_trace" not in ge_replace_src
    assert "log_final_emission_decision(" in ss_src
    assert "log_final_emission_trace(" in ss_src
    assert "feg.log_final_emission_decision" not in ss_src
    assert "feg.log_final_emission_trace" not in ss_src


def test_bj116_strict_social_social_exchange_gate_reexports_removed() -> None:
    """BJ-116: strict-social social exchange helpers no longer re-exported through gate."""
    import game.social_exchange_emission as social_exchange_emission

    assert not hasattr(feg, "build_final_strict_social_response")
    assert not hasattr(feg, "minimal_social_emergency_fallback_line")
    assert not hasattr(feg, "strict_social_deterministic_fallback_family_token")
    assert callable(getattr(social_exchange_emission, "build_final_strict_social_response", None))
    assert callable(getattr(social_exchange_emission, "minimal_social_emergency_fallback_line", None))
    assert callable(getattr(social_exchange_emission, "strict_social_deterministic_fallback_family_token", None))


def test_bj116_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "build_final_strict_social_response(" in ss_src
    assert "minimal_social_emergency_fallback_line(" in ss_src
    assert "strict_social_deterministic_fallback_family_token(" in ss_src
    assert "feg.build_final_strict_social_response" not in ss_src
    assert "feg.minimal_social_emergency_fallback_line" not in ss_src
    assert "feg.strict_social_deterministic_fallback_family_token" not in ss_src


def test_bj117_telemetry_provenance_gate_reexports_removed() -> None:
    """BJ-117: telemetry/provenance helpers no longer re-exported through gate."""
    import game.fallback_provenance_debug as fallback_provenance_debug
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "record_stage_snapshot")
    assert not hasattr(feg, "realign_fallback_provenance_selector_to_current_text")
    assert callable(getattr(stage_diff_telemetry, "record_stage_snapshot", None))
    assert callable(getattr(fallback_provenance_debug, "realign_fallback_provenance_selector_to_current_text", None))


def test_bj117_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "record_stage_snapshot(" in ss_src
    assert "realign_fallback_provenance_selector_to_current_text(" in ss_src
    assert "feg.record_stage_snapshot" not in ss_src
    assert "feg.realign_fallback_provenance_selector_to_current_text" not in ss_src


def test_bj118_should_replace_candidate_intro_fallback_gate_reexport_removed() -> None:
    """BJ-118: should_replace_candidate_intro_fallback no longer re-exported through gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard

    assert not hasattr(feg, "should_replace_candidate_intro_fallback")
    assert callable(getattr(anti_reset_emission_guard, "should_replace_candidate_intro_fallback", None))


def test_bj119_stage_diff_telemetry_gate_reexports_removed() -> None:
    """BJ-119: stage_diff_telemetry helpers no longer re-exported through gate."""
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "diff_turn_stage")
    assert not hasattr(feg, "record_stage_transition")
    assert not hasattr(feg, "snapshot_turn_stage")
    assert callable(getattr(stage_diff_telemetry, "diff_turn_stage", None))
    assert callable(getattr(stage_diff_telemetry, "record_stage_transition", None))
    assert callable(getattr(stage_diff_telemetry, "snapshot_turn_stage", None))


def test_bj120_harness_patches_canonical_owner_seams() -> None:
    """BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    import tests.helpers.gate_equivalence_monkeypatch as gate_mp
    import tests.test_turn_packet_stage_diff_integration as tp_stage_diff

    mp_src = inspect.getsource(gate_mp.patch_build_final_strict_social_response)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in mp_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in mp_src
    tp_src = inspect.getsource(tp_stage_diff.test_gate_exit_records_observability_before_cache_pop)
    assert 'monkeypatch.setattr(emission_finalize, "record_stage_snapshot"' in tp_src
    assert 'monkeypatch.setattr(feg, "record_stage_snapshot"' not in tp_src
    assert "import game.final_emission_gate as feg" not in inspect.getsource(tp_stage_diff)


def test_bj121_strict_social_build_patches_use_stack_seam_not_gate() -> None:
    """BJ-121: strict-social build monkeypatches target strict_social_stack, not gate re-exports."""
    import pathlib

    import tests.helpers.strict_social_harness as strict_social_harness

    harness_src = inspect.getsource(strict_social_harness.run_strict_social_motive_overclaim_gate_case)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in harness_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in harness_src

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    audited = [
        repo_root / "tests/test_fallback_behavior_gate.py",
        repo_root / "tests/test_scene_state_anchoring.py",
        repo_root / "tests/test_final_emission_boundary_convergence.py",
        repo_root / "tests/test_speaker_contract_enforcement.py",
        repo_root / "tests/test_social_exchange_emission.py",
        repo_root / "tests/test_prompt_context.py",
        repo_root / "tests/test_c4_narrative_mode_live_pipeline.py",
        repo_root / "tests/helpers/gate_equivalence_monkeypatch.py",
        repo_root / "tests/helpers/strict_social_harness.py",
    ]
    stale = 'monkeypatch.setattr(feg, "build_final_strict_social_response"'
    stale_module = 'monkeypatch.setattr(feg_module, "build_final_strict_social_response"'
    for path in audited:
        text = path.read_text(encoding="utf-8")
        assert stale not in text, f"{path.name} still patches gate build seam"
        assert stale_module not in text, f"{path.name} still patches gate build seam via feg_module"


def test_bj122_scene_state_anchoring_tests_use_ssa_owner_bindings_not_gate() -> None:
    """BJ-122: scene_state_anchoring tests patch/read SSA owner bindings, not removed gate re-exports."""
    import tests.test_scene_state_anchoring as scene_state_anchoring_tests

    module_src = inspect.getsource(scene_state_anchoring_tests)
    assert "import game.final_emission_gate as feg" not in module_src
    assert 'monkeypatch.setattr(feg, "_repair_location_opening"' not in module_src
    assert 'monkeypatch.setattr(feg, "validate_scene_state_anchoring"' not in module_src
    assert "feg._resolve_scene_state_anchor_contract" not in module_src
    assert "feg._merge_scene_state_anchor_meta" not in module_src

    repair_src = inspect.getsource(scene_state_anchoring_tests.test_scene_state_anchor_narrator_neutral_only_when_location_rebind_unavailable)
    validate_src = inspect.getsource(scene_state_anchoring_tests.test_validate_scene_state_anchoring_invoked_once_without_boundary_repair)
    resolve_src = inspect.getsource(scene_state_anchoring_tests.test_contract_resolution_from_gm_output_nested_paths)
    assert 'monkeypatch.setattr(scene_state_anchor_owner, "_repair_location_opening"' in repair_src
    assert 'monkeypatch.setattr(scene_state_anchor_owner, "validate_scene_state_anchoring"' in validate_src
    assert "scene_state_anchor_owner._resolve_scene_state_anchor_contract(" in resolve_src


def test_bj72_gate_context_initialization_delegator_removed() -> None:
    """BJ-72: gate context initialization delegator removed; apply_final_emission_gate calls owner directly."""
    assert not hasattr(feg, "_initialize_gate_execution_context")
    assert callable(getattr(gate_context, "initialize_gate_execution_context", None))


def test_bj72_apply_final_emission_gate_calls_gate_context_owner_directly() -> None:
    """BJ-72: gate orchestration calls gate_context owner directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "initialize_gate_execution_context(" in gate_src
    assert "_initialize_gate_execution_context" not in gate_src


def test_bj51_gate_interaction_continuity_public_reexports_locked() -> None:
    """BJ-51/BJ-76: gate re-exports IC owner entrypoints; no gate-private IC delegators remain."""
    import game.interaction_continuity as ic

    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation


def test_bj52_fallback_provenance_gate_wrappers_removed() -> None:
    """BJ-52/BN4: upstream fallback provenance wrappers removed; pregate containment routes via telemetry helper."""
    import game.fallback_provenance_debug as fpd
    import game.final_emission_finalize as fin
    import game.final_emission_gate_context as gc
    import game.final_emission_gate_preflight_telemetry as gpft

    assert not hasattr(feg, "_upstream_fallback_canonical_provenance")
    assert not hasattr(feg, "_apply_upstream_fallback_pregate_containment")
    assert not hasattr(feg, "_finalize_upstream_fallback_overwrite_containment")
    assert callable(getattr(fpd, "upstream_fallback_canonical_provenance", None))
    assert callable(getattr(fpd, "apply_upstream_fallback_pregate_containment", None))
    assert callable(getattr(fpd, "finalize_upstream_fallback_overwrite_containment", None))
    assert not hasattr(gc, "apply_upstream_fallback_pregate_containment")
    assert callable(getattr(gpft, "apply_gate_preflight_telemetry_and_containment", None))
    assert callable(getattr(fin, "finalize_upstream_fallback_overwrite_containment", None))


def test_bj53_referent_clarity_pre_finalize_gate_wrapper_removed() -> None:
    """BJ-53: referent pre-finalize wrapper removed; terminal pipeline owner calls repairs layer directly."""
    assert not hasattr(feg, "_apply_referent_clarity_pre_finalize")
    assert callable(getattr(terminal_pipeline, "_apply_referent_clarity_pre_finalize", None))


def test_bj54_narration_constraint_debug_merge_gate_wrapper_removed() -> None:
    """BJ-54: narration-constraint debug merge wrapper removed; terminal pipeline owner merges directly."""
    assert not hasattr(feg, "_merge_narration_constraint_debug_into_outputs")
    assert callable(getattr(terminal_pipeline, "_merge_narration_constraint_debug_into_outputs", None))


def test_bj55_gate_fem_text_fingerprint_helper_removed() -> None:
    """BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns _patch_fem_text_fingerprint."""
    assert not hasattr(feg, "_patch_gate_fem_text_fingerprint")
    assert callable(getattr(terminal_pipeline, "_patch_fem_text_fingerprint", None))


def test_bj56_scene_opening_finalize_delegators_removed() -> None:
    """BJ-56: scene-opening finalize wrappers removed; finalize owner and non_strict_stack call directly."""
    assert not hasattr(feg, "_patch_scene_opening_candidate_emission_debug")
    assert not hasattr(feg, "_reassert_scene_opening_accepted_candidate")
    assert callable(getattr(emission_finalize, "patch_scene_opening_candidate_emission_debug", None))
    assert callable(getattr(emission_finalize, "reassert_scene_opening_accepted_candidate", None))


def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_removed() -> None:
    """BJ-57: route-illegal strip wrapper removed; finalize owner owns strip helper."""
    assert not hasattr(feg, "_strip_appended_route_illegal_contamination_sentences")
    assert callable(getattr(emission_finalize, "strip_appended_route_illegal_contamination_sentences", None))


def test_bj58_contract_resolver_gate_delegators_removed() -> None:
    """BJ-58: contract resolver wrappers removed; tone/authority owners resolve directly."""
    assert not hasattr(feg, "_resolve_tone_escalation_contract")
    assert not hasattr(feg, "_resolve_narrative_authority_contract")
    assert callable(getattr(tone_escalation, "resolve_tone_escalation_contract", None))
    assert callable(getattr(narrative_authority, "resolve_narrative_authority_contract", None))


def test_bj59_dialogue_social_plan_gate_delegators_removed() -> None:
    """BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls dialogue_social_plan directly."""
    assert not hasattr(feg, "_enforce_dialogue_plan_invariant_on_strict_social")
    assert not hasattr(feg, "_strip_dialogue_from_text")
    assert not hasattr(feg, "_strict_social_line_matches_terminal_emission_pool")
    assert not hasattr(feg, "_is_bare_speech_attribution_shell_line")
    assert callable(getattr(dialogue_social_plan, "enforce_dialogue_plan_invariant_on_strict_social", None))
    assert callable(getattr(dialogue_social_plan, "strip_dialogue_from_text", None))
    assert callable(getattr(dialogue_social_plan, "strict_social_line_matches_terminal_emission_pool", None))
    assert callable(getattr(dialogue_social_plan, "is_bare_speech_attribution_shell_line", None))


def test_bj60_sealed_fallback_selector_gate_delegator_removed() -> None:
    """BJ-60: non-strict sealed selector wrapper removed; generic exit calls sealed_fallback owner."""
    assert not hasattr(feg, "_select_non_strict_replace_path_terminal_sealed_fallback_selection")
    assert callable(getattr(sealed_fallback, "select_non_strict_replace_path_terminal_sealed_fallback_selection", None))


def test_bj73_visibility_enforcement_gate_delegator_removed() -> None:
    """BJ-73: visibility enforcement gate delegator removed; terminal pipeline calls owner directly."""
    assert not hasattr(feg, "_apply_visibility_enforcement")
    assert callable(getattr(visibility_fallback, "apply_visibility_enforcement", None))


def test_bj73_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert "_apply_visibility_enforcement" not in tp_src


def test_bj74_n4_floor_seam_gate_delegator_removed() -> None:
    """BJ-74: N4 floor seam gate delegator removed; terminal pipeline calls owner directly."""
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")
    assert callable(getattr(acceptance_quality_gate, "apply_acceptance_quality_n4_floor_seam", None))


def test_bj74_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """BJ-74: terminal pipeline calls acceptance_quality owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src


def test_bj75_interaction_continuity_attach_gate_delegator_removed() -> None:
    """BJ-75: IC validation attach gate delegator removed; terminal pipeline calls owner directly."""
    import game.interaction_continuity as ic

    assert not hasattr(feg, "_attach_interaction_continuity_validation")
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))


def test_bj75_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "attach_interaction_continuity_validation(" in tp_src
    assert "feg._attach_interaction_continuity_validation" not in tp_src


def test_bj76_interaction_continuity_emission_step_gate_delegator_removed() -> None:
    """BJ-76: IC emission-step gate delegator removed; stacks call interaction_continuity owner directly."""
    import game.interaction_continuity as ic

    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))


def test_bj76_terminal_pipeline_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: terminal pipeline calls interaction_continuity emission step owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_interaction_continuity_emission_step(" in tp_src
    assert "feg._apply_interaction_continuity_emission_step" not in tp_src


def test_bj76_non_strict_stack_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: non_strict_stack calls interaction_continuity emission step owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "apply_interaction_continuity_emission_step(" in nss_src
    assert "feg._apply_interaction_continuity_emission_step" not in nss_src


def test_bj77_speaker_contract_gate_delegator_removed() -> None:
    """BJ-77: speaker-contract gate delegator removed; strict_social_stack calls owner directly."""
    import game.speaker_contract_enforcement as sce

    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert callable(getattr(sce, "enforce_emitted_speaker_with_contract", None))


def test_bj77_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "enforce_emitted_speaker_with_contract(" in ss_src
    assert "feg.enforce_emitted_speaker_with_contract" not in ss_src


def test_bj78_sync_eff_social_gate_reexport_removed() -> None:
    """BJ-78: strict-social sync no longer resolves through gate re-export."""
    import game.speaker_contract_enforcement as sce

    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert callable(getattr(sce, "_sync_eff_social_to_resolution", None))


def test_bj78_strict_social_stack_calls_sync_owner_directly() -> None:
    """BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_sync_eff_social_to_resolution(" in ss_src
    assert "feg._sync_eff_social_to_resolution" not in ss_src


def test_bj79_tone_escalation_layer_gate_delegator_removed() -> None:
    """BJ-79: tone escalation layer gate delegator removed; stacks call owner directly."""
    assert not hasattr(feg, "_apply_tone_escalation_layer")
    assert callable(getattr(tone_escalation, "apply_tone_escalation_layer", None))


def test_bj79_stacks_call_tone_escalation_owner_directly() -> None:
    """BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_tone_escalation_layer(" in nss_src
    assert "apply_tone_escalation_layer(" in ss_src
    assert "feg._apply_tone_escalation_layer" not in nss_src
    assert "feg._apply_tone_escalation_layer" not in ss_src


def test_bj80_narrative_authority_layer_gate_delegator_removed() -> None:
    """BJ-80: narrative authority layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_narrative_authority as narrative_authority

    assert not hasattr(feg, "_apply_narrative_authority_layer")
    assert callable(getattr(narrative_authority, "apply_narrative_authority_layer", None))


def test_bj80_stacks_call_narrative_authority_owner_directly() -> None:
    """BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_narrative_authority_layer(" in nss_src
    assert "apply_narrative_authority_layer(" in ss_src
    assert "feg._apply_narrative_authority_layer" not in nss_src
    assert "feg._apply_narrative_authority_layer" not in ss_src


def test_bj81_anti_railroading_layer_gate_delegator_removed() -> None:
    """BJ-81: anti-railroading layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_anti_railroading as anti_railroading

    assert not hasattr(feg, "_apply_anti_railroading_layer")
    assert callable(getattr(anti_railroading, "apply_anti_railroading_layer", None))


def test_bj81_stacks_call_anti_railroading_owner_directly() -> None:
    """BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_anti_railroading_layer(" in nss_src
    assert "apply_anti_railroading_layer(" in ss_src
    assert "feg._apply_anti_railroading_layer" not in nss_src
    assert "feg._apply_anti_railroading_layer" not in ss_src


def test_bj82_context_separation_layer_gate_delegator_removed() -> None:
    """BJ-82: context separation layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_context_separation as context_separation

    assert not hasattr(feg, "_apply_context_separation_layer")
    assert callable(getattr(context_separation, "apply_context_separation_layer", None))


def test_bj82_stacks_call_context_separation_owner_directly() -> None:
    """BJ-82: strict and non-strict stacks call context_separation owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_context_separation_layer(" in nss_src
    assert "apply_context_separation_layer(" in ss_src
    assert "feg._apply_context_separation_layer" not in nss_src
    assert "feg._apply_context_separation_layer" not in ss_src


def test_bj83_player_facing_narration_purity_layer_gate_delegator_removed() -> None:
    """BJ-83: narration purity layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_player_facing_narration_purity as narration_purity

    assert not hasattr(feg, "_apply_player_facing_narration_purity_layer")
    assert callable(getattr(narration_purity, "apply_player_facing_narration_purity_layer", None))


def test_bj83_stacks_call_narration_purity_owner_directly() -> None:
    """BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_player_facing_narration_purity_layer(" in nss_src
    assert "apply_player_facing_narration_purity_layer(" in ss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in nss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in ss_src


def test_bj84_answer_shape_primacy_layer_gate_delegator_removed() -> None:
    """BJ-84: answer-shape primacy layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_answer_shape_primacy as answer_shape_primacy

    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")
    assert callable(getattr(answer_shape_primacy, "apply_answer_shape_primacy_layer", None))


def test_bj84_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src


def test_bj85_scene_state_anchor_layer_gate_delegator_removed() -> None:
    """BJ-85: scene state anchor layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_scene_state_anchor as scene_state_anchor

    assert not hasattr(feg, "_apply_scene_state_anchor_layer")
    assert callable(getattr(scene_state_anchor, "apply_scene_state_anchor_layer", None))


def test_bj85_stacks_call_scene_state_anchor_owner_directly() -> None:
    """BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src


def test_bj47_merge_gate_layer_metas_into_fem_merge_order_locked(monkeypatch) -> None:
    """FEM layer-meta merges run in fixed post-AEP-second-pass order (Cycle AN2 / BJ-47)."""
    order: list[str] = []
    fem: dict[str, object] = {}
    layer_meta = {"marker": True}

    def _track(name: str, fn):
        def _wrapped(meta, dbg):
            order.append(name)
            fn(meta, dbg)

        return _wrapped

    monkeypatch.setattr(
        fem_assembly,
        "merge_response_type_meta",
        _track("response_type", fem_assembly.merge_response_type_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_answer_completeness_meta",
        _track("ac", fem_assembly._merge_answer_completeness_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_answer_exposition_plan_meta",
        _track("aep", fem_assembly._merge_answer_exposition_plan_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_response_delta_meta",
        _track("rd", fem_assembly._merge_response_delta_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_social_response_structure_meta",
        _track("srs", fem_assembly._merge_social_response_structure_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_narrative_authenticity_into_final_emission_meta",
        _track("nat", fem_assembly.merge_narrative_authenticity_into_final_emission_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_narrative_authority_meta",
        _track("na", fem_assembly.merge_narrative_authority_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_tone_escalation_meta",
        _track("te", fem_assembly.merge_tone_escalation_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_anti_railroading_meta",
        _track("ar", fem_assembly.merge_anti_railroading_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_context_separation_meta",
        _track("cs", fem_assembly.merge_context_separation_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_player_facing_narration_purity_meta",
        _track("purity", fem_assembly.merge_player_facing_narration_purity_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_answer_shape_primacy_meta",
        _track("asp", fem_assembly.merge_answer_shape_primacy_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_scene_state_anchor_meta",
        _track("ssa", fem_assembly._merge_scene_state_anchor_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_fallback_behavior_meta",
        _track("fb", fem_assembly._merge_fallback_behavior_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_fast_fallback_neutral_composition_meta",
        _track("ffnc", fem_assembly._merge_fast_fallback_neutral_composition_meta),
    )

    fem_assembly.merge_gate_layer_metas_into_fem(
        fem,
        response_type_debug=layer_meta,
        ac_layer_meta=layer_meta,
        aep_layer_meta=layer_meta,
        rd_layer_meta=layer_meta,
        srs_layer_meta=layer_meta,
        nat_layer_meta=layer_meta,
        na_layer_meta=layer_meta,
        te_layer_meta=layer_meta,
        ar_layer_meta=layer_meta,
        cs_layer_meta=layer_meta,
        purity_layer_meta=layer_meta,
        asp_layer_meta=layer_meta,
        ssa_layer_meta=layer_meta,
        fb_layer_meta=layer_meta,
        ffnc_layer_meta=layer_meta,
    )
    assert order == [
        "response_type",
        "ac",
        "aep",
        "rd",
        "srs",
        "nat",
        "na",
        "te",
        "ar",
        "cs",
        "purity",
        "asp",
        "ssa",
        "fb",
        "ffnc",
    ]

    order.clear()
    fem_assembly.merge_gate_layer_metas_into_fem(
        fem,
        response_type_debug=layer_meta,
        ac_layer_meta=layer_meta,
        aep_layer_meta=layer_meta,
        rd_layer_meta=layer_meta,
        srs_layer_meta=layer_meta,
        nat_layer_meta=layer_meta,
        na_layer_meta=layer_meta,
        te_layer_meta=layer_meta,
        ar_layer_meta=layer_meta,
        cs_layer_meta=layer_meta,
        purity_layer_meta=layer_meta,
        asp_layer_meta=layer_meta,
        ssa_layer_meta=layer_meta,
        fb_layer_meta=layer_meta,
        ffnc_layer_meta=layer_meta,
        include_fast_fallback_neutral_composition=False,
    )
    assert order == [
        "response_type",
        "ac",
        "aep",
        "rd",
        "srs",
        "nat",
        "na",
        "te",
        "ar",
        "cs",
        "purity",
        "asp",
        "ssa",
        "fb",
    ]


def test_bj129_gate_module_thin_boundary_source_shape_locked() -> None:
    """BJ-129: gate owner rejects regrowth beyond orchestration wiring + documented live seams."""
    from tests.helpers.gate_thin_boundary_locks import (
        BJ128_LIVE_GATE_SEAM_SYMBOLS,
        BJ129_ALLOWED_GATE_IMPORT_MODULES,
        assert_gate_bj129_thin_boundary_shape,
        gate_import_modules,
        module_level_defs,
    )

    assert_gate_bj129_thin_boundary_shape(feg)

    gate_src = inspect.getsource(feg)
    assert gate_import_modules(gate_src) == BJ129_ALLOWED_GATE_IMPORT_MODULES
    assert module_level_defs(gate_src) == ("apply_final_emission_gate",)

    for name in BJ128_LIVE_GATE_SEAM_SYMBOLS:
        assert hasattr(feg, name), f"gate missing documented live seam: {name!r}"
