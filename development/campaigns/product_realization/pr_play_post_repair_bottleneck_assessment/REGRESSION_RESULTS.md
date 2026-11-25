# Regression results

No production code was changed. Provider calls and retries stayed disabled. Experimental physical adjudication stayed unset.

## Combined selection

The established combined command from `artifacts/pr_play_ordinary_semantic_admission/combined_verified_command.txt`.

| Result | Count |
|---|---:|
| Passed | 405 |
| Failed | 20 |
| Errors | 0 |
| Skipped | 0 |
| Total | 425 |
| Duration | 488.644 s |

Failure identities match `artifacts/pr_play_authored_topic_retrieval/regression_results.json` combined_after. New identities: none. Resolved identities: none.

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
- `tests.test_pr_play_79df3_classification::test_duplicate_refusal_does_not_publish`
- `tests.test_pr_play_79df3_classification::test_two_refusals_then_gameplay_advances`
- `tests.test_pr_play_79df3_classification::test_save_reload_keeps_the_preceding_publication`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`

## Focused preservation

The established focused command. 611 passed, 0 failed, 0 errors, 0 skipped. Duration 1979.109 s. This selection covers physical nonexecution, authored travel and local action, notice and scene composition, marking lifecycle, object identity, save/reload, snapshots, and publication checks included in that command.

## Recent gameplay modules

132 tests, 128 passed, 4 failed, 0 errors. Duration 73.873 s.

Fully passed: ordinary semantic admission, grounded unresolved-action handling, grounded information ownership, authored topic retrieval, and the disclosure-boundary module.

The four failures are the same social-question relevance identities already recorded in the predecessor topic suite:

- `tests.test_social_question_relevance_answer_selection::test_general_http_ask_a_not_b`
- `tests.test_social_question_relevance_answer_selection::test_general_http_relevant_hook_still_lands`
- `tests.test_social_question_relevance_answer_selection::test_general_http_unauthorized_no_leak`
- `tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance`

They were not reclassified as passes. The wider historical topic suite's other inherited failures were not re-executed as a separate 306-test run; the new authored-topic tests, which were the last repair's additions, passed.

JUnit: `artifacts/pr_play_post_repair_bottleneck_assessment/combined.xml`, `focused.xml`, `preservation_recent.xml`.
