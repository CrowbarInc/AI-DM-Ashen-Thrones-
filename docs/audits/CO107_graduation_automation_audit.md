# CO107 — Graduation Automation Audit & Operational Readiness

**Date:** 2026-06-28  
**Scope:** Operational readiness audit only. No taxonomy, scoring, propagation, or automation changes.

**Prior cycles:** CO106 established permanent governance for all 5 active keys; engineering work complete.

---

## Executive summary

The recurrence graduation pipeline is **fully automated** for evidence ingestion and artifact regeneration. Remaining operator involvement is **bounded and recurring** — protected replay execution, optional trajectory snapshots, retirement propagation when registry entries exist, and periodic graduation review.

**Recommendation stability:** Verified deterministic — identical history payload produces identical BQC4/BQC5 recommendations. Current state: **B** (validation cycle), stable across regeneration.

**Verdict:** Program has transitioned from engineering initiative to **stable operational process**. Future graduation depends solely on naturally accumulated evidence.

---

## 1. Graduation automation audit

### End-to-end workflow map

```
Protected replay (pytest -m golden_replay)
    ↓ [automatic on assertion failure]
record_protected_replay_assertion_failure()
    ↓ [automatic at pytest_sessionfinish when exitstatus ≠ 0]
write_protected_replay_failure_report_if_present()
    → write_owner_drift_hotspot_artifacts()
    → write_owner_drift_risk_artifacts()
        → write_bug_recurrence_history_artifacts(rows, recurrence_event_metadata=...)
            → aggregate analytics from event log
            → build_recurrence_confidence_audit / outcome_validation
            → build_recurrence_final_graduation_decision
            → write bug_recurrence_history.{json,md}
            → write BQ16, BQC4, BQC5 (canonical path only)

Retirement propagation (manual trigger)
    tools/propagate_outcome_retirements.py
        → update event log (recurrence_status: retired)
        → write_bug_recurrence_history_artifacts([])
            → same graduation cascade as above

Trajectory snapshot (manual trigger)
    tools/capture_recurrence_trajectory_activation.py
        → write_bug_recurrence_history_artifacts([], temporal_trajectory_capture=True)
            → append recurrence_trajectory_history.json
            → same graduation cascade
```

**Authority:** [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md) (CO100); implementation in `tests/conftest.py`, `tests/helpers/failure_dashboard_orchestration.py`, `tests/helpers/failure_dashboard_recurrence.py`.

### Automation verification

| Capability | Automatic? | Trigger | Graduation docs updated? |
|---|---|---|---|
| Protected observation recording | **Yes** | Live golden replay failure + sessionfinish | **Yes** — via owner-drift risk cascade |
| Event log append | **Yes** | Same cascade | **Yes** |
| History regeneration | **Yes** | Any `write_bug_recurrence_history_artifacts()` call | **Yes** |
| BQ16 / BQC4 / BQC5 regeneration | **Yes** | When output path is canonical `bug_recurrence_history.json` | **Yes** |
| Retirement propagation | **Manual** | `python tools/propagate_outcome_retirements.py` | **Yes** — on run |
| Trajectory snapshot append | **Manual** | `capture_recurrence_trajectory_activation.py` or `temporal_trajectory_capture=True` | **Yes** — on run |
| Backfill from report | **Manual** | `tools/backfill_bug_recurrence_history.py` | **Yes** — on run |
| Corpus expansion | **Manual** | `tools/expand_protected_replay_observations.py` | **Yes** — via backfill |
| Recommendation recompute | **Yes** | Any history regeneration | **Yes** — deterministic builders |
| Git commit of artifacts | **Manual** | Operator / CI policy | N/A |
| CI artifact upload | **Partial** | `.github/workflows/convergence-checks.yml` uploads failure report only | Does not commit golden-replay lane |

### Integration checks (CO107)

