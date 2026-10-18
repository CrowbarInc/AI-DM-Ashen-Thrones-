# 15 — Regression Comparison

## Baseline, before production edits

369 tests. 349 passed. 20 failed. `artifacts/pr_eg/baseline_junit.xml`.

Failed identities:

- `test_turn_pipeline_shared.py::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `test_turn_pipeline_shared.py::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `test_turn_pipeline_shared.py::test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `test_turn_pipeline_shared.py::test_chat_targeted_retry_unresolved_question_only`
- `test_turn_pipeline_shared.py::test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `test_turn_pipeline_shared.py::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `test_turn_pipeline_shared.py::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `test_turn_pipeline_shared.py::test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `test_turn_pipeline_shared.py::test_chat_active_target_direct_command_routes_to_social_exchange`
- `test_turn_pipeline_shared.py::test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `test_turn_pipeline_shared.py::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `test_turn_pipeline_shared.py::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `test_turn_pipeline_shared.py::test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `test_turn_pipeline_shared.py::test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `test_turn_pipeline_shared.py::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `test_turn_pipeline_shared.py::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`
- `test_exploration_resolution.py::test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `test_exploration_resolution.py::test_chat_observe_area_resolution_kwarg_to_build_messages`
- `test_exploration_resolution.py::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `test_exploration_resolution.py::test_chat_exploration_parsed_routes_through_exploration`

These are the PR-EF-R4 historical twenty. They were not cleaned up.

## Final

369 tests. 350 passed. 19 failed. `artifacts/pr_eg/regression_junit.xml`. Same command, including `tests/test_pr_ef_r4_authorization.py`.

## Resolved

- `test_turn_pipeline_shared.py::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`

The clean-refusal path now ends on the in-character line instead of failing that assertion. This was not a targeted cleanup of the historical set.

## New failures

None. An intermediate tree had extra failures (generic invalid line on a captured social holdout, skipped narration on speaker repair, a Windows rename error on one movement test). Those are not in the final junit. The movement error was a file-lock `PermissionError` on `session.json` and did not recur.

## Other suites

`tests/test_pr_eg_dialogue_quality.py` and `tests/test_pr_dc_subjective_followups.py`: 73 passed.

Earlier in the cycle, `tests/test_question_dimension_answer_sufficiency.py` and `tests/test_pr_ed_provider_efficiency.py` were in a 112-passed run with the dialogue file. They were not re-run as a separate process after quote recovery. The provider-efficiency file is inside the final family and did not appear as a new failure.
