# BV17C — Program Metrics Rollup

**Date:** 2026-06-21  
**Scope:** BV2–BV17 contraction program (BV2 meta → BV17 reassessment)  
**Method:** Cycle closeout reports + fresh BU scan (`artifacts/bv17_hotspot_analysis.json`)  
**Primary question:** What was achieved by the contraction program?

---

## Executive summary

The BV2–BV17 program **eliminated accidental hub concentration** while **preserving live-path orchestration**. Measured wins concentrate in **fallback incidence collapse**, **recurrence deduplication**, and **compat-barrel retirement**. Fan-in did not uniformly fall — it **reclassified** from monolith-shaped accidental hubs into **named, governed domain authorities** with import guards and FI caps.

---

## Fan-in reductions (accidental / retired surfaces)

| Surface | Program start (BV1 / pre-decomposition) | Program end (BV17) | Δ | Cycle |
| --- | ---: | ---: | ---: | --- |
| `tests.helpers.emission_smoke_assertions` | **73** | **15** | **−58** | BV7 |
| `game.final_emission_meta` (write hub) | **61** | **24** | **−37** | BV2 |
| Read-side authority cluster | **70** | **19** | **−51** | BV10 |
| Smoke compat bridge (`replay_smoke` + `gate_integration`) | **95** (BV11 peak) | **2** | **−93** | BV12 |
| `game.final_emission_text` (compat barrel) | **52** | **4** | **−48** | BV13 |
| `game.social_exchange_emission` (compat barrel) | **52** | **12** | **−40** | BV14 |
| `game.final_emission_terminal_pipeline` | **26** | **11** | **−15** | BV16C |
| Gate re-export / governance inflation (BV15 target) | ~57% symbol FI on `apply_final_emission_gate` | namespace retired; gate FI **30** stable | governance-clean | BV15 |

**Interpretation:** Raw FI on retired compat surfaces fell **>200 combined** across smoke/text/social bridges. Replacement domain hubs (e.g. `replay_fem_read_smoke` 56, `text_formatting` 51) are **intentional** and **governed**, not regressions.

---

## Fan-in redistribution (governed authorities — intentional)

| Domain hub | End FI | Governance | Cycle |
| --- | ---: | --- | --- |
| `tests.helpers.replay_fem_read_smoke` | 56 | BV12C import guard + compat FI cap | BV12 |
| `tests.helpers.gate_orchestration_smoke` | 39 | BV12C import guard + compat FI cap | BV12 |
| `game.final_emission_text_formatting` | 51 | BV13C import guard + compat FI cap ≤8 | BV13 |
| `game.social_exchange_policy` | 33 | BV14C import guard + compat FI cap ≤12 | BV14 |
| `game.social_exchange_fallback_catalog` | 26 | BV14C domain owner | BV14 |
| Read facades (attribution + observability + projection) | 48 | BV10C direct-import guard | BV10 |

---

## Fan-out reductions / stabilization

| Module | Start FO | End FO | Δ | Notes |
| --- | ---: | ---: | ---: | --- |
| `game.final_emission_meta` | 6 | 8 | +2 | Write packaging narrowed; slight delegate FO |
| `game.final_emission_terminal_pipeline` | 13–14 | 15 | +1 | Sequencer retained; owner imports explicit |
| `game.final_emission_visibility_fallback` | 17–18 | 20 | +2–3 | Legitimate authority; test coupling elevated |
| Smoke compat barrels | high FO on monolith | **≤2 FO** on shims | collapsed | BV7C/BV12C |
| `tests.test_ownership_registry` | 57 | 57 | 0 | Intentional governance meta-router |

**Net:** Fan-out **did not shrink globally** — the program **localized** fan-out to named owners instead of monolith routers. Terminal and visibility FO growth is **test-coupling**, not production orchestration sprawl.

---

## Fallback reductions

| Metric | Program start (BV1) | Program end (BV17) | Δ |
| --- | ---: | ---: | ---: |
| Fallback incidence (FEM corpus) | **69.16%** (74/107) | **1.05%** (1/95) | **−68.11 pp** |
| Fallback events | 74 | 1 | **−73** |
| Observe-route share | **95.45%** | **4.35%** | **−91.1 pp** |
| Ownerless fallback events | 13 | 0 | **−13** |
| Fallback area FI (BU) | 103 | 90 | −13 |
| Residual event kind | — | `referential_clarity_hard_replacement` (1) | isolated |