| Check | Result |
|---|---|
| Protected observations update event log | **Pass** — CO102 validated live pipeline |
| Retirement propagation integrates with history | **Pass** — CO104–CO105; `--check` passes post-CO105 |
| Trajectory history updates | **Pass** — snapshot #17 appended (2026-06-28T20:00:00Z run) |
| Graduation artifacts regenerate | **Pass** — BQ16/BQC4/BQC5 dated 2026-06-28T20:00:00Z |
| Recommendation reflects current evidence | **Pass** — BQC4 `one_final_targeted_validation_cycle_required`; calibration 66.3 |

### Remaining manual operational steps

| Step | When required | Command / action |
|---|---|---|
| Commit protected artifacts | After live failure or operational tool run | `git add artifacts/golden_replay/` + graduation docs |
| Backfill | Report exists but event log not updated in-session | `python tools/backfill_bug_recurrence_history.py` |
| Trajectory snapshot | Periodic convergence monitoring | `python tools/capture_recurrence_trajectory_activation.py --generated-at <ISO8601>` |
| Retirement propagation | New documented registry entry (future) | `python tools/propagate_outcome_retirements.py` |
| Propagation idempotency verify | After propagation or audit | `python tools/propagate_outcome_retirements.py --check` |
| Graduation review | Periodic cadence (see §4) | Read BQC4, BQC5, BQ16 |

**No manual history editing** — all updates flow through event log + builders.

---

## 2. Convergence trigger inventory

Every condition capable of changing graduation state, mapped to existing workflow participation.

| Trigger | Affects | Participates in workflow? | Path |
|---|---|---|---|
| New protected replay observation | Event log, volume, trends, forecast | **Yes** | Live failure cascade → `write_bug_recurrence_history_artifacts` |
| Validated retirement (`recurrence_status: retired`) | Outcome validation, closure rate, calibration | **Yes** | `propagate_outcome_retirements.py` → history regeneration |
| Trajectory snapshot growth | `trajectory_available`, reduction signals, maturity | **Yes** | `capture_recurrence_trajectory_activation.py` (`temporal_trajectory_capture=True`) |
| Calibration score change | BQC4 recommendation, `graduation_confidence_ready` | **Yes** | Derived in `calculate_confidence_calibration_score()` on regeneration |
| Governance health change | Completion dimension, maturity | **Yes** | `_governance_health_score()` on regeneration |
| Outcome evidence strength change | BQC5 recommendation, effectiveness gap | **Yes** | `calculate_effectiveness_evidence_strength()` on regeneration |
| Natural inactivity (90-day dormant) | Dormant outcome signals | **Yes** | `_validate_dormant_outcome_signal()` — time-driven, no new trigger needed |
| Corpus backfill | Observation volume (not recommended for calibration) | **Yes** | `backfill_bug_recurrence_history.py` |
| CI golden replay pass (no failure) | None | **Yes** — no-op | No cascade when exitstatus=0 and no failures recorded |
| Manual history edit | Would affect all metrics | **Excluded** — policy violation | Not in workflow |

**No undocumented triggers.** All graduation state changes derive from protected event log content or trajectory history, recomputed on regeneration.

---

## 3. Recommendation stability

### BQC4 decision tree (deterministic)

Builder: `_determine_final_graduation_recommendation()` in `replay_bug_recurrence_serialization.py`.

| Priority | Condition | Recommendation token | Human label |
|---|---|---|---|
| 1 | `formal_ready` ∧ readiness ≥ 90 ∧ no blockers | `graduate_recurrence_program` | **A — Graduate** |
| 2 | `trajectory_available` ∧ readiness ≥ 70 | `one_final_targeted_validation_cycle_required` | **B — Validation cycle** |
| 3 | Else | `recurrence_program_remains_operationally_immature` | **C — Immature** |

**`formal_ready` requires (all):** calibration ≥ 70, gap ≤ 0.20, trajectory available, zero critical blind spots, `graduation_confidence_ready=true`.

**`graduation_confidence_ready` requires (all):** score ≥ 70, gap ≤ 0.20, zero severe overconfidence penalties, forecast/governance/effectiveness statuses ≠ overconfident.

### BQC5 decision tree (deterministic)

