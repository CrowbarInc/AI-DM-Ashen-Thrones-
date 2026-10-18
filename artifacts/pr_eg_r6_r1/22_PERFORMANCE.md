# 22 PERFORMANCE

```json
{
  "final_fresh": {
    "turns": 60,
    "provider_calls": 52,
    "calls_per_turn": 0.8666666666666667,
    "mean_input_tokens_per_turn": 1462.9666666666667,
    "p95_input_tokens_per_turn": 1892,
    "mean_latency_ms": 1895.768286663709,
    "p95_latency_ms": 2783.7787000171375,
    "input_tokens": 87778,
    "output_tokens": 9185,
    "retry_calls": 0
  },
  "original_before": {
    "turns": 1,
    "provider_calls": 1,
    "calls_per_turn": 1.0,
    "mean_input_tokens_per_turn": 1638,
    "p95_input_tokens_per_turn": 1638,
    "mean_latency_ms": 3375.8326999959536,
    "p95_latency_ms": 3375.8326999959536,
    "input_tokens": 1638,
    "output_tokens": 164,
    "retry_calls": 0
  },
  "original_after": {
    "turns": 2,
    "provider_calls": 2,
    "calls_per_turn": 1.0,
    "mean_input_tokens_per_turn": 1638,
    "p95_input_tokens_per_turn": 1638,
    "mean_latency_ms": 2405.559599996195,
    "p95_latency_ms": 3023.5833000042476,
    "input_tokens": 3276,
    "output_tokens": 328,
    "retry_calls": 0
  },
  "note": "Retry purposes only; generic retry activity is not exhaustively instrumented. Dollar cost not calculated without verified pricing. Authorship and interrupted runs are excluded from final-turn aggregates, retained in usage files."
}
```

The authorization function is deterministic and creates no additional provider request. The single original fresh baseline is too small and structurally different from the full final set to establish a general latency regression. No dollar-pricing or exhaustive retry-frequency claim is made.
