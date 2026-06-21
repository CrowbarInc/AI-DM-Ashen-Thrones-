# BV7 — `emission_smoke_assertions` Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only. Maps every direct importer of `tests.helpers.emission_smoke_assertions`.
**Method:** AST + import-regex scan (`scripts/bv7_smoke_facade_discovery.py`); fan-in reconciled with `scripts/bu_final_emission_coupling_discovery.py`.

## Hub baseline (current)

| Metric | Value | Source |
|---|---:|---|
| Fan-in (module, BU scan) | **73** | `docs/audits/BU_import_fan_in_fan_out.csv` |
| Fan-in (AST scan, incl. tools/lazy) | **77** | `artifacts/bv7_smoke_analysis.json` |
| Fan-in (tests) | **69** | BU scan breakdown |
| Fan-in (helpers) | **4** | BU scan breakdown |
| Fan-out (production modules) | **8** | facade lazy imports |
| Public exports | **45** | `tests/helpers/emission_smoke_assertions.py` |
| Module LOC | **620** | same |

**BV5 rank:** #1 ecosystem fan-in hub (73 FI); ~2.6× `final_emission_meta_read` (28 FI).

## Importer summary by subsystem

| Subsystem | Importers | Primary symbols |
|---|---:|---|
| integration/regression | 39 | `final_emission_meta_from_output` (26), `apply_final_emission_gate_consumer` (22), `response_type_contract` (6) |
| final emission gate | 10 | `apply_final_emission_gate_consumer` (4), `response_type_contract` (3), `final_emission_meta_from_output` (2) |
| fallback | 10 | `apply_final_emission_gate_consumer` (6), `final_emission_meta_from_output` (6), `response_type_contract` (3) |
| HTTP/pipeline integration | 4 | `final_emission_meta_from_output` (3), `apply_final_emission_gate_consumer` (1), `assert_final_route_accept_candidate_smoke` (1) |
| speaker/social | 4 | `final_emission_meta_from_output` (2), `apply_final_emission_gate_consumer` (2), `assert_social_grounding_smoke` (1) |
| observability/diagnostics | 2 | `final_emission_meta_from_output` (2) |
| tools/analysis | 2 | `final_emission_meta_from_output` (2), `apply_final_emission_gate_consumer` (1) |
| fallback helpers | 1 | `response_type_contract` (1) |
| speaker helpers | 1 | `apply_final_emission_gate_consumer` (1) |
| replay helpers | 1 | `final_emission_meta_from_output` (1) |
| test helpers | 1 | `_gm_response` (1), `gm_response_stub` (1) |
| replay | 1 | `apply_final_emission_gate_consumer` (1) |
| ownership governance | 1 | `emission_smoke_assertions` (1) |

