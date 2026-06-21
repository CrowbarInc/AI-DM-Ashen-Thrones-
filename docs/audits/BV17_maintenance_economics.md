# BV17 — Maintenance Economics Refresh

**Date:** 2026-06-21  
**Prior matrices:** [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md), [BV9_maintenance_matrix.md](BV9_maintenance_matrix.md), [BV11_maintenance_matrix.md](BV11_maintenance_matrix.md)  
**Method:** BU CSV area rollups + BV11 baseline + BV12–BV16C closeout verification

---

## Executive verdict

**Classification:** **CONTRACTION_COMPLETE**

**Primary drag center:** `governed_domain_authorities_and_test_infrastructure`

## Dimension scorecard

| Dimension | BV17 assessment |
| --- | --- |
| Maintenance Drag | low — no accidental monoliths; remaining FI is domain-owned |
| Maintenance Locality | high — BV12–BV16 moved edits to named owners |
| Ownership Clarity | high — registry guards + FI caps on compat barrels |
| Operability | high — gate/terminal sequencing preserved; monkeypatch inflation removed |
| Replay Risk Concentration | medium — strict_social_stack + visibility_fallback on live path |

## Area matrix (BV11 → BV17)

| Area | BV11 FI | BV17 FI | Δ FI | BV11 FO | BV17 FO |
| --- | --- | --- | --- | --- | --- |
| replay | 136 | 137 | 1 | 33 | 34 |
| fallback | 76 | 90 | 14 | 50 | 53 |
| attribution | 132 | 133 | 1 | 23 | 24 |
| final_emission | 381 | 386 | 5 | 210 | 222 |
| speaker_finalize | 34 | 34 | 0 | 30 | 36 |
| tests_smoke | 54 | 59 | 5 | 7 | 10 |
| tests_registry | 0 | 0 | 0 | 57 | 57 |
| text_domain | None | 0 | 0 | None | 0 |
| social_domain | None | 94 | 94 | None | 33 |

## Key cluster metrics (BV11 → BV17)

| Cluster | BV11 (approx) | BV17 | Interpretation |
| --- | --- | --- | --- |
| Smoke compat bridge | 95 | 2 | Collapsed — domain hubs absorbed traffic |
| Smoke domain hubs | 6 | 99 | Intentional governed redistribution |
| Text compat + domain | 104 | 4+59 | Compat 52→4; formatting owns composition |
| Social compat + domain | 104 | 12+… | Compat 52→12; policy/catalog own slices |
| Gate + terminal | 56 | 41 | Terminal 26→11; gate stable 30 |
| Accidental shim FI total | — | 18 | ≤18 — contraction threshold met |

## Status notes

- Compat smoke shims collapsed: replay_smoke 56→1, gate_integration 39→1.
- Text compat collapsed: final_emission_text 52→4; formatting authority 51 FI (governed).
- Social compat collapsed: social_exchange_emission 52→12; domain modules own composition.
- Terminal pipeline deflated: 26→11 BU FI; BV16C removed monkeypatch namespace inflation.
- Gate orchestration stable at 30 FI (1 production); test orchestration is primary consumer.
- visibility_fallback grew 17→31 — legitimate authority with elevated test coupling.
- Fallback incidence unchanged at 1.05% (1/95); recurrence keys 0 post-BV8A.

## Net shift since BV5/BV9

| Drag center | BV5/BV9 status | BV17 status |
|---|---|---|
| Fallback incidence | **Reduced** (1.05%) | **Unchanged** — not a driver |
| Meta write hub | FI 61 → 24 | **Stable** — read facades governed |
| Smoke monolith | FI 73 pre-BV7 | **Retired** — domain hubs + shims |
| Text/social compat | FI 52 each accidental | **Shim-only** (4 / 12 FI) |
| Gate/terminal convergence | Accidental namespace FI | **Governed authorities** |
| Recurrence | 8 speaker rows | **0 recurring keys** (BV8A) |

