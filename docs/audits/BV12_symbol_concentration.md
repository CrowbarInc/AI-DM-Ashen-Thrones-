# BV12 — Symbol Concentration Analysis

**Date:** 2026-06-21  
**Method:** Per-symbol importer scan (aliases normalized to source export)  

---

## Executive answer

Both bridge modules are **already minimal** (2 exports each, <60 LOC). High module FI is **symbol concentration**, not helper sprawl: `final_emission_meta_from_output` (~55 effective FI) and `apply_final_emission_gate_consumer` (39 FI) dominate.

## Symbol fan-in (effective, alias-normalized)

| Module | Symbol | Effective FI | Role |
| --- | --- | --- | --- |
| replay_smoke_assertions | `final_emission_meta_from_output` | 67 | FEM read bridge (BV7A/BV10C) |
| replay_smoke_assertions | `read_turn_debug_notes` | 3 | Turn-packet debug notes (pipeline/HTTP) |
| gate_integration_smoke | `apply_final_emission_gate_consumer` | 39 | Full gate orchestration via runtime |
| gate_integration_smoke | `gm_response_stub` | 3 | Fake GM HTTP fixture stub |

## Classification

| Category | Symbols | Combined effective FI |
| --- | --- | --- |
| Bridge symbols (cross-domain) | final_emission_meta_from_output, apply_final_emission_gate_consumer | ~94 |
| Replay-only symbols | read_turn_debug_notes | 3 |
| Gate-only symbols | gm_response_stub | 2 |
| Internal coupling | gate → replay (final_emission_meta_from_output) | 1 module edge |

## Highest fan-in helpers (ranked)

| Rank | Symbol | FI | Risk |
| --- | --- | --- | --- |
| 1 | final_emission_meta_from_output | 67 | high — post-BV10C routing hub |
| 2 | apply_final_emission_gate_consumer | 39 | high — gate orchestration choke point |
| 3 | read_turn_debug_notes | 3 | low — narrow pipeline surface |
| 4 | gm_response_stub | 3 | low — fixture-only |