Builder: `_determine_bqc5_graduation_recommendation()`.

| Priority | Condition | Recommendation |
|---|---|---|
| 1 | `formal_ready` (includes outcome_supported, has_outcomes) | Graduate |
| 2 | trajectory ∧ has_outcomes | Validation period |
| 3 | trajectory only | Validation period |
| 4 | Else | Immature |

### Transition map (current → future)

| Transition | Gate | Current state |
|---|---|---|
| **C → B** | `trajectory_available=true` AND readiness ≥ 70 | **Already achieved** (trajectory since CO101; readiness 94.7) |
| **B → A** | All `formal_ready` conditions + readiness ≥ 90 + empty blockers | **Blocked** — calibration 66.3, gap 0.40, `graduation_confidence_ready=false`, governance incomplete |
| **Confidence ready** | Calibration score ≥ 70, gap ≤ 0.20, no overconfident dimensions | **Not met** |
| **Graduated** | BQC4 recommendation = graduate + `formal_graduation_criteria_met=true` | **Not met** |

### Determinism verification

| Test | Result |
|---|---|
| Regenerate twice without event log change | **Stable** — calibration 66.3, recommendation B (CO107 run) |
| `propagate_outcome_retirements.py --check` | **Pass** — no pending mutations |
| Unit tests | **16 passed** — `test_build_recurrence_final_graduation_decision_*`, outcome validation tests |
| Contract tests | **3 passed** — CO99/CO100 documentation locks |

Identical evidence → identical recommendations. No stochastic or time-of-day variance in builders (except `as_of` for inactivity calculations, which use event timestamps not wall clock during regeneration).

---

## 4. Operational maintenance guide

### Recurring operator responsibilities

| Task | Cadence | Type | Effort |
|---|---|---|---|
| Run protected replay lane | Weekly or pre-release | **Operational** | `python -m pytest -m golden_replay -q` |
| Review failure report on red runs | As needed | **Operational** | Read `replay_failure_report.md` |
| Commit golden-replay artifacts | After meaningful observation changes | **Operational** | Git commit |
| Capture trajectory snapshot | Monthly | **Operational** | `capture_recurrence_trajectory_activation.py` |
| Graduation review (BQC4/BQC5) | Monthly or after snapshot | **Operational** | Read regenerated audits |
| Propagation check | After any propagation | **Operational** | `propagate_outcome_retirements.py --check` |
| Backfill | When CI report not committed | **Operational** | `backfill_bug_recurrence_history.py` |

### One-time / completed engineering work (no recurrence)

| Task | Status |
|---|---|
| Recurrence taxonomy (CO99) | **Closed** |
| Observation pipeline (CO100–CO102) | **Complete** |
| Outcome linkage (CO103–CO105) | **Complete** |
| Governance classification (CO106) | **Complete** |
| Retirement registry for existing fixes | **Complete** (2 keys) |
| Toolchain defects (D1/D2) | **Fixed** (CO102) |

### Not recommended recurring work

| Task | Reason |
|---|---|
| Corpus expansion for calibration | CO103/CO106 — inflates volume without outcome signal |
| Retirement propagation on permanent keys | CO106 — 5 keys excluded by governance |
| Manual history edits | Policy violation |
| Formula/threshold tuning | Out of scope — graduation via evidence only |

---

## 5. Graduation artifact refresh

Regenerated (CO107):

```bash
python tools/capture_recurrence_trajectory_activation.py --generated-at 2026-06-28T20:00:00Z
```

| Artifact | Date | Key values | Consistent? |
|---|---|---|---|
| `BQ16_recurrence_graduation_audit.md` | 2026-06-28T20:00:00Z | Readiness 94.7; CO99 preamble preserved | **Yes** |
| `BQC4_final_graduation_decision.md` | 2026-06-28T20:00:00Z | Recommendation B; calibration 66.3; snapshots 17 | **Yes** |
| `BQC5_effectiveness_validation.md` | 2026-06-28T20:00:00Z | 2 retired; 5 outcomes; strength 0.60 | **Yes** |
| `bug_recurrence_history.json` | Regenerated | Aligns with 19-event log, 7 keys | **Yes** |

