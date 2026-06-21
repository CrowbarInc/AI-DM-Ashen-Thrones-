# BV11 — Maintenance Matrix Refresh

**Date:** 2026-06-21  
**Prior matrix:** [BV9_maintenance_matrix.md](BV9_maintenance_matrix.md)  
**Method:** BU CSV area rollups + BV9 baseline + BV10 closeout verification

---

## Executive verdict

**Classification:** **MIXED_OR_INCONCLUSIVE** — BV10 **reduced** authority-cluster FI (−73%) while **redistributing** read traffic to facades (+48 FI) and **increasing** replay-smoke bridge load (+10 FI). Net repository drag shifted rather than uniformly declining.

**Primary drag center:** `smoke_bridge_and_terminal_emission_core`

## Area matrix (BV9 → BV11)

| Area | BV9 FI | BV11 FI | Δ FI | BV9 FO | BV11 FO |
| --- | --- | --- | --- | --- | --- |
| replay | 126 | 136 | 10 | 33 | 33 |
| fallback | 76 | 76 | 0 | 50 | 50 |
| attribution | 106 | 132 | 26 | 19 | 23 |
| final_emission | 410 | 381 | -29 | 211 | 210 |
| speaker_finalize | 34 | 34 | 0 | 30 | 30 |
| tests_smoke | 54 | 54 | 0 | 8 | 7 |
| tests_registry | 0 | 0 | 0 | 57 | 57 |

## Key cluster metrics

| Cluster | BV9 | BV11 | Δ |
| --- | --- | --- | --- |
| Authority cluster | 70 | 19 | -51 |
| Smoke bridge | 85 | 95 | 10 |
| Gate + terminal | 56 | 56 | 0 |
| Text + social (production core) | 104 | 104 | 0 |

## Status notes

- BV10 closed the read-side authority cluster: combined FI 70 → 19 (−73%).
- Read traffic redistributed to governed facades (attribution + observability + projection ≈ 48 FI).
- replay_smoke_assertions grew 46 → 56 (+10) — now the single largest module by fan-in.
- Production-core pair final_emission_text + social_exchange_emission unchanged at 52 FI each.
- Gate + terminal convergence remains 30 + 26 = 56 FI with medium replay risk.
- Fallback (1.05%) and recurrence (0 recurring keys) remain non-drivers.

## Net shift since BV9

| Drag center | BV9 status | BV11 status |
|---|---|---|
| Read-side attribution | **#1 unaddressed cluster** (70 FI) | **Closed** — authority 19 FI, facades governed |
| replay_smoke_assertions | FI 46 (#3) | **FI 56 (#1)** — bridge load increased |
| Smoke bridge combined | 85 FI | **95 FI** (+12%) |
| Gate / terminal | Convergence hub (56 FI) | **Unchanged** — still #2 production cluster |
| Fallback / recurrence | Collapsed / stable | **Unchanged** — not drivers |

