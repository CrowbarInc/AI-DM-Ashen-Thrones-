# BV5 — Maintenance Cost Matrix (Refresh)

**Date:** 2026-06-21  
**Scope:** Rebuild of [BV1C_maintenance_cost_matrix.md](BV1C_maintenance_cost_matrix.md) after BV2, BV3, BV4B.  
**Method:** BU AST scan (628 files, 220 modules), BV1A locality re-run, BV1B incidence re-run, BV4B metrics, BS attribution artifacts (unchanged).

---

## Executive verdict

BV2–BV4 **demonstrated measured maintenance reduction** on the dominant BV1C cost center (fallback incidence) and **structural reduction** on meta write coupling. **Redistribution persists** in meta read facades, terminal pipeline convergence, and test smoke/registry hubs. Bug-fix locality **remains unobserved** (N = 0).

**BV5 matrix classification:** **REDUCED_COST** on runtime fallback + meta core; **REDISTRIBUTED_COST** residual on read facades and tests.

---

## Integrated area matrix

| Area | Pre-BV state (BV1C) | Current state (BV5) | Ownership | Fan-in | Fan-out | Hotspot count | Bug-fix locality | Fallback impact | Net result |
|---|---|---|---|---:|---:|---:|---|---|---|
| **Replay** | Area FI **86**; `golden_replay_projection` **18/7**; `final_emission_replay_projection` **15/4**; speaker recurrence **8** rows | `golden_replay_projection` **14/6** (−4 FI); `final_emission_replay_projection` **15/5**; recurrence **8** unchanged | Replay projection owner stable; golden adapter lighter | **86** (area est.) | **80** (area est.) | **3** | **Unchanged / unobserved** | **Reduced trigger volume** — fallback projection tests touch fewer live events | **Improved observability, reduced fallback drag** |
| **Fallback** | FI **103**; `visibility_fallback` **17/17**; incidence **69.16%**; observe **95.45%**; 13 ownerless | `visibility_fallback` **17/18**; incidence **1.05%**; observe **4.35%**; 0 ownerless | BK owners on **1/1** events; selection/content stamped | **103** (area est.) | **193** (area est.) | **12 → ~4 active** (volume collapse) | **Unchanged / unobserved** | **Measured reduction** — events 74 → 1 (cross-scope); BV3D lineage 11 → 1 | **Reduced** (primary BV5 win) |
| **Attribution** | Owner bucket **38.78%**; FI **75**; strict completeness **0%** | Unchanged BS metrics; FI **75** est. | BS3 contract **100%** compliance | **75** | **53** | **4** | **Unchanged / unobserved** | Indirect — fallback events carry full stamps | **Improved legibility, unchanged completeness gap** |
| **Final emission** | Gate **28/7**; meta **61/6**; terminal **26/13**; area FI **443** | Gate **30/9**; meta **24/8**; meta_read **28/1**; bucket_views **22/1**; terminal **26/14**; `passive_scene_pressure` new | BJ owners + BV2 facades + BV4B satisfier | **443** (area est.) | **218** (area est.) | **8 → 9** (+PSP module) | **Unchanged / unobserved** | Gate hooks for satisfier (+2 FI); meta **−37 FI** | **Mixed — meta core reduced; read facades added** |
| **Speaker finalize** | Enforcement **15/4**; finalize **11/8**; area FI **80** | **15/4** unchanged; finalize **11/8**; terminal **26/14** | Split enforcement vs adoption; shared terminal hub | **80** | **125** | **2** | **Unchanged / unobserved** | **1** RC observe fallback touches visibility/sealed path | **Unchanged drag** |
| **Ownership governance** | Registry **57** FO; BU20–BU30 CI closed | Registry **57** FO unchanged | Self-maintaining matrix contract | **0** | **57** | **4** | **Unchanged / unobserved** | Ownerless **0** on current scan | **Improved runtime stamping; registry hub unchanged** |
| **Tests** | Smoke **70/5**; registry **57** FO; gate stub **19 LOC** | Smoke **73/5**; registry **57** FO; BV4B tests added | Facades intentional; BV4 decomposition **not shipped** | **73** (smoke) | **57** (registry) | **6** | **Unchanged / unobserved** | Fallback test suites still present; fewer live fallback cases to debug | **Shifted + slight FI increase** |

---

## Maintenance burden accounting (BV2–BV4)

| Program | Burden removed | Burden relocated | Burden unchanged | Structural simplification? | Measured maintenance reduction? |
|---|---|---|---|---|---|
| **BV2 meta consolidation** | Direct meta imports **−37** (61→24) | meta_read **+28** FI; bucket_views **+22** FI | Terminal pipeline; gate | **Yes** — typed read/write split | **Partial** — core meta edits narrower |
| **BV3E RC repair** | RC hard replace **−11** events | Partial PSP reclass (+9 at BV3F) | Visibility router FI | **Yes** — upstream repair before fallback | **Yes** — incidence **46%→12%** on BV3D |
| **BV4B concrete beat** | PSP **−10** events; observe **−43.48 pp** | Gate/terminal/PSP module hooks (+2 gate FI) | 1 RC residual | **Yes** — upstream satisfier | **Yes** — incidence **12%→1%** |
| **BV4 test facade (planned)** | — | — | Smoke **70→73** | **No** | **No** — not executed |

