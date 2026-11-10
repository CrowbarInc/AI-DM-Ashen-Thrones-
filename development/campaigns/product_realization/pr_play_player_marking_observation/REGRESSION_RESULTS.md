# Regression Results

Milestone: `pr_play_player_marking_observation`. Date: 2026-11-09. Live provider calls: 0. Full suite: not run.

## New observation and marking tests

`tests/test_player_marking_observation.py`: 10 passed / 0 failed.

`tests/test_grounded_marking_action.py`: 12 passed / 0 failed. The publication-failure case now expects the committed sentence and one marking, including after the request-lane cache is cleared.

## Focused modules

```text
.\.venv\Scripts\python.exe -m pytest tests/test_pr_play_76_physical.py tests/test_pr_play_71_persistence_recovery.py tests/test_pr_play_75_persistence.py tests/test_state_authority.py tests/test_pr_play_t06_persistent_manipulation.py tests/test_pr_play_t04_local_action.py tests/test_pr_play_t05_composition.py tests/test_pr_play_preseal_authority.py tests/test_object_instances.py tests/test_object_marking.py tests/test_atomic_character_save.py tests/test_object_marking_inspection.py tests/test_object_observation.py tests/test_object_visibility_authoring.py tests/test_pr_play_60_inventory_projection.py tests/test_snapshots.py tests/test_grounded_marking_action.py tests/test_player_marking_observation.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_player_marking_observation/after_focused_junit.xml --basetemp=development/tmp/player_observation_after_focused
```

596 passed / 0 failed / 0 errors / 0 skipped (596 tests).

The predecessor file list inside that run is 574 passed. Module counts: observation 88, inspection 72, marking 63, atomic save 13, identity 52, visibility authoring 93, inventory projection 45, snapshots 5, physical 55, persistence recovery 8, persistence 4, state authority 26, preseal 17, T04 12, T05 15, T06 6. Added in the same command: grounded marking 12, player observation 10.

## Combined selection

Before and after each: 408 passed / 17 failed / 0 errors / 0 skipped (425 tests). New failing identities: none. Newly passing identities: none.

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
