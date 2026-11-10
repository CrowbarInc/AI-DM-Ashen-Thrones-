# Performance and usage

PR-PLAY-52's local hook measurement, about 6 ms including evidence writing, is not a provider latency. The provider time below is from this run only.

Two real requests. No retries. No timeouts. No provider error.

| Scenario | Started (UTC) | Completed (UTC) | Create latency | Adapter latency | Hook work | Validation | Turn |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A notice board | 2026-11-03T03:35:24.305411+00:00 | 2026-11-03T03:35:27.072804+00:00 | 2301.393 ms | 2765.708 ms | 2769.381 ms | 1.546 ms | 2897.936 ms |
| B rain barrel | 2026-11-03T03:35:27.436224+00:00 | 2026-11-03T03:35:29.346168+00:00 | 1717.644 ms | 1908.590 ms | 1912.010 ms | 1.652 ms | 2028.274 ms |

Create latency is the ledger's `dispatch()` timer around `responses.create`. Adapter latency is `request_expression`'s timer, which also includes constructing the client. The gap is local client setup, about 464 ms on A and 191 ms on B.

Local hook overhead after the adapter returned was about 3.7 ms on A and 3.4 ms on B. That is the same order as PR-PLAY-52's offline hook. Validation was about 1.6 ms. Evidence writing is inside `total_hook_ms` and is under 2 ms beyond hook work.

| Aggregate | Value |
| --- | --- |
| Successful provider requests | 2 |
| Failed provider requests | 0 |
| Input tokens | 421 + 411 = 832 |
| Output tokens | 63 + 59 = 122 |
| Total tokens | 954 |
| Mean create latency | 2009.5 ms |
| Maximum create latency | 2301.4 ms |
| Mean adapter latency | 2337.1 ms |
| Maximum adapter latency | 2765.7 ms |
| Output tokens per request | 63 and 59, both under the cap of 80 and under the ceiling of 1,000 |
| Estimated cost | unavailable |

`provider_usage.jsonl` contains `initialized`, then for each request `admitted`, `dispatch_attempted`, and `completed`. The completed rows show purpose `expression`, `sent: true`, and the same token counts. The in-memory snapshot agrees: 2 dispatched requests, 832 / 122 / 954. Usage was not reported as zero.

Scenario C added no ledger row and no create call. Its hook work was 0.237 ms before evidence writing.
