# Deterministic regression verification

Providers stayed disabled. The API key was removed. External sockets were audit-denied. Storage was isolated. Interpretation, expression, host retries, and startup upstream preflight were disabled. No live request was added.

## Combined

Command: `.venv\Scripts\python.exe -u artifacts/pr_play_live_probe_configuration_recovery/run_regression.py combined_close`

455 passed / 17 failed. 472 tests. 785.7s. Pytest exit code 1 because those 17 failed. New failure identities: 0. Missing inherited identities: 0. Provider records: 0. External network attempts: 0.

Inherited identities:

- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`

## Focused

Command: `.venv\Scripts\python.exe -u artifacts/pr_play_live_probe_configuration_recovery/run_regression.py focused_close`

470 passed / 1 failed. 471 tests. 707.7s. Pytest exit code 1. New failure identities: 0. Missing inherited identities: 0. Provider records: 0. External network attempts: 0.

Inherited identity:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Historical comparison remains combined 455/17 and focused 470/1. These slices do not certify the full repository. No production gameplay repair was made for these failures.

Exact argv and environment are in `combined_close_command.json` and `focused_close_command.json`.
