# Regression Results

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failures: []; newly passing: [].

72 inspection/removal tests passed. Separate predecessor controls: 76 marking/atomic, 52 identity, 50 inventory/snapshot and 143 preservation passed before and after.

Same selections compared before/after; no totals from overlapping suites added. Combined covers travel/immutable publication and baseline admission/narration controls; preservation selection covers T04/T05/T06, closed inspection, physical persistence and state authority. No live provider calls; no external network attempts in completed runners. Full suite not run. Exact baseline failure identities:

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

Exact commands (Python executable and argument arrays), totals, elapsed times and complete failure text are also in regression_results.json and *_command.json / *_execution.json.

### before_combined

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_79a_continuity.py", "tests/test_pr_eb_conversational_continuity.py", "tests/test_pr_eg_r1_continuity.py", "tests/test_referenced_surface_grounding_inspection_resolution.py", "tests/test_pr_play_39_action_admission.py", "tests/test_at_opt_02_retreat_and_budget.py", "tests/test_at_opt_04_mixed_key_policy.py", "tests/test_at_opt_06_instruction_eligibility.py", "tests/test_at_opt_06_same_scene_transition.py", "tests/test_narrative_planning_transition_node.py", "tests/test_prompt_context_transition_node_consumption.py", "tests/test_pr_ed_provider_efficiency.py", "tests/test_pr_br_continuation18_immutable_boundary.py", "tests/test_perception_narration_authority_audible_non_invention.py", "tests/test_pr_play_post_npc_handoff.py", "tests/test_pr_play_46_mechanical_boundary.py", "tests/test_pr_play_79df3_classification.py", "tests/test_pr_play_79b_integration.py", "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate", "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone", "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome", "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context", "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop", "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload", "tests/test_pr_play_preseal_authority.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_t04_local_action.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\before_combined_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_before_combined_pytest"]
```

405 passed / 20 failed / 0 errors / 0 skipped (425 tests)

### before_marking

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking.py", "tests/test_atomic_character_save.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\before_marking_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_before_marking_pytest"]
```

76 passed / 0 failed / 0 errors / 0 skipped (76 tests)

### before_identity

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_instances.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\before_identity_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_before_identity_pytest"]
```

52 passed / 0 failed / 0 errors / 0 skipped (52 tests)

### before_inventory_snapshot

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_60_inventory_projection.py", "tests/test_snapshots.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\before_inventory_snapshot_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_before_inventory_snapshot_pytest"]
```

50 passed / 0 failed / 0 errors / 0 skipped (50 tests)

### before_preservation

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_76_physical.py", "tests/test_pr_play_71_persistence_recovery.py", "tests/test_pr_play_75_persistence.py", "tests/test_state_authority.py", "tests/test_pr_play_t06_persistent_manipulation.py", "tests/test_pr_play_t04_local_action.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_preseal_authority.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\before_preservation_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_before_preservation_pytest"]
```

143 passed / 0 failed / 0 errors / 0 skipped (143 tests)

### after_combined

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_79a_continuity.py", "tests/test_pr_eb_conversational_continuity.py", "tests/test_pr_eg_r1_continuity.py", "tests/test_referenced_surface_grounding_inspection_resolution.py", "tests/test_pr_play_39_action_admission.py", "tests/test_at_opt_02_retreat_and_budget.py", "tests/test_at_opt_04_mixed_key_policy.py", "tests/test_at_opt_06_instruction_eligibility.py", "tests/test_at_opt_06_same_scene_transition.py", "tests/test_narrative_planning_transition_node.py", "tests/test_prompt_context_transition_node_consumption.py", "tests/test_pr_ed_provider_efficiency.py", "tests/test_pr_br_continuation18_immutable_boundary.py", "tests/test_perception_narration_authority_audible_non_invention.py", "tests/test_pr_play_post_npc_handoff.py", "tests/test_pr_play_46_mechanical_boundary.py", "tests/test_pr_play_79df3_classification.py", "tests/test_pr_play_79b_integration.py", "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate", "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone", "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome", "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context", "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop", "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload", "tests/test_pr_play_preseal_authority.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_t04_local_action.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\after_combined_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_after_combined_pytest"]
```

405 passed / 20 failed / 0 errors / 0 skipped (425 tests)

### after_marking

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking.py", "tests/test_atomic_character_save.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\after_marking_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_after_marking_pytest"]
```

76 passed / 0 failed / 0 errors / 0 skipped (76 tests)

### after_identity

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_instances.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\after_identity_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_after_identity_pytest"]
```

52 passed / 0 failed / 0 errors / 0 skipped (52 tests)

### after_inventory_snapshot

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_60_inventory_projection.py", "tests/test_snapshots.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\after_inventory_snapshot_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_after_inventory_snapshot_pytest"]
```

50 passed / 0 failed / 0 errors / 0 skipped (50 tests)

### after_preservation

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_76_physical.py", "tests/test_pr_play_71_persistence_recovery.py", "tests/test_pr_play_75_persistence.py", "tests/test_state_authority.py", "tests/test_pr_play_t06_persistent_manipulation.py", "tests/test_pr_play_t04_local_action.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_preseal_authority.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\after_preservation_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_after_preservation_pytest"]
```

143 passed / 0 failed / 0 errors / 0 skipped (143 tests)

### final_inspection

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking_inspection.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\final_inspection_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_final_inspection_pytest"]
```

72 passed / 0 failed / 0 errors / 0 skipped (72 tests)

### bounded_performance

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking_inspection.py::test_bounded_measurements", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_inspection\\bounded_performance_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_inspection_bounded_performance_pytest"]
```

1 passed / 0 failed / 0 errors / 0 skipped (1 tests)
