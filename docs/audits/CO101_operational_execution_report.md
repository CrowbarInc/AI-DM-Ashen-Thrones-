# CO101 — Protected Replay Observation Execution & Backfill Verification

**Date:** 2026-06-27  
**Scope:** Operational verification only. No governance, taxonomy, classifier, attribution, or production changes.

**Runbook reference:** [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md) (CO100)

---

## Executive summary

The CO100 documented workflow **executes successfully** via existing tooling. Observation expansion and backfill appended commit-worthy events to the protected lane, recurrence history regenerated, trajectory analysis is **active**, and graduation artifacts updated.

**Verdict:** Pipeline operational. Evidence accumulation progressed materially against the CO99/CO100 baseline. Formal graduation remains blocked by **confidence calibration** (`graduation_confidence_ready: false`), not by missing architecture.

---

## 1. Workflow execution

### Commands run

| Step | Command | Result |
|---|---|---|
| Observation expansion | `python tools/expand_protected_replay_observations.py --refresh-corpus` | **Success** — 17 observations, 6 keys |
| Failure report backfill | `python tools/backfill_bug_recurrence_history.py` | **Success** — parsed 1 row, appended 1 event |
| Trajectory snapshot | `python tools/capture_recurrence_trajectory_activation.py --generated-at 2026-06-27T16:00:00Z` | **Failed** — see §Implementation defects |
| Trajectory (workaround) | `write_bug_recurrence_history_artifacts(..., temporal_trajectory_capture=True)` | **Success** — snapshot #7 appended |
| Idempotency check | `expand_protected_replay_observations.py --check` + `backfill_bug_recurrence_history.py --check` | **Success** — no missing rows |

### Corpus artifacts produced

- `artifacts/golden_replay/replay_failure_corpus_observations.md` — refreshed curated corpus (3 scenario rows)
- `artifacts/golden_replay/bug_recurrence_event_log.json` — protected lane updated
- `artifacts/golden_replay/bug_recurrence_history.{json,md}` — regenerated
- `artifacts/golden_replay/recurrence_trajectory_history.json` — snapshot #7 appended
- `docs/audits/BQ16_recurrence_graduation_audit.md` — regenerated
- `docs/audits/BQC4_final_graduation_decision.md` — regenerated

---

## 2. Protected replay routing validation

All **18** protected-lane events pass `is_commit_worthy_recurrence_event()`:

| Check | Result |
|---|---|
| `event_source=protected_replay_failure` | 18 / 18 |
| `artifact_source` under `artifacts/golden_replay/` | 18 / 18 |
| Non-null `scenario_id` | 18 / 18 |
| Classification fields present (`category`, `field_path`, `investigate_first`, `owner_drift_bucket`) | 18 / 18 |
| Session noise excluded | 751 events in session diagnostic log |

**Artifact source distribution (protected lane):**

| Source | Events |
|---|---:|
| `artifacts/golden_replay/replay_failure_report.md` | 15 (mixed path separators) |
| `artifacts/golden_replay/replay_failure_corpus_observations.md` | 3 |

**New corpus scenarios (this run):**

- `wrong_speaker_strict_social_emission`
- `directed_npc_question`
- `sanitizer_scaffold_leakage`

**Routing authority preserved:** Lane routing unchanged; no production or classifier modifications.

---

## 3. Observation quality verification

| Requirement (CO100 runbook) | Status |
|---|---|
| Artifact preservation | **Met** — report + event log + history co-generated |
| Classification present | **Met** — all events carry recurrence key components |
| Authority chain intact | **Met** — taxonomy closed; graduation docs regenerated from builders |
| Duplicate handling | **Met** — `--check` passes; backfill dedupe skips existing rows |
| Invalid observation rejection | **Met** — 751 session-diagnostic events excluded from protected lane |
| History regeneration | **Met** — full analytics stack rebuilt from protected log |

**Duplicate handling:** Re-running expansion and backfill with `--check` confirms no missing parseable rows. Backfill reported `skipped_duplicate_count: 0` on the single new replay_failure_report row.

**Integrity note:** Six protected events use Windows backslash `artifact_source` paths (`artifacts\golden_replay\...`). Commit-worthiness still passes (prefix match). Normalization inconsistency is cosmetic, not a lane-routing failure.

---

## 4. Trajectory status

