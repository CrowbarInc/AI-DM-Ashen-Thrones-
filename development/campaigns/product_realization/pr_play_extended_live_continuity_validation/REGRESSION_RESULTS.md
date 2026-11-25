# Regression results

Run after the live session, with live interpretation, expression generation, and provider retries disabled. The API key and the provider-call disable flag were removed from the suite environment. An audit hook recorded external network attempts. None were recorded. Pytest's own exit code is 1 for combined and focused because the inherited failures remain. The runner process exited 0.

| Suite | Tests | Passed | Failed | New identities | Missing identities | Elapsed |
|---|---:|---:|---:|---:|---:|---:|
| Combined | 472 | 455 | 17 | 0 | 0 | 102.03 s |
| Focused | 471 | 470 | 1 | 0 | 0 | 168.95 s |
| Scoped | 191 | 191 | 0 | 0 | 0 | 60.77 s |
| Recall acceptance | 71 | 71 | 0 | 0 | 0 | 5.7 s |

The recall figure is the existing 71-row offline harness, re-executed without overwriting its historical `acceptance_matrix.json`. A separate pytest command stored beside that harness selects the same 191 tests as the scoped suite. That command also passed 191/0. It is not a second 71-test result, and it is not counted again.

Combined identities, unchanged from the prior baseline:

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

Focused identity, unchanged: `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`.

Evidence: `artifacts/pr_play_extended_live_continuity_validation/live_execution/regression/`.
