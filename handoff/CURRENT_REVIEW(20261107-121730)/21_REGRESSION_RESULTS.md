# Regression Results

PR-PLAY-75 focused baseline: 1,065 passed, 20 failed. This cycle's focused run failed the same 20 test identities and no others. New focused failures: 0.

Isolated lifecycle (`test_pr_play_71_lifecycle.py`, `test_pr_play_71_persistence_recovery.py`, `test_pr_play_71v_verification.py`): 39 passed, 0 failed. The same files fail inside the combined focused run, which matches the historical combined-versus-isolated split.

Boundary plus broader, run together: the 6 historical opening failures and the 9 historical authority-assurance failures. No additional failure identity appeared. Those 15 tests are the previous boundary and broader failure lists.

This cycle's physical and matrix suites: 121 passed. They are new tests, not a regression of an older passing set.
