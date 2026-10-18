# 12 — Performance Comparison

| Sample | Calls | Input tokens | Output | Total | Retry-purpose calls | Median turn ms |
|---|---:|---:|---:|---:|---:|---:|
| conversation_1.json | 17 | 194928 | 2468 | 197396 | 3 | 3512.264 |
| conversation_2.json | 17 | 196186 | 2366 | 198552 | 3 | 4128.475 |
| conversation_3.json | 17 | 197112 | 2390 | 199502 | 3 | 2958.969 |
| originals_1.json | 8 | 124736 | 1062 | 125798 | 2 | 8379.993 |
| originals_2.json | 5 | 52942 | 728 | 53670 | 2 | 6290.853 |

Whole cycle provider totals: {'requests': 134, 'input_tokens': 1087623, 'output_tokens': 21970, 'total_tokens': 1109593}. Raw request/model/token/latency records are in usage JSONL; missing fields remain unknown, not silently zeroed per request. End-to-end latency is perf_counter across actual HTTP. Retry totals count stamped provider purposes; summarized retry_count can underreport compared with request records. Some narration usage records lack provider latency, so HTTP time is the reliable per-turn timing here.

Matched original-24 recorded baseline/final provider-free HTTP timings are in recorded_performance.json; both use the same captured interpretation workload but are single local runs, not controlled benchmarks.

Historical R1 ten-turn observation was about 40,755 tokens and 2.74s median. Final R2 has eleven turns and three knowledge-limited/request patterns provoking large strict-social prompts and bounded retry; its roughly 200k-token conversation is substantially more expensive in observed totals. Workloads are different, so this is not a controlled speed/cost comparison and no improvement is claimed. The repair adds no mandatory interpretation call, no new narration route, no broad retry or unbounded memory; it preserves the one-retry ceiling and deterministic PR-ED skip seams. Existing strict-social context size/overrejection/retry behavior remains an important efficiency limitation. A default budget increase was explicitly recorded after measuring prompt size; there was no silent cap bypass.
