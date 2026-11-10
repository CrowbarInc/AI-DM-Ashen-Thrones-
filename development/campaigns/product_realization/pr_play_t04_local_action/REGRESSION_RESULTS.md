# Regression results

Pre-edit identity is the predecessor manifest: 1,296 paths, 0 hash differences before this cycle’s edits. The predecessor combined result on that tree was **393 passed / 20 failed** of 413. This cycle did not re-execute that selection before editing because the hashes matched. The after selection below is the fresh run.

| Selection | Before | After |
|---|---:|---:|
| Main, 235 | 222/13 | 222/13 |
| Authority, 146 | 139/7 | 142/4 |
| Pre-seal authority, 17 | 17/0 | 17/0 |
| New composition, 15 | 15/0 | 15/0 |
| New local action, 12 | — | 12/0 |
| Combined | 393/20 of 413 | **408/17 of 425** |

Errors: 0. Skips: 0. Collection errors: 0. Live provider calls: **0**.

The authority difference is three tests that failed in the predecessor and passed here: `test_duplicate_refusal_does_not_publish`, `test_two_refusals_then_gameplay_advances`, and `test_save_reload_keeps_the_preceding_publication`. Their phrase is “Good day, Gate Guard.” The local-action resolver returns none before any outcome. Prior diagnostics were an events-file assertion, `RuntimeError: This portal is not running`, and a missing operational-refusal log class. An isolated rerun also passed 3/3. They are not claimed as a classification repair.

No new failure identity appeared. The updated post-NPC handoff assertion expects the repaired T04 completion; it is the limitation this cycle removes, not an obsolete assertion edited to hide an unrelated failure.

## Failure identities that remain

- `tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one`
- `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing`
- `tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working`

## Commands

From the repository root, `.venv/Scripts/python.exe`:

```text
python -m pytest tests/test_pr_play_t04_local_action.py tests/test_pr_play_post_npc_handoff.py tests/test_pr_play_t05_composition.py -q --tb=line -p no:cacheprovider
python -m pytest <main 235> <authority 146> tests/test_pr_play_preseal_authority.py tests/test_pr_play_t05_composition.py tests/test_pr_play_t04_local_action.py -q --tb=line -p no:cacheprovider --junitxml=artifacts/pr_play_t04_local_action/after_regression_junit.xml
python artifacts/pr_play_t04_local_action/run_sequence.py
python -m pytest tests/test_pr_play_76_physical.py tests/test_pr_play_23_local_interaction.py -q --tb=line -p no:cacheprovider
```

The combined pytest argument list is the predecessor main list, authority list, pre-seal module, T05 composition module, and the new local-action module. Junit: 425 tests, 17 failures, 0 errors, 0 skipped. Physical module: 32 passed. PR-PLAY-23: 3 failed outside this selection; see `NEGATIVE_CONTROLS.md`.
