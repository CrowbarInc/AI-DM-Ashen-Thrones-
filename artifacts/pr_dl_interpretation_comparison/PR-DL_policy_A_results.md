# PR-DL Policy A Results

Provider requests charged to this policy: 0
Actual input tokens: 0
Actual output tokens: 0
Actual total tokens: 0

Fully handled (11): S1, control_movement, control_combat, control_observation, control_authored_fact, control_followup, var_compound_control, var_pronoun_control, var_social_control, var_negated_control, var_hypothetical_control
Partially handled (0): none
Missed complications (10): C1, compound, ambiguous, declared_canon, mechanical_dump, var_compound_subtle, var_ambiguous_subtle, var_conseq_social, var_unsupported_mechanic, var_quote_control
Incorrect interpretations (10): C1, compound, ambiguous, declared_canon, mechanical_dump, var_compound_subtle, var_ambiguous_subtle, var_conseq_social, var_unsupported_mechanic, var_quote_control
Unnecessary escalations (0): none
Useful clarifications (0): none
Authority violations in consumed model output (0): none
Unsupported asserted outcomes (0): none

| Scenario | Deterministic | Live | Policy result | Resolver |
| --- | --- | --- | --- | --- |
| S1 | PASS | PASS | PASS | social |
| C1 | FAIL | PASS | FAIL | social |
| compound | FAIL | PASS | FAIL | travel |
| ambiguous | FAIL | PASS | FAIL | social |
| declared_canon | FAIL | FAIL | FAIL | world_action |
| mechanical_dump | FAIL | FAIL | FAIL | social |
| control_movement | PASS | PASS | PASS | travel |
| control_combat | PASS | FAIL | PASS | combat |
| control_observation | PASS | PASS | PASS | exploration |
| control_authored_fact | PASS | PASS | PASS | social |
| control_followup | PASS | PASS | PASS | social |
| var_compound_subtle | FAIL | PASS | FAIL | world_action |
| var_compound_control | PASS | PASS | PASS | social |
| var_ambiguous_subtle | FAIL | PASS | FAIL | social |
| var_pronoun_control | PASS | PASS | PASS | social |
| var_conseq_social | FAIL | PASS | FAIL | adjudication |
| var_social_control | PASS | PASS | PASS | adjudication |
| var_unsupported_mechanic | FAIL | PARTIAL | FAIL | world_action |
| var_quote_control | FAIL | PASS | FAIL | travel |
| var_negated_control | PASS | PASS | PASS | exploration |
| var_hypothetical_control | PASS | PASS | PASS | social |

Policy A uses the deterministic contract only. Interpretation usage is zero. A correct deterministic result stays in place even when the stored model output is wrong.
