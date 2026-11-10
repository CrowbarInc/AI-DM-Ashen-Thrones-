# Token and Latency Attribution

Source: completed ledger rows with `sent: true`, one row per attempt. Admission and dispatch rows are not extra requests. Cycles are separate revisions. Do not read the table as one benchmark.

Provider latency is the ledger `latency_ms` (dispatch to completion). Server totals are the session `performance.elapsed_ms` where a session log recorded them. Browser paint time was not instrumented on these runs. Server time is not paint time.

p95 is omitted when a route has fewer than five latency samples.

## By cycle and purpose

| Cycle | Route | Requests | Input | Output | Tokens/request | Provider latency median ms | Useful provider publications |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 79 | primary_turn | 3 | 71,433 | 2,582 | 24,671.7 | 4,344.5 | 0 narrations published (cycle report) |
| 79 | retry_escalation | 2 | 57,075 | 621 | 28,848.0 | 2,968.1 | Included in the 0 published narrations |
| 79 | interpretation | 4 | 10,096 | 864 | 2,740.0 | 1,899.2 | Not separately scored |
| 79 | contract_interpretation | 2 | 1,843 | 223 | 1,033.0 | 1,570.4 | Not separately scored |
| 79 | expression | 2 | 154 | 77 | 115.5 | 812.5 | 0 dialogue lines accepted (cycle report) |
| 79A | primary_turn | 3 | 74,257 | 4,468 | 26,241.7 | 11,579.4 | UNKNOWN exact accept count |
| 79A | expression | 15 | 2,676 | 464 | 209.3 | 886.1 (p95 1,306.9) | Several lines published, then the conversation broke (handoff). Exact count UNKNOWN |
| 79A | interpretation | 1 | 2,426 | 227 | 2,653.0 | 1,906.2 | UNKNOWN |
| 79A | contract_interpretation | 2 | 1,880 | 208 | 1,044.0 | 1,316.2 | UNKNOWN |
| 79B | primary_turn | 1 | 25,294 | 1,662 | 26,956.0 | 11,334.2 | Opening-scale call. Dialogue goal not met |
| 79B | expression | 17 | 3,188 | 575 | 221.4 | 870.7 (p95 1,248.2) | Six consecutive accepted lines were not reached |
| 79B | interpretation | 2 | 4,693 | 479 | 2,586.0 | 1,936.1 | UNKNOWN |
| 79B | contract_interpretation | 3 | 3,381 | 339 | 1,240.0 | 1,197.1 | UNKNOWN |
| 79C | primary_turn | 1 | 25,294 | 1,363 | 26,657.0 | 11,867.0 | Opening-scale call |
| 79C | expression | 15 | 2,979 | 417 | 226.4 | 765.1 (p95 1,218.4) | UNKNOWN |
| 79C | interpretation | 1 | 2,390 | 185 | 2,575.0 | 1,564.3 | UNKNOWN |
| 79C | contract_interpretation | 3 | 3,340 | 314 | 1,218.0 | 1,527.1 | UNKNOWN |
| 79D browser | contract_interpretation | 1 | 1,136 | 120 | 1,256.0 | 2,612.5 | Stage ledger, not a full campaign |
| 79D browser | expression | 2 | 639 | 53 | 346.0 | 1,162.0 | Stage ledger |
| 79D final | contract_interpretation | 4 | 4,431 | 459 | 1,222.5 | 1,426.3 | Handoff: five NPC lines and one live narration across all 79D browser ledgers |
| 79D final | expression | 4 | 773 | 86 | 214.8 | 996.9 | Same handoff claim. Per-stage split UNKNOWN |
| 79D boundary | expression | 1 | 276 | 20 | 296.0 | 1,282.7 | Boundary stage |
| 79D-F | contract_interpretation | 3 | 3,442 | 352 | 1,264.7 | 1,692.9 | Examinations and the guard question |
| 79D-F | expression | 2 | 224 | 26 | 125.0 | 1,434.0 | Retreat accepted (72 tokens). Guard expression not accepted |
| 79D-F2 | contract_interpretation | 1 | 1,160 | 122 | 1,282.0 | 2,797.3 | UNKNOWN beyond the cycle’s one accepted line |
| 79D-F2 | expression | 2 | 420 | 49 | 234.5 | 1,341.8 | Earlier browser stage |
| 79D-F2 final | expression | 1 | 273 | 34 | 307.0 | 1,938.3 | Accepted “Hello, Gate Guard.” |
| 79D-F3 HTTP | primary_turn | 1 | 22,777 | 600 | 23,377.0 | 5,339.7 | 0. Published fallback does not narrate the retreat |
| 79D-F3 browser | — | 0 | 0 | 0 | — | — | Simulated admission. No completed request |

