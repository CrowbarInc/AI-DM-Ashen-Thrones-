"""Historical BJ thin-boundary/delegator/re-export regression locks for final emission gate.

This file owns mostly static ``inspect``/source-shape coverage that guards against
gate-module regrowth: removed delegators, collapsed re-exports, and harness patch seams.

Behavioral orchestration tests (layer order, selector snapshots, N4 placement) remain in
``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import inspect

import pytest

from tests.helpers import gate_delegator_governance as gdg
from tests.helpers.gate_delegator_governance import (
    FEM_ASSEMBLY,
    FINALIZE,
    GATE,
    GATE_CONTEXT,
    GENERIC_EXIT,
    NARRATION_CONSTRAINT_DEBUG,
    REPAIRS,
    FAST_FALLBACK,
    ACCEPTANCE_QUALITY,
    META,
    TEXT,
    TONE_ESCALATION,
    NARRATIVE_AUTHORITY,
    ANTI_RAILROADING,
    CONTEXT_SEPARATION,
    NARRATION_PURITY,
    ANSWER_SHAPE_PRIMACY,
    SCENE_STATE_ANCHOR,
    DIALOGUE_SOCIAL_PLAN,
    SCENE_EMIT_INTEGRITY,
    PASSIVE_SCENE_PRESSURE,
    NARRATIVE_MODE_OUTPUT,
    INTERACTION_CONTINUITY,
    SPEAKER_CONTRACT,
    SOCIAL_EXCHANGE,
    ANTI_RESET,
    DIEGETIC_FALLBACK,
    BOUNDARY_CONTRACT,
    STAGE_DIFF,
    FALLBACK_PROVENANCE,
    PREFLIGHT_TELEMETRY,
    NON_STRICT_STACK,
    OPENING_FALLBACK,
    RESPONSE_TYPE,
    SEALED_FALLBACK,
    STRICT_SOCIAL_STACK,
    TERMINAL_PIPELINE,
    VISIBILITY_FALLBACK,
    assert_gate_lacks,
    assert_owner_callable,
    function_source,
    gate_module,
    load_game_module,
    module_source,
    owner_callable,
)

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
    emission_text = load_game_module("game.final_emission_text")
    emission_meta = load_game_module("game.final_emission_meta")
    finalize = load_game_module(FINALIZE)
    pre = emission_text._normalize_text(selector)
    finalized = finalize.finalize_emission_output(out, pre_gate_text=pre, fast_path=True)
    pft = (finalized.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
    assert "internal_state" in finalized
    fem = emission_meta.read_final_emission_meta_dict(finalized) or {}
    assert fem.get("finalize_route_illegal_strip_applied") is True
    lineage = fem.get("final_emission_mutation_lineage")
    assert "finalize_route_illegal_strip" in lineage
    assert "finalize_packaging" in lineage


def test_bj69_terminal_finalize_fast_path_gate_delegators_removed() -> None:
    """BJ-69: terminal pipeline, finalize, and fast-path gate delegators removed; exit stacks call owners."""
    assert_gate_lacks("_run_gate_terminal_enforcement_pipeline")
    assert_gate_lacks("_finalize_emission_output")
    assert_gate_lacks("_final_emission_fast_path_eligible")
    assert_owner_callable(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert_owner_callable(FINALIZE, "finalize_emission_output")
    assert_owner_callable(FINALIZE, "final_emission_fast_path_eligible")


def test_bj69_exit_stacks_terminal_finalize_fast_path_call_owners_directly() -> None:
    """BJ-69: generic and strict-social exit stacks call terminal/finalize owners directly."""
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    for src in (ge_accept_src, ge_replace_src, ss_src):
        assert "terminal_pipeline.run_gate_terminal_enforcement_pipeline" in src
        assert "emission_finalize.finalize_emission_output" in src
        assert "emission_finalize.final_emission_fast_path_eligible" in src
        assert "feg._run_gate_terminal_enforcement_pipeline" not in src
        assert "feg._finalize_emission_output" not in src
        assert "feg._final_emission_fast_path_eligible" not in src


def test_bj71_non_strict_layer_stack_gate_delegator_removed() -> None:
    """BJ-71: non-strict layer stack gate delegator removed; apply_final_emission_gate calls owner directly."""
    assert_gate_lacks("_run_non_strict_layer_stack")
    assert_owner_callable(NON_STRICT_STACK, "run_non_strict_layer_stack")


def test_bj71_apply_final_emission_gate_calls_non_strict_stack_owner_directly() -> None:
    """BJ-71: gate orchestration calls non_strict_stack owner directly."""
    gate_src = function_source(GATE, "apply_final_emission_gate")
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src


def test_bj70_exit_stack_gate_delegators_removed() -> None:
    """BJ-70: exit/stack gate delegators removed; apply_final_emission_gate calls owners directly."""
    assert_gate_lacks("_run_strict_social_composition_trunk")
    assert_gate_lacks("_run_generic_accept_exit")
    assert_gate_lacks("_run_generic_replace_exit")
    assert_owner_callable(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert_owner_callable(GENERIC_EXIT, "run_generic_accept_exit")
    assert_owner_callable(GENERIC_EXIT, "run_generic_replace_exit")


def test_bj70_apply_final_emission_gate_calls_exit_stack_owners_directly() -> None:
    """BJ-70: gate orchestration calls generic/strict-social exit owners directly."""
    gate_src = function_source(GATE, "apply_final_emission_gate")
    assert "run_strict_social_composition_trunk(" in gate_src
    assert "run_generic_accept_exit(" in gate_src
    assert "run_generic_replace_exit(" in gate_src
    assert "_run_strict_social_composition_trunk" not in gate_src
    assert "_run_generic_accept_exit" not in gate_src
    assert "_run_generic_replace_exit" not in gate_src


def test_bj63_fem_assembly_gate_delegators_collapsed() -> None:
    """Cycle BJ-63: FEM assembly gate delegators removed; exit stacks call owner directly."""
    for name in (
        "_build_gate_accept_fem_base",
        "_build_gate_replace_fem_base",
        "_merge_gate_layer_metas_into_fem",
    ):
        assert_gate_lacks(name)
    for name in (
        "build_gate_accept_fem_base",
        "build_gate_replace_fem_base",
        "merge_gate_layer_metas_into_fem",
    ):
        assert_owner_callable(FEM_ASSEMBLY, name)


def test_bj64_opening_rt_accept_path_promotion_gate_alias_removed() -> None:
    """BJ-64: opening RT accept-path promotion alias removed; non_strict_stack calls owner."""
    assert_gate_lacks("_scene_opening_rt_contract_accept_path_promotes_candidate")
    src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    assert "opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate" in src
    assert "_scene_opening_rt_contract_accept_path_promotes_candidate" not in src


def test_bj65_opening_upstream_prepare_observability_merge_gate_alias_removed() -> None:
    """BJ-65: opening upstream-prepare observability merge alias removed; stacks call response_type owner."""
    assert_gate_lacks("_merge_opening_upstream_prepare_attach_observability_into_response_type_debug")
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    marker = "response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in nss_src
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in ss_src


def test_bj66_dead_opening_fallback_gate_imports_removed() -> None:
    """BJ-66: gate no longer re-exports unused opening-fallback normalization helpers."""
    gate_source = module_source(GATE)
    assert "final_emission_opening_fallback" not in gate_source
    assert_gate_lacks("_gm_output_normalized_for_opening_context")
    assert_gate_lacks("_opening_curated_facts_schema_ok")


def test_bj67_stacks_response_type_enforcement_calls_owner_directly() -> None:
    """BJ-67: stacks call response_type owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    marker = "response_type.enforce_response_type_contract"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._enforce_response_type_contract" not in nss_src
    assert "feg._enforce_response_type_contract" not in ss_src


