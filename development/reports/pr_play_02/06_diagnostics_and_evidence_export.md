# 06 — Diagnostics and Evidence Export

Reused provider_budget durable ledger. Playtest-only additions: admission sequence,
admission decision, remaining request allowance, SDK retry classification zero,
host retry policy disabled/unavailable and distinct rejected events. Existing
attempt_id/run_id join admission, dispatch and completion. Admission and dispatch
event time provide start markers; completed.time and latency_ms provide completion
and elapsed time. Existing completion_status distinguishes success, failure and
interruption. Reported input/output/total usage are integers only when complete and
consistent; otherwise null/unavailable. Exception messages/payloads/keys are not
logged; provider errors are stored as a fixed classification.

Admission reservations, dispatched_requests, completions and rejections are distinct.
Rejected operations have no admitted sequence (null) but unique attempt_id; they do
not increment request or dispatch counters. Constructor failure can reserve an
allowance without dispatch. No SDK transport retries occur with reviewed zero-retry
constructors; normal SDK retries are not independently counted by this ledger.
Host retry wrapper attempts may run locally but cannot dispatch under the host flag;
the ledger records admitted operations, not those local wrapper invocations.

Gameplay submissions are the chronological session_log request/player_input entries
(including blocked chat submissions); opening has start_campaign request identity.
They are not the same as provider operations. A pre-gated submission can require zero
provider operations and does not fabricate a rejected outbound attempt. Blocked Start
errors need operator notes/screenshots. This avoids inventing a turn from a retry.

tools/atgb/accounting.inspect_ledger received a small compatibility adjustment to
recognize rejection evidence separately from admitted lifecycles. Its counters and
usage reconciliation remain authoritative at their existing scope. No new logging
or export framework. The old ATGB source fingerprint manifest was not regenerated.

Existing persisted diagnostic method: data/session_log.jsonl, data/session.json
debug traces, state/content JSON, API timing fields; provider_usage.jsonl enabled
by ASHEN_PROVIDER_USAGE_PATH. No gameplay diagnostic-export button was found.
The manual artifact gives exact Copy-Item and Compress-Archive commands for one
folder and prints its result. Expected output:
artifacts/pr_play_02/manual-YYYYMMDD-HHMMSS-EVIDENCE.zip.

Includes full disposable state/content, transcript/resolver diagnostics, before/
after copies, provider accounting/timing/usage, notes and screenshots saved by the
operator. Screenshots, stopwatch/UI latency, exact terminal errors and operator
evaluation require separate capture into that same folder. Provider price/cost,
unreported usage, browser responsiveness and external provider traces are absent.
State can reveal campaign secrets and should go only to the intended reviewer.
Never package .env, credentials, cookies, auth headers or unrelated normal saves.

Developer review packaging uses existing tools/build_review_handoff.py and an
explicit allowlist; it is distinct from the later operator evidence ZIP. This pass's
ledger contains labeled mocked requests only, not live gameplay evidence.
