# CE3 — Replay Bug Recurrence Decomposition Summary

## Summary

Decomposed the 10,466-line replay bug recurrence monolith into four focused helper modules plus a narrow public facade. Implementation was moved verbatim in source order within each module to preserve recurrence calculations, JSON schemas, markdown output, artifact paths, event ordering, and deterministic behavior.

The facade (`replay_bug_recurrence.py`) is now **472 LOC** with re-exports only. Executable ownership is split across events (**986 LOC**), history analytics (**3,066 LOC**), program statistics (**4,337 LOC**), and serialization (**2,117 LOC**).

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/replay_bug_recurrence.py` | Replaced monolith with CE3 facade and `__all__` re-exports |
| `tests/helpers/replay_bug_recurrence_events.py` | **Added** — keys, rows, event log persistence, history aggregation |
| `tests/helpers/replay_bug_recurrence_history.py` | **Added** — trend/forecast/portfolio/remediation/governance/lifecycle analytics |
| `tests/helpers/replay_bug_recurrence_statistics.py` | **Added** — effectiveness, maturity, roadmap, completion, graduation, trajectory |
| `tests/helpers/replay_bug_recurrence_serialization.py` | **Added** — confidence calibration, outcome validation, markdown renderers |
| `tools/ce3_decompose_replay_bug_recurrence.py` | **Added** — reproducible line-range extraction script |
| `tests/test_replay_bug_recurrence_decomposition.py` | **Added** — compatibility, import-direction, calculation, serialization tests |

Local reference only (not required for runtime): `tests/helpers/replay_bug_recurrence_monolith.py.bak`

## Responsibilities Extracted

| Responsibility | Old Owner | New Owner | Compatibility |
|---|---|---|---|
| Recurrence key derivation and row projection | `replay_bug_recurrence.py` | `replay_bug_recurrence_events.py` | Facade re-export |
| Event log load/write/append and commit-worthiness | `replay_bug_recurrence.py` | `replay_bug_recurrence_events.py` | Facade re-export |
| History aggregation and regression recurrence rate | `replay_bug_recurrence.py` | `replay_bug_recurrence_events.py` | Facade re-export |
| Timeline/trend/forecast/portfolio analytics | `replay_bug_recurrence.py` | `replay_bug_recurrence_history.py` | Facade re-export |
| Remediation, ROI, governance, lifecycle enrichment | `replay_bug_recurrence.py` | `replay_bug_recurrence_history.py` | Facade re-export |
| Program effectiveness, maturity, roadmap, completion | `replay_bug_recurrence.py` | `replay_bug_recurrence_statistics.py` | Facade re-export |
| Graduation audit and trajectory snapshot history | `replay_bug_recurrence.py` | `replay_bug_recurrence_statistics.py` | Facade re-export |
| Confidence calibration and outcome validation | `replay_bug_recurrence.py` | `replay_bug_recurrence_serialization.py` | Facade re-export |
| Markdown report renderers (BQ graduation/confidence/outcome) | `replay_bug_recurrence.py` | `replay_bug_recurrence_serialization.py` | Facade re-export |

### CE3 Responsibility Map (facade header)

```
# - replay_bug_recurrence_events: keys, rows, event log persistence, history aggregation
# - replay_bug_recurrence_history: trend/forecast/portfolio/remediation/governance/lifecycle analytics
# - replay_bug_recurrence_statistics: effectiveness, maturity, roadmap, completion, graduation
# - replay_bug_recurrence_serialization: confidence calibration, outcome validation, markdown renderers
```

## Compatibility Preserved

- All existing imports from `tests.helpers.replay_bug_recurrence` continue to work via facade re-exports.
- No import-site changes required in `failure_dashboard_recurrence.py`, `replay_drift_reports.py`, tools, or tests.
- Cross-module private helpers (`_regression_rate_value`, `_parse_iso_timestamp`, `_clamp_maturity_score`, `_maturity_volume_factor`) are explicitly imported where star-import visibility would otherwise hide them.

## LOC / Function Comparison

| Module | LOC | Top-level defs |
|---|---:|---:|
| Pre-CE3 monolith | 10,466 | 222 |
| `replay_bug_recurrence.py` (facade) | 472 | 0 |
| `replay_bug_recurrence_events.py` | 986 | 40 |
| `replay_bug_recurrence_history.py` | 3,066 | 73 |
| `replay_bug_recurrence_statistics.py` | 4,337 | 77 |
| `replay_bug_recurrence_serialization.py` | 2,117 | 32 |
| **Focused modules total** | **10,506** | **222** |

Facade LOC reduction vs monolith: **95.5%** (10,466 → 472).

## Dependency Graph

```
replay_bug_recurrence.py (facade)
  → replay_bug_recurrence_events.py
  → replay_bug_recurrence_history.py
  → replay_bug_recurrence_statistics.py
  → replay_bug_recurrence_serialization.py

