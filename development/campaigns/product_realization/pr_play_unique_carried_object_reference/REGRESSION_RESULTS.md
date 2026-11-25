# Regression

Provider calls stayed disabled. Provider records: 0. External network attempts: 0. The selection is the reliability-rebaseline command list. Results: `artifacts/pr_play_unique_carried_object_reference/combined_final_result.json` and `focused_final_result.json`.

Commands:

```text
python artifacts/pr_play_unique_carried_object_reference/run_regression.py combined_final
python artifacts/pr_play_unique_carried_object_reference/run_regression.py focused_final
```

## Combined

472 tests. 455 passed. 17 failed. Elapsed 628.4 seconds. Pytest exit code 1.

`new_failure_identities`: none. `missing_failure_identities`: none. The 17 identities match the rebaseline.

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

These selected suites do not show that the rest of the repository passes.

## Focused

471 tests. 470 passed. 1 failed. Elapsed 721.4 seconds. Pytest exit code 1.

The only failure is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. `new_failure_identities`: none. `missing_failure_identities`: none.

## Investigated and not kept

Before the publication stamp, a combined run reported 453 passed / 19 failed. The two identities that were not in the rebaseline were both `tests.test_pr_play_preseal_authority::test_http_publication_matches_prepared_authority`: "I inspect the brass token." (`authored_hidden`) and "I inspect the glass kiln schedule." (`unsupported`). The early unmatched return skipped `last_publication` and `referenced_surface_authority`. The stamp restored those fields without incrementing the turn. That result file was replaced by the final combined run. The preseal file then passed, and the final combined run has no new identities.

A focused run started against a leftover `focused_final` basetemp directory reported 469 passed / 2 failed. The extra identity was `tests.test_atomic_character_save::test_precommit_failures_preserve_previous_file[serialization]`, a setup `FileExistsError` (`WinError 183`) on that directory. It is not a product assertion. The directory was removed and the focused selection was run again. That clean run is the focused result above.