**Primary cycles:** BV3 (referential clarity), BV4 (passive scene), BK ownership stamping.

---

## Recurrence reductions (BV8A)

| Metric | Before (BV8A) | After (BV8A) | Program end |
| --- | ---: | ---: | ---: |
| Total recurrence rows | 11 | 4 | 4 |
| Recurring keys | 1 | 0 | 0 |
| Dominant share | 0.7273 | 0.25 | 0.25 |
| Speaker projection family | 8 duplicate rows | **RETIRED** | retired |
| Active single-observation keys | 4 | 3 | 3 |

---

## Compatibility-barrel retirements

| Barrel | Pre-retirement FI | Post-retirement FI | Cap / guard | Cycle |
| --- | ---: | ---: | --- | --- |
| `emission_smoke_assertions` | 73 | 15 | FI ≤18; import guard | BV7C |
| `replay_smoke_assertions` | 56 | 1 | FI ≤2; BV12C guard | BV12C |
| `gate_integration_smoke` | 39 | 1 | FI ≤2; BV12C guard | BV12C |
| `final_emission_text` | 52 | 4 | FI ≤8; BV13C guard | BV13C |
| `social_exchange_emission` | 52 | 12 | FI ≤12; BV14C guard | BV14C |

**Accidental shim FI total (BV17):** **18** (text 4 + social 12 + smoke 2).

---

## Authority reclassifications

| Prior classification | Example modules | New classification | Cycle |
| --- | --- | --- | --- |
| Accidental write hub | `final_emission_meta` | Legitimate write authority + read facades | BV2 |
| Accidental read cluster | meta_read + bucket + schema | Governed read authorities (FI 19) | BV10 |
| Accidental smoke monolith | `emission_smoke_assertions` | Smoke-core compat + domain hubs | BV7, BV12 |
| Accidental text router | `final_emission_text` | Formatting/policy authorities + shim | BV13 |
| Accidental social router | `social_exchange_emission` | Policy/catalog/validation/projection + shim | BV14 |
| Test-monkeypatch namespace | `final_emission_terminal_pipeline` | Governed finalize sequencer (FI 11) | BV16C |
| Accidental gate namespace | gate re-exports | Governed orchestration owner (FI 30) | BV15 |

**Top-25 accidental hub count:** **multiple at BV11** → **0 at BV17**.

---

## Concentration shape (repository-wide)

| Metric | BV1 (program start) | BV17 (program end) | Δ |
| --- | ---: | ---: | ---: |
| Top-1 FI share | ~8.7% (meta/smoke era) | **5.1%** | −3.6 pp |
| Top-5 FI share | ~32.8% | **18.9%** | −13.9 pp |
| Top hotspot FI | **73** (accidental smoke) | **56** (governed replay_fem) | reclassified |
| Governed + legitimate in top 25 | 0 (by design) | **17** | +17 |
| Ecosystem modules (BU) | 216–220 | 223 | +3 (domain owners) |

---

## Cycle contribution map

| Cycle | Primary metric moved |
| --- | --- |
| BV2 | Meta write FI −64%; read facades introduced |
| BV3 | RC hard-replacement events −11; incidence 46%→12% |
| BV4 | Passive-scene observe collapse; incidence 12%→1% |
| BV7 | Smoke monolith FI −79% |
| BV8A | Speaker recurrence family retired; recurring keys 1→0 |
| BV10 | Authority cluster FI −73% (70→19) |
| BV12 | Smoke compat bridge −93 FI |
| BV13 | Text compat −48 FI |
| BV14 | Social compat −40 FI |
| BV15 | Gate namespace / governance validation |
| BV16C | Terminal AST FI 26→9; monkeypatch inflation removed |
| BV17 | Contraction complete; baseline established |

---

## Evidence

| Source | Role |
| --- | --- |
| `docs/audits/BV1_maintenance_cost_matrix.md` | Program-start baseline |
| `docs/audits/BV5_maintenance_cost_matrix.md` | Mid-program fallback/meta wins |
| `docs/audits/BV7_closeout.md` | Smoke monolith retirement |
| `docs/audits/BV10C_fan_in_closeout.md` | Read cluster closeout |
| `docs/audits/BV12_closeout.md` – `BV14_closeout.md` | Domain decomposition |
| `docs/audits/BV16C_fan_in_report.md` | Terminal governance |
| `docs/audits/BV17_hotspot_inventory.md` | Program-end measurement |
| `artifacts/bv17_hotspot_analysis.json` | Machine-readable end state |
