# BV7 — Smoke Assertion Family Map

**Date:** 2026-06-21
**Scope:** Major assertion families exported by `emission_smoke_assertions`.

| Family | Assertion count | Consumer count | Primary subsystem | Concentration |
|---|---:|---:|---|---|
| FEM/read bridge | 2 | 46 | replay / FEM projection | HIGH |
| Gate integration bridge | 2 | 39 | integration / gate orchestration | HIGH |
| Consumer layer bridge (AC/RD/RT) | 14 | 18 | final emission gate / boundary | HIGH |
| Route wiring smoke | 7 | 8 | route / HTTP pipeline | MEDIUM |
| Phrase/hygiene smoke | 11 | 4 | HTTP/pipeline integration | LOW |
| Repair evidence smoke | 1 | 2 | ownership / repair wiring | LOW |
| Social/open-call smoke | 6 | 4 | speaker / social routing | LOW |
| Smoke phrase constants | 9 | 2 | synthetic smoke / AC boundary | LOW |

## Family detail

### FEM/read bridge

- **Assertions (2):** `final_emission_meta_from_output`, `read_turn_debug_notes`
- **Consumers (46):**
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

### Gate integration bridge

- **Assertions (2):** `apply_final_emission_gate_consumer`, `gm_response_stub`
- **Consumers (39):**
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
  - `tests/test_final_emission_scene_integrity.py`
  - `tests/test_golden_replay_direct_seam.py`
  - `tests/test_interaction_continuity_repair.py`
  - `tests/test_lead_lifecycle_block3_transcript_regression.py`
  - `tests/test_lead_npc_payoff_and_fallback.py`
  - `tests/test_narration_transcript_regressions.py`
  - `tests/test_narrative_authority_rules.py`
  - `tests/test_narrative_mode_output_validator.py`
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

### Consumer layer bridge (AC/RD/RT)

- **Assertions (14):** `validate_answer_completeness`, `apply_answer_completeness_layer`, `apply_response_delta_layer`, `enforce_response_type_contract_layer`, `skip_answer_completeness_layer`, `skip_response_delta_layer`, `strict_social_answer_pressure_rd_contract_active`, `validate_response_delta`, `inspect_response_delta_failure`, `assert_response_delta_boundary_validate_only`, `assert_no_boundary_reorder_repair`, `response_type_contract`, `assert_response_type_meta`, `assert_response_type_contract_surfaces`
- **Consumers (18):**
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
  - `tests/test_narration_transcript_regressions.py`
  - `tests/test_player_facing_narration_purity.py`
  - `tests/test_prompt_context.py`
  - `tests/test_response_delta_requirement.py`
  - `tests/test_response_policy_contracts.py`
  - `tests/test_speaker_contract_enforcement.py`
  - `tests/test_tone_escalation_rules.py`
  - `tests/test_turn_pipeline_shared.py`

### Route wiring smoke

- **Assertions (7):** `assert_final_route_present_smoke`, `assert_final_route_accept_candidate_smoke`, `assert_final_route_not_replaced_smoke`, `has_non_accept_final_route_smoke`, `assert_final_route_replaced_or_not_accept`, `assert_dialogue_lock_social_route_smoke`, `assert_dialogue_lock_non_dialogue_route_smoke`
- **Consumers (8):**
  - `tests/test_c4_narrative_mode_live_pipeline.py`
  - `tests/test_diegetic_fallback_narration.py`
  - `tests/test_empty_social_retry_regressions.py`
  - `tests/test_interaction_continuity_repair.py`
  - `tests/test_opening_start_seam_regressions.py`
  - `tests/test_social_exchange_emission.py`
  - `tests/test_turn_packet_stage_diff_integration.py`
  - `tests/test_turn_pipeline_shared.py`

### Phrase/hygiene smoke

- **Assertions (11):** `assert_player_text_present`, `assert_global_visibility_stock_absent`, `assert_procedural_adjudication_smoke`, `assert_no_validator_voice_smoke`, `assert_no_retry_coaching_leak_smoke`, `assert_no_social_visible_intro_filler_smoke`, `assert_no_uncertainty_fallback_stock_smoke`, `assert_no_internal_scaffold_labels`, `assert_no_advisory_prose`, `assert_no_unresolved_stock_phrases`, `assert_http_chat_response_smoke`
- **Consumers (4):**
  - `tests/test_broad_address_social_bid.py`
  - `tests/test_emission_smoke_assertions_contract.py`
  - `tests/test_mixed_state_recovery_regressions.py`
  - `tests/test_turn_pipeline_shared.py`

### Repair evidence smoke

- **Assertions (1):** `assert_emission_repair_evidence`
- **Consumers (2):**
  - `tests/test_emission_smoke_assertions_contract.py`
  - `tests/test_turn_pipeline_shared.py`

### Social/open-call smoke

- **Assertions (6):** `assert_social_grounding_smoke`, `assert_continuity_validation_failed_without_repair`, `assert_open_social_solicitation_route`, `assert_broadcast_open_call_rejected_smoke`, `assert_open_call_crowd_reaction_wiring_smoke`, `assert_open_call_no_unresolved_retry_smoke`
- **Consumers (4):**
  - `tests/test_broad_address_social_bid.py`
  - `tests/test_broadcast_open_call_social.py`
  - `tests/test_interaction_continuity_repair.py`
  - `tests/test_social_speaker_grounding.py`

### Smoke phrase constants

- **Assertions (9):** `SMOKE_PROCEDURAL_ADJUDICATION_PHRASES`, `SMOKE_VALIDATOR_VOICE_PHRASES`, `SMOKE_RETRY_COACHING_LEAK_PHRASES`, `SMOKE_SOCIAL_VISIBLE_INTRO_FILLER_PHRASES`, `SMOKE_UNCERTAINTY_FALLBACK_STOCK_PHRASES`, `SMOKE_SYNTHETIC_INTERNAL_LEAK_PATTERNS`, `SMOKE_SYNTHETIC_SCAFFOLD_LEAK_PATTERNS`, `SMOKE_SYNTHETIC_VAGUE_FILLER_PATTERNS`, `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH`
- **Consumers (2):**
  - `tests/test_answer_completeness_rules.py`
  - `tests/test_synthetic_smoke.py`

