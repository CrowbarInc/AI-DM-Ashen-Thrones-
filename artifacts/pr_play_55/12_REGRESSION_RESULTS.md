# Regression results

Command: `python artifacts/pr_play_55/run_regression.py`.

Provider calls disabled. Live narration flags unset. Protected artifact trees under `artifacts/pr_play_49`, `pr_play_47`, `pr_play_52`, and `pr_play_50` were snapshotted and restored if a test rewrote them.

The frozen holdout test is not in this command. It ran once earlier: `tests/test_pr_play_55_holdout.py`, 1 passed. That run wrote `evaluation.json`.

| | Collected | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| PR-PLAY-54 focused reference | 523 | 520 | 3 | 0 | 0 |
| This command | 532 | 529 | 3 | 0 | 0 |
| Holdout test, separate one-shot | 1 | 1 | 0 | 0 | 0 |

New tests inside the command: 9, all in `tests/test_pr_play_55_discovery_claims.py`. All 9 passed. The holdout file adds 1 passed test outside the command.

Previously known failures, seen again:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

New failures in this command: none.

Skipped: none.

Pytest exit code: 0 from the runner, because the three failures are the prior set. The raw pytest process exits 1, as it did in PR-PLAY-54. The runner records that and does not treat it as a new regression.

## Outside the focused command

A separate run of `test_pr_cx_authority_assurance.py` and three PR-BR continuation files showed failures. The shared symptom on the assurance file is `KeyError: 'hard_validation_attempt_1'` after `classify_propositions` had already accepted the family. Biography fails the same way as geography. This cycle did not change biography grounding. The working tree already contained unrelated edits to gameplay modules. Those failures are not counted as new focused-suite regressions, and they were not bisected on a clean tree.

Suites not named in the command were not run.
