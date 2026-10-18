# PR-DL Cost Analysis

Figures are provider-reported token counts for the 21 interpretation requests. No provider price is stated. Narration tokens are not included. This is not a complete-turn cost.

| Policy | Requests | Input | Output | Total | Useful PASS interpretations | Total tokens per useful PASS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A deterministic | 0 | 0 | 0 | 0 | 0 | undefined |
| B selective | 10 | 7610 | 1439 | 9049 | 7 | 1292.7143 |
| C universal | 21 | 15943 | 2811 | 18754 | 17 | 1103.1765 |

Useful PASS interpretations are stored outputs the policy consumes whose gameplay score is PASS. Policy B's useful set is C1, compound, ambiguous, var_ambiguous_subtle, var_conseq_social, var_social_control, var_hypothetical_control. Two of those, `var_social_control` and `var_hypothetical_control`, were already PASS under deterministic handling.

Beneficial corrections, including the partial unsupported-mechanic reading: C1, compound, ambiguous, var_compound_subtle, var_ambiguous_subtle, var_conseq_social, var_unsupported_mechanic, var_quote_control.
Selective routing receives the beneficial cases it triggers: C1, compound, ambiguous, var_ambiguous_subtle, var_conseq_social, var_unsupported_mechanic.

Avoided interpretation requests under B: 11
Avoided input tokens: 8333
Avoided output tokens: 1372
Avoided total tokens: 9705

Additional full successes present in C and absent from B: var_compound_subtle, var_quote_control
Missed useful interpretations (selective false negatives with live PASS): var_compound_subtle, var_quote_control
Unnecessary selective invocations: var_social_control, var_hypothetical_control

The output cap was 400. No request was retried. No model was switched. Preflight estimates summed to 27,319 conservative input tokens. Actual input was 15943, inside the 30,000 ceiling. Actual output was 2811, inside the 8,000 ceiling. Actual total was 18754, inside the 38,000 ceiling.
