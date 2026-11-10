# Performance and usage

Provider: OpenAI. Model returned: `gpt-4.1-mini-2025-04-14`. Cost: not estimated. The configuration has no price table.

| Request | Input tokens | Output tokens | Total | Adapter latency ms | Ledger dispatch latency ms | Retries | Error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A1 | 421 | 73 | 494 | 3222.399 | 2621.126 | 0 | none |
| A2 | 421 | 59 | 480 | 1767.808 | 1417.386 | 0 | none |
| B1 | 420 | 67 | 487 | 1981.214 | 1624.939 | 0 | none |
| C1 | 411 | 62 | 473 | 1723.679 | 1267.712 | 0 | none |
| C2 | 411 | 58 | 469 | 1907.526 | 1545.370 | 0 | none |
| D1 | 403 | 52 | 455 | 1143.391 | 877.579 | 0 | none |

Adapter latency is the clock inside `request_expression`, including client construction. Ledger latency is the dispatch interval recorded by provider accounting. Both sets match the same six requests. Token totals match the ledger completions exactly: input 2,487, output 371, total 2,858. `usage_consistent` is true on all six completions.

| Measure | Value |
| --- | --- |
| Provider requests | 6 |
| Successful requests | 6 |
| Failed requests | 0 |
| Total tokens | 2,858 |
| Mean adapter latency | 1.958 s |
| Median adapter latency | 1.838 s |
| Maximum adapter latency | 3.222 s |
| Mean ledger dispatch latency | 1.559 s |
| Maximum ledger dispatch latency | 2.621 s |
| Mean direct validator latency | 1.115 ms |
| Maximum direct validator latency | 1.526 ms |
| Mean pipeline validation latency | 5.609 ms |
| Maximum pipeline validation latency | 18.858 ms |

Output tokens stayed under the 80-token adapter cap and under the 700-token cycle cap. The largest output was 73 tokens. Aggregate tokens are 2,858 of the 12,000 cycle ceiling.

## PR-PLAY-53

That cycle recorded 2 successful requests, 954 tokens, about 2.01 seconds mean provider latency, and about 2.30 seconds maximum. This cycle's mean adapter latency is close to that mean. The maximum here is higher, on A1. Token use per request is about 476, against about 477 in that earlier pair. The comparison is descriptive. Six requests do not establish a stable latency distribution.

No request timed out. No retry ran.
