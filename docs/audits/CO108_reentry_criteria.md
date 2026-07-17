# CO108 — Recurrence Engineering Re-Entry Criteria

**Date:** 2026-06-28  
**Scope:** Documentation only. Defines objective conditions to reopen the closed recurrence engineering program.

**Default state:** Recurrence engineering is **closed**. Platform stewardship handles all routine work per [`CO108_platform_stewardship_guide.md`](CO108_platform_stewardship_guide.md).

---

## Purpose

Re-entry criteria prevent two failure modes:

1. **Premature reopening** — treating normal evidence accumulation or product bug fixes as recurrence architecture work.
2. **Deferred reopening** — ignoring genuine architectural defects because the program is marked closed.

Any re-entry must be **documented**, **scoped**, and **justified** against the criteria below before implementation begins.

---

## Re-entry gate (all required)

| Gate | Requirement |
|---|---|
| **Documented trigger** | At least one criterion from §Objective triggers is met |
| **Impact assessment** | Written note describing affected modules, artifacts, and governance docs |
| **Scope boundary** | Explicit list of in-scope vs out-of-scope changes |
| **No routine-evidence masquerade** | Trigger is not solely "calibration score still below target" or "waiting for more snapshots" |

---

## Objective triggers (any one sufficient)

### T1 — Architectural defect in recurrence pipeline

**Condition:** Deterministic failure in recurrence-specific code paths that cannot be resolved through product bug fixes alone.

| Indicators | Examples |
|---|---|
| Observation cascade fails to write event log on valid protected failure | Sessionfinish hook regression |
| Graduation builders produce inconsistent output from identical input | Non-determinism in BQC4/BQC5 |
| Protected-lane routing incorrectly excludes commit-worthy events | `is_commit_worthy_recurrence_event()` false negative at scale |
| Retirement propagation corrupts event log or violates idempotency | `--check` fails after valid propagation |

**Not T1:** Single golden replay scenario failure caused by production code defect (handle as product fix + stewardship).

---

### T2 — Governance inconsistency

**Condition:** Documented governance intent contradicts machine-readable recurrence state, and resolution requires **engineering** (not documentation-only reclassification).

| Indicators | Examples |
|---|---|
| Active key lacks CO106-equivalent classification with live defect signal | New key with unresolved investigate tier and no disposition doc |
| Retirement registry and event log disagree after valid propagation | Builder bug, not operator error |
| CG-4 registry and runtime taxonomy enums diverge | Code allows status value not in registry |
| BQ16 preamble and builder output systematically contradict | Renderer regression (CO102-class) |

**Not T2:** Updating audit markdown to reflect new evidence without code changes (stewardship documentation).

---

### T3 — Deterministic automation failure

**Condition:** Existing graduation automation produces incorrect or incomplete artifacts under valid operational inputs.

| Indicators | Examples |
|---|---|
| Regeneration drops CO99/CO100 governance preamble | CO102 regression |
| Trajectory capture fails when event log is valid | Tooling defect |
| Backfill produces duplicate events despite idempotency contract | Serialization bug |
| Contract tests in `test_recurrence_contract.py` fail due to builder regression | Implementation defect |

**Not T3:** Operator skipped backfill when report exists (stewardship execution gap).

---

### T4 — New recurrence capability requiring design work

**Condition:** Requested capability is outside the closed program scope per [`CO108_engineering_boundary_specification.md`](CO108_engineering_boundary_specification.md) §4–§5.

| Indicators | Examples |
|---|---|
| New taxonomy family or graduation dimension | Requires CG-4 amendment + builder design |
| New observation source beyond protected replay lane | Architecture decision |
| CI policy to auto-commit recurrence artifacts | New automation design |
| Cross-system recurrence correlation | New feature program |

**Not T4:** Running existing tools on existing sources more frequently (stewardship cadence change).

---

### T5 — Scoring or threshold change request

**Condition:** Stakeholders require modification to graduation formulas, calibration weights, or `formal_ready` gate constants.

| Indicators | Examples |
|---|---|
| Change to `calculate_confidence_calibration_score()` weights | Engineering + audit cycle |
| Change to `calculate_effectiveness_evidence_strength()` formula | Same |
| Lower graduation thresholds to force recommendation **A** | Policy decision requiring explicit re-entry |

**Not T5:** Calibration score rising naturally through validated retirements (operational evidence).

---

## Explicit exclusions (never sufficient alone)

| Exclusion | Rationale |
|---|---|
| Routine protected replay monitoring | Stewardship (CO108) |
| Trajectory snapshot cadence | Stewardship |
| BQC4 recommendation **B** persisting | Expected post-CO106 ceiling |
| Calibration score 66.3, gap 0.40 | Evidence-limited; operational path |
| 5 permanent active keys | Governance resolved (CO106) |
| Desire for faster graduation | Not architectural trigger |
| Corpus expansion for volume | CO103 policy — not engineering |
| Product bug fix without recurrence architecture impact | Normal engineering |
| Documentation of monthly graduation watch | Stewardship reporting |

---

## Re-entry process (when triggered)

1. **Record trigger** — Document which criterion (T1–T5) applies with reproducible evidence.
2. **Scope cycle** — Name cycle (e.g., CO109); limit to trigger scope; restate CO108 constraints still in force.
3. **Assess blast radius** — List modules: `replay_bug_recurrence_*.py`, tools, artifacts, CG-4 registry, runbook.
4. **Implement** — Only after scope approval within the team; prefer minimal diff.
5. **Validate** — Existing contract tests + trigger-specific verification.
6. **Close or extend** — Return to stewardship when trigger resolved; update closeout docs if architecture changed materially.

---

## Cross-references

- Engineering closeout: [`CO108_recurrence_program_closeout.md`](CO108_recurrence_program_closeout.md)
- Boundary specification: [`CO108_engineering_boundary_specification.md`](CO108_engineering_boundary_specification.md)
- Stewardship guide: [`CO108_platform_stewardship_guide.md`](CO108_platform_stewardship_guide.md)
