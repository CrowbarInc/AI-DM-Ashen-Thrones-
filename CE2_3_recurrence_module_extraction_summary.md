# CE2.3 — Recurrence Module Extraction Summary

## Summary

Extracted recurrence-specific markdown rendering and artifact orchestration from `tests/helpers/failure_dashboard_report.py` into `tests/helpers/failure_dashboard_recurrence.py`. The report hub now delegates recurrence work via compatibility re-exports; implementation moved verbatim to preserve report and JSON output.

Hub size reduced from **3,280 LOC / 65 functions** (post CE2.2) to **1,469 LOC / 43 functions** — a **55% LOC reduction** in the report hub. Recurrence ownership is now **1,845 LOC** in the dedicated module.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_recurrence.py` | **Added** — recurrence markdown renderers, metadata helper, history writer orchestration |
| `tests/helpers/failure_dashboard_report.py` | Removed ~1,776 LOC of recurrence code; re-exports 3 public recurrence APIs; dropped direct `replay_bug_recurrence` imports |
| `tests/test_failure_dashboard_recurrence.py` | **Added** — compatibility, writer, import-direction tests |

## Responsibilities Moved

| Responsibility | Old Owner | New Owner | Compatibility Preserved |
|---|---|---|---|
| Recurrence history markdown (`render_bug_recurrence_history_markdown`) | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Yes — re-exported |
| Recurrence history JSON writer (`write_bug_recurrence_history_artifacts`) | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Yes — re-exported |
| Protected replay recurrence metadata (`protected_replay_recurrence_event_metadata`) | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Yes — re-exported |
| 16 `_recurrence_*_markdown_lines` section builders | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Internal (private) |
| Recurrence orchestration stack (analytics → payload → side-effect docs) | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Via writer re-export |
| Recurrence markdown `_cell` helper | `failure_dashboard_report.py` | `failure_dashboard_recurrence.py` | Internal duplicate |

## Remaining Responsibilities in failure_dashboard_report.py

| Metric | CE2 baseline (pre CE2.1) | Post CE2.2 | Post CE2.3 |
|---|---:|---:|---:|
| LOC | 3,359 | 3,280 | **1,469** |
| Functions | 82 | 65 | **43** |

Still owned by the hub:

- Dashboard / protected failure / scorecard / stability rendering
- Drift hotspot/trend/longitudinal/risk writer orchestration
- Session recording wrapper (`record_protected_replay_assertion_failure`)
- Pytest session artifact facade (`write_requested_dashboard_artifacts`)
- Path and session compatibility re-exports

## Dependency Graph

```
failure_dashboard_report.py
  → failure_dashboard_recurrence.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → replay_drift_reports.py
  → failure_classifier.py
  → runtime_lineage_reporting.py

failure_dashboard_recurrence.py
  → failure_dashboard_paths.py
  → replay_bug_recurrence.py
  → replay_drift_reports.py

failure_dashboard_session.py
  → game.runtime_lineage_telemetry (normalize only)

failure_dashboard_paths.py
  → (stdlib only)

replay_bug_recurrence.py
  → failure_dashboard_paths.py
```

**No reverse imports.** **No new cycles.**

- `failure_dashboard_recurrence` does **not** import `failure_dashboard_report` or `failure_dashboard_session`
- `failure_dashboard_report` no longer imports `replay_bug_recurrence` directly

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Filenames | **No** |
| Directories | **No** |
| Report formats | **No** (code moved verbatim) |
| Recurrence semantics | **No** |
| Artifact contents | **No** |

Path constants remain re-exported from `failure_dashboard_report.py` for tool compatibility (`BUG_RECURRENCE_*`, `RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH`, etc.).

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_dashboard_report.py tests/test_failure_classifier.py tests/test_replay_bug_class_recurrence.py tests/test_replay_drift_hotspots.py tests/test_replay_drift_longitudinal.py tests/test_replay_drift_trends.py tests/test_replay_drift_risk.py tests/test_golden_replay_trend.py tests/test_bz_protected_replay_trend_window_2.py tests/test_golden_replay_protected_bridge.py -q --tb=line

# 475 passed, 1 failed (baseline)
```

Note: `tests/test_replay_bug_recurrence.py` does not exist; ran `tests/test_replay_bug_class_recurrence.py` instead.

## Known Baseline Issues

**Unchanged** — not caused by this block:

```text
tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report
# IndexError: empty events list in tmp_path/bug_recurrence_event_log.json
```

Tmp-path protected recurrence writes route to the session-diagnostic event log per existing dashboard report tests.

## Follow-up Recommendation

**Proceed to CE2.4 — Drift Writer Cascade Extraction.**

The largest remaining hub concentrations are:

1. Drift artifact writer cascade (`write_rerun_drift_scorecard_artifacts` fans out to longitudinal/hotspot/trend/risk/recurrence)
2. Protected failure + stability scorecard rendering
3. Dashboard table rendering

CE2.4 should extract drift writer orchestration while keeping render/write pairs and cascade order locked by existing drift test modules.

Diagnostic Concentration Risk impact: **significant reduction** — recurrence block (~54% of pre-split function LOC) is now isolated; hub LOC down 56% from CE2 baseline.
