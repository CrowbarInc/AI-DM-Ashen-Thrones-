# Regression Results

Milestone: `pr_play_grounded_marking_removal`. Date: 2026-11-09. Live provider calls: 0. Full suite: not run.

## Removal and predecessor marking tests

`tests/test_grounded_marking_removal.py`, `tests/test_player_marking_observation.py`, and `tests/test_grounded_marking_action.py`: 37 passed / 0 failed before the focused command. Of those, 15 are the new removal tests. Junit for the predecessor pair before the edit: `artifacts/pr_play_grounded_marking_removal/before_new_junit.xml` (22 passed).

## Focused modules

```text
.\.venv\Scripts\python.exe -m pytest tests/test_pr_play_76_physical.py tests/test_pr_play_71_persistence_recovery.py tests/test_pr_play_75_persistence.py tests/test_state_authority.py tests/test_pr_play_t06_persistent_manipulation.py tests/test_pr_play_t04_local_action.py tests/test_pr_play_t05_composition.py tests/test_pr_play_preseal_authority.py tests/test_object_instances.py tests/test_object_marking.py tests/test_atomic_character_save.py tests/test_object_marking_inspection.py tests/test_object_observation.py tests/test_object_visibility_authoring.py tests/test_pr_play_60_inventory_projection.py tests/test_snapshots.py tests/test_grounded_marking_action.py tests/test_player_marking_observation.py tests/test_grounded_marking_removal.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_grounded_marking_removal/after_focused_junit.xml --basetemp=development/tmp/removal_after_focused
```

611 passed / 0 failed / 0 errors / 0 skipped (611 tests). Time 495.083 seconds. The predecessor focused count was 596. The difference is the 15 removal tests.

## Combined selection

Before, recorded before `game/api.py` was edited:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_pr_play_79a_continuity.py tests/test_pr_eb_conversational_continuity.py tests/test_pr_eg_r1_continuity.py tests/test_referenced_surface_grounding_inspection_resolution.py tests/test_pr_play_39_action_admission.py tests/test_at_opt_02_retreat_and_budget.py tests/test_at_opt_04_mixed_key_policy.py tests/test_at_opt_06_instruction_eligibility.py tests/test_at_opt_06_same_scene_transition.py tests/test_narrative_planning_transition_node.py tests/test_prompt_context_transition_node_consumption.py tests/test_pr_ed_provider_efficiency.py tests/test_pr_br_continuation18_immutable_boundary.py tests/test_perception_narration_authority_audible_non_invention.py tests/test_pr_play_post_npc_handoff.py tests/test_pr_play_46_mechanical_boundary.py tests/test_pr_play_79df3_classification.py tests/test_pr_play_79b_integration.py tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload tests/test_pr_play_preseal_authority.py tests/test_pr_play_t05_composition.py tests/test_pr_play_t04_local_action.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_grounded_marking_removal/before_combined_junit.xml --basetemp=development/tmp/removal_before_combined
```

405 passed / 20 failed / 0 errors / 0 skipped (425 tests). Time 147.689 seconds.

After, same command with `after_combined_junit.xml` and `development/tmp/removal_after_combined`: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). Time 60.854 seconds.

New failing identities: none. Newly passing identities: none.

The 20 identities, identical before and after:

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

Seventeen match the predecessor's combined run. These three failed in this cycle's before run as well, so they are not a new regression from the removal edit:

- `test_duplicate_refusal_does_not_publish`
- `test_two_refusals_then_gameplay_advances`
- `test_save_reload_keeps_the_preceding_publication`

They are the known fluctuating classification trio. This cycle did not repair them and did not add a fourth.
