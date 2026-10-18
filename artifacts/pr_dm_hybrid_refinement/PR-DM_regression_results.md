# PR-DM Regression Results

Command: `python -m pytest tests/test_pr_dm_hybrid_refinement.py -q --tb=line`
Timeout: 120 seconds. Timed out: False. Return code: 0. Progress marks: 9 passed, 0 failed, 0 skipped, 9 collected.

Command: `python -m pytest tests/test_pr_dl_interpretation_comparison.py tests/test_pr_dk_escalation_routing.py tests/test_pr_dj_selective_interpretation.py tests/test_pr_dg_architecture_preflight.py tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py tests/test_pr_cx_authority_assurance.py -q --tb=line`
Timeout: 180 seconds. Timed out: False. Return code: 0. Progress marks: 47 passed, 0 failed, 0 skipped, 47 collected.

Command: `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line`
Timeout: 240 seconds. Timed out: False. Return code: 1. Progress marks: 41 passed, 24 failed, 0 skipped, 65 collected.

Failed tests:

- tests/test_turn_pipeline_shared.py::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape
- tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]
- tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]
- tests/test_turn_pipeline_shared.py::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback
- tests/test_turn_pipeline_shared.py::test_chat_known_follow_up_bypasses_uncertainty_fallback
- tests/test_turn_pipeline_shared.py::test_chat_targeted_retry_unresolved_question_only
- tests/test_turn_pipeline_shared.py::test_chat_targeted_retry_prefers_highest_priority_failure_first
- tests/test_turn_pipeline_shared.py::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback
- tests/test_turn_pipeline_shared.py::test_chat_repeated_social_questions_keep_npc_uncertainty_voice
- tests/test_turn_pipeline_shared.py::test_chat_social_pressure_line_prefers_dialogue_over_adjudication
- tests/test_turn_pipeline_shared.py::test_chat_mixed_turn_preserves_embedded_adjudication_metadata
- tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[Approaching the notice board, Galinor studies the posting about the missing patrol. Does it have any other details?-notice_board-Does it have any other details?]
- tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I check the notice. Is there more written below?-notice_board-Is there more written below?]
- tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I examine the broken lantern; does it show signs of tampering?-broken_lantern-does it show signs of tampering?]
- tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I study the strange brass device. Anything unusual?-brass_device-Anything unusual?]
- tests/test_turn_pipeline_shared.py::test_chat_action_outcome_contract_survives_inside_active_social_scene
- tests/test_turn_pipeline_shared.py::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane
- tests/test_turn_pipeline_shared.py::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels
- tests/test_turn_pipeline_shared.py::test_chat_social_exchange_invalid_blob_is_repaired_before_emit
- tests/test_turn_pipeline_shared.py::test_chat_social_exchange_blocks_advisory_prose_before_emit
- tests/test_turn_pipeline_shared.py::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract
- tests/test_turn_pipeline_shared.py::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair
- tests/test_turn_pipeline_shared.py::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical
- tests/test_turn_pipeline_shared.py::test_pipeline_strict_social_ragged_stranger_fallback_repaired

The shared turn-pipeline progress line matches the PR-DL run: 41 passed and 24 failed out of 65. Those failures are inherited. PR-DM did not change production gameplay modules and did not repair them.
The focused PR-DM suite is the new surface. A failure there would be a new failure.
