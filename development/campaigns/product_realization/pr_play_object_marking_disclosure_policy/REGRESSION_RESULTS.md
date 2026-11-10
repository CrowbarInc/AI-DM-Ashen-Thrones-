# Regression Results

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failures: []; newly passing: [].

88 observation tests passed; supplemental visibility/confidentiality/publication: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests), identical failure identities/pass count with the new module import-blocked in a feature-absent control.

Separate identical predecessor selections: inspection: 72 before / 72 after; marking: 76 before / 76 after; identity: 52 before / 52 after; inventory_snapshot: 50 before / 50 after; preservation: 143 before / 143 after. No overlaps are summed into combined totals. Supplemental coverage does not replace the established before/after command. Its two failures are tests/test_pr_play_20_response_confidentiality.py::test_successful_start_serialized_boundary (HTTP 422 versus expected 200) and ::test_rejected_turn_with_composed_state (missing character_secret in existing player DTO). These are unrelated existing contract/fixture disagreements; no repair is attempted. Reference rerun explicitly blocks importing game.object_observation, verifies it never loaded, and uses the exact same prior-source bytes/selection: 238 passed / 2 failed, same identities. This is a post-implementation feature-absent control, not a fabricated pre-edit run. Existing production source hashes are all identical to entry.

Combined protects immutable publication/travel and narration; preservation protects state authority, T04/T05/T06 and closed inspection. Zero collection errors/skips and zero live provider/network calls. Full suite not run. All exact failure texts and command arrays retained in regression_results.json.

Baseline failure identities:

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

Exact commands:

### before_combined

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_79a_continuity.py", "tests/test_pr_eb_conversational_continuity.py", "tests/test_pr_eg_r1_continuity.py", "tests/test_referenced_surface_grounding_inspection_resolution.py", "tests/test_pr_play_39_action_admission.py", "tests/test_at_opt_02_retreat_and_budget.py", "tests/test_at_opt_04_mixed_key_policy.py", "tests/test_at_opt_06_instruction_eligibility.py", "tests/test_at_opt_06_same_scene_transition.py", "tests/test_narrative_planning_transition_node.py", "tests/test_prompt_context_transition_node_consumption.py", "tests/test_pr_ed_provider_efficiency.py", "tests/test_pr_br_continuation18_immutable_boundary.py", "tests/test_perception_narration_authority_audible_non_invention.py", "tests/test_pr_play_post_npc_handoff.py", "tests/test_pr_play_46_mechanical_boundary.py", "tests/test_pr_play_79df3_classification.py", "tests/test_pr_play_79b_integration.py", "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate", "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone", "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome", "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context", "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop", "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload", "tests/test_pr_play_preseal_authority.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_t04_local_action.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_combined_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_combined_pytest"]
```

405 passed / 20 failed / 0 errors / 0 skipped (425 tests)

### before_inspection

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking_inspection.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_inspection_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_inspection_pytest"]
```

72 passed / 0 failed / 0 errors / 0 skipped (72 tests)

### before_marking

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking.py", "tests/test_atomic_character_save.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_marking_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_marking_pytest"]
```

76 passed / 0 failed / 0 errors / 0 skipped (76 tests)

### before_identity

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_instances.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_identity_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_identity_pytest"]
```

52 passed / 0 failed / 0 errors / 0 skipped (52 tests)

### before_inventory_snapshot

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_60_inventory_projection.py", "tests/test_snapshots.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_inventory_snapshot_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_inventory_snapshot_pytest"]
```

50 passed / 0 failed / 0 errors / 0 skipped (50 tests)

### before_preservation

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_76_physical.py", "tests/test_pr_play_71_persistence_recovery.py", "tests/test_pr_play_75_persistence.py", "tests/test_state_authority.py", "tests/test_pr_play_t06_persistent_manipulation.py", "tests/test_pr_play_t04_local_action.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_preseal_authority.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\before_preservation_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_before_preservation_pytest"]
```

143 passed / 0 failed / 0 errors / 0 skipped (143 tests)

### after_combined

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_79a_continuity.py", "tests/test_pr_eb_conversational_continuity.py", "tests/test_pr_eg_r1_continuity.py", "tests/test_referenced_surface_grounding_inspection_resolution.py", "tests/test_pr_play_39_action_admission.py", "tests/test_at_opt_02_retreat_and_budget.py", "tests/test_at_opt_04_mixed_key_policy.py", "tests/test_at_opt_06_instruction_eligibility.py", "tests/test_at_opt_06_same_scene_transition.py", "tests/test_narrative_planning_transition_node.py", "tests/test_prompt_context_transition_node_consumption.py", "tests/test_pr_ed_provider_efficiency.py", "tests/test_pr_br_continuation18_immutable_boundary.py", "tests/test_perception_narration_authority_audible_non_invention.py", "tests/test_pr_play_post_npc_handoff.py", "tests/test_pr_play_46_mechanical_boundary.py", "tests/test_pr_play_79df3_classification.py", "tests/test_pr_play_79b_integration.py", "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate", "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone", "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome", "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context", "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop", "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload", "tests/test_pr_play_preseal_authority.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_t04_local_action.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_combined_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_combined_pytest"]
```

405 passed / 20 failed / 0 errors / 0 skipped (425 tests)

### after_inspection

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking_inspection.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_inspection_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_inspection_pytest"]
```

72 passed / 0 failed / 0 errors / 0 skipped (72 tests)

### after_marking

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_marking.py", "tests/test_atomic_character_save.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_marking_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_marking_pytest"]
```

76 passed / 0 failed / 0 errors / 0 skipped (76 tests)

### after_identity

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_instances.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_identity_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_identity_pytest"]
```

52 passed / 0 failed / 0 errors / 0 skipped (52 tests)

### after_inventory_snapshot

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_60_inventory_projection.py", "tests/test_snapshots.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_inventory_snapshot_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_inventory_snapshot_pytest"]
```

50 passed / 0 failed / 0 errors / 0 skipped (50 tests)

### after_preservation

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_76_physical.py", "tests/test_pr_play_71_persistence_recovery.py", "tests/test_pr_play_75_persistence.py", "tests/test_state_authority.py", "tests/test_pr_play_t06_persistent_manipulation.py", "tests/test_pr_play_t04_local_action.py", "tests/test_pr_play_t05_composition.py", "tests/test_pr_play_preseal_authority.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\after_preservation_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_after_preservation_pytest"]
```

143 passed / 0 failed / 0 errors / 0 skipped (143 tests)

### verified_observation

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_object_observation.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\verified_observation_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_verified_observation_pytest"]
```

88 passed / 0 failed / 0 errors / 0 skipped (88 tests)

### additional_visibility

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_63_disclosure.py", "tests/test_pr_play_65_authoritative_disclosure.py", "tests/test_final_emission_visibility.py", "tests/test_final_emission_visibility_fallback.py", "tests/test_pr_play_20_response_confidentiality.py", "tests/test_pr_play_66_publication.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\additional_visibility_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_additional_visibility_pytest"]
```

238 passed / 2 failed / 0 errors / 0 skipped (240 tests)

### reference_visibility

```text
C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
["tests/test_pr_play_63_disclosure.py", "tests/test_pr_play_65_authoritative_disclosure.py", "tests/test_final_emission_visibility.py", "tests/test_final_emission_visibility_fallback.py", "tests/test_pr_play_20_response_confidentiality.py", "tests/test_pr_play_66_publication.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_object_marking_disclosure_policy\\reference_visibility_junit.xml", "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\marking_disclosure_reference_visibility_pytest"]
```

238 passed / 2 failed / 0 errors / 0 skipped (240 tests)
