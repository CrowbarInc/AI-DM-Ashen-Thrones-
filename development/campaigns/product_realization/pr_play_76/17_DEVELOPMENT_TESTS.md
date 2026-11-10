# Development Tests

`tests/test_pr_play_76_physical.py` and `tests/test_pr_play_76_matrix.py` were run together after the last expectation correction.

- Result: 121 passed, 0 failed.
- Physical file: 55 cases, including both HTTP campaign branches and the failed-write rollback.
- Matrix file: 66 parametrized cases, M00 through M65.

Deferred take, drop, and unheld place are asserted as refusals. They are not counted as working inventory operations. The matrix case "I place the cup down." expects the carrying refusal. The matrix case "Can I unlatch the door?" on a locked door expects a locked refusal and no open state change.
