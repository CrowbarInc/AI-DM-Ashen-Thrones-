# CO103 — Calibration Maturity Assessment

**Date:** 2026-06-28  
**Scope:** Evidence correlation and operational maturity only. Scoring methodology unchanged.

**Prior cycles:** CO100 (workflow) → CO101 (expansion) → CO102 (live pipeline + tooling)

---

## Executive summary

Protected replay observations **do correlate with real engineering outcomes** when sourced from live failures during active programs (vocative projection fix, BX speaker parity). However, **outcome evidence is not reflected in the recurrence history outcome validation layer**, producing a structural **overconfidence** state: high readiness scores with `validated_outcome_count: 0`.

Calibration remains the graduation blocker — classified as **operational maturity** (outcome linkage gap), not implementation deficiency.

---

## Current confidence state (post-regeneration)

| Metric | Value | Target | Status |
|---|---:|---:|---|
| Graduation readiness | 94.7 | ≥ 90.0 | Met |
| Operational readiness | 100.0 | ≥ 80.0 | Met |
| Overall maturity | 76.5 | ≥ 80.0 | Unmet |
| Governance health | 43.7 | ≥ 80.0 | Unmet |
| Calibration score | 55.3 | ≥ 70.0 | Unmet |
| Largest calibration gap | 0.80 | ≤ 0.20 | Unmet |
| Outcome evidence strength | 0.20 | (implicit ≥ 0.75 for confidence ready) | Unmet |
| `graduation_confidence_ready` | false | true | Unmet |
| BQC4 recommendation | B (validation cycle) | A (graduate) | Open |
| Program graduated | false | true | Open |

**Trajectory:** Active (10 snapshots). **Validated outcomes in main history:** 0.

---

## Evidence quality assessment

| Dimension | Assessment |
|---|---|
| **Observation volume** | Adequate for structural analytics (19 events, 7 keys) |
| **Live vs corpus mix** | **Weak for calibration** — 3/7 keys corpus-only; inflates confidence without outcome backing |
| **Outcome documentation** | **Strong externally** (BV8A, BX closeout, test pass verification) |
| **Outcome linkage to recurrence JSON** | **Absent** — main history rejects retirement without event-log evidence |
| **Lifecycle completion rate** | 0% in machine-readable history; ~57% keys have human-auditable fix/design outcomes |
| **Duplicate inflation** | Material on vocative key (8 events → 1 failure signature) |

---

## Why low calibration is not a formula defect

Reviewing `recurrence_confidence_calibration_summary` and BQC5 without modifying formulas:

| Hypothesis | Supported? | Evidence |
|---|---|---|
| **Insufficient sample size** | Partially | 7 keys meet volume targets; outcome signals still zero |
| **Insufficient lifecycle completion** | **Yes** | `validated_outcome_count: 0`, `retired_keys: 0`, `dormant_keys: 0` despite BV8A retirement doc |
| **Insufficient diversity** | No | 4 owner drift buckets, 8 scenarios, live + corpus + BX sources |
| **Genuine uncertainty** | No | Outcomes classifiable from audits; uncertainty is **recording gap**, not unknown engineering state |

**Confidence calculation behavior (unchanged):** Reports `effectiveness_confidence: 1.0` and `governance_confidence: 1.0` from structural volume while `outcome_evidence_strength: 0.20` — correctly flagged **overconfident** (gap 0.80). Formula is working as designed; inputs lack validated outcome signals.

---

## Remaining operational blockers

| Blocker | Category | Operational remediation (not architectural) |
|---|---|---|
| Zero validated outcomes in protected history | Outcome linkage | Record retirements for keys with audit-backed fix evidence (e.g. BV8A vocative) via existing backfill/retirement workflow |
| Corpus rows without live failures | Evidence quality | Stop counting corpus expansion toward calibration evidence; prefer live observations (CO102 path) |
| Active status on fixed keys | Lifecycle | Apply `recurrence_status: retired` when protected replay passes + audit closeout exists |
| CO102 false positive event | Hygiene | Mark or dedupe pipeline-validation artifact (optional operational cleanup) |
| Governance health 43.7 | Completion dimension | Improves when lifecycle closures register in history |
| Outcome evidence strength 0.20 | Calibration | Requires ≥1 validated outcome signal per BQC5 definition |

---

## Estimated path to graduation

| Stage | Operational action | Expected calibration impact |
|---|---|---|
| **CO104** | Link BV8A-class retirement evidence into protected event log (existing retirement tooling) | Outcome strength ↑; gap ↓ |
| **CO105** | Accumulate 2+ live-failure→fix cycles with explicit retirement in log | `validated_outcome_count` ≥ 2 |
| **CO106** | Re-run graduation regeneration; verify `graduation_confidence_ready` | Potential BQC4 → A if governance health follows |

**No formula or threshold changes required** — graduation advances when **existing outcome validation inputs** receive evidence the audits already document.

---

## Recommended CO104 target

**CO104 — Outcome Retirement Propagation**

Operational cycle to propagate audit-backed fix/retirement evidence (starting with BV8A vocative projection key) into the protected event log using **existing** retirement/backfill tooling — closing the observation→outcome→calibration loop without new KPIs or scoring changes.

---

## Cross-references

- Outcome inventory: [`CO103_outcome_lifecycle_inventory.md`](CO103_outcome_lifecycle_inventory.md)
- Correlation report: [`CO103_observation_outcome_correlation.md`](CO103_observation_outcome_correlation.md)
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Effectiveness validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)
