"""Final-emission gate delegate closeout / direct-owner seam locks (tests only).

This module owns **structural** BJ delegate-collapse closeout enforcement (cycles
BJ-27–BJ-129): gate wrappers must stay collapsed, stack/exit modules must call owner
modules directly, and harness monkeypatches must target canonical owner seams.

This is **not** the global test-responsibility ownership registry. Registry identity,
inventory parity, duplicate allowlist governance, and registry neighbor assertions remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_closeout_delegate_locks.py``.
BJ-128/BJ-129 thin-boundary constants are sourced from
``tests/helpers/gate_thin_boundary_locks.py`` (``_BJ129_ALLOWED_GATE_IMPORT_MODULES``,
``_BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES``).

Cycle BJ-123 — allowed ``feg.*`` harness patch seams: ``get_speaker_selection_contract``,
``apply_final_emission_gate`` (orchestration entry; direct calls, not monkeypatch targets).

Cycle BJ-124 — gate module must not re-export BJ-123-dead harness seams.

Cycle BJ-127 — global stale gate harness scan (no stale feg monkeypatches or dead feg alias imports).

Cycle BJ-128 — gate module keeps orchestration + live seams only; no import-only residue.

Cycle BJ-129 — gate module must not regrow beyond orchestration + documented live seams.

Closeout bands (CO65):

- BJ-27–68 entrypoint locks (this file): governance primitives, source/inspect helpers;
  intentional direct — BJ-39 harness tail, BJ-52, BJ-56, BJ-61.
- BJ-70–114 registry verify (``ownership_closeout_delegate_locks.py``): extracted helpers;
  intentional direct — BJ-108/109 constant-presence locks.
- BJ-115–119 production routing: source primitives in verify module.
- BJ-120–127 harness / stale-FEG scans: intentionally direct in verify module.
- BJ-128–129 thin boundary: ``gate_thin_boundary_locks`` dedicated helpers.
"""

from __future__ import annotations

from tests.ownership_closeout_delegate_locks import (
    verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly,
    verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly,
    verify_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly,
    verify_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly,
    verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly,
    verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly,
    verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly,
    verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly,
    verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly,
    verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly,
    verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly,
    verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly,
    verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly,
    verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly,
    verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly,
    verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly,
    verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly,
    verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly,
    verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly,
    verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly,
    verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly,
    verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly,
    verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly,
    verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly,
    verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly,
    verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly,
    verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly,
    verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly,
    verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly,
    verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly,
    verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly,
    verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly,
    verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly,
    verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly,
    verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly,
    verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly,
    verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly,
    verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly,
    verify_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly,
    verify_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly,
    verify_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly,
    verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly,
    verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly,
    verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly,
    verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly,
    verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly,
    verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly,
    verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly,
    verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate,
    verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate,
    verify_bj120_ownership_registry_harness_patches_canonical_owner_seams,
    verify_bj121_ownership_registry_strict_social_build_patches_use_stack_seam,
    verify_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings,
    verify_bj123_ownership_registry_harness_patches_no_stale_feg_seams,
    verify_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports,
    verify_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate,
    verify_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate,
    verify_bj127_ownership_registry_global_stale_gate_harness_scan,
    verify_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports,
    verify_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked,
)



def test_bj27_referential_clarity_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-27/BJ-50: referential-clarity orchestration lives on visibility fallback owner."""
    from tests.helpers.gate_delegator_governance import VISIBILITY_FALLBACK, assert_owner_callable

    assert_owner_callable(VISIBILITY_FALLBACK, "apply_referential_clarity_enforcement")

def test_bj50_visibility_enforcement_gate_wrapper_collapsed() -> None:
    """Cycle BJ-50/BJ-73: visibility enforcement lives on final_emission_visibility_fallback owner."""
    from tests.helpers.gate_delegator_governance import SEALED_FALLBACK, VISIBILITY_FALLBACK, assert_gate_lacks, assert_owner_callable, load_game_module
    assert_gate_lacks('_apply_visibility_enforcement')
    assert_gate_lacks('_standard_visibility_safe_fallback')
    assert_gate_lacks('_apply_first_mention_enforcement')
    assert_gate_lacks('_apply_referential_clarity_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_visibility_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_first_mention_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_referential_clarity_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'standard_visibility_safe_fallback')
    assert_owner_callable(SEALED_FALLBACK, 'select_visibility_safe_fallback')
    assert load_game_module(SEALED_FALLBACK).select_visibility_safe_fallback.__module__ == 'game.final_emission_sealed_fallback'

def test_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """Cycle BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    verify_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly()

