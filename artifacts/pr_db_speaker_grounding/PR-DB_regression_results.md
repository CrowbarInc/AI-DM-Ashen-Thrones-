# PR-DB Regression Results

No live provider calls.

Historical shared pipeline cited by the task: 45 passed / 24 failed.

## Focused suites

| Suite | Result |
|---|---|
| PR-DB `tests/test_pr_db_speaker_grounding.py` | 13 passed / 0 failed / 0 skipped |
| PR-CZ `tests/test_pr_cz_followup_reliability.py` | 10 passed / 0 failed / 0 skipped |
| PR-CX `tests/test_pr_cx_authority_assurance.py` | 9 passed / 0 failed / 0 skipped |
| PR-CW `tests/test_pr_cw_social_context_projection.py` | 39 passed / 0 failed / 0 skipped |
| PR-CT `tests/test_pr_ct_safe_prompt_deduplication.py` | 3 passed / 0 failed / 0 skipped |
| PR-CP `tests/test_pr_cp_authorized_finalization.py` | 9 passed / 0 failed / 0 skipped |
| PR-CE `tests/test_pr_ce_subjective_preference_classification.py` | 13 passed / 0 failed / 0 skipped |
| PR-CK `tests/test_pr_ck_ordinary_resolver_selection.py` | 30 passed / 0 failed / 0 skipped |
| PR-CN `tests/test_pr_cn_contextual_figure_integrity.py` | 13 passed / 0 failed / 0 skipped |
| PR-CV policy contract `tests/test_pr_bt_policy_instruction_deduplication.py` | 5 passed / 0 failed / 0 skipped |
| PR-CV policy contract `tests/test_pr_bt_selective_epistemic_guidance.py` | 3 passed / 0 failed / 0 skipped |
| PR-CR recovery `tests/test_pr_by_narration_only_retry_contract.py` | 22 passed / 0 failed / 0 skipped |
| Immutable `tests/test_pr_br_continuation18_immutable_boundary.py` | 21 passed / 0 failed / 0 skipped |
| C19 `tests/test_pr_br_continuation19_hard_authority.py` | 11 passed / 0 failed / 0 skipped |
| C19 free text `tests/test_pr_br_c19_free_text_authority.py` | 5 passed / 0 failed / 0 skipped |
| Consequential claims `tests/test_bounded_improvisation_authority.py` | 5 passed / 0 failed / 0 skipped |
| Authored knowledge `tests/test_authored_knowledge_realization.py` | 13 passed / 3 failed / 0 skipped |
| Watch-break regression `tests/test_world_action_social_continuity_break.py` | 8 passed / 0 failed / 0 skipped |

Combined focused run excluding the separate C19 file: 227 passed / 3 failed / 0 skipped.

The three failures are all in `tests/test_authored_knowledge_realization.py`:

- `test_retry_fallback_prefers_authored_topic_over_ignorance`
- `test_http_notice_question_communicates_patrol_fact`
- `test_http_read_notice_board_speaks_written_clue`

They expect authored patrol wording such as "northwest" and instead keep an ignorance or scene line. Those player lines are not the keep-watch follow-up. They were not repaired.

PR-CZ recorded this file as 14 passed / 2 failed. This worktree run is 13 passed / 3 failed. The extra failure is outside the speaker-grounding change.

## Shared turn pipeline

`tests/test_turn_pipeline_shared.py`: 41 passed / 24 failed / 0 skipped. 65 tests collected.

The cited historical result is 45 passed / 24 failed. Failure count is still 24. This worktree's copy of `tests/test_turn_pipeline_shared.py` was already modified before PR-DB, and the collected total is 65 rather than 69. The 24 failing names are the existing chat, retry, notice-board, and strict-social cases. They were not repaired.

JUnit: `artifacts/pr_db_speaker_grounding/focused_regression.xml` and `shared_regression.xml`.
