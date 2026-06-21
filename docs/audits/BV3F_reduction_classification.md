# BV3F — Reduction Classification

**Date:** 2026-06-21  
**Question:** Did BV3E achieve effective incidence reduction, or did fallback burden relocate across families?  
**Authority:** `artifacts/bv3f_reduction_metrics.json`, `artifacts/golden_replay/bv1b_fallback_incidence_report.json`.

---

## Classification

## **`EFFECTIVE_REDUCTION`**

Primary BV3 discriminator met on replay-derived metrics: `referential_clarity_hard_replacement` decreased **−11** (12 → 1), matching BV3E projection exactly. Repair activation increased **1 → 11** with **100%** success on BV3E-eligible shapes.

---

## Reduction vs relocation analysis

### Primary metric — referential clarity hard replacement

| Check | BV3D | Actual | Verdict |
|---|---:|---:|---|
| Replacement count decreased | 12 | **1** | **PASS** (−11) |
| Repair activation increased | 1 | **11** | **PASS** |
| Projection convergence | −11 projected | **−11 actual** | **PASS** |

This is **not** a simulation-only result. Post-refresh FEM carries `referential_clarity_bv3e_repair_mode=exact_alias_introducer` on 10 replay turns.

### Fallback incidence

| Check | BV3D | Actual | Verdict |
|---|---:|---:|---|
| Overall fallback count decreased | 45 events | **11 events** | **PASS** |
| Overall fallback rate decreased | 46.39% | **11.58%** | **PASS** |
| Observe fallback turns decreased | 12 | **11** | **PASS** (marginal) |

### Compensating family increase (relocation watch)

| Family | BV3D (observe lineage) | Actual (observe lineage) | Delta | Assessment |
|---|---:|---:|---:|---|
| `referential_clarity_hard_replacement` | 12 | **1** | **−11** | Real reduction |
| `sealed_passive_scene_pressure_fallback` | 1 | **10** | **+9** | Lineage reclassification on turns where RC hard replace was avoided but sealed passive-scene path still fires |
| `scene_opening` | 0 (observe) | 0 | 0 | N/A on observe |
| `minimal_social_emergency_fallback` | — | 0 | — | No compensating increase |

**Relocation verdict:** Partial lineage reclassification observed. Nine observe events shifted from RC attribution hard replace to sealed passive-scene lineage. However:

- Total observe fallback turns still decreased (12 → 11).
- No increase in scene-opening or diagnostics families.
- RC event count dropped by the full projected amount.

This pattern is **effective reduction on the BV3 primary discriminator**, not pure ownership relabeling (BV3B failure mode) and not zero change.

---

## Classification criteria mapping

| Criterion | Threshold | Result |
|---|---|---|
| RC hard replacement delta | ≤ −8 | **−11** ✓ |
| Repair applied vs projection | ≥ 80% of projected | **11/12 = 92%** ✓ |
| Fallback count decreased | Required | **45 → 11** ✓ |
| Compensating dominant-family increase | Must not offset RC reduction | Sealed +9 but RC −11; net observe −1 ✓ |

Would **not** qualify as `NO_MEASURABLE_CHANGE` (BV3B) — upstream repair stamps are now observable on replay FEM. Would **not** qualify as pure relocation — RC events genuinely eliminated, not renamed in place at stable counts.

---

## Residual risk

Observe-route rate remains **47.83%** because sealed passive-scene fallbacks dominate the remaining observe burden (10/11 events). BV3E addressed the attribution trigger cluster; sealed content selection remains the next cost center (see BV4 recommendation).

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv3f_reduction_metrics.json` | Classification inputs |
| `artifacts/bv3a_referential_clarity_metrics.json` | RC + fallback kind counts |
| `artifacts/bv3f_replay_refresh/pre_refresh.bv3e_shape_simulation.json` | Pre-refresh projection |
