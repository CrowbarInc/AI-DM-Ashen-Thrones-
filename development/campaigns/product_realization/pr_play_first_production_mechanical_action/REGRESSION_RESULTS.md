# Regression results

Runner: `artifacts/pr_play_first_production_mechanical_action/run_regression.py`. Selections: the campaign-ruleset-binding combined and focused lists. Isolated storage. Provider records 0. External network attempts empty. The new production-action tests are not in those selections. They are reported in `ACCEPTANCE_MATRIX.md`.

| Run | Tests | Passed | Failed | New identities | Missing identities | Provider records | Elapsed |
|---|---:|---:|---:|---|---|---:|---:|
| Combined before | 472 | 455 | 17 | none | none | 0 | 957.5 s |
| Combined after | 472 | 455 | 17 | none | none | 0 | 839.4 s |
| Focused before | 471 | 470 | 1 | none | none | 0 | 1309.7 s |
| Focused after | 471 | 470 | 1 | none | none | 0 | 1263.9 s |

The after runs overlapped with the broad replay, so the shorter elapsed times are not a performance claim.

The 17 combined failures, before and after:

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

The focused failure, before and after, is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`.

No test was weakened or deleted to obtain this match. The equipment assertion in `tests/test_mechanical_action_contract.py` now requires `resolve_mechanical_action` to leave equipment unresolved and proposal-free. That file is outside the combined and focused selections. It passed in the separate ruleset run.
