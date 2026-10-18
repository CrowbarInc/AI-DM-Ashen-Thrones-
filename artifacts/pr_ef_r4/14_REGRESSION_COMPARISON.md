# 14 — Regression Comparison

## Baseline

Historical PR-EF-R2, not re-run on this tree before the edit: **321 passed / 20 failed**. PR-EF-R3 confirmed the source hashes and did not re-execute the family.

## Post-implementation

Family command: the eighteen R2 files, plus `tests/test_pr_ef_r2_social_authority.py` and `tests/test_pr_ef_r4_authorization.py`.

**349 passed / 20 failed.** Junit: `artifacts/pr_ef_r4/regression_junit.xml`.

The R4 module contributed 28 passes and 0 failures. The pass count is higher than 321 because this run includes those added tests. It is not evidence that historical failures were fixed.

## Failure identities

The 20 failures are exactly the PR-EF-R2 set. No new identity. No historical identity cleared.

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
- `test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`
- `test_chat_quarterstaff_attack_mechanical_resolution_absent`
- `test_chat_observe_area_resolution_kwarg_to_build_messages`
- `test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution`
- `test_chat_exploration_parsed_routes_through_exploration`

## Signatures

Message-level drift against the R2 junit was not recomputed. These identities were already failing before this cycle. During implementation, several other tests failed and were restored before this measurement: location follow-up “Where can I find them?”, dialogue-then-docks movement, GM clarification with public evidence, mixed GM observation plus NPC question, compound correction of a pending inspect-then-move, and the captured “ask Mara” / “turn to Mara” authority cases. Those are not in the final 20.

## Not cleaned up

The cycle did not try to turn the inherited twenty green. Social repair, exploration routing, and retry-fallback expectations in that list stay as they were.
