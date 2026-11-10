# PR-PLAY-14 Live execution

One authorized harness invocation occurred. No rerun, synthetic scenario, probe, judge, or repair was executed during this pass.

Exact command (in a dedicated tool PowerShell process; process-local environment discarded at exit):
```powershell
$env:ASHEN_OPENING_RENDERER = '1'
& .\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse *> artifacts/pr_play_14/launcher_output.txt
```
Invocation metadata: invocation.json. Runner timestamp: 2026-11-01T15:04:18.754898+00:00 (November 1, 2026, 10:04:18.754898 AM EST). Configured and actual execution mode: Live, production transport selected. No synthetic SDK replacement was installed. Production transport selection does not imply a provider request occurred.

Runtime worker ready.json independently confirms renderer enabled/selected, model gpt-4.1-mini, isolated data path, six requests, token ceilings 200000/20000/220000, SDK/host retries zero, diagnostics enabled, probes disabled. PID 2368 bound port 50501. The readiness file precedes uvicorn startup in worker.py; it proves worker configuration, not successful HTTP readiness or an actual renderer invocation.

Outcome: BLOCKED by application_startup_failure / TimeoutError at the 30-second startup deadline. Runner elapsed time 31.312 seconds, excluding final evidence export. Controller never received HTTP 200 from GET /api/state during startup. Individual polling outcomes were not recorded; no specific HTTP status, connectivity error, or server exception can be assigned. Application log is empty. No worker_failure.json exists. Cleanup stopped the owned worker (exit 1); no unrelated process was terminated.

Provider requests dispatched: **0**, derived from zero dispatch_attempted/admitted/completed entries in the initialized journal. Native result exposes null live_calls and lacks a budget snapshot; those raw fields are preserved. Zero is a review derivation from the durable journal and empty scenario steps, not a fabricated native counter.

Campaign scenario steps: none; new campaign and Start Campaign never submitted. Player turns attempted/completed: 0/0. Opening acceptance unknown, not rejected; no presentation plan, parsing, semantic validation, rendering, or publication occurred. No provider HTTP failures or parser failures were observed because no request occurred. All five actions were skipped due to startup timeout. Request budget was not exhausted.

Evidence paths relative to archive root: harness/20261101T150418Z-2c4a2a1e0fe1/configuration/run.json; diagnostics/ready.json; diagnostics/provider_usage.jsonl; diagnostics/execution_log.json; reports/result.json; reports/SUMMARY.md; reports/GAMEPLAY_REPORT.md; data/; evidence/evidence.zip. Original empty directories retained in the filesystem; absent baseline/opening/turn snapshots are explicitly unavailable. Isolated bootstrap files retained as post-shutdown evidence, not relabeled as gameplay snapshots.
