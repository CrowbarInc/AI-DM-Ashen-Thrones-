# PR-PLAY-29 performance

| # | Operation | Input | Output | Total | Provider seconds | Status | Retry |
|---|---|---:|---:|---:|---:|---|---:|
| 1 | opening | 1378 | 120 | 1498 | 2.893 | completed | 0 |
| 2 | Turn 1 interpretation | 2306 | 217 | 2523 | 2.207 | completed | 0 |
| 3 | Turn 1 expression | 252 | 12 | 264 | 1.350 | completed | 0 |
| 4 | Turn 2 interpretation | 2392 | 195 | 2587 | 1.887 | completed | 0 |

Actual totals: 6328 input + 544 output = 6872 tokens. Four actual provider dispatches, 80% of five-request ceiling. Configured model gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. All four results accepted for their purpose; only opening renderer selection and Turn 1 expression contribute directly to published text. Interpretations remain internal.

Opening API latency 4.906s; Turn 1 4.703s; Turn 2 2.609s. Owned live experiment duration 54.000s, startup through shutdown including evidence gates; preflight/report packaging excluded. Raw observer provider latency differs from native latency_ms because the native budget wraps diagnostics as well; both retained. SDK success/completed responses establish provider success; raw provider HTTP status was not separately captured.

Retries 0; fallback-model requests 0; expression rejection/fallback 0. Turn 2 directly used authored engine speech, so no Turn 2 expression request or token usage exists. Never estimate a fifth call. No AI judge. Source: performance_measurements.json, provider_usage.jsonl, request/response_01..04.json.
