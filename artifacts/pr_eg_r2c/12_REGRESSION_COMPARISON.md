# 12 — Regression Comparison

Baseline: 393 passing / 19 failing across the 22 historical family files. Final: 421 passing / 20 failing across that family plus 29 new tests. Existing-family post result is 393 passing / the same 19 failing. No baseline passing identity is lost after the documented single rename. No historical failing identity is resolved.

New failure: tests.test_pr_eg_r2c_speech_adoption::test_frozen_holdout[H6]. It is a new frozen relevance qualification case. Six existing assertions were intentionally updated to reflect host selection; the initial unmodified run (385 pass / 27 fail) is preserved. Two of its failures exposed an actual authority-conflict bug and were fixed before the final run. Three later scope errors from non-social history enforcement were removed; their evidence is retained. No new critical regression in the existing family remains unexplained.

Inherited failing identities:

- `tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages`
- `tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration`
- `tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange`
- `tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`

Exact machine comparison: regression_comparison.json. Entire repository suite was not run; the required relevant historical family and all added tests were run. No unrelated inherited repair was attempted.