Machine detail: `artifacts/at_opt_01/ledger_summary.json`.

79D’s three browser ledgers sum to 12 requests and 7,993 tokens, matching the handoff. They are three stages. The table keeps them separate.

79D-F2’s two ledgers sum to 4 requests and 2,058 tokens, matching the handoff.

## Requests over 20,000 input tokens

All eleven are `gm.call_gpt`. None are expression or interpretation.

| Cycle | Purpose | Input | Output | Total | Latency ms |
| --- | --- | ---: | ---: | ---: | ---: |
| 79 | primary_turn | 25,294 | 1,382 | 26,676 | recorded in ledger |
| 79 | primary_turn | 22,961 | 600 | 23,561 | output hit the 600 cap |
| 79 | primary_turn | 23,178 | 600 | 23,778 | output hit the 600 cap |
| 79 | retry_escalation | 28,425 | 314 | 28,739 | |
| 79 | retry_escalation | 28,650 | 307 | 28,957 | |
| 79A | primary_turn | 25,294 | 1,924 | 27,218 | |
| 79A | primary_turn | 25,294 | 1,944 | 27,238 | same input count as the row above |
| 79A | primary_turn | 23,669 | 600 | 24,269 | output hit the 600 cap |
| 79B | primary_turn | 25,294 | 1,662 | 26,956 | |
| 79C | primary_turn | 25,294 | 1,363 | 26,657 | |
| 79D-F3 | primary_turn | 22,777 | 600 | 23,377 | 5,339.716 |

Identical 25,294 input counts recur on 79, 79A (twice), 79B, and 79C. That is recorded. Equal counts do not prove the prompts were byte-identical. Two 79A completions with the same input count and different output counts are two sent requests.

## Publication efficiency

| Cycle | Sent | Completed and sent | Tokens | Provider-backed useful publications | Tokens per useful provider publication |
| --- | ---: | ---: | ---: | --- | --- |
| 79 | 13 | 13 | 144,968 | 0 narrations and 0 dialogue lines accepted | Undefined. 131,711 of the tokens are the five primary/retry calls |
| 79A | 21 | 21 | 86,606 | Handoff says several lines published. Exact count UNKNOWN | UNKNOWN. Primary calls are 78,725 of the tokens (90.9%) |
| 79B | 23 | 23 | 39,611 | Six consecutive accepted lines were not reached. Exact count UNKNOWN | UNKNOWN. The one primary call is 26,956 tokens (68.1%) |
| 79C | 20 | 20 | 36,282 | UNKNOWN | UNKNOWN. The one primary call is 26,657 tokens |
| 79D stages | 12 | 12 | 7,993 | Handoff: five NPC lines and one live narration | 1,332 if those six are the useful publications. Per-line token split was not re-audited |
| 79D-F | 5 | 5 | 4,044 | 1 accepted retreat expression | 72 for that publication. 4,044 if the whole cycle is the denominator |
| 79D-F2 | 4 | 4 | 2,058 | 1 accepted greeting expression | 307 for that call. 2,058 for the cycle |
| 79D-F3 | 1 | 1 | 23,377 | 0 | Undefined |

Rejected or replaced primary output is the expensive case. F3’s only sent call was replaced before publication. PR-PLAY-79’s narration report is 0 published. Two of 79’s three primary calls, one of 79A’s three, and the F3 call all finished at exactly 600 output tokens, which is the narration cap. Whether those completions were truncated is a hypothesis: the ledger records the count and does not record finish reason.

## F3 timing coverage

Provider dispatch 5,339.716 ms. Session narration stage 6,032 ms. Session total 6,166 ms. The GM `provider_call` stamp says 5,733 ms. The stamp starts when dispatch is about to run; the ledger timer starts inside `RequestAttempt.dispatch`. The gap is local overhead around the provider call. Browser-visible completion for this HTTP script: not measured.

The F browser retreat’s network row records server monotonic time 4,115.47 ms and provider latency 1,936.353 ms. That server figure is not paint time.
