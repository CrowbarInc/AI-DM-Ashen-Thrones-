# BV11 — Top-20 Concentration Rankings

**Date:** 2026-06-21  
**Population:** BU AST import graph + supplemental read-facade AST scan  
**Risk heuristic:** FI + 0.35×FO + ownership concentration weight  
**Baseline:** BV9 (`artifacts/bv9_hotspot_analysis.json`)

---

| Rank | Module | FI | FO | Type | Risk | Change since BV9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `tests.helpers.replay_smoke_assertions` | 56 | 1 | helper | high | +10 |
| 2 | `game.social_exchange_emission` | 52 | 12 | production | high | 0 |
| 3 | `game.final_emission_text` | 52 | 1 | production | high | 0 |
| 4 | `tests.helpers.gate_integration_smoke` | 39 | 2 | helper | medium | 0 |
| 5 | `game.final_emission_gate` | 30 | 9 | production | medium | 0 |
| 6 | `game.realization_provenance` | 28 | 1 | production | medium | 0 |
| 7 | `game.final_emission_terminal_pipeline` | 26 | 14 | production | medium | 0 |
| 8 | `game.final_emission_meta` | 24 | 8 | production | medium | 0 |
| 9 | `game.final_emission_repairs` | 23 | 7 | production | low | 0 |
| 10 | `tests.helpers.opening_fallback_evidence` | 23 | 4 | helper | low | 0 |
| 11 | `game.final_emission_strict_social_stack` | 22 | 22 | production | medium | 0 |
| 12 | `game.final_emission_validators` | 22 | 4 | production | low | 0 |
| 13 | `game.attribution_read_views` | 21 | 1 | production | low | new |
| 14 | `game.observability_attribution_read` | 19 | 1 | production | low | new |
| 15 | `game.final_emission_visibility_fallback` | 17 | 18 | production | low | 0 |
| 16 | `tests.helpers.failure_dashboard_report` | 16 | 7 | helper | low | 0 |
| 17 | `tests.helpers.strict_social_harness` | 15 | 7 | helper | low | 0 |
| 18 | `game.final_emission_replay_projection` | 15 | 5 | production | low | 0 |
| 19 | `tests.helpers.emission_smoke_assertions` | 15 | 5 | helper | low | 0 |
| 20 | `game.speaker_contract_enforcement` | 15 | 4 | production | low | 0 |

## Category highlights

### Helper / bridge facades

| Module | FI | FO | Risk | Δ since BV9 |
| --- | --- | --- | --- | --- |
| tests.helpers.replay_smoke_assertions | 56 | 1 | high | +10 |
| tests.helpers.gate_integration_smoke | 39 | 2 | medium | 0 |
| game.attribution_read_views | 21 | 1 | low | new |
| game.observability_attribution_read | 19 | 1 | low | new |
| tests.helpers.emission_smoke_assertions | 15 | 5 | low | 0 |

### Read facades (post-BV10)

| Module | FI | FO | Risk | Δ since BV9 |
| --- | --- | --- | --- | --- |
| game.attribution_read_views | 21 | 1 | low | new |
| game.observability_attribution_read | 19 | 1 | low | new |

### Replay surfaces

| Module | FI | FO | Risk | Δ since BV9 |
| --- | --- | --- | --- | --- |
| tests.helpers.replay_smoke_assertions | 56 | 1 | high | +10 |
| game.final_emission_replay_projection | 15 | 5 | low | 0 |

