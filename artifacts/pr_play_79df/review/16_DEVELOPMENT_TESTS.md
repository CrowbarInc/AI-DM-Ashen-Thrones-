# Development tests

Command result recorded in `artifacts/pr_play_79df/development.xml`.

187 passed, 0 failed, 0 skipped, 5.877 seconds, timestamp `2026-11-08T08:16:30-05:00`.

| Module | Tests |
| --- | --- |
| `tests.test_pr_play_79df_verification` | 14 |
| `tests.test_pr_play_79df_holdout` | 32 |
| `tests.test_pr_play_79d_closeout` | 59 |
| `tests.test_pr_play_79c_publication` | 82 |

The 14 verification tests cover accepted settlement, three rejection reasons, the closed narration gate, dialogue speech that stays speech, renderer nonmutation, cross-campaign isolation, snapshot recall, a stale dialogue owner that is not applied, completed-attempt accounting, the request ceiling, a blocked protected write, and position matching the publication.

An earlier run in this cycle failed 18 tests because the harness still hit the live-model guard, started dialogue with no interlocutor, and pointed admission at an existing ledger. The harness was corrected. Application source and the frozen holdout expectations were not changed. The 187-pass run is the run after that harness correction.

These tests do not replace the live browser sequence.
