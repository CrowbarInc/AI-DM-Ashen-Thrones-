# BV14 — Social Exchange Emission Dependency Inventory

**Date:** 2026-06-21
**Scope:** Analysis only — every direct importer of `game.social_exchange_emission`
**Method:** `python tools/bv14_social_exchange_emission_discovery.py` + BU CSV reconciliation

---

## Hub baseline (current)

| Module | BU fan-in | AST direct importers | Public exports | LOC | Fan-out |
| --- | --- | --- | --- | --- | --- |
| `game.social_exchange_emission` | **52** | 52 | 47 | 3881 | 17 |

**BV13 context:** `final_emission_text` compat FI **52 → 5**; `social_exchange_emission` is now the highest-ranked remaining **production-core** concentration.

## Importer split

| Layer | Count | Share |
| --- | --- | --- |
| Production (`game/`) | 27 | 51% |
| Tests (`tests/`) | 25 | 48% |

## Summary by subsystem

| Subsystem | Importers | Primary symbols |
| --- | --- | --- |
| final emission pipeline | 13 | `minimal_social_emergency_fallback_line` |
| speaker/social | 10 | `build_final_strict_social_response` |
| production runtime | 8 | `strict_social_emission_will_apply` |
| final emission gate | 6 | `effective_strict_social_resolution_for_emission` |
| integration/regression | 6 | `social_exchange_emission (module)` |
| narrative/social | 5 | `strict_social_ownership_terminal_fallback` |
| speaker helpers | 1 | `effective_strict_social_resolution_for_emission` |
| HTTP/pipeline integration | 1 | `apply_social_exchange_retry_fallback_gm` |
| replay | 1 | `_sse (module)` |
| ownership governance | 1 | `social_exchange_emission (module)` |

## Full importer table

