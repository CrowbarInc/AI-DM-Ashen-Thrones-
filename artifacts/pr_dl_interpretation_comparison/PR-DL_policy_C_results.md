# PR-DL Policy C Results

Provider requests charged to this policy: 21
Actual input tokens: 15943
Actual output tokens: 2811
Actual total tokens: 18754

Fully handled (17): S1, C1, compound, ambiguous, control_movement, control_observation, control_authored_fact, control_followup, var_compound_subtle, var_compound_control, var_ambiguous_subtle, var_pronoun_control, var_conseq_social, var_social_control, var_quote_control, var_negated_control, var_hypothetical_control
Partially handled (1): var_unsupported_mechanic
Missed complications (3): declared_canon, mechanical_dump, var_unsupported_mechanic
Incorrect interpretations (3): declared_canon, mechanical_dump, control_combat
Unnecessary escalations (11): S1, control_movement, control_combat, control_observation, control_authored_fact, control_followup, var_compound_control, var_pronoun_control, var_social_control, var_negated_control, var_hypothetical_control
Useful clarifications (2): ambiguous, var_ambiguous_subtle
Authority violations in consumed model output (3): declared_canon, mechanical_dump, control_combat
Unsupported asserted outcomes (2): declared_canon, mechanical_dump

| Scenario | Deterministic | Live | Policy result | Resolver |
| --- | --- | --- | --- | --- |
| S1 | PASS | PASS | PASS | social |
| C1 | FAIL | PASS | PASS | social |
| compound | FAIL | PASS | PASS | travel |
| ambiguous | FAIL | PASS | PASS | social |
| declared_canon | FAIL | FAIL | FAIL | world_action |
| mechanical_dump | FAIL | FAIL | FAIL | social |
| control_movement | PASS | PASS | PASS | travel |
| control_combat | PASS | FAIL | FAIL | combat |
| control_observation | PASS | PASS | PASS | exploration |
| control_authored_fact | PASS | PASS | PASS | social |
| control_followup | PASS | PASS | PASS | social |
| var_compound_subtle | FAIL | PASS | PASS | world_action |
| var_compound_control | PASS | PASS | PASS | social |
| var_ambiguous_subtle | FAIL | PASS | PASS | social |
| var_pronoun_control | PASS | PASS | PASS | social |
| var_conseq_social | FAIL | PASS | PASS | adjudication |
| var_social_control | PASS | PASS | PASS | adjudication |
| var_unsupported_mechanic | FAIL | PARTIAL | PARTIAL | world_action |
| var_quote_control | FAIL | PASS | PASS | travel |
| var_negated_control | PASS | PASS | PASS | exploration |
| var_hypothetical_control | PASS | PASS | PASS | social |

Policy C consumes the stored interpretation on every scenario. A rejected adapter result is an unusable interpretation for that turn.