def test_bj68_response_type_enforcement_gate_delegator_removed() -> None:
    """BJ-68: gate no longer re-exports enforce_response_type_contract; harnesses call owner."""
    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness

    assert_gate_lacks("_enforce_response_type_contract")
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert "response_type.enforce_response_type_contract" in ob_src
    assert "feg._enforce_response_type_contract" not in ob_src
    assert "final_emission_response_type" in smoke_fn_src
    assert "final_emission_gate" not in smoke_fn_src
    assert_owner_callable(RESPONSE_TYPE, "enforce_response_type_contract")


def test_bj86_fast_fallback_neutral_composition_layer_gate_delegator_removed() -> None:
    """BJ-86: FFNC layer gate delegator removed; stacks call owner directly."""
    assert_gate_lacks("_apply_fast_fallback_neutral_composition_layer")
    assert_owner_callable(FAST_FALLBACK, "apply_fast_fallback_neutral_composition_layer")


def test_bj86_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src


def test_bj87_answer_completeness_layer_gate_reexport_removed() -> None:
    """BJ-87: answer completeness layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_answer_completeness_layer")


def test_bj87_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_apply_answer_completeness_layer(" in nss_src
    assert "feg._apply_answer_completeness_layer" not in nss_src
    assert "emission_repairs._apply_answer_completeness_layer(" in ss_src
    assert "feg._apply_answer_completeness_layer" not in ss_src


def test_bj88_answer_exposition_plan_layer_gate_reexport_removed() -> None:
    """BJ-88: answer exposition plan layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_answer_exposition_plan_layer")


