# User Guide and Operational Readiness

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

The standalone guide is `docs/AUTOMATED_PLAYTEST_GUIDE.md`. It covers installation,
all modes, exact commands, authorization/cost, result interpretation, ZIP discovery,
timeouts, safe recovery and limitations without requiring implementation knowledge.

Deterministic command (executed successfully through PowerShell):

```powershell
.\scripts\run_live_playtest.ps1 -Scenario CampaignOpening -Mode Deterministic -CaptureResponse
```

Latest summary/verdict and exact evidence ZIP path:

```powershell
.\scripts\run_live_playtest.ps1 -Latest
```

Scripted deterministic example:

```powershell
.\scripts\run_live_playtest.ps1 -Scenario ScriptedObservation -Mode ScriptedGameplay
```

Example PASS summary: `artifacts/atgb/automated_playtests/20261030T011639Z-812744c9c860/reports/SUMMARY.md`.
Example machine report: `artifacts/atgb/automated_playtests/20261030T011639Z-812744c9c860/reports/result.json`.
Example evidence: `artifacts/atgb/automated_playtests/20261030T011639Z-812744c9c860/evidence/evidence.zip`.
Run layout is unique, local, path-space safe and compatible with the established
ATGB isolation root. A fixed optional localhost port refuses an existing listener.
No manual environment setup, fixture copying, Uvicorn window, API invocation,
journal collection or compression is needed. Exit 0 means PASS; 2 means another
verdict. PowerShell may display a nonzero native command exit as its own failure.
No live command has been executed. Read report 10 before considering one.
