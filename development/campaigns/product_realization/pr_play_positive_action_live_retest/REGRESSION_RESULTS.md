# Regression results

## Authorized live continuation

The same provider-disabled scoped selection was rerun for the continuation and passed 191/191 with zero external network attempts. The retained combined 455 passed / 17 inherited failures and focused 470 passed / 1 inherited failure were reused. All 405 production/data files matched the preparation checkpoint by SHA-256. The current scoped run found zero new failures. The broader suites were last run during preparation.

## Retained preparation evidence

Current runs used the same established test selections as the immediately preceding milestone. Storage and basetemp paths were isolated and external networking was blocked. Exact command arguments, JUnit, logs and identity comparisons are in the review bundle. Tests and production code were preserved.

```powershell
.venv/Scripts/python.exe artifacts/pr_play_positive_action_live_retest/run_regression.py combined_final
.venv/Scripts/python.exe artifacts/pr_play_positive_action_live_retest/run_regression.py focused_final
.venv/Scripts/python.exe artifacts/pr_play_positive_action_live_retest/run_acceptance.py
```

| Suite | Historical | Current | New identities | Missing historical identities |
|---|---|---|---:|---:|
| Combined | 455 passed / 17 failed | 455 passed / 17 failed | 0 | 0 |
| Focused | 470 passed / 1 failed | 470 passed / 1 failed | 0 | 0 |
| Scoped | 191 passed / 0 failed | 191 passed / 0 failed | 0 | 0 |

## Combined failure identities

- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload` (inherited)
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive` (inherited)
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded` (inherited)
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one` (inherited)
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid` (inherited)
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop` (inherited)
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context` (inherited)
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver` (inherited)
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing` (inherited)
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated` (inherited)
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working` (inherited)

## Focused failure identities

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution` (inherited)

## Scoped failure identities

No failures.
