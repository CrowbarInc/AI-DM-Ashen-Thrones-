# 15 — Provider Performance

FRESH measured totals and turn averages:

```json
{
  "primary": {
    "turns": 15,
    "provider_calls": 8,
    "interpretation_calls": 8,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 14874,
    "output_tokens": 1507,
    "avg_input_tokens": 991.6,
    "avg_output_tokens": 100.46666666666667,
    "calls_per_turn": 0.5333333333333333,
    "avg_latency_ms": 1395.9375133311066,
    "max_latency_ms": 3651.693299994804,
    "p50_latency_ms": 2000.4724999889731,
    "raw_failure_flags": 6,
    "failed_turns": [
      3,
      7,
      8,
      13,
      14
    ]
  },
  "secondary": {
    "turns": 12,
    "provider_calls": 6,
    "interpretation_calls": 6,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 11220,
    "output_tokens": 1123,
    "avg_input_tokens": 935.0,
    "avg_output_tokens": 93.58333333333333,
    "calls_per_turn": 0.5,
    "avg_latency_ms": 1227.5578999954935,
    "max_latency_ms": 3293.486800015671,
    "p50_latency_ms": 1036.5795500110835,
    "raw_failure_flags": 6,
    "failed_turns": [
      1,
      2,
      6,
      7,
      12
    ]
  },
  "combined": {
    "turns": 27,
    "provider_calls": 14,
    "interpretation_calls": 14,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 26094,
    "output_tokens": 2630,
    "avg_input_tokens": 966.4444444444445,
    "avg_output_tokens": 97.4074074074074,
    "calls_per_turn": 0.5185185185185185,
    "avg_latency_ms": 1321.1021296263896,
    "max_latency_ms": 3651.693299994804,
    "p50_latency_ms": 1981.6883000021335,
    "raw_failure_flags": 12,
    "failed_turns": [
      3,
      7,
      8,
      13,
      14,
      1,
      2,
      6,
      7,
      12
    ]
  }
}
```

All sent calls are interpretation. No narration, semantic validation provider call, or retry is observed in these 27 turns. Deterministic host adoption is not a semantic-validation call. live_usage.jsonl supplies actual token usage and returned models; live_qualification.json has wall-clock turn timing and provider-call counts. High-latency outliers are the individual interpretation turns; all turn timings are retained. No unbounded loop or large prompt escalation is observed.

HISTORICAL PR-EG-R1 measured 6 calls / 56,440 input tokens for its primary15 and 4 calls / 53,374 input tokens for secondary12, including two narration calls each. R2 experiments were isolated compact-generation/validator calls, not a comparable production conversation. The present fixture adds security questions and uses a second speaker; it is not an apples-to-apples performance comparison. Lower input totals follow bypassing narration, while relevance fails. This is not an overall performance/quality improvement claim.
