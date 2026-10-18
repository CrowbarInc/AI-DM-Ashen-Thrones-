PR-DW state persistence

Disposable save path:
- `artifacts/pr_dw_interactive_playtest/disposable_data`

Disposable state after probes:
- `active_scene_id: frontier_gate`
- `turn_counter: 1`
- `time_pressure: 1`
- `interpretation_telemetry.interpretation_api_calls: 0`
- Session log entries: 2

Production save check:
- `data/session.json` remained `turn_counter: 0`
- `data/session.json` remained `last_saved_at: 2026-10-09T22:36:15.473168Z`

Persistence result:
- Disposable state persisted through the app.
- Production save files were not used for the PR-DW server run.

