# Harness Architecture

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

`scripts/run_live_playtest.ps1` resolves repository/interpreter and forwards flags.
`tools/playtest/runner.py` validates scenario/configuration, prepares a fresh store,
starts an owned server process, drives HTTP, collects snapshots, classifies and
exports. `worker.py` binds its socket, attests DATA_DIR/PID, configures transport,
and serves the existing ASGI application. `analysis.py` compares observations and
classifies stages. `browser.py` defines a future rendered-UI adapter. JSON scenario
definitions follow existing repository JSON conventions.

Scenario contracts contain ID/version/description/fixture/modes/actions/invariants,
action and request ceilings, input/output/total budgets, six stage timeouts,
evidence requirements and stop conditions. Unknown actions, unpinned fixtures,
repeated New/Start, expanded established limits and unbounded timeouts are refused.
Bundled scenarios are selected by name; arbitrary external code is not loaded.

Deterministic is default: synthetic SDK Responses transport, external socket
connect/connect_ex denied, real production admission and validation. Live is
explicitly flagged, opening-only, single-admission, no retries. ScriptedGameplay
is deterministic only. A failed step stops further player actions; final evidence
capture is permitted and never invokes another opening/provider request.

Ownership justification: the existing ATGB driver owns benchmark conversations,
partitions, score worksheets and chat turns. It does not expose a bounded owned
Uvicorn lifecycle or one-opening HTTP diagnostic transaction. Extending it with
these unrelated semantics would change its frozen benchmark contract. This small
controller composes its existing fixture/isolation/accounting/revision helpers
and leaves benchmark authority unchanged. Production API and provider owners are
unchanged. No new persistent gameplay structure is introduced.

Isolation root is `artifacts/atgb/automated_playtests/`, fitting the existing ATGB
safe-path guard. Unique UTC+UUID directories never reuse prior stores. Environment
changes stay in the worker; PowerShell restores PYTHONPATH. A Windows venv redirector
is avoided when launching the worker so the attested PID is the owned server PID.
Readiness uses safe GET state polling only after socket binding and isolation
attestation. No connection to an unrelated running server is accepted.
