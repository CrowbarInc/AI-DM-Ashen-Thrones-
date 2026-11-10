# Test results

Command and machine-readable counts: `regression_summary.json`. Raw log: `focused.txt`. JUnit: `focused.xml`.

Collected: 426. Passed: 423. Failed: 3. Errors: 0. Skipped: 0.

PR-PLAY-52 baseline on the same suite without the new file: 405 collected, 402 passed, 3 failed.

The new file is `tests/test_pr_play_53_quarantined_live.py`. It accounts for the 21 additional tests. Those 21 passed. They cover:

- Live flag defaulting off, with no provider client.
- A fake successful prelude staying out of the player response and out of campaign state.
- The known false-accept key sentence staying quarantined.
- The rain-barrel context excluding the patrol route.
- Timeout fault suppressing the live call.
- A provider timeout and a provider exception leaving the deterministic turn in place, with one create and no retry.
- Request-ceiling refusal before a client is constructed, with the refusal written to the accounting ledger.
- The six-request cap, the 10,000-token cap, and an output cap above 1,000.
- The fabrication corpus, including the misses that remain manual review.

Previously known failures, seen again:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

New failures: none.

The regression process set `ASHEN_DISABLE_PROVIDER_CALLS=1` and did not set the live flag. It did not make a narration request. Predecessor evidence files that the suite rewrote were restored: `artifacts/pr_play_49/evidence_performance.json`, `artifacts/pr_play_47/evidence_performance.json`, and `artifacts/pr_play_52/integration_results.json`.

No test was skipped. No test failed to execute.