| File | Subsystem | Symbols imported | Ownership bucket |
| --- | --- | --- | --- |
| `game/anti_reset_emission_guard.py` | production runtime | `effective_strict_social_resolution_for_emission`, `minimal_social_emergency_fallback_line` | fallback-emission |
| `game/api.py` | production runtime | `strict_social_emission_will_apply` | gate-preflight-policy |
| `game/api_turn_support.py` | production runtime | `strict_social_emission_will_apply` | gate-preflight-policy |
| `game/dialogue_social_plan.py` | narrative/social | `_text_is_strict_social_minimal_emergency_fallback`, `strict_social_ownership_terminal_fallback` | fallback-emission |
| `game/emitted_speaker_signature.py` | narrative/social | `_has_explicit_interruption_shape`, `interruption_cue_present_in_text` | eligibility-policy |
| `game/final_emission_answer_shape_primacy.py` | final emission pipeline | `merged_player_prompt_for_gate` | gate-preflight-policy |
| `game/final_emission_anti_railroading.py` | final emission pipeline | `merged_player_prompt_for_gate` | gate-preflight-policy |
| `game/final_emission_context_separation.py` | final emission pipeline | `merged_player_prompt_for_gate` | gate-preflight-policy |
| `game/final_emission_fem_assembly.py` | final emission pipeline | `project_strict_social_replace_realization_family` | realization-projection |
| `game/final_emission_gate_preflight_strict_social.py` | final emission gate | `effective_strict_social_resolution_for_emission`, `merged_player_prompt_for_gate`, `strict_social_emission_will_apply`, `strict_social_suppress_non_native_coercion_for_narration_beat` | realization-projection |
| `game/final_emission_generic_exit.py` | final emission pipeline | `log_final_emission_decision`, `log_final_emission_trace` | telemetry-projection |
| `game/final_emission_narrative_authority.py` | final emission pipeline | `merged_player_prompt_for_gate` | gate-preflight-policy |
| `game/final_emission_referential_clarity.py` | final emission pipeline | `_active_interlocutor_matches_resolution_social_npc`, `_npc_display_name_for_emission`, `_speaker_label`, `is_route_illegal_global_or_sanitizer_fallback_text`, `strict_social_emission_will_apply` | route-legality-validator |
| `game/final_emission_response_type.py` | final emission pipeline | `minimal_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` | fallback-emission |
| `game/final_emission_sealed_fallback.py` | final emission pipeline | `minimal_social_emergency_fallback_line` | fallback-emission |
| `game/final_emission_strict_social_stack.py` | final emission pipeline | `build_final_strict_social_response`, `log_final_emission_decision`, `log_final_emission_trace`, `minimal_social_emergency_fallback_line`, `strict_social_deterministic_fallback_family_token` | fallback-emission |
| `game/final_emission_terminal_pipeline.py` | final emission pipeline | `minimal_social_emergency_fallback_line`, `stamp_strict_social_deterministic_fallback_family` | fallback-emission |
| `game/final_emission_validators.py` | final emission pipeline | `is_route_illegal_global_or_sanitizer_fallback_text`, `replacement_is_route_legal_social` | route-legality-validator |
| `game/final_emission_visibility_fallback.py` | final emission pipeline | `_npc_display_name_for_emission`, `log_final_emission_decision`, `log_final_emission_trace`, `minimal_social_emergency_fallback_line`, `select_strict_social_emergency_fallback_line` | fallback-emission |
| `game/gm.py` | production runtime | `apply_social_exchange_retry_fallback_gm`, `apply_strict_social_terminal_dialogue_fallback_if_needed`, `effective_strict_social_resolution_for_emission`, `is_route_illegal_global_or_sanitizer_fallback_text`, `is_scene_directed_watch_question`, `looks_like_npc_directed_question`, `minimal_social_emergency_fallback_line`, `repair_strict_social_terminal_dialogue_fallback_if_needed`, `strict_social_emission_will_apply`, `strict_social_terminal_dialogue_fallback_valid` | fallback-emission |
| `game/gm_retry.py` | production runtime | `_merge_open_social_recovery_emission_debug`, `build_open_social_solicitation_recovery` | strict-social-composition |
| `game/interaction_context.py` | narrative/social | `merged_player_prompt_for_gate`, `should_apply_strict_social_exchange_emission` | realization-projection |
| `game/interaction_continuity.py` | narrative/social | `minimal_social_emergency_fallback_line` | fallback-emission |
| `game/output_sanitizer.py` | production runtime | `effective_strict_social_resolution_for_emission`, `select_strict_social_emergency_fallback_line`, `social_fallback_line_for_sanitizer`, `strict_social_emission_will_apply` | fallback-emission |
| `game/response_policy_enforcement.py` | production runtime | `effective_strict_social_resolution_for_emission`, `minimal_social_emergency_fallback_line`, `strict_social_emission_will_apply` | fallback-emission |
| `game/speaker_contract_enforcement.py` | narrative/social | `_has_explicit_interruption_shape`, `_npc_display_name_for_emission`, `interruption_cue_present_in_text`, `strict_social_ownership_terminal_fallback` | fallback-emission |
| `game/upstream_response_repairs.py` | production runtime | `_npc_display_name_for_emission`, `minimal_social_emergency_fallback_line`, `strict_social_emission_will_apply` | fallback-emission |
| `tests/helpers/strict_social_harness.py` | speaker helpers | `effective_strict_social_resolution_for_emission` | strict-social-composition |
| `tests/test_anti_reset_emission_guard.py` | integration/regression | `social_exchange_emission (module)` | module-monkeypatch |
| `tests/test_broad_address_social_bid.py` | speaker/social | `_open_social_recovery_passes_anti_stall`, `build_open_social_solicitation_recovery`, `see (module)` | strict-social-composition |
| `tests/test_contextual_minimal_repair_regressions.py` | integration/regression | `is_route_illegal_global_or_sanitizer_fallback_text` | route-legality-validator |
| `tests/test_dialogue_interaction_establishment.py` | speaker/social | `player_line_triggers_strict_social_emission`, `reconcile_strict_social_resolution_speaker`, `resolve_strict_social_npc_target_id` | strict-social-composition |
| `tests/test_fallback_shipped_contract_propagation.py` | integration/regression | `strict_social_emission_will_apply` | gate-preflight-policy |
| `tests/test_final_emission_boundary_convergence.py` | final emission gate | `minimal_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` | fallback-emission |
| `tests/test_final_emission_gate_orchestration_order.py` | final emission gate | `effective_strict_social_resolution_for_emission` | strict-social-composition |
| `tests/test_final_emission_meta.py` | final emission gate | `project_strict_social_replace_realization_family`, `stamp_strict_social_deterministic_fallback_family`, `strict_social_deterministic_fallback_family_token` | realization-projection |
| `tests/test_final_emission_sealed_fallback.py` | final emission gate | `social_exchange_emission (module)` | module-monkeypatch |
| `tests/test_final_emission_visibility_fallback.py` | final emission gate | `social_exchange_emission (module)` | module-monkeypatch |
| `tests/test_gm_retry.py` | HTTP/pipeline integration | `apply_social_exchange_retry_fallback_gm`, `social_exchange_emission (module)` | strict-social-composition |
| `tests/test_narration_transcript_regressions.py` | replay | `_sse (module)`, `build_final_strict_social_response`, `social_exchange_emission (module)` | strict-social-composition |
| `tests/test_narrative_authority_rules.py` | integration/regression | `merged_player_prompt_for_gate` | gate-preflight-policy |
| `tests/test_output_sanitizer.py` | integration/regression | `social_exchange_emission_module (module)` | module-monkeypatch |
| `tests/test_ownership_registry.py` | ownership governance | `social_exchange_emission (module)`, `strict_social_emission_will_apply\n"` | ownership-governance |
| `tests/test_realization_provenance.py` | integration/regression | `build_final_strict_social_response` | strict-social-composition |
| `tests/test_social_answer_candidate.py` | speaker/social | `build_final_strict_social_response` | strict-social-composition |
| `tests/test_social_emission_quality.py` | speaker/social | `build_final_strict_social_response`, `select_best_grounded_social_answer_text`, `social_final_emission_malformed_player_echo` | route-legality-validator |
| `tests/test_social_exchange_emission.py` | speaker/social | `_apply_interruption_repeat_guard`, `_social_integrity_fallback_line_candidates`, `apply_strict_social_ownership_enforcement`, `apply_strict_social_sentence_ownership_filter`, `apply_strict_social_terminal_dialogue_fallback_if_needed`, `build_final_strict_social_response`, `coerce_resolution_for_strict_social_emission`, `deterministic_social_fallback_line`, `effective_strict_social_resolution_for_emission`, `hard_reject_social_exchange_text`, `is_route_illegal_global_or_sanitizer_fallback_text`, `lawful_strict_social_dialogue_emergency_fallback_line`, `minimal_social_emergency_fallback_line`, `normalize_social_exchange_candidate`, `reconcile_strict_social_resolution_speaker`, `should_apply_strict_social_exchange_emission`, `strict_social_emission_will_apply`, `strict_social_ownership_terminal_fallback`, `strict_social_terminal_dialogue_fallback_valid`, `synthetic_social_exchange_resolution_for_emission` | fallback-emission |
| `tests/test_social_fallback_leak_containment.py` | speaker/social | `apply_social_exchange_retry_fallback_gm` | strict-social-composition |
| `tests/test_social_interaction_authority.py` | speaker/social | `reconcile_strict_social_resolution_speaker` | strict-social-composition |
| `tests/test_social_speaker_grounding.py` | speaker/social | `apply_social_exchange_retry_fallback_gm`, `build_final_strict_social_response`, `reconcile_strict_social_resolution_speaker` | strict-social-composition |
| `tests/test_social_target_authority_regressions.py` | speaker/social | `build_final_strict_social_response`, `player_line_triggers_strict_social_emission` | strict-social-composition |
| `tests/test_strict_social_emergency_fallback_dialogue.py` | speaker/social | `apply_strict_social_terminal_dialogue_fallback_if_needed`, `lawful_strict_social_dialogue_emergency_fallback_line`, `repair_strict_social_terminal_dialogue_fallback_if_needed`, `strict_social_terminal_dialogue_fallback_valid` | fallback-emission |
