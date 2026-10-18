# PR-CW Regression Results

Final focused regression: 249 passed, no failures. The combined run has
303 passed / 27 failed. A projection-disabled comparison reproduces exactly the
same failure identities. Authored knowledge independently remains 14 passed / 2 failed;
in the combined ordering it is 13 passed / 3 failed. The additional order-sensitive
`test_retry_fallback_prefers_authored_topic_over_ignorance` failure also occurs with
projection disabled. Shared pipeline remains 41 passed / 24 failed, matching Phase 1.
No new reproducible projection regression observed.

- `tests.test_authored_knowledge_realization`: 13 passed / 3 failed
- `tests.test_bounded_improvisation_authority`: 5 passed / 0 failed
- `tests.test_final_emission_gate`: 1 passed / 0 failed
- `tests.test_pr_br_claim_control_regex_bound`: 1 passed / 0 failed
- `tests.test_pr_br_claim_control_slice1`: 6 passed / 0 failed
- `tests.test_pr_br_claim_control_slice2`: 10 passed / 0 failed
- `tests.test_pr_br_continuation18_immutable_boundary`: 21 passed / 0 failed
- `tests.test_pr_br_continuation19_hard_authority`: 11 passed / 0 failed
- `tests.test_pr_br_structured_realization_envelope`: 11 passed / 0 failed
- `tests.test_pr_bt_policy_instruction_deduplication`: 5 passed / 0 failed
- `tests.test_pr_bt_selective_epistemic_guidance`: 3 passed / 0 failed
- `tests.test_pr_bw_narration_only_envelope`: 5 passed / 0 failed
- `tests.test_pr_by_narration_only_retry_contract`: 22 passed / 0 failed
- `tests.test_pr_cc_social_reply_reconciliation`: 11 passed / 0 failed
- `tests.test_pr_ce_subjective_preference_classification`: 13 passed / 0 failed
- `tests.test_pr_ck_ordinary_resolver_selection`: 30 passed / 0 failed
- `tests.test_pr_cn_contextual_figure_integrity`: 13 passed / 0 failed
- `tests.test_pr_cp_authorized_finalization`: 9 passed / 0 failed
- `tests.test_pr_ct_safe_prompt_deduplication`: 3 passed / 0 failed
- `tests.test_pr_cw_social_context_projection`: 39 passed / 0 failed
- `tests.test_social_question_relevance_answer_selection`: 25 passed / 0 failed
- `tests.test_turn_packet_stage_diff_integration`: 5 passed / 0 failed
- `tests.test_turn_pipeline_shared`: 41 passed / 24 failed

Failure identities in the combined run (also present with projection disabled):

- `tests.test_authored_knowledge_realization::test_retry_fallback_prefers_authored_topic_over_ignorance`
- `tests.test_authored_knowledge_realization::test_http_notice_question_communicates_patrol_fact`
- `tests.test_authored_knowledge_realization::test_http_read_notice_board_speaks_written_clue`
- `tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]`
- `tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]`
- `tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only`
- `tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `tests.test_turn_pipeline_shared::test_chat_repeated_social_questions_keep_npc_uncertainty_voice`
- `tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[Approaching the notice board, Galinor studies the posting about the missing patrol. Does it have any other details?-notice_board-Does it have any other details?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I check the notice. Is there more written below?-notice_board-Is there more written below?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I examine the broken lantern; does it show signs of tampering?-broken_lantern-does it show signs of tampering?]`
- `tests.test_turn_pipeline_shared::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I study the strange brass device. Anything unusual?-brass_device-Anything unusual?]`
- `tests.test_turn_pipeline_shared::test_chat_action_outcome_contract_survives_inside_active_social_scene`
- `tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `tests.test_turn_pipeline_shared::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`
- `tests.test_turn_pipeline_shared::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical`
- `tests.test_turn_pipeline_shared::test_pipeline_strict_social_ragged_stranger_fallback_repaired`
