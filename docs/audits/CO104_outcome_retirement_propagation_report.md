# CO104 — Outcome Retirement Propagation Report

**Date:** 2026-06-28  
**Scope:** Operational recording only. No taxonomy, governance, calibration formula, or threshold changes.

**Prior cycles:** CO100 (workflow) → CO101 (expansion) → CO102 (live pipeline) → CO103 (calibration gap analysis)

---

## Executive summary

Audit-backed retirement for the BV8A vocative projection recurrence key was **propagated into the protected event log** using `tools/propagate_outcome_retirements.py` (BV8A retirement registry + evidence gate). Protected history now records **validated outcomes** (`validated_outcome_count: 3`, `retired_keys: 1`), closing the observation→outcome recording gap identified in CO103.

**Verdict:** Lifecycle propagation **succeeds** and is **idempotent**. Graduation remains open — calibration improved materially but `graduation_confidence_ready` is still `false`.

---

## 1. Retirement candidate inventory

Only candidates with **documented engineering disposition** in audit artifacts were considered. No retirements were inferred.

| # | Recurrence key (abbrev.) | Disposition (CO103) | Explicit retirement doc? | Propagation decision |
|---|---|---|---|---|
| 1 | `speaker_drift\|projection\|selected_speaker_id\|golden_replay.py` | Accepted fix + duplicate inflation | **Yes** — [BV8A_retirement_registry.md](BV8A_retirement_registry.md) `RETIRED`; [BV8A_retirement_evidence.md](BV8A_retirement_evidence.md) | **Propagated** |
| 2 | `speaker_drift\|speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | Intentional design + duplicate | No retirement registry entry | **Not propagated** — design decision, not retired defect |
| 3 | `speaker_drift\|speaker\|selected_speaker_source\|speaker_contract_enforcement.py` | Intentional design | No retirement registry entry | **Not propagated** |
| 4 | `emission_drift\|projection\|response_type_candidate_ok\|golden_replay.py` | Accepted fix (BX) | BX closeout; no explicit `RETIRED` registry | **Not propagated** — fix documented, retirement not registered |
| 5 | `fallback_drift\|fallback\|final_emitted_source\|final_emission_gate.py` | Duplicate report (corpus) | No | **Not propagated** |
| 6 | `semantic_drift\|sanitizer\|scaffold_leakage\|output_sanitizer.py` | Duplicate report (corpus) | No | **Not propagated** |
| 7 | `fallback_drift\|projection\|fallback_family\|golden_replay.py` | Rejected report (CO102 false positive) | No | **Not propagated** — false positive, not engineering fix |

### Supporting audit evidence (propagated key)

| Evidence | Source |
|---|---|
| Green vocative structural invariant | `tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` (evidence gate in propagation tool) |
| Retirement registry `RETIRED` status | [BV8A_retirement_registry.md](BV8A_retirement_registry.md) |
| Validated outcome in BV8A sidecar | `artifacts/bv8a_recurrence_history.json` |
| Historical failure retained | `artifacts/golden_replay/replay_failure_report.md`, 8 protected-lane events preserved |

---

## 2. Retirement propagation execution

### Commands run

| Step | Command | Result |
|---|---|---|
| Dry run | `python tools/propagate_outcome_retirements.py --dry-run --generated-at 2026-06-28T14:00:00Z` | 1 candidate, 8 events would mutate |
| Propagation | `python tools/propagate_outcome_retirements.py --generated-at 2026-06-28T14:00:00Z` | **Success** — 8 events marked `recurrence_status: retired` |
| History regeneration | (automatic via propagation tool) | BQ16, BQC4, BQC5 regenerated |
| Trajectory snapshot | `python tools/capture_recurrence_trajectory_activation.py --generated-at 2026-06-28T14:30:00Z` | Snapshot #13 appended |
| Idempotency check | `python tools/propagate_outcome_retirements.py --check` | **Passed** |
| Second propagation | `python tools/propagate_outcome_retirements.py --generated-at 2026-06-28T14:00:00Z` | **0 mutations** — stable |

### Propagation integrity checks

| Requirement | Status |
|---|---|
| Observation chronology preserved | **Met** — all 19 events retained; no dedupe or removal |
| Replay evidence preserved | **Met** — `artifact_source`, `run_id`, `recorded_at`, failure fields unchanged |
| Authority routing preserved | **Met** — `event_source=protected_replay_failure`, commit-worthy lane unchanged |
| Outcome linkage recorded | **Met** — `recurrence_status: retired` + `bv8a_retirement_evidence` on 8 projection events |
| No duplicate retirement records | **Met** — idempotent re-run produces 0 mutations |
| No manual history editing | **Met** — event log updated via tooling; history regenerated from log |

### Event log change summary

| Metric | Before | After |
|---|---:|---:|
| Total protected events | 19 | 19 |
| Projection key events | 8 | 8 |
| Projection events with `recurrence_status: retired` | 0 | **8** |
| Events with `bv8a_retirement_evidence` | 0 | **8** |

---

## 3. Lifecycle integrity validation

### Propagated key lifecycle chain

```
Observation (2026-06-04 vocative failure, 8 events)
    ↓
Classification (projection / speaker_drift / selected_speaker_id)
    ↓