Internal consistency: BQC4 blockers match CO106 calibration ceiling analysis; permanent active keys unchanged; no propagation performed.

---

## 6. Long-term operational readiness assessment

### Current operational maturity

| Dimension | Status |
|---|---|
| Governance | **Complete** — all keys classified (CO106) |
| Toolchain | **Complete** — live pipeline validated (CO102) |
| Retirement propagation | **Complete** — idempotent, multi-key (CO105) |
| Inventory | **Complete** — 2 retired, 5 permanent active |
| Automation | **Complete** — graduation cascade wired |
| Graduation | **Open** — evidence-limited, not implementation-limited |

### Remaining graduation prerequisites

| Prerequisite | Source | Engineering or operational? |
|---|---|---|
| Calibration score ≥ 70 | Outcome + governance evidence | **Operational** |
| Largest gap ≤ 0.20 | Effectiveness/governance alignment | **Operational** |
| `graduation_confidence_ready=true` | All confidence dimensions calibrated | **Operational** |
| Governance health ≥ 80 | Lifecycle completion over time | **Operational** |
| Live failure→fix→retire on **new** key | Independent operational cycle | **Operational** |
| Optional CO102 sentinel hygiene | Retraction of false positive | **Operational** (optional) |

**No remaining engineering prerequisites** for the 7-key inventory.

### Expected evidence accumulation path

1. **Live protected replay** produces new observations on genuine failures (rare when suite green).
2. **Engineering fix + retirement registry** (when fix occurs) → propagation → calibration lift.
3. **Trajectory snapshots** accumulate → governance health convergence over time.
4. **Calibration metrics** rise monotonically with validated outcomes (CO104–CO105 demonstrated).
5. **BQC4 recommendation** transitions B → A when `formal_ready` gates clear — no operator decision required beyond reviewing regenerated docs.

### Estimated operator involvement

| Phase | Involvement |
|---|---|
| Steady state (green suite) | **Low** — monthly trajectory capture + graduation review (~15 min) |
| Live failure event | **Medium** — triage, fix, registry doc, propagation, commit (~1–2 hours engineering + 15 min operational) |
| Graduation convergence | **Low** — read BQC4 when `graduation_confidence_ready` flips true |

### Recommended graduation review cadence

| Review | Frequency | Artifacts |
|---|---|---|
| Quick status | Monthly | BQC4 recommendation + calibration score |
| Full convergence | Quarterly | BQ16 + BQC4 + BQC5 + CO106 inventory cross-check |
| Post-incident | After live failure or propagation | Event log + history + `--check` |

---

## 7. Recommended CO108 target

**CO108 — Scheduled Operational Cycle & Graduation Watch**

Operational cycle assuming no architectural work:

1. **Execute** scheduled protected replay monitoring run (document pass/fail; commit artifacts if failures).
2. **Capture** trajectory snapshot #18+ on fixed cadence.
3. **Monitor** BQC4 for `graduation_confidence_ready` transition — document delta only, no formula changes.
4. **Optional:** Execute one live failure→fix→retire cycle if a genuine protected replay failure occurs during monitoring (natural trigger, not fabricated).
5. **Produce** graduation watch report comparing monthly snapshots until recommendation reaches **A** or evidence plateau is confirmed.

Purpose: demonstrate sustained operational process execution with minimal operator overhead until graduation occurs naturally.

---

## Cross-references

- CO106 governance audit: [`CO106_active_recurrence_governance_audit.md`](CO106_active_recurrence_governance_audit.md)
- CO100 runbook: [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md)
- Propagation tool: `tools/propagate_outcome_retirements.py`
- Trajectory tool: `tools/capture_recurrence_trajectory_activation.py`
- Graduation builders: `tests/helpers/replay_bug_recurrence_serialization.py`, `replay_bug_recurrence_statistics.py`
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Effectiveness validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)
