# Regression Results

Milestone: `pr_play_broad_gameplay_evaluation`. Evaluation dates: 2026-11-09–10 (America/New_York).

Current combined baseline: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed. New failing identities: []; newly passing: []. These are current runs, not copied historical totals.

Focused owner selection: 611 passed / 0 failed / 0 errors / 0 skipped (611 tests). Includes all 37 marking lifecycle tests (15 removal, 10 observation, 12 creation), state authority, disclosure, visibility authoring, storage failure/atomicity, snapshots, physical/publication, preseal and T04/T05 modules. Full suite: not run. The established selection is taken verbatim from predecessor REGRESSION_RESULTS.md; no test or expectation was edited.

Exact commands: `artifacts/pr_play_broad_gameplay_evaluation/combined_command.txt`, `combined_after_command.txt`, `focused_command.txt`. Outputs and JUnit use the corresponding prefixes in that directory. Invocation: `.\.venv\Scripts\python.exe artifacts/pr_play_broad_gameplay_evaluation/run_regression.py combined` (then `focused`, `combined_after`). Twelve-turn command: `.\.venv\Scripts\python.exe artifacts/pr_play_broad_gameplay_evaluation/run_evaluation.py`; after-run replay/controls: `followup_evaluation.py`. Analysis: `analyze.py`. Provider-disabling environment is explicit in scripts and existing pytest guards block actual model clients.

Exact 20 combined failing identities (same baseline/after):

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

The classification trio that historically fluctuated is not excused away: all identities above are recorded exactly as measured. No new failure identity appeared. Results of after-run twelve-turn replay: 12/12 texts unchanged from before and immediate predecessor. No production behavior repair claimed.
