# BV9 — Top-20 Concentration Rankings

**Date:** 2026-06-21  
**Population:** BU AST import graph (`BU_import_fan_in_fan_out.csv`)  
**Risk heuristic:** FI + 0.35×FO + ownership concentration weight

---

| Rank | Module | FI | FO | Ownership concentration | Risk |
| --- | --- | --- | --- | --- | --- |
| 1 | `game.social_exchange_emission` | 52 | 12 | 0.0264 | high |
| 2 | `game.final_emission_text` | 52 | 1 | 0.0 | high |
| 3 | `tests.helpers.replay_smoke_assertions` | 46 | 1 | 0.0024 | high |
| 4 | `tests.helpers.gate_integration_smoke` | 39 | 2 | 0.0024 | medium |
| 5 | `game.final_emission_gate` | 30 | 9 | 0.0072 | medium |
| 6 | `game.final_emission_meta_read` | 29 | 1 | 0.0024 | medium |
| 7 | `game.realization_provenance` | 28 | 1 | 0.0 | medium |
| 8 | `game.final_emission_terminal_pipeline` | 26 | 14 | 0.0 | medium |
| 9 | `game.final_emission_meta` | 24 | 8 | 0.2734 | medium |
| 10 | `game.final_emission_repairs` | 23 | 7 | 0.0072 | low |
| 11 | `tests.helpers.opening_fallback_evidence` | 23 | 4 | 0.1007 | low |
| 12 | `game.final_emission_strict_social_stack` | 22 | 22 | 0.0 | medium |
| 13 | `game.final_emission_validators` | 22 | 4 | 0.0 | low |
| 14 | `game.final_emission_owner_bucket_views` | 22 | 1 | 0.2206 | low |
| 15 | `game.final_emission_ownership_schema` | 19 | 1 | 0.4173 | low |
| 16 | `game.final_emission_visibility_fallback` | 17 | 18 | 0.1151 | low |
| 17 | `tests.helpers.failure_dashboard_report` | 16 | 7 | 0.0528 | low |
| 18 | `tests.helpers.strict_social_harness` | 15 | 7 | 0.0024 | low |
| 19 | `tests.helpers.emission_smoke_assertions` | 15 | 6 | 0.012 | low |
| 20 | `game.final_emission_replay_projection` | 15 | 5 | 0.3597 | low |

## Category highlights

### Helper facades

| Module | FI | FO | Risk |
| --- | --- | --- | --- |
| tests.helpers.replay_smoke_assertions | 46 | 1 | high |
| tests.helpers.gate_integration_smoke | 39 | 2 | medium |
| tests.helpers.emission_smoke_assertions | 15 | 6 | low |

### Replay surfaces

| Module | FI | FO | Risk |
| --- | --- | --- | --- |
| tests.helpers.replay_smoke_assertions | 46 | 1 | high |
| game.final_emission_replay_projection | 15 | 5 | low |

### Fallback surfaces

| Module | FI | FO | Risk |
| --- | --- | --- | --- |
| game.final_emission_visibility_fallback | 17 | 18 | low |

### Ownership hubs

| Module | FI | FO | Risk |
| --- | --- | --- | --- |
| game.final_emission_meta_read | 29 | 1 | medium |
| game.final_emission_owner_bucket_views | 22 | 1 | low |
| game.final_emission_ownership_schema | 19 | 1 | low |

