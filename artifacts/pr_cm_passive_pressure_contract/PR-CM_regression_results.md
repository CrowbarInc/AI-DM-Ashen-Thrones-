# PR-CM regression results

Live provider calls: 0. Interpreter: `.venv\Scripts\python.exe`. HTTP tests used FastAPI `TestClient` with stubbed `call_gpt`.

No timeouts. No interrupted runs. No skipped tests in these runs.

## 1. Revised passive-pressure tests

Both passed inside the shared-file run.

- `test_chat_single_wait_records_world_progress_and_keeps_hard_valid_narration`
- `test_chat_repeated_passive_waits_advance_world_and_ground_scene_stall`

## 2. Shared turn pipeline

`tests/test_turn_pipeline_shared.py`

41 passed, 24 failed, 0 skipped, 0 errors. About 11.2 seconds.

PR-CL baseline: 39 passed, 26 failed, 0 skipped, 0 errors.

The only failure-list change is the removal of the two obsolete tests:

- `test_chat_single_wait_in_tense_scene_forces_interaction_pressure`
- `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere`

No shared-pipeline failure is new relative to the PR-CL list. The file still has 65 tests. The two replacements occupy the same slots and pass.

## 3. PR-CM controls and diagnostic

`tests/test_pr_cm_passive_pressure_contract.py`: 5 passed, 0 failed.

## 4. PR-CK resolver selection

`tests/test_pr_ck_ordinary_resolver_selection.py`: 30 passed, 0 failed.

## 5. Grounded observation

`tests/test_grounded_observation_non_invention.py`: 11 passed, 2 failed.

Same two follow-up failures PR-CL recorded. Not introduced here.

## 6. Passive-pressure fallback

`tests/test_final_emission_passive_scene_pressure.py`: 4 passed, 0 failed.

`tests/test_bv4b_concrete_beat_upstream_satisfier.py`: 4 passed, 0 failed.

## 7. World tick and clocks

`tests/test_world_progression_tick_integration.py`: 6 passed, 0 failed.

`tests/test_world_state.py`: 11 passed, 0 failed.

`tests/test_clocks_projects_logging_lint.py`: 5 passed, 0 failed.

## 8. NPC agenda

`tests/test_agenda_simulation.py`: 9 passed, 0 failed.

## 9. Immutable response, C18, and authority

`tests/test_pr_br_continuation18_immutable_boundary.py`: 21 passed, 0 failed.

`tests/test_pr_br_gm_resolution_decision.py`: 9 passed, 0 failed.

`tests/test_pr_br_continuation19_hard_authority.py`: 10 passed, 1 failed.

The failure is `test_raw_chat_stub_authority_and_contracts` (`initial_generation` versus `regeneration`). PR-CL did not run this file. PR-CM did not edit it or any product file. It is not attributed to this cycle.

## 10. PR-CI authored-answer finalization

`tests/test_social_question_relevance_answer_selection.py`: 25 passed, 0 failed.

## 11. PR-CC and PR-CE

`tests/test_pr_cc_social_reply_reconciliation.py`: 11 passed, 0 failed.

`tests/test_pr_ce_subjective_preference_classification.py`: 13 passed, 0 failed.

## 12. PR-BY and PR-BW

`tests/test_pr_by_narration_only_retry_contract.py`: 22 passed, 0 failed.

`tests/test_pr_bw_narration_only_envelope.py`: 5 passed, 0 failed.

## Focused junit

`pytest_focused.xml`: 204 tests, 201 passed, 3 failed, 0 skipped, 0 errors.

The 3 failures are the two inherited grounded-observation follow-ups and the continuation19 case above.
