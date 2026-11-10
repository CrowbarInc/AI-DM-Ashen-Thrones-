# PR-PLAY-24 performance

All configured requests gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. No retries, escalations, fallbacks or judge requests.

| Request/purpose | Input | Output | Total | Provider seconds | API seconds | Status | Retries |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 primary_turn | 1378 | 120 | 1498 | 3.897 | 5.016 | completed | 0 |
| 2 interpretation | 2306 | 226 | 2532 | 2.298 | 5.500 | completed | 0 |
| 3 expression | 163 | 15 | 178 | 1.097 | 5.500 | completed | 0 |

Rows 2 and 3 belong to ONE HTTP action; the shared 5.500s API duration must not be summed twice. Provider seconds measure SDK invocation wall time; dispatch ledger latencies are preserved separately. Model selection was not changed.

Totals: 3 provider requests, 3847 input + 361 output = 4208 tokens. Opening: 1498 tokens, 5.016s API. Ordinary question: TWO provider calls, 2710 tokens, 5.500s API. No follow-up; remaining provider budget zero. Expression request was attempted once, not a retry of interpretation.

Live controller duration: 13.922s (start through state capture, cleanup and port verification). Offline preflight controller: 2.469s; combined measured controllers 16.391s. Repository inspection/report writing/packaging excluded from runtime; no claim that these durations measure the entire human review session. Request timestamps and detailed timing preserved in performance_measurements.json and provider ledger.

Output limits unchanged: opening 3000 (existing), expression 80 (existing); aggregate ceilings 200000 input, 20000 output, 220000 total. Production request ceiling 3 was reached without a fourth admission attempt.