## Full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
|---|---|---|---|
| `tests/helpers/opening_fallback_evidence.py` | fallback helpers | `response_type_contract` | fallback-projection |
| `tests/helpers/strict_social_harness.py` | speaker helpers | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/helpers/transcript_snapshots.py` | replay helpers | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/helpers/turn_pipeline_http_fixtures.py` | test helpers | `_gm_response`, `gm_response_stub` | test-fixture-helper |
| `tests/test_answer_completeness_rules.py` | integration/regression | `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH`, `apply_answer_completeness_layer`, `apply_final_emission_gate_consumer`, `assert_no_boundary_reorder_repair`, `validate_answer_completeness` | consumer-layer-bridge |
| `tests/test_anti_railroading.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_anti_railroading_retry_alignment.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_anti_railroading_transcript_regressions.py` | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_anti_reset_emission_guard.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_api_narration_path_selection.py` | HTTP/pipeline integration | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | speaker/social | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_block_u_finalize_stack_divergence.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_broad_address_social_bid.py` | integration/regression | `assert_no_unresolved_stock_phrases`, `assert_open_social_solicitation_route` | speaker/social-smoke |
| `tests/test_broadcast_open_call_social.py` | integration/regression | `assert_broadcast_open_call_rejected_smoke`, `assert_open_call_crowd_reaction_wiring_smoke`, `assert_open_call_no_unresolved_retry_smoke`, `assert_open_social_solicitation_route` | speaker/social-smoke |
| `tests/test_bv3a_observe_referential_clarity_repair.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_bv3e_eligibility_expansion.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_bv4b_concrete_beat_upstream_satisfier.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_c4_narrative_mode_live_pipeline.py` | HTTP/pipeline integration | `apply_final_emission_gate_consumer`, `assert_final_route_accept_candidate_smoke`, `assert_final_route_replaced_or_not_accept`, `final_emission_meta_from_output` | route-wiring-smoke |
| `tests/test_context_separation.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_contextual_minimal_repair_regressions.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_dead_turn_detection.py` | observability/diagnostics | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_dialogue_plan_final_emission_gate.py` | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_dialogue_social_convergence.py` | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_diegetic_fallback_narration.py` | fallback | `apply_final_emission_gate_consumer`, `assert_final_route_not_replaced_smoke`, `assert_final_route_present_smoke` | fallback-assertions |
| `tests/test_emission_smoke_assertions_contract.py` | integration/regression | `assert_emission_repair_evidence`, `assert_global_visibility_stock_absent`, `assert_no_advisory_prose`, `assert_procedural_adjudication_smoke`, `enforce_response_type_contract_layer`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_empty_social_retry_regressions.py` | integration/regression | `assert_final_route_replaced_or_not_accept`, `final_emission_meta_from_output` | route-wiring-smoke |
| `tests/test_fallback_behavior_gate.py` | fallback | `final_emission_meta_from_output`, `response_type_contract` | fallback-projection |
| `tests/test_fallback_behavior_repairs.py` | fallback | `final_emission_meta_from_output`, `response_type_contract` | fallback-projection |
| `tests/test_fallback_overwrite_containment.py` | fallback | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | fallback-projection |
| `tests/test_fallback_shipped_contract_propagation.py` | fallback | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | fallback-projection |
| `tests/test_final_emission_answer_exposition_plan_convergence.py` | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_final_emission_boundary_convergence.py` | final emission gate | `apply_answer_completeness_layer`, `apply_final_emission_gate_consumer`, `apply_response_delta_layer` | consumer-layer-bridge |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | final emission gate | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_final_emission_gate_delegator_regression.py` | final emission gate | `emission_smoke_assertions (module)` | mixed/downstream-smoke |
| `tests/test_final_emission_gate_diagnostics.py` | final emission gate | `response_type_contract` | consumer-layer-bridge |
| `tests/test_final_emission_gate_orchestration_order.py` | final emission gate | `response_type_contract` | consumer-layer-bridge |
| `tests/test_final_emission_opening_fallback.py` | fallback | `final_emission_meta_from_output`, `response_type_contract` | fallback-projection |
| `tests/test_final_emission_response_type.py` | final emission gate | `response_type_contract` | consumer-layer-bridge |
| `tests/test_final_emission_scene_integrity.py` | final emission gate | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_final_emission_visibility.py` | final emission gate | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_golden_replay_direct_seam.py` | replay | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_interaction_continuity_repair.py` | integration/regression | `apply_final_emission_gate_consumer`, `assert_continuity_validation_failed_without_repair`, `assert_final_route_not_replaced_smoke`, `assert_final_route_present_smoke`, `final_emission_meta_from_output` | route-wiring-smoke |
| `tests/test_lead_lifecycle_block3_transcript_regression.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_lead_npc_payoff_and_fallback.py` | fallback | `apply_final_emission_gate_consumer` | fallback-assertions |
| `tests/test_manual_play_latency.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_mixed_state_recovery_regressions.py` | integration/regression | `assert_global_visibility_stock_absent`, `assert_no_social_visible_intro_filler_smoke` | hygiene-smoke |
| `tests/test_narration_transcript_regressions.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_narrative_authority_rules.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_narrative_mode_output_validator.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_observational_telemetry_confidence.py` | observability/diagnostics | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_opening_start_seam_regressions.py` | fallback | `has_non_accept_final_route_smoke` | route-wiring-smoke |
| `tests/test_ownership_registry.py` | ownership governance | `emission_smoke_assertions (module)` | ownership-governance |
| `tests/test_player_facing_narration_purity.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_prompt_context.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_referential_clarity_player_coref.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_referential_clarity_strict_social_local_repair.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_response_delta_requirement.py` | integration/regression | `apply_final_emission_gate_consumer`, `apply_response_delta_layer`, `assert_no_boundary_reorder_repair`, `assert_response_delta_boundary_validate_only`, `inspect_response_delta_failure`, `skip_answer_completeness_layer`, `skip_response_delta_layer`, `strict_social_answer_pressure_rd_contract_active`, `validate_response_delta` | consumer-layer-bridge |
| `tests/test_response_policy_contracts.py` | integration/regression | `apply_final_emission_gate_consumer`, `enforce_response_type_contract_layer`, `final_emission_meta_from_output`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_retry_tone_alignment.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_run_scenario_spine_validation.py` | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_scene_destination_binding.py` | integration/regression | `apply_final_emission_gate_consumer` | gate-integration-bridge |
| `tests/test_scene_state_anchoring.py` | integration/regression | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_scene_transition_authority.py` | integration/regression | `read_turn_debug_notes` | FEM-read-bridge |
| `tests/test_social_emission_quality.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_social_exchange_emission.py` | integration/regression | `assert_final_route_replaced_or_not_accept`, `final_emission_meta_from_output` | route-wiring-smoke |
| `tests/test_social_interaction_authority.py` | integration/regression | `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_social_speaker_grounding.py` | speaker/social | `assert_social_grounding_smoke` | speaker/social-smoke |
| `tests/test_speaker_contract_enforcement.py` | speaker/social | `apply_final_emission_gate_consumer`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_speaker_contract_risk.py` | speaker/social | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tests/test_strict_social_emergency_fallback_dialogue.py` | fallback | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | fallback-projection |
| `tests/test_synthetic_smoke.py` | integration/regression | `SMOKE_SYNTHETIC_INTERNAL_LEAK_PATTERNS`, `SMOKE_SYNTHETIC_SCAFFOLD_LEAK_PATTERNS`, `SMOKE_SYNTHETIC_VAGUE_FILLER_PATTERNS` | mixed/downstream-smoke |
| `tests/test_tone_escalation_rules.py` | integration/regression | `apply_final_emission_gate_consumer`, `response_type_contract` | consumer-layer-bridge |
| `tests/test_turn_packet_stage_diff_integration.py` | HTTP/pipeline integration | `assert_final_route_present_smoke`, `final_emission_meta_from_output` | route-wiring-smoke |
| `tests/test_turn_pipeline_shared.py` | HTTP/pipeline integration | `assert_dialogue_lock_non_dialogue_route_smoke`, `assert_dialogue_lock_social_route_smoke`, `assert_emission_repair_evidence`, `assert_global_visibility_stock_absent`, `assert_http_chat_response_smoke`, `assert_no_advisory_prose`, `assert_no_internal_scaffold_labels`, `assert_no_retry_coaching_leak_smoke`, `assert_no_social_visible_intro_filler_smoke`, `assert_no_uncertainty_fallback_stock_smoke`, `assert_no_unresolved_stock_phrases`, `assert_no_validator_voice_smoke`, `assert_player_text_present`, `assert_procedural_adjudication_smoke`, `assert_response_type_contract_surfaces`, `assert_response_type_meta`, `read_turn_debug_notes` | fallback-assertions |
| `tests/test_upstream_fast_fallback_block_l.py` | fallback | `apply_final_emission_gate_consumer` | fallback-assertions |
| `tools/bv3d_build_positive_control_corpus.py` | tools/analysis | `apply_final_emission_gate_consumer`, `final_emission_meta_from_output` | FEM-read-bridge |
| `tools/bv3e_shape_simulation.py` | tools/analysis | `final_emission_meta_from_output` | FEM-read-bridge |

## Top imported symbols (caller fan-in)

| Symbol | Consumer files |
|---|---:|
| `final_emission_meta_from_output` | 44 |
| `apply_final_emission_gate_consumer` | 38 |
| `response_type_contract` | 14 |
| `assert_final_route_replaced_or_not_accept` | 3 |
| `assert_final_route_present_smoke` | 3 |
| `assert_global_visibility_stock_absent` | 3 |
| `apply_answer_completeness_layer` | 2 |
| `assert_no_boundary_reorder_repair` | 2 |
| `assert_no_unresolved_stock_phrases` | 2 |
| `assert_open_social_solicitation_route` | 2 |
| `assert_final_route_not_replaced_smoke` | 2 |
| `assert_emission_repair_evidence` | 2 |
| `assert_no_advisory_prose` | 2 |
| `assert_procedural_adjudication_smoke` | 2 |
| `enforce_response_type_contract_layer` | 2 |

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv7_smoke_analysis.json` | Per-importer symbol extraction |
| `docs/audits/BU_import_fan_in_fan_out.csv` | Official module fan-in |
| `docs/audits/BU_caller_fan_in.csv` | Per-symbol caller fan-in |
| `tests/helpers/emission_smoke_assertions.py` | Facade module doc + exports |
