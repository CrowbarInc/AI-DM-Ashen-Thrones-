# PR-DM Cost Analysis

Token counts are the provider-reported counts stored by PR-DL for `gpt-4.1-mini-2025-04-14`. PR-DM did not make requests and did not invent measurements. Narration tokens are not included. This is not a complete-turn cost and it is not a price.

| Policy | Hypothetical invoked requests | Stored input tokens | Stored output tokens | Stored total tokens | Fully handled | Partially handled | Remaining failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 0 | 0 | 0 | 0 | 11 | 0 | 10 |
| B | 10 | 7610 | 1439 | 9049 | 16 | 1 | 4 |
| C | 21 | 15943 | 2811 | 18754 | 17 | 1 | 3 |
| D | 12 | 9132 | 1725 | 10857 | 18 | 0 | 3 |

D's requests are the original selective requests plus `var_compound_subtle` and `var_quote_control`. Their stored totals are 923 and 885 tokens.

Marginal cost against B: 1808 additional stored tokens for 2 additional fully handled scenarios, 904.0000 stored tokens per additional full interpretation.

Marginal change against C: 1 additional fully handled scenario and -7897 stored tokens. The negative token delta means D uses fewer stored interpretation tokens than universal routing while also keeping `control_combat`.

The two additional full interpretations are interpretation records. They do not measure a completed combat, movement, or world update. No complete-turn affordability is claimed.
