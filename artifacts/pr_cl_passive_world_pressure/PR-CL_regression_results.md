# PR-CL regression results

Live provider calls: 0. No product code changed, so these runs are the inherited worktree, not a repair delta. Broad repository regression was not run.

Interpreter: `.venv\Scripts\python.exe` (Python 3.12). HTTP tests used FastAPI `TestClient`.

## 1. Target passive-pressure tests

Both failed at `_assert_concrete_pressure`.

- `test_chat_single_wait_in_tense_scene_forces_interaction_pressure`
- `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere`

## 2. PR-CK resolver selection

`tests/test_pr_ck_ordinary_resolver_selection.py`

30 passed, 0 failed.

## 3. Passive-wait and pressure beat

`tests/test_final_emission_passive_scene_pressure.py`: 4 passed, 0 failed.

`tests/test_bv4b_concrete_beat_upstream_satisfier.py`: 4 passed, 0 failed.

Shared-file siblings that keep hard-valid atmosphere passed inside the shared run:

- `test_chat_passive_scene_prefers_already_introduced_suspicious_figure`
- `test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere`

## 4. World clock

`tests/test_clocks_projects_logging_lint.py`: 5 passed, 0 failed.

`tests/test_world_state.py`: 11 passed, 0 failed.

## 5. Scheduled events

`tests/test_world_progression_tick_integration.py`: 6 passed, 0 failed.

## 6. NPC activity

`tests/test_agenda_simulation.py`: 9 passed, 0 failed. Includes the mobile `npc_moved` lock.

## 7. Scene-stall retry

`test_chat_targeted_retry_scene_stall_only` passed inside the shared file.

## 8. Immutable response and C18

`tests/test_pr_br_continuation18_immutable_boundary.py`: 21 passed, 0 failed.

## 9. Authority

`tests/test_pr_br_gm_resolution_decision.py`: 9 passed, 0 failed.

`tests/test_grounded_observation_non_invention.py`: 11 passed, 2 failed. The two failures are the follow-up sentences after the anti-invention check (`test_frontier_gate_post_return_observe_does_not_invent_confrontation`, `test_milestone_examine_does_not_keep_invented_inscription`). They fail on clue wording in a later turn. PR-CL did not touch that path and does not claim them.

## 10. Entire shared turn pipeline

`tests/test_turn_pipeline_shared.py`

39 passed, 26 failed, 0 skipped, 0 errors. About 12.9 seconds.

PR-CK recorded 38 passed / 27 failed. The inventory delta is one test: `test_chat_targeted_retry_validator_voice_only` is in the PR-CK failure list and passes in this run (reconfirmed alone: 1 passed). PR-CL did not edit that test or its code. It is not claimed as a passive-pressure repair. The other 26 PR-CK failures are still failing, including both target tests. No shared-pipeline failure is new relative to that list.

## 11. PR-CI authored-answer finalization

`tests/test_social_question_relevance_answer_selection.py`, which holds `test_immutable_preseal_preserves_selected_authored_answer_over_ignorance`: 25 passed, 0 failed.

## 12. PR-CC and PR-CE

`tests/test_pr_cc_social_reply_reconciliation.py`: 11 passed, 0 failed.

`tests/test_pr_ce_subjective_preference_classification.py`: 13 passed, 0 failed.

## 13. PR-BY and PR-BW

`tests/test_pr_by_narration_only_retry_contract.py`: 22 passed, 0 failed.

`tests/test_pr_bw_narration_only_envelope.py`: 5 passed, 0 failed.

## Extra file included with the focused run

`tests/test_authored_knowledge_realization.py`: 14 passed, 2 failed (`test_http_notice_question_communicates_patrol_fact`, `test_http_read_notice_board_speaks_written_clue`). Pre-existing on this worktree. Not a PR-CL change. Not claimed as resolved or introduced.

Focused junit (`pytest_focused.xml`): 204 tests, 200 passed, 4 failed. All 4 are the grounded-observation follow-ups and the authored-knowledge HTTP tests above.
