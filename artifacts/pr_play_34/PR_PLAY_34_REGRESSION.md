# Regression results

Dedicated assertion run, before the readiness controls:

` .venv/Scripts/python.exe -m pytest tests/test_pr_play_34_readiness_diagnostics.py --basetemp=development/tmp/pr_play_34_assert -q --tb=short `

Result: **6 passed**, 0 failed, 0 skipped. No retries.

Focused suite, after the readiness controls:

`.venv/Scripts/python.exe -m pytest tests/test_pr_play_33_process_ownership.py tests/test_playtest_startup_readiness.py tests/test_pr_play_34_readiness_diagnostics.py --basetemp=development/tmp/pr_play_34_process --junitxml=artifacts/pr_play_34/regression.xml -ra`

Result: **30 passed**, 0 failed, 0 errors, 0 skipped, time 1.740 seconds. No retries. No environment-specific failures. No test was converted to a skip. JUnit: `regression.xml`.

The 30 tests are the 24 PR-PLAY-33 ownership and startup tests plus 6 diagnostics tests for the corrected bootstrap and assertion rules. Gameplay suites were not added.
