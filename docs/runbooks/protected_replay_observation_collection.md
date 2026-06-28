# Protected Replay Observation Collection Runbook

**Cycle:** CO100  
**Scope:** Operational documentation only. Describes the **existing** protected replay observation process. No new operational requirements, metrics, thresholds, or taxonomy changes.

**Goal:** Repeatable observation workflow that produces recurrence evidence consistent with the [CO99 operational graduation baseline](../audits/BQ16_recurrence_graduation_audit.md#operational-graduation-baseline-co99).

---

## Authority chain

| Role | Governing document | What it owns |
|---|---|---|
| **Taxonomy authority** | [`CG_recurrence_taxonomy_registry.md`](../audits/CG_recurrence_taxonomy_registry.md) | Recurrence vocabulary (identity key, event source, trend/governance/lifecycle statuses). **Closed** — do not extend for graduation. |
| **Operational authority** | This runbook + [`BQ36_recurrence_write_path_audit.md`](../audits/BQ36_recurrence_write_path_audit.md) | How protected replay failures become commit-worthy recurrence events and artifacts. |
| **Graduation authority** | [`BQ16_recurrence_graduation_audit.md`](../audits/BQ16_recurrence_graduation_audit.md) (audit builder) + [`BQC4_final_graduation_decision.md`](../audits/BQC4_final_graduation_decision.md) (final recommendation) | Whether recurrence operational graduation criteria are met. **Active — not graduated.** |

**CO99 baseline:** Evidence requirements and remaining blockers are defined in BQ16 §Operational graduation baseline (CO99). This runbook operationalizes collection only; it does not redefine graduation thresholds.

---

## Observation lifecycle

Each stage below maps to existing code paths. Follow in order when a protected replay failure occurs.

### 1. Protected replay executed

| Item | Detail |
|---|---|
| **Command** | `python -m pytest -m golden_replay -q --tb=short` |
| **CI** | `.github/workflows/convergence-checks.yml` runs the same marker |
| **Scenario catalog** | [`docs/testing/protected_replay_manifest.md`](../testing/protected_replay_manifest.md) |
| **Assertion path** | `tests/helpers/golden_replay.py` → `record_protected_replay_assertion_failure()` on assertion failure when `report_scenario_id` is set |

Protected replay runs are **report-only** (`RECURRENCE_REPORT_ONLY`, `RECURRENCE_ADVISORY_ONLY`). Failures do not gate production emission.

### 2. Recurrence event observed

On assertion failure, the runner:

1. Builds failure classification rows via `build_failure_dashboard_rows()` / `classify_replay_failure`.
2. Enriches rows with `scenario_id`, `test_node_id`, `failed_invariant`, source path, branch, and turn metadata.
3. Appends rows to the session-scoped protected failure buffer (`record_protected_replay_assertion_failure`).

Each row carries the fields consumed by recurrence identity: `owner_drift_bucket`, `category`, `field_path`, `investigate_first` (see CG-4 §Recurrence identity key).

### 3. Event recorded

At `pytest_sessionfinish` when `exitstatus != 0`:

```
tests/conftest.py
  → write_requested_dashboard_artifacts()
    → write_protected_replay_failure_report_if_present()
      → write_owner_drift_risk_artifacts(..., recurrence_event_metadata=protected_replay_recurrence_event_metadata(...))
        → write_bug_recurrence_history_artifacts(rows, recurrence_event_metadata=...)
```

`protected_replay_recurrence_event_metadata()` sets `event_source=protected_replay_failure` and `artifact_source` to the report path being written.

### 4. Evidence preserved

The protected failure cascade writes (when failures were recorded):

| Artifact | Path | Purpose |
|---|---|---|
| Protected failure report | `artifacts/golden_replay/replay_failure_report.md` | Human-readable classification table; backfill input |
| Owner drift hotspots | `artifacts/golden_replay/owner_drift_hotspots.{json,md}` | Triage by owner drift bucket |
| Owner drift risk | `artifacts/golden_replay/owner_drift_risk.{json,md}` | Risk summary; triggers recurrence write |
| Protected event log | `artifacts/golden_replay/bug_recurrence_event_log.json` | Commit-worthy recurrence events only |
| Session diagnostic log | `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json` | Excluded events with routing reasons |
| Recurrence history | `artifacts/golden_replay/bug_recurrence_history.{json,md}` | Aggregated protected-lane analytics |

CI uploads `replay_failure_report.md` as an external artifact on failure; **commit** the golden-replay paths above when observations should advance graduation evidence.

### 5. Recurrence taxonomy applied

Taxonomy is **not** chosen at observation time by operators. Existing classifiers derive:

- **Identity key:** `build_recurrence_key()` from classification row fields (`replay_bug_recurrence_events.py`).
- **Event source:** `protected_replay_failure` via metadata helper.
- **Summary/trend/governance/lifecycle statuses:** Computed when history artifacts regenerate (`replay_bug_recurrence_history.py`, `replay_bug_recurrence_statistics.py`).

Refer to [`CG_recurrence_taxonomy_registry.md`](../audits/CG_recurrence_taxonomy_registry.md) for vocabulary ownership. Do not add new status values during observation collection.

### 6. Observation committed

Commit-worthiness routing (`is_commit_worthy_recurrence_event()` in `replay_bug_recurrence_events.py`) decides protected vs session-diagnostic lane. **Allow** (protected lane):

- `event_source=protected_replay_failure` with `artifact_source` prefix `artifacts/golden_replay/`
- Backfill rows with `persistence_intent=backfill_protected_replay`

**Disallow** (session diagnostic lane — not dropped):

- `event_source=session`
- Ephemeral paths (`codex_pytest_tmp`, `pytest_tmp`, `/tmp/`)
- Synthetic drift keys (`|unknown|…|unknown`)
- Protected events with null `scenario_id`

Full write-path inventory: [`BQ36_recurrence_write_path_audit.md`](../audits/BQ36_recurrence_write_path_audit.md).

**Manual backfill** (when report exists but event log was not updated in-session):

```bash
python tools/backfill_bug_recurrence_history.py
```

Backfill uses `persistence_intent=backfill_protected_replay` and dedupe keys (`recurrence_backfill_dedupe_key`) for idempotency.

### 7. Trend tracking updated

After protected-lane append, `write_bug_recurrence_history_artifacts()` regenerates timeline, trend summary, forecast, portfolio, governance, lifecycle, and maturity payloads from the **protected event log only**.

Trend buckets use `calculate_protected_replay_regression_recurrence_rate()` (BQ3.6). Session-sourced events do not affect protected trend metrics.

**Trajectory snapshots:** When history is regenerated with `temporal_trajectory_capture=True` (e.g. `tools/capture_recurrence_trajectory_activation.py`), a follow-up snapshot appends to `artifacts/golden_replay/bug_recurrence_trajectory_history.json`. CO99 requires ≥ 2 snapshots for `trajectory_available=true`.

### 8. Graduation evidence accumulated

Regenerated history feeds graduation audit builders:

| Output | Builder | Path |
|---|---|---|
| Graduation audit | `replay_bug_recurrence_statistics.py` | `docs/audits/BQ16_recurrence_graduation_audit.md` |
| Final recommendation | `replay_bug_recurrence_serialization.py` | `docs/audits/BQC4_final_graduation_decision.md` |

Re-run history regeneration (with committed protected event log) after meaningful observation volume changes. Compare against CO99 baseline targets in BQ16 (observation volume, trajectory, confidence, blind spots).

---

## Observation quality requirements

Requirements below reference existing governance. They do **not** introduce new thresholds.

### Required replay artifacts

For an observation to count toward protected graduation evidence:

1. **`artifacts/golden_replay/replay_failure_report.md`** — committed under `artifacts/golden_replay/` (not pytest tmp).
2. **Corresponding protected-lane event** in `bug_recurrence_event_log.json` with matching `artifact_source`.
3. **Non-null `scenario_id`** on the classification row / event.
4. **Regenerated `bug_recurrence_history.json`** reflecting the protected event log (occurs automatically on write).

Optional but useful for triage: owner drift hotspot and risk artifacts from the same write cascade.

### Required recurrence classification

Each commit-worthy event must include classification fields sufficient for `build_recurrence_key()`:

- `owner_drift_bucket` (from `classify_owner_drift_bucket`)
- `category`
- `field_path`
- `investigate_first`

`event_source` must be `protected_replay_failure`. Vocabulary authority: CG-4 registry §Recurrence identity key and §Event source.

### Required supporting evidence

| Evidence | Source |
|---|---|
| Failure invariant | `failed_invariant` on classification row |
| Test reproduction | `test_node_id`; report §Focused failing tests |
| Run provenance | `recorded_at`, `command`, `run_id` in event metadata |
| Drift context | `expected` / `actual` / `replay_tags` in failure table |
| Runtime lineage (when present) | `runtime_lineage_events` appended during recording |

### Invalid observations

Do **not** treat these as graduation evidence:

| Condition | Routing | Reference |
|---|---|---|
| `event_source=session` | Session diagnostic log | BQ36 contamination table |
| Ephemeral `artifact_source` (pytest tmp) | Session diagnostic log | BQ35 §Artifact source distribution |
| Synthetic drift keys with `\|unknown\|` placeholders | Session diagnostic log | BQ36 synthetic drift keys |
| Null `scenario_id` on protected events | Session diagnostic log | `is_commit_worthy_recurrence_event()` |
| Events with no classification row backing | N/A — should not be appended | Failure classifier contract |
| Manually edited event log without matching report row | Integrity violation — discard | Replay integrity below |

### Duplicate handling

| Mechanism | Scope |
|---|---|
| Backfill dedupe | `recurrence_backfill_dedupe_key()` / `existing_backfill_dedupe_keys()` — idempotent re-parse of the same report row |
| Re-run same failure | New event append unless backfill dedupe matches; repeated keys increase `occurrence_count` in history aggregation |
| Session vs protected duplication | Lane routing prevents session events from entering protected log (BQ3.6) |

**Note:** Full `(recurrence_key, scenario_id, run_id)` dedupe guard is a deferred recommendation (BV8 R6), not an current operational requirement.

### Replay integrity expectations

1. **Report ↔ log consistency:** Every protected-lane event should trace to a row in `replay_failure_report.md` (or backfill metadata with `persistence_intent=backfill_protected_replay`).
2. **Artifact path prefix:** Commit-worthy events require `artifact_source` under `artifacts/golden_replay/`.
3. **No manual taxonomy edits:** Do not hand-edit recurrence keys or status vocabularies in committed artifacts.
4. **Advisory-only posture:** Observations are report-only; they do not change replay assertions, production code, or graduation thresholds.
5. **Classifier vocabulary frozen:** Row vocabulary remains `tests/failure_classification_contract.py`; behavior remains `tests/helpers/failure_classifier.py` (BQC4 scope statement).

---

## Failure triage (operator steps)

When protected replay fails:

1. Open `artifacts/golden_replay/replay_failure_report.md`.
2. Use §Failure Locator and §Focused failing tests to reproduce locally.
3. Review §Owner Drift Breakdown and classification table for `category`, `investigate_first`, and drift bucket.
4. Confirm the event landed in `bug_recurrence_event_log.json` (not session diagnostic log) via `commit_worthy` routing in BQ36 policy.
5. If the report was generated in CI but not committed, run backfill after committing the report to golden-replay paths.
6. Regenerate graduation audits when observation volume materially changes (history write or `capture_recurrence_trajectory_activation.py` for trajectory).

Session-only diagnostics (`--write-rerun-drift-scorecard`, `--write-failure-dashboard`) produce **session** recurrence events — useful for dev inspection, **not** graduation evidence.

---

## Cross-references

| Document | Relationship |
|---|---|
| [`BQ16_recurrence_graduation_audit.md`](../audits/BQ16_recurrence_graduation_audit.md) | Graduation authority; CO99 evidence targets |
| [`BQ36_recurrence_write_path_audit.md`](../audits/BQ36_recurrence_write_path_audit.md) | Write-path inventory; commit-worthiness policy |
| [`BQC4_final_graduation_decision.md`](../audits/BQC4_final_graduation_decision.md) | Final graduation recommendation (verdict C — operationally immature) |
| [`CG_recurrence_taxonomy_registry.md`](../audits/CG_recurrence_taxonomy_registry.md) | Taxonomy authority (closed) |
| [`BQ35_recurrence_event_source_audit.md`](../audits/BQ35_recurrence_event_source_audit.md) | Historical source contamination analysis |
| [`BQ_recurrence_history_discovery.md`](../audits/BQ_recurrence_history_discovery.md) | Recording vs emission architecture |
| [`docs/testing/protected_replay_manifest.md`](../testing/protected_replay_manifest.md) | Scenario catalog and reproduction commands |

---

## CO100 handoff

This runbook is the authoritative operator guide for protected replay observation collection. Graduation advances through **evidence accumulation** per CO99 — not additional taxonomy or classifier implementation.
