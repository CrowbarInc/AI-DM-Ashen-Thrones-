# BV5 — Fallback Burden Comparison (BV1B vs BV3F vs BV4B)

**Date:** 2026-06-21  
**Question:** Did BV3 and BV4 reduce fallback maintenance burden, or relocate it across families?  
**Authority:** `artifacts/golden_replay/bv1b_fallback_incidence_report.json`, `artifacts/bv3f_reduction_metrics.json`, `artifacts/bv4b_concrete_beat_metrics.json`, `artifacts/golden_replay/fallback_incidence_history.json`.

---

## Executive answer

Fallback burden **was reduced**, not merely relocated, on the **BV3D measurement corpus lineage**:

- **BV3F:** RC hard replacement **−11** events; total incidence **46.39% → 11.58%** (BV3D scope).
- **BV4B:** PSP cluster **10 → 0** via upstream concrete-beat satisfier; incidence **11.58% → 1.05%**; observe route **47.83% → 4.35%**.

Partial reclassification (RC avoided → PSP) occurred at BV3F but **net observe turns still fell**. BV4B **eliminated** the compensating PSP family without introducing a new dominant family.

**Corpus caveat:** BV1B used **107 FEM**; BV3F/BV4B use **95 FEM (BV3D filtered)**. Cross-scope deltas are directional, not strict longitudinal continuations.

---

## Comparison table

| Metric | BV1B | BV3F | BV4B (BV5 current) | BV1B → BV4B delta |
|---|---:|---:|---:|---:|
| **Measurement scope** | 107 FEM (artifact scan) | 95 FEM (BV3D) | 95 FEM (BV3D) | Scope changed |
| **Eligible turns** | 107 | 95 | 95 | −12 |
| **Fallback events** | 74 | 11 | **1** | **−73** |
| **Fallback incidence** | **69.16%** | **11.58%** | **1.05%** | **−68.11 pp** |
| **Observe-route rate** | **95.45%** (42/44) | **47.83%** (11/23) | **4.35%** (1/23) | **−91.10 pp** |
| **Ownerless count** | **13** | **0** | **0** | **−13** |
| **Owner-bucket coverage** | 61/74 (82.4%) | 11/11 (100%) | 1/1 (100%) | +17.6 pp |
| **Selection-owner coverage** | 70/74 | 11/11 | 1/1 | Complete on corpus |
| **Dominant family (events)** | `referential_clarity_hard_replacement` **38** (51%) | `sealed_passive_scene_pressure_fallback` **10** (90.9%) | `referential_clarity_hard_replacement` **1** (100%) | Family dominance **rotated then collapsed** |
| **Dominant family share** | 51.4% | 90.9% | 100% | Concentration on **1 residual event** |
| **Second family** | `scene_opening` 31 (42%) | RC hard replace **1** (9.1%) | — | Scene-opening **0** on BV3D corpus |
| **PSP events** | 1 | 10 | **0** | **−1 → −10** net elimination at BV4B |

---

## Phase deltas (like-for-like BV3D corpus)

| Metric | BV3F | BV4B | BV3F → BV4B Δ |
|---|---:|---:|---:|
| Fallback incidence | 11.58% | 1.05% | **−10.53 pp** |
| Observe-route rate | 47.83% | 4.35% | **−43.48 pp** |
| PSP events | 10 | 0 | **−10** |
| RC hard replace | 1 | 1 | 0 |
| Satisfier applied (observe) | — | 10 | BV4B upstream beat injection |

---

## Family trajectory

```
BV1B (107 FEM):  RC ██████████████████████████████████████ 38
                 SO ███████████████████████████████ 31
                 RT ████ 4
                 PSP █ 1

BV3F (95 FEM):   PSP ██████████ 10
                 RC █ 1

BV4B (95 FEM):   RC █ 1
                 PSP (none)
```

---

## Relocation vs reduction analysis

| Check | BV3F | BV4B | Verdict |
|---|---|---|---|
| Total fallback events decreased | 45 → 11 (vs BV3D baseline) | 11 → 1 | **Reduction** |
| Compensating family offset RC drop | PSP +9 vs BV3D observe lineage | PSP **eliminated** | BV3F partial reclass; BV4B **no offset** |
| Observe turns with fallback decreased | 12 → 11 (BV3D → BV3F) | 11 → 1 | **Reduction** |
| Router fan-in (`visibility_fallback`) | 17 → 17 | 17 → 17 | Path **stable**; volume **down** |
| New runtime modules for satisfier | BV3E repair stamps | `passive_scene_pressure` + gate/terminal hooks | **Bounded new surface** vs eliminated trigger volume |

**Classification:** **EFFECTIVE_REDUCTION** on both BV3F (RC primary discriminator) and BV4B (PSP cluster). Not pure **REDISTRIBUTED_COST** at BV4B — PSP events **removed**, not renamed at stable counts.

---

## Residual burden

| Item | Count | Maintenance implication |
|---|---:|---|
| RC hard-replacement observe fallback | **1** | Residual multi-entity / non-introducer shape (BV4 candidate BV4B-RC expansion) |
| Scene-opening route on BV3D corpus | **0** | Not active on filtered corpus |
| Ownerless events | **0** | BK/BU stamping objective **met** on current scan |
| Gate lineage label default | 1/1 events `event_owner=gate` | Measurement hygiene (BV4C deferred) |

---

## Longitudinal snapshot status

| Snapshot pair | Trend | Notes |
|---|---|---|
| BV1 → BV1B (107 FEM) | **Stable** (0.00 pp) | Pre-BV3 frozen baseline |
| BV3B refresh (200 FEM) | Corpus break | Not comparable to 107 FEM without normalization |
| BV3F → BV4B (95 FEM) | **Improving** | **−10.53 pp** incidence; legitimate trend on active scope |

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/golden_replay/fallback_incidence_history.json` | Longitudinal snapshots |
| `artifacts/bv3f_reduction_metrics.json` | BV3F classification inputs |
| `artifacts/bv4b_concrete_beat_metrics.json` | BV4B comparison table |
| [BV3F_reduction_classification.md](BV3F_reduction_classification.md) | BV3F EFFECTIVE_REDUCTION |
| [BV4B_concrete_beat_report.md](BV4B_concrete_beat_report.md) | Satisfier verification |
