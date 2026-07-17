# CE6 — Generated Replay Artifact Churn Reduction Summary

## Summary

Introduced an explicit retention/versioning policy for `artifacts/golden_replay/` without deleting tracked evidence or changing replay behavior, report formats, or writer orchestration. Canonical protected replay evidence remains committed; clearly local-regenerable diagnostics are documented and gitignored.

## Artifact Families Reviewed

16 families registered in `tests/helpers/golden_replay_artifact_manifest.py` covering **111 git-tracked files** under `artifacts/golden_replay/` (plus local-only paths excluded from version control).

| Family | Retention class | Commit policy |
|---|---|---|
| `protected_replay_failure_report` | canonical_versioned_evidence | commit |
| `protected_replay_observation_corpus` | canonical_versioned_evidence | commit |
| `bug_recurrence_history` | canonical_versioned_evidence | commit (intentional refresh) |
| `bug_recurrence_legacy_baseline` | historical_baseline | baseline_freeze |
| `owner_drift_longitudinal` | redundant_paired_output | paired_mirror |
| `owner_drift_hotspots` | redundant_paired_output | paired_mirror |
| `owner_drift_trends` | redundant_paired_output | paired_mirror |
| `owner_drift_risk` | redundant_paired_output | paired_mirror |
| `rerun_drift_scorecard` | reproducible_local_output | local_only |
| `long_session_stability_scorecard` | reproducible_local_output | local_only |
| `replay_maintenance_metrics` | reproducible_local_output | local_only |
| `protected_replay_trend_window_bw` | historical_baseline | baseline_freeze |
| `protected_replay_trend_window_bz` | canonical_versioned_evidence | commit |
| `fallback_governance_reports` | canonical_versioned_evidence | commit |
| `fallback_incidence_baselines` | historical_baseline | baseline_freeze |
| `projection_governance_reports` | canonical_versioned_evidence | commit |

## Retention Policy

### Commit and review intentionally

- Protected replay evidence: `replay_failure_report.md`, `replay_failure_corpus_observations.md`
- BZ trend window outputs: `trend_window_2/`
- Fallback/projection governance report families
- Bug recurrence operational snapshots (when governance state intentionally changes)

### Baseline freeze (rare updates only)

- BW trend window inputs: `trend_window/` (immutable comparison lane)
- Explicit baselines: `bv1b_fallback_incidence_report.baseline.json`, `bug_recurrence_event_log.legacy.json`

### Paired mirror (JSON source + Markdown mirror)

- Owner drift families (`owner_drift_*`) and other JSON/MD pairs written atomically by dashboard writers
- Policy: refresh JSON and Markdown together in focused commits; JSON is machine source

### Local only (regenerate; do not commit)

- `replay_maintenance_metrics.json/md` — `python tools/replay_maintenance_metrics.py`
- `rerun_drift_scorecard.json/md` — `ASHEN_WRITE_RERUN_DRIFT_SCORECARD=1 pytest`
- `long_session_stability_scorecard.json/md` — `ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD=1 pytest`

## Files Changed

| File | Change |
|---|---|
| `artifacts/golden_replay/README.md` | **Added** — directory overview and quick retention policy |
| `artifacts/golden_replay/artifact_manifest.md` | **Added** — human-readable family inventory and churn watch list |
| `tests/helpers/golden_replay_artifact_manifest.py` | **Added** — machine registry, retention classes, path groupings |
| `tests/test_golden_replay_artifact_manifest.py` | **Added** — manifest/doc/gitignore contract validation |
| `.gitignore` | **Updated** — ignore local-regenerable golden replay diagnostics |

No artifact files deleted. No report writer behavior changed.

## Ignore Changes

Added to `.gitignore` (paths were **not** previously tracked):

```
artifacts/golden_replay/replay_maintenance_metrics.json
artifacts/golden_replay/replay_maintenance_metrics.md
artifacts/golden_replay/rerun_drift_scorecard.json
artifacts/golden_replay/rerun_drift_scorecard.md
artifacts/golden_replay/long_session_stability_scorecard.json
artifacts/golden_replay/long_session_stability_scorecard.md
```

**Not gitignored (preserved auditability):**

- `replay_failure_report.md`
- `replay_failure_corpus_observations.md`
- `trend_window/` and `trend_window_2/`
- Committed recurrence/drift/fallback/projection snapshots

## Risks Avoided

- Did **not** delete or untrack canonical protected replay evidence
- Did **not** change report formats or pytest artifact writer logic
- Did **not** gitignore currently tracked high-churn families (would require explicit `git rm --cached` closeout)
- Did **not** collapse JSON/Markdown pairs (preserves human audit mirrors)
- Documented BW/BZ trend-window immutability boundaries from existing governance

## Validation Results

```text
python -m pytest tests/test_golden_replay_artifact_manifest.py \
  tests/test_failure_dashboard_paths.py \
  tests/test_replay_maintenance_metrics.py -q --tb=short

# 75 passed
```

Contract checks include:

- Every manifest family appears in `artifact_manifest.md`
- All `failure_dashboard_paths.py` golden-replay canonical paths are registered
- Local-only families match gitignore entries
- Protected canonical evidence paths are not classified as local-only
- Family IDs are unique

## Remaining Artifact Churn Concerns

| Concern | Assessment |
|---|---|
| Tracked recurrence/drift paired outputs | **High churn** — `bug_recurrence_*`, `owner_drift_*` still committed; policy now says refresh intentionally, but local pytest runs can still dirty working tree |
| `audits/failure_dashboard_latest.md` | **Moderate** — opt-in dashboard output, still **tracked**; not gitignored (ignore would not affect tracked file without untracking) |
| `trend_window/_storage/` bulk | **Low churn, high size** — frozen BW baseline fixtures; commit rarely by design |
| Paired JSON/Markdown duplication | **Structural** — auditability tradeoff; future CE could commit JSON-only for operational snapshots after operator workflow change |
| Untracked `replay_maintenance_metrics.*` | **Resolved** — now gitignored with documented local-only policy |

Recommended next step (out of CE6 scope): a focused governance closeout to stop tracking operational recurrence/drift snapshots unless a refresh commit is intended, while keeping protected failure report + trend baselines committed.
