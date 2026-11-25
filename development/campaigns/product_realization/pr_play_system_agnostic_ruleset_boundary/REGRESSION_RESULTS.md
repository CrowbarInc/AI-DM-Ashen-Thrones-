# Regression results

Combined selection: **455 passed / 17 failed** before and **455 passed / 17 failed** after, 472 tests both times. New failure identities: none. Missing identities: none. Provider records: 0. External network attempts: 0.

Focused selection: **470 passed / 1 failed** before and **470 passed / 1 failed** after, 471 tests both times. The only failure, before and after, is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. New identities: none. Provider records: 0.

New contract tests, reported separately: **54 passed / 0 failed**. Existing equipment-policy tests, reported separately: **56 passed / 0 failed**. Provider records: 0.

No assertion was weakened or deleted. No frozen gameplay fixture or historical evaluation record was edited.

Commands are `artifacts/pr_play_system_agnostic_ruleset_boundary/verify_gate.py` with phases `combined_before`, `combined_after`, `focused_before`, `focused_after`, `contract`, and `policy`. Each phase writes `_command.json`, `_result.json`, and JUnit XML beside that script. Storage was isolated under `development/tmp/system_agnostic_ruleset_boundary`. Live interpretation, expression generation, provider retries, and upstream preflight were disabled. `ASHEN_DISABLE_PROVIDER_CALLS` was unset for these pytest phases. External sockets were blocked by an audit hook.

Exact combined failures, before and after:

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

Elapsed times are in the result JSON files. The two before phases ran concurrently and are slower than the separate after phases. Do not treat those elapsed times as a performance claim.