def test_bj28_speaker_contract_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-28/BJ-77/BJ-78: speaker-contract orchestration lives on speaker_contract_enforcement owner."""
    from tests.helpers.gate_delegator_governance import (
        GATE,
        SPEAKER_CONTRACT,
        assert_gate_lacks,
        assert_owner_callable,
        assert_owner_is,
    )
    assert_owner_callable(SPEAKER_CONTRACT, 'enforce_emitted_speaker_with_contract')
    assert_owner_callable(SPEAKER_CONTRACT, '_sync_eff_social_to_resolution')
    assert_gate_lacks('enforce_emitted_speaker_with_contract', '_sync_eff_social_to_resolution')
    assert_owner_is(GATE, 'get_speaker_selection_contract', SPEAKER_CONTRACT, 'get_speaker_selection_contract')

def test_bj29_interaction_continuity_emission_owner_entrypoint_locked() -> None:
    """Cycle BJ-29/BJ-51/BJ-75/BJ-76: interaction-continuity orchestration lives on interaction_continuity owner."""
    from tests.helpers.gate_delegator_governance import (
        GATE,
        INTERACTION_CONTINUITY,
        assert_gate_lacks,
        assert_owner_callable,
        assert_owner_is,
    )
    assert_owner_callable(INTERACTION_CONTINUITY, 'apply_interaction_continuity_emission_step')
    assert_owner_callable(INTERACTION_CONTINUITY, 'attach_interaction_continuity_validation')
    assert_gate_lacks('_apply_interaction_continuity_emission_step')
    assert_owner_is(
        GATE,
        'apply_interaction_continuity_emission_step',
        INTERACTION_CONTINUITY,
        'apply_interaction_continuity_emission_step',
    )
    assert_owner_is(
        GATE,
        'attach_interaction_continuity_validation',
        INTERACTION_CONTINUITY,
        'attach_interaction_continuity_validation',
    )

def test_bj51_interaction_continuity_gate_wrappers_fully_collapsed() -> None:
    """Cycle BJ-51/BJ-75/BJ-76: all IC gate delegators removed; owners called from stack modules."""
    from tests.helpers.gate_delegator_governance import INTERACTION_CONTINUITY, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_apply_interaction_continuity_emission_step', '_attach_interaction_continuity_validation')
    assert_owner_callable(INTERACTION_CONTINUITY, 'apply_interaction_continuity_emission_step')
    assert_owner_callable(INTERACTION_CONTINUITY, 'attach_interaction_continuity_validation')

def test_bj52_fallback_provenance_gate_wrappers_collapsed() -> None:
    """Cycle BJ-52/BN4: upstream fallback provenance containment wrappers removed from gate."""
    import game.fallback_provenance_debug as fpd
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_gate_context as gc
    import game.final_emission_gate_preflight_telemetry as gpft
    assert not hasattr(feg, '_upstream_fallback_canonical_provenance')
    assert not hasattr(feg, '_apply_upstream_fallback_pregate_containment')
    assert not hasattr(feg, '_finalize_upstream_fallback_overwrite_containment')
    assert callable(getattr(fpd, 'upstream_fallback_canonical_provenance', None))
    assert callable(getattr(fpd, 'apply_upstream_fallback_pregate_containment', None))
    assert callable(getattr(fpd, 'finalize_upstream_fallback_overwrite_containment', None))
    assert not hasattr(gc, 'apply_upstream_fallback_pregate_containment')
    assert callable(getattr(gpft, 'apply_gate_preflight_telemetry_and_containment', None))
    assert callable(getattr(fin, 'finalize_upstream_fallback_overwrite_containment', None))

def test_bj53_referent_clarity_pre_finalize_gate_wrapper_collapsed() -> None:
    """Cycle BJ-53: referent pre-finalize wrapper removed from gate; terminal pipeline owns the hook."""
    from tests.helpers.gate_delegator_governance import TERMINAL_PIPELINE, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_apply_referent_clarity_pre_finalize')
    assert_owner_callable(TERMINAL_PIPELINE, '_apply_referent_clarity_pre_finalize')

def test_bj54_narration_constraint_debug_merge_gate_wrapper_collapsed() -> None:
    """BU2-B: narration-constraint debug merge owned by final_emission_narration_constraint_debug."""
    from tests.helpers.gate_delegator_governance import (
        NARRATION_CONSTRAINT_DEBUG,
        TERMINAL_PIPELINE,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=NARRATION_CONSTRAINT_DEBUG,
        owner_attr="merge_narration_constraint_debug_into_outputs",
        gate_private_attr="_merge_narration_constraint_debug_into_outputs",
        callers=((TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),),
        module_private_lacks=(
            (TERMINAL_PIPELINE, "_merge_narration_constraint_debug_into_outputs"),
        ),
    )

def test_bj55_gate_fem_text_fingerprint_helper_collapsed() -> None:
    """Cycle BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns fingerprint patch."""
    from tests.helpers.gate_delegator_governance import TERMINAL_PIPELINE, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_patch_gate_fem_text_fingerprint')
    assert_owner_callable(TERMINAL_PIPELINE, '_patch_fem_text_fingerprint')

def test_bj56_scene_opening_finalize_delegators_collapsed() -> None:
    """BU2-C: scene-opening accept debug owned by final_emission_opening_fallback."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_opening_fallback as opening_fallback
    assert not hasattr(feg, '_patch_scene_opening_candidate_emission_debug')
    assert not hasattr(feg, '_reassert_scene_opening_accepted_candidate')
    assert opening_fallback.patch_scene_opening_candidate_emission_debug.__module__ == 'game.final_emission_opening_fallback'
    assert opening_fallback.reassert_scene_opening_accepted_candidate.__module__ == 'game.final_emission_opening_fallback'
    assert getattr(fin, 'reassert_scene_opening_accepted_candidate', None) is opening_fallback.reassert_scene_opening_accepted_candidate

