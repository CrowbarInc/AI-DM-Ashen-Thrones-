# BV7B — Remaining `emission_smoke_assertions` Importers

**Date:** 2026-06-21  
**Baseline (pre-BV7B):** 30 module fan-in (post-BV7A)  
**Scope:** Residual direct importers after AC/RD/RT consumer-layer extraction

---

## Summary

After BV7B, **15 suites** retain direct `emission_smoke_assertions` imports (phrase/route/speaker smoke and the compatibility constant `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH`). **16 suites** migrated to family-specific helpers. Two additional files use dynamic `import emission_smoke_assertions as smoke` (ownership/delegator regression) and are excluded from static FI.

---

## By assertion family

### response_type_contract (RT) — migrated off monolith

| File | Symbols migrated |
|---|---|
| `tests/helpers/opening_fallback_evidence.py` | `response_type_contract` |
| `tests/test_tone_escalation_rules.py` | `response_type_contract` |
| `tests/test_speaker_contract_enforcement.py` | `response_type_contract` |
| `tests/test_prompt_context.py` | `response_type_contract` |
| `tests/test_player_facing_narration_purity.py` | `response_type_contract` |
| `tests/test_narration_transcript_regressions.py` | `response_type_contract` |
| `tests/test_final_emission_opening_fallback.py` | `response_type_contract` |
| `tests/test_fallback_behavior_repairs.py` | `response_type_contract` |
| `tests/test_fallback_behavior_gate.py` | `response_type_contract` |
| `tests/test_final_emission_gate_orchestration_order.py` | `response_type_contract` |
| `tests/test_final_emission_gate_diagnostics.py` | `response_type_contract` |
| `tests/test_final_emission_response_type.py` | `response_type_contract` |
| `tests/test_response_policy_contracts.py` | `response_type_contract`, `enforce_response_type_contract_layer` |
| `tests/test_emission_smoke_assertions_contract.py` | `response_type_contract`, `enforce_response_type_contract_layer` (partial) |

**Target module:** `tests/helpers/response_type_smoke.py`

---

### actor-consistency (AC) — migrated off monolith

| File | Symbols migrated |
|---|---|
| `tests/test_answer_completeness_rules.py` | `validate_answer_completeness`, `apply_answer_completeness_layer` |
| `tests/test_final_emission_boundary_convergence.py` | `apply_answer_completeness_layer` |
| `tests/test_response_delta_requirement.py` | `skip_answer_completeness_layer` |

**Target module:** `tests/helpers/actor_consistency_smoke.py`

---

### route-determinism (RD) — migrated off monolith

| File | Symbols migrated |
|---|---|
| `tests/test_answer_completeness_rules.py` | `assert_no_boundary_reorder_repair` |
| `tests/test_final_emission_boundary_convergence.py` | `apply_response_delta_layer` |
| `tests/test_response_delta_requirement.py` | full RD seam bundle |

**Target module:** `tests/helpers/route_determinism_smoke.py`

---

### phrase smoke — still on monolith (intentional)

| File | Symbols |
|---|---|
| `tests/test_emission_smoke_assertions_contract.py` | phrase/repair smoke helpers |
| `tests/test_turn_pipeline_shared.py` | phrase hygiene bundle |
| `tests/test_mixed_state_recovery_regressions.py` | `assert_global_visibility_stock_absent`, `assert_no_social_visible_intro_filler_smoke` |
| `tests/test_broad_address_social_bid.py` | `assert_no_unresolved_stock_phrases` |
| `tests/test_synthetic_smoke.py` | `SMOKE_SYNTHETIC_*` pattern tuples |

---

### speaker smoke — still on monolith (intentional)

| File | Symbols |
|---|---|
| `tests/test_social_speaker_grounding.py` | `assert_social_grounding_smoke` |
| `tests/test_broadcast_open_call_social.py` | open-call routing smoke bundle |
| `tests/test_interaction_continuity_repair.py` | `assert_continuity_validation_failed_without_repair` + route smoke |

---

### route wiring smoke — still on monolith (intentional)

| File | Symbols |
|---|---|
| `tests/test_turn_packet_stage_diff_integration.py` | `assert_final_route_present_smoke` |
| `tests/test_c4_narrative_mode_live_pipeline.py` | `assert_final_route_*` |
| `tests/test_diegetic_fallback_narration.py` | `assert_final_route_*` |
| `tests/test_empty_social_retry_regressions.py` | `assert_final_route_replaced_or_not_accept` |
| `tests/test_interaction_continuity_repair.py` | `assert_final_route_*` |
| `tests/test_opening_start_seam_regressions.py` | `has_non_accept_final_route_smoke` |
| `tests/test_social_exchange_emission.py` | `assert_final_route_replaced_or_not_accept` |
| `tests/test_turn_pipeline_shared.py` | dialogue-lock route smoke |

---

### mixed suites — split imports (partial monolith retention)

| File | Monolith retained | Family module |
|---|---|---|
| `tests/test_turn_pipeline_shared.py` | phrase + route smoke | `response_type_smoke` (RT meta surfaces) |
| `tests/test_emission_smoke_assertions_contract.py` | phrase/repair smoke | `response_type_smoke` (RT layer) |
| `tests/test_answer_completeness_rules.py` | `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` | `actor_consistency_smoke`, `route_determinism_smoke` |
| `tests/test_broad_address_social_bid.py` | phrase + open-call route | — |
| `tests/test_interaction_continuity_repair.py` | route + continuity speaker | — |

---

## Dynamic importers (not in static FI)

| File | Pattern |
|---|---|
| `tests/test_ownership_registry.py` | `from tests.helpers import emission_smoke_assertions as smoke` |
| `tests/test_final_emission_gate_delegator_regression.py` | lazy import in test body |

---

## Migration totals

| Category | Files |
|---|---:|
| Fully migrated off monolith | 12 |
| Split (family + monolith smoke) | 4 |
| Monolith-only (phrase/route/speaker) | 11 |
| Dynamic import | 2 |
