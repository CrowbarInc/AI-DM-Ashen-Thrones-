# CE2.1 — Artifact Path Registry Extraction Summary

## Summary

Extracted replay diagnostic artifact path ownership from `tests/helpers/failure_dashboard_report.py` into a new dedicated module `tests/helpers/failure_dashboard_paths.py`. The hub module now imports path constants and path helpers from the registry and re-exports them for backward compatibility.

The measured import cycle between `failure_dashboard_report.py` and `replay_bug_recurrence.py` is **removed**. `replay_bug_recurrence.py` now imports `RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH` from `failure_dashboard_paths.py` at module level (no lazy import from the report hub).

No filenames, directories, report formats, or writer orchestration logic were changed.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_paths.py` | **Added** — canonical path constants, env gate names, recurrence path helpers |
| `tests/helpers/failure_dashboard_report.py` | Removed inline path definitions and path helpers; imports + compatibility re-exports |
| `tests/helpers/replay_bug_recurrence.py` | Replaced 3 lazy imports from report hub with top-level import from path registry |
| `tests/test_failure_dashboard_paths.py` | **Added** — path authority, compatibility alias, helper, cycle, and writer smoke tests |

## Path Authority Moved

| Artifact Family | Old Owner | New Owner | Compatibility Preserved? |
|---|---|---|---|
| Failure dashboard latest | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes — re-exported from report hub |
| Protected replay failure report | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Rerun drift scorecard (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Long-session stability scorecard (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Owner drift longitudinal (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Owner drift hotspots (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Owner drift trends (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Owner drift risk (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Bug recurrence history (JSON/MD) | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Bug recurrence event log | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Session diagnostic event log | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Recurrence trajectory history | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes — also consumed directly by `replay_bug_recurrence.py` |
| Opt-in env gate names | `failure_dashboard_report.py` | `failure_dashboard_paths.py` | Yes |
| Recurrence path derivation helpers | `failure_dashboard_report.py` (private) | `failure_dashboard_paths.py` (public helpers) | Yes — report hub uses transitional private aliases |

Recurrence governance doc paths (`RECURRENCE_*_DOC_PATH`) remain owned by `replay_bug_recurrence.py` (unchanged).

## Compatibility Surface

Re-exports preserved on `tests/helpers/failure_dashboard_report.py` (same public names, same objects):

- `FAILURE_DASHBOARD_ENV_VAR`
- `RERUN_DRIFT_SCORECARD_ENV_VAR`
- `LONG_SESSION_STABILITY_SCORECARD_ENV_VAR`
- `FAILURE_DASHBOARD_LATEST_PATH`
- `PROTECTED_REPLAY_FAILURE_REPORT_PATH`
- `RERUN_DRIFT_SCORECARD_JSON_PATH`
- `RERUN_DRIFT_SCORECARD_MARKDOWN_PATH`
- `LONG_SESSION_STABILITY_SCORECARD_JSON_PATH`
- `LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH`
- `OWNER_DRIFT_LONGITUDINAL_JSON_PATH`
- `OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH`
- `OWNER_DRIFT_HOTSPOTS_JSON_PATH`
- `OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH`
- `OWNER_DRIFT_TRENDS_JSON_PATH`
- `OWNER_DRIFT_TRENDS_MARKDOWN_PATH`
- `OWNER_DRIFT_RISK_JSON_PATH`
- `OWNER_DRIFT_RISK_MARKDOWN_PATH`
- `BUG_RECURRENCE_HISTORY_JSON_PATH`
- `BUG_RECURRENCE_HISTORY_MARKDOWN_PATH`
- `BUG_RECURRENCE_EVENT_LOG_JSON_PATH`
- `BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH`
- `RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH`

Transitional internal aliases in the report hub (not part of public contract):

- `_bug_recurrence_event_log_path` → `failure_dashboard_paths.bug_recurrence_event_log_path`
- `_bug_recurrence_session_diagnostic_event_log_path` → `failure_dashboard_paths.bug_recurrence_session_diagnostic_event_log_path`
- `_bug_recurrence_trajectory_history_path` → `failure_dashboard_paths.bug_recurrence_trajectory_history_path`

All 21 existing import sites can continue importing path constants from `failure_dashboard_report.py` unchanged.

## Import Cycle Result

**Removed.**

Before:

```
failure_dashboard_report.py → replay_bug_recurrence.py → failure_dashboard_report.py (lazy path import)
```

After:

```
failure_dashboard_report.py → replay_bug_recurrence.py
failure_dashboard_report.py → failure_dashboard_paths.py
replay_bug_recurrence.py → failure_dashboard_paths.py
```

AST verification:

- `replay_bug_recurrence.py` imports `failure_dashboard_report`: **False**
- `replay_bug_recurrence.py` imports `failure_dashboard_paths`: **True**

One-way dependency from report hub to recurrence analytics remains (orchestration unchanged).

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Filenames | **No** |
| Directories | **No** |
| Report formats | **No** |
| Writer behavior | **No** |

Path helper logic was moved verbatim; canonical `Path(...)` string values are identical.

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_paths.py -q --tb=short
# 47 passed

python -m pytest tests/test_failure_dashboard_paths.py tests/test_failure_dashboard_report.py tests/test_failure_classifier.py tests/test_golden_replay_trend.py tests/test_bz_protected_replay_trend_window_2.py tests/test_replay_drift_hotspots.py tests/test_replay_drift_longitudinal.py tests/test_replay_drift_trends.py tests/test_replay_drift_risk.py -q --tb=line
# 288 passed
```

Additional note on requested suite item:

- `tests/test_replay_drift_reports.py` — **not present** in repository; substituted with `tests/test_replay_drift_{hotspots,longitudinal,trends,risk}.py`.

Baseline issue (not addressed in this block):

```text
python -m pytest tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report -q --tb=short
# FAILED — IndexError: empty events list in tmp_path/bug_recurrence_event_log.json
```

This appears **unrelated to path extraction**: `tests/test_failure_dashboard_report.py::test_protected_replay_recurrence_write_routes_ephemeral_tmp_events_to_diagnostic_lane` documents that tmp-path protected recurrence writes route to `bug_recurrence_session_diagnostic_event_log.json`, not the protected event log. The bridge test expects the protected log. No path or helper behavior changed in this block.

Import-cycle check (inline script):

```text
replay_bug_recurrence imports failure_dashboard_report: False
failure_dashboard_report imports replay_bug_recurrence: True
replay_bug_recurrence imports failure_dashboard_paths: True
failure_dashboard_report imports failure_dashboard_paths: True
```

## Follow-up Recommendation

**Proceed to CE2.2 (session collection buffers)** — path registry extraction succeeded with no behavioral drift in the focused validation set.

Optional small follow-ups before CE2.2:

1. Fix or realign `test_protected_golden_assertion_failure_records_canonical_report` to read the session-diagnostic event log when using tmp paths (baseline test issue).
2. Optionally document `failure_dashboard_paths.py` in replay governance contract docs (docs-only; not required for CE2.2).

Diagnostic Concentration Risk impact: **modest reduction** (~100 LOC and cycle removed from hub); largest concentration (recurrence rendering) remains for CE2.3+.