def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_collapsed() -> None:
    """Cycle BJ-57: route-illegal strip wrapper removed from gate; finalize owner owns strip helper."""
    from tests.helpers.gate_delegator_governance import FINALIZE, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_strip_appended_route_illegal_contamination_sentences')
    assert_owner_callable(FINALIZE, 'strip_appended_route_illegal_contamination_sentences')

def test_bj30_dialogue_social_plan_strict_social_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-30: strict-social dialogue plan enforcement lives on dialogue_social_plan owner."""
    from tests.helpers.gate_delegator_governance import DIALOGUE_SOCIAL_PLAN, assert_owner_callable
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'enforce_dialogue_plan_invariant_on_strict_social')
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'strip_dialogue_from_text')
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'strict_social_line_matches_terminal_emission_pool')
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'is_bare_speech_attribution_shell_line')

def test_bj59_dialogue_social_plan_gate_delegators_collapsed() -> None:
    """Cycle BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls owner directly."""
    from tests.helpers.gate_delegator_governance import DIALOGUE_SOCIAL_PLAN, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks(
        '_enforce_dialogue_plan_invariant_on_strict_social',
        '_strip_dialogue_from_text',
        '_strict_social_line_matches_terminal_emission_pool',
        '_is_bare_speech_attribution_shell_line',
    )
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'enforce_dialogue_plan_invariant_on_strict_social')
    assert_owner_callable(DIALOGUE_SOCIAL_PLAN, 'strip_dialogue_from_text')

def test_bj60_sealed_fallback_selector_gate_delegator_collapsed() -> None:
    """Cycle BJ-60: non-strict sealed selector wrapper removed from gate; owner resolves opening provider."""
    from tests.helpers.gate_delegator_governance import SEALED_FALLBACK, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_select_non_strict_replace_path_terminal_sealed_fallback_selection')
    assert_owner_callable(SEALED_FALLBACK, 'select_non_strict_replace_path_terminal_sealed_fallback_selection')

def test_bj61_sealed_fallback_stamp_gate_delegators_collapsed() -> None:
    """Cycle BJ-61: sealed FEM stamp/route-meta import aliases removed from gate; generic_exit calls owner."""
    import game.final_emission_gate as feg
    import game.final_emission_sealed_fallback as sf
    for name in ('_stamp_sealed_fallback_realization_family', '_stamp_non_strict_sealed_replacement_realization_family', '_prepare_sealed_replacement_route_meta'):
        assert not hasattr(feg, name), name
    for name in ('stamp_sealed_fallback_realization_family', 'stamp_non_strict_sealed_replacement_realization_family', 'prepare_sealed_replacement_route_meta'):
        assert callable(getattr(sf, name, None)), name

def test_bj62_generic_exit_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-62: generic exit calls FEM assembly owner directly."""
    from tests.helpers.gate_delegator_governance import (
        FEM_ASSEMBLY,
        GENERIC_EXIT,
        assert_function_source_contains,
        assert_owner_callable,
    )

    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_accept_exit",
        "fem_assembly.build_gate_accept_fem_base",
        "fem_assembly.merge_gate_layer_metas_into_fem",
        forbidden=("_build_gate_accept_fem_base", "_merge_gate_layer_metas_into_fem"),
    )
    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_replace_exit",
        "fem_assembly.build_gate_replace_fem_base",
        "fem_assembly.merge_gate_layer_metas_into_fem",
        forbidden=("_build_gate_replace_fem_base", "_merge_gate_layer_metas_into_fem"),
    )
    assert_owner_callable(FEM_ASSEMBLY, "build_gate_accept_fem_base")
    assert_owner_callable(FEM_ASSEMBLY, "build_gate_replace_fem_base")
    assert_owner_callable(FEM_ASSEMBLY, "merge_gate_layer_metas_into_fem")

