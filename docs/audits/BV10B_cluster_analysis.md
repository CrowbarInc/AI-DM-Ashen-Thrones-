# BV10B — Cluster Analysis

**Date:** 2026-06-21

## Actual FI reduction

| Slice | Pre-BV10B | Post-BV10B | Δ | Share of reduction |
|---|---:|---:|---:|---:|
| `final_emission_meta_read` | 31 | 24 | -7 | 18% |
| `final_emission_owner_bucket_views` | 24 | 7 | -17 | 45% |
| `final_emission_ownership_schema` | 22 | 8 | -14 | 37% |
| **Authority cluster** | **77** | **39** | **-38** | 100% |

**Net authority cluster reduction:** 77 → 39 (**-49%**).
**Migrations executed:** 32 files.

## Facade absorption

| Facade | External FI | Primary subsystems |
|---|---:|---|
| `attribution_read_views` | 20 |  |
| `ownership_projection_views` | 7 |  |
| `observability_attribution_read` | 10 |  |

## Remaining migration opportunities (Phase 3 / BV10C)

| Opportunity | Est. edges | Risk |
|---|---:|---|
| Gate/smoke `read_final_emission_meta_dict` hardening (C5) | ~14 | Low |
| Fallback write modules (intentional direct) | 0 | N/A |
| Owner suites (`test_final_emission_meta`, `test_opening_fallback_owner_bucket`) | 0 | N/A |
| `test_bv10_read_cluster_direct_import_guard` enforcement | governance | Low |

## Accidental hubs remaining

| Hub | Status |
|---|---|
| `failure_classification_sync` | **Resolved** — single `attribution_read_views` import |
| `final_emission_replay_projection` | **Reduced** — lazy adapters use facades; top-level projection vocabulary only |
| Gate test cluster (`read_final_emission_meta_dict`) | **Open** — deferred C5 |
| `emission_smoke_assertions` / `replay_smoke_assertions` | **Open** — smoke bridge |
