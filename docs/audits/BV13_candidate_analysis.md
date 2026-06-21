# BV13 — Candidate Analysis

**Date:** 2026-06-21  
**Context:** BV12 closed; compat bridge regrowth blocked.

---

## Current top fan-in (selected)

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

## Re-ranked decomposition candidates

| Rank | Target | FI | Rationale | Risk |
| --- | --- | --- | --- | --- |
| **1 (BV13)** | `game.final_emission_text` | 52 | Largest production text choke; 39 in-game importers; pregate/finalize policy sprawl | Medium — production core |
| 2 | `game.social_exchange_emission` | 52 | Tied production FI; strict-social composition cross-cuts gate stack | Medium-high — social authority surface |
| 3 | `game.final_emission_gate` | 30 | Gate owner; BN preflight extractions ongoing; 28 test importers | Medium — owner module |
| 4 | `game.final_emission_terminal_pipeline` | 26 | Hub-flagged terminal stack; 23 test + 2 production importers | Medium — finalize coupling |
| 5 | Domain smoke facades | 56+39 | Post-BV12 intentional; defer until production cores decompose | Low — governed hubs |
| 6 | Recurrence / fallback residuals | — | `final_emission_replay_projection`, fallback provenance, golden replay drift | Low-medium — observability band |

## BV13 recommendation

**Select `game.final_emission_text` as BV13 target.**

Evidence:

- Tied for highest production FI (52) with `social_exchange_emission`
- Text/policy functions cross-cut gate preflight, finalize, and composition layers
- BV12 removed test-bridge concentration; next ROI is **production core decomposition**
- `social_exchange_emission` remains BV14 parallel candidate (social-specific authority)

Suggested BV13 scope:

1. Symbol concentration audit (pregate vs finalize vs validator text helpers)
2. Extraction candidates aligned to BN preflight boundaries already in place
3. Import guard + FI cap pattern mirroring BV12C governance

