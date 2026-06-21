# BV9 — Maintenance Matrix Refresh

**Date:** 2026-06-21  
**Prior matrix:** [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md)  
**Method:** BU CSV area rollups + BV8A recurrence + BV1B fallback re-read

---

## Executive verdict

**Classification:** **REDISTRIBUTED_COST** — fallback and recurrence wins shifted drag to **final-emission read facades** and **gate/terminal convergence**.

**Primary drag center:** `final_emission_meta_read_attribution_cluster`

## Area matrix

| Area | Prior FI | Current FI | Δ FI | Prior FO | Current FO |
| --- | --- | --- | --- | --- | --- |
| replay | 86 | 126 | 40 | 80 | 33 |
| fallback | 103 | 76 | -27 | 193 | 50 |
| attribution | 75 | 106 | 31 | 53 | 19 |
| final_emission | 443 | 410 | -33 | 218 | 211 |
| speaker_finalize | 80 | 34 | -46 | 125 | 30 |
| tests_smoke | 73 | 54 | -19 | 5 | 8 |
| tests_registry | 0 | 0 | 0 | 57 | 57 |

## Status notes

- Fallback incidence remains at 1.05% (1/95 turns) — no longer dominant drag.
- Speaker projection recurrence retired in BV8A deduplicated view.
- Largest single-module FI: final_emission_text and social_exchange_emission (52 each).
- Largest test-bridge cluster post-BV7: replay_smoke_assertions (46) + gate_integration_smoke (39).
- Largest unaddressed read-side cluster: meta_read (29) + owner_bucket_views (22) + ownership_schema (19).

## Net shift since BV5

| Drag center | BV5 status | BV9 status |
|---|---|---|
| Fallback incidence | **Reduced** (1.05%) | **Collapsed** — residual 1 event |
| Meta write (`final_emission_meta`) | **Reduced** (FI 24) | Stable read facades dominate |
| Smoke facade | FI 73 pre-BV7 | FI 17 post-BV7B |
| Speaker recurrence | 8 rows active | **Retired** (BV8A) |
| Gate / terminal | Convergence hub | **Largest remaining FI cluster** |

