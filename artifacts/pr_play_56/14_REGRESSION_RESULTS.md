# Regression results

Command: `python artifacts/pr_play_56/run_regression.py`.

Provider calls were disabled. Live narration flags were unset. Protected trees under `artifacts/pr_play_49`, `pr_play_47`, `pr_play_52`, and `pr_play_50` were restored if a test rewrote them. The holdout test writes `artifacts/pr_play_55/evaluation.json`; that file was restored after a passing run.

| Suite | Collected | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| Focused narration and quarantine command | 532 | 529 | 3 | 0 | 0 |
| Frozen holdout, separate | 1 | 1 | 0 | 0 | 0 |
| `tests/test_pr_cx_authority_assurance.py` | 9 | 0 | 9 | 0 | 0 |

The focused result matches the PR-PLAY-55 focused baseline: 529 passed, 3 failed, 0 new failures.

Previously known focused failures, seen again and not modified:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

## Broader `hard_validation_attempt_1` failure

All 9 tests in `tests/test_pr_cx_authority_assurance.py` fail with `KeyError: 'hard_validation_attempt_1'`. The failures include biography, geography, hidden information, an NPC action, a discovery, and the harmless controls. The missing key is on the sealed metadata after `run_preserve_if_valid`. This is the failure PR-PLAY-55 already reported. This cycle did not edit `game/immutable_valid_response.py`. The failure is recorded, not repaired.

The individual PR-BR continuation files were not re-executed. PR-PLAY-55 did not name which three of them failed. They remain unidentified beyond that earlier note.

No test was edited to obtain this result.
