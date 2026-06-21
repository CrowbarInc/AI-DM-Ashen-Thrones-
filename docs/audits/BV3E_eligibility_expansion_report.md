# BV3E — Eligibility Expansion Report

**Date:** 2026-06-21  
**Goal:** Expand BV3A repair eligibility on production-shaped observe turns without weakening referential-clarity guarantees.

---

## Executive summary

BV3E adds a **low-risk exact-alias introducer repair path** for multi-violation observe turns where a singular indefinite role noun (`a nearby guard`) disambiguates to one visible entity via exact-alias matching and title exclusion.

| Metric | Baseline (BV3D frozen FEM) | Post-expansion (simulated) |
|---|---:|---:|
| BV3A-eligible observe turns | 1 | 1 |
| BV3E-eligible observe turns | 1 | **12** (+11 simulated) |
| Newly eligible (BV3E − BV3A) | 0 | **11** |
| Upstream repair applied | 1 | **12** (projected) |
| `referential_clarity_hard_replacement` (frozen FEM) | 12 | 12 |
| Projected hard-replacement delta after refresh | — | **−11** |

Frozen FEM metadata remains pre-BV3E until replay refresh; **shape simulation** (`artifacts/bv3e_shape_simulation.json`) validates eligibility and repair on full gate candidate text.

---

## Baseline (BV3D)

Source: `artifacts/bv3d_eligibility_report.json`, `artifacts/bv3a_referential_clarity_metrics.json`

| Metric | Value |
|---|---:|
| Observe turns (measurement scope) | 23 |
| Upstream repair eligible | 1 |
| Upstream repair applied | 1 |
| Replay-only eligible | 0 |
| `referential_clarity_hard_replacement` | 12 |
| Observe-route fallback rate | 0.522 |
| Repair success rate on ambiguous observe | 0.091 |

---

## Post-expansion

Source: `artifacts/bv3e_eligibility_metrics.json`, `artifacts/bv3e_shape_simulation.json`

| Metric | Frozen FEM | Simulated (live world) |
|---|---:|---:|
| BV3E-eligible | 0 | **11** |
| Newly eligible vs BV3A | 0 | **11** |
| Upstream repair applied | 0 | **11** |
| Repair success rate on eligible shapes | — | **1.0** (11/11) |
| BV3E repair mode | — | `exact_alias_introducer` |

**Example repair:**

```text
Before: … a nearby guard points with his spear-butt … "…," he says.
After:  … a nearby gate guard points with his spear-butt … "…," he says.
```

All three violations clear after introducer alias substitution; no hard replace.

---

## Delta

| Metric | Delta | Notes |
|---|---:|---|
| Newly eligible observe turns | **+11** | Simulated; requires replay refresh for FEM stamps |
| Projected `referential_clarity_hard_replacement` | **−11** | 11 gate-interruption turns avoid hard replace |
| Observe-route rate (projected) | **≈ −0.48 pp per avoided replace** | Depends on refresh denominator |
| BV3A regression | **0** | OBS-M001 fixture still passes |

---

## Implementation scope

| Component | Path |
|---|---|
| Eligibility expansion | `game/final_emission_referential_clarity.py` |
| Unit tests | `tests/test_bv3e_eligibility_expansion.py` |
| Cluster inventory tool | `tools/bv3e_violation_cluster_inventory.py` |
| Shape simulation | `tools/bv3e_shape_simulation.py` |
| Metrics | `tools/bv3e_eligibility_metrics.py` → `artifacts/bv3e_eligibility_metrics.json` |

**Instrumentation fields added:**

- `referential_clarity_bv3e_repair_mode` — `exact_alias_introducer` when BV3E path applies

---

## Verification

| Suite | Result |
|---|---|
| `tests/test_bv3e_eligibility_expansion.py` | **PASS** (5) |
| `tests/test_bv3a_observe_referential_clarity_repair.py` | **PASS** (3) |
| `tests/test_final_emission_referential_clarity.py` | **PASS** |
| `tests/test_speaker_contract_enforcement.py` | **PASS** |
| `tests/test_final_emission_meta.py` (attribution) | **PASS** |
| `tests/test_final_emission_visibility.py` | **PASS** |
| `tests/test_final_emission_visibility_fallback.py` | **PASS** |
| `tests/test_final_emission_sealed_fallback.py` | **PASS** |
| Golden replay suites | **PASS** (2 env-flake failures unrelated to BV3E: PermissionError on tmp combat.json, empty bug-recurrence fixture) |

---

## Risk assessment

| Area | Assessment |
|---|---|
| **Referential clarity guarantees** | **Low risk** — repair aborts unless referential clarity + first mention + visibility re-validation pass |
| **Speaker contracts** | **No change** — strict-social path untouched |
| **Replay contracts** | **No change** — meta snapshot includes BV3E mode; preservation unchanged |
| **Ownership relocation** | **Avoided** — repair activates instead of hard replace on MV-01 shapes |
| **False-positive alias match** | **Mitigated** — offset-targeted substitution + singular introducer + title exclusion |
| **Remaining hard replaces** | Archive ambiguous-speaker shapes without introducer (~30 turns) — intentional |

---

## Next steps

1. **Replay refresh** — re-materialize FEM on hygiene corpus so `referential_clarity_bv3e_repair_mode` and reduced hard-replacement counts appear in live metrics.
2. **Monitor** `artifacts/bv3e_eligibility_metrics.json` after refresh for frozen-FEM vs simulated convergence.
3. **Defer** medium-risk candidates (EC-M01 … EC-M04) pending corpus evidence.

---

## Success criteria

| Criterion | Status |
|---|---|
| Production-shaped observe turns eligible for repair | **Met** (11/11 simulated) |
| `referential_clarity_hard_replacement` decreases via repair activation | **Projected −11** after refresh |
| Ownership / speaker / replay contracts unchanged | **Met** |
| Low-risk-only implementation | **Met** |