---

## Net result summary

| Net label | Areas |
|---|---|
| **Reduced (measured)** | Fallback incidence; observe-route volume; meta write fan-in; runtime ownerless gaps |
| **Reduced (structural, scoped)** | Golden replay adapter fan-in; gate LOC (unchanged) |
| **Improved legibility** | Meta read facades; BV4B satisfier instrumentation; fallback ownership stamping |
| **Shifted / relocated** | Meta read imports; test smoke facade; terminal pipeline convergence |
| **Unchanged (measured)** | Bug-fix locality; speaker recurrence (8 rows); attribution owner bucket **38.78%**; registry fan-out **57** |

---

## Classification review (Task 5)

### Question

Does evidence support upgrading BV1C **REDISTRIBUTED_COST** to **REDUCED_COST**?

| Classification | Evidence | Supports | Contradicts | Confidence |
|---|---|---|---|---|
| **REDUCED_COST** | Fallback incidence **69.16% → 1.05%** (active lineage); PSP **eliminated**; meta core FI **−64%**; ownerless **13 → 0** | Dominant BV1C drag center addressed with measured outcomes | — | **High** on fallback; **Medium** repo-wide |
| **REDISTRIBUTED_COST** | Meta ecosystem imports **61 → 74**; smoke FI **+3**; gate FI **+2**; new PSP module | Residual hub pattern | Fallback volume collapse | **Medium** (secondary surfaces) |
| **MIXED_OR_INCONCLUSIVE** | Bug-fix N = **0**; attribution unchanged; corpus scope **107 → 95 FEM**; recurrence retirement **0** validated outcomes | Uncertainty bounds | Does not overturn fallback measurement | **Medium** as umbrella label |

### BV5 decision

**Primary classification: REDUCED_COST**

Rationale: BV1C's decisive contradictor was **unchanged 69.16% fallback incidence**. BV3F + BV4B **removed that contradictor** with event-level evidence (not relabeling at stable totals). Residual redistribution on meta read facades and tests **does not offset** a **>90%** fallback trigger reduction on the active corpus.

**Secondary qualifier:** Residual **REDISTRIBUTED_COST** on meta read facades and test governance until BV4 facade cycle or equivalent ships.

**Confidence:** **Medium-high** — strong fallback metrics; bounded by corpus scope change and absent bug-fix cohort.

---

## Scorecard recommendation (Task 6)

Baseline: [BV1C_scorecard_recommendation.md](BV1C_scorecard_recommendation.md) (BO **5/10** economics, ownership **7→8**).

| Dimension | BV1C action | BV5 recommendation | Δ | Rationale |
|---|---|---|---|---|
| **Maintenance Economics** | Keep **5/10** | **Increase → 6/10** | **+1** | Measured fallback reduction + meta core FI drop; offset by test smoke + meta facade sprawl |
| **Maintenance Drag** | Keep **5–6/10** | **Increase → 7/10** | **+1** | Fallback debugging drag collapsed; observe route **4.35%**; speaker recurrence + smoke facade persist |
| **Ownership Clarity** | Increase **7→8** | **Keep 8/10** | 0 | Runtime ownerless **0**; attribution field gaps unchanged; registry unchanged |
| **Operational Simplicity (Operability)** | Keep | **Keep** | 0 | More modules (220); clearer meta facades; satisfier adds operator meta fields |

### Scorecard action table

| Dimension | Action | Confidence | Primary evidence |
|---|---|---|---|
| Maintenance Economics | **Increase +1** | Medium-high | BV5 fallback comparison; meta FI −37 |
| Maintenance Drag | **Increase +1** | Medium-high | Incidence 1.05%; observe 4.35% |
| Ownership Clarity | **Keep 8** | High | 0 ownerless; BS contract 100% |
| Operational Simplicity | **Keep** | Medium | Facade breadth vs simpler fallback ops |

---

## Evidence

| Source | Role |
|---|---|
| [BV1C_maintenance_cost_matrix.md](BV1C_maintenance_cost_matrix.md) | Prior matrix |
| [BV5_scorecard_revalidation.md](BV5_scorecard_revalidation.md) | Hub FI table |
| [BV5_fallback_burden_comparison.md](BV5_fallback_burden_comparison.md) | Phase comparison |
| `docs/audits/BU_import_fan_in_fan_out.csv` | Current coupling |
| `artifacts/bv4b_concrete_beat_metrics.json` | BV4B metrics |
