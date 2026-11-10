# Regression results

Isolated lifecycle, re-run this cycle:

`tests/test_pr_play_71_lifecycle.py`, `tests/test_pr_play_71_persistence_recovery.py`, `tests/test_pr_play_71v_verification.py`

39 passed, exit 0. Basetemp `development/tmp/pr78_lifecycle`.

Combined lanes, `artifacts/pr_play_78/run_regression.py`, output `artifacts/pr_play_78/regression_results.json` (copied from `development/tmp/pr78_regression/`):

| Lane | Passed | Failed | New versus PR-PLAY-77 | Cleared |
|---|---|---|---|---|
| Focused | 1065 | 20 | 0 | 0 |
| Boundary | 101 | 6 | 0 | 0 |
| Broader | 0 | 9 | 0 | 0 |

The 20, 6, and 9 failure identities match `artifacts/pr_play_77/regression_results.json`. They were not reclassified. The focused lane's lifecycle failures are the same names that pass when that lane is isolated (39/39). That split was already true in PR-PLAY-77.

PR-PLAY-77 multistep tests passed in the 259-test closure run. No new regression was identified.
