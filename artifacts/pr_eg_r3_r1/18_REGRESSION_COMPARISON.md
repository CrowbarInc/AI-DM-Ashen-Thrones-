# 18 — Regression Comparison

Predecessor file: `artifacts/pr_eg_r3/final_relevant_junit.xml`. Counts: {'failed': 25, 'passed': 605} of 630.

Before the degree-word and "another way" repair: {'failed': 25, 'passed': 691}.

First post-repair run: {'failed': 27, 'passed': 690}. Two tests failed with `PermissionError` while replacing `session.json` on Windows. Both passed when rerun alone. They are listed in `environmental_file_locks` and are not product failures.

Confirming run: `final_relevant_junit_confirm.xml`. Counts: {'failed': 25, 'passed': 692} of 717.

New failures against the PR-EG-R3 identities: none.

Resolved failures: none.

Inherited failing identities (25):

- `tests.test_by3_strict_social_semantic_mutation::test_by3_generate_repo_artifacts`
- `tests.test_by3_strict_social_semantic_mutation::test_by3_report_schema_and_gap_closure`
- `tests.test_by3_strict_social_semantic_mutation::test_by3_strict_social_hidden_mutation_detected`
- `tests.test_by3_strict_social_semantic_mutation::test_by3_writer_raw_checkpoint_present_on_strict_social_turn`
- `tests.test_by3_strict_social_semantic_mutation::test_by3_wrong_speaker_fixture_has_attributable_trace`
- `tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration`
- `tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages`
- `tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance`
- `tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange`
- `tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`

The confirming pass count is higher because this suite adds the R3-R1 tests and the R2C-R2 reference-eligibility file to the PR-EG-R3 selection. No inherited failure changed state. The full repository suite was not run.
