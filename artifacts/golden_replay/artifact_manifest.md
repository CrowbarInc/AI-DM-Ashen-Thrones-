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
| `projection_coverage_report` | canonical_versioned_evidence | `tests.helpers.golden_replay_projection` | commit | `python tools/fallback_projection_coverage_audit.py` |
| `projection_gap_reality_report` | canonical_versioned_evidence | `tests.helpers.golden_replay_projection` | commit | `python tools/fallback_projection_gap_reality_audit.py` |
| `projection_drift_watch_report` | canonical_versioned_evidence | `tests.helpers.golden_replay_projection` | commit | `python tools/projection_drift_watch.py` |
| `failure_dashboard_latest` | temporary_session_output | `tests.helpers.failure_dashboard_report` | commit (high-churn) | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` |

## CF6 artifact importance (projection governance)

Machine authority: `tests/helpers/golden_replay_artifact_manifest.py` (`importance`, `generator`, `ci_required`).

| Importance | Meaning | Review on semantic projection change? |
|---|---|---|
| `acceptance-critical` | CI-gated acceptance contract | **Yes** — manifest field-path section only |
| `governance` | Frozen or intentional governance evidence | Only when governance lane explicitly changes |
| `diagnostic` | Operational failure/recurrence/drift snapshots | No — refresh deliberately |
| `advisory` | Read-only audit scans and portfolio reports | No — optional closeout refresh |
| `developer_convenience` | Local-only regenerable diagnostics | Never commit |
| `ephemeral` | Session scratch / CI upload | Never commit |

**Acceptance-critical generated artifacts (CI):**

- `docs/testing/protected_replay_manifest.md` generated field-path section — `python tools/refresh_protected_replay_manifest.py --check`

**Not acceptance-critical:** pytest golden replay assertions (no committed artifact), advisory projection reports, diagnostic dashboard outputs, trend-window baselines (governance lane).

## Regeneration boundaries (CF6)

| Bundle | Artifacts | Trigger | Intentional? |
|---|---|---|---|
| CI manifest check | protected replay manifest generated section | registry / drift-bucket edit | Yes |
| BV3F/BV3B `refresh_projection_artifacts()` | gap reality JSON, drift watch JSON+MD | corpus refresh closeout | Yes — **excludes** coverage report |
| Failure dashboard cascade | failure report, bug recurrence, owner drift families | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` | Yes — coupled diagnostic bundle |
| Coverage audit (standalone) | `projection_coverage_report.json` | registry or shape catalog edit | Yes — manual / closeout only |
| Trend window tool | `trend_window/` or `trend_window_2/` tree | explicit BW/BZ closeout | Yes — not ordinary projection edits |

**Churn reduction:** semantic projection changes should require manifest refresh (if field registry changes) and pytest assertion updates — not automatic refresh of advisory scans or diagnostic snapshots.

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
