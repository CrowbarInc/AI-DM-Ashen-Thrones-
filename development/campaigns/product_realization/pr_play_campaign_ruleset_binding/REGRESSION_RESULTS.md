# Regression results

Combined before: 455 passed / 17 failed; final: 455 passed / 17 failed. Focused before: 470 passed / 1 failed; final: 470 passed / 1 failed. Exact failure sets unchanged. Lifecycle before: 59 passed / 9 failed; after: 59 passed / 9 failed. New binding/architecture + existing boundary/policy/public-projection selection: 223 passed, zero failures. Final binding + save/load + persistence recheck after fail-closed loader refinement: 94 passed, zero failures.

No test assertion was weakened or removed. The combined/focused historical selections are distinct from the new contract selection. Full repository suite was not run or claimed clean. Additional lifecycle tests were compared with captured pre-edit module source in a fresh isolated process. Inherited identities are listed below and in machine-readable result files. No live provider calls/retries were introduced.

## Combined inherited failures

- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`

## Focused inherited failures

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

## Lifecycle inherited failures

- `tests.test_new_campaign_silent_reset_nc2::test_new_campaign_response_and_log_empty`
- `tests.test_new_campaign_silent_reset_nc2::test_explicit_start_campaign_chat_still_produces_opening_resolution`
- `tests.test_start_campaign_api::test_start_campaign_emits_opening_and_sets_started`
- `tests.test_start_campaign_api::test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text`
- `tests.test_start_campaign_api::test_start_campaign_promotes_valid_upstream_prepared_scene_opening`
- `tests.test_start_campaign_api::test_failed_start_campaign_does_not_mark_started`
- `tests.test_compat_import_governance::test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`
- `tests.test_compat_import_governance::test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities`
- `tests.test_compat_import_governance::test_bv14c_social_exchange_compat_fi_cap_locked`