replay_bug_recurrence_events.py
  → failure_dashboard_paths.py
  → replay_drift_taxonomy.py

replay_bug_recurrence_history.py
  → replay_bug_recurrence_events.py

replay_bug_recurrence_statistics.py
  → replay_bug_recurrence_events.py
  → replay_bug_recurrence_history.py

replay_bug_recurrence_serialization.py
  → replay_bug_recurrence_events.py
  → replay_bug_recurrence_history.py
  → replay_bug_recurrence_statistics.py

failure_dashboard_recurrence.py
  → replay_bug_recurrence.py (unchanged public entry)

replay_drift_reports.py
  → replay_bug_recurrence.py (unchanged public entry)
```

**No reverse imports.** **No new cycles.** Focused modules do not import `failure_dashboard_report`, `failure_dashboard_recurrence`, or `failure_dashboard_session`.

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Recurrence calculations | **No** |
| Recurrence classifications | **No** |
| JSON schemas | **No** |
| Markdown output | **No** |
| Artifact filenames | **No** |
| Artifact directories | **No** |
| Event ordering | **No** |
| Deterministic behavior | **No** |

## Validation Results

```text
python -m pytest tests/test_replay_bug_class_recurrence.py \
  tests/test_failure_dashboard_recurrence.py \
  tests/test_failure_dashboard_report.py \
  tests/test_replay_maintenance_metrics.py \
  tests/test_recurrence_trajectory_history.py \
  tests/test_replay_bug_recurrence_decomposition.py \
  tests/test_migrate_bug_recurrence_event_log.py \
  tests/test_expand_protected_replay_observations.py -q --tb=no

# 255 passed
```

## Known Baseline Issues

**Unchanged** — not caused by CE3:

```text
python -m pytest tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report -q --tb=line

# FAILED — IndexError: list index out of range (pre-existing protected-bridge baseline)
```

## Remaining Concentration Assessment

| Area | Assessment |
|---|---|
| `replay_bug_recurrence.py` | **Low** — facade-only; suitable public entry point |
| `replay_bug_recurrence_events.py` | **Moderate** — cohesive event/history foundation (~986 LOC) |
| `replay_bug_recurrence_history.py` | **Elevated** — broad analytics stack (~3,066 LOC); candidate for a future CE pass splitting forecast/portfolio vs trend/governance |
| `replay_bug_recurrence_statistics.py` | **Elevated** — largest module (~4,337 LOC); maturity/roadmap/completion/graduation could be split if maintenance touch rises |
| `replay_bug_recurrence_serialization.py` | **Moderate** — report rendering and late-stage audits (~2,117 LOC) |

Overall replay maintenance cost for bug recurrence is improved: the primary import surface is narrow, event/history foundations are isolated from late-stage graduation/outcome reporting, and layering constraints (`failure_dashboard_paths`, `failure_dashboard_session`, `failure_dashboard_recurrence`) remain intact.