def test_bj88_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """BJ-88: stacks call final_emission_repairs answer exposition plan directly (3 strict-social sites)."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = module_source(STRICT_SOCIAL_STACK)
    assert "_apply_answer_exposition_plan_layer(" in nss_src
    assert "feg._apply_answer_exposition_plan_layer" not in nss_src
    assert ss_src.count("emission_repairs._apply_answer_exposition_plan_layer(") == 3
    assert "feg._apply_answer_exposition_plan_layer" not in ss_src


def test_bj89_response_delta_layer_gate_reexport_removed() -> None:
    """BJ-89: response delta layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_response_delta_layer")


def test_bj89_stacks_call_response_delta_repairs_owner_directly() -> None:
    """BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_apply_response_delta_layer(" in nss_src
    assert "feg._apply_response_delta_layer" not in nss_src
    assert "emission_repairs._apply_response_delta_layer(" in ss_src
    assert "feg._apply_response_delta_layer" not in ss_src


def test_bj90_social_response_structure_layer_gate_reexport_removed() -> None:
    """BJ-90: social response structure layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_social_response_structure_layer")


def test_bj90_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_apply_social_response_structure_layer(" in nss_src
    assert "feg._apply_social_response_structure_layer" not in nss_src
    assert "emission_repairs._apply_social_response_structure_layer(" in ss_src
    assert "feg._apply_social_response_structure_layer" not in ss_src


def test_bj91_narrative_authenticity_layer_gate_reexport_removed() -> None:
    """BJ-91: narrative authenticity layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_narrative_authenticity_layer")


def test_bj91_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_apply_narrative_authenticity_layer(" in nss_src
    assert "feg._apply_narrative_authenticity_layer" not in nss_src
    assert "emission_repairs._apply_narrative_authenticity_layer(" in ss_src
    assert "feg._apply_narrative_authenticity_layer" not in ss_src


def test_bj92_fallback_behavior_layer_gate_reexport_removed() -> None:
    """BJ-92: fallback behavior layer no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "_apply_fallback_behavior_layer")


def test_bj92_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "_apply_fallback_behavior_layer(" in nss_src
    assert "feg._apply_fallback_behavior_layer" not in nss_src
    assert "_apply_fallback_behavior_layer(" in tp_src
    assert "feg._apply_fallback_behavior_layer" not in tp_src


def test_bj93_fallback_behavior_debug_merge_gate_reexports_removed() -> None:
    """BJ-93: fallback behavior debug/meta merge helpers no longer re-exported through gate."""
    assert_owner_callable(REPAIRS, "merge_fallback_behavior_into_emission_debug")
    assert_owner_callable(REPAIRS, "_merge_fallback_behavior_meta")


def test_bj93_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """BJ-93: non_strict_stack and terminal_pipeline call repairs fallback debug/meta merge directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in nss_src
    assert "merge_fallback_behavior_into_emission_debug(" in tp_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in tp_src
    assert "_merge_fallback_behavior_meta(" in tp_src
    assert "feg._merge_fallback_behavior_meta" not in tp_src


def test_bj94_conversational_memory_inspection_debug_merge_gate_reexport_removed() -> None:
    """BJ-94: conversational memory inspection debug merge no longer re-exported through gate."""
    assert_owner_callable(
        REPAIRS,
        "merge_conversational_memory_inspection_into_emission_debug",
    )


def test_bj94_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BU2-A: conversational memory debug merge lives on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "merge_conversational_memory_inspection_into_emission_debug(" not in src
    assert "merge_conversational_memory_inspection_into_emission_debug(" in fa_src


def test_bj95_scene_state_anchor_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-95: scene state anchor emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(SCENE_STATE_ANCHOR, "_merge_scene_state_anchor_into_emission_debug")


def test_bj95_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BU2-A: scene_state_anchor debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_scene_state_anchor_into_emission_debug(" not in src
    assert "_merge_scene_state_anchor_into_emission_debug(" in fa_src


def test_bj96_tone_escalation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-96: tone escalation emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(TONE_ESCALATION, "merge_tone_escalation_into_emission_debug")


def test_bj96_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: tone_escalation debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_tone_escalation_into_emission_debug(" not in src
    assert "merge_tone_escalation_into_emission_debug(" in fa_src


def test_bj97_narrative_authority_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-97: narrative authority emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(NARRATIVE_AUTHORITY, "merge_narrative_authority_into_emission_debug")


def test_bj97_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narrative_authority debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_narrative_authority_into_emission_debug(" not in src
    assert "merge_narrative_authority_into_emission_debug(" in fa_src


def test_bj98_anti_railroading_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-98: anti-railroading emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(ANTI_RAILROADING, "merge_anti_railroading_into_emission_debug")


def test_bj98_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BU2-A: anti_railroading debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_anti_railroading_into_emission_debug(" not in src
    assert "merge_anti_railroading_into_emission_debug(" in fa_src


def test_bj99_context_separation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-99: context separation emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(CONTEXT_SEPARATION, "merge_context_separation_into_emission_debug")


def test_bj99_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: context_separation debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_context_separation_into_emission_debug(" not in src
    assert "merge_context_separation_into_emission_debug(" in fa_src


def test_bj100_narration_purity_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-100: narration purity emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(NARRATION_PURITY, "merge_player_facing_narration_purity_into_emission_debug")


def test_bj100_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narration_purity debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_player_facing_narration_purity_into_emission_debug(" not in src
    assert "merge_player_facing_narration_purity_into_emission_debug(" in fa_src


def test_bj101_answer_shape_primacy_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-101: answer-shape primacy emission_debug merge no longer re-exported through gate."""
    assert_owner_callable(ANSWER_SHAPE_PRIMACY, "merge_answer_shape_primacy_into_emission_debug")


