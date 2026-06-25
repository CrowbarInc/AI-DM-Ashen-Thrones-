# CE1 — Replay Maintenance Metrics Summary

## Summary

Created a read-only replay maintenance concentration metrics pipeline at `tools/replay_maintenance_metrics.py`. The tool quantifies replay helper/test ownership, import fan-in/fan-out, git touch activity, and concentration indicators, emitting deterministic JSON and Markdown reports under `artifacts/golden_replay/`.

## Files Changed

| File | Change |
|---|---|
| `tools/replay_maintenance_metrics.py` | **Added** — read-only metrics collector and report generator |
| `tests/test_replay_maintenance_metrics.py` | **Added** — schema, CLI, and markdown/json generation tests |
| `artifacts/golden_replay/replay_maintenance_metrics.json` | **Generated** — baseline metrics snapshot |
| `artifacts/golden_replay/replay_maintenance_metrics.md` | **Generated** — human-readable metrics report |

## Metrics Produced

| Category | Description |
|---|---|
| Ownership totals | LOC/functions/file counts for helpers, tests, artifact modules, compatibility facade |
| Top 20 rankings | By LOC, functions, and importer count |
| Dependency concentration | Fan-in/fan-out for nine target replay modules |
| Concentration indicators | Largest file/helper/test share, average helper/test size |
| Touch concentration | Git commits touching replay ownership files (30/60/90 days) |
| Maintenance risk assessment | Heuristic signals from concentration + churn |

## Sample Output (2026-06-24 baseline)

**Executive summary**

| Metric | Value |
|---|---:|
| Replay files analyzed | 80 |
| Replay total LOC | 47,022 |
| Replay helper LOC | 24,370 |
| Replay test LOC | 16,001 |
| Artifact module LOC | 2,910 |
| Compatibility facade LOC | 723 |

**Import concentration (target modules)**

| Module | Fan-In | Fan-Out |
|---|---:|---:|
| `tests.helpers.failure_dashboard_report` | 27 | 11 |
| `tests.helpers.golden_replay_projection` | 17 | 7 |
| `tests.helpers.golden_replay` | 10 | 13 |
| `tests.helpers.failure_dashboard_paths` | 10 | 0 |
| `tests.helpers.failure_dashboard_session` | 6 | 1 |
| `tests.helpers.protected_replay_registry` | 6 | 0 |
| `tests.helpers.failure_dashboard_drift` | 4 | 4 |
| `tests.helpers.failure_dashboard_recurrence` | 3 | 3 |
| `tests.helpers.failure_dashboard_stability` | 3 | 4 |

**Concentration indicators**

| Indicator | Value |
|---|---:|
| Largest file share | 22.26% (`replay_bug_recurrence.py`) |
| Largest helper share | 42.95% (`replay_bug_recurrence.py`) |
| Largest test share | 19.63% (`test_replay_bug_class_recurrence.py`) |
| Average replay helper LOC | 974.8 |
| Average replay test LOC | 400.0 |

**Maintenance risk (baseline snapshot)**

- Risk level: `elevated`
- Report hub fan-in: 27
- Signals: single-file LOC concentration, helper concentration, high report-hub fan-in, active 30-day churn

## Validation Results

```text
python -m pytest tests/test_replay_maintenance_metrics.py -rA --tb=short

# 6 passed
```

```text
python tools/replay_maintenance_metrics.py --generated-at "2026-06-24T00:00:00Z"

# Wrote artifacts/golden_replay/replay_maintenance_metrics.json
# Wrote artifacts/golden_replay/replay_maintenance_metrics.md
```

## Recommendations for Future Monitoring

1. **Run after each CE cycle** — regenerate metrics with a fixed `--generated-at` timestamp in CI or release notes to compare concentration deltas.
2. **Track report hub fan-in** — target downward trend as compatibility surface shrinks; current baseline is 27 importers on `failure_dashboard_report`.
3. **Watch `replay_bug_recurrence.py` share** — largest helper at ~43% of helper LOC; future decomposition candidates should reflect in largest-helper-share metric.
4. **Use touch concentration** — files with high 30-day touches plus high fan-in are maintenance hotspots; prioritize reviews there.
5. **Commit baseline JSON** — store periodic snapshots (or diff against prior) to quantify Replay Maintenance Cost over time.

## Tool Usage

```bash
python tools/replay_maintenance_metrics.py
python tools/replay_maintenance_metrics.py --generated-at "2026-06-24T00:00:00Z"
python tools/replay_maintenance_metrics.py --json-out path/to/metrics.json --markdown-out path/to/metrics.md
```

The tool performs read-only analysis except for writing the requested report artifacts.
