# BV4A — Verification Projection

**Date:** 2026-06-21  
**Purpose:** Estimate post-Phase-1 metrics if upstream concrete-beat satisfiers ship successfully.  
**Baseline:** BV3F snapshot (`artifacts/bv3f_reduction_metrics.json`, `artifacts/bv4a_passive_scene_inventory.json`).

---

## Current state (BV3F)

| Metric | Value | Source |
|---|---:|---|
| Canonical FEM instances | 95 | BV3D scan |
| Observe turns | 23 | bv1b report |
| Observe fallback turns | 11 | bv1b report |
| **Observe route rate** | **47.83%** | 11/23 |
| **Overall fallback incidence** | **11.58%** | 11/95 |
| `sealed_passive_scene_pressure_fallback` | **10** | bv4a inventory |
| `referential_clarity_hard_replacement` | **1** | bv3f metrics |
| PSP share of observe fallbacks | **90.9%** | 10/11 |

---

## Phase 1 projection model

**Assumptions:**

- EC-4A-01 upstream contract + EC-4A-02 beat injection repair cover **80–100%** of current PSP cluster (single trigger class, 100% concentration).
- Residual **1** RC hard-replacement event unchanged in Phase 1 (addressed by BV4B).
- No compensating increase in scene-opening or diagnostics families (guarded by BV3F relocation analysis).
- Corpus size stable at ~95 FEM until next replay refresh.

**Conservative / target / stretch scenarios:**

| Metric | BV3F baseline | Conservative (P1) | Target (P1) | Stretch (P1) |
|---|---:|---:|---:|---:|
| **PSP events** | 10 | **2** | **0–1** | **0** |
| **Observe fallback turns** | 11 | **3** | **1–2** | **1** |
| **Observe route rate** | 47.83% | **13.0%** | **4.3–8.7%** | **4.3%** |
| **Overall fallback incidence** | 11.58% | **3.2%** | **1.1–2.1%** | **1.1%** |
| **RC hard replacement** | 1 | **1** | **1** | **1** |
| Upstream PSP repair applied (observe) | 0 | **8** | **10** | **10** |

### Derivation

```text
observe_route_rate = observe_fallback_turns / observe_turns

Conservative: PSP 10→2, total observe fallbacks 11→3 (RC 1 + PSP 2)
  → 3/23 = 13.04%

Target: PSP 10→1, total 11→2 (RC 1 + PSP 1)
  → 2/23 = 8.70%
  OR PSP 10→0, total 11→1 (RC only)
  → 1/23 = 4.35%

Stretch: PSP 10→0, total 11→1
  → 1/23 = 4.35%

overall_incidence = fallback_turns / eligible_fem

Conservative: 3/95 = 3.16%
Target: 2/95 = 2.11% to 1/95 = 1.05%
Stretch: 1/95 = 1.05%
```

---

## Phase 2 projection (after retry + accept path)

| Metric | Target (P2) | Stretch (P2) |
|---|---:|---:|
| PSP events | **0–1** | **0** |
| Observe route rate | **<8.7%** | **4.3%** (RC residual only) |
| Overall fallback incidence | **<2.1%** | **1.1%** |

---

## Success criteria (BV4A Phase 1 sign-off)

| Criterion | BV3F | Phase 1 target |
|---|---|---|
| PSP event count | 10 | **≤2** |
| PSP delta vs BV3F | — | **≤−8** |
| `passive_scene_upstream_repair_applied` on replay FEM | 0 | **≥8** |
| RC hard replacement | 1 | **≤1** (no compensating increase) |
| Observe route rate | 47.83% | **<15%** |
| Reduction classification | — | **EFFECTIVE_REDUCTION** (not relocation) |

---

## Verification protocol

### Snapshot pipeline

1. Implement Phase 1 work items ([BV4A_reduction_plan.md](BV4A_reduction_plan.md)).
2. Replay refresh under new gate code (`tools/bv3f_replay_corpus_refresh.py` or BV4A successor).
3. Run:
   ```bash
   python tools/bv4a_passive_scene_inventory.py
   python tools/bv3f_reduction_metrics.py
   python tools/bv1b_fallback_incidence_validation.py
   ```
4. Compare against BV3F baseline — require **strictly lower PSP count** and **upstream repair stamps > 0**.

### Regression gates

| Gate | Command | Pass condition |
|---|---|---|
| Passive scene pressure unit tests | `pytest tests/test_final_emission_passive_scene_pressure.py` | Green |
| BV3E regression | `pytest tests/test_bv3e_eligibility_expansion.py` | Green |
| Non-strict stack | `pytest tests/test_final_emission_non_strict_stack.py` | Green |
| Golden replay | `pytest tests/test_golden_replay_*.py -q` | No drift |
| Manifest | `python tools/refresh_protected_replay_manifest.py --check` | Exit 0 |

### Reduction vs relocation discrimination

| Signal | Relocation (fail) | Reduction (pass) |
|---|---|---|
| PSP count | Stable ~10 | **≥8 decrease** |
| RC count | Increases >1 | **Stable ≤1** |
| New dominant family | RC or global_scene rises | **No new dominant family** |
| Upstream repair stamps | 0 | **`passive_scene_upstream_repair_applied > 0`** |

---

## Confidence assessment

| Projection | Confidence | Basis |
|---|---|---|
| PSP −8 to −10 on current corpus | **High** | Single trigger class; 100% concentration; GM instructions already exist |
| Observe route <15% | **High** | PSP accounts for 90.9% of observe fallbacks |
| Overall incidence <3% | **Medium** | Depends on corpus refresh denominator |
| Stretch 0 PSP | **Medium** | Residual RC + latent multi-turn triggers may remain |
| Multi-turn stalled interaction coverage | **Low** | Not represented on single-turn hygiene corpus |

---

## Comparison to BV3F (referential clarity path)

| Dimension | BV3 → BV3F | BV4A Phase 1 (projected) |
|---|---|---|
| Primary family | RC hard replacement | PSP sealed fallback |
| Events at baseline | 12 | 10 |
| Upstream satisfier | BV3E exact_alias_introducer | Concrete-beat contract + injection |
| Projected delta | −11 | **−8 to −10** |
| Dominant post-fix residual | PSP (exposed) | RC (1 event) → BV4B |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv4a_passive_scene_inventory.json` | PSP event authority |
| `artifacts/bv3f_reduction_metrics.json` | BV3F baseline |
| [BV4A_concentration_report.md](BV4A_concentration_report.md) | Pareto / concentration |
| [BV4A_reduction_plan.md](BV4A_reduction_plan.md) | Phase definitions |
