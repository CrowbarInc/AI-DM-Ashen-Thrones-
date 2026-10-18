# PR-DE Regression Results

No live calls. Pre-change and post-change commands used the same file list. The post command also ran the new PR-DE tests, `test_manual_play_latency.py`, and `test_build_messages_projection.py`.

## Required suite

Pre-change: 353 tests, 326 passed, 27 failed, 0 skipped.

Post-change, same 353 tests: 326 passed, 27 failed, 0 skipped.

The failure set is identical. No required test started failing, and none of the inherited failures started passing.

| Suite | Passed | Failed | Skipped |
|---|---:|---:|---:|
| PR-DE focused | 6 | 0 | 0 |
| PR-DC subjective follow-ups | 52 | 0 | 0 |
| PR-DB speaker grounding | 13 | 0 | 0 |
| PR-CZ follow-up reliability | 10 | 0 | 0 |
| PR-CX authority | 9 | 0 | 0 |
| PR-CW context projection | 39 | 0 | 0 |
| PR-CV policy (`test_pr_bt_policy_instruction_deduplication`, `test_pr_bt_selective_epistemic_guidance`, `test_response_policy_contracts`) | 22 | 0 | 0 |
| PR-CT instruction dedupe | 3 | 0 | 0 |
| PR-CP finalization | 9 | 0 | 0 |
| PR-CR retry (`test_pr_by_narration_only_retry_contract`) | 22 | 0 | 0 |
| PR-CE subjective classification | 13 | 0 | 0 |
| PR-CK resolver | 30 | 0 | 0 |
| PR-CN contextual extraction | 13 | 0 | 0 |
| Immutable response (`test_pr_br_continuation18_immutable_boundary`) | 21 | 0 | 0 |
| Consequential claims are inside PR-CP, PR-DC, and PR-CE | included above | 0 | 0 |
| C18 / C19 (`continuation19_hard_authority`, `c19_free_text_authority`) | 16 | 0 | 0 |
| Authored knowledge | 13 | 3 | 0 |
| Shared turn pipeline | 41 | 24 | 0 |

Shared pipeline baseline: 41 passed, 24 failed, 0 skipped.

Shared pipeline after: 41 passed, 24 failed, 0 skipped.

Inherited authored-knowledge failures, not repaired:

- `test_retry_fallback_prefers_authored_topic_over_ignorance`
- `test_http_notice_question_communicates_patrol_fact`
- `test_http_read_notice_board_speaks_written_clue`

The 24 shared-pipeline failures match the pre-change names, including the dialogue-lock, retry, notice-board mixed-turn, and strict-social cases. They were already failing on this dirty worktree before the omission.

## Extra check

`test_build_messages_projection.py`: 2 passed.

`test_manual_play_latency.py`: 5 passed, 1 failed. `test_chat_begin_nonretryable_quota_repairs_malformed_opening_fast_fallback` also fails when `omit_exact_duplicate_provider_contracts` is replaced with the identity function. It is outside the required list and is not caused by the omission. It was not repaired.
