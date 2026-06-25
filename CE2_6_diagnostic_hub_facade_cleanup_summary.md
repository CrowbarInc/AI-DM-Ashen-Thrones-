# CE2.6 — Diagnostic Hub Final Facade / Orchestration Cleanup Summary

## Summary

Extracted pytest-session artifact orchestration from `tests/helpers/failure_dashboard_report.py` into `tests/helpers/failure_dashboard_orchestration.py`. The report hub now delegates orchestration via compatibility re-exports; implementation moved verbatim to preserve artifact gates, write ordering, and public import sites.

Hub size reduced from **772 LOC / 22 functions** (post CE2.5) to **723 LOC / 20 functions** — a **6% LOC reduction**. Orchestration ownership is now **88 LOC / 2 functions** in the dedicated module.

Across CE2 (CE2.1–CE2.6), the report hub shrank from **3,359 LOC / 82 functions** to **723 LOC / 20 functions** — a **78% LOC reduction**.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_orchestration.py` | **Added** — session artifact dispatch and env-gated recording cleanup |
| `tests/helpers/failure_dashboard_report.py` | Removed orchestration block; re-exports 2 public orchestration APIs |
| `tests/test_failure_dashboard_orchestration.py` | **Added** — compatibility, gate, ordering, import-direction tests |

## Responsibilities Moved

| Responsibility | Old Owner | New Owner | Compatibility Preserved |
|---|---|---|---|
| Pytest-session artifact dispatch (`write_requested_dashboard_artifacts`) | `failure_dashboard_report.py` | `failure_dashboard_orchestration.py` | Yes — re-exported |
| Env-gated recording cleanup (`clear_requested_artifact_recordings`) | `failure_dashboard_report.py` | `failure_dashboard_orchestration.py` | Yes — re-exported |

## Remaining Responsibilities in failure_dashboard_report.py

| Metric | CE2 baseline | CE2.3 | CE2.4 | CE2.5 | CE2.6 |
|---|---:|---:|---:|---:|---:|
| LOC | 3,359 | 1,469 | 996 | 772 | **723** |
| Functions | 82 | 43 | 27 | 22 | **20** |

Still owned by the hub (~723 LOC):

| Domain | Examples |
|---|---|
| Generic failure dashboard rendering | `render_failure_dashboard_markdown`, `write_failure_dashboard_artifact` |
| Protected replay failure reporting | `render_protected_replay_failure_report`, `write_protected_replay_failure_report_if_present` |
| Classification row building | `build_failure_dashboard_rows`, `record_protected_replay_assertion_failure` |
| Dashboard env gate | `failure_dashboard_requested` |
| Compatibility re-exports | orchestration, stability, drift, recurrence, session, path constants |

Extracted diagnostic modules:

| Module | LOC | Functions | Domain |
|---|---:|---:|---|
| `failure_dashboard_recurrence.py` | 1,845 | — | Recurrence history |
| `failure_dashboard_drift.py` | 540 | 17 | Drift artifact cascade |
| `failure_dashboard_stability.py` | 262 | 6 | Stability scorecards |
| `failure_dashboard_orchestration.py` | 88 | 2 | Session artifact dispatch |
| `failure_dashboard_session.py` | — | — | Session buffers |
| `failure_dashboard_paths.py` | — | — | Path registry |

## Compatibility Exports Preserved

All existing import sites continue to work via `failure_dashboard_report.py` re-exports:

- `write_requested_dashboard_artifacts` (conftest `pytest_sessionfinish`)
- `clear_requested_artifact_recordings` (conftest `pytest_configure`)
- All drift, stability, recurrence, session, and path symbols unchanged

Object identity preserved for orchestration re-exports.

## Dependency Graph

```
failure_dashboard_report.py
  → failure_dashboard_orchestration.py
  → failure_dashboard_stability.py
  → failure_dashboard_drift.py
  → failure_dashboard_recurrence.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → replay_drift_reports.py
  → failure_classifier.py
  → runtime_lineage_reporting.py

failure_dashboard_orchestration.py
  → failure_dashboard_drift.py
  → failure_dashboard_stability.py
  → failure_dashboard_session.py
  → failure_dashboard_report.py (lazy, function-scoped only — rendering writers + dashboard gate)

failure_dashboard_stability.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → failure_dashboard_drift.py (_owner_drift_summary_table_lines)
  → replay_drift_reports.py

failure_dashboard_drift.py
  → failure_dashboard_recurrence.py
  → failure_dashboard_session.py
  → failure_dashboard_paths.py
  → replay_drift_reports.py
```

**No top-level reverse imports.** **No import cycles at module load.**

Orchestration lazy-imports report rendering writers inside dispatch functions to avoid a load-time cycle while keeping rendering in the report facade.

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Filenames | **No** |
| Directories | **No** |
| Markdown content | **No** |
| JSON schemas | **No** |
| Artifact write gates | **No** |
| Artifact ordering | **No** — failure: protected → dashboard; success: rerun → stability; dashboard when gated |
| Env/pytest option behavior | **No** |

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_orchestration.py tests/test_failure_dashboard_report.py tests/test_failure_dashboard_stability.py tests/test_failure_dashboard_drift.py tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_classifier.py -rA --tb=no

# 227 passed
```

## Known Baseline Issues

**Unchanged** — not caused by this block:

```text
tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report
# IndexError: list index out of range in tmp_path/bug_recurrence_event_log.json
```

## Recommendation — CE2 Closure

**CE2 can close.**

The diagnostic hub decomposition is complete:

1. **CE2.1** — path registry isolated
2. **CE2.2** — session buffers isolated
3. **CE2.3** — recurrence rendering/orchestration isolated
4. **CE2.4** — drift writer cascade isolated
5. **CE2.5** — stability scorecards isolated
6. **CE2.6** — session orchestration isolated

`failure_dashboard_report.py` is now a focused **compatibility/rendering facade** (~723 LOC, 20 functions) with no broad artifact-family ownership. Diagnostic Concentration Risk is substantially reduced: specialized surfaces live in dedicated modules; the hub primarily renders dashboard and protected-replay reports plus re-exports.

Optional future work (outside CE2 scope): move protected-replay writer side-effects (hotspot/risk cascade on failure write) into orchestration or drift, further slimming the report module. Not required for CE2 closure.
