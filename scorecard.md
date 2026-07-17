# Golden Rerun Drift Scorecard

- Generated at: `2026-06-24T00:00:00Z`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_failure_dashboard_orchestration.py tests/test_failure_dashboard_report.py tests/test_failure_dashboard_stability.py tests/test_failure_dashboard_drift.py tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_classifier.py -rA --tb=no`
- Report only: `true`

## Summary

- Total turns compared: `1`
- Speaker deltas: `1`
- Route deltas: `1`
- Fallback deltas: `0`
- Text fingerprint deltas: `1`
- Scaffold predicate deltas: `0`
- Runtime-lineage deltas: `0`
- Semantic delta frequency deltas: `0`


## Owner Drift Summary

| Owner Drift Bucket | Count |
|---|---:|
| `replay_drift_unclassified` | `1` |
| `route_drift` | `1` |
| `speaker_drift` | `1` |

## Semantic Delta Frequency

- Response-delta checked delta: `{}`
- Response-delta failed delta: `{}`
- Response-delta repaired delta: `{}`
- Response-delta kind deltas: `{}`
- Echo-overlap band deltas: `{}`
- Response-delta unknown delta: `{}`

## Compact Per-Turn Drift Rows

| Turn | Previous Turn ID | Current Turn ID | Drift Fields | Details |
|---:|---|---|---|---|
| 0 | t01 | t01 | route, speaker, text_fingerprint | route dialogue -> action; speaker runner -> guard; text_hash c859b4c0778c0314 -> 975d25cb28e506cb |
