# Regression Results

Milestone: `pr_play_grounded_marking_action_integration`. Date: 2026-11-09. Live provider calls: 0. Full suite: not run.

## Grounded marking

```text
.\.venv\Scripts\python.exe -m pytest tests/test_grounded_marking_action.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_grounded_marking_action_integration/marking_action_junit.xml --basetemp=development/tmp/marking_action_focused
```

12 passed / 0 failed / 0 errors / 0 skipped (12 tests). The concealed observation test is included and passed in this run. An earlier combined-process run of that one test hit the playtest request limit after 240 other HTTP tests and is not a product failure. Its isolated rerun passed before this clean file run.

## Focused predecessor selection

```text
.\.venv\Scripts\python.exe -m pytest tests/test_pr_play_76_physical.py tests/test_pr_play_71_persistence_recovery.py tests/test_pr_play_75_persistence.py tests/test_state_authority.py tests/test_pr_play_t06_persistent_manipulation.py tests/test_pr_play_t04_local_action.py tests/test_pr_play_t05_composition.py tests/test_pr_play_preseal_authority.py tests/test_object_instances.py tests/test_object_marking.py tests/test_atomic_character_save.py tests/test_object_marking_inspection.py tests/test_object_observation.py tests/test_object_visibility_authoring.py tests/test_pr_play_60_inventory_projection.py tests/test_snapshots.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_grounded_marking_action_integration/after_focused_junit.xml --basetemp=development/tmp/marking_action_after_focused
```

After, run alone: 574 passed / 0 failed / 0 errors / 0 skipped (574 tests).

Before, run beside another pytest process: 573 passed / 1 failed / 0 errors / 0 skipped (574 tests). The failure was `tests.test_pr_play_71_persistence_recovery::test_atomic_replace_transient_lock[1]`. The serial after run includes that test and passes it.

Module counts inside the after run, all passing: observation 88, inspection 72, marking 63 plus atomic save 13 (76), identity 52, visibility authoring 93, inventory projection 45 plus snapshots 5 (50), preservation files 143 (physical 55, persistence recovery 8, persistence 4, state authority 26, preseal 17, T04 12, T05 15, T06 6).

## Combined selection

Before and after each: 408 passed / 17 failed / 0 errors / 0 skipped (425 tests). New failing identities: none. Newly passing identities: none. Junit: `before_combined_junit.xml`, `after_combined_junit.xml`.

The 17 identities, identical before and after:

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

Historical reference 405/20 is not this measurement. Three historical classification failures already passed in the before run and still pass after. They are not claimed as repairs.

## Disclosure selection

Before: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests). The two failures are the historical `character_secret` pair in `tests/test_pr_play_20_response_confidentiality.py`.

After command also appended the concealed marking test, so the junit is 241 tests and 3 failures. Removing that extra test leaves 240 tests and the same two historical failures. The concealed test passed in the dedicated 12-test run.
