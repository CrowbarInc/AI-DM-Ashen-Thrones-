# BV17 — Authority Classification Review

**Date:** 2026-06-21  
**Scope:** Top-25 modules by fan-in  

---

## Classification key

| Status | Meaning |
|---|---|
| **legitimate authority** | Production owner on live emission path; FI reflects real coupling |
| **governed authority** | Intentional post-decomposition domain hub with import guards + FI caps |
| **compatibility shim** | Delegate barrel; low FI by design; regrowth blocked |
| **accidental hub** | High FI without ownership boundary — *none remain in top 25* |
| **mixed authority/utility** | Test/helper surfaces combining contract enforcement and convenience |

## Top-25 classification

| Rank | Module | FI | Authority Status | Retirement posture |
| --- | --- | --- | --- | --- |
| 1 | `tests.helpers.replay_fem_read_smoke` | 56 | governed authority | left intact — intentional post-decomposition domain owner |
| 2 | `game.final_emission_text_formatting` | 51 | governed authority | left intact — intentional post-decomposition domain owner |
| 3 | `tests.helpers.gate_orchestration_smoke` | 39 | governed authority | left intact — intentional post-decomposition domain owner |
| 4 | `game.social_exchange_policy` | 33 | governed authority | left intact — intentional post-decomposition domain owner |
| 5 | `game.final_emission_visibility_fallback` | 31 | legitimate authority | governance-clean optional — migrate test seams (BV16 pattern); do not decompose body |
| 6 | `game.final_emission_gate` | 30 | governed authority | left intact — intentional post-decomposition domain owner |
| 7 | `game.realization_provenance` | 29 | legitimate authority | left intact — production authority on live emission path |
| 8 | `game.social_exchange_fallback_catalog` | 26 | governed authority | left intact — intentional post-decomposition domain owner |
| 9 | `game.final_emission_repairs` | 25 | legitimate authority | left intact — production authority on live emission path |
| 10 | `game.final_emission_meta` | 24 | legitimate authority | left intact — production authority on live emission path |
| 11 | `tests.helpers.opening_fallback_evidence` | 23 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 12 | `game.final_emission_strict_social_stack` | 22 | legitimate authority | left intact — production authority on live emission path |
| 13 | `game.final_emission_validators` | 22 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 14 | `game.attribution_read_views` | 21 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 15 | `game.observability_attribution_read` | 19 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 16 | `tests.helpers.failure_dashboard_report` | 16 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 17 | `game.speaker_contract_enforcement` | 15 | legitimate authority | left intact — production authority on live emission path |
| 18 | `tests.helpers.strict_social_harness` | 15 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 19 | `game.final_emission_replay_projection` | 15 | governed authority | left intact — intentional post-decomposition domain owner |
| 20 | `tests.helpers.emission_smoke_assertions` | 15 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |
| 21 | `tests.helpers.replay_drift_taxonomy` | 15 | governed authority | left intact — intentional post-decomposition domain owner |
| 22 | `game.runtime_lineage_telemetry` | 15 | legitimate authority | left intact — production authority on live emission path |
| 23 | `game.final_emission_opening_fallback` | 14 | legitimate authority | left intact — production authority on live emission path |
| 24 | `tests.helpers.golden_replay_projection` | 14 | governed authority | left intact — intentional post-decomposition domain owner |
| 25 | `tests.helpers.failure_classifier` | 13 | mixed authority/utility | left intact — test/helper utility; split only if regrowth detected |

## Summary

- **Governed + legitimate authorities:** 17 / 25
- **Compatibility shims:** 0 / 25
- **Accidental hubs:** 0 / 25
- **Mixed utility:** 8 / 25

**Verdict:** Repository concentration is now **authority-shaped**, not **hub-shaped**.

