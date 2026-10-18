# PR-CO Latency And Retries

All figures below are measured from the OpenAI Responses usage and the probe timer. Cached input tokens were 0 on every request.

## Requests

| # | Turn | Kind | Retry | Reason | Latency s | Input | Output | Total | Usable output |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | startup | preflight | 0 | | 2.545 | 24 | 2 | 26 | yes |
| 2 | T1 | generation | 0 | | 3.365 | 30970 | 128 | 31098 | yes, then hard_invalid |
| 3 | T1 | generation | 1 | hard_invalid | 2.155 | 38464 | 67 | 38531 | yes, then hard_invalid |
| 4 | T2 | interpretation | 0 | | 2.382 | 900 | 130 | 1030 | yes |
| 5 | T2 | generation | 0 | | 2.942 | 29914 | 128 | 30042 | yes, then hard_invalid |
| 6 | T2 | generation | 1 | hard_invalid | 2.415 | 37347 | 132 | 37479 | yes, then hard_invalid |
| 7 | T3 | generation | 0 | | 3.108 | 35302 | 120 | 35422 | yes, then hard_invalid |
| 8 | T3 | generation | 1 | hard_invalid | 2.841 | 43230 | 43 | 43273 | yes, then hard_invalid |
| 9 | T4 | interpretation | 0 | | 2.022 | 960 | 97 | 1057 | yes |
| 10 | T4 | generation | 0 | | 8.214 | 32342 | 1156 | 33498 | yes, then hard_invalid |
| 11 | T4 | generation | 1 | hard_invalid | 17.068 | 40247 | 2292 | 42539 | yes, then hard_invalid |
| 12 | T5 | interpretation | 0 | | 1.514 | 927 | 115 | 1042 | yes |

No request was automatically rerun by the probe. The retries above are the engine's own regeneration after `hard_invalid`.

Turn 5 logged `[RETRY SKIPPED: NONRETRYABLE UPSTREAM ERROR]` and `failure_class=unknown_api_error`. The message excerpt is `provider request budget reached (12)`. That error is the probe guard, classified by `call_gpt` as an upstream failure. The realization fallback family is `gpt_budget_or_provider_failure`.

## Aggregates

- Provider requests: 12, including 1 preflight and 4 generation retries.
- Combined tokens: 295,037.
- Total provider latency: 50.571 seconds.
- Mean latency per request: 4.214 seconds.
- Mean provider latency per completed HTTP turn: 9.605 seconds.
- Median provider latency per completed HTTP turn: 5.949 seconds (T3).
- Slowest request: T4 retry, 17.068 seconds, 2,292 output tokens.
- Wall clock of the probe process: about 60 seconds.

Turns 1–4 each spent a generation and a retry. Turns 2 and 4 also spent an interpretation call. That pattern reached 12 requests during turn 5's interpretation, so the observation generation was never sent.

Retry token overhead: 161,822 tokens (the four `retry_attempt=1` generations), 54.8% of all tokens.

Tokens on generations that validation rejected: 291,882 (98.9% of all tokens). Interpretation and preflight account for the other 3,155 tokens.
