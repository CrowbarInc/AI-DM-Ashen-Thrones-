# CO109 — Foundation Engineering Playbook

**Date:** 2026-06-28  
**Scope:** Domain-agnostic methodology template derived from the recurrence program (CO99–CO108) and sibling foundation initiatives (CO96, BQ36).

**Purpose:** Provide a reusable lifecycle for future **foundation programs** — subsystems that establish platform capabilities (observability, governance, graduation, operational workflow) rather than product features.

**Not in scope:** Recurrence-specific implementation details. For recurrence stewardship, see [`CO108_platform_stewardship_guide.md`](CO108_platform_stewardship_guide.md).

---

## 1. Recommended lifecycle stages

```
┌─────────────┐   ┌────────────────┐   ┌─────────────┐   ┌─────────────┐
│  Discovery  │──►│ Implementation │──►│ Validation  │──►│ Convergence │
└─────────────┘   └────────────────┘   └─────────────┘   └─────────────┘
       │                  │                    │                  │
       ▼                  ▼                    ▼                  ▼
  Write-path audit    Narrow extraction    Live + unit tests   Governance classify
  Authority registry  Tooling              Idempotency         Zero unresolved work
  Gap inventory       Cascade wiring       Contract locks      Calibration ceiling
       │                  │                    │                  │
       └──────────────────┴────────────────────┴──────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
           ┌──────────────┐ ┌─────────────┐ ┌──────────┐
           │Operationalize│ │ Stewardship │ │ Closeout │
           └──────────────┘ └─────────────┘ └──────────┘
                    │               │               │
               Runbook          Recurring ops    Boundaries
               Automation audit  Artifact hygiene Re-entry criteria
               Deterministic docs               Archive (CO109)
```

### Stage definitions

| Stage | Goal | Entry criteria | Exit criteria |
|---|---|---|---|
| **Discovery** | Understand current state without changing behavior | Problem or subsystem identified | Write-path / authority audit complete; gaps classified |
| **Implementation** | Build minimal correct architecture | Discovery exit met | Core pipeline functional; modules owned |
| **Validation** | Prove pipeline under real conditions | Implementation exit met | Live path + unit tests pass; defects documented |
| **Convergence** | Resolve ambiguity; link evidence to outcomes | Validation exit met | All entities governance-classified; zero unresolved engineering |
| **Operationalization** | Make routine execution repeatable | Convergence exit met | Runbook + automation map + deterministic doc generation |
| **Stewardship** | Transfer to platform maintainers | Operationalization exit met | Recurring cadence documented; no engineering backlog |
| **Closeout** | Formally close engineering program | Stewardship model defined | Boundaries, re-entry criteria, final assessment published |
| **Archive** | Capture reusable patterns | Closeout complete | Retrospective + playbook (CO109-class cycle) |

---

## 2. Reusable engineering patterns

### 2.1 Discovery-first cycles

**Practice:** Begin with read-only audits (write-path, event source, taxonomy overlap) before any implementation cycle.

**Recurrence example:** BQ36 classified 43 events before commit-worthiness policy; CO103 inventory preceded propagation.

**Apply when:** Subsystem has persisted state, multiple writers, or unclear ownership.

**Deliverable template:** Audit doc with tables — caller inventory, contamination paths, policy recommendation, explicit non-goals.

---

### 2.2 Authority registry governance

**Practice:** Maintain a single registry document per taxonomy family listing: allowed values, owning module, consumers, and explicit "does not own" boundaries.

