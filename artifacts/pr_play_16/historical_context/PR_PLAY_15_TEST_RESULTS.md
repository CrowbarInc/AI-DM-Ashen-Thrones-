# Test results

Focused: **10 passed, 0 failed, 0 skipped, 0 errors** (focused_tests.txt/.xml).
Existing relevant suite: **26 passed, 0 failed, 0 skipped, 0 errors** (existing_tests.txt/.xml). Includes success, deadline cleanup, interruption, occupied port, unauthorized Live refusal, external socket denial, redaction, evidence integrity and ScriptedObservation offline execution. Its provider dispatch counters represent synthetic SDK calls; no real provider requests or tokens were consumed. This suite intentionally exercises synthetic campaign actions; startup-cycle validation does not.

Commands (PowerShell, repository root):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_playtest_startup_readiness.py -q -o addopts= --junitxml=artifacts/pr_play_15/focused_tests.xml
.venv/Scripts/python.exe -m pytest tests/test_automated_playtest.py -q -o addopts= --junitxml=artifacts/pr_play_15/existing_tests.xml
$env:ASHEN_OPENING_RENDERER='1'
.venv/Scripts/python.exe -m tools.playtest.validate_startup
```

The integration commands ran with authorized local loopback access outside the sandbox. The focused tests use deterministic mocked transport/clock and require no network.

## Five consecutive final offline cycles

| Cycle | PID | IPv4 port | Startup seconds | Shutdown seconds | HTTP | Cleanup | Dispatches |
|---|---|---|---|---|---|---|---|
| 1 | 31892 | 52328 | 1.641 | 0.016 | 200 | stopped / released | 0 |
| 2 | 13036 | 52335 | 1.812 | 0.016 | 200 | stopped / released | 0 |
| 3 | 2996 | 52341 | 1.718 | 0.000 | 200 | stopped / released | 0 |
| 4 | 24220 | 52347 | 1.750 | 0.000 | 200 | stopped / released | 0 |
| 5 | 6744 | 52352 | 1.781 | 0.016 | 200 | stopped / released | 0 |

startup_cycles.json records OS process creation UTC, HTTP response UTC, PID/port, durations, renderer attestation and limits. Each cycle uses a fresh pinned isolated store and OS-assigned port. Readiness deadline is unchanged at 30s. Every cycle returns HTTP 200 from the real /api/state endpoint, stops its worker, confirms no remaining connection, and successfully binds the released port. All five completed. Native scenario reports say INCONCLUSIVE/interrupted_execution because the validator intentionally unwinds before gameplay; they are not relabeled gameplay passes. The validator's independent lifecycle assertions establish startup success.

## Failure controls

Occupied port: worker fails at socket_binding with OSError 10048; controller records worker_exited, exits in 0.234s, reaps worker (exit 2), and leaves original listener intact. No ready file is emitted, no campaign requests occur, no provider dispatch occurs.

Restricted sandbox: final check reports PermissionError; readiness_poll.jsonl preserves access_denied/10013, cleanup stopped PID 4460 in 0.031s; controller elapsed 3.610s including preflight. It no longer waits the full deadline. Initial unrepaired sandbox attempts remain preserved (initial_timeout.json and stack_reproduction.json), along with the successful unrestricted comparison.

Focused regressions cover HTTP 503 followed by 200, worker exit, stale PID attestation, connection refusal, request timeout, access denial, invalid response, absent attestation/deadline, late success rejection and transient attestation parse retry. Real success/cleanup/bind failure are covered by the lifecycle validator and existing suite.

An initial validation-driver monkeypatch of subprocess.Popen caused an import TypeError before worker creation; corrected the driver to inspect the actual process at the readiness hook. validation_driver_preflight_error.txt and its failed run are retained. This diagnostic-driver failure is not counted among the five final cycles. The first diagnostic output-root rejection similarly occurred before worker launch and did not weaken isolation.

Provider verification: five cycles = **0 admissions/dispatches**, initialized-only durable journals and budget snapshots show dispatched_requests=0; bind control exits before accounting and dispatch code; initial comparisons performed GET only using synthetic transport. No probes, live gameplay, live requests or provider tokens. final_process_check.json verifies all nine attested investigation worker PIDs are absent. Bind-failure PID 23364 is separately reaped in its result. No unresolved test failures. git diff --check passed for scoped files.
