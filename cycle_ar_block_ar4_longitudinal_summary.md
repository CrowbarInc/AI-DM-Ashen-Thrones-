# Cycle AR — Block AR4: Longitudinal Drift Attribution Summary

**Date:** 2026-06-06  
**Prerequisites:** AR2 (`owner_drift_classifications`), AR3 (reporting integration)

---

## 1. Existing scorecard inventory (pre-AR4)

### Artifact locations

| Artifact | Path | Writer |
| --- | --- | --- |
| Rerun scorecard JSON | `artifacts/golden_replay/rerun_drift_scorecard.json` | `write_rerun_drift_scorecard_artifacts` |
| Rerun scorecard markdown | `artifacts/golden_replay/rerun_drift_scorecard.md` | `write_rerun_drift_scorecard_artifacts` |
| Protected failure report | `artifacts/golden_replay/replay_failure_report.md` | `write_protected_replay_failure_report_if_present` |
| Failure dashboard (opt-in) | `audits/failure_dashboard_latest.md` | `write_failure_dashboard_artifact` |
| **Longitudinal JSON (AR4)** | `artifacts/golden_replay/owner_drift_longitudinal.json` | `write_owner_drift_longitudinal_artifacts` |
| **Longitudinal markdown (AR4)** | `artifacts/golden_replay/owner_drift_longitudinal.md` | `write_owner_drift_longitudinal_artifacts` |

### Scorecard schema (AR2/AR3 relevant keys)

```json
{
  "schema_version": 1,
  "report_only": true,
  "total_turns_compared": 1,
  "summary": { "speaker_delta_count": 0, "...": 0 },
  "frequencies": { "...": {} },
  "per_turn_deltas": [],
  "owner_drift_classifications": [
    { "turn_index": 0, "owner_drift_bucket": "speaker_drift", "delta_key": "speaker" }
  ]
}
```

### Protected failure row schema (AR3)

Classification rows include optional `owner_drift_bucket` plus existing category/owner fields. Protected reports do **not** feed longitudinal aggregation in AR4 — longitudinal scope is **rerun scorecard history** only.

### Retention behavior

| Mechanism | Behavior |
| --- | --- |
| `record_rerun_drift_scorecard()` | Appends scorecards to in-memory session list `_RECORDED_RERUN_DRIFT_SCORECARDS` |
| `recorded_rerun_drift_scorecards()` | Returns session scorecard history for aggregation |
| `pytest_sessionfinish` (opt-in) | Writes latest scorecard + longitudinal artifacts on successful golden replay run with `--write-rerun-drift-scorecard` |
| On-disk artifacts | Overwritten each write; no automatic multi-session persistence beyond pytest session recording |

### Existing aggregation helpers (pre-AR4)

| Helper | Module | Scope |
| --- | --- | --- |
| `summarize_owner_drift_buckets(classifications)` | `replay_drift_taxonomy.py` | Single scorecard / single row set |
| `aggregate_owner_drift_history(scorecards)` | `replay_drift_longitudinal.py` | **AR4** multi-run |

---

## 2. Aggregation model

### `aggregate_owner_drift_history(scorecards)`

Input: list of rerun scorecard dicts (uses `owner_drift_classifications` only).

Output:

```python
{
    "total_runs": 3,
    "total_owner_drift_events": 5,
    "owner_bucket_counts": { "route_drift": 2, "speaker_drift": 3, ... },
    "owner_bucket_percentages": { "route_drift": 40.0, "speaker_drift": 60.0, ... },
    "most_common_bucket": "speaker_drift",
    "least_common_bucket": "route_drift",
}
```

Rules:

- Skips scorecards with `comparison_available: false`
- Percentages = bucket count / total events across all runs (1 decimal)
- Most/least common among buckets with count > 0; ties broken alphabetically by bucket name

### `build_owner_drift_trend_summary(history)`

Returns all 9 buckets with `bucket`, `count`, `percentage`, `rank` (rank 1 = highest count).

### `render_owner_drift_longitudinal_report(history)`

Advisory markdown with trend table + highest/lowest concentration sections.

---

## 3. Files modified

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_longitudinal.py` | **New.** Aggregation, trend summary, markdown renderer |
| `tests/helpers/failure_dashboard_report.py` | Longitudinal artifact paths; `write_owner_drift_longitudinal_artifacts`; append on scorecard write |
| `tests/test_replay_drift_longitudinal.py` | **New.** 8 tests |

**Not modified:** `game/**`, replay assertions, protected scenarios, existing report section renderers (append-only integration).

---

## 4. Report integration (append-only)

When `write_rerun_drift_scorecard_artifacts` runs:

1. Writes existing scorecard JSON + markdown (unchanged AR3 content).
2. **Appends** `# Owner Drift Longitudinal Report` to scorecard markdown file.
3. Writes standalone `owner_drift_longitudinal.json` and `.md` with full history aggregate + `trend_summary`.

History source: `recorded_rerun_drift_scorecards()` when non-empty, else current scorecard.

---

## 5. Sample outputs

### Longitudinal markdown

```markdown
# Owner Drift Longitudinal Report

- Advisory only: `true`
- Report only: `true`
- Total runs: `3`
- Total owner drift events: `5`

## Owner Drift Trend Summary

| Bucket | Count | Percentage |
|---|---:|---:|
| `speaker_drift` | `3` | 60% |
| `route_drift` | `2` | 40% |

## Highest Concentration

`speaker_drift`

## Lowest Concentration

`route_drift`
```

### Longitudinal JSON (excerpt)

```json
{
  "advisory_only": true,
  "most_common_bucket": "speaker_drift",
  "owner_bucket_counts": { "speaker_drift": 3, "route_drift": 2 },
  "report_only": true,
  "schema_version": 1,
  "total_runs": 3,
  "trend_summary": [
    { "bucket": "speaker_drift", "count": 3, "percentage": 60.0, "rank": 1 }
  ]
}
```

---

## 6. Test coverage

**`tests/test_replay_drift_longitudinal.py`** — 8 tests:

- Empty history aggregation
- Single scorecard
- Multiple scorecards + percentages
- Trend ranking
- Report rendering (populated + empty)
- Standalone artifact write
- Scorecard write appends longitudinal + writes standalone artifacts

**Regression:** longitudinal + taxonomy + golden replay suites — all green.

---

## 7. Compatibility verification

| Check | Result |
| --- | --- |
| Scorecard `report_only: true` | Pass — unchanged |
| Pass/fail logic | Pass — no comparator/assertion changes |
| Existing scorecard markdown sections | Pass — longitudinal appended after existing content |
| Protected failure report | Pass — not modified |
| New telemetry | Pass — none; consumes `owner_drift_classifications` only |

---

## 8. Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass |
| No new protected scenarios | Pass |
| No runtime changes | Pass |
| No new acceptance gates | Pass — `advisory_only: true` on longitudinal JSON |
| Longitudinal does not affect CI pass/fail | Pass |

---

## 9. Acceptance

**PASS** — owner drift trends aggregate across scorecard history; percentages and rankings generated; longitudinal reports render; replay behavior unchanged.

**Operator command** (unchanged from Cycle S, now also writes longitudinal artifacts):

```powershell
python -m pytest -m golden_replay -q --write-rerun-drift-scorecard
```

Artifacts: `rerun_drift_scorecard.*`, `owner_drift_longitudinal.*`
