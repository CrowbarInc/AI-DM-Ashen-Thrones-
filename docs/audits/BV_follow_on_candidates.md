# BV — Follow-On Maintenance Candidates

**Date:** 2026-06-21  
**Trigger:** BV1C classification **REDISTRIBUTED_COST** — hubs relocated, not eliminated.  
**Purpose:** Prioritize the next three maintenance-economics cycles with projected ROI and scorecard impact.

---

## BV2 — Final-Emission Meta Read-Side Consolidation

**Target hub:** `game/final_emission_meta` — FI **61/6**, **134** ownership refs, growing read-side coupling (+4 fan-in since BU).

| Item | Detail |
|---|---|
| **Problem** | Centralized schema/read interpretation absorbs writes from 20+ distributed modules; meta changes risk cross-surface replay/fallback/governance regressions. |
| **Scope** | Split read models by concern (fallback stamp vs replay lineage vs gate preflight meta); reduce cross-family imports; align with BK owner buckets without expanding write paths. |
| **Burden addressed** | Relocated read-side hub growth from BJ/BK; meta touched 3/10 post-BI commits. |
| **Projected ROI** | **Medium** — lowers blast radius on policy metadata edits; does not reduce fallback incidence directly. Estimated 15–25% reduction in meta-touch commit breadth based on BO locality patterns for scoped extractions. |
| **Expected scorecard impact** | Maintenance Economics **+0.5** (keep→marginal increase if successful); Maintenance Drag **+0.5**; Ownership Clarity **keep**; Operational Simplicity **+0.5** |
| **Risk** | Partial split recreates smear if boundaries unclear; requires registry/matrix updates. |
| **Success metric** | Meta fan-in stable or down after split; attribution strict completeness unchanged or up; zero fallback incidence regression. |

---

## BV3 — Fallback Observe-Route Incidence Reduction

**Target hub:** `game/final_emission_visibility_fallback` + observe-route corpus (**95.45%** trigger rate, 38/74 selection-owner events).

| Item | Detail |
|---|---|
| **Problem** | Fallback incidence **unchanged** at 69.16%; referential clarity dominates (51%); observe route is the highest-leverage hotspot. Relocation named owners but did not reduce triggers. |
| **Scope** | Target referential-clarity upstream preparation on observe turns; reduce hard-replacement triggers without removing fallback paths; close 13 unbucketed owner-bucket events. |
| **Burden addressed** | Measured runtime fallback volume — the largest **unchanged** cost center in BV1B. |
| **Projected ROI** | **High** if trigger rate drops ≥10 pp on corpus — directly improves fallback maintenance economics score (currently **62.0** burden, `high` classification). |
| **Expected scorecard impact** | Maintenance Economics **+1**; Maintenance Drag **+1**; Ownership Clarity **+0.5** (bucket closure); Operational Simplicity **keep** |
| **Risk** | Behavior change vs measurement-only prior cycles; requires protected replay validation. |
| **Success metric** | Second longitudinal snapshot shows **improving** trend; observe route rate <85%; owner-bucket gaps ≤5 events. |

---

## BV4 — Test Governance Facade Decomposition

**Target hubs:** `tests.helpers.emission_smoke_assertions` (**70** fan-in), `tests.test_ownership_registry` (**57** fan-out, **320** refs, 5/10 post-BI commits).

| Item | Detail |
|---|---|
| **Problem** | Largest measured fan-in node is a test facade; governance registry is the largest fan-out router. Together they concentrate test coupling displaced from the gate monolith. |
| **Scope** | Shard smoke facade by concern (gate preflight vs fallback vs replay projection adapters); split registry scans into domain-scoped assertion modules with shared contract core; preserve CI markers. |
| **Burden addressed** | Test-side redistribution hubs from BJ/BM/BU; reduces cascading test updates on single-module edits. |
| **Projected ROI** | **Medium-high** — test churn reduction; no direct fallback incidence impact. Aligns with BO recommendation to target helper decomposition. |
| **Expected scorecard impact** | Maintenance Drag **+1**; Maintenance Economics **+0.5**; Ownership Clarity **keep**; Operational Simplicity **+0.5** |
| **Risk** | Import churn across 69+ test consumers; temporary drag during migration. |
| **Success metric** | No single test helper FI >35; registry fan-out <40; post-cycle governance commit median files <25. |

---

## Priority ordering

| Rank | Cycle | Rationale |
|---:|---|---|
| 1 | **BV3** | Only candidate targeting **measured unchanged burden** (incidence rate) |
| 2 | **BV4** | Addresses **largest fan-in node** in ecosystem (smoke facade 70) |
| 3 | **BV2** | Addresses **fastest-growing production read hub** (meta +4 FI) |

---

## Deferred (not top-3)

| Surface | Why deferred |
|---|---|
| `final_emission_terminal_pipeline` (26/13) | Legitimate BJ owner; cross-cutting but fewer post-BI touches than meta/visibility |
| `final_emission_replay_projection` | Import-bounded; speaker recurrence may resolve via BV3 upstream fixes |
| Runtime megamodules (`interaction_context`, `api`, `gm`) | Outside BI–BM scope; BO-identified but not redistribution artifacts |

---

## Evidence

| Source | Role |
|---|---|
| [BV1C_hub_migration_analysis.md](BV1C_hub_migration_analysis.md) | Hub categories A–D |
| [BV1A_maintenance_hotspots.md](BV1A_maintenance_hotspots.md) | Post-BI touch ranks |
| [BV1B_fallback_baseline_comparison.md](BV1B_fallback_baseline_comparison.md) | Incidence stable |
| `artifacts/golden_replay/fallback_maintenance_economics_summary.json` | Burden score 62.0 |