def test_bj63_strict_social_stack_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-63: strict-social stack calls FEM assembly owner; gate FEM delegators removed."""
    from tests.helpers.gate_delegator_governance import (
        FEM_ASSEMBLY,
        STRICT_SOCIAL_STACK,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
        function_source,
    )

    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        "fem_assembly.build_gate_accept_fem_base",
        "fem_assembly.build_gate_replace_fem_base",
        "fem_assembly.merge_pre_terminal_layer_debug",
        forbidden=(
            "_build_gate_accept_fem_base",
            "_build_gate_replace_fem_base",
            "_merge_gate_layer_metas_into_fem",
        ),
    )
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert ss_src.count("fem_assembly.merge_gate_layer_metas_into_fem") == 2
    assert_gate_lacks(
        "_build_gate_accept_fem_base",
        "_build_gate_replace_fem_base",
        "_merge_gate_layer_metas_into_fem",
    )
    assert_owner_callable(FEM_ASSEMBLY, "build_gate_accept_fem_base")
    assert_owner_callable(FEM_ASSEMBLY, "build_gate_replace_fem_base")
    assert_owner_callable(FEM_ASSEMBLY, "merge_gate_layer_metas_into_fem")

def test_bj64_non_strict_stack_opening_rt_promotion_calls_owner_directly() -> None:
    """Cycle BJ-64: non-strict stack calls opening RT promotion owner; gate alias removed."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        OPENING_FALLBACK,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=OPENING_FALLBACK,
        owner_attr="scene_opening_rt_contract_accept_path_promotes_candidate",
        owner_call="opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate",
        gate_private_attr="_scene_opening_rt_contract_accept_path_promotes_candidate",
        callers=((NON_STRICT_STACK, "run_non_strict_layer_stack"),),
        forbidden_markers=("_scene_opening_rt_contract_accept_path_promotes_candidate",),
    )

def test_bj65_stacks_opening_upstream_prepare_observability_merge_calls_owner_directly() -> None:
    """Cycle BJ-65: stacks call response_type owner for opening upstream-prepare observability merge."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        RESPONSE_TYPE,
        STRICT_SOCIAL_STACK,
        assert_inspect_callers_call_owner_directly,
    )

    owner_call = (
        "response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug"
    )
    assert_inspect_callers_call_owner_directly(
        owner_module=RESPONSE_TYPE,
        owner_attr="_merge_opening_upstream_prepare_attach_observability_into_response_type_debug",
        owner_call=owner_call,
        gate_private_attr="_merge_opening_upstream_prepare_attach_observability_into_response_type_debug",
        callers=(
            (NON_STRICT_STACK, "run_non_strict_layer_stack"),
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),
        ),
        caller_owner_call_counts={
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"): 2,
        },
    )

def test_bj31_tone_escalation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-31/BJ-79: tone escalation layer lives on final_emission_tone_escalation owner."""
    from tests.helpers.gate_delegator_governance import TONE_ESCALATION, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(TONE_ESCALATION, 'apply_tone_escalation_layer')
    assert_owner_callable(TONE_ESCALATION, 'resolve_tone_escalation_contract')
    assert_gate_lacks('_apply_tone_escalation_layer')

