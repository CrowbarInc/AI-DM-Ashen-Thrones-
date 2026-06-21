# BV10C — Fan-In Closeout

**Date:** 2026-06-21
**Method:** `scripts/bu_final_emission_coupling_discovery.py` (authority) + AST importer scan (facades/replay adapter)

## Timeline

| Phase | Authority cluster FI | Δ vs prior | Key deliverable |
|---|---:|---:|---|
| BV10A (facade extraction) | 70 → 77* | +7 delegate edges | `attribution_read_views`, `ownership_projection_views`, `observability_attribution_read` |
| BV10B (consumer migration) | **77 → 39** | **−38** | Attribution + observability consumer retargeting |
| BV10C (replay adapter + C5 + lock) | **39 → 19** | **-20** | Gate/smoke FEM reads + governance guard |

*BV10A temporarily increased measured FI by adding facade delegate modules importing authority.

## Authority cluster (primary metric)

| Module | BV10B | BV10C | Δ |
|---|---:|---:|---:|
| `final_emission_meta_read` | **24** | **4** | **-20** |
| `final_emission_owner_bucket_views` | **7** | **7** | **+0** |
| `final_emission_ownership_schema` | **8** | **8** | **+0** |
| **Sum** | **39** | **19** | **-20** |

**Target 31–35:** ✓ exceeded (lower concentration)

## Facade fan-in (external adopters, AST)

| Facade | FI |
|---|---:|
| `attribution_read_views` | **20** |
| `ownership_projection_views` | **7** |
| `observability_attribution_read` | **18** |
| **Facade sum** | **45** |

## Replay adapter

| Module | BU CSV FI | AST external FI |
|---|---:|---:|
| `final_emission_replay_projection` | **15** | **22** |

## BV10C migrations (C5 gate/smoke consolidation)

| Consumer cluster | Route |
|---|---|
| Gate owner suites (`test_final_emission_gate_*`, visibility, opening fallback) | `tests.helpers.replay_smoke_assertions.final_emission_meta_from_output` |
| Observability production reads (`stage_diff_telemetry`, `post_emission_speaker_adoption`) | `game.observability_attribution_read` |
| Layer owner FEM key reads (acceptance quality, narrative mode, opening accept debug) | `game.observability_attribution_read.FINAL_EMISSION_META_KEY` |
| `emission_smoke_assertions` debug notes | `replay_smoke_assertions.read_turn_debug_notes` (removed direct meta_read) |
