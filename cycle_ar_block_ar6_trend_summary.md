# Cycle AR — Block AR6: Drift Trend Analysis Summary

**Date:** 2026-06-06  
**Prerequisites:** AR4 (longitudinal scorecard history), AR5 (hotspot reporting)

---

## Objective

Convert longitudinal scorecard owner drift counts into trend-aware diagnostics so operators can see whether replay instability is improving, worsening, or stable — advisory only.

---

## Trend model

### Input

Ordered **longitudinal scorecard history** — list of rerun scorecards with `owner_drift_classifications` (from `recorded_rerun_drift_scorecards()` or explicit list).

### Comparison window

- **Current** = latest scorecard in history
- **Previous** = immediately prior scorecard (zeros if only one run)

### Per-bucket output (`compute_owner_drift_trends`)

```python
{
    "route_drift": {
        "current": 10,
        "previous": 6,
        "delta": 4,
        "direction": "up",
    },
    ...
}
```

All **9** owner drift buckets always present.

### Direction rules (deterministic)

| Delta | Direction |
| --- | --- |
| `> 0` | `up` |
| `< 0` | `down` |
| `== 0` | `stable` |

### Interpretation for operators

| Direction | Meaning for drift counts |
| --- | --- |
| `up` | **Worsening** — more drift events in latest run |
| `down` | **Improving** — fewer drift events in latest run |
| `stable` | Unchanged between runs |

---

## Files modified

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_trends.py` | **New.** Trend computation, summary, enrichment, markdown renderer |
| `tests/helpers/replay_drift_hotspots.py` | Top drift fields show Count + Trend when enriched |
| `tests/helpers/failure_dashboard_report.py` | Trend artifact paths; `write_owner_drift_trend_artifacts`; hotspot/trend integration on scorecard write |
| `tests/test_replay_drift_trends.py` | **New.** 8 tests |
| `tests/test_replay_drift_hotspots.py` | +1 trend display test |

**Not modified:** `game/**`, replay assertions, protected scenarios, pass/fail logic.

---

## Artifact outputs

| Artifact | Path |
| --- | --- |
| Trend JSON | `artifacts/golden_replay/owner_drift_trends.json` |
| Trend markdown | `artifacts/golden_replay/owner_drift_trends.md` |

Written by `write_owner_drift_trend_artifacts()` when rerun scorecard artifacts are generated.

JSON payload includes: `owner_drift_trends`, `owner_bucket_trend_summary`, `field_drift_trends`, `scorecard_runs_compared`, `advisory_only: true`.

---

## Sample trend markdown

```markdown
# Owner Drift Trend Report

- Advisory only: `true`
- Report only: `true`

## Drift Trend Summary

| Bucket | Previous | Current | Delta | Direction |
|---|---:|---:|---:|---|
| `route_drift` | 6 | 10 | +4 | `up` |
| `speaker_drift` | 8 | 5 | -3 | `down` |

## Improving Areas

- `speaker_drift` (-3)

## Worsening Areas

- `route_drift` (+4)

## Stable Areas

- `fallback_drift`
```

---

## Hotspot trend integration

`enrich_hotspots_with_field_trends()` compares field-path counts between latest and prior scorecards and attaches `trend_direction` to `top_drift_fields`.

Hotspot markdown example:

```markdown
## Top Drift Fields

1. selected_speaker_id
   Count: 15
   Trend: up
```

Enabled automatically when hotspot artifacts are written alongside scorecard history.

---

## Test coverage

**`tests/test_replay_drift_trends.py`** — 8 tests:

- Empty history (all stable)
- Increasing / decreasing bucket trends
- Single-run baseline
- All-bucket summary table
- Trend report rendering
- Hotspot enrichment
- Artifact generation

**Regression:** 50 tests across AR4–AR6 diagnostic modules — all green.

---

## Compatibility verification

| Check | Result |
| --- | --- |
| Pass/fail unchanged | Pass |
| Assertions unchanged | Pass |
| Existing report sections unchanged | Pass — trend/hotspot artifacts standalone; scorecard body unchanged |
| Scorecard `report_only` | Pass |

---

## Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass |
| No runtime changes | Pass |
| No new acceptance gates | Pass |
| Advisory only | Pass |

---

## Acceptance

**PASS** — trends computed correctly; trend reports generated; hotspot reports enriched with field trends; replay behavior unchanged.

**Operator command** (unchanged):

```powershell
python -m pytest -m golden_replay -q --write-rerun-drift-scorecard
```

Produces scorecard, longitudinal, hotspot, and trend artifacts under `artifacts/golden_replay/`.
