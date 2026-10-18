# PR-DM Fallback Contract

The deterministic interpretation and the stored model proposal are both retained as records. Consumption is not execution. `known_execution_support` is false for every row.

Rules applied:

- An invalid or authority-rejected model payload is not consumed.
- A PASS deterministic reading is preserved when the model payload is not consumed.
- A FAIL deterministic reading is not executed because the model payload was rejected. The result is unsupported, clarification, or safe abstention.
- A schema-valid and authority-valid payload may be retained as an interpretation. That retention does not authorize a resolver, a roll, or a state write.

| Scenario | Routed | Disposition | If the stored output were offered | Usefulness | Execution |
| --- | --- | --- | --- | --- | --- |
| S1 | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| C1 | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| compound | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| ambiguous | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| declared_canon | True | unsupported | unsupported | unsupported_action | not_executed |
| mechanical_dump | True | unsupported | unsupported | unsupported_action | not_executed |
| control_movement | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| control_combat | False | deterministic_unrouted | preserve_deterministic | deterministic_interpretation | not_executed |
| control_observation | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| control_authored_fact | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| control_followup | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| var_compound_subtle | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| var_compound_control | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| var_ambiguous_subtle | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| var_pronoun_control | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| var_conseq_social | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| var_social_control | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| var_unsupported_mechanic | True | unsupported | unsupported | unsupported_action | not_executed |
| var_quote_control | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |
| var_negated_control | False | deterministic_unrouted | consume_interpretation | deterministic_interpretation | not_executed |
| var_hypothetical_control | True | consume_interpretation | consume_interpretation | successful_interpretation | not_executed |

Preserving `control_combat` is the counterfactual that universal routing failed. The invented weapon id is discarded. The deterministic attack interpretation remains the selected interpretation, and it is still not executed by this experiment.

Rejecting `declared_canon` does not fall through into a world-action execution. The deterministic reading is FAIL, so the disposition is unsupported.
