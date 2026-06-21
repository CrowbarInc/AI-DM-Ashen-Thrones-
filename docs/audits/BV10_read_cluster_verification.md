# BV10 — Read-Cluster Verification (Post BV10C)

**Date:** 2026-06-21

## Is the read-side attribution cluster still a maintenance hotspot?

**No — concentration has shifted to facades.** Authority cluster FI dropped from **70** (pre-BV10A combined baseline) to **19** (post-BV10C BU CSV). Residual direct authority imports are confined to write owners, facade delegates, one bucket owner suite, and the replay smoke bridge.

## Has concentration actually reduced?

| Metric | Pre-BV10 | Post-BV10C | Change |
|---|---:|---:|---|
| Authority cluster FI | 70 | **19** | **−73%** |
| `attribution_read_views` external FI | 0 | **20** | traffic absorbed |
| Accidental triple-import test files | 16 | **0** | eliminated |

## Largest repository hotspot (game modules, BU CSV fan-in)

| Rank | Module | FI |
|---:|---|---:|
| 1 | `final_emission_text` | **52** |
| 2 | `social_exchange_emission` | **52** |
| 3 | `final_emission_gate` | **30** |
| 4 | `realization_provenance` | **28** |
| 5 | `final_emission_terminal_pipeline` | **26** |
| 6 | `final_emission_meta` | **24** |
| 7 | `final_emission_repairs` | **23** |
| 8 | `final_emission_strict_social_stack` | **22** |

**Largest hotspot:** `final_emission_text` (FI **52**). The read-side attribution cluster (`meta_read` + `owner_bucket_views` + `ownership_schema`) no longer ranks in the top maintenance magnets; `final_emission_meta` write owner (FI **24**) and `final_emission_replay_projection` replay adapter remain adjacent high-traffic surfaces by design.

## Governance

Direct read-cluster authority imports are locked by `test_bv10_read_cluster_direct_import_guard_*` in `tests/test_ownership_registry.py`. New consumers must route through facades or approved owner suites.
