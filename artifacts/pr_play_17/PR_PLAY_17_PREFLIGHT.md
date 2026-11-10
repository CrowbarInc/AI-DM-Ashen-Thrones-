# PR-PLAY-17 Preflight

**PASS for execution qualification.** Current session: Workspace Write, network access enabled, auto_review approval policy; Windows PowerShell and Python 3.12.0 in the repository venv. Workspace writes empirically verified by these artifacts. No escalation required. These are effective session instructions, not an inference from a configuration file. See environment.json.

One IPv4 127.0.0.1 TCP test passed listener creation, bind/listen, client connect, bidirectional payload exchange, close and port rebind. Zero provider calls. See loopback.json. This verifies local TCP; outbound provider connectivity was established later by the one authorized live request, without probes.

One actual offline worker startup cycle passed: HTTP GET /api/state 200 in 1.875 seconds; http_ready.json generated; isolated worker PID 32340 terminated and port 52724 released. Journal contains initialization only, zero dispatches and zero player actions. The PR-PLAY-15 stop-at-readiness controlled KeyboardInterrupt intentionally produces a BLOCKED/incomplete scenario report; it is not a failed readiness check. See offline_readiness.json and offline_run/diagnostics/.

An earlier evidence-driver invocation was rejected before worker creation because I chose artifacts/pr_play_17 as the isolated store root. The harness correctly requires artifacts/atgb or development/tmp. This invocation mistake was corrected without changing safeguards; initial_invocation_readiness.json and initial_rejected_invocation/ preserve it. It was not a startup cycle or live attempt. No worker startup was retried after failure.

Provider configuration: credentials present (boolean only); default, high-precision and escalation routes all gpt-4.1-mini. Request ceiling 6; aggregate input/output/total ceilings 200000/20000/220000. Existing opening output allowance 3000. SDK retries 0, host retries 0; no fallback, judges or provider probes. No settings changed.

ASHEN_OPENING_RENDERER=1 was scoped to execution processes. Both offline and actual live workers attest enabled/selected in ready.json. Live capture enabled. Live worker HTTP readiness also passed in 1.938 seconds. No permanent configuration/environment changes. See safe_configuration.json and live_run/diagnostics/ready.json.
