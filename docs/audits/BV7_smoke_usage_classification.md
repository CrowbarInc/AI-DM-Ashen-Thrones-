# BV7 — Smoke Facade Usage Classification

**Date:** 2026-06-21
**Scope:** Group `emission_smoke_assertions` imports by assertion purpose.

## Classification totals

| Purpose | Importer count | Share of 73 | Dominant symbols |
|---|---:|---:|---|
| replay assertions | 47 | 64.4% | final_emission_meta_from_output |
| test helpers | 41 | 56.2% | apply_final_emission_gate_consumer |
| observability assertions | 20 | 27.4% | assert_response_type_* |
| fallback assertions | 6 | 8.2% | assert_*_smoke (phrase/hygiene) |
| attribution assertions | 2 | 2.7% | assert_open_social_solicitation_route |
| ownership assertions | 2 | 2.7% | assert_emission_repair_evidence |
| speaker assertions | 2 | 2.7% | assert_social_grounding_smoke |

> Note: Importers may appear in multiple purpose buckets when they import symbols from more than one family.

## By purpose

### attribution assertions (2 files)

- `tests/test_broad_address_social_bid.py`
- `tests/test_broadcast_open_call_social.py`

### fallback assertions (6 files)

- `tests/test_broad_address_social_bid.py`
- `tests/test_emission_smoke_assertions_contract.py`
- `tests/test_mixed_state_recovery_regressions.py`
- `tests/test_opening_start_seam_regressions.py`
- `tests/test_synthetic_smoke.py`
- `tests/test_turn_pipeline_shared.py`

### observability assertions (20 files)

- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_answer_completeness_rules.py`
- `tests/test_emission_smoke_assertions_contract.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_behavior_repairs.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_gate_diagnostics.py`
- `tests/test_final_emission_gate_orchestration_order.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_response_type.py`
- `tests/test_interaction_continuity_repair.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_player_facing_narration_purity.py`
- `tests/test_prompt_context.py`
- `tests/test_response_delta_requirement.py`
- `tests/test_response_policy_contracts.py`
- `tests/test_speaker_contract_enforcement.py`
- `tests/test_synthetic_smoke.py`
- `tests/test_tone_escalation_rules.py`
- `tests/test_turn_pipeline_shared.py`

### ownership assertions (2 files)

- `tests/test_emission_smoke_assertions_contract.py`
- `tests/test_turn_pipeline_shared.py`

### replay assertions (47 files)

- `tests/helpers/transcript_snapshots.py`
- `tests/test_anti_railroading.py`
- `tests/test_anti_railroading_retry_alignment.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_api_narration_path_selection.py`
- `tests/test_block_s_speaker_local_rebind_equivalence.py`
- `tests/test_block_u_finalize_stack_divergence.py`
- `tests/test_bv3a_observe_referential_clarity_repair.py`
- `tests/test_bv3e_eligibility_expansion.py`
- `tests/test_bv4b_concrete_beat_upstream_satisfier.py`
- `tests/test_c4_narrative_mode_live_pipeline.py`
- `tests/test_context_separation.py`
- `tests/test_contextual_minimal_repair_regressions.py`
- `tests/test_dead_turn_detection.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_empty_social_retry_regressions.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_behavior_repairs.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_final_emission_boundary_no_semantic_repair.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_interaction_continuity_repair.py`
- `tests/test_lead_lifecycle_block3_transcript_regression.py`
- `tests/test_manual_play_latency.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_narrative_authority_rules.py`
- `tests/test_narrative_mode_output_validator.py`
- `tests/test_observational_telemetry_confidence.py`
- `tests/test_player_facing_narration_purity.py`
- `tests/test_prompt_context.py`
- `tests/test_referential_clarity_player_coref.py`
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_response_policy_contracts.py`
- `tests/test_retry_tone_alignment.py`
- `tests/test_scene_state_anchoring.py`
- `tests/test_scene_transition_authority.py`
- `tests/test_social_emission_quality.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_social_interaction_authority.py`
- `tests/test_speaker_contract_risk.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_turn_packet_stage_diff_integration.py`
- `tests/test_turn_pipeline_shared.py`
- `tools/bv3d_build_positive_control_corpus.py`
- `tools/bv3e_shape_simulation.py`

### speaker assertions (2 files)

- `tests/test_social_speaker_grounding.py`
- `tests/test_turn_pipeline_shared.py`

### test helpers (41 files)

- `tests/helpers/strict_social_harness.py`
- `tests/helpers/turn_pipeline_http_fixtures.py`
- `tests/test_answer_completeness_rules.py`
- `tests/test_anti_railroading.py`
- `tests/test_anti_railroading_transcript_regressions.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_bv3a_observe_referential_clarity_repair.py`
- `tests/test_bv4b_concrete_beat_upstream_satisfier.py`
- `tests/test_c4_narrative_mode_live_pipeline.py`
- `tests/test_context_separation.py`
- `tests/test_dialogue_plan_final_emission_gate.py`
- `tests/test_dialogue_social_convergence.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_final_emission_answer_exposition_plan_convergence.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_gate_delegator_regression.py`
- `tests/test_final_emission_scene_integrity.py`
- `tests/test_golden_replay_direct_seam.py`
- `tests/test_interaction_continuity_repair.py`
- `tests/test_lead_lifecycle_block3_transcript_regression.py`
- `tests/test_lead_npc_payoff_and_fallback.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_narrative_authority_rules.py`
- `tests/test_narrative_mode_output_validator.py`
- `tests/test_ownership_registry.py`
- `tests/test_player_facing_narration_purity.py`
- `tests/test_prompt_context.py`
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_response_delta_requirement.py`
- `tests/test_response_policy_contracts.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_scene_destination_binding.py`
- `tests/test_scene_state_anchoring.py`
- `tests/test_speaker_contract_enforcement.py`
- `tests/test_speaker_contract_risk.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_tone_escalation_rules.py`
- `tests/test_upstream_fast_fallback_block_l.py`
- `tools/bv3d_build_positive_control_corpus.py`

