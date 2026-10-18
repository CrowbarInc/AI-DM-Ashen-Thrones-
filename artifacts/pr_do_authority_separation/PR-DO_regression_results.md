# PR-DO Regression Results

No suite timed out. Production saves were not modified. Live provider calls: 0.

| Suite | Command | Timeout | Timed out | Return code | Passed | Failed |
| --- | --- | --- | --- | --- | --- | --- |
| PR-DO | `python -m pytest tests/test_pr_do_authority_separation.py -q --tb=line` | 120s | false | 0 | 12 | 0 |
| PR-DN | `python -m pytest tests/test_pr_dn_interpretation_robustness.py -q --tb=line` | 120s | false | 0 | 3 | 0 |
| PR-DM | `python -m pytest tests/test_pr_dm_hybrid_refinement.py -q --tb=line` | 180s | false | 0 | 9 | 0 |
| PR-DL | `python -m pytest tests/test_pr_dl_interpretation_comparison.py -q --tb=line` | 180s | false | 0 | 8 | 0 |
| PR-DK | `python -m pytest tests/test_pr_dk_escalation_routing.py -q --tb=line` | 180s | false | 0 | 2 | 0 |
| PR-DJ | `python -m pytest tests/test_pr_dj_selective_interpretation.py -q --tb=line` | 180s | false | 0 | 9 | 0 |
| Authority | `python -m pytest tests/test_pr_cx_authority_assurance.py -q --tb=line` | 180s | false | 0 | 9 | 0 |
| Turn pipeline | `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line` | 300s | false | 1 | 41 | 24 |

New PR-DO failures: 0.

Inherited turn-pipeline failures: 24. These are the same 24 failures recorded in the PR-DN review. They were not repaired.

- `test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- `test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]`
- `test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]`
- `test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `test_chat_known_follow_up_bypasses_uncertainty_fallback`
- `test_chat_targeted_retry_unresolved_question_only`
- `test_chat_targeted_retry_prefers_highest_priority_failure_first`
- `test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback`
- `test_chat_repeated_social_questions_keep_npc_uncertainty_voice`
- `test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- `test_chat_mixed_turn_preserves_embedded_adjudication_metadata`
- `test_chat_mixed_scene_object_investigation_question_recovers_action_outcome` (4 parameter rows)
- `test_chat_action_outcome_contract_survives_inside_active_social_scene`
- `test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- `test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`
- `test_chat_social_exchange_invalid_blob_is_repaired_before_emit`
- `test_chat_social_exchange_blocks_advisory_prose_before_emit`
- `test_chat_repeated_interruption_progresses_without_losing_dialogue_contract`
- `test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair`
- `test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical`
- `test_pipeline_strict_social_ragged_stranger_fallback_repaired`

Raw output: `regression_stdout.txt`.
