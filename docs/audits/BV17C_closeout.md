# BV17C — Contraction Program Closeout

**Date:** 2026-06-21  
**Program:** BV2–BV17 (meta authority reduction → post-contraction reassessment)  
**Status:** **CLOSED**  
**Repository mode:** **Maintenance Mode** (exited Contraction Mode)

---

## Mode transition

| Field | Value |
| --- | --- |
| **Status** | `REPOSITORY_CONTRACTION_COMPLETE` |
| **Classification** | `LEGITIMATE_AUTHORITY_DOMINANT` |
| **Comparison baseline** | **BV17C** (permanent) |
| **Prior mode** | Contraction Mode (BV2–BV17) |
| **Current mode** | **Maintenance Mode** |

### Protected metrics (BV17C baseline lock)

Future repository scans compare against these values. Breaches are **regressions**, not contraction triggers.

| Metric | Locked value |
| --- | ---: |
| Shim FI (accidental compat total) | **18** |
| Accidental hubs (top 25) | **0** |
| Fallback incidence (FEM corpus) | **1.05%** |
| Recurrence keys | **0** |
| Top-1 FI share | **5.1%** |

**Machine-readable baseline:** `artifacts/bv17_hotspot_analysis.json`

### Maintenance Mode rules

1. **Do not** create new BV contraction cycles.
2. Treat future **FI-cap violations** as regressions.
3. Treat **new accidental hubs** as defects.
4. Compare future repository scans against **BV17C**.
5. Future work must be justified by: **new functionality**, **new architecture goals**, **measurable regressions**, or **optional-register ROI** ([BV17C_optional_work.md](BV17C_optional_work.md)).

**Optional backlog (maintenance-positive, not required):** BV18A (visibility-fallback test seam migration), BV18E (residual RC event elimination).

---

## Final verdict

### **REPOSITORY_CONTRACTION_COMPLETE**

The BV2–BV17 contraction program **achieved its objectives**. Accidental hub concentration has been **eliminated**, fallback maintenance drag **collapsed**, and remaining high fan-in modules are **governed or legitimate authorities** with registry-enforced regrowth prevention.

**Future work is no longer driven by hotspot retirement.** It proceeds from **new functionality**, **product milestones**, or **isolated optional ROI** items in [BV17C_optional_work.md](BV17C_optional_work.md).

---

## What was achieved

| Objective | Outcome | Evidence |
| --- | --- | --- |
| Reduce fallback maintenance drag | Incidence **69% → 1%** | [BV17C_scorecard.md](BV17C_scorecard.md) |
| Retire accidental hubs | **0** in top 25 | [BV17C_authority_transition.md](BV17C_authority_transition.md) |
| Install governed domain owners | Smoke/text/social decomposed | BV12–BV14 closeouts |
| Preserve live orchestration | Gate + terminal centralized | BV15/BV16 validation |
| Prevent regrowth | Import guards + FI caps | Registry + BV12C–BV16C |
| Establish post-contraction baseline | BV17C metrics locked | [BV17C_program_metrics.md](BV17C_program_metrics.md) |

---

## Program arc

```text
BV2–BV4   Runtime economics (meta write, fallback incidence, passive scene)
BV7       Smoke monolith retirement
BV8A      Recurrence deduplication
BV10      Read-side authority closure
BV12–BV14 Compat bridge → domain authority migration (smoke, text, social)
BV15–BV16 Gate/terminal governance validation
BV17      Reassessment → REPOSITORY_CONTRACTION_COMPLETE
BV17C     Formal closeout + baseline establishment
```

---

## Lessons learned

### 1. Fan-in reduction ≠ maintenance reduction

Decomposition **moved** fan-in from compat barrels to domain authorities. Maintenance improved because **ownership became explicit**, not because total FI fell.

### 2. Measure incidence, not just imports

Fallback **69% → 1%** was the decisive economics win. Import-graph metrics alone would have missed the program's primary ROI.

### 3. Govern before decomposing further

BV12C–BV14C **import guards + FI caps** made redistribution stable. Without locks, domain hubs would have reverted to accidental bridge patterns (as seen post-BV10 smoke bridge growth).

### 4. Do not split live sequencers without boundary proof

BV15/BV16 validated that gate orchestration and terminal finalize sequencing are **legitimate centralized authorities**. Test-monkeypatch inflation was the problem — not the sequencer bodies.

### 5. Closeout requires reclassification audit

Top modules by FI at program end (`replay_fem_read_smoke`, `text_formatting`) look like hotspots by number alone. **Authority classification** (BV17) proved they are **governed**, not accidental.

### 6. Bug-fix locality remains unobserved

Zero post-BI corrective commits means **locality improvement is structural, not empirically validated** in commit history. This does not block closeout but limits confidence on edit-spread claims.

---

## Future guidance

### Do

- Compare future scans against **BV17C baselines** (top-1 share 5.1%, shim FI 18, 0 accidental hubs).
- Route new emission/text/social work through **existing domain authorities**.
- Treat **compat barrel FI cap failures** as regressions requiring immediate fix.
- Consult [BV17C_optional_work.md](BV17C_optional_work.md) for opportunistic polish only.

### Do not

- Schedule standing BV cycles for hub retirement without cap breach or new accidental hub in top 10.
- Split gate, terminal, or stack sequencers without acyclic boundary proof.
- Re-merge domain hubs into compat barrels for convenience imports.
- Use raw top-N FI alone to justify decomposition — **classify authority first**.

### Regression triggers (investigate, not auto-cycle)

| Trigger | Action |
| --- | --- |
| Compat barrel FI exceeds cap | Fix import routing; do not raise cap |
| Accidental hub appears in top 10 | Classify; apply BV12–BV16 pattern if confirmed |
| Fallback incidence >5% on FEM corpus | Investigate runtime — not structural by default |
| Recurring keys >0 with dominant share >0.5 | Review BV8A retirement registry |

---

## Closeout package index

| Document | Purpose |
| --- | --- |
| [BV17C_program_metrics.md](BV17C_program_metrics.md) | Full metrics rollup |
| [BV17C_scorecard.md](BV17C_scorecard.md) | Before / after scorecard |
| [BV17C_authority_transition.md](BV17C_authority_transition.md) | Retired vs retained authorities |
| [BV17C_maintenance_economics.md](BV17C_maintenance_economics.md) | Economics vs BV5 |
| [BV17C_repository_state.md](BV17C_repository_state.md) | LEGITIMATE_AUTHORITY_DOMINANT rationale |
| [BV17C_optional_work.md](BV17C_optional_work.md) | Optional / deferred register |
| [BV17_hotspot_inventory.md](BV17_hotspot_inventory.md) | Post-contraction measurement |
| `artifacts/bv17_hotspot_analysis.json` | Machine-readable baseline |

---

## Sign-off criteria

| Criterion | Met? |
| --- | --- |
| Program metrics documented | ✓ |
| Before/after scorecard published | ✓ |
| Authority transition summarized | ✓ |
| Maintenance economics finalized vs BV5 | ✓ |
| Repository state classified | ✓ |
| Optional work registered | ✓ |
| Formal closeout issued | ✓ |

**Program status:** **CLOSED**  
**Repository mode:** **Maintenance Mode**  
**Next structural cycle:** **None required**  
**Post-contraction baseline:** **BV17C / BV17 measurement (2026-06-21)**
