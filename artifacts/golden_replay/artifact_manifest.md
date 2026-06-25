# Golden Replay Artifact Manifest

Lightweight retention index for `artifacts/golden_replay/`. Machine authority:
`tests/helpers/golden_replay_artifact_manifest.py`.

## Retention classes

| Class | Meaning |
|---|---|
| `canonical_versioned_evidence` | Commit-worthy governance/acceptance evidence |
| `historical_baseline` | Frozen comparison inputs; update only with explicit closeout |
| `redundant_paired_output` | JSON source + Markdown mirror written together |
| `reproducible_local_output` | Regenerate locally; **do not commit** (gitignored) |
| `temporary_session_output` | Ephemeral pytest/session scratch (see repo `.gitignore`) |

## Commit policies

| Policy | Action |
|---|---|
| `commit` | Track in git; update intentionally |
| `baseline_freeze` | Track in git; treat as immutable baseline |
| `paired_mirror` | Track JSON+MD together when refreshing operational snapshots |
| `local_only` | Regenerate locally; excluded from version control |

## Artifact families

| Family | Retention class | Owner module | Commit? | Regenerate |
|---|---|---|---|---|
| `protected_replay_failure_report` | canonical_versioned_evidence | `tests.helpers.failure_dashboard_report` | commit | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `protected_replay_observation_corpus` | canonical_versioned_evidence | `tests.helpers.protected_replay_observation_corpus` | commit | `python tools/expand_protected_replay_observations.py` |
| `bug_recurrence_history` | canonical_versioned_evidence | `tests.helpers.failure_dashboard_recurrence` | commit (intentional refresh) | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `bug_recurrence_legacy_baseline` | historical_baseline | `tests.helpers.replay_bug_recurrence_history` | baseline_freeze | frozen |
| `owner_drift_longitudinal` | redundant_paired_output | `tests.helpers.failure_dashboard_drift` | paired_mirror | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `owner_drift_hotspots` | redundant_paired_output | `tests.helpers.replay_drift_hotspots` | paired_mirror | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `owner_drift_trends` | redundant_paired_output | `tests.helpers.replay_drift_trends` | paired_mirror | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `owner_drift_risk` | redundant_paired_output | `tests.helpers.replay_drift_risk` | paired_mirror | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |
| `rerun_drift_scorecard` | reproducible_local_output | `tests.helpers.failure_dashboard_drift` | **local_only** | `ASHEN_WRITE_RERUN_DRIFT_SCORECARD=1 pytest` |
| `long_session_stability_scorecard` | reproducible_local_output | `tests.helpers.failure_dashboard_stability` | **local_only** | `ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD=1 pytest` |
| `replay_maintenance_metrics` | reproducible_local_output | `tools.replay_maintenance_metrics` | **local_only** | `python tools/replay_maintenance_metrics.py` |
| `protected_replay_trend_window_bw` | historical_baseline | `tests.helpers.protected_replay_trend_movement` | baseline_freeze | BW lane — frozen inputs under `trend_window/` |
| `protected_replay_trend_window_bz` | canonical_versioned_evidence | `tests.helpers.protected_replay_trend_movement` | commit | BZ lane — outputs under `trend_window_2/` |
| `fallback_governance_reports` | canonical_versioned_evidence | `tests.helpers.runtime_lineage_reporting` | commit | report-family specific refresh |
| `fallback_incidence_baselines` | historical_baseline | `tests.helpers.runtime_lineage_reporting` | baseline_freeze | BV baselines incl. `.baseline.json` |
| `projection_governance_reports` | canonical_versioned_evidence | `tests.helpers.golden_replay_projection` | commit | projection governance refresh |

## High-churn families (watch list)

These families create frequent diffs when pytest artifact writers run locally:

- `bug_recurrence_history` — history JSON/MD, event logs, trajectory history
- `owner_drift_hotspots` / `owner_drift_risk` / `owner_drift_trends` / `owner_drift_longitudinal`
- Paired JSON/Markdown outputs where timestamps or row ordering may shift

**Churn reduction policy:** treat these as operational snapshots. Refresh and commit together during governance updates; avoid committing local session output unless the recurrence/drift state change is intentional.

## Local-only paths (gitignored)

```
artifacts/golden_replay/replay_maintenance_metrics.json
artifacts/golden_replay/replay_maintenance_metrics.md
artifacts/golden_replay/rerun_drift_scorecard.json
artifacts/golden_replay/rerun_drift_scorecard.md
artifacts/golden_replay/long_session_stability_scorecard.json
artifacts/golden_replay/long_session_stability_scorecard.md
```

Related opt-in writer output outside this directory: `audits/failure_dashboard_latest.md` (still tracked today; regenerate with `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest`).

## Protected evidence (never gitignore)

- `artifacts/golden_replay/replay_failure_report.md`
- `artifacts/golden_replay/replay_failure_corpus_observations.md`
- `artifacts/golden_replay/trend_window/` (BW baseline inputs)
- `artifacts/golden_replay/trend_window_2/` (BZ governance outputs)

## Related path registry

Dashboard writer canonical paths remain defined in `tests/helpers/failure_dashboard_paths.py` and re-exported from `tests/helpers/failure_dashboard_report.py`.