def test_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly() -> None:
    """Cycle BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly()

def test_bj32_narrative_authority_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-32/BJ-80: narrative authority layer lives on final_emission_narrative_authority owner."""
    from tests.helpers.gate_delegator_governance import NARRATIVE_AUTHORITY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(NARRATIVE_AUTHORITY, 'apply_narrative_authority_layer')
    assert_owner_callable(NARRATIVE_AUTHORITY, 'resolve_narrative_authority_contract')
    assert_gate_lacks('_apply_narrative_authority_layer')

def test_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly() -> None:
    """Cycle BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly()

def test_bj58_contract_resolver_gate_delegators_collapsed() -> None:
    """Cycle BJ-58: contract resolver wrappers removed from gate; tone/authority owners resolve directly."""
    from tests.helpers.gate_delegator_governance import NARRATIVE_AUTHORITY, TONE_ESCALATION, assert_gate_lacks, assert_owner_callable
    assert_gate_lacks('_resolve_tone_escalation_contract', '_resolve_narrative_authority_contract')
    assert_owner_callable(TONE_ESCALATION, 'resolve_tone_escalation_contract')
    assert_owner_callable(NARRATIVE_AUTHORITY, 'resolve_narrative_authority_contract')

def test_bj33_anti_railroading_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-33/BJ-81: anti-railroading layer lives on final_emission_anti_railroading owner."""
    from tests.helpers.gate_delegator_governance import ANTI_RAILROADING, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(ANTI_RAILROADING, 'apply_anti_railroading_layer')
    assert_owner_callable(ANTI_RAILROADING, 'resolve_anti_railroading_contract')
    assert_gate_lacks('_apply_anti_railroading_layer')

def test_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly() -> None:
    """Cycle BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly()

def test_bj34_context_separation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-34/BJ-82: context separation layer lives on final_emission_context_separation owner."""
    from tests.helpers.gate_delegator_governance import CONTEXT_SEPARATION, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(CONTEXT_SEPARATION, 'apply_context_separation_layer')
    assert_owner_callable(CONTEXT_SEPARATION, 'resolve_context_separation_contract')
    assert_gate_lacks('_apply_context_separation_layer')

def test_bj82_ownership_registry_stacks_call_context_separation_owner_directly() -> None:
    """Cycle BJ-82: strict and non-strict stacks call context_separation owner directly."""
    verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly()

def test_bj35_player_facing_narration_purity_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-35/BJ-83: narration purity layer lives on final_emission_player_facing_narration_purity owner."""
    from tests.helpers.gate_delegator_governance import NARRATION_PURITY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(NARRATION_PURITY, 'apply_player_facing_narration_purity_layer')
    assert_owner_callable(NARRATION_PURITY, 'resolve_player_facing_narration_purity_contract')
    assert_gate_lacks('_apply_player_facing_narration_purity_layer')

def test_bj83_ownership_registry_stacks_call_narration_purity_owner_directly() -> None:
    """Cycle BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly()

def test_bj36_answer_shape_primacy_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-36/BJ-84: answer-shape primacy layer lives on final_emission_answer_shape_primacy owner."""
    from tests.helpers.gate_delegator_governance import ANSWER_SHAPE_PRIMACY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(ANSWER_SHAPE_PRIMACY, 'apply_answer_shape_primacy_layer')
    assert_owner_callable(ANSWER_SHAPE_PRIMACY, 'validate_answer_shape_primacy')
    assert_gate_lacks('_apply_answer_shape_primacy_layer')

def test_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """Cycle BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly()

def test_bj37_scene_state_anchor_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-37/BJ-85: scene state anchor apply layer lives on final_emission_scene_state_anchor owner."""
    from tests.helpers.gate_delegator_governance import SCENE_STATE_ANCHOR, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(SCENE_STATE_ANCHOR, 'apply_scene_state_anchor_layer')
    assert_gate_lacks('_apply_scene_state_anchor_layer')

def test_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly() -> None:
    """Cycle BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly()

