# Regression results

All commands used `.\.venv\Scripts\python.exe` with `PYTHONPATH=.`. Live provider calls: 0.

## Commands

| Command | Result |
|---|---|
| `pytest tests/test_at_opt_02_retreat_and_budget.py -q` | 20 passed, 0 failed, 0 skipped |
| `pytest tests/test_pr_play_79df3_classification.py tests/test_pr_play_79b_integration.py tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome -q` | 118 passed, 0 failed, 0 skipped |
| `python artifacts/at_opt_02/rerun_holdout.py` | 28 passed, 0 failed |
| `pytest tests/test_pr_play_79df3_holdout.py -q` | Stopped by the storage guard before its assertion |

The adjacent 118 are 27 classification, 81 publication-integration, 1 flag-off physical, and 9 physical-publication cases including the enabled step-back.

## Preexisting and new failures

No failure in the 20 new tests or the 118 adjacent tests. The frozen holdout’s 28 expected rows matched when the runner wrote `artifacts/at_opt_02/holdout_rerun.json`.

The direct pytest of that holdout raises `PermissionError` because it tries to write `artifacts/pr_play_79df3/holdout_results.jsonl`. That historical file was not modified. The case results are the redirected 28/28. No new holdout identity.

Protected files from `artifacts/pr_play_79df3/protected_exit.json`: 150 unchanged, 0 changed, 0 missing. Recorded in `artifacts/at_opt_02/protected_rehash.json`.

## Protected regression

The protected slice rehashed here is those 150 files. The broad historical focused suite was not run. The HTTP acceptance script was not run.

Machine-readable counts: `artifacts/at_opt_02/regression_results.json`.