**Recurrence example:** [`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md) (CG-4).

**Apply when:** Overlapping status words, multiple modules importing constants, or frequent taxonomy drift.

**Rules:**
- Registry changes require explicit cycle scope.
- Separate **vocabulary authority** from **operational graduation authority**.
- Cross-reference closed sibling programs to prevent reopening.

---

### 2.3 Operational-before-architectural sequencing

**Practice:** Document and validate the operator workflow (runbook) before building advanced features (propagation, calibration tuning, new automation).

**Recurrence example:** CO100 runbook before CO104 retirement propagation.

**Apply when:** Evidence collection depends on human or CI execution paths.

**Anti-pattern:** Building propagation tools before operators can reliably produce commit-worthy events.

---

### 2.4 Narrow helper extraction

**Practice:** Split monolithic modules by ownership boundary (events, history, statistics, serialization) with a compatibility facade.

**Recurrence example:** `replay_bug_recurrence_events.py`, `_history.py`, `_statistics.py`, `_serialization.py` + facade.

**Apply when:** Audit repeatedly references "this module owns X but not Y" confusion.

**Caution:** Update **all tooling imports** when constants move (CO101 D1 lesson).

---

### 2.5 Parity locking (documentation contracts)

**Practice:** Contract tests assert generated or canonical docs contain required governance sections and path constants match code.

**Recurrence example:** `tests/test_recurrence_contract.py` (CO99/CO100 locks).

**Apply when:** Generated artifacts overwrite hand-authored governance sections.

**Minimum assertions:** Authority doc paths, program status strings, baseline section headers.

---

### 2.6 Behavioral regression validation

**Practice:** Opt-in or CI-gated end-to-end test exercising the full production cascade, not just unit tests of builders.

**Recurrence example:** CO102 live protected replay pipeline test.

**Apply when:** Multi-hook pipelines (pytest sessionfinish, file cascades) where unit tests miss integration gaps.

---

### 2.7 Deterministic documentation generation

**Practice:** Encode stable governance preamble in renderers; inject dynamic values from builder payload; never rely on manual post-regeneration edits.

**Recurrence example:** CO102 `render_recurrence_graduation_audit_governance_preamble_markdown()`.

**Apply when:** Artifacts regenerate frequently from operational triggers.

**Rule:** If it's governance-critical, it's **code-rendered**, not hand-maintained in generated files.

---

### 2.8 Retirement registry + propagation tool

**Practice:** Document fix disposition in a registry; propagate into machine-readable state via idempotent tool with evidence gate, dry-run, and `--check`.

**Recurrence example:** `tools/propagate_outcome_retirements.py` + BV8A/BX registries.

**Apply when:** Human audit trail exists but machine-readable history lacks outcome signals.

**Requirements:** Preserve chronology; no dedupe of historical events; idempotent re-run.

---

### 2.9 Governance classification before action

**Practice:** Classify every active entity (permanent design, duplicate, sentinel, retirement candidate) before propagation or metric chasing.

**Recurrence example:** CO106 — 5 permanent active keys excluded from propagation.

**Apply when:** Calibration metrics create pressure to "retire everything."

**Output:** Eligibility matrix with explicit blocking conditions.

---

### 2.10 Intentional gap acceptance

**Practice:** Document architectural constraints as **resolved decisions**, not backlog items.

**Recurrence example:** CO106 permanent keys; CO96 strict completeness 0%.

**Apply when:** Metrics imply unfinished work but governance intent says otherwise.

**Phrase:** "Not unfinished work" with supporting closeout reference.

---

### 2.11 Engineering closeout criteria

**Practice:** Closeout cycle produces: canonical summary, stewardship guide, boundary specification, re-entry criteria, final assessment.

**Recurrence example:** CO108 deliverable set (mirrors CO96 attribution closeout).

**Apply when:** Zero unresolved engineering on inventory; automation verified.

**Explicit statement:** Evidence-limited operational states are **not** engineering reopeners.

---

### 2.12 Calibration honesty under volume growth

**Practice:** Expect confidence scores to **drop** when fuller evidence reveals overconfidence. Treat as success of calibration, not regression.

**Recurrence example:** CO101 readiness 94.7 but calibration 55.0 after volume expansion.

**Apply when:** Early low-volume metrics look optimistic.

---

## 3. Cycle scoping template

Each foundation cycle should declare:

```markdown
# COxxx — [Title]

**Date:** YYYY-MM-DD
**Scope:** [What is in/out — prefer "documentation only" or narrow fix list]

**Prior cycles:** [Dependencies]

## Executive summary
[Verdict in one paragraph]

## Constraints (Do NOT)
- [Explicit non-goals]

## Validation
- [Commands run]
- [Pass/fail table]

## Recommended COxxx+1 target
[Single successor with clear type: operational vs engineering]
```

**Recurrence discipline:** Ten cycles (CO99–CO108) each with explicit constraints prevented scope creep.

---

## 4. Artifact hierarchy

| Tier | Purpose | Mutation rule |
|---|---|---|
| **Event log** | Source of truth for observations | Append via tooling only |
| **Aggregated history** | Derived analytics | Regenerated from log |
| **Graduation audits** | Human-readable decision support | Regenerated; governance preamble code-rendered |
| **Registry docs** | Vocabulary and retirement authority | Engineering cycles only |
| **Runbooks** | Operator procedure | Clarifications OK; new requirements need cycle |
| **Closeout docs** | Program boundary | Immutable after archive |

---

## 5. When NOT to use this playbook

| Situation | Prefer instead |
|---|---|
| Single product bug fix | Normal engineering + optional retirement registry |
| Feature with user-facing UI | Product development lifecycle |
| Metric tuning to force graduation | Rejected — violates evidence-based graduation |
| Reopening closed taxonomy without re-entry criteria | Governance violation |

---

## Cross-references

- Retrospective timeline: [`CO109_recurrence_engineering_retrospective.md`](CO109_recurrence_engineering_retrospective.md)
- Process assessment: [`CO109_process_improvement_assessment.md`](CO109_process_improvement_assessment.md)
- Attribution closeout template: [`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md)
