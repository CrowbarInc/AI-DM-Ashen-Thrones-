# 18 — Frozen holdout

Developer-authored. Not external validation.

Frozen before the memory-question repair and the greeting repair.

- Cases in the manifest: 105
- Hash: `32f047cb11ef518eb3cf485815ff61a98712bd2c56a3205d323fb866f2fccbbd`
- Hash matched the freeze file: yes
- Passed: 105
- Failed: 0
- Multi-turn cases: 45
- Save/resume executions: 15
- Cross-domain cases: 45
- Narration cases: 15

The fixture was not edited after the run. Later repairs were checked with development tests and the HTTP campaign, not by changing the holdout. Results: `artifacts/pr_play_79/holdout_results.json`.
