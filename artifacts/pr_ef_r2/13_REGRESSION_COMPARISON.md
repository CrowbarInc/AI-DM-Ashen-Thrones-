# 13 — Regression Comparison

Baseline: 293 pass / 26 fail. Final: 321 pass / 20 fail. Added tests: 22. Resolved: 6. New failing IDs: 0. Changed inherited signatures: 3. Exact command JSON, XML and output files preserved, with full identity/signature comparison in regression_comparison.json. This is the established comparison family, not the entire repository suite. An unchanged intermediate run (final4) hit WinError 5 during atomic session-file replacement; the isolated persistence test passed, and final5 repeated the complete suite with that identity passing. Both runs are retained.

Resolved identities:
- tests.test_pr_du_player_pipeline::test_pr_du_four_action_sequence_and_ooc_through_production_chat
- tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]
- tests.test_turn_pipeline_shared::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]
- tests.test_turn_pipeline_shared::test_chat_repeated_social_questions_keep_npc_uncertainty_voice
- tests.test_turn_pipeline_shared::test_pipeline_strict_social_ragged_stranger_fallback_repaired
- tests.test_turn_pipeline_shared::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical

New failing identities:
- None.

Remaining inherited identities:
- tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration
- tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution
- tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages
- tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent
- tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange
- tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape
- tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels
- tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback
- tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane
- tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata
- tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract
- tests.test_turn_pipeline_shared::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair
- tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit
- tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit
- tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication
- tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first
- tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only
- tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback
- tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback
- tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback

Changed signatures (before → after):
{
  "tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract": {
    "before": "AssertionError: assert 'Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd.' != 'Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd.'",
    "after": "assert 'Tavern Runner says, \"I cannot answer that from what is settled here.\"' != 'Tavern Runner says, \"I cannot answer that from what is settled here.\"'"
  },
  "tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback": {
    "before": "assert 1 == 2\n +  where 1 = len([[{'role': 'system', 'content': 'You are the game master for a solo Pathfinder 1e inspired browser campaign.\\n\\nRule P...itative_social_target_requires_dialogue\", \"dialogue_turn_contains_question_expectation\", \"social_question_guard\"]}}'}]])",
    "after": "AssertionError"
  },
  "tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit": {
    "before": "AssertionError: unresolved stock: unexpected player-facing phrase 'from here, no certain answer presents itself'",
    "after": "AssertionError"
  }
}
