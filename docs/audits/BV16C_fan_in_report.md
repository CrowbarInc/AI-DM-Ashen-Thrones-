# BV16C — Fan-In Report

**Date:** 2026-06-21

## Module AST fan-in (tests + production)

| Module | AST importers | Production | Tests | Top symbol AST FI |
| --- | --- | --- | --- | --- |
| `terminal_pipeline` | **9** | 0 | 9 | `terminal_pipeline` (7) |
| `visibility_fallback` | **25** | 0 | 25 | `visibility_fallback` (21) |
| `acceptance_quality` | **6** | 0 | 6 | `acceptance_quality` (3) |
| `interaction_continuity` | **11** | 0 | 11 | `apply_interaction_continuity_emission_step` (5) |
| `opening_fallback` | **6** | 0 | 6 | `opening_fallback` (3) |

## BV16 projection vs actual

| Metric | BV16 projected | BV16C actual |
| --- | --- | --- |
| Terminal AST FI | 6–8 | **9** |
| Visibility noop via terminal namespace | ~16 | **0** |

## Success criteria

| Criterion | Status |
| --- | --- |
| Terminal remains centralized authority | **Yes** — production exit owners unchanged |
| Test/governance FI inflation removed | **Yes** — AST 26 → 9 |
| Stale delegate monkeypatches | **0** remaining |
| Replay / ordering unchanged | Validated by targeted pytest suites |
