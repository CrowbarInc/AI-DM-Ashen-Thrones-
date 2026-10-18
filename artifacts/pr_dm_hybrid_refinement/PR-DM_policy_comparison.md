# PR-DM Policy Comparison

The same stored output is used for every policy. A, B, and C are the original PR-DL policies. D is the refined selective policy. Gameplay labels for A, B, and C were recomputed from the stored scores and matched the published lists.

| Policy | Fully handled | Partially handled | Requests | What the count means |
| --- | ---: | ---: | ---: | --- |
| A deterministic | 11 | 0 | 0 | Deterministic interpretation only |
| B original selective | 16 | 1 | 10 | Stored calls the original router would make |
| C universal | 17 | 1 | 21 | Every stored call consumed when the adapter accepts it |
| D refined selective | 18 | 0 | 12 | Original selective calls plus the new completeness hits, after the authority guard |

D fully handled: S1, C1, compound, ambiguous, control_movement, control_combat, control_observation, control_authored_fact, control_followup, var_compound_subtle, var_compound_control, var_ambiguous_subtle, var_pronoun_control, var_conseq_social, var_social_control, var_quote_control, var_negated_control, var_hypothetical_control.

D consumed as interpretations: C1, compound, ambiguous, var_compound_subtle, var_ambiguous_subtle, var_conseq_social, var_social_control, var_quote_control, var_hypothetical_control.

D rejected: declared_canon, mechanical_dump, var_unsupported_mechanic.

D did not execute any row. A PASS under D is a retained interpretation. It is not evidence that a resolver ran, a roll was made, or the world changed.

Universal routing loses `control_combat` because it consumes an invented weapon id and the adapter rejects the payload. Refined selective routing does not send that row, so the deterministic combat interpretation stays selected. If that payload is offered anyway, the fallback preserves the deterministic interpretation and still does not execute it.

`var_unsupported_mechanic` was PARTIAL under B and C because the clarification was consumed. D rejects that clarification. The partial credit is withdrawn. The row is an unsupported action, not a handled turn and not an execution.

Remaining original-matrix failures under D: declared_canon, mechanical_dump, var_unsupported_mechanic. Routing misses under D: none.

Decision code from this comparison: A.
