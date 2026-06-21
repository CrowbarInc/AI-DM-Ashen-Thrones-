# BV14A — Extraction Report

**Date:** 2026-06-21  
**Phase:** BV14A — domain extraction (compat preserved)  
**Primary metric:** Decomposition readiness

---

## Module fan-in baseline

| Module | AST FI (post-BV14A) | LOC | Role |
| --- | --- | --- | --- |
| `game.social_exchange_emission` | **55** (compat; BU baseline still **52**) | 1,563 | Composition + re-exports |
| `game.social_exchange_fallback_catalog` | 0 direct external | 828 | Canonical fallback |
| `game.social_exchange_policy` | 0 direct external | 898 | Canonical policy |
| `game.social_exchange_validation` | 0 direct external | 578 | Canonical validation |
| `game.social_exchange_projection` | 0 direct external | 97 | Canonical projection |

**Compat FI unchanged (52–55):** all existing consumers still import via `social_exchange_emission` — expected for BV14A.

---

## Symbol split (canonical ownership)

| Domain | Key symbols | Est. symbol FI (BU) |
| --- | --- | --- |
| Fallback catalog | `minimal_social_emergency_fallback_line` (10), `select_*` (2), `deterministic_*` (3) | ~20 |
| Policy | `strict_social_emission_will_apply` (9), `merged_player_prompt_for_gate` (7), `effective_*` (7) | ~15 |
| Validation | `is_route_illegal_*` (4), `replacement_is_route_legal_social` (1) | ~6 |
| Projection | `log_final_emission_*` (3), FEM family stamp/project (2) | ~5 |
| Composition (compat) | `build_final_strict_social_response` (8), `hard_reject_*` (1) | ~10 |

---

## Migration-ready import count (BV14B)

| Consumer layer | Files importing compat | Phase 2 target module |
| --- | --- | --- |
| Production (`game/`) | 27 | fallback / policy / validation / projection |
| Tests (`tests/`) | 26 | direct domain imports |
| **Total** | **53** | — |

### Wave priority (from BV14 plan)

| Wave | Expected Δ compat FI | Risk |
| --- | --- | --- |
| 2A Fallback sprawl | −18 | Medium-high (phrase catalog) |
| 2B Policy / API / preflight | −12 | Low-medium |
| 2C Validation | −6 | Low |
| 2D Projection / telemetry | −5 | Low |
| 2E Tests | −15 | Low |

**Projected compat FI after BV14B:** **52 → ~6–10**

---

## Validation results (BV14A gate)

| Suite cluster | Tests | Result |
| --- | --- | --- |
| Strict-social (`test_social_exchange_emission`, quality, emergency fallback) | 120+ | **Green** |
| Replay / transcript (`test_narration_transcript_regressions`) | 40+ | **Green** |
| Gate orchestration (`test_final_emission_gate_orchestration_order`) | 30+ | **Green** |
| Validators (`test_final_emission_validators`) | 40+ | **Green** |
| Fallback (`test_final_emission_visibility_fallback`, boundary convergence) | 50+ | **Green** |
| BV14A delegate verification | 6 | **Green** |

**Total validated:** 329 tests across 10 requested suites + delegate tests.

---

## Decomposition readiness scorecard

| Criterion | Status |
| --- | --- |
| Canonical modules exist | **Yes** — 4 domain owners |
| Compat re-exports preserve import paths | **Yes** — FI unchanged |
| Composition authority isolated | **Yes** — `build_final_strict_social_response` local |
| No logic duplication | **Yes** — `is` identity verified |
| Private leaks inventoried | **Yes** — see `BV14A_private_leak_inventory.md` |
| BV14B consumer migration unblocked | **Yes** |

**Verdict:** BV14B consumer migration can begin safely.
