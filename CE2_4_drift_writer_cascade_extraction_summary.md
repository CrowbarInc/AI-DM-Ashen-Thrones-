# CE2.4 — Drift Writer Cascade Extraction Summary

## Summary

Extracted drift-specific artifact writing, markdown rendering, and orchestration from `tests/helpers/failure_dashboard_report.py` into `tests/helpers/failure_dashboard_drift.py`. The report hub now delegates drift work via compatibility re-exports; implementation moved verbatim to preserve artifact formats, filenames, write order, and public import sites.

Hub size reduced from **1,469 LOC / 43 functions** (post CE2.3) to **996 LOC / 27 functions** — a **32% LOC reduction** in the report hub. Drift ownership is now **540 LOC / 17 functions** in the dedicated module.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_drift.py` | **Added** — drift markdown renderers, artifact writers, scorecard cascade orchestration |
| `tests/helpers/failure_dashboard_report.py` | Removed ~473 LOC of drift code; re-exports 12 public drift APIs; retains path/env constant re-exports for tool compatibility |
| `tests/test_failure_dashboard_drift.py` | **Added** — compatibility, writer, cascade-order, import-direction tests |

## Responsibilities Moved

| Responsibility | Old Owner | New Owner | Compatibility Preserved |
|---|---|---|---|
| Rerun drift scorecard markdown (`render_rerun_drift_scorecard_markdown`) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Rerun drift scorecard writer cascade (`write_rerun_drift_scorecard_artifacts`) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Opt-in rerun scorecard gate (`write_rerun_drift_scorecard_artifacts_if_requested`) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Longitudinal artifact writers | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Hotspot artifact writers | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Trend artifact writers | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Risk artifact writers (incl. recurrence side-effect trigger) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Hotspot classification collection (`collected_hotspot_classifications`) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Longitudinal scorecard aggregation helper | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Rerun scorecard env gate (`rerun_drift_scorecard_requested`) | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Yes — re-exported |
| Owner drift summary/breakdown markdown helpers | `failure_dashboard_report.py` | `failure_dashboard_drift.py` | Internal — imported by hub for dashboard/protected/stability surfaces |

## Remaining Responsibilities in failure_dashboard_report.py

| Metric | CE2 baseline (pre CE2.1) | Post CE2.3 | Post CE2.4 |
|---|---:|---:|---:|
| LOC | 3,359 | 1,469 | **996** |
| Functions | 82 | 43 | **27** |

Still owned by the hub:

- Generic failure dashboard table rendering
- Protected replay failure report rendering
- Long-session stability scorecard rendering and writers
- Session recording wrapper (`record_protected_replay_assertion_failure`)
- Pytest session artifact facade (`write_requested_dashboard_artifacts`)
- Path, session, recurrence, and drift compatibility re-exports

## Dependency Graph

```
failure_dashboard_report.py
  → failure_dashboard_drift.py
  → failure_dashboard_recurrence.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → replay_drift_reports.py
  → failure_classifier.py
  → runtime_lineage_reporting.py

failure_dashboard_drift.py
  → failure_dashboard_paths.py
  → failure_dashboard_session.py
  → failure_dashboard_recurrence.py
  → replay_drift_reports.py

failure_dashboard_recurrence.py
  → failure_dashboard_paths.py
  → replay_bug_recurrence.py
  → replay_drift_reports.py

failure_dashboard_session.py
  → game.runtime_lineage_telemetry (normalize only)

failure_dashboard_paths.py
  → (stdlib only)

replay_drift_reports.py
  → replay_drift_hotspots.py
  → replay_drift_longitudinal.py
  → replay_drift_trends.py
  → replay_drift_risk.py
```

**No reverse imports.** **No new cycles.**

- `failure_dashboard_drift` does **not** import `failure_dashboard_report`
- Drift analytics remain in `replay_drift_*` modules; drift module orchestrates and renders only

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Filenames | **No** |
| Directories | **No** |
| Report formats | **No** (code moved verbatim) |
| Drift calculations | **No** |
| Artifact contents | **No** |
| Cascade write order | **No** — scorecard → append longitudinal → longitudinal artifacts → hotspots → trends → risk |

Path and env constants remain re-exported from `failure_dashboard_report.py` for tool compatibility (`OWNER_DRIFT_*`, `RERUN_DRIFT_SCORECARD_*`, etc.).

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_drift.py tests/test_failure_dashboard_report.py tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_classifier.py tests/test_replay_drift_hotspots.py tests/test_replay_drift_longitudinal.py tests/test_replay_drift_trends.py tests/test_replay_drift_risk.py tests/test_golden_replay_trend.py tests/test_bz_protected_replay_trend_window_2.py -rA --tb=no

# 313 passed
```

Additional baseline check (not in required pass set):

```text
python -m pytest tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report --tb=line

# 1 failed (baseline)
```

## Known Baseline Issues

**Unchanged** — not caused by this block:

```text
tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report
# IndexError: list index out of range in tmp_path/bug_recurrence_event_log.json
```

## Follow-up Recommendation

**Proceed to CE2.5 — Stability Module Extraction.**

The largest remaining hub concentrations are:

1. Long-session stability scorecard rendering and writers (`render_long_session_stability_scorecard_markdown`, `write_long_session_stability_scorecard_artifacts`)
2. Protected replay failure report rendering
3. Generic failure dashboard table rendering

CE2.5 should extract stability scorecard ownership while keeping drift and recurrence modules unchanged.

Diagnostic Concentration Risk impact: **significant reduction** — drift writer cascade (~540 LOC, 17 functions) is now isolated; hub LOC down 70% from CE2 baseline and 32% from CE2.3.
