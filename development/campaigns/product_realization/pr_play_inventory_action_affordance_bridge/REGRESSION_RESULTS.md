# Fresh current-source regression

Combined exact predecessor selection: 425 tests; 405 passed /20 failed /0 errors /0 skipped. New failure identities: ['tests.test_pr_play_79df3_classification::test_duplicate_refusal_does_not_publish', 'tests.test_pr_play_79df3_classification::test_save_reload_keeps_the_preceding_publication', 'tests.test_pr_play_79df3_classification::test_two_refusals_then_gameplay_advances']. Resolved predecessor identities: []. `regression_comparison.json` includes exact failure identities; commands, logs and JUnit XML are packaged. There is no production implementation before/after pair.

The new three identities concern duplicate refusal, two refusals then gameplay, and saved publication. The forced provider-disable flag prevents these tests' intended request-budget admission refusal path. A targeted fresh-process recheck unsets only that provider-disable condition, retains disabled expression/retries and startup preflight, and blocks external socket connections. 3/3 pass; external network attempts: 0. Windows event-loop loopback sockets remain allowed. The first too-strict socket guard blocked those local event-loop sockets; its failed intermediate records remain in environment_recheck.*. No test or production assertion was edited. The full 425-test selection was not rerun under the corrected environment, so no fresh 408/17 or zero-raw-new-failures claim is made.

Focused current selection: inventory reference binding, marking action, removal, observation: 65 tests, 65 passed /0 failed. Final execution partitions the same four modules into fresh processes to bound accumulating process-local storage audit hooks, as in the predecessor's focused verification. The completed focused_module_0 was reused; the other three modules ran concurrently with distinct basetemps as focused_verified_module_1 through 3. The interrupted partial single-process focused_current.log and briefly started sequential focused_module_1.log are retained as intermediate records. authoritative_labels in focused_current_result.json, module commands/XML and aggregate XML identify the complete final run. This is a smaller fresh selection than the predecessor's 611 focused preservation cases. The latter total was independently verified from historical module XML, not rerun in full. No test was deleted, skipped or weakened.

Current combined failures:
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
- `tests.test_pr_play_79df3_classification::test_duplicate_refusal_does_not_publish`
- `tests.test_pr_play_79df3_classification::test_two_refusals_then_gameplay_advances`
- `tests.test_pr_play_79df3_classification::test_save_reload_keeps_the_preceding_publication`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
