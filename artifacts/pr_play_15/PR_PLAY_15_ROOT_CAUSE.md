# Root cause and architecture

## Finding

Confirmed in this execution environment, high confidence: the restricted Windows sandbox denies local TCP connections (WinError 10013). Python 3.12 asyncio's ProactorEventLoop stalls in socket.socketpair -> accept while constructing its internal loopback self-pipe, before uvicorn can log server startup or execute the ASGI lifespan. The controller independently receives local connection access denial. Increasing the readiness timeout cannot repair this boundary.

The same provider-stubbed diagnostic reaches /api/state HTTP 200 outside that sandbox. Five independent startup/shutdown cycles then pass outside it. Historical PR-PLAY-14 attribution is strongly supported but not proven: its logs discarded exactly the needed transport detail and contain no stack. No application startup-order defect is established.

## Evidence and investigation

1. Read PR-PLAY-14 preflight, execution/final reports, invocation, configuration, original result, ready file, empty application log, initialized-only provider journal and cleanup record before edits.
2. An initial diagnostic output location was refused by the existing isolation guard before worker creation; corrected it to artifacts/atgb without weakening the guard.
3. Initial actual startup reproduction (initial_timeout.json) ran the existing deterministic worker and stopped before any scenario action. Every captured readiness request failed with URLError/WinError 10013; worker timed out after configuration attestation.
4. Added phase events and one bounded eight-second stack capture. stack_reproduction.json references the run containing startup_stack.log: the worker is blocked inside socketpair accept, called from asyncio Proactor loop construction. Events end at server_run_entered. No ASGI initialization event or uvicorn log occurs.
5. Repeated the same startup-only question with sandbox restrictions lifted (unrestricted_comparison.json): HTTP 200, no scenario actions or provider dispatch. This changes the execution context, not the application architecture.
6. Final sandbox check (repaired_sandbox_failure.json) now terminates promptly with PermissionError; readiness_poll.jsonl records access_denied/os_error 10013 and cleanup succeeds.

## Startup path and lifecycle

scripts/run_live_playtest.ps1 selects the venv Python (bundled fallback), sets repository PYTHONPATH and invokes tools.playtest.runner. runner.run_playtest validates authorization/scenario, dependencies and pinned fixture, prepares a fresh isolated store, then launches the base interpreter directly to avoid a Windows venv redirector PID. Popen owns that single worker, disables a visible console, and captures stdout plus stderr into a capped, redacted application.log through a drain thread. process.poll detects early exits each polling iteration; stop_owned terminates, waits, then kills on bounded timeout. No server subprocess or reload process is spawned. This is ownership-specific cleanup, not a general descendant-tree terminator.

worker.main binds AF_INET 127.0.0.1 to the requested port (0 selects an OS-assigned free port) and calls listen before game imports. A conflict fails at bind; an existing listener is neither reused nor killed. Configuration, isolation, accounting and retry controls initialize; ready.json is written before uvicorn.Server.run. Uvicorn must then construct its event loop, initialize FastAPI's lifespan (ensure_data_files_exist and skipped upstream preflight logging), and begin servicing /api/state. The GET does not require new_campaign or start_campaign. All successful cycles exercised that real production endpoint on the isolated bootstrap store.

ready.json means configuration/isolation initialized, plus a prebound listening socket. It does not mean ASGI or HTTP ready. Old and new controllers require /api/state HTTP 200; no premature-ready acceptance defect was found. Added phase/time fields retain all original keys, and http_ready.json independently records endpoint success. Existing ready.json consumers (runner and tests) retain their contract.

The startup timer starts after Popen and log-thread creation. It covers worker imports/configuration, uvicorn/event-loop/lifespan initialization and HTTP polling. It excludes earlier preflight and fixture copying, which have their own cap. Requests ignore machine proxies; controller and worker both use IPv4 loopback. Poll requests are capped at one second and remaining deadline. A monotonic deadline remains 30 seconds; late HTTP success is not accepted. Failed HTTP JSON responses retain status in polling evidence; non-JSON payloads are recorded as invalid_response because the shared request parser rejects them. Bodies and arbitrary exception strings are excluded.

## Alternatives

| Hypothesis | Evidence / conclusion |
|---|---|
| Premature ready file incorrectly accepted | Rejected: controller always performs HTTP polling; file semantics needed clarification only |
| Historical port conflict | Strongly disfavored: bind precedes historical ready file; controlled occupied-port test produces OSError 10048 and no ready file |
| IPv4/IPv6/proxy mismatch | Rejected in reproduction: both sides use 127.0.0.1; proxy handling explicitly bypassed |
| Slow game initialization or application deadlock | Not supported: stack is before ASGI lifespan, and unrestricted startup is under two seconds in five cycles |
| Worker exited unnoticed | Not observed historically; original controller polls process state; new regression verifies early exit detection |
| Polling discarded evidence | Confirmed: old loop caught connection/parse exceptions and discarded them; fixed with safe structured metadata and fail-fast access denial |
| Provider issue | Rejected for startup reproduction: provider transport stubbed, probes forbidden; five cycles additionally disable provider admission and record zero dispatches |
| Sandbox/network restriction | Confirmed now by WinError 10013, socketpair stack and successful unrestricted comparison; probable historical cause, not directly provable |

Relevant source locations: runner.py stop_owned (~154), wait_for_http_ready (~169), Popen/readiness invocation (~378); worker.py main (~121), ready.json (~164), ASGI wrapper (~173), server run (~196), exception diagnostic (~205); game/api.py lifespan (~297). Review source_snapshots and the task-specific diffs for exact packaged lines.
