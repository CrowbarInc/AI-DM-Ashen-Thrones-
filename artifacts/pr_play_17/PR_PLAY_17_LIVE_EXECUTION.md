# PR-PLAY-17 Live Execution

Executed once in PowerShell, with scoped renderer flag and restoration in finally:

```powershell
$previousRenderer = $env:ASHEN_OPENING_RENDERER
try {
    $env:ASHEN_OPENING_RENDERER = '1'
    .\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse *>&1 | Tee-Object -FilePath artifacts/pr_play_17/live_console.txt
} finally { $env:ASHEN_OPENING_RENDERER = $previousRenderer }
```

The launcher's parameter contract was read before execution. Run ID: 20261101T153625Z-02fc6545bc28. Live invocations **1**, actual dispatched provider requests **1**, completed provider transports **1**. No synthetic live results. New Campaign returned 200; baseline capture succeeded. Start Campaign returned **422**, opening_failure_reason **arbitrary_narration_field**. Opening rejected; zero commits. Player turns attempted **0**, completed **0**, T1–T5 skipped. No rerun or repairs.

Earliest decisive failure: **Opening presentation-plan compliance**, a provider response format failure. Response was parseable JSON but contained narration/player_facing_text and declared_claims rather than selected_entries. Native diagnostic classification missing_structured_envelope is broader than the specific renderer rejection. Candidate then failed structured_contract_failure; application safe_nonresolution did not become an accepted opening. This is not a provider connection failure or budget exhaustion. Application refused publication and preserved state. Underlying cause of model noncompliance is not established.

See request_review.json, live_run/reports/result.json, live_run/diagnostics/provider_usage.jsonl and live_run/opening_response_evidence/. Exact provider HTTP status was not persisted; application 422 is not the provider HTTP status. Cleanup stopped owned PID 32648; independent port rebind passed (live_cleanup.json). Original harness evidence/evidence.zip preserved.