def test_bj101_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BU2-A: answer_shape_primacy debug merge consolidated on fem_assembly pre-terminal helper."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    fa_src = function_source(FEM_ASSEMBLY, "merge_pre_terminal_layer_debug")
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_answer_shape_primacy_into_emission_debug(" not in src
    assert "merge_answer_shape_primacy_into_emission_debug(" in fa_src


def test_bj102_tone_escalation_pregate_flag_gate_reexport_removed() -> None:
    """BJ-102: non-hostile escalation pregate flag no longer re-exported through gate."""
    assert_owner_callable(TONE_ESCALATION, "flag_non_hostile_escalation_from_writer_pregate")


def test_bj102_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "flag_non_hostile_escalation_from_writer_pregate(" in ss_src
    assert "feg._flag_non_hostile_escalation_from_writer_pregate" not in ss_src


def test_bj103_scene_emit_integrity_assessment_gate_reexport_removed() -> None:
    """BJ-103: scene emit integrity assessment no longer re-exported through gate."""
    assert_owner_callable(SCENE_EMIT_INTEGRITY, "_compute_scene_emit_integrity_assessment")


def test_bj103_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_compute_scene_emit_integrity_assessment(" in nss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in nss_src
    assert "_compute_scene_emit_integrity_assessment(" in ss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in ss_src


def test_bj104_passive_scene_pressure_due_check_gate_reexport_removed() -> None:
    """BJ-104: passive scene pressure due-check no longer re-exported through gate."""
    assert_owner_callable(PASSIVE_SCENE_PRESSURE, "_passive_scene_pressure_due_for_fallback")


def test_bj104_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    assert "_passive_scene_pressure_due_for_fallback(" in nss_src
    assert "feg._passive_scene_pressure_due_for_fallback" not in nss_src


def test_bj105_narrative_mode_output_assessment_gate_reexport_removed() -> None:
    """BJ-105: narrative mode output legality assessment no longer re-exported through gate."""
    assert_owner_callable(NARRATIVE_MODE_OUTPUT, "_narrative_mode_output_legality_assessment")


def test_bj105_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    assert "_narrative_mode_output_legality_assessment(" in nss_src
    assert "feg._narrative_mode_output_legality_assessment" not in nss_src


def test_bj106_response_type_decision_payload_gate_reexport_removed() -> None:
    """BJ-106: response_type decision payload no longer re-exported through gate."""
    assert_owner_callable(META, "response_type_decision_payload")


def test_bj106_callers_use_response_type_decision_payload_owner_directly() -> None:
    """BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "response_type_decision_payload(" in ss_src
    assert "feg._response_type_decision_payload" not in ss_src
    assert "response_type_decision_payload(" in ge_accept_src
    assert "feg._response_type_decision_payload" not in ge_accept_src
    assert "response_type_decision_payload(" in ge_replace_src
    assert "feg._response_type_decision_payload" not in ge_replace_src


def test_bj107_infer_accept_path_final_emitted_source_gate_reexport_removed() -> None:
    """BJ-107: accept-path final_emitted_source inference no longer re-exported through gate."""
    assert_owner_callable(META, "infer_accept_path_final_emitted_source")


def test_bj107_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    assert "infer_accept_path_final_emitted_source(" in ss_src
    assert "feg.infer_accept_path_final_emitted_source" not in ss_src
    assert "infer_accept_path_final_emitted_source(" in ge_accept_src
    assert "feg.infer_accept_path_final_emitted_source" not in ge_accept_src


def test_bj108_opening_fallback_projection_gate_reexports_removed() -> None:
    """BJ-108: opening fallback projection helpers no longer re-exported through gate."""
    emission_meta = load_game_module(META)
    assert_gate_lacks("apply_opening_fallback_projection_fields")
    assert_gate_lacks("OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")
    assert_owner_callable(META, "apply_opening_fallback_projection_fields")
    assert hasattr(emission_meta, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")


def test_bj108_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "apply_opening_fallback_projection_fields(" in ge_replace_src
    assert "feg.apply_opening_fallback_projection_fields" not in ge_replace_src
    assert "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" in ge_replace_src
    assert "feg.OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" not in ge_replace_src


def test_bj109_final_emission_meta_key_gate_reexport_removed() -> None:
    """BJ-109: FINAL_EMISSION_META_KEY no longer re-exported through gate."""
    emission_meta = load_game_module(META)
    assert_gate_lacks("FINAL_EMISSION_META_KEY")
    assert hasattr(emission_meta, "FINAL_EMISSION_META_KEY")
    assert emission_meta.FINAL_EMISSION_META_KEY == "_final_emission_meta"


def test_bj109_callers_use_final_emission_meta_key_owner_directly() -> None:
    """BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "FINAL_EMISSION_META_KEY" in ss_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ss_src
    assert "FINAL_EMISSION_META_KEY" in ge_accept_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_accept_src
    assert "FINAL_EMISSION_META_KEY" in ge_replace_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_replace_src


def test_bj110_assert_final_emission_mutation_allowed_gate_reexport_removed() -> None:
    """BJ-110: boundary mutation assertion no longer re-exported through gate."""
    assert_owner_callable(BOUNDARY_CONTRACT, "assert_final_emission_mutation_allowed")


def test_bj110_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "assert_final_emission_mutation_allowed(" in ge_replace_src
    assert "feg.assert_final_emission_mutation_allowed" not in ge_replace_src


def test_bj111_normalize_text_gate_reexport_removed() -> None:
    """BJ-111: _normalize_text no longer re-exported through gate."""
    assert_owner_callable(TEXT, "_normalize_text")


def test_bj111_callers_use_normalize_text_owner_directly() -> None:
    """BJ-111: stack/exit callers use final_emission_text._normalize_text directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
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
    assert_owner_callable(TEXT, "_normalize_text_preserve_paragraphs")


def test_bj112_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """BJ-112: strict_social_stack calls final_emission_text._normalize_text_preserve_paragraphs directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_normalize_text_preserve_paragraphs(" in ss_src
    assert "feg._normalize_text_preserve_paragraphs" not in ss_src


def test_bj113_diegetic_classified_fallback_meta_gate_reexport_removed() -> None:
    """BJ-113: diegetic_classified_fallback_meta no longer re-exported through gate."""
    assert_owner_callable(DIEGETIC_FALLBACK, "fallback_template_metadata")


def test_bj113_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "diegetic_classified_fallback_meta(" in ge_replace_src
    assert "feg.diegetic_classified_fallback_meta" not in ge_replace_src


def test_bj114_anti_reset_suppresses_intro_style_fallbacks_gate_reexport_removed() -> None:
    """BJ-114: anti_reset_suppresses_intro_style_fallbacks no longer re-exported through gate."""
    assert_owner_callable(ANTI_RESET, "anti_reset_suppresses_intro_style_fallbacks")


def test_bj114_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    assert "anti_reset_suppresses_intro_style_fallbacks(" in ge_replace_src
    assert "feg.anti_reset_suppresses_intro_style_fallbacks" not in ge_replace_src


def test_bj115_log_final_emission_logging_gate_reexports_removed() -> None:
    """BJ-115: final emission logging helpers no longer re-exported through gate."""
    assert_owner_callable(SOCIAL_EXCHANGE, "log_final_emission_decision")
    assert_owner_callable(SOCIAL_EXCHANGE, "log_final_emission_trace")


def test_bj115_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    ge_accept_src = function_source(GENERIC_EXIT, "run_generic_accept_exit")
    ge_replace_src = function_source(GENERIC_EXIT, "run_generic_replace_exit")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
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
    assert_owner_callable(SOCIAL_EXCHANGE, "build_final_strict_social_response")
    assert_owner_callable(SOCIAL_EXCHANGE, "minimal_social_emergency_fallback_line")
    assert_owner_callable(SOCIAL_EXCHANGE, "strict_social_deterministic_fallback_family_token")


def test_bj116_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "build_final_strict_social_response(" in ss_src
    assert "minimal_social_emergency_fallback_line(" in ss_src
    assert "strict_social_deterministic_fallback_family_token(" in ss_src
    assert "feg.build_final_strict_social_response" not in ss_src
    assert "feg.minimal_social_emergency_fallback_line" not in ss_src
    assert "feg.strict_social_deterministic_fallback_family_token" not in ss_src


def test_bj117_telemetry_provenance_gate_reexports_removed() -> None:
    """BJ-117: telemetry/provenance helpers no longer re-exported through gate."""
    assert_owner_callable(STAGE_DIFF, "record_stage_snapshot")
    assert_owner_callable(FALLBACK_PROVENANCE, "realign_fallback_provenance_selector_to_current_text")


def test_bj117_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "record_stage_snapshot(" in ss_src
    assert "realign_fallback_provenance_selector_to_current_text(" in ss_src
    assert "feg.record_stage_snapshot" not in ss_src
    assert "feg.realign_fallback_provenance_selector_to_current_text" not in ss_src


def test_bj118_should_replace_candidate_intro_fallback_gate_reexport_removed() -> None:
    """BJ-118: should_replace_candidate_intro_fallback no longer re-exported through gate."""
    assert_owner_callable(ANTI_RESET, "should_replace_candidate_intro_fallback")


def test_bj119_stage_diff_telemetry_gate_reexports_removed() -> None:
    """BJ-119: stage_diff_telemetry helpers no longer re-exported through gate."""
    assert_owner_callable(STAGE_DIFF, "diff_turn_stage")
    assert_owner_callable(STAGE_DIFF, "record_stage_transition")
    assert_owner_callable(STAGE_DIFF, "snapshot_turn_stage")


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
    assert_gate_lacks("_initialize_gate_execution_context")
    assert_owner_callable(GATE_CONTEXT, "initialize_gate_execution_context")


def test_bj72_apply_final_emission_gate_calls_gate_context_owner_directly() -> None:
    """BJ-72: gate orchestration calls gate_context owner directly."""
    gate_src = function_source(GATE, "apply_final_emission_gate")
    assert "initialize_gate_execution_context(" in gate_src
    assert "_initialize_gate_execution_context" not in gate_src


def test_bj51_gate_interaction_continuity_public_reexports_locked() -> None:
    """BJ-51/BJ-76: gate re-exports IC owner entrypoints; no gate-private IC delegators remain."""
    ic = load_game_module(INTERACTION_CONTINUITY)
    feg = gate_module()
    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation


def test_bj52_fallback_provenance_gate_wrappers_removed() -> None:
    """BJ-52/BN4: upstream fallback provenance wrappers removed; pregate containment routes via telemetry helper."""
    gc = load_game_module(GATE_CONTEXT)
    assert_gate_lacks("_upstream_fallback_canonical_provenance")
    assert_gate_lacks("_apply_upstream_fallback_pregate_containment")
    assert_gate_lacks("_finalize_upstream_fallback_overwrite_containment")
    assert_owner_callable(FALLBACK_PROVENANCE, "upstream_fallback_canonical_provenance")
    assert_owner_callable(FALLBACK_PROVENANCE, "apply_upstream_fallback_pregate_containment")
    assert_owner_callable(FALLBACK_PROVENANCE, "finalize_upstream_fallback_overwrite_containment")
    assert not hasattr(gc, "apply_upstream_fallback_pregate_containment")
    assert_owner_callable(PREFLIGHT_TELEMETRY, "apply_gate_preflight_telemetry_and_containment")
    assert_owner_callable(FINALIZE, "finalize_upstream_fallback_overwrite_containment")


def test_bj53_referent_clarity_pre_finalize_gate_wrapper_removed() -> None:
    """BJ-53: referent pre-finalize wrapper removed; terminal pipeline owner calls repairs layer directly."""
    assert_gate_lacks("_apply_referent_clarity_pre_finalize")
    assert_owner_callable(TERMINAL_PIPELINE, "_apply_referent_clarity_pre_finalize")


def test_bj54_narration_constraint_debug_merge_gate_wrapper_removed() -> None:
    """BU2-B: narration-constraint debug merge owned by final_emission_narration_constraint_debug."""
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert_gate_lacks("_merge_narration_constraint_debug_into_outputs")
    assert not hasattr(load_game_module(TERMINAL_PIPELINE), "_merge_narration_constraint_debug_into_outputs")
    assert "merge_narration_constraint_debug_into_outputs(" in tp_src
    assert_owner_callable(NARRATION_CONSTRAINT_DEBUG, "merge_narration_constraint_debug_into_outputs")


def test_bj55_gate_fem_text_fingerprint_helper_removed() -> None:
    """BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns _patch_fem_text_fingerprint."""
    assert_gate_lacks("_patch_gate_fem_text_fingerprint")
    assert_owner_callable(TERMINAL_PIPELINE, "_patch_fem_text_fingerprint")


def test_bj56_scene_opening_finalize_delegators_removed() -> None:
    """BU2-C: scene-opening accept debug owned by final_emission_opening_fallback."""
    opening_fallback = load_game_module(OPENING_FALLBACK)
    finalize = load_game_module(FINALIZE)
    assert_gate_lacks("_patch_scene_opening_candidate_emission_debug")
    assert_gate_lacks("_reassert_scene_opening_accepted_candidate")
    assert opening_fallback.patch_scene_opening_candidate_emission_debug.__module__ == (
        "game.final_emission_opening_fallback"
    )
    assert opening_fallback.reassert_scene_opening_accepted_candidate.__module__ == (
        "game.final_emission_opening_fallback"
    )
    assert getattr(finalize, "reassert_scene_opening_accepted_candidate", None) is (
        opening_fallback.reassert_scene_opening_accepted_candidate
    )


def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_removed() -> None:
    """BJ-57: route-illegal strip wrapper removed; finalize owner owns strip helper."""
    assert_gate_lacks("_strip_appended_route_illegal_contamination_sentences")
    assert_owner_callable(FINALIZE, "strip_appended_route_illegal_contamination_sentences")


def test_bj58_contract_resolver_gate_delegators_removed() -> None:
    """BJ-58: contract resolver wrappers removed; tone/authority owners resolve directly."""
    assert_gate_lacks("_resolve_tone_escalation_contract")
    assert_gate_lacks("_resolve_narrative_authority_contract")
    assert_owner_callable(TONE_ESCALATION, "resolve_tone_escalation_contract")
    assert_owner_callable(NARRATIVE_AUTHORITY, "resolve_narrative_authority_contract")


def test_bj59_dialogue_social_plan_gate_delegators_removed() -> None:
    """BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls dialogue_social_plan directly."""
    assert_gate_lacks("_enforce_dialogue_plan_invariant_on_strict_social")
    assert_gate_lacks("_strip_dialogue_from_text")
    assert_gate_lacks("_strict_social_line_matches_terminal_emission_pool")
    assert_gate_lacks("_is_bare_speech_attribution_shell_line")
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, "enforce_dialogue_plan_invariant_on_strict_social")
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, "strip_dialogue_from_text")
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, "strict_social_line_matches_terminal_emission_pool")
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, "is_bare_speech_attribution_shell_line")


