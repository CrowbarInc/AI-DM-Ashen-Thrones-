# Provider accounting

Limits for the browser process: 5 requests, 4,000 input tokens, 1,000 output tokens, 5,000 total tokens. Retries disabled. Model `gpt-4.1-mini`. No opening.

| # | Purpose | Attempt | In | Out | Total | Latency ms |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | expression | `aed6b30c010a448681b307a0fe012397` | 60 | 12 | 72 | 1936.353 |
| 2 | contract_interpretation | `8ec204a85891458382e48cd17e29bb26` | 1115 | 132 | 1247 | 1692.886 |
| 3 | expression | `a47332cdcfcf44e5b4721a69f309ede4` | 164 | 14 | 178 | 931.592 |
| 4 | contract_interpretation | `7048bd2695c3489e9600451bfe359d7b` | 1164 | 103 | 1267 | 1538.854 |
| 5 | contract_interpretation | `bfb084b295d349f68965818471ce70d0` | 1163 | 117 | 1280 | 2097.418 |

Completed requests: 5. Input tokens: 3,666. Output tokens: 378. Total tokens: 4,044. Retries: 0. All five rows have `usage_consistent` true and `sent` true. Admitted and dispatch rows for the same attempt are not extra requests.

Ordering: the retreat sent expression only. The guard question sent interpretation, then expression. Each examination sent interpretation only. No expression ran before its turn’s interpretation, and no turn sent two expressions.

The budget was fully used on requests and remained under the token ceiling. A further live call was not made.
