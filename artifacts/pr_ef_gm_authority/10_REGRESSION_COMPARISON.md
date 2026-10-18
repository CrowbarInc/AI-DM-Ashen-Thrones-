# 10 — Regression Comparison

Baseline: 256/286 passed, 30 failed. Final: 271/301 passed, 30 failed. Added PR-EF tests: 15. New failing IDs: 0; resolved inherited IDs: 0; inherited failing IDs: 30; changed normalized failure messages: 0.

Full individual results and preserved signatures: regression_comparison.json, baseline_junit.xml and final_junit.xml. Object addresses are normalized for message comparison; no failure is suppressed. The pre-existing failures concern social/final-emission/retry behavior and four exploration chat routes. They were not repaired to make the baseline green.

The exact comparison commands are in validation_commands.json. Same 16 PR-EC/ED suite files, plus the new PR-EF test file only in the final run. This is a representative regression family, not the complete repository test suite. Windows sandbox TestClient hangs in local socketpair setup; provider-disabled HTTP runs were performed outside the sandbox. Test model guards remain enabled. A first profiler temp-directory permission failure was resolved by putting TEMP/TMP under the workspace.

Inherited failing tests:

- `tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration`
- `tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages`
- `tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `tests.test_turn_pipeline_shared::test_chat_action_outcome_contract_survives_inside_active_social_scene`
- `tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange`
- `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]`
- `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]`
- `tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[Approaching the notice board, Galinor studies the posting about the missing patrol. Does it have any other details?-notice_board-Does it have any other details?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I check the notice. Is there more written below?-notice_board-Is there more written below?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I examine the broken lantern; does it show signs of tampering?-broken_lantern-does it show signs of tampering?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I study the strange brass device. Anything unusual?-brass_device-Anything unusual?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `tests.test_turn_pipeline_shared::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`
- `tests.test_turn_pipeline_shared::test_chat_repeated_social_questions_keep_npc_uncertainty_voice`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `tests.test_turn_pipeline_shared::test_pipeline_strict_social_ragged_stranger_fallback_repaired`
- `tests.test_turn_pipeline_shared::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical`
