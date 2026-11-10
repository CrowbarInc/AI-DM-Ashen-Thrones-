# PR-PLAY-34 inspection — readiness procedure

The PR-PLAY-33 diagnostic is preserved at `artifacts/pr_play_33/readiness.py`. It was not edited. One isolated run remains at `artifacts/atgb/pr_play_33/readiness/20261102T004939Z-7d36523024d3`.

## What failed

Two separate assertions failed. They are not the same check.

1. **Controller assertion (unlabeled).** `reports/result.json` records `failure.type = AssertionError` and `failure.stage = application_startup_failure`. That stage is set in `tools/playtest/runner.py` immediately before `wait_for_http_ready` and is cleared only after that call returns. The diagnostic replaces `wait_for_http_ready`. Any exception it raises is therefore classified as an application startup failure even after HTTP 200.

   The replacement (`readiness.py` lines 39–50) performs five bare asserts after `original_wait` returns, then raises `KeyboardInterrupt` so the controller stops before scenario actions. `diagnostics/readiness_poll.jsonl` already contains `http_response` status 200, so the request guard (`GET` and `/api/state`) had passed. `diagnostics/ready.json` shows the three value checks would have passed as well:

   - `ready.pid` 35756 equals the cleaned-up Popen pid 35756
   - `isolation_verified` true and `diagnostics_enabled` true
   - `sdk_retries` 0 and `host_retries` 0

   The snapshot of the process table was never written. The two asserts that needed it cannot be recovered from the saved run:

   - worker parent pid equals the controller pid
   - the worker has no child processes

   `KeyboardInterrupt` was never reached. No scenario action ran (`steps` is empty).

2. **Outer assertion (identified).** `artifacts/pr_play_33/readiness_output.txt` raises at line 76:

   `assert not (run/'data/session.json').exists()`

   That check runs only after `run_playtest` returns. It is an incorrect expectation. `game/storage.py` `load_session` creates `session.json` when it is missing. `GET /api/state` calls `compose_state`, which calls `load_session`. The saved session has `turn_counter` 0, `campaign_started` false, an empty chat history, and an empty session log. `provider_usage.jsonl` contains only `initialized`. Provider dispatches are 0.

## Conditions evaluated before the controller assertion

In order: worker spawn, isolation attestation (`pid`, data directory, `isolation_verified`), `GET /api/state` returning 200, then the five unlabeled asserts above. Process cleanup ran in the controller `finally` block and stopped pid 35756. The port was released. The diagnostic uses `output_root` under `artifacts/atgb/pr_play_33/readiness`, which `prepare_isolated_store` treats as an isolated store. `stop_owned` terminates only the Popen handle for that worker. It does not scan the machine or close an unrelated listener. The occupied-port and observer controls never started.

## Diagnostic assumption to correct

Creating `session.json` on `GET /api/state` is established application behavior. The readiness check must reject a started campaign, a nonzero turn, gameplay actions, and provider dispatches. It must not treat the bootstrap file itself as failure. The process-launch repair in `runner.start_worker` stays as PR-PLAY-33 left it.