def test_bj60_sealed_fallback_selector_gate_delegator_removed() -> None:
    """BJ-60: non-strict sealed selector wrapper removed; generic exit calls sealed_fallback owner."""
    assert_gate_lacks("_select_non_strict_replace_path_terminal_sealed_fallback_selection")
    assert_owner_callable(SEALED_FALLBACK, "select_non_strict_replace_path_terminal_sealed_fallback_selection")


def test_bj73_visibility_enforcement_gate_delegator_removed() -> None:
    """BJ-73: visibility enforcement gate delegator removed; terminal pipeline calls owner directly."""
    assert_gate_lacks("_apply_visibility_enforcement")
    assert_owner_callable(VISIBILITY_FALLBACK, "apply_visibility_enforcement")


def test_bj73_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert "_apply_visibility_enforcement" not in tp_src


def test_bj74_n4_floor_seam_gate_delegator_removed() -> None:
    """BJ-74: N4 floor seam gate delegator removed; terminal pipeline calls owner directly."""
    assert_gate_lacks("_apply_acceptance_quality_n4_floor_seam")
    assert_owner_callable(ACCEPTANCE_QUALITY, "apply_acceptance_quality_n4_floor_seam")


def test_bj74_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """BJ-74: terminal pipeline calls acceptance_quality owner directly."""
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src


