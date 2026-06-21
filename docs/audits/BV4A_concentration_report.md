# BV4A — Passive Scene Pressure Concentration Report

**Date:** 2026-06-21  
**Corpus:** Post-BV3F refresh, BV3D measurement scope (95 FEM / 10 PSP events).  
**Authority:** `artifacts/bv4a_passive_scene_inventory.json`, `artifacts/golden_replay/bv1b_fallback_incidence_report.json`

---

## Executive summary

Passive-scene sealed fallback incidence is **maximally concentrated** on the current corpus: one trigger class, one upstream text shape, one emitted template, one selection owner, one route. The **smallest set of causes responsible for most fallbacks** is a **single root cause** — upstream observe narration missing concrete interaction under passive-scene pressure.

---

## Owner concentration

| Owner / module | Events | Share of PSP | Share of all observe fallbacks |
|---|---:|---:|---:|
| **Selection:** `game.final_emission_gate` | 10 | 100% | 90.9% |
| **Content:** `game.final_emission_sealed_fallback` | 10 | 100% | 90.9% |
| **Bucket:** `sealed-gate` | 10 | 100% | 90.9% |
| **Realization:** `gate_terminal_repair` | 10 | 100% | 90.9% |
| Visibility selection owner | 0 | 0% | — |

**Herfindahl index (selection owner):** 1.0 — complete concentration on gate hub label.

**Interpretation:** All passive-scene events present as gate-terminal sealed repairs. Visibility/passive-scene module owns the candidate logic (`final_emission_passive_scene_pressure.py`) but selection owner stamping routes through gate — same packaging distortion BV3 Phase 1 identified for RC events.

---

## Route concentration

| Route | PSP events | Observe turns | PSP / observe turns | Observe fallback share |
|---|---:|---:|---:|---:|
| **observe** | **10** | 23 | 43.5% | 90.9% (10/11) |
| scene_opening | 0 | 62 | 0% | 0% |
| social_probe | 0 | 10 | 0% | 0% |

**Observe route rate (post-BV3F):** 47.83% (11/23)  
**PSP contribution to observe route rate:** 43.48% (10/23) — PSP alone accounts for **90.9%** of observe-route fallback turns.

---

## Trigger concentration

| Trigger class | Events | Cumulative share |
|---|---:|---:|
| **Missing actor initiative** | **10** | **100%** |
| All other classes | 0 | 100% |

| Rejection reason | Events | Share |
|---|---:|---:|
| **`passive_scene_pressure_missing_concrete_beat`** | **10** | **100%** |

| Preceding fallback family | Events | Share |
|---|---:|---:|
| **`referential_clarity_upstream_repair`** | **10** | **100%** |

---

## Content shape concentration

| Dimension | Unique shapes | Dominant shape share |
|---|---:|---:|
| Upstream text (pre-gate) | **1** | 100% |
| Emitted sealed content | **1** | 100% |
| Player action | **1** | 100% (`I scan the notice board and watch who reacts.`) |
| Passive candidate kind | **1** | 100% (`passive_scene_pressure_generic`) |
| Hygiene source | 10 batches | 100% refreshed replay |

**Smallest cause set:** **1 root cause** (missing upstream concrete interaction under passive-scene pressure) → **10/10 events (100%)**.

---

## Temporal / corpus note

Concentration is partially amplified by BV3F refresh homogeneity:

- 30 hygiene batches cycling 3 observe prompts
- Dominant prompt index produced notice-board passive observe turns
- Stub GPT returns fixed atmospheric upstream text

**Risk:** Incidence metrics may **understate** trigger diversity (stalled interaction, lead-figure paths) present in live multi-turn sessions. Concentration analysis is **authoritative for current measurement corpus** but Phase 2 planning should include scenario-spine multi-turn validation.

---

## Comparison to pre-BV3F RC concentration

| Family | Pre-BV3F (BV3D) | Post-BV3F (BV4A) |
|---|---:|---:|
| `referential_clarity_hard_replacement` (observe) | 12 | **1** |
| `sealed_passive_scene_pressure_fallback` (observe) | 1 | **10** |

**Not relocation at stable totals:** Observe fallback turns 12 → 11 (−1). RC −11, PSP +9. BV3E shifted **classification and trigger layer** on the same observe shapes; PSP was previously bundled inside RC attribution path.

---

## Pareto summary

| Cause | Events | Cumulative % |
|---|---:|---:|
| Upstream missing concrete beat under passive-scene pressure | 10 | **100%** |

**Top-1 cause accounts for 100% of passive-scene sealed fallbacks** on refreshed corpus.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv4a_passive_scene_inventory.json` | Event-level concentration data |
| `artifacts/bv3f_reduction_metrics.json` | Post-BV3F family split |
| [BV4A_trigger_taxonomy.md](BV4A_trigger_taxonomy.md) | Trigger class definitions |
