# 04 — Windows atomic-write recovery

The implementation matches the reported repair. Four `os.replace` attempts. Sleeps of 10, 30, and 90 milliseconds occur only between WinError 5 failures. There is no loop past the fourth attempt.

Fault injection in `tests/test_pr_play_71v_verification.py` and the frozen holdout covered:

- Immediate success.
- Success after one, two, and three transient WinError 5 failures.
- Exhaustion when all four attempts fail: `PermissionError` propagates, elapsed time stays between 0.12 and 1.0 seconds, and the prior target bytes remain.
- An unrelated `PermissionError` and a non-permission `OSError` are not retried.
- A missing source and an unavailable destination do not leave a partial target.
- Temporary files are removed.
- The enclosing operation runs once. Provider and resolver calls are not repeated.

Holdout W13 locked the destination on the real Windows filesystem, observed WinError 5, and recovered. Elapsed time was 137.7 milliseconds. That is the real lock test. The other atomic cases used a deterministic replace interceptor.

Holdout W12 is not a product failure. After the target contents and the call count were asserted, the runner read a missing `expect_delays` key and raised `KeyError`. Elapsed time was 135.5 milliseconds, consistent with the three sleeps. The case was left frozen and was not rerun. The delay list is asserted by the development tests.