def test_bj75_interaction_continuity_attach_gate_delegator_removed() -> None:
    """BJ-75: IC validation attach gate delegator removed; terminal pipeline calls owner directly."""
    assert_owner_callable(INTERACTION_CONTINUITY, "attach_interaction_continuity_validation")


def test_bj75_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "attach_interaction_continuity_validation(" in tp_src
    assert "feg._attach_interaction_continuity_validation" not in tp_src


def test_bj76_interaction_continuity_emission_step_gate_delegator_removed() -> None:
    """BJ-76: IC emission-step gate delegator removed; stacks call interaction_continuity owner directly."""
    assert_owner_callable(INTERACTION_CONTINUITY, "apply_interaction_continuity_emission_step")


def test_bj76_terminal_pipeline_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: terminal pipeline calls interaction_continuity emission step owner directly."""
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "apply_interaction_continuity_emission_step(" in tp_src
    assert "feg._apply_interaction_continuity_emission_step" not in tp_src


def test_bj76_non_strict_stack_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: non_strict_stack calls interaction_continuity emission step owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    assert "apply_interaction_continuity_emission_step(" in nss_src
    assert "feg._apply_interaction_continuity_emission_step" not in nss_src


def test_bj77_speaker_contract_gate_delegator_removed() -> None:
    """BJ-77: speaker-contract gate delegator removed; strict_social_stack calls owner directly."""
    assert_owner_callable(SPEAKER_CONTRACT, "enforce_emitted_speaker_with_contract")


def test_bj77_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "enforce_emitted_speaker_with_contract(" in ss_src
    assert "feg.enforce_emitted_speaker_with_contract" not in ss_src


def test_bj78_sync_eff_social_gate_reexport_removed() -> None:
    """BJ-78: strict-social sync no longer resolves through gate re-export."""
    assert_owner_callable(SPEAKER_CONTRACT, "_sync_eff_social_to_resolution")


def test_bj78_strict_social_stack_calls_sync_owner_directly() -> None:
    """BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "_sync_eff_social_to_resolution(" in ss_src
    assert "feg._sync_eff_social_to_resolution" not in ss_src


