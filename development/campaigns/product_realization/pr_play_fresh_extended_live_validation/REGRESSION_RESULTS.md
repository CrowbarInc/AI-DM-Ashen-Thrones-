# Regression results

| Deterministic suite | Historical pass / fail | Pre-run | Post-run | Post-run new identities |
| --- | --- | --- | --- | ---: |
| Combined | 455 / 17 | 455 / 17 | 455 / 17 | 0 |
| Focused | 470 / 1 | 470 / 1 | 470 / 1 | 0 |
| Scoped | 191 / 0 | 191 / 0 | 191 / 0 | 0 |
| Historical recall | 71 / 0 | 71 / 0 | 71 / 0 | 0 |
| Inspection admission | 64 / 0 | 64 / 0 | 64 / 0 | 0 |
| Statement ownership | 65 / 0 | 65 / 0 | 65 / 0 | 0 |
| NPC addressee and social commitment | 71 / 0 | 71 / 0 | 71 / 0 | 0 |
| Social grounding reconciliation | 37 / 0 | 37 / 0 | 37 / 0 | 0 |
| Incidental posture | 85 / 0 | 85 / 0 | 85 / 0 | 0 |
| Current-scene evidence scope | 84 / 0 | 84 / 0 | 84 / 0 | 0 |

The exact prior JUnit test identities were rerun in isolated processes. Historical recall uses the existing 71-case replay matrix. The 84 current-scene cases come from the prior final and extra JUnit captures. External provider networking was blocked during these deterministic runs.

All ten suites matched their prior pass/fail totals. All inherited failure identities were identical before and after live execution.

## Combined inherited failures

- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`

## Focused inherited failures

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

[Machine-readable comparison](evidence/regression_comparison.json) · [Raw regression evidence](evidence/regression/)
