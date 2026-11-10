# Diagnostic assertion report

## Original failure

`artifacts/pr_play_33/readiness_output.txt` ends at `readiness.py` line 76:

`assert not (run/'data/session.json').exists()`

`reports/result.json` for run `20261102T004939Z-7d36523024d3` records a second, earlier failure: `AssertionError` at stage `application_startup_failure`. That stage is still set while the diagnostic's replacement for `wait_for_http_ready` is running. The wrapper's five asserts had no identifiers, and the process table was not saved. The HTTP poll had already recorded status 200, so the request guard had passed. `ready.json` shows three of the five asserts would have passed: pid 35756 matched, isolation and diagnostics were true, and both retry counts were 0. The two asserts that needed the process table were parent equality and zero children.

## Identified cause

The same wrapper conditions were measured again, separately, on control A before cleanup:

| Identifier | Result | Observed |
| --- | --- | --- |
| H1 ready pid equals Popen pid | PASS | 32792 = 32792 |
| H2 parent equals controller | PASS | 26144 = 26144 |
| H3 worker has no children | FAIL, not a harness gate | one child, `conhost.exe` pid 16612 |
| H4 isolation and diagnostics | PASS | both true |
| H5 retries | PASS | 0 and 0 |

H3 is the assert that raises. `conhost.exe` is a Windows console host, not a second interpreter. The base-interpreter launch from PR-PLAY-33 is intact. Treating every child as a startup failure was an incorrect diagnostic assumption. An interpreter descendant remains a gating failure.

The session assert failed because `load_session` creates `session.json` when `compose_state` serves `GET /api/state`. The saved PR-PLAY-33 session had `turn_counter` 0 and `campaign_started` false. That behavior was left unchanged.

## Correction

`artifacts/pr_play_34/evaluate.py` scores each condition by identifier and records expected value, observed value, evidence, and whether cleanup succeeded. The snapshot is written to `diagnostics/readiness_snapshot.json` before the controller's cleanup. A bootstrap file is allowed. A started campaign, nonzero turn, chat or log activity, gameplay trace, or provider dispatch fails.
