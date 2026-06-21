# BV7 — Smoke Facade Decomposition Candidates

**Date:** 2026-06-21
**Goal:** Reduce module FI while preserving BE6 triple-layer smoke boundaries.

## Candidate ranking (by projected FI relief)

| Rank | Module candidate | Source family | Current consumer FI | Migration cost | Risk | Projected module FI after split |
|---:|---|---|---:|---|---|---:|
| 1 | `replay_smoke_assertions.py` | FEM/read bridge | **~42** | 2/5 | Low | **~31** (thin re-export) → **~12–18** (post-migration) |
| 2 | `gate_integration_smoke.py` | Gate integration bridge | **~37** | 3/5 | Medium | **~36** (thin re-export) → **~12–18** (post-migration) |
| 3 | `consumer_layer_smoke.py` | Consumer layer bridge (AC/RD/RT) | **~18** | 4/5 | Medium | **~55** (thin re-export) → **~12–18** (post-migration) |
| 4 | `route_smoke_assertions.py` | Route wiring smoke | **~8** | 2/5 | Low | **~65** (thin re-export) → **~12–18** (post-migration) |
| 5 | `fallback_smoke_assertions.py` | Phrase/hygiene smoke | **~4** | 2/5 | Low | **~69** (thin re-export) → **~12–18** (post-migration) |
| 6 | `speaker_smoke_assertions.py` | Social/open-call smoke | **~4** | 2/5 | Low | **~69** (thin re-export) → **~12–18** (post-migration) |
| 7 | `attribution_smoke_assertions.py` | Open-call / broadcast routing | **~2** | 1/5 | Low | **~71** (thin re-export) → **~12–18** (post-migration) |

## Candidate detail

### `replay_smoke_assertions.py`

- **Source family:** FEM/read bridge
- **Symbols:** `final_emission_meta_from_output`, `read_turn_debug_notes`
- **Projected FI reduction:** −42 on extracted surface (overlap-adjusted module FI drop **~42**)
- **Migration cost:** 2/5
- **Risk:** Low
- **Notes:** Extract to `tests/helpers/replay_smoke_assertions.py`; re-export from thin facade during migration.

### `gate_integration_smoke.py`

- **Source family:** Gate integration bridge
- **Symbols:** `apply_final_emission_gate_consumer`, `gm_response_stub`
- **Projected FI reduction:** −37 on extracted surface (overlap-adjusted module FI drop **~37**)
- **Migration cost:** 3/5
- **Risk:** Medium
- **Notes:** Co-locate with `strict_social_harness` / runtime seam docs; shrink gate-consumer FI on monolith.

### `consumer_layer_smoke.py`

- **Source family:** Consumer layer bridge (AC/RD/RT)
- **Symbols:** `response_type_contract`, `validate_answer_completeness`, `apply_*_layer`, `enforce_response_type_contract_layer`, `assert_response_delta_*`
- **Projected FI reduction:** −18 on extracted surface (overlap-adjusted module FI drop **~18**)
- **Migration cost:** 4/5
- **Risk:** Medium
- **Notes:** Merge with or alias `repairs_consumer_facade`; registry already splits AC/RD owners.

### `route_smoke_assertions.py`

- **Source family:** Route wiring smoke
- **Symbols:** `assert_final_route_*`, `has_non_accept_final_route_smoke`, `assert_dialogue_lock_*`
- **Projected FI reduction:** −8 on extracted surface (overlap-adjusted module FI drop **~8**)
- **Migration cost:** 2/5
- **Risk:** Low
- **Notes:** Pure smoke; aligns with AL3 route wiring charter.

### `fallback_smoke_assertions.py`

- **Source family:** Phrase/hygiene smoke
- **Symbols:** `assert_*_smoke phrase helpers`, `SMOKE_*_PHRASES`
- **Projected FI reduction:** −4 on extracted surface (overlap-adjusted module FI drop **~4**)
- **Migration cost:** 2/5
- **Risk:** Low
- **Notes:** Preserve BE6 layer-2 separation from sanitizer owner.

### `speaker_smoke_assertions.py`

- **Source family:** Social/open-call smoke
- **Symbols:** `assert_social_grounding_smoke`, `assert_open_*`, `assert_broadcast_*`
- **Projected FI reduction:** −4 on extracted surface (overlap-adjusted module FI drop **~4**)
- **Migration cost:** 2/5
- **Risk:** Low
- **Notes:** Isolate social routing smoke from FEM/gate bridges.

### `attribution_smoke_assertions.py`

- **Source family:** Open-call / broadcast routing
- **Symbols:** `assert_open_social_solicitation_route`, `assert_broadcast_open_call_*`
- **Projected FI reduction:** −2 on extracted surface (overlap-adjusted module FI drop **~2**)
- **Migration cost:** 1/5
- **Risk:** Low
- **Notes:** Optional merge with speaker_smoke_assertions.

## Overlap adjustment

Many files import **both** `final_emission_meta_from_output` and `apply_final_emission_gate_consumer`. Extracting both bridges yields **~45–52** unique consumer migrations, not 79 additive.

**Highest-ROI pair:** `replay_smoke_assertions` + `gate_integration_smoke` (−~55 unique files, module FI → **~15–20** with re-exports).