def test_bj42_terminal_enforcement_pipeline_owner_entrypoint_locked() -> None:
    """Cycle BJ-42/BJ-69: terminal enforcement pipeline lives on final_emission_terminal_pipeline owner."""
    from tests.helpers.gate_delegator_governance import TERMINAL_PIPELINE, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(TERMINAL_PIPELINE, 'run_gate_terminal_enforcement_pipeline')
    assert_gate_lacks('_run_gate_terminal_enforcement_pipeline')

def test_bj43_non_strict_layer_stack_owner_entrypoint_locked() -> None:
    """Cycle BJ-43/BJ-71: non-strict pre-fork layer stack lives on final_emission_non_strict_stack owner."""
    from tests.helpers.gate_delegator_governance import NON_STRICT_STACK, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(NON_STRICT_STACK, 'run_non_strict_layer_stack')
    assert_gate_lacks('_run_non_strict_layer_stack')

def test_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly() -> None:
    """Cycle BJ-71: apply_final_emission_gate calls non_strict_stack owner directly."""
    verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly()

def test_bj44_strict_social_composition_trunk_owner_entrypoint_locked() -> None:
    """Cycle BJ-44/BJ-70: strict-social composition trunk lives on final_emission_strict_social_stack owner."""
    from tests.helpers.gate_delegator_governance import STRICT_SOCIAL_STACK, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(STRICT_SOCIAL_STACK, 'run_strict_social_composition_trunk')
    assert_gate_lacks('_run_strict_social_composition_trunk')

def test_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly() -> None:
    """Cycle BJ-70: apply_final_emission_gate calls generic/strict-social exit owners directly."""
    verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly()

