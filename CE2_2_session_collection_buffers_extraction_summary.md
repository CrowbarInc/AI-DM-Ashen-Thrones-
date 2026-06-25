# CE2.2 — Session Collection Buffers Extraction Summary

## Summary

Extracted mutable pytest-session collection buffers from `tests/helpers/failure_dashboard_report.py` into `tests/helpers/failure_dashboard_session.py`. The report hub now re-exports session record/clear/access APIs for backward compatibility and delegates buffer mutation to the session module.

`record_protected_replay_assertion_failure` remains in the report hub (classification + enrichment logic) but appends to session buffers via internal session helpers.

No artifact paths, report formats, writer orchestration, or ordering/reset semantics were changed.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/failure_dashboard_session.py` | **Added** — six in-memory buffers, record/clear/access helpers, `clear_all_session_buffers` |
| `tests/helpers/failure_dashboard_report.py` | Removed module-level `_RECORDED_*` lists and inline record/clear implementations; imports + re-exports from session module |
| `tests/test_failure_dashboard_session.py` | **Added** — ordering, reset scope, compatibility, writer consumption, import-direction tests |

## Session State Moved

| Buffer / Collection | Old Owner | New Owner | Compatibility Preserved? |
|---|---|---|---|
| Failure dashboard rows | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes — re-exported |
| Runtime lineage events (dashboard lane) | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes |
| Protected replay failure rows | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes |
| Protected replay runtime lineage events | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes |
| Rerun drift scorecards | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes |
| Long-session stability scorecards | `failure_dashboard_report.py` | `failure_dashboard_session.py` | Yes |
| `record_protected_replay_assertion_failure` orchestration | `failure_dashboard_report.py` | **Unchanged location** (uses session append helpers) | Yes |

## Compatibility Surface

Re-exports preserved on `tests/helpers/failure_dashboard_report.py`:

- `record_failure_dashboard_rows`
- `record_runtime_lineage_events`
- `record_rerun_drift_scorecard`
- `record_long_session_stability_scorecard`
- `clear_recorded_failure_dashboard_rows`
- `clear_recorded_protected_replay_failures`
- `clear_recorded_rerun_drift_scorecards`
- `clear_recorded_long_session_stability_scorecards`
- `recorded_failure_dashboard_rows`
- `recorded_runtime_lineage_events`
- `recorded_protected_replay_failure_rows`
- `recorded_protected_replay_runtime_lineage_events`
- `recorded_rerun_drift_scorecards`
- `recorded_long_session_stability_scorecards`

Still implemented in report hub (not moved):

- `record_protected_replay_assertion_failure` — delegates buffer writes to `_append_protected_replay_failure_row` / `_extend_protected_replay_runtime_lineage_events`
- `clear_requested_artifact_recordings` — env-gated clears calling session re-exports

New session-only helpers (internal to report hub unless imported directly):

- `append_protected_replay_failure_row`
- `extend_protected_replay_runtime_lineage_events`
- `clear_all_session_buffers` (test utility)

No import-site changes required for `tests/conftest.py`, `tests/helpers/golden_replay.py`, or existing tests.

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Artifact filenames | **No** |
| Artifact directories | **No** |
| Report formats | **No** |
| Writer behavior | **No** |
| Record ordering | **No** |
| Reset behavior | **No** |

Buffer semantics (dict copies on record, lineage normalization cap `[:16]`, scorecard Mapping guard) moved verbatim.

## Import Direction

| Relationship | Present? |
|---|---|
| `failure_dashboard_session` imports `failure_dashboard_report` | **No** |
| `failure_dashboard_report` imports `failure_dashboard_session` | **Yes** |
| New import cycle introduced | **No** |

`failure_dashboard_session.py` imports only `game.runtime_lineage_telemetry.normalize_runtime_lineage_events` for lineage normalization at collection time.

Existing acyclic chain preserved:

```
failure_dashboard_report → failure_dashboard_session
failure_dashboard_report → replay_bug_recurrence → failure_dashboard_paths
```

## Tests Run

```text
python -m pytest tests/test_failure_dashboard_session.py tests/test_failure_dashboard_paths.py tests/test_failure_dashboard_report.py tests/test_failure_classifier.py tests/test_golden_replay_protected_bridge.py tests/test_golden_replay_trend.py tests/test_bz_protected_replay_trend_window_2.py tests/test_replay_drift_hotspots.py tests/test_replay_drift_longitudinal.py tests/test_replay_drift_trends.py tests/test_replay_drift_risk.py -q --tb=line

# 298 passed, 1 failed (baseline)
```

## Known Baseline Issues

**Unchanged from CE2.1** — not caused by this block:

```text
tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report
# IndexError: empty events list in tmp_path/bug_recurrence_event_log.json
```

Tmp-path protected recurrence writes route to `bug_recurrence_session_diagnostic_event_log.json` per `tests/test_failure_dashboard_report.py::test_protected_replay_recurrence_write_routes_ephemeral_tmp_events_to_diagnostic_lane`. The bridge test still expects the protected event log.

## Follow-up Recommendation

**Proceed to CE2.3 — recurrence module extraction** (markdown renderers + `write_bug_recurrence_history_artifacts` orchestration). Session buffers are now isolated; the largest remaining hub concentration is recurrence rendering (~54% of function LOC per CE2 recon).

Optional parallel cleanup (not blocking CE2.3):

- Fix protected-bridge test to read session-diagnostic event log under tmp paths, or assert lane routing explicitly.

Diagnostic Concentration Risk impact: **modest reduction** (~115 LOC and mutable state removed from hub); writers/renderers unchanged.
