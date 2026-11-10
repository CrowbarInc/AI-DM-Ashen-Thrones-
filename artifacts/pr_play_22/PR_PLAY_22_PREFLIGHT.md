# PR-PLAY-22 preflight

Verdict: PASS. One offline cycle; zero live provider calls. Loopback TCP, Player HTTP readiness, internal snapshots, owned-process shutdown and port release verified. No campaign initialized during preflight.

Branch: feature/product-realization. Full dirty status and revision: repository_status.json. Existing uncommitted api.py, api_ui_mode.py, gm.py and harness changes retained; no reset. Production and harness hashes recorded in offline_source_hashes.json. No AGENTS.md found by repository search; .agents directory empty.

Existing harness: scripts/run_live_playtest.ps1 and tools/playtest runner/worker; FiveTurnGameplay scenario version 1.0.0. Test-only PR-PLAY-22 controller reuses isolation, child environment, HTTP transport, readiness, logging, snapshots and cleanup. Replaces privileged HTTP snapshot access with Player HTTP plus direct isolated-file diagnostics. Does not alter production behavior.

Configured provider: existing OpenAI Responses integration, gpt-4.1-mini. Credentials present; never serialized. ASHEN_OPENING_RENDERER=1; output allowance 3000 unchanged. Diagnostics and response recording enabled. SDK retries=0, host retries=0; every actual dispatch guarded against model variation. No provider connectivity probe. Author/Debug modes remain denied by resolve_requested_ui_mode; no privileged HTTP requests made.

Budget: production durable admission tested offline: six synthetic dispatches permitted, seventh refused before invocation. Live request ceiling 6; token ceilings 200000 input / 20000 output / 220000 total unchanged. All calls, including interpretation and realization, count. Pending calls may consume remaining budget within an ordinary turn; exhaustion stops the experiment.

Known baseline: PR-PLAY-21 test results and repaired_tests.txt retain 17 functional failures (3 opening, 14 ordinary); one additional transient Windows I/O failure passed its targeted rerun. No repairs or fresh broad suite during this product experiment. Existing failure evidence will be correlated only where behavior supports it.

Offline evidence: ../atgb/pr_play_22/offline. offline_summary.json and offline_budget_verification.json. The synthetic budget ledger is explicitly offline evidence, not live usage. Worker is terminated by existing owned-process cleanup (Windows exit code 1); socket rebind confirms release.
