# Regression results

Selections and environment match the narration-turn-integrity runner: live interpretation, expression generation, provider retries, and upstream preflight disabled; provider-calls flag, physical adjudication, and `OPENAI_API_KEY` removed; non-local sockets blocked; storage isolated. Predecessor: `artifacts/pr_play_ai_dm_reliability_rebaseline`. Pytest exit 1 is the inherited failure count. The runner exits 0 when `new_failure_identities` is empty.

## Combined

Command: `.venv\Scripts\python.exe -u artifacts/pr_play_live_carried_object_grounding/run_regression.py combined_close`

Official rerun after the unresolved-examine deferral:

- Tests: 472
- Passed: 455
- Failed: 17
- Elapsed: 964.3 s
- Provider records: 0
- External network attempts: none
- New failure identities: none
- Missing failure identities: none
- Predecessor: 455 passed / 17 failed

Inherited identities:

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

An earlier combined run, before unknown scene examines were returned to the existing referent owner, was 454 passed / 18 failed. The extra identity was `tests.test_pr_play_39_action_admission::test_missing_footprints_are_not_created` (`DECLINE` / `referent_not_in_scene` observed as `CLARIFY`). That test passes on the official rerun and is not in the failure list above. The result file records the official rerun.

## Focused

Command: `.venv\Scripts\python.exe -u artifacts/pr_play_live_carried_object_grounding/run_regression.py focused_close`

- Tests: 471
- Passed: 470
- Failed: 1
- Elapsed: 1012.3 s
- Provider records: 0
- External network attempts: none
- New failure identities: none
- Missing failure identities: none
- Predecessor: 470 passed / 1 failed

The remaining identity is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. Assertion: resolution must have `prompt`.

## Adjacent

`tests/test_unique_carried_object_reference.py`, `tests/test_inventory_object_reference_binding.py`, and `tests/test_pr_dh_live_interpretation.py`: 43 passed, exit 0.

No existing test was weakened.
