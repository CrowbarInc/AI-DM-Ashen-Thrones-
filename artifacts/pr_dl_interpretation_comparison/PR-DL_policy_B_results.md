# PR-DL Policy B Results

Provider requests charged to this policy: 10
Actual input tokens: 7610
Actual output tokens: 1439
Actual total tokens: 9049

Fully handled (16): S1, C1, compound, ambiguous, control_movement, control_combat, control_observation, control_authored_fact, control_followup, var_compound_control, var_ambiguous_subtle, var_pronoun_control, var_conseq_social, var_social_control, var_negated_control, var_hypothetical_control
Partially handled (1): var_unsupported_mechanic
Missed complications (5): declared_canon, mechanical_dump, var_compound_subtle, var_unsupported_mechanic, var_quote_control
Incorrect interpretations (4): declared_canon, mechanical_dump, var_compound_subtle, var_quote_control
Unnecessary escalations (2): var_social_control, var_hypothetical_control
Useful clarifications (2): ambiguous, var_ambiguous_subtle
Authority violations in consumed model output (2): declared_canon, mechanical_dump
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
| control_combat | PASS | FAIL | PASS | combat |
| control_observation | PASS | PASS | PASS | exploration |
| control_authored_fact | PASS | PASS | PASS | social |
| control_followup | PASS | PASS | PASS | social |
| var_compound_subtle | FAIL | PASS | FAIL | world_action |
| var_compound_control | PASS | PASS | PASS | social |
| var_ambiguous_subtle | FAIL | PASS | PASS | social |
| var_pronoun_control | PASS | PASS | PASS | social |
| var_conseq_social | FAIL | PASS | PASS | adjudication |
| var_social_control | PASS | PASS | PASS | adjudication |
| var_unsupported_mechanic | FAIL | PARTIAL | PARTIAL | world_action |
| var_quote_control | FAIL | PASS | FAIL | travel |
| var_negated_control | PASS | PASS | PASS | exploration |
| var_hypothetical_control | PASS | PASS | PASS | social |

Policy B consumes the stored interpretation only where the preserved PR-DK B trigger is true: an existing routing signal or an independent completeness check. Elsewhere it keeps the deterministic result.
