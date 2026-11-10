# Regression results

Command: `python artifacts/pr_play_54/run_regression.py`.

Provider calls were disabled. The live narration flag was unset. Pytest exit code was 1 because three known tests failed. The runner treated that as the prior baseline, not as a new failure.

| | Collected | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| PR-PLAY-53 historical | 426 | 423 | 3 | 0 | 0 |
| This cycle | 523 | 520 | 3 | 0 | 0 |

New tests: 97, all in `tests/test_pr_play_54_consequential_validation.py`. All 97 passed. The PR-PLAY-53 file still contributes 21 tests.

Previously known failures, seen again:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

New failures: none.

Skipped tests: none.

Unexecuted tests: the suites not in the command were not run. The command is the PR-PLAY-53 focused list plus the new file. It includes narration validation, the adversarial corpus, paraphrase and positive controls, quarantine, provider-accounting, and narration-state tests.

No test was weakened into a skip. The PR-PLAY-53 fabrication test still asserts the old pass/fail labels against `validate_generated_response`, and now also asserts that consequential lines fail closed in the prelude.
