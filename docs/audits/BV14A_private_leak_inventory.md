# BV14A — Private Leak Inventory

**Date:** 2026-06-21  
**Phase:** BV14A extraction (compat preserved; leaks not fixed)  
**Method:** AST importer scan + production import grep

---

## Summary

**11** external importers still reach for `_`-prefixed symbols via `game.social_exchange_emission` compat barrel. BV14B should migrate consumers to named domain modules and eliminate private cross-module imports.

| Leaked symbol | AST FI | Canonical owner (post-BV14A) | Projected BV14B target |
| --- | --- | --- | --- |
| `_npc_display_name_for_emission` | 4 | `social_exchange_policy` | Promote public `npc_display_name_for_emission` on policy |
| `_active_interlocutor_matches_resolution_social_npc` | 2 | `social_exchange_fallback_catalog` | Promote on fallback or policy |
| `_has_explicit_interruption_shape` | 2 | `social_exchange_validation` | Import validation directly |
| `_speaker_label` | 2 | `social_exchange_policy` | Promote public on policy |
| `_text_is_strict_social_minimal_emergency_fallback` | 2 | `social_exchange_fallback_catalog` | Import fallback_catalog |
| `_merge_open_social_recovery_emission_debug` | 1 | `social_exchange_fallback_catalog` | Import fallback_catalog |
| `_open_social_recovery_passes_anti_stall` | 1 | `social_exchange_fallback_catalog` | Import fallback_catalog |
| `_apply_interruption_repeat_guard` | 1 | `social_exchange_emission` (composition) | Keep on composition or promote |
| `_social_integrity_fallback_line_candidates` | 1 | `social_exchange_fallback_catalog` | Import fallback_catalog |

---

## Production importers (encapsulation violations)

| File | Private symbols | Ownership bucket |
| --- | --- | --- |
| `game/final_emission_referential_clarity.py` | `_active_interlocutor_matches_resolution_social_npc`, `_npc_display_name_for_emission`, `_speaker_label` | referential clarity repair |
| `game/final_emission_visibility_fallback.py` | `_npc_display_name_for_emission` | terminal fallback |
| `game/speaker_contract_enforcement.py` | `_has_explicit_interruption_shape`, `_npc_display_name_for_emission` | speaker finalization |
| `game/emitted_speaker_signature.py` | `_has_explicit_interruption_shape` | speaker signature |
| `game/upstream_response_repairs.py` | `_npc_display_name_for_emission` | upstream repair |
| `game/dialogue_social_plan.py` | `_text_is_strict_social_minimal_emergency_fallback` | narrative/social |
| `game/gm_retry.py` | `_merge_open_social_recovery_emission_debug` | GM retry recovery |

---

## Test importers

| File | Private symbols |
| --- | --- |
| `tests/test_social_exchange_emission.py` | `_apply_interruption_repeat_guard`, `_social_integrity_fallback_line_candidates` |
| `tests/test_broad_address_social_bid.py` | `_open_social_recovery_passes_anti_stall` |

---

## Migration paths (BV14B — not implemented in BV14A)

| Wave | Action | Expected Δ compat FI |
| --- | --- | --- |
| B1 | Promote `_npc_display_name_for_emission`, `_speaker_label` → public on `social_exchange_policy` | −4 private leak calls |
| B2 | Promote fallback helpers on `social_exchange_fallback_catalog` | −6 |
| B3 | Route validation private scans via `social_exchange_validation` | −2 |
| B4 | Cap compat private re-exports in BV14C governance lock | prevent regrowth |

**Note:** BV14A preserves all compat imports unchanged; leaks remain intentionally documented for Phase 2.
