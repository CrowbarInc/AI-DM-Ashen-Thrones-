# PR-PLAY-26 performance

| Request | Purpose | Input | Output | Total | Provider seconds | API seconds | Status/retries |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | primary_turn | 1378 | 120 | 1498 | 3.480 | 4.359 | completed/0 |
| 2 | interpretation | 2306 | 235 | 2541 | 2.322 | 3.719 | completed/0 |
| 3 | expression | 221 | 10 | 231 | 0.988 | 3.719 | completed/0 |

Configured model gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. Requests 2 and 3 share one API duration; do not add those API values. No follow-up requests.

Totals: 3 requests; 3905 input, 365 output, 4270 total tokens. Opening 4.359s; first interaction 3.719s; follow-up N/A. Live experiment 30.360s, including manual review wait and cleanup; offline preflight 3.625s, packaging excluded. Retries 0; no fallback/judge requests. No token ceilings increased.
