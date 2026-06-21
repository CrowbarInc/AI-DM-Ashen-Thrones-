# BV17C — Before / After Scorecard

**Date:** 2026-06-21  
**Program:** BV2–BV17 contraction  
**Program start baseline:** BV1 / pre-BV2 (`docs/audits/BV1_maintenance_cost_matrix.md`)  
**Program end baseline:** BV17 post-BV16C (`docs/audits/BV17_hotspot_inventory.md`)

---

## Scorecard

| Metric | Program start | Program end | Delta |
| --- | ---: | ---: | ---: |
| **Fallback incidence** | 69.16% (74/107 FEM) | 1.05% (1/95) | **−68.11 pp** |
| **Observe route rate** | 95.45% | 4.35% | **−91.1 pp** |
| **Fallback events (corpus)** | 74 | 1 | **−73** |
| **Ownerless fallback events** | 13 | 0 | **−13** |
| **Recurrence row count** | 11 | 4 | **−7** |
| **Recurring keys** | 1 | 0 | **−1** |
| **Recurrence dominant share** | 0.7273 | 0.25 | **−0.48** |
| **Top hotspot FI** | 73 (`emission_smoke_assertions`) | 56 (`replay_fem_read_smoke`, governed) | −17; **reclassified** |
| **Top-1 FI share** | ~8.7% | 5.1% | **−3.6 pp** |
| **Top-5 FI share** | ~32.8% | 18.9% | **−13.9 pp** |
| **Accidental hub count (top 25)** | ≥4 (smoke, text, social, read cluster) | **0** | **−4+** |
| **Governed authority count (top 25)** | 0 | **9** | **+9** |
| **Legitimate authority count (top 25)** | mixed / unlabeled | **8** | explicit |
| **Compat shim FI total** | ~200+ (combined bridges) | **18** | **−182+** |
| **`final_emission_meta` FI** | 61 | 24 | **−37 (−61%)** |
| **Read authority cluster FI** | 70 (BV11 pre-BV10) | 19 | **−51 (−73%)** |
| **Smoke compat bridge FI** | 95 (BV11) | 2 | **−93** |
| **Text compat barrel FI** | 52 | 4 | **−48** |
| **Social compat barrel FI** | 52 | 12 | **−40** |
| **Terminal pipeline FI** | 26 | 11 | **−15 (−58%)** |
| **Gate orchestration FI** | 28–30 | 30 | ~0 (stable legitimate owner) |
| **Emission smoke monolith FI** | 73 | 15 | **−58 (−79%)** |
| **Ownership registry FO** | 57 | 57 | 0 (intentional) |
| **Governance collectors (`collect_*`)** | lower | 114 | expanded lock surface |
| **Gate thin boundary lock lines** | lower | 929 | expanded boundary docs |
| **Bug-fix locality cohort** | N = 0 | N = 0 | unobserved |
| **Attribution owner-bucket coverage** | 38.78% | 38.78% (BS unchanged) | 0 pp |

---

## Qualitative scorecard

| Dimension | Program start | Program end |
| --- | --- | --- |
| **Hub shape** | Accidental monoliths and bridge barrels | Authority-shaped, domain-owned |
| **Maintenance driver** | Fallback incidence + smoke/text/social routers | Residual legitimate authorities + test infra |
| **Regrowth risk** | Ungoverned import paths | Import guards + FI caps on all compat barrels |
| **Next-cycle driver** | Hotspot retirement queue (BV12–BV16) | **None required** — optional polish only |

---

## Program grade

| Area | Start | End | Grade |
| --- | --- | --- | --- |
| Runtime fallback economics | Critical drag | Collapsed | **A** |
| Hub retirement | Multiple accidental hubs | Zero in top 25 | **A** |
| Authority legibility | Mixed / accidental | Governed + named | **A** |
| Fan-in redistribution | N/A | Intentional domain hubs | **B+** (FI moved, not deleted) |
| Attribution completeness | 38.78% | 38.78% | **C** (unchanged gap) |
| Bug-fix locality evidence | Unobserved | Unobserved | **Incomplete** |

**Overall program outcome:** **SUCCESS** — primary contraction objectives met; residual gaps are **non-hotspot** and **optional**.

---

## Evidence

| Source | Role |
| --- | --- |
| `docs/audits/BV1_maintenance_cost_matrix.md` | Start column |
| `docs/audits/BV5_maintenance_cost_matrix.md` | Mid-program fallback confirmation |
| `docs/audits/BV11_hotspot_inventory.md` | Pre-BV12 decomposition peak |
| `docs/audits/BV17_concentration_rankings.md` | End-state top 25 |
| `artifacts/bv1b_fallback_summary.json` | End fallback incidence |
| `artifacts/bv8a_recurrence_history.json` | Recurrence metrics |
