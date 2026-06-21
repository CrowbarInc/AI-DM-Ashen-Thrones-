# BV13A — Extraction Report

**Date:** 2026-06-21  
**Phase:** BV13 Phase 1 complete  
**Method:** `python tools/bv13_final_emission_text_discovery.py`

---

## Module split summary

| Module | LOC | Exports | Production importers (direct) | Role |
| --- | --- | --- | --- | --- |
| `final_emission_text_formatting` | 71 | 6 functions | 0 (Phase 1) | Canonical formatting |
| `final_emission_text_policy` | 79 | 6 constants | 0 (Phase 1) | Canonical policy vocabulary |
| `final_emission_text_legacy_semantic_repair` | 318 | 2 public + helpers | 0 | Test-only legacy repair |
| `final_emission_text` (compat) | 58 | re-exports + 1 wrapper | **52** | Compatibility barrel |

---

## Fan-in baseline (post-extraction)

| Module | BU FI | AST direct importers | Notes |
| --- | --- | --- | --- |
| `game.final_emission_text` | **52** | 52 | Unchanged — compat re-exports preserve import graph |
| `game.final_emission_text_formatting` | 0* | 2 | compat barrel + legacy module |
| `game.final_emission_text_policy` | 0* | 1 | compat barrel only |
| `game.final_emission_text_legacy_semantic_repair` | 0* | 1 | compat barrel only |

\* BU CSV not yet refreshed; internal fan-in only until Phase 2 migration begins.

### Symbol FI (unchanged at compat surface)

| Symbol | Compat FI | Canonical owner after Phase 2 |
| --- | --- | --- |
| `_normalize_text` | 47 | `final_emission_text_formatting` |
| `_normalize_terminal_punctuation` | 4 | formatting |
| `_ACTION_RESULT_PATTERNS` | 3 | policy |
| `_ANSWER_DIRECT_PATTERNS` | 3 | policy |
| `_normalize_text_preserve_paragraphs` | 3 | formatting |
| `_global_narrative_fallback_stock_line` | 3 | compat (fallback wrapper) |
| `_sanitize_output_text` | 2 | formatting |
| `_ANSWER_FILLER_PATTERNS` | 2 | policy |
| `_RESPONSE_TYPE_VALUES` | 2 | policy |
| Other policy/formatting | 1 each | respective owner |

---

## Migration-ready import count (Phase 2)

| Target module | Consumers to migrate | Share |
| --- | --- | --- |
| `final_emission_text_formatting` | **~47** (`_normalize_text` alone) + 6 multi-symbol | ~90% of compat FI |
| `final_emission_text_policy` | **~6** unique modules | ~12% of compat FI |
| Stay on compat | **~3** (fallback stock line) + governance | ~6% residual |

### By usage class (from BV13 discovery)

| Class | Importers | Phase 2 wave |
| --- | --- | --- |
| gate | 28 | 2A |
| finalization | 10 | 2B |
| diagnostics | 6 | 2D (fallback) |
| tests | 13 | 2E |

**Total migration-ready:** **52** direct compat importers (mechanical import path rewrite).

---

## Projected Phase 2 FI reduction

| Stage | `final_emission_text` FI | `formatting` FI | `policy` FI |
| --- | --- | --- | --- |
| BV13A (now) | **52** | 2 (internal) | 1 (internal) |
| After Phase 2 migration | **~5–8** | **~47** | **~6** |
| Δ vs baseline | **−44 to −47** | +45 | +5 |

---

## Validation summary

| Suite | Result |
| --- | --- |
| `test_bv13a_final_emission_text_facade_delegates` | **Pass** (8 tests) |
| Final emission visibility / boundary | **Pass** |
| Response policy / acceptance quality | **Pass** |
| BJ-111/112 delegator normalize ownership | **Pass** |
| Gate BJ-129 thin boundary | Pre-existing gate import residue (unchanged by BV13A) |

Replay parity: formatting functions are **identical objects** re-exported through compat barrel — no text output delta expected.

---

## Decomposition readiness

| Criterion | Status |
| --- | --- |
| Formatting separated from policy | **Ready** |
| Legacy repair isolated | **Ready** |
| Compat barrel preserves all consumer imports | **Ready** |
| Delegate verification automated | **Ready** |
| Phase 2 migration can begin | **Yes** |
