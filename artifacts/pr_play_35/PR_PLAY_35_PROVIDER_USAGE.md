# Provider usage

| Measure | Value |
| --- | --- |
| Dispatched requests | 1 |
| Mission ceiling | 10 |
| Requests remaining | 9 |
| Input tokens | 26714 |
| Output tokens | 1667 |
| Total tokens | 28381 |
| Provider latency | 12104.932 ms |
| HTTP latency for start | 13.047 s |
| Experiment wall time | 14.969 s |
| Completed gameplay turns | 0 |
| Average latency per completed turn | not applicable |
| Retries or fallbacks | 0 |
| Provider errors or timeouts | 0 |
| Budget stop | no |

The single dispatch was `purpose=primary_turn`, `owner=gm.call_gpt`, configured model `gpt-4.1-mini`, returned model `gpt-4.1-mini-2025-04-14`, completion status `completed`, usage consistent. SDK retries were 0 and host retries were disabled. The ledger then recorded `accepted_structured_response`: extraction succeeded, JSON parsing succeeded, narration length 945, nine declarations.

No second provider call was made after the semantic rejection.
