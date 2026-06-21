# BV3F — Reduction Validation

**Date:** 2026-06-21  
**Goal:** Confirm BV3E produces measurable replay-derived reduction in `referential_clarity_hard_replacement`, not simulation-only projection.  
**Authority:** `artifacts/bv3f_reduction_metrics.json`, post-refresh metric re-runs.

---

## Commands executed

```bash
python tools/bv3f_replay_corpus_refresh.py --hygiene-batches 30
python tools/bv3a_referential_clarity_metrics.py
python tools/bv3d_eligibility_report.py
python tools/bv1b_fallback_incidence_validation.py
python tools/bv3e_eligibility_metrics.py
python tools/bv3f_reduction_metrics.py
```

---

## Comparison table

| Metric | BV3D | BV3E Projection | Actual | Delta (Actual − Projection) |
|---|---:|---:|---:|---:|
| Eligible turns | 1 | 12 | **11** | −1 |
| Repairs applied | 1 | 12 | **11**¹ | −1 |
| Repair success rate | 9.1% | 100% | **100%**² | 0 |
| Referential clarity hard replacements | 12 | **1** | **1** | **0** |
| Observe-route rate | 52.17% | 4.35%³ | **47.83%** | +43.48 pp |
| Fallback incidence | 46.39% | — | **11.58%** | — |

¹ **11** upstream repairs applied per `bv3d_eligibility_report.json` (10 BV3E replay + 1 positive-control fixture). BV3E-specific stamp count: 10.  
² On BV3E-eligible shapes: 10/10 success (`bv3e_repair_success_count`).  
³ Projection assumes all 11 simulated repairs avoid observe-route fallback entirely; actual corpus still records sealed passive-scene fallbacks on repaired-adjacent turns.

---

## Delta vs BV3D frozen baseline

| Metric | BV3D | Actual | Delta |
|---|---:|---:|---:|
| Eligible turns | 1 | 11 | **+10** |
| Repairs applied | 1 | 11 | **+10** |
| Referential clarity hard replacements | 12 | 1 | **−11** |
| Observe-route rate | 52.17% | 47.83% | −4.34 pp |
| Fallback incidence | 46.39% | 11.58% | −34.81 pp |
| Observe fallback events | 12 | 11 | −1 |

---

## Primary discriminator

**`referential_clarity_hard_replacement`:** projected **−11**, actual **−11**. Projection convergence on the primary BV3 discriminator is **exact**.

Replay refresh confirms BV3E repair activation on production-shaped observe turns. Frozen-FEM simulation (`pre_refresh.bv3e_shape_simulation.json`) and post-refresh FEM stamps converge on eligibility and hard-replacement avoidance for the MV-01 exact-alias introducer cluster.

---

## Secondary signals

| Signal | Result |
|---|---|
| `referential_clarity_bv3e_repair_mode` stamped on replay FEM | **10/10** replay-only eligible |
| Replay-only eligible count | **0 → 10** |
| Repair activation rate (all observe) | 4.35% → **47.83%** |
| Unrepaired violation turns (observe) | 12 → **1** |
| Scene-opening fallback (repo-wide) | 30 → **0** (corpus refresh; non-observe route) |

---

## Interpretation

BV3E delivers the projected **−11** reduction in `referential_clarity_hard_replacement` events on replay-derived metrics. Observe-route rate did **not** fall to the optimistic projection because remaining observe fallbacks now classify primarily as `sealed_passive_scene_pressure_fallback` (10 events) rather than attribution hard replace — a partial lineage reclassification, not a simulation artifact.

Overall fallback incidence fell sharply (46.39% → 11.58%) due to corpus refresh removing stale scene-opening FEM and BV3E eliminating RC hard replace on the dominant violation cluster.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv3f_reduction_metrics.json` | Aggregated comparison authority |
| `artifacts/bv3f_replay_refresh/pre_refresh.*` | Frozen BV3D/BV3E baselines |
| `artifacts/bv3e_eligibility_metrics.json` | Post-expansion eligibility |
| `artifacts/bv3a_referential_clarity_metrics.json` | RC incidence |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Fallback incidence |
