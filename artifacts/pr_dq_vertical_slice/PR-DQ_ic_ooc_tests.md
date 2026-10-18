# PR-DQ IC/OOC Tests

Deterministic fixtures. No live provider calls.

## Message cases

| # | Case | Test |
| --- | --- | --- |
| 1 | Explicit IC override | test_explicit_ic_override |
| 2 | Explicit OOC override | test_explicit_ooc_override_blocks_an_action_sentence |
| 3 | AUTO mode | test_auto_mode_classifies_prefixes_and_defers_unmarked_text |
| 4 | OOC: prefix | test_ooc_prefix |
| 5 | IC: prefix | test_ic_prefix |
| 6 | Ordinary IC action | test_ordinary_ic_action_routes_to_the_gameplay_adapter |
| 7 | Ordinary IC dialogue | test_ordinary_ic_dialogue |
| 8 | OOC rules question | test_ooc_rules_question_does_not_execute |
| 9 | OOC correction | test_ooc_correction_of_a_committed_action_requires_adjudication |
| 10 | Ambiguous statement | test_ambiguous_statement_stays_unresolved |
| 11 | Unsupported IC mechanic | test_unsupported_ic_mechanic_stays_in_character |
| 12 | Mixed IC/OOC message | test_mixed_message_is_deferred |
| 13 | Reclassification before execution | test_reclassification_before_execution_reroutes |
| 14 | Reclassification after execution | test_reclassification_after_execution_does_not_rewrite_state |
| 15 | OOC message cannot advance time | test_ooc_message_cannot_advance_time |
| 16 | OOC message cannot invoke a gameplay resolver | test_ooc_message_cannot_invoke_a_gameplay_resolver |
| 17 | OOC message cannot mutate state | test_ooc_message_cannot_mutate_state |
| 18 | Unified history preserves message order | test_unified_history_preserves_message_order |
| 19 | Explicit override takes precedence | test_explicit_override_takes_precedence_over_automatic_classification |
| 20 | Rejected or deferred messages do not change state | test_rejected_or_deferred_messages_do_not_change_state |

## Vertical slice

| Test | What it locks |
| --- | --- |
| test_four_turn_sequence_keeps_the_ooc_interruption_in_one_history | Lantern, OOC interruption, Mara, gate, notice board. |
| test_slice_report_matches_the_played_sequence | History order, clock, scene, and resolver list. |
| test_notice_board_is_blocked_while_the_courtyard_is_active | Turn 4 does not resolve from the courtyard. |

## Regression

Full suite output is in `PR-DQ_regression_results.md`.

No suite was repaired. These commands do not request live provider calls.
Turn-pipeline failures that appear in the PR-DP regression file are inherited.

| Suite | Timeout | Timed out | Return code | Summary |
| --- | --- | --- | --- | --- |
| PR-DQ | 180s | False | 0 | 23 passed |
| PR-DO | 120s | False | 0 | 12 passed |
| Authority | 180s | False | 0 | 9 passed |
| Conversation | 180s | False | 0 | 34 passed |
| Turn pipeline | 300s | False | 1 | 41 passed, 24 failed |

## Inherited turn-pipeline failures

Inherited and still failing: 24
New failures: 0
Recorded in PR-DP but not in this run: 0
