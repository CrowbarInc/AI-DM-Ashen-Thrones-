# Regression results

- combined_baseline: {'passed': 405, 'failed': 20}
- combined_after: {'passed': 405, 'failed': 20}
- focused_after: {'passed': 611}
- topic_focused_before: {'failed': 37, 'passed': 269}
- topic_focused_after: {'passed': 280, 'failed': 26}
- admission_after: {'passed': 32}

Exact combined before/after failure comparison: {"new_failure_identities": [], "resolved_failure_identities": [], "baseline_diff_predecessor": []}

Topic suite has no new failure identities; 11 new-test failures resolve with final owners. Its 26 remaining failures reproduce with captured initial source modules under identical provider-disabled settings. These include legacy HTTP/continuity expectations and expression-generation holdouts with generation disabled. They were not skipped, changed or relabeled as passes. All 22 added tests pass. Commands, stdout and JUnit preserve exact failures; regression_results.json includes full case identities/details. Whole-suite success is not claimed.

Inherited combined identities:

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