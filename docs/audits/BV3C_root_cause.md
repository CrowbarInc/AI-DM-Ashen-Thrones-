# BV3C — Root Cause Determination

**Date:** 2026-06-21  
**Primary metric:** Repair Activation Rate = **0%** (0 / 65 observe FEM instances)  
**Expected:** >0% on observe turns matching BV3A eligibility rules

---

## Selected root cause

## **Mixed causes**

No single defect explains the gap. BV3A code behaves as tested; replay measurement reflects **corpus composition**, **eligibility boundary**, and **metric scan scope**.

---

## Cause breakdown

| # | Cause class | Weight | Explanation |
|---|---|---|---|
| 1 | **Corpus mismatch** | **High** | 68% of observe FEM (44/65) are **pre-BV3A archived** hygiene snapshots without upstream instrumentation. Zero applied is partially a **measurement denominator** problem. |
| 2 | **Eligibility drift** | **High** | All 11 refreshed turns with `upstream_repair_attempted=true` have `eligible=false`: multi-violation (10), `referent_drift` (1). **Zero turns** match the unit-test profile (single `ambiguous_entity_reference` + pronoun + grounding). |
| 3 | **Replay divergence** | **Medium** | API path emits **prepared/retry** text (named guards, passive-scene accepts), not the BV3B stub shape. Standalone validation of emitted guard dialogue returns **ok=True** — upstream exits without attempt. Retry passes leave FEM violation samples that **do not match** finalized text. |
| 4 | **Pipeline bypass** | **None** | Refreshed observe turns reach `apply_observe_referential_clarity_upstream_repair` when violations exist. Not the failure mode. |
| 5 | **Instrumentation defect** | **None** | Field stamps true on eligible fixture; preserved via meta snapshot; visible as false/not-null on refreshed artifacts. |
| 6 | **Metadata mismatch** | **None** | No case of `applied=true` lost before persistence. |

---

## Causal chain (refreshed turns only)

```
/api/chat observe
  → non-strict layer stack + retry/prepared emission
  → gate candidate often passes referential validation OR fails with ≠1 violation / referent_drift
  → apply_observe_referential_clarity_upstream_repair
       attempted=true (when violations present)
       eligible=false (multi-violation or wrong kind)
       applied=false
  → apply_referential_clarity_enforcement hard replace
  → referential_clarity_replacement_applied=true
  → metrics: upstream_repair_applied=0
```

---

## Why unit tests pass

Tests exercise a **narrow contract slice**:

- One violation, token `he`, dialogue attribution  
- Interlocutor + social NPC grounding  
- Direct gate consumer on synthetic candidate  

Replay exercises **production emission economics**:

- No social target on observe turns  
- Multi-person frontier_gate scenes (4–6 actors)  
- Named anchors and retry bundles that bypass or fail eligibility  

**Intersection is empty** → tests pass, replay activation 0%.

---

## Answer to audit question

> Why did BV3A produce 0 repairs despite passing tests?

**Because the refreshed replay corpus contains no observe turn that satisfies BV3A's eligibility predicate at upstream repair time**, and the majority of scanned FEM predates BV3A instrumentation. The implementation activates correctly on the synthetic fixture; production candidates are different shapes that are ineligible or already validator-clean.

---

## Not root cause

- Missing call to upstream repair in terminal pipeline  
- Broken `referential_clarity_upstream_repair_applied` stamp  
- Strict-social misclassification of observe turns in scan  
- Downstream hard replace running before upstream (ordering is correct)

---

## Confidence

| Claim | Confidence |
|---|---|
| Instrumentation works | High (unit test + code review) |
| Pipeline reaches upstream on violations | High (11 attempted on refreshed turns) |
| Corpus lacks eligible shapes | High (eligibility extract) |
| Archive inflates null-upstream count | High (44/65 from pre-refresh tree) |
| Retry/FEM snapshot divergence | Medium (1 confirmed turn; likely more in nested FEM) |
