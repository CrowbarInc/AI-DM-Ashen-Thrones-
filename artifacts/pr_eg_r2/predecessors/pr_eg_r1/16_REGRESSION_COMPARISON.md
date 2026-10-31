# 16 — Regression Comparison

## Pre-change

Family without `tests/test_pr_eg_r1_continuity.py`: **371 passed, 19 failed**.

Junit: `artifacts/pr_eg_r1/baseline_junit.xml`.

## Post-change

Same family plus the continuity tests: **393 passed, 19 failed**.

Junit: `artifacts/pr_eg_r1/regression_junit.xml`.

The 22 new passes are the 20 frozen holdouts, personal-ignorance recovery, and the zero-call north-road quote.

## Resolved

No inherited failing test was the target of this cycle. None of the 19 flipped to passing.

## New failures

None. An intermediate run briefly failed `test_production_ten_turn_sequence`, two semantic-ownership cases, and one snapshot test. Those were caused by capturing every question as an NPC ask, including "Could you interpret the situation for me?" and "Which road do you mean?". The final code leaves those on their previous paths. They pass.

## Unchanged failing identities

- `test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `test_chat_targeted_retry_unresolved_question_only`
- `test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback`
- `test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `test_chat_active_target_direct_command_routes_to_social_exchange`
- `test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `test_chat_observe_area_resolution_kwarg_to_build_messages`
- `test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `test_chat_exploration_parsed_routes_through_exploration`

These remain the inherited dialogue-contract and exploration-routing failures. This cycle did not expand into that cleanup.
