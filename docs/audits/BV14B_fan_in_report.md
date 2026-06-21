# BV14B — Fan-In Report

**Date:** 2026-06-21

## Module fan-in

| Module | Before (BV14A) | After (BV14B) | Delta |
| --- | --- | --- | --- |
| `game.social_exchange_emission` | **52** | **12** | **-40** |
| `game.social_exchange_fallback_catalog` | 0 (direct external) | **24** | **+24** |
| `game.social_exchange_policy` | 0 (direct external) | **29** | **+29** |
| `game.social_exchange_validation` | 0 (direct external) | **12** | **+12** |
| `game.social_exchange_projection` | 0 (direct external) | **11** | **+11** |

## Symbol moves by domain

| Domain | Symbol moves |
| --- | --- |
| policy | 44 |
| fallback_catalog | 44 |
| projection | 18 |
| composition | 14 |
| validation | 9 |

## Residual compat importers

**12** files still import `game.social_exchange_emission` (target ≤12; projected steady-state 6–10):

- `game/final_emission_strict_social_stack.py`
- `game/social_exchange_validation.py`
- `tests/helpers/gate_thin_boundary_locks.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_ownership_registry.py`
- `tests/test_realization_provenance.py`
- `tests/test_social_answer_candidate.py`
- `tests/test_social_emission_quality.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_social_speaker_grounding.py`
- `tests/test_social_target_authority_regressions.py`
- `tools/bv14a_extract_domains.py`

## Private leak cleanup (BV14A → BV14B)

| Former private symbol | Public surface | Canonical module |
| --- | --- | --- |
| `_npc_display_name_for_emission` | `npc_display_name_for_emission` | `social_exchange_policy` |
| `_speaker_label` | `speaker_label` | `social_exchange_policy` |
| `_has_explicit_interruption_shape` | `has_explicit_interruption_shape` | `social_exchange_validation` |
| `_text_is_strict_social_minimal_emergency_fallback` | `text_is_strict_social_minimal_emergency_fallback` | `social_exchange_fallback_catalog` |
| `_active_interlocutor_matches_resolution_social_npc` | `active_interlocutor_matches_resolution_social_npc` | `social_exchange_fallback_catalog` |
| `_merge_open_social_recovery_emission_debug` | `merge_open_social_recovery_emission_debug` | `social_exchange_fallback_catalog` |
| `_open_social_recovery_passes_anti_stall` | `open_social_recovery_passes_anti_stall` | `social_exchange_fallback_catalog` |
| `_social_integrity_fallback_line_candidates` | `social_integrity_fallback_line_candidates` | `social_exchange_fallback_catalog` |
| `_apply_interruption_repeat_guard` | `apply_interruption_repeat_guard` | `social_exchange_emission` (composition) |

External production imports of `_`-prefixed symbols via compat barrel: **0** (post-BV14B).

## Success criteria

- Compat FI **52 → 12** (target ≤12)
- No runtime/replay/strict-social behavior changes (compat re-exports preserved)
- Private symbol leaks eliminated from external compat imports
