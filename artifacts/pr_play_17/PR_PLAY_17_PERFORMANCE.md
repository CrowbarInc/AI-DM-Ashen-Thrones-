# PR-PLAY-17 Performance

| Metric | Observed |
|---|---:|
| Live dispatched requests | 1 / 6 ceiling |
| Successful provider transport/completion | 1 |
| Failed provider transport | 0 |
| Accepted gameplay responses | 0 |
| Contract-rejected responses | 1 |
| Input tokens | 26,986 |
| Output tokens | 2,050 |
| Total tokens | 29,036 |
| Total provider latency | 14.189359 s |
| Average request latency | 14.189359 s |
| Longest request latency | 14.189359 s |
| Harness wall-clock execution | 18.906 s |
| Completed player turns | 0 |
| Requests per completed turn | Undefined (zero denominator) |

The provider completed without output truncation; opening allowance remained 3000. Aggregate ceilings unchanged at input/output/total 200000/20000/220000. Five request admissions remained unused; no budget exhaustion. No retries, fallback, judges or probes. Token/latency evidence comes from native completed ledger record, not synthetic estimates; see request_review.json and live_run/diagnostics/provider_usage.jsonl.

One opening response took about 14.2 seconds at the provider and failed publication. This is a noticeable wait, and did not deliver a usable interactive result. Ordinary-turn latency and steady-state interactive suitability cannot be assessed from this one failed opening. No reliable current pricing was consulted; monetary cost not estimated. Harness wall time excludes qualification, review and archive construction.
