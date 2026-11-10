# 12 — Development tests

The matrix is covered by the existing lifecycle and persistence modules plus `tests/test_pr_play_71v_verification.py`. No second test framework was added.

Isolated command:

`pytest tests/test_pr_play_71_lifecycle.py tests/test_pr_play_71_persistence_recovery.py tests/test_pr_play_71v_verification.py --basetemp development/tmp/pr71v_isolated`

Result: 39 passed, 0 failed, about 24 seconds. Provider calls were disabled. This run is the development-test result for items 01 through 60, including atomic retries, rollback, both branches, transcript isolation, projection, rejected narration, and permanent-failure publication.

The same modules also appear inside the combined focused process, where they failed with HTTP 503. That process result is recorded in the regression report and is not the isolated result.
