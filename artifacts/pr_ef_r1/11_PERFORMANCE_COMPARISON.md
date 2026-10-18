# 11 — Performance Comparison

| Live sample | Calls | Input | Output | Total | Median turn ms | Retry-stamped requests |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 62422 | 2681 | 65103 | 3033.5155 | 0 |
| 2 | 11 | 87666 | 3099 | 90765 | 2390.949 | 1 |
| 3 | 9 | 39066 | 1525 | 40591 | 2439.7625 | 0 |
| 4 | 11 | 69992 | 3136 | 73128 | 2674.0185 | 1 |
| 5 | 9 | 39250 | 1505 | 40755 | 2744.0385 | 0 |

Cycle totals including availability/holdouts: {'input_tokens': 336813, 'output_tokens': 16494, 'total_tokens': 353307, 'requests': 75}. Budget revisions and actual limits in budget.json; no exhaustion. Request-level records are authoritative; missing usage is not zero. Retry count uses explicit retry_escalation provider purposes, not inferred response wording. Existing summary telemetry can report retry_count=0 despite a sent retry_escalation request; that instrumentation discrepancy is retained in raw resolutions and corrected only in this evidence aggregation.

Historical PR-EF sequences: 85,242 / 87,739 tokens and 9 calls each. Different code, prompts, phrasing and outcomes preclude a controlled live speedup claim. Same PR-ED disabled profiler: baseline median 89ms and 6 narration entries; final measured median 97ms and 5 entries. Single-run machine load differs; no latency improvement claim. The last ambiguity-only gate does not affect that profiler workload.

No mandatory second interpretation, new retry loop, model switch or full-transcript injection. Existing caps/timeouts/retry controls retained. Successful clue discovery skips redundant narration while NPC dialogue still uses its provider.
