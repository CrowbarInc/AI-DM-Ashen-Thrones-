# BV14 — Candidate Analysis

**Date:** 2026-06-21  
**Context:** BV13 closed; `final_emission_text` compat barrel capped.

---

## Current top fan-in (selected, BU baseline)

| Module | BU FI | Layer |
| --- | --- | --- |
| `tests.helpers.replay_fem_read_smoke` | 56 |  |
| `game.final_emission_text` | 52 |  |
| `game.social_exchange_emission` | 52 |  |
| `tests.helpers.gate_orchestration_smoke` | 39 |  |
| `game.final_emission_gate` | 30 |  |
| `game.realization_provenance` | 28 |  |
| `game.final_emission_terminal_pipeline` | 26 |  |
| `game.final_emission_meta` | 24 |  |
| `game.final_emission_repairs` | 23 |  |
| `tests.helpers.opening_fallback_evidence` | 23 |  |
| `game.final_emission_strict_social_stack` | 22 |  |
| `game.final_emission_validators` | 22 |  |

## Candidate evaluation

| Candidate | FI | Assessment | Risk | BV14 fit |
| --- | --- | --- | --- | --- |
| `game.social_exchange_emission` | 52 | Tied pre-BV13 production FI; strict-social composition authority; cross-cuts gate stack | Medium-high — social authority surface | **Primary** |
| `game.final_emission_text_formatting` | 51 | Post-BV13 intentional primitive hub; homogeneous symbol category | Low — already decomposed and governed | Defer — maintenance acceptable |
| Domain smoke facades | 56+39 | Post-BV12 intentional; BV12C capped | Low — governed test hubs | Defer |
| `game.final_emission_gate` / terminal pipeline | 30 / 26 | Gate owner + finalize coupling; BN preflight extractions ongoing | Medium — owner modules | Secondary (after social core) |

## BV14 recommendation

**Select `game.social_exchange_emission` as BV14 target.**

Evidence:

- Highest remaining **production-core** FI alongside retired `final_emission_text` monolith
- Strict-social composition cross-cuts gate preflight, validators, and terminal pipeline
- BV13 removed text/policy choke; next ROI is **social emission authority decomposition**
- Formatting hub FI is homogeneous and governed; smoke facades are BV12C-locked

Suggested BV14 scope:

1. Symbol concentration audit (strict-social vs narration vs sanitizer coupling)
2. Extraction aligned to existing BN8 strict-social preflight boundary
3. Import guard + FI cap pattern mirroring BV13C governance

