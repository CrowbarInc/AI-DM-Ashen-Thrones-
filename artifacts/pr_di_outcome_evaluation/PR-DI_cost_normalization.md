# PR-DI Cost Normalization

Actual PR-DH usage: 22 requests, 18983 input tokens, 2859 output tokens, 21842 total tokens. Provider: gpt-4.1-mini. Narration tokens were not measured and are excluded. No monetary pricing is inferred.

## Per Scenario

| scenario | candidate | requests | input | output | total | latency_ms | valid_interpretation | useful_interpretation | engine_supported_outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | A | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| S1 | B | 1 | 723 | 165 | 888 | 1999.529 | 1 | 1 | 1 |
| S1 | C | 2 | 1488 | 174 | 1662 | 3515.275 | 1 | 1 | 0 |
| C1 | A | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| C1 | B | 1 | 722 | 167 | 889 | 1658.318 | 1 | 1 | 0 |
| C1 | C | 2 | 1439 | 170 | 1609 | 3177.604 | 1 | 1 | 0 |
| compound | A | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| compound | B | 1 | 721 | 166 | 887 | 2121.706 | 1 | 1 | 0 |
| compound | C | 2 | 1460 | 151 | 1611 | 2308.429 | 1 | 1 | 0 |
| ambiguous | A | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ambiguous | B | 1 | 718 | 193 | 911 | 1763.914 | 1 | 1 | 0 |
| ambiguous | C | 4 | 4176 | 364 | 4540 | 4693.001 | 1 | 0 | 0 |
| declared_canon | A | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| declared_canon | B | 1 | 735 | 304 | 1039 | 3286.496 | 1 | 1 | 0 |
| declared_canon | C | 2 | 1531 | 209 | 1740 | 2900.437 | 1 | 1 | 0 |
| mechanical_dump | A | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| mechanical_dump | B | 1 | 795 | 366 | 1161 | 3231.875 | 1 | 1 | 0 |
| mechanical_dump | C | 4 | 4475 | 430 | 4905 | 5245.394 | 1 | 1 | 0 |


## Aggregate

| candidate | requests | input | output | total | latency_ms | valid_count | tokens_per_valid | useful_count | tokens_per_useful | supported_count | tokens_per_supported |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 | 0 | 0 | 0 | 0 | 1 | 0.0 | 2 | 0.0 | 2 | 0.0 |
| B | 6 | 4414 | 1361 | 5775 | 14061.838 | 6 | 962.5 | 6 | 962.5 | 1 | 5775.0 |
| C | 16 | 14569 | 1498 | 16067 | 21840.14 | 6 | 2677.83 | 5 | 3213.4 | 0 | N/A |


Interpretation: B bought useful interpretation in all six scenarios for 5,775 tokens and one supported execution outcome. C spent 16,067 tokens across 16 rounds, with useful interpretation in five scenarios but no successful live execution in the recovered PR-DH transcripts. A had zero interpretation-provider cost but only two useful/supported outcomes under this rubric.
