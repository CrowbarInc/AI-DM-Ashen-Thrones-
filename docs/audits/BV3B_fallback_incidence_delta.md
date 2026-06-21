# BV3B — Fallback Incidence Delta

**Date:** 2026-06-21  
**Measurement:** `tools/bv1b_fallback_incidence_validation.py` on refreshed corpus  
**Baselines:** BV1B pre-refresh snapshot (`bv1b_fallback_incidence_report.baseline.json`), BV3 projection targets from [BV3_fallback_reduction_verification.md](BV3_fallback_reduction_verification.md)

---

## Executive answer

**Overall fallback incidence fell (−11.66 pp) on a larger, refreshed corpus, but the primary BV3A target metric moved in the wrong direction.** `referential_clarity_hard_replacement` events rose **38 → 48 (+10)**. BV3A upstream repair instrumentation on observe turns reports **0** applied repairs in the refreshed corpus. This pattern is **corpus reshaping plus persistent hard-replace incidence**, not demonstrated BV3A effectiveness.

---

## Top-level delta vs BV1B baseline (107 FEM)

| Metric | BV1B baseline | BV3B current | Delta |
|---|---:|---:|---:|
| Eligible FEM turns | 107 | 200 | +93 |
| Fallback events | 74 | 115 | +41 |
| **Fallback incidence** | **69.16%** | **57.50%** | **−11.66 pp** |
| Observe eligible turns | 44 | 65 | +21 |
| Observe fallback turns | 42 | 52 | +10 |
| **Observe route rate** | **95.45%** | **80.00%** | **−15.45 pp** |
| Ownerless events (no bucket) | 13 | 13 | 0 |
| Selection owner coverage | 70/74 | 111/115 | +41 events stamped |
| Owner bucket coverage | 61/74 | 102/115 | +41 events bucketed |

---

## Family-level delta vs BV1B baseline

| Fallback family | BV1B | BV3B | Delta | Primary route |
|---|---:|---:|---:|---|
| **`referential_clarity_hard_replacement`** | **38** | **48** | **+10** | observe |
| `scene_opening` | 31 | 62 | +31 | scene_opening |
| `response_type_prepared_emission` | 4 | 4 | 0 | observe / unknown |
| **`sealed_passive_scene_pressure_fallback`** | **1** | **1** | **0** | observe |

---

## Comparison vs BV3 verification projections (Phase 2 conservative)

| Metric | BV1B baseline | BV3 Phase 2 conservative target | BV3B current | Met? |
|---|---:|---:|---:|---|
| Observe route rate | 95.45% | ≤85% (stretch ~54%) | 80.00% | ✓ vs Phase 2 threshold |
| Overall incidence | 69.16% | ≤60% (stretch ~52%) | 57.50% | ✓ vs Phase 2 threshold |
| Referential clarity events | 38 | ≤26 (stretch ≤23) | **48** | **✗** |
| Ownerless (repo) | 13 | ≤5 | 13 | ✗ |

Phase 2 route/incidence thresholds are met **only because the denominator and route mix changed**; the referential-clarity family **regressed** against the BV3 primary discriminator.

---

## BV3A instrumentation on refreshed observe turns

From `artifacts/bv3b_referential_clarity_metrics.json`:

| Signal | Count |
|---|---:|
| Observe turns in scan | 65 |
| Turns with `ambiguous_entity_reference` | 49 |
| `referential_clarity_upstream_repair_applied` | **0** |
| `referential_clarity_local_substitution_applied` | **0** |
| `referential_clarity_replacement_applied` | 49 |
| Unrepaired violation turns | 10 |
| Repair success rate on observe | **0.0** |

---

## Longitudinal snapshot

`tools/bv1b_fallback_incidence_validation.py` appended a new row to `artifacts/golden_replay/fallback_incidence_history.json` (BV3B refresh run). Trend vs BV1B remains **`stable`** on the frozen 107-FEM baseline pair; the BV3B row introduces a **corpus-version break** (200 FEM) and must not be read as a like-for-like trend continuation without normalization.

---

## Interpretation

1. **Not effective BV3A reduction:** hard-replace count increased; upstream repair never stamped on refreshed observe FEM.
2. **Not pure relocation:** selection owner remains `game.final_emission_visibility_fallback` on referential-clarity events; counts did not hold constant while owners moved.
3. **Mixed incidence story:** lower overall rate is explained by more scene_opening-eligible turns at 50% fallback rate and expanded non-observe denominator—not by eliminating observe referential-clarity fallbacks.

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.baseline.json` | Pre-refresh BV1B |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Post-refresh measurement |
| `artifacts/bv3b_referential_clarity_metrics.json` | BV3A instrumentation |
| [BV3B_replay_refresh.md](BV3B_replay_refresh.md) | Corpus regeneration log |
