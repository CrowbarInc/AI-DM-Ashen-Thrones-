# 18 — Regression Comparison

```json
{
  "baseline_counts": {
    "passed": 692,
    "failed": 25
  },
  "final_counts": {
    "passed": 692,
    "failed": 25
  },
  "new_failures": [],
  "inherited_failures": [
    "tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent",
    "tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages",
    "tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution",
    "tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration",
    "tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape",
    "tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback",
    "tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback",
    "tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only",
    "tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first",
    "tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback",
    "tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback",
    "tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication",
    "tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange",
    "tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata",
    "tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane",
    "tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels",
    "tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit",
    "tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit",
    "tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract",
    "tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_strict_social_hidden_mutation_detected",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_wrong_speaker_fixture_has_attributable_trace",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_report_schema_and_gap_closure",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_writer_raw_checkpoint_present_on_strict_social_turn",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_generate_repo_artifacts"
  ],
  "fixed": []
}
```

Full identities and outcomes are in regression_comparison.json and both JUnit files. Two EF-R2 assertion updates implement intentional fixed-fallback sealing; no frozen input is edited. Baseline matches R4 692/25 after the replay-only environment flag was removed and a zero external-request budget was added. Historical Windows atomic replace PermissionError appeared once during an intermediate run; final result is reported without suppressing failures. No complete repository suite claim.
