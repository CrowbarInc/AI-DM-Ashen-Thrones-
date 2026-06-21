# BV17 — Retirement Analysis

**Date:** 2026-06-21  
**Scope:** Top-25 high-FI modules — decompose vs governance-clean vs leave intact  

---

## Decision framework

| Action | When |
|---|---|
| **Decompose** | Accidental hub with unclear ownership and no live-path sequencer role |
| **Governance-clean** | Legitimate authority with test/monkeypatch FI inflation (BV16 pattern) |
| **Leave intact** | Governed domain hub, compat shim at cap, or live orchestration owner |

## Module decisions

| Module | FI | Authority | Decision |
| --- | --- | --- | --- |
| tests.helpers.replay_fem_read_smoke | 56 | governed authority | left intact — intentional post-decomposition domain owner |
| game.final_emission_text_formatting | 51 | governed authority | left intact — intentional post-decomposition domain owner |
| tests.helpers.gate_orchestration_smoke | 39 | governed authority | left intact — intentional post-decomposition domain owner |
| game.social_exchange_policy | 33 | governed authority | left intact — intentional post-decomposition domain owner |
| game.final_emission_visibility_fallback | 31 | legitimate authority | governance-clean optional — migrate test seams (BV16 pattern); do not decompose body |
| game.final_emission_gate | 30 | governed authority | left intact — intentional post-decomposition domain owner |
| game.realization_provenance | 29 | legitimate authority | left intact — production authority on live emission path |
| game.social_exchange_fallback_catalog | 26 | governed authority | left intact — intentional post-decomposition domain owner |
| game.final_emission_repairs | 25 | legitimate authority | left intact — production authority on live emission path |
| game.final_emission_meta | 24 | legitimate authority | left intact — production authority on live emission path |
| tests.helpers.opening_fallback_evidence | 23 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| game.final_emission_strict_social_stack | 22 | legitimate authority | left intact — production authority on live emission path |
| game.final_emission_validators | 22 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| game.attribution_read_views | 21 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| game.observability_attribution_read | 19 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| tests.helpers.failure_dashboard_report | 16 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| game.speaker_contract_enforcement | 15 | legitimate authority | left intact — production authority on live emission path |
| tests.helpers.strict_social_harness | 15 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| game.final_emission_replay_projection | 15 | governed authority | left intact — intentional post-decomposition domain owner |
| tests.helpers.emission_smoke_assertions | 15 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| tests.helpers.replay_drift_taxonomy | 15 | governed authority | left intact — intentional post-decomposition domain owner |
| game.runtime_lineage_telemetry | 15 | legitimate authority | left intact — production authority on live emission path |
| game.final_emission_opening_fallback | 14 | legitimate authority | left intact — production authority on live emission path |
| tests.helpers.golden_replay_projection | 14 | governed authority | left intact — intentional post-decomposition domain owner |
| tests.helpers.failure_classifier | 13 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |

## Aggregate verdict

| Action | Count (top 25) |
|---|---:|
| Leave intact | 24 |
| Governance-clean (optional) | 1 |
| Decompose | 0 |

**No top-25 module warrants decomposition.** Optional governance-clean applies at most to `game.final_emission_visibility_fallback` (test seam migration mirroring BV16C).

