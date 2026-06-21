# BV12 — Smoke Bridge Dependency Inventory

**Date:** 2026-06-21  
**Scope:** Analysis only — every direct importer of `replay_smoke_assertions` and `gate_integration_smoke`  
**Method:** `python tools/bv12_smoke_bridge_discovery.py` + BU CSV reconciliation  

---

## Hub baseline (current)

| Module | BU fan-in | AST direct importers | Public exports | LOC |
| --- | --- | --- | --- | --- |
| `tests.helpers.replay_smoke_assertions` | 56 | 57 | 2 | 26 |
| `tests.helpers.gate_integration_smoke` | 39 | 40 | 2 | 58 |
| **Combined** | 95 | — | 4 | 84 |

**BV11 context:** Combined FI **95** — largest addressable maintenance cluster post-BV10. `emission_smoke_assertions` barrel FI **15** (phrase/route smoke only; bridge symbols migrated direct in BV7A).

## Importer overlap

| Pattern | Count |
| --- | --- |
| Replay-only importers | 32 |
| Gate-only importers | 15 |
| Dual-bridge importers (both modules) | 25 |

Dual-bridge coupling is **consumer-side** (25 suites run gate orchestration and FEM reads in the same file), plus **module-side** (`gate_integration_smoke` imports `final_emission_meta_from_output` from replay bridge).

## `replay_smoke_assertions` — summary by subsystem

| Subsystem | Importers | Primary symbol |
| --- | --- | --- |
| integration/regression | 30 | final_emission_meta_from_output |
| fallback | 6 | final_emission_meta_from_output |
| final emission gate | 6 | final_emission_meta_from_output |
| HTTP/pipeline integration | 4 | final_emission_meta_from_output |
| observability/diagnostics | 3 | final_emission_meta_from_output |
| test helpers | 2 | final_emission_meta_from_output |
| speaker/social | 2 | final_emission_meta_from_output |
| tools/analysis | 2 | final_emission_meta_from_output |
| replay helpers | 1 | final_emission_meta_from_output |
| replay | 1 | final_emission_meta_from_output |

## `replay_smoke_assertions` — full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
| --- | --- | --- | --- |
| tests/helpers/behavioral_gauntlet_eval.py | test helpers | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/helpers/emission_smoke_assertions.py | test helpers | `final_emission_meta_from_output`, `read_turn_debug_notes` | FEM-read-bridge |
| tests/helpers/transcript_snapshots.py | replay helpers | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_anti_railroading.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_anti_railroading_retry_alignment.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_anti_reset_emission_guard.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_api_narration_path_selection.py | HTTP/pipeline integration | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_block_s_speaker_local_rebind_equivalence.py | speaker/social | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_block_u_finalize_stack_divergence.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_bv3a_observe_referential_clarity_repair.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_bv3e_eligibility_expansion.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_bv4b_concrete_beat_upstream_satisfier.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_c4_narrative_mode_live_pipeline.py | HTTP/pipeline integration | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_context_separation.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_contextual_minimal_repair_regressions.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_dead_turn_detection.py | observability/diagnostics | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_dead_turn_evaluation_threading.py | observability/diagnostics | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_empty_social_retry_regressions.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_fallback_behavior_gate.py | fallback | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_fallback_behavior_repairs.py | fallback | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_fallback_overwrite_containment.py | fallback | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_fallback_shipped_contract_propagation.py | fallback | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_final_emission_boundary_no_semantic_repair.py | final emission gate | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_final_emission_gate_diagnostics.py | final emission gate | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_final_emission_gate_n4.py | final emission gate | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_final_emission_gate_orchestration_order.py | final emission gate | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_final_emission_gate_selector_snapshots.py | final emission gate | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_final_emission_opening_fallback.py | fallback | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_final_emission_visibility.py | final emission gate | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_golden_replay_direct_seam.py | replay | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_interaction_continuity_repair.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_lead_lifecycle_block3_transcript_regression.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_manual_play_latency.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_narration_transcript_regressions.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_narrative_authority_rules.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_narrative_mode_output_validator.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_observational_telemetry_confidence.py | observability/diagnostics | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_player_facing_narration_purity.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_prompt_context.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_referential_clarity_player_coref.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_referential_clarity_strict_social_local_repair.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_response_policy_contracts.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_retry_tone_alignment.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_run_scenario_spine_validation.py | integration/regression | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_scene_state_anchoring.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_scene_transition_authority.py | integration/regression | `read_turn_debug_notes` | debug-notes-bridge |
| tests/test_social_emission_quality.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_social_exchange_emission.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_social_interaction_authority.py | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_speaker_contract_risk.py | speaker/social | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_strict_social_emergency_fallback_dialogue.py | fallback | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_tone_escalation_rules.py | integration/regression | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_transcript_gauntlet_actor_addressing.py | integration/regression | `final_emission_meta_from_output`, `read_final_emission_meta_dict` | mixed/downstream-smoke |
| tests/test_turn_packet_stage_diff_integration.py | HTTP/pipeline integration | `final_emission_meta_from_output` | FEM-read-bridge |
| tests/test_turn_pipeline_shared.py | HTTP/pipeline integration | `read_turn_debug_notes` | debug-notes-bridge |
| tools/bv3d_build_positive_control_corpus.py | tools/analysis | `final_emission_meta_from_output` | FEM-read-bridge |
| tools/bv3e_shape_simulation.py | tools/analysis | `final_emission_meta_from_output` | FEM-read-bridge |

