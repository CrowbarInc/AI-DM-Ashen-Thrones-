# BV15 — Candidate Analysis

**Date:** 2026-06-21  
**Context:** BV14 closed; `social_exchange_emission` compat barrel capped at composition authority.

---

## Current top fan-in (selected, BU baseline + post-BV14 AST)

| Module | BU FI | Post-BV14 AST FI | Layer |
| --- | --- | --- | --- |
| `game.social_exchange_emission` | 52 | 12 | compat composition (capped) |
| `game.social_exchange_fallback_catalog` | 0 | 26 | fallback authority |
| `game.final_emission_text_formatting` | 51 | — | text primitive hub (BV13 governed) |
| `tests.helpers.replay_fem_read_smoke` | 56 | — | smoke facade (BV12C capped) |
| `game.final_emission_gate` | 30 | — | gate orchestration owner |
| `game.final_emission_terminal_pipeline` | 26 | — | terminal finalize coupling |

## Candidate evaluation

| Candidate | FI | Assessment | Risk | BV15 fit |
| --- | --- | --- | --- | --- |
| `game.final_emission_gate` | 30 | Largest remaining production orchestration owner; BN preflight extractions ongoing | Medium — owner module; gate stack coupling | **Primary** |
| `game.final_emission_terminal_pipeline` | 26 | Finalize/terminal coupling with gate + strict-social stack; heterogeneous finalize paths | Medium — terminal owner semantics | **Secondary** (paired with gate) |
| `game.final_emission_text_formatting` | 51 | Post-BV13 intentional primitive hub; homogeneous symbol category; BV13C governed | Low — already decomposed and capped | Defer — maintenance acceptable |
| Domain smoke facades | 56+39 | Post-BV12 intentional; BV12C capped at 2 each | Low — governed test hubs | Defer |
| Recurrence/fallback residuals | — | BV8/BV9 retirement evidence; no new production FI choke post-BV14 | Low — observability + retirement registry | Defer — monitor via BV9 matrix |

## BV15 recommendation

**Select `game.final_emission_gate` as BV15 target** (with `final_emission_terminal_pipeline` as paired follow-on).

Evidence:

- Highest remaining **production-core orchestration** FI after BV14 social-exchange decomposition
- BN1–BN11 preflight extractions already reduced gate_context surface; gate owner FI still ~30
- Terminal pipeline FI ~26 shares finalize coupling — natural Phase 2 after gate owner split
- Formatting hub and smoke facades are governed; recurrence residuals are retirement-tracked not FI-chokes

Suggested BV15 scope:

1. Gate owner vs terminal pipeline authority boundary audit (orchestration vs finalize)
2. Consumer migration for preflight/helper imports already extracted in BN series
3. Import guard + FI cap pattern mirroring BV13C/BV14C governance

