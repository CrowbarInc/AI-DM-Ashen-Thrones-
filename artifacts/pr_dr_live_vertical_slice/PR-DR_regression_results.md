# PR-DR Regression Results

No suite was repaired. These commands set ASHEN_DISABLE_LIVE_INTERPRETATION=1.
Turn-pipeline failures that appear in the PR-DQ regression file are inherited.

| Suite | Timeout | Timed out | Return code | Summary |
| --- | --- | --- | --- | --- |
| PR-DR | 180s | False | 0 | 12 passed |
| PR-DQ | 180s | False | 0 | 23 passed |
| PR-DO | 120s | False | 0 | 12 passed |
| PR-DP | 180s | False | 0 | 11 passed |
| Authority | 180s | False | 0 | 9 passed |
| Conversation | 180s | False | 0 | 34 passed |
| Turn pipeline | 300s | False | 1 | 41 passed, 24 failed |

## Inherited turn-pipeline failures

Inherited and still failing: 24
New failures: 0
Recorded in PR-DQ but not in this run: 0

## Suite output

### PR-DR

Command: `python -m pytest tests/test_pr_dr_live_vertical_slice.py -q --tb=line`
Timeout: 180s. Timed out: False. Return code: 0.

```
............                                                             [100%]
```

### PR-DQ

Command: `python -m pytest tests/test_pr_dq_ic_ooc_messages.py tests/test_pr_dq_vertical_slice.py -q --tb=line`
Timeout: 180s. Timed out: False. Return code: 0.

```
.......................                                                  [100%]
```

### PR-DO

Command: `python -m pytest tests/test_pr_do_authority_separation.py -q --tb=line`
Timeout: 120s. Timed out: False. Return code: 0.

```
............                                                             [100%]
```

### PR-DP

Command: `python -m pytest tests/test_pr_dp_contract_qualification.py -q --tb=line`
Timeout: 180s. Timed out: False. Return code: 0.

```
...........                                                              [100%]
```

### Authority

Command: `python -m pytest tests/test_pr_cx_authority_assurance.py -q --tb=line`
Timeout: 180s. Timed out: False. Return code: 0.

```
.........                                                                [100%]
```

### Conversation

Command: `python -m pytest tests/test_conversational_memory_window.py -q --tb=line`
Timeout: 180s. Timed out: False. Return code: 0.

```
..................................                                       [100%]
```

### Turn pipeline

Command: `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line`
Timeout: 300s. Timed out: False. Return code: 1.

```
o\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\tests\test_turn_pipeline_shared.py:2075: AssertionError: assert 'tavern runner' in 'no one here can answer that from what is settled here.'
E   AssertionError: assert None
     +  where None = <built-in method get of dict object at 0x000001C94A3C4D40>('speaker_contract_enforcement_reason')
     +    where <built-in method get of dict object at 0x000001C94A3C4D40> = {}.get
---------------------------- Captured stdout call -----------------------------
[PROMPT] fresh campaign prompt constructed
C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\tests\test_turn_pipeline_shared.py:2103: AssertionError: assert None
=========================== short test summary info ===========================
FAILED tests/test_turn_pipeline_shared.py::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape
FAILED tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[scene_hold_filler]
FAILED tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]
FAILED tests/test_turn_pipeline_shared.py::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback
FAILED tests/test_turn_pipeline_shared.py::test_chat_known_follow_up_bypasses_uncertainty_fallback
FAILED tests/test_turn_pipeline_shared.py::test_chat_targeted_retry_unresolved_question_only
FAILED tests/test_turn_pipeline_shared.py::test_chat_targeted_retry_prefers_highest_priority_failure_first
FAILED tests/test_turn_pipeline_shared.py::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback
FAILED tests/test_turn_pipeline_shared.py::test_chat_repeated_social_questions_keep_npc_uncertainty_voice
FAILED tests/test_turn_pipeline_shared.py::test_chat_social_pressure_line_prefers_dialogue_over_adjudication
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_turn_preserves_embedded_adjudication_metadata
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[Approaching the notice board, Galinor studies the posting about the missing patrol. Does it have any other details?-notice_board-Does it have any other details?]
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I check the notice. Is there more written below?-notice_board-Is there more written below?]
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I examine the broken lantern; does it show signs of tampering?-broken_lantern-does it show signs of tampering?]
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome[I study the strange brass device. Anything unusual?-brass_device-Anything unusual?]
FAILED tests/test_turn_pipeline_shared.py::test_chat_action_outcome_contract_survives_inside_active_social_scene
FAILED tests/test_turn_pipeline_shared.py::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane
FAILED tests/test_turn_pipeline_shared.py::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels
FAILED tests/test_turn_pipeline_shared.py::test_chat_social_exchange_invalid_blob_is_repaired_before_emit
FAILED tests/test_turn_pipeline_shared.py::test_chat_social_exchange_blocks_advisory_prose_before_emit
FAILED tests/test_turn_pipeline_shared.py::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract
FAILED tests/test_turn_pipeline_shared.py::test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair
FAILED tests/test_turn_pipeline_shared.py::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical
FAILED tests/test_turn_pipeline_shared.py::test_pipeline_strict_social_ragged_stranger_fallback_repaired
```