## `gate_integration_smoke` — summary by subsystem

| Subsystem | Importers | Primary symbol |
| --- | --- | --- |
| integration/regression | 22 | apply_final_emission_gate_consumer |
| fallback | 6 | apply_final_emission_gate_consumer |
| final emission gate | 4 | apply_final_emission_gate_consumer |
| test helpers | 2 | apply_final_emission_gate_consumer |
| speaker/social | 2 | apply_final_emission_gate_consumer |
| speaker helpers | 1 | apply_final_emission_gate_consumer |
| HTTP/pipeline integration | 1 | apply_final_emission_gate_consumer |
| replay | 1 | apply_final_emission_gate_consumer |
| tools/analysis | 1 | apply_final_emission_gate_consumer |

## `gate_integration_smoke` — full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
| --- | --- | --- | --- |
| tests/helpers/emission_smoke_assertions.py | test helpers | `apply_final_emission_gate_consumer`, `gm_response_stub` | gate-integration-bridge |
| tests/helpers/strict_social_harness.py | speaker helpers | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/helpers/turn_pipeline_http_fixtures.py | test helpers | `_gm_response`, `gm_response_stub` | mixed/downstream-smoke |
| tests/test_answer_completeness_rules.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_anti_railroading.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_anti_railroading_transcript_regressions.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_anti_reset_emission_guard.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_bv3a_observe_referential_clarity_repair.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_bv4b_concrete_beat_upstream_satisfier.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_c4_narrative_mode_live_pipeline.py | HTTP/pipeline integration | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_context_separation.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_dialogue_plan_final_emission_gate.py | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_dialogue_social_convergence.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_diegetic_fallback_narration.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_fallback_overwrite_containment.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_fallback_shipped_contract_propagation.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_final_emission_answer_exposition_plan_convergence.py | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_final_emission_boundary_convergence.py | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_final_emission_scene_integrity.py | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_golden_replay_direct_seam.py | replay | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_interaction_continuity_repair.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_lead_lifecycle_block3_transcript_regression.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_lead_npc_payoff_and_fallback.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_narration_transcript_regressions.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_narrative_authority_rules.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_narrative_mode_output_validator.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_player_facing_narration_purity.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_prompt_context.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_referential_clarity_strict_social_local_repair.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_response_delta_requirement.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_response_policy_contracts.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_run_scenario_spine_validation.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_scene_destination_binding.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_scene_state_anchoring.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_speaker_contract_enforcement.py | speaker/social | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_speaker_contract_risk.py | speaker/social | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_strict_social_emergency_fallback_dialogue.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_tone_escalation_rules.py | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tests/test_upstream_fast_fallback_block_l.py | fallback | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| tools/bv3d_build_positive_control_corpus.py | tools/analysis | `apply_final_emission_gate_consumer` | gate-integration-bridge |

