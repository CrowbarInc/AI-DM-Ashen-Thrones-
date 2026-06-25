# Golden Replay Artifacts

This directory holds replay diagnostic outputs, governance snapshots, and protected-replay evidence.

**Retention authority:** [`artifact_manifest.md`](artifact_manifest.md) and the machine registry at `tests/helpers/golden_replay_artifact_manifest.py`.

## Quick policy

| Kind | Commit? | Examples |
|---|---|---|
| Protected canonical evidence | Yes — review intentionally | `replay_failure_report.md`, `replay_failure_corpus_observations.md`, `trend_window_2/` |
| Historical baselines | Yes — freeze; rare updates | `trend_window/`, `*.baseline.json`, `bug_recurrence_event_log.legacy.json` |
| Operational paired snapshots | Yes — refresh deliberately | `bug_recurrence_*`, `owner_drift_*` JSON+Markdown pairs |
| Local regenerable outputs | **No** — gitignored | `replay_maintenance_metrics.*`, `rerun_drift_scorecard.*`, `long_session_stability_scorecard.*` |

## Regeneration (common)

```bash
# Failure dashboard bundle (recurrence + owner drift + protected failure report)
ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest

# Opt-in scorecards (local only; not committed)
ASHEN_WRITE_RERUN_DRIFT_SCORECARD=1 pytest
ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD=1 pytest

# CE1 maintenance concentration metrics (local only)
python tools/replay_maintenance_metrics.py
```

## Auditability rules

- Do **not** delete canonical protected replay evidence without an explicit governance closeout.
- Prefer updating committed snapshots in focused refresh commits, not as drive-by pytest side effects.
- JSON is the machine source for paired families; Markdown is a human mirror regenerated alongside JSON.
- Protected observation field paths remain governed by `docs/testing/protected_replay_manifest.md`, not this directory alone.

See [`artifact_manifest.md`](artifact_manifest.md) for the full family inventory.