Engineering disposition (accepted fix — BV8A, test green)
    ↓
Retirement (BV8A registry RETIRED + evidence gate PASS)
    ↓
Protected history (recurrence_status: retired → validated_outcome_count ≥ 1)
    ↓
Graduation artifacts (BQC5 has_validated_outcomes: true)
```

**Lifecycle complete** for the vocative projection key.

### Remaining lifecycle discontinuities (6 active keys)

| Key class | Discontinuity | Category |
|---|---|---|
| BX emission_drift (4 events) | Fix documented in BX program; no `retired` status in log | Incomplete retirement coverage |
| BX speaker keys (4 events) | Design decision documented; still `active` | Intentional — not retired defects |
| Corpus-only keys (3 events) | Tests pass; no live failure since backfill | Duplicate observations without outcome linkage |
| CO102 false positive (1 event) | Rejected in CO103; still `active` | Hygiene gap (optional retraction) |

No architectural discontinuities — all gaps are **operational recording** or **evidence accumulation**.

---

## 4. Calibration impact assessment

Metrics measured after propagation + trajectory snapshot. **Formulas and thresholds unchanged.**

| Metric | Pre-CO104 (CO103) | Post-CO104 | Target | Status |
|---|---:|---:|---:|---|
| `validated_outcome_count` | 0 | **3** | ≥ 1 | **Met** |
| `retired_keys` | 0 | **1** | — | Improved |
| `has_validated_outcomes` | false | **true** | — | Improved |
| Outcome evidence strength | 0.20 | **0.43** | ~0.75 for confidence ready | Unmet |
| Calibration score | 55.3 | **61.7** | ≥ 70.0 | Unmet |
| Largest calibration gap | 0.80 | **0.57** | ≤ 0.20 | Unmet |
| Governance health score | 43.7 | **45.9** | ≥ 80.0 | Unmet |
| `graduation_confidence_ready` | false | **false** | true | Unmet |
| BQC4 recommendation | B | **B** | A | Open |
| Overall maturity score | 76.5 | **78.0** | ≥ 80.0 | Unmet |
| Active keys | 7 | **6** | — | Expected after retirement |

**Interpretation:** Propagating one documented retirement **closes the primary CO103 recording gap** and raises outcome evidence strength (+0.23) and calibration score (+6.4). Remaining calibration limitation is **incomplete retirement coverage** across 6 active keys and **insufficient outcome volume** (1 retired key of 7), not formula defect.

---

## 5. Idempotency verification

| Check | First run | Second run |
|---|---|---|
| Events mutated | 8 | **0** |
| Event log row count | 19 | **19** (unchanged) |
| `validated_outcome_count` | 3 | **3** (stable) |
| `calibration_score` | 61.7 | **61.7** (stable) |
| `--check` exit code | N/A (pre-propagation would fail) | **0** |

Deterministic operational behavior confirmed.

---

## 6. Remaining operational blockers

| Blocker | Root cause | Implementation vs evidence |
|---|---|---|
| Calibration score 61.7 < 70 | 6/7 keys lack validated closure | **Evidence accumulation** — propagate BX-class retirements when registry entries exist |
| Governance health 45.9 < 80 | Low lifecycle completion rate (1/7 retired) | **Evidence accumulation** |
| `graduation_confidence_ready: false` | Outcome strength 0.43; gap 0.57 | **Both** — more retirements + live fix cycles |
| BX emission_drift key active | Accepted fix without retirement registry entry | **Implementation work** — document + propagate retirement when BX emission fix is registry-backed |
| Corpus duplicate keys active | Corpus backfill without live failures | **Evidence quality** — prefer live observations (CO102 path) |
| CO102 false positive active | Pipeline validation artifact | **Optional hygiene** — retract or mark deprecated |

### Genuine uncertainty

**None identified.** Remaining limitations are classifiable as incomplete retirement coverage or insufficient long-term operational history — not unknown engineering state.

---

## 7. Recommended CO105 target

**CO105 — Multi-Key Outcome Retirement & Live Fix Cycle Validation**

Operational cycle to:

1. Register explicit retirement disposition for BX emission-drift key (accepted fix with closeout evidence).
2. Execute a **live** protected-replay failure → fix → retirement cycle (second validated outcome per CO103 path).
3. Re-measure calibration without formula changes; target `validated_outcome_count ≥ 2` retired keys and outcome strength approaching confidence-ready band.

Distinguishes **registry/documentation work** (BX emission key) from **evidence accumulation** (second live fix cycle).

---

## Cross-references

- CO103 calibration gap: [`CO103_calibration_maturity_assessment.md`](CO103_calibration_maturity_assessment.md)
- CO103 lifecycle inventory: [`CO103_outcome_lifecycle_inventory.md`](CO103_outcome_lifecycle_inventory.md)
- BV8A retirement evidence: [`BV8A_retirement_evidence.md`](BV8A_retirement_evidence.md)
- Propagation tool: `tools/propagate_outcome_retirements.py`
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Effectiveness validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)
- Protected event log: `artifacts/golden_replay/bug_recurrence_event_log.json`
- Protected history: `artifacts/golden_replay/bug_recurrence_history.json`
