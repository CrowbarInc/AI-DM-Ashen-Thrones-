# 19 Regression results

Focused suite, including the new publication tests: 744 collected, 741 passed, 3 failed, 0 errors, 0 skipped. The three failures are the previously known ones:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

No new focused failure. The historical focused count was 732 passed and 3 failed out of 735. The increase is the PR-PLAY-61 tests.

PR-PLAY-55 holdout wrapper: 1 passed.

Broader authority-assurance file: 9 failed, 0 passed. Every failure is `KeyError: 'hard_validation_attempt_1'`. That is the known broader set. It was not repaired.

Provider calls were disabled for this regression. Protected artifact trees that a test rewrote were restored. H41 and the inventory/persistent-consequence tests are inside the focused suite and did not add a failure.
