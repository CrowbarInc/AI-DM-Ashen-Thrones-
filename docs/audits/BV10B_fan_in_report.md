# BV10B — Fan-In Report

**Date:** 2026-06-21
**Method:** `scripts/bu_final_emission_coupling_discovery.py` (authority modules) + AST importer count (facades)

## Baseline vs post-migration

| Module | Pre-BV10B | Post-BV10B | Δ |
|---|---:|---:|---:|
| `final_emission_meta_read` | **31** | **24** | **-7** |
| `final_emission_owner_bucket_views` | **24** | **7** | **-17** |
| `final_emission_ownership_schema` | **22** | **8** | **-14** |
| **Authority cluster sum** | **77** | **39** | **-38** |

## New facade fan-in (external adopters)

| Facade | FI (importers) |
|---|---:|
| `attribution_read_views` | **20** |
| `ownership_projection_views` | **7** |
| `observability_attribution_read` | **10** |
| **Facade sum** | **37** |

## Target assessment

| Metric | Pre-BV10B | Post-BV10B | Target | Met? |
|---|---:|---:|---:|---|
| Authority cluster FI | 77 | **39** | indirect reduction | ✓ |
| Phase 2 combined authority FI | 77 | **39** | **≤45** | **✓** |

**Note:** Facade modules absorb former authority importers. Authority cluster FI is the primary concentration metric; facade FI replaces scattered authority edges.