def test_bj79_tone_escalation_layer_gate_delegator_removed() -> None:
    """BJ-79: tone escalation layer gate delegator removed; stacks call owner directly."""
    assert_gate_lacks("_apply_tone_escalation_layer")
    assert_owner_callable(TONE_ESCALATION, "apply_tone_escalation_layer")


def test_bj79_stacks_call_tone_escalation_owner_directly() -> None:
    """BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_tone_escalation_layer(" in nss_src
    assert "apply_tone_escalation_layer(" in ss_src
    assert "feg._apply_tone_escalation_layer" not in nss_src
    assert "feg._apply_tone_escalation_layer" not in ss_src


def test_bj80_narrative_authority_layer_gate_delegator_removed() -> None:
    """BJ-80: narrative authority layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(NARRATIVE_AUTHORITY, "apply_narrative_authority_layer")


def test_bj80_stacks_call_narrative_authority_owner_directly() -> None:
    """BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_narrative_authority_layer(" in nss_src
    assert "apply_narrative_authority_layer(" in ss_src
    assert "feg._apply_narrative_authority_layer" not in nss_src
    assert "feg._apply_narrative_authority_layer" not in ss_src


def test_bj81_anti_railroading_layer_gate_delegator_removed() -> None:
    """BJ-81: anti-railroading layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(ANTI_RAILROADING, "apply_anti_railroading_layer")


