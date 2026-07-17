# CO108 — Recurrence Engineering Boundary Specification

**Date:** 2026-06-28  
**Scope:** Documentation only. Defines what work belongs to platform maintenance vs recurrence engineering.

**Governing closeout:** [`CO108_recurrence_program_closeout.md`](CO108_recurrence_program_closeout.md)

---

## Purpose

After CO108, the recurrence subsystem operates under **platform stewardship**. This document prevents scope creep: routine operational activity must not be mistaken for an active engineering program, and genuine architectural needs must not be buried in maintenance tickets.

---

## Work categories

### 1. Maintenance work (platform stewardship — default)

**Definition:** Execution of existing workflows using current tools, taxonomy, formulas, and thresholds. No design decisions about recurrence architecture.

| Examples | In scope? |
|---|---|
| Weekly/monthly protected replay runs | **Yes** |
| Committing regenerated artifacts after observation changes | **Yes** |
| Monthly trajectory capture | **Yes** |
| Reading BQC4/BQC5 for graduation status | **Yes** |
| Running `propagate_outcome_retirements.py` when registry entry exists | **Yes** |
| Running `backfill_bug_recurrence_history.py` when report exists | **Yes** |
| Post-incident triage using existing failure report format | **Yes** |
| Runbook typo/clarification (no new requirements) | **Yes** |
| Optional CO102 sentinel retraction (`deprecated`) | **Yes** — hygiene |

**Owner:** Platform steward. **Engineering program:** Closed.

---

### 2. Operational evidence accumulation (not engineering)

**Definition:** Natural growth of protected-lane evidence through live operations, time, and validated outcomes. Metrics change because **events occurred**, not because recurrence architecture changed.

| Examples | Reopens engineering? |
|---|---|
| New protected replay failure on genuine defect | **No** — triggers normal fix workflow |
| Fix merged + retirement registry + propagation | **No** — existing propagation semantics |
| Trajectory snapshots accumulating over months | **No** |
| Calibration score rising as validated outcomes increase | **No** |
| Governance health converging over longitudinal history | **No** |
| BQC4 recommendation transitioning B → A when gates clear | **No** — deterministic builder outcome |
| Waiting for live failure→fix→retire on **new** key | **No** — CO106 documented path |

**Critical rule:** Evidence accumulation alone **does not** reopen the recurrence engineering program. Stewards execute the CO100 workflow; engineers fix bugs through normal product engineering when failures occur.

---

### 3. Bug fixes (product engineering — adjacent, not recurrence program)

**Definition:** Correcting defective behavior discovered via protected replay or otherwise. Uses normal code review and testing. May **consume** recurrence workflow outputs but is not recurrence **architecture** work.

| Examples | Recurrence engineering? |
|---|---|
| Fix speaker contract violation causing golden replay failure | **No** — product bug fix |
| Add retirement registry documenting the fix | **No** — stewardship disposition |
| Propagate retirement after fix lands | **No** — operational workflow |
| Fix unrelated production emission bug | **No** |

If the fix requires **changing recurrence key formula, event routing, or graduation builders**, that crosses into category 4 or 5 and may trigger re-entry.

---

### 4. Future architectural work (re-entry required)

**Definition:** Changes to recurrence subsystem structure, authority model, data flow, or cross-program contracts.

| Examples | Re-entry required? |
|---|---|
| New recurrence taxonomy family or status enum | **Yes** |
| Change to `build_recurrence_key()` formula | **Yes** |
| Modify protected-lane routing or commit-worthiness rules | **Yes** |
| Restructure graduation builder decision trees | **Yes** |
| Change replay observation cascade wiring | **Yes** |
| Merge recurrence with unrelated analytics systems | **Yes** |
| Resolve CO106 permanent-key disposition via new registry policy | **Yes** |

**Process:** Evaluate against [`CO108_reentry_criteria.md`](CO108_reentry_criteria.md) before starting.

---

### 5. Future feature work (re-entry required)

**Definition:** New recurrence **capabilities** beyond the closed program scope.

| Examples | Re-entry required? |
|---|---|
| New graduation dimensions or KPIs | **Yes** |
| New automation beyond existing cascade | **Yes** |
| Operator dashboard for recurrence outside pytest artifacts | **Yes** |
| Cross-campaign recurrence correlation | **Yes** |
| ML-based recurrence prediction | **Yes** |
| CI auto-commit of golden-replay artifacts | **Yes** — new operational policy |
| Synthetic outcome injection for calibration | **Yes** — policy violation unless explicitly designed |

---

## Decision matrix

```
Does the work change recurrence taxonomy, formulas, thresholds,
builders, replay cascade, or introduce new capabilities?
    │
    ├─ No  → Maintenance, evidence accumulation, or product bug fix
    │         (recurrence engineering program stays closed)
    │
    └─ Yes → Check CO108 re-entry criteria
              │
              ├─ Criteria met → Open targeted engineering cycle
              └─ Criteria not met → Defer or handle as unrelated work
```

---

## Explicit non-reopeners

The following **do not** justify reopening recurrence engineering:

| Condition | Why not |
|---|---|
| BQC4 still recommendation **B** | Expected — evidence-limited graduation (CO106 ceiling) |
| Calibration score below 70 | Operational evidence path, not architecture gap |
| `graduation_confidence_ready: false` | Same |
| 5 permanent active keys remain | Governance intent resolved (CO106) |
| Monthly trajectory snapshots | Stewardship cadence |
| Green golden replay suite for extended period | Normal steady state |
| Desire to accelerate graduation via corpus inflation | Policy violation (CO103) |

---

## Interaction with sibling programs

| Program | Status | Recurrence boundary |
|---|---|---|
| Attribution (CO96) | Closed | Do not reopen for recurrence graduation |
| Failure classification (CO98/CG-1) | Closed | Classifier rows feed recurrence; do not extend taxonomy for graduation |
| Recurrence taxonomy (CO99/CG-4) | Closed | Vocabulary frozen; re-entry required for extension |
| Recurrence operational graduation | Active (evidence) | Stewardship monitors BQC4; not engineering |

---

## Cross-references

- Stewardship guide: [`CO108_platform_stewardship_guide.md`](CO108_platform_stewardship_guide.md)
- Re-entry criteria: [`CO108_reentry_criteria.md`](CO108_reentry_criteria.md)
- Governance audit: [`CO106_active_recurrence_governance_audit.md`](CO106_active_recurrence_governance_audit.md)
