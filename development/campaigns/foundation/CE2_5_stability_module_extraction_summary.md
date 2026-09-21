# CE2.5 — Stability Module Extraction Summary

## Summary

Extracted long-session stability scorecard rendering and artifact writing from `tests/helpers/failure_dashboard_report.py` into `tests/helpers/failure_dashboard_stability.py`. The report hub now delegates stability work via compatibility re-exports; implementation moved verbatim to preserve report contents, filenames, ordering, and public import sites.

Hub size reduced from **996 LOC / 27 functions** (post CE2.4) to **772 LOC / 22 functions** — a **22% LOC reduction** in the report hub. Stability ownership is now **262 LOC / 6 functions** in the dedicated module.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_stability.py` | **Added** — stability markdown renderers, artifact writers, env gate |
| `tests/helpers/failure_dashboard_report.py` | Removed ~224 LOC of stability code; re-exports 4 public stability APIs; retains path/env constant re-exports for tool compatibility |
| `tests/test_failure_dashboard_stability.py` | **Added** — compatibility, writer, session-flow, import-direction tests |

## Responsibilities Moved

| Responsibility | Old Owner | New Owner | Compatibility Preserved |
|---|---|---|---|
| Stability ownership markdown (`_stability_ownership_markdown_lines`) | `failure_dashboard_report.py` | `failure_dashboard_stability.py` | Internal (private) |
| Long-session scorecard markdown (`render_long_session_stability_scorecard_markdown`) | `failure_dashboard_report.py` | `failure_dashboard_stability.py` | Yes — re-exported |
| Stability artifact writer (`write_long_session_stability_scorecard_artifacts`) | `failure_dashboard_report.py` | `failure_dashboard_stability.py` | Yes — re-exported |
| Opt-in stability gate (`write_long_session_stability_scorecard_artifacts_if_requested`) | `failure_dashboard_report.py` | `failure_dashboard_stability.py` | Yes — re-exported |
| Stability env gate (`long_session_stability_scorecard_requested`) | `failure_dashboard_report.py` | `failure_dashboard_stability.py` | Yes — re-exported |

## Remaining Responsibilities in failure_dashboard_report.py

| Metric | CE2 baseline (pre CE2.1) | Post CE2.3 | Post CE2.4 | Post CE2.5 |
|---|---:|---:|---:|---:|
| LOC | 3,359 | 1,469 | 996 | **772** |
| Functions | 82 | 43 | 27 | **22** |

Still owned by the hub (~772 LOC):

| Domain | Approx. share | Examples |
|---|---|---|
| Generic failure dashboard rendering | ~35% | `render_failure_dashboard_markdown`, `write_failure_dashboard_artifact` |
| Protected replay failure reporting | ~40% | `render_protected_replay_failure_report`, `write_protected_replay_failure_report_if_present` |
| Classification row building | ~15% | `build_failure_dashboard_rows`, `record_protected_replay_assertion_failure` |
| Session artifact facade / orchestration | ~10% | `write_requested_dashboard_artifacts`, `clear_requested_artifact_recordings` |
| Compatibility re-exports | (import surface) | drift, recurrence, session, stability, path constants |

Extracted modules now own the specialized diagnostic surfaces:

| Module | LOC | Functions | Domain |
|---|---:|---:|---|
| `failure_dashboard_recurrence.py` | 1,845 | — | Recurrence history rendering/orchestration |
| `failure_dashboard_drift.py` | 540 | 17 | Drift artifact cascade |
| `failure_dashboard_stability.py` | 262 | 6 | Long-session stability scorecards |

## Dependency Graph

```
failure_dashboard_report.py
  → failure_dashboard_stability.py
  → failure_dashboard_drift.py
  → failure_dashboard_recurrence.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → replay_drift_reports.py
  → failure_classifier.py
  → runtime_lineage_reporting.py

failure_dashboard_stability.py
  → failure_dashboard_paths.py
  → failure_dashboard_session.py
  → failure_dashboard_drift.py (_owner_drift_summary_table_lines only)
  → replay_drift_reports.py

failure_dashboard_drift.py
  → failure_dashboard_paths.py
  → failure_dashboard_session.py
  → failure_dashboard_recurrence.py
  → replay_drift_reports.py

failure_dashboard_session.py
  → game.runtime_lineage_telemetry (normalize only)

failure_dashboard_paths.py
  → (stdlib only)
```

**No reverse imports.** **No new cycles.**

- `failure_dashboard_stability` does **not** import `failure_dashboard_report`
- Stability analytics remain in `replay_drift_reports` / taxonomy; stability module orchestrates and renders only

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Filenames | **No** |
| Directories | **No** |
| Report formats | **No** (code moved verbatim) |
| Stability metrics | **No** |
| Artifact contents | **No** |
| Scorecard ordering | **No** — writer uses `recorded_long_session_stability_scorecards()` for history/trends/hotspots |

Path and env constants remain re-exported from `failure_dashboard_report.py` for tool compatibility (`LONG_SESSION_STABILITY_SCORECARD_*`, etc.).

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_stability.py tests/test_failure_dashboard_report.py tests/test_failure_dashboard_drift.py tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_classifier.py tests/test_golden_replay_trend.py tests/test_bz_protected_replay_trend_window_2.py -rA --tb=no

# 279 passed
```

Additional contract coverage (not in required pass set):

```text
python -m pytest tests/test_stability_reporting_contract.py -q

# 10 passed
```

## Known Baseline Issues

**Unchanged** — not caused by this block:

```text
tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report
# IndexError: list index out of range in tmp_path/bug_recurrence_event_log.json
```

## Follow-up Recommendation

**The report hub is now sufficiently focused for a final optional cleanup block**, but not strictly required.

`failure_dashboard_report.py` at **772 LOC / 22 functions** (down **77%** from CE2 baseline) now primarily owns:

1. Generic dashboard table rendering
2. Protected replay failure report rendering
3. Classification row building
4. High-level pytest-session orchestration (`write_requested_dashboard_artifacts`)
5. Compatibility re-export facade

A **CE2.6 compatibility facade / orchestration extraction** could move `write_requested_dashboard_artifacts` and `clear_requested_artifact_recordings` into a thin `failure_dashboard_orchestration.py`, leaving the report hub as pure rendering. This is optional — the concentration risk metric has already dropped substantially across CE2.3–CE2.5.

Diagnostic Concentration Risk impact: **significant reduction** — stability block (~262 LOC) is now isolated; hub LOC down 77% from CE2 baseline and 22% from CE2.4.
