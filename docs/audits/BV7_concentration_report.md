# BV7 — Smoke Facade Concentration Report

**Date:** 2026-06-21
**Primary metric:** Fan-in concentration

## Executive answer

`tests.helpers.emission_smoke_assertions` remains the **largest ecosystem fan-in node** at **73 FI** — unchanged through BV2–BV5 despite meta read-side redistribution. The facade is **partially intentional** (Cycle AL4/AS2 downstream smoke surface) but has **accidentally absorbed** BV2-scale read and gate-integration bridges, making it a cross-cutting maintenance hub beyond smoke-only scope.

## Module-level fan-in (top hubs)

| Rank | Module | FI | vs smoke |
|---:|---|---:|---|
| 1 | `tests.helpers.emission_smoke_assertions` | **73** | baseline |
| 2 | `game.final_emission_text` | **52** | -21 vs smoke |
| 3 | `game.social_exchange_emission` | **52** | -21 vs smoke |
| 4 | `game.final_emission_gate` | **30** | -43 vs smoke |
| 5 | `game.final_emission_meta_read` | **28** | -45 vs smoke |
| 6 | `game.realization_provenance` | **28** | -45 vs smoke |
| 7 | `game.final_emission_terminal_pipeline` | **26** | -47 vs smoke |
| 8 | `game.final_emission_meta` | **24** | -49 vs smoke |

## Smoke facade fan-out

| Production dependency | Role |
|---|---|
| `game.final_emission_meta_read` | FEM + debug read delegate (BV2 read facade) |
| `game.final_emission_runtime` | Gate orchestration via `apply_final_emission_gate_consumer` |
| `game.final_emission_validators` | AC/RD validator seams |
| `game.final_emission_repairs` | AC/RD layer seams |
| `game.final_emission_response_type` | Response-type enforcement seam |

**Fan-out:** 5 production modules (+ typing/stdlib). Narrow FO vs FI — classic **hub-and-spoke test delegate** shape.

## Symbol-level ownership concentration

| Symbol | FI | % of module FI | Owner intent |
|---|---:|---:|---|
| `final_emission_meta_from_output` | 42 | 58% | FEM read bridge (BV2 read-side spillover) |
| `apply_final_emission_gate_consumer` | 37 | 51% | Gate integration bridge (AS2 consumer seam) |
| `response_type_contract` | 14 | 19% | Test scaffold helper |

Top-3 symbols account for **~93 symbol-imports** across **~55 unique files** (heavy overlap: gate + FEM co-import).

## Legitimate aggregation vs accidental hub

| Signal | Legitimate facade | Accidental hub |
|---|---|---|
| Documented AS2/AL4 downstream smoke charter | ✓ | |
| BE6 triple-layer phrase split enforced in registry | ✓ | |
| 58% FI on FEM read re-export (duplicates `final_emission_meta_read` test path) | | ✓ |
| 51% FI on full gate orchestration wrapper | | ✓ (belongs beside `strict_social_harness`) |
| AC/RD/RT layer bridges (18 consumers) parallel `repairs_consumer_facade` | | ✓ |
| BV2–BV5 added +3 net importers while meta FI fell −64% | | ✓ (concentration persisted) |

**Verdict:** **Hybrid** — smoke phrase/route families are legitimate; **read + gate + consumer bridges** create accidental maintenance drag.

## Evidence

| Source | Role |
|---|---|
| [BV5_hub_comparison.md](BV5_hub_comparison.md) | Pre-BV7 hub baseline |
| [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md) | Meta FI reduction contrast |
| `tests/test_ownership_registry.py` | BE6 / BJ-4 facade governance locks |
