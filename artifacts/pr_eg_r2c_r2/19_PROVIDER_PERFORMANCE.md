# 19 — Provider Performance

```json
{
  "primary": {
    "turns": 16,
    "provider_calls": 10,
    "interpretation_calls": 10,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 19149,
    "output_tokens": 1884,
    "calls_per_turn": 0.625,
    "input_tokens_per_turn": 1196.8125,
    "output_tokens_per_turn": 117.75,
    "average_latency_ms": 1790.0699750025524,
    "maximum_latency_ms": 3339.6101999969687,
    "high_cost_outliers": [
      {
        "turn": 1,
        "latency_ms": 3339.6101999969687,
        "calls": 1,
        "input_tokens": 1729
      },
      {
        "turn": 12,
        "latency_ms": 3120.457799988799,
        "calls": 1,
        "input_tokens": 1987
      },
      {
        "turn": 13,
        "latency_ms": 3116.0750999988522,
        "calls": 1,
        "input_tokens": 1962
      }
    ]
  },
  "secondary": {
    "turns": 13,
    "provider_calls": 8,
    "interpretation_calls": 8,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 15202,
    "output_tokens": 1528,
    "calls_per_turn": 0.6153846153846154,
    "input_tokens_per_turn": 1169.3846153846155,
    "output_tokens_per_turn": 117.53846153846153,
    "average_latency_ms": 1535.8231692404772,
    "maximum_latency_ms": 3007.5326000223868,
    "high_cost_outliers": [
      {
        "turn": 1,
        "latency_ms": 3007.5326000223868,
        "calls": 1,
        "input_tokens": 1725
      },
      {
        "turn": 4,
        "latency_ms": 2655.302200000733,
        "calls": 1,
        "input_tokens": 1888
      },
      {
        "turn": 6,
        "latency_ms": 2566.2529000255745,
        "calls": 1,
        "input_tokens": 1886
      }
    ]
  },
  "combined": {
    "turns": 29,
    "provider_calls": 18,
    "interpretation_calls": 18,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 34351,
    "output_tokens": 3412,
    "calls_per_turn": 0.6206896551724138,
    "input_tokens_per_turn": 1184.5172413793102,
    "output_tokens_per_turn": 117.65517241379311,
    "average_latency_ms": 1676.0972689712773,
    "maximum_latency_ms": 3339.6101999969687,
    "high_cost_outliers": [
      {
        "turn": 1,
        "latency_ms": 3339.6101999969687,
        "calls": 1,
        "input_tokens": 1729
      },
      {
        "turn": 12,
        "latency_ms": 3120.457799988799,
        "calls": 1,
        "input_tokens": 1987
      },
      {
        "turn": 13,
        "latency_ms": 3116.0750999988522,
        "calls": 1,
        "input_tokens": 1962
      }
    ]
  }
}
```



Final per-request journals: final_literal_qualified_live_usage.jsonl / final_provider_usage.json, with configured/returned model, request IDs, sent flags, usage consistency and provider latency. HTTP latency includes local engine work. Per-turn averages include deterministic zero-call turns; outliers are measured.



The R1 reference was 14 calls/27 turns and about 1.14s mean. Final qualification adds real ambiguity and clarification repetition with two visible NPCs, so it is not a controlled performance benchmark. There is no narration or retry escalation. development_provider_cost.json reports all five developmental/qualification runs separately; failed-run cost is retained.
