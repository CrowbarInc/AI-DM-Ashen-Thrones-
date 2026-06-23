# BZ Protected Replay Trend Window #2

Report-only measurement lane comparing BW baseline run artifacts to BZ window output.

## Replay Key Movement

- Corpus match: `True`
- Baseline: `artifacts/golden_replay/trend_window/runs/run-000.json`
- Current: `artifacts/golden_replay/trend_window_2/runs/run-000.json`
- Active keys: `49`
- New keys: `10`
- Retired keys: `0`
- Unchanged keys: `39`

## Recurrence Movement

- Comparison mode: `baseline_establishment`
- Baseline available: `False`
- Current available: `True`
- Current snapshot: `artifacts/golden_replay/bug_recurrence_history.json`
- Newly recurring: `0`
- Still recurring: `0`
- No longer recurring: `0`
- Count increased: `0`
- Count decreased: `0`

## Regression Recurrence Rate Evidence

Use the explicit current recurrence snapshot at `artifacts/golden_replay/bug_recurrence_history.json` (`protected_replay_regression_recurrence_rate`) to score Regression Recurrence Rate. BZ recurrence movement does not infer BW-time recurrence state when `comparison_mode` is `baseline_establishment`.

## Success Criteria

- Measurement only; no replay behavior changes.
- BW artifacts under `artifacts/golden_replay/trend_window/` remain immutable inputs.
- BZ artifacts are written only under `artifacts/golden_replay/trend_window_2/`.