| Metric | Pre-CO101 (CO99 baseline) | Post-CO101 |
|---|---|---|
| `trajectory_available` | `false` | **`true`** |
| Snapshot count | 1 (BQ-C4) / 6 (trajectory file) | **7** |
| Latest snapshot timestamp | — | `2026-06-27T16:00:00Z` |
| Latest `protected_observation_count` | 11 (snapshot #6) | **18** |

Trajectory change detection is active per BQC4: portfolio risk change `+4.0`, stability change `-41.7`.

---

## 5. Evidence growth (CO99 baseline comparison)

| Metric | CO99 / BQ-C4 baseline | Post-CO101 | Δ |
|---|---|---:|---|
| Protected event count | ~1 commit-worthy (BQ36 audit) / low volume | **18** | +17 |
| Unique recurrence keys | Below confidence threshold | **6** | +5 |
| Protected observations (history) | Low (`recurrence_data_quality` critical) | **18** | Volume target met (≥ 5) |
| Keys target (≥ 3) | Unmet | **Met** (6 keys) | ✓ |
| Graduation readiness score | 52.3 | **94.7** | +42.4 |
| Operational readiness score | 11.7 | **100.0** | +88.3 |
| Overall maturity score | 36.2 | **76.5** | +40.3 |
| Forecast confidence | 0.2 | **1.0** | +0.8 |
| Critical blind spots | 2 | **0** | −2 |
| `trajectory_available` | false | **true** | ✓ |
| BQC4 recommendation | **C** — operationally immature | **B** — one final validation cycle | Improved |
| `graduation_confidence_ready` | false | **false** | Unchanged |
| Calibration score | 84.0 | **55.0** | −29.0 |
| Largest calibration gap | 0.29 | **0.80** | +0.51 |
| Program graduated | false | **false** | Unchanged |

**Interpretation:** Volume and trajectory blockers from CO99 are **resolved operationally**. Remaining graduation blockers are **calibration/overconfidence** (governance health 38.8 vs target 80.0; effectiveness outcomes still `insufficient_evidence` for remediation/lifecycle closure).

---

## 6. Implementation defects discovered

Documented before any fix proposal (per CO101 constraints):

### D1 — `capture_recurrence_trajectory_activation.py` import failure

```
ImportError: cannot import name 'RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH'
from tests.helpers.failure_dashboard_report
```

**Cause:** Constant moved to `replay_bug_recurrence_serialization.py` during module decomposition; tool not updated.

**Workaround used:** Direct call to `write_bug_recurrence_history_artifacts(..., temporal_trajectory_capture=True)` — succeeds and regenerates BQ16/BQC4.

**CO102 recommendation:** One-line import fix in the tool (no behavior change).

### D2 — Graduation audit doc strips CO99 governance context on regeneration

Regenerated `BQ16_recurrence_graduation_audit.md` no longer contains CO99 §Governance context, §Operational graduation baseline, or CO100 cross-references added in CO99/CO100.

**Cause:** `render_recurrence_graduation_audit_report_markdown()` emits metrics-only content; hand-authored governance sections are overwritten.

**CO102 recommendation:** Extend audit renderer with stable governance preamble, or restore via documentation contract lock post-regeneration.

---

## 7. Remaining blockers

| Blocker | Status | Category |
|---|---|---|
| `graduation_confidence_ready` | false | Confidence calibration |
| Calibration score 55.0 < 70.0 | Unmet | Overconfident vs observed effectiveness |
| Largest calibration gap 0.80 > 0.20 | Unmet | Governance/effectiveness overconfidence |
| Governance health 38.8 < 80.0 | Unmet | Completion dimension |
| Overall maturity 76.5 < 80.0 | Unmet | Program maturity |
| Remediation/lifecycle effectiveness | `insufficient_evidence` | Outcome validation |
| Program graduated | false | Verdict |

These are **evidence-quality and calibration** constraints, not pipeline failures.

---

## 8. Operational findings

1. **Pipeline works as documented.** Expansion → backfill → history regeneration → graduation audit update completes end-to-end.
2. **Protected lane integrity confirmed.** 100% commit-worthiness; session noise correctly segregated (751 diagnostic events).
3. **Corpus expansion is effective** for volume targets but produces **synthetic curated observations** — calibration flags overconfidence when volume jumps without matched outcome evidence.
4. **Trajectory is now active** — CO99 trajectory blocker cleared.
5. **BQC4 improved from C → B** — readiness score crossed formal threshold (94.7 ≥ 90.0) but confidence gate still closed.
6. **Live pytest path not exercised this cycle** — evidence came from corpus backfill tools, not a failing `golden_replay` CI run. Session-finish cascade remains unverified in this execution.

---

## 9. Recommended CO102 target

**CO102 — Live Protected Replay Observation & Tooling Repair**

1. **Fix D1:** Repair `capture_recurrence_trajectory_activation.py` import (operational tooling only).
2. **Fix D2:** Restore stable CO99/CO100 governance preamble in regenerated BQ16 (documentation contract).
3. **Execute live observation:** Run `python -m pytest -m golden_replay -q` (or targeted failing scenario) to validate session-finish → `replay_failure_report.md` → protected lane path documented in CO100.
4. **Calibration validation cycle:** Collect observations with outcome backing (remediation closure or recurrence reduction) to address BQC4 overconfidence blockers without changing scoring methodology.

---

## Cross-references

- CO100 runbook: [`protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md)
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Write-path authority: [`BQ36_recurrence_write_path_audit.md`](BQ36_recurrence_write_path_audit.md)