def test_bj81_stacks_call_anti_railroading_owner_directly() -> None:
    """BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_anti_railroading_layer(" in nss_src
    assert "apply_anti_railroading_layer(" in ss_src
    assert "feg._apply_anti_railroading_layer" not in nss_src
    assert "feg._apply_anti_railroading_layer" not in ss_src


def test_bj82_context_separation_layer_gate_delegator_removed() -> None:
    """BJ-82: context separation layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(CONTEXT_SEPARATION, "apply_context_separation_layer")


def test_bj82_stacks_call_context_separation_owner_directly() -> None:
    """BJ-82: strict and non-strict stacks call context_separation owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_context_separation_layer(" in nss_src
    assert "apply_context_separation_layer(" in ss_src
    assert "feg._apply_context_separation_layer" not in nss_src
    assert "feg._apply_context_separation_layer" not in ss_src


def test_bj83_player_facing_narration_purity_layer_gate_delegator_removed() -> None:
    """BJ-83: narration purity layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(NARRATION_PURITY, "apply_player_facing_narration_purity_layer")


def test_bj83_stacks_call_narration_purity_owner_directly() -> None:
    """BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_player_facing_narration_purity_layer(" in nss_src
    assert "apply_player_facing_narration_purity_layer(" in ss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in nss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in ss_src


def test_bj84_answer_shape_primacy_layer_gate_delegator_removed() -> None:
    """BJ-84: answer-shape primacy layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(ANSWER_SHAPE_PRIMACY, "apply_answer_shape_primacy_layer")


def test_bj84_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src


def test_bj85_scene_state_anchor_layer_gate_delegator_removed() -> None:
    """BJ-85: scene state anchor layer gate delegator removed; stacks call owner directly."""
    assert_owner_callable(SCENE_STATE_ANCHOR, "apply_scene_state_anchor_layer")


def test_bj85_stacks_call_scene_state_anchor_owner_directly() -> None:
    """BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    nss_src = function_source(NON_STRICT_STACK, "run_non_strict_layer_stack")
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src


def test_bj47_merge_gate_layer_metas_into_fem_merge_order_locked(monkeypatch) -> None:
    """FEM layer-meta merges run in fixed post-AEP-second-pass order (Cycle AN2 / BJ-47)."""
    fem_assembly = load_game_module(FEM_ASSEMBLY)
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

    assert_gate_bj129_thin_boundary_shape(gate_module())

    gate_src = module_source(GATE)
    assert gate_import_modules(gate_src) == BJ129_ALLOWED_GATE_IMPORT_MODULES
    assert module_level_defs(gate_src) == ("apply_final_emission_gate",)

    feg = gate_module()
    for name in BJ128_LIVE_GATE_SEAM_SYMBOLS:
        assert hasattr(feg, name), f"gate missing documented live seam: {name!r}"
