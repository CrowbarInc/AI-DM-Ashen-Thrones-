# Regression Results

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failures: []; resolved: [].

76 new marking/atomic tests; 52 identity tests; 50 inventory/snapshot controls; 143 preservation controls passed, separately selected.

Exact commands/arguments/executable and elapsed times: regression_results.json plus *_command.json / *_execution.json. Selections kept separate; no totals combined to imply improvement. Original authoritative 425-node command comes from artifacts/pr_play_t06_persistent_manipulation/baseline_command.json. Preservation selection is unchanged architecture validation_command.json. Covers T04/T05/T06, closed inspection, physical persistence and state authority; combined covers travel/immutable publication. One after_combined attempt died in installed openai import with Windows access violation; no result was assigned. Same selection rerun final_combined completed. No collection errors/skips in completed runs. One pre-existing test_two_refusals_then_gameplay_advances failure stays at TestClient.__exit__/wait_shutdown: before RuntimeError(This portal is not running), after concurrent.futures.CancelledError. Exact traces retained; this is a teardown diagnostic variation at the same failing identity, not a claimed product repair. Causal origin unproven. The other nineteen normalized failure diagnostics match after removing addresses, run temp paths and random turn IDs. No live provider calls or network attempts escaped guards. No full-suite or Gameplay Benchmark claim.

Known before/after failure identities:

- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working
- tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver
- tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing
- tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid
- tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one
- tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded
- tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive
- tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish
- tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances
- tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication
- tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal
- tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context
- tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop
- tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload
