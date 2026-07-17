# CO105 — Multi-Key Retirement Validation Report

**Date:** 2026-06-28  
**Scope:** Operational recording and lifecycle validation only. No taxonomy, governance, calibration formula, or threshold changes.

**Prior cycles:** CO104 (single-key BV8A propagation) → CO105 (multi-key expansion)

---

## Executive summary

A **second documented retirement** (BX emission-drift key) was propagated into the protected event log using the consolidated `tools/propagate_outcome_retirements.py` registry. Protected history now records **2 retired keys** and **5 validated outcome signals**, demonstrating that the observation→retirement lifecycle **scales beyond the BV8A validation case** with deterministic, idempotent behavior.

**Verdict:** Multi-key propagation **succeeds**. Calibration progressed materially (61.7 → 66.3) without formula changes. Graduation remains open — `graduation_confidence_ready` is still `false`.

---

## 1. Remaining recurrence key review

Post-CO104 baseline: **6 active keys**. After CO105: **5 active keys**, **2 retired keys**.

| # | Recurrence key (abbrev.) | Events | Disposition | Audit evidence | Retirement eligible? | CO105 action |
|---|---|---:|---|---|---|---|
| 1 | `speaker_drift\|projection\|selected_speaker_id\|golden_replay.py` | 8 | Accepted fix | [BV8A_retirement_evidence.md](BV8A_retirement_evidence.md) | **Yes** — already propagated (CO104) | No mutation (already retired) |
| 2 | `emission_drift\|projection\|response_type_candidate_ok\|golden_replay.py` | 4 | Accepted fix (BX) | [BX_emission_retirement_evidence.md](BX_emission_retirement_evidence.md), BX closeout, CO103 | **Yes** — registry documented | **Propagated** |
| 3 | `speaker_drift\|speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | 2 | Intentional design | [BX closeout](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md) | **No** — design decision, not retired defect | Remains active |
| 4 | `speaker_drift\|speaker\|selected_speaker_source\|speaker_contract_enforcement.py` | 2 | Intentional design | BX closeout | **No** | Remains active |
| 5 | `fallback_drift\|fallback\|final_emitted_source\|final_emission_gate.py` | 1 | Duplicate report (corpus) | CO103 corpus mapping | **No** — no engineering fix or registry | Remains active |
| 6 | `semantic_drift\|sanitizer\|scaffold_leakage\|output_sanitizer.py` | 1 | Duplicate report (corpus) | CO103 corpus mapping | **No** | Remains active |
| 7 | `fallback_drift\|projection\|fallback_family\|golden_replay.py` | 1 | Rejected report (CO102) | CO102 pipeline validation artifact | **No** — false positive | Remains active |

### Missing evidence preventing propagation (5 active keys)

| Key | Blocker |
|---|---|
| BX speaker keys (×2) | Intentional architecture — not engineering retirements |
| Corpus fallback + sanitizer | Duplicate observations; tests pass; no retirement registry |
| CO102 fallback_family | Rejected false positive; no fix warranted |

---

## 2. Additional retirement propagation

### Registry registration

| Key | Registry doc | Evidence doc |
|---|---|---|
| BX emission-drift | [BX_emission_retirement_registry.md](BX_emission_retirement_registry.md) | [BX_emission_retirement_evidence.md](BX_emission_retirement_evidence.md) |

Consolidated with BV8A `RETIRED` entry in `tools/propagate_outcome_retirements.py` → `DOCUMENTED_RETIREMENT_REGISTRY`.

### Commands run

| Step | Command | Result |
|---|---|---|
| Dry run | `python tools/propagate_outcome_retirements.py --dry-run --generated-at 2026-06-28T16:00:00Z` | 2 candidates; 4 events would mutate (emission only) |
| BX evidence gate | `python -m pytest -m bx_speaker_parity -q --tb=short` | **PASS** |
| Propagation | `python tools/propagate_outcome_retirements.py --generated-at 2026-06-28T16:00:00Z` | **Success** — 4 emission events → `retired` |
| Trajectory snapshot | `python tools/capture_recurrence_trajectory_activation.py --generated-at 2026-06-28T16:30:00Z` | Snapshot #15 appended |
| Idempotency check | `python tools/propagate_outcome_retirements.py --check` | **Passed** |
| Second propagation | `python tools/propagate_outcome_retirements.py --generated-at 2026-06-28T16:00:00Z` | **0 mutations** |

### Event log change summary

| Metric | Post-CO104 | Post-CO105 |
|---|---:|---:|
| Total protected events | 19 | 19 |
| Retired keys | 1 | **2** |
| Emission events with `recurrence_status: retired` | 0 | **4** |
| Active keys in history | 6 | **5** |

---

## 3. Second operational lifecycle (BX emission — independent of BV8A)

```
Protected replay (bx5_guard_* scenarios, 2026-06-22 BX development run)
    ↓
Observation (4 commit-worthy emission_drift events in protected log)
    ↓
Engineering disposition (BX program closed 2026-06-22; CO103 accepted fix)
    ↓
Retirement registration (BX_emission_retirement_registry.md — CO105)
    ↓
Retirement propagation (recurrence_status: retired on 4 events)
    ↓
History regeneration (bug_recurrence_history.json from event log)
    ↓
Graduation artifacts (BQ16, BQC4, BQC5 auto-regenerated)
    ↓
Calibration update (outcome strength 0.43 → 0.60; score 61.7 → 66.3)
```

**Lifecycle complete** for BX emission-drift key — independent engineering program, independent evidence gate (`bx_speaker_parity`), independent recurrence key.

---

## 4. Propagation consistency validation

| Requirement | BV8A projection key | BX emission key | Consistent? |
|---|---|---|---|
| Per-key evidence gate | Vocative structural invariant | `bx_speaker_parity` marker suite | Yes — key-specific gates, shared tooling |
| Per-key failure isolation | Gate failure does not block other keys | Same | Yes |
| `recurrence_status: retired` only | + `bv8a_retirement_evidence` blob | Status field only (no new semantics) | Expected difference — BV8A pre-existing blob |
| Chronology preserved | 8/8 events retained | 4/4 events retained | Yes |
| Authority routing preserved | `protected_replay_failure` lane | Same | Yes |
| Idempotent re-run | 0 mutations when retired | Same | Yes |
| Deterministic regeneration | Stable metrics on re-run | Same | Yes |

**Note:** BV8A vocative gate test node was corrected to `tests/test_golden_replay_structural_invariants.py::…` (test moved from `test_golden_replay.py`). CO104 retirement metadata remains valid; gate now passes on re-run.

No special-case propagation logic introduced — only registry entries and evidence gate mappings differ by key.

---

## 5. Calibration progression assessment

Metrics measured after CO105 propagation + trajectory snapshot #15. **Formulas and thresholds unchanged.**

| Metric | CO104 (baseline) | CO105 (after) | Δ | Target | Status |
|---|---:|---:|---:|---:|---|
| `retired_keys` | 1 | **2** | +1 | ≥ 2 (CO105 goal) | **Met** |
| `validated_outcome_count` | 3 | **5** | +2 | — | Improved |
| Outcome evidence strength | 0.43 | **0.60** | +0.17 | ~0.75 | Unmet |
| Calibration score | 61.7 | **66.3** | +4.6 | ≥ 70.0 | Unmet (closer) |
| Largest calibration gap | 0.57 | **0.40** | −0.17 | ≤ 0.20 | Unmet (closer) |
| Governance health | 45.9 | **45.9** | 0 | ≥ 80.0 | Unmet |
| Overall maturity | 78.0 | **79.0** | +1.0 | ≥ 80.0 | Near |
| `graduation_confidence_ready` | false | **false** | — | true | Unmet |
| BQC4 recommendation | B | **B** | — | A | Open |
| Active keys | 6 | **5** | −1 | — | Expected |

**Interpretation:** Multi-key retirement propagation produces **monotonic calibration improvement** through operational evidence alone. Two retired keys satisfy the CO105 expansion target; remaining gap is **evidence volume and governance completion**, not mechanism failure.

---

## 6. Remaining active recurrence-key inventory

| Key (abbrev.) | Events | Status | Blocker category |
|---|---:|---|---|
| `speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | 2 | active | Intentional design — not a retireable defect |
| `speaker\|selected_speaker_source\|speaker_contract_enforcement.py` | 2 | active | Intentional design |
| `fallback\|final_emitted_source\|final_emission_gate.py` | 1 | active | Corpus duplicate — no live failure |
| `sanitizer\|scaffold_leakage\|output_sanitizer.py` | 1 | active | Corpus duplicate |
| `projection\|fallback_family\|golden_replay.py` | 1 | active | False positive (CO102) |

---

## 7. Remaining graduation blockers

| Blocker | Root cause | Implementation vs evidence |
|---|---|---|
| Calibration 66.3 < 70 | 5/7 keys still active | **Evidence accumulation** |
| Gap 0.40 > 0.20 | Structural confidence still exceeds outcome strength | **Evidence accumulation** |
| Governance health 45.9 < 80 | Lifecycle completion 2/7 (28.6%) | **Evidence accumulation** |
| 5 active keys without closure | No documented retirements for remaining keys | **Not implementation gaps** — dispositions are design/duplicate/false-positive |
| `graduation_confidence_ready: false` | Outcome strength 0.60 below implicit ready band | **Evidence accumulation** + optional corpus hygiene |

### Genuine uncertainty

**None.** Remaining blockers are classifiable as insufficient retirement coverage, corpus noise, or threshold distance — not unknown engineering state.

---

## 8. Recommended CO106 target

**CO106 — Graduation Threshold Convergence & Corpus Hygiene**

Operational cycle to:

1. Retract or mark deprecated the CO102 false-positive `fallback_family` event (optional hygiene — reduces active-key noise without new semantics).
2. Accumulate long-term operational history (≥ 3 trajectory snapshots post-multi-key retirement) to stabilize governance health scoring.
3. Re-measure calibration against unchanged thresholds; target calibration score ≥ 70 and gap ≤ 0.20.
4. If metrics converge, evaluate BQC4 recommendation transition B → A without formula changes.

Separates **optional hygiene work** from **time-based evidence accumulation** required for governance health convergence.

---

## Cross-references

- CO104 baseline: [`CO104_outcome_retirement_propagation_report.md`](CO104_outcome_retirement_propagation_report.md)
- BX emission registry: [`BX_emission_retirement_registry.md`](BX_emission_retirement_registry.md)
- BX emission evidence: [`BX_emission_retirement_evidence.md`](BX_emission_retirement_evidence.md)
- Propagation tool: `tools/propagate_outcome_retirements.py`
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Effectiveness validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)