def test_bj69_ownership_registry_exit_stacks_call_terminal_finalize_owners_directly() -> None:
    """Cycle BJ-69: exit stacks call terminal pipeline and finalize owners directly."""
    from tests.helpers.gate_delegator_governance import (
        FINALIZE,
        GENERIC_EXIT,
        STRICT_SOCIAL_STACK,
        TERMINAL_PIPELINE,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
    )

    terminal_finalize_required = (
        "terminal_pipeline.run_gate_terminal_enforcement_pipeline",
        "emission_finalize.finalize_emission_output",
        "emission_finalize.final_emission_fast_path_eligible",
    )
    terminal_finalize_forbidden = (
        "feg._run_gate_terminal_enforcement_pipeline",
        "feg._finalize_emission_output",
        "feg._final_emission_fast_path_eligible",
    )
    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_accept_exit",
        *terminal_finalize_required,
        forbidden=terminal_finalize_forbidden,
    )
    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_replace_exit",
        *terminal_finalize_required,
        forbidden=terminal_finalize_forbidden,
    )
    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        *terminal_finalize_required,
        forbidden=terminal_finalize_forbidden,
    )
    assert_gate_lacks(
        "_run_gate_terminal_enforcement_pipeline",
        "_finalize_emission_output",
        "_final_emission_fast_path_eligible",
    )
    assert_owner_callable(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert_owner_callable(FINALIZE, "finalize_emission_output")
    assert_owner_callable(FINALIZE, "final_emission_fast_path_eligible")

def test_bj45_generic_exit_owner_entrypoints_locked() -> None:
    """Cycle BJ-45/BJ-70: generic accept/replace exits live on final_emission_generic_exit owner."""
    from tests.helpers.gate_delegator_governance import GENERIC_EXIT, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(GENERIC_EXIT, 'run_generic_accept_exit')
    assert_owner_callable(GENERIC_EXIT, 'run_generic_replace_exit')
    assert_gate_lacks('_run_generic_accept_exit', '_run_generic_replace_exit')

def test_bj46_fem_assembly_owner_entrypoints_locked() -> None:
    """Cycle BJ-46/BJ-63: FEM accept/replace base assembly lives on final_emission_fem_assembly owner."""
    from tests.helpers.gate_delegator_governance import FEM_ASSEMBLY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(FEM_ASSEMBLY, 'build_gate_accept_fem_base')
    assert_owner_callable(FEM_ASSEMBLY, 'build_gate_replace_fem_base')
    assert_gate_lacks('_build_gate_accept_fem_base', '_build_gate_replace_fem_base')

def test_bj47_fem_assembly_merge_gate_layer_metas_owner_entrypoint_locked() -> None:
    """Cycle BJ-47/BJ-63: FEM layer-meta merge lives on final_emission_fem_assembly owner."""
    from tests.helpers.gate_delegator_governance import FEM_ASSEMBLY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(FEM_ASSEMBLY, 'merge_gate_layer_metas_into_fem')
    assert_gate_lacks('_merge_gate_layer_metas_into_fem')

def test_bj48_fast_fallback_neutral_composition_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-48/BJ-86: FFNC layer apply/default-meta live on final_emission_fast_fallback_composition owner."""
    from tests.helpers.gate_delegator_governance import FAST_FALLBACK, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(FAST_FALLBACK, 'default_fast_fallback_neutral_composition_meta')
    assert_owner_callable(FAST_FALLBACK, 'apply_fast_fallback_neutral_composition_layer')
    assert_gate_lacks('_apply_fast_fallback_neutral_composition_layer')

def test_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """Cycle BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly()

def test_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """Cycle BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly()

def test_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """Cycle BJ-88: stacks call final_emission_repairs answer exposition plan directly."""
    verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly()

def test_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly() -> None:
    """Cycle BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly()

def test_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """Cycle BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly()

def test_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """Cycle BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly()

def test_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """Cycle BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly()

def test_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-93: stacks call final_emission_repairs fallback debug/meta merge helpers directly."""
    verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly()

def test_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BU2-A: conversational memory debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly()

def test_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BU2-A: scene_state_anchor debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly()

def test_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: tone_escalation debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly()

def test_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narrative_authority debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly()

def test_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BU2-A: anti_railroading debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly()

def test_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: context_separation debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly()

def test_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narration_purity debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly()

def test_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BU2-A: answer_shape_primacy debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly()

def test_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """Cycle BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly()

def test_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """Cycle BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly()

def test_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """Cycle BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly()

def test_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """Cycle BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly()

def test_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly() -> None:
    """Cycle BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly()

def test_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """Cycle BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly()

def test_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """Cycle BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    verify_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly()

def test_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly() -> None:
    """Cycle BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    verify_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly()

def test_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """Cycle BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    verify_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly()

def test_bj111_ownership_registry_callers_use_normalize_text_owner_directly() -> None:
    """Cycle BJ-111: stack/exit callers use final_emission_text_formatting._normalize_text directly."""
    verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly()

def test_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """Cycle BJ-112: strict_social_stack calls final_emission_text_formatting._normalize_text_preserve_paragraphs directly."""
    verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly()

def test_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """Cycle BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly()

def test_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """Cycle BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly()

def test_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """Cycle BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly()

def test_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """Cycle BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly()

def test_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """Cycle BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly()

def test_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate() -> None:
    """Cycle BJ-118: should_replace_candidate_intro_fallback lives on anti_reset owner, not gate."""
    verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate()

def test_bj119_ownership_registry_stage_diff_telemetry_not_on_gate() -> None:
    """Cycle BJ-119: stage_diff_telemetry helpers live on stage_diff owner, not gate."""
    verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate()

def test_bj120_ownership_registry_harness_patches_canonical_owner_seams() -> None:
    """Cycle BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    verify_bj120_ownership_registry_harness_patches_canonical_owner_seams()

def test_bj121_ownership_registry_strict_social_build_patches_use_stack_seam() -> None:
    """Cycle BJ-121: strict-social build monkeypatches target strict_social_stack, not gate."""
    verify_bj121_ownership_registry_strict_social_build_patches_use_stack_seam()

def test_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings() -> None:
    """Cycle BJ-122: scene_state_anchoring tests use final_emission_scene_state_anchor owner bindings."""
    verify_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings()

def test_bj123_ownership_registry_harness_patches_no_stale_feg_seams() -> None:
    """Cycle BJ-123: tests/helpers patch canonical owner modules, not removed feg re-exports."""
    verify_bj123_ownership_registry_harness_patches_no_stale_feg_seams()

def test_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports() -> None:
    """Cycle BJ-124: gate module must not re-export BJ-123-dead harness seams."""
    verify_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports()

def test_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-125/BN8: anti-reset tests patch social_exchange_emission + preflight strict-social seam."""
    verify_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate()

def test_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-126/BN8: narration transcript tests patch owner + preflight strict-social seam."""
    verify_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate()

def test_bj127_ownership_registry_global_stale_gate_harness_scan() -> None:
    """Cycle BJ-127: global scan — no stale feg monkeypatches or dead feg alias imports."""
    verify_bj127_ownership_registry_global_stale_gate_harness_scan()

def test_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports() -> None:
    """Cycle BJ-128: gate module keeps orchestration + live seams only; no import-only residue."""
    verify_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports()

def test_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked() -> None:
    """Cycle BJ-129: gate module must not regrow beyond orchestration + documented live seams."""
    verify_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked()

def test_bj49_gate_context_owner_entrypoint_locked() -> None:
    """Cycle BJ-49/BJ-72: gate entry/preflight context lives on final_emission_gate_context owner."""
    from tests.helpers.gate_delegator_governance import GATE_CONTEXT, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(GATE_CONTEXT, 'initialize_gate_execution_context')
    assert_owner_callable(GATE_CONTEXT, 'GateExecutionContext')
    assert_gate_lacks('_initialize_gate_execution_context')

def test_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly() -> None:
    """Cycle BJ-72: apply_final_emission_gate calls gate_context owner directly."""
    verify_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly()

def test_bj41_finalize_emission_output_owner_entrypoint_locked() -> None:
    """Cycle BJ-41/BJ-69: finalize packaging and fast-path eligibility live on final_emission_finalize owner."""
    from tests.helpers.gate_delegator_governance import FINALIZE, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(FINALIZE, 'finalize_emission_output')
    assert_owner_callable(FINALIZE, 'final_emission_fast_path_eligible')
    assert_gate_lacks('_finalize_emission_output', '_final_emission_fast_path_eligible')

def test_bj40_acceptance_quality_n4_floor_seam_owner_entrypoint_locked() -> None:
    """Cycle BJ-40/BJ-74: N4 floor seam lives on final_emission_acceptance_quality owner."""
    from tests.helpers.gate_delegator_governance import ACCEPTANCE_QUALITY, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(ACCEPTANCE_QUALITY, 'apply_acceptance_quality_n4_floor_seam')
    assert_gate_lacks('_apply_acceptance_quality_n4_floor_seam')

def test_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """Cycle BJ-74: terminal pipeline calls acceptance_quality N4 floor seam owner directly."""
    verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly()

def test_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """Cycle BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly()

def test_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly() -> None:
    """Cycle BJ-76: terminal pipeline and non_strict_stack call IC emission-step owner directly."""
    verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly()

def test_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """Cycle BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly()

def test_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly() -> None:
    """Cycle BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly()

def test_bj39_response_type_contract_owner_entrypoint_locked() -> None:
    """Cycle BJ-39/BJ-67/BJ-68: response-type contract enforcement lives on final_emission_response_type owner."""
    import inspect

    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        RESPONSE_TYPE,
        STRICT_SOCIAL_STACK,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
        function_source,
    )

    assert_owner_callable(RESPONSE_TYPE, "enforce_response_type_contract")
    assert_gate_lacks("_enforce_response_type_contract")
    assert_function_source_contains(
        NON_STRICT_STACK,
        "run_non_strict_layer_stack",
        "response_type.enforce_response_type_contract",
        forbidden=("feg._enforce_response_type_contract",),
    )
    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        "response_type.enforce_response_type_contract",
        forbidden=("feg._enforce_response_type_contract",),
    )
    ss_src = function_source(STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk")
    assert ss_src.count("response_type.enforce_response_type_contract") == 2

    # Harness compatibility locks — module-level source; outside game-module manifest.
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert "response_type.enforce_response_type_contract" in ob_src
    assert "final_emission_response_type" in smoke_fn_src

def test_bj38_fallback_debug_merge_helpers_live_on_repairs_owner() -> None:
    """Cycle BJ-38/BJ-93/BJ-94: fallback/conversational-memory emission_debug merges live on final_emission_repairs."""
    from tests.helpers.gate_delegator_governance import REPAIRS, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(REPAIRS, 'merge_fallback_behavior_into_emission_debug')
    assert_owner_callable(REPAIRS, 'merge_conversational_memory_inspection_into_emission_debug')
    assert_gate_lacks(
        '_merge_fallback_behavior_into_emission_debug',
        '_merge_conversational_memory_inspection_into_emission_debug',
    )
