# 17 — Provider Performance

```json
{
  "primary": {
    "turns": 15,
    "provider_calls": 8,
    "interpretation_calls": 8,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 14929,
    "output_tokens": 1522,
    "calls_per_turn": 0.5333333333333333,
    "input_tokens_per_turn": 995.2666666666667,
    "output_tokens_per_turn": 101.46666666666667,
    "average_latency_ms": 1164.2324200016446,
    "maximum_latency_ms": 2912.667099997634,
    "failed_turns": [
      7,
      8
    ],
    "high_cost_outliers": [
      {
        "turn": 1,
        "elapsed_ms": 2912.667099997634,
        "calls": 1,
        "input_tokens": 1711
      },
      {
        "turn": 12,
        "elapsed_ms": 2259.8974999855272,
        "calls": 1,
        "input_tokens": 1903
      },
      {
        "turn": 9,
        "elapsed_ms": 2108.2988000125624,
        "calls": 1,
        "input_tokens": 1866
      }
    ]
  },
  "secondary": {
    "turns": 12,
    "provider_calls": 6,
    "interpretation_calls": 6,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 11182,
    "output_tokens": 1132,
    "calls_per_turn": 0.5,
    "input_tokens_per_turn": 931.8333333333334,
    "output_tokens_per_turn": 94.33333333333333,
    "average_latency_ms": 1104.6360750042368,
    "maximum_latency_ms": 2471.3910999998916,
    "failed_turns": [],
    "high_cost_outliers": [
      {
        "turn": 1,
        "elapsed_ms": 2471.3910999998916,
        "calls": 1,
        "input_tokens": 1713
      },
      {
        "turn": 11,
        "elapsed_ms": 2333.687900012592,
        "calls": 1,
        "input_tokens": 1897
      },
      {
        "turn": 3,
        "elapsed_ms": 2079.831299983198,
        "calls": 1,
        "input_tokens": 1865
      }
    ]
  },
  "combined": {
    "turns": 27,
    "provider_calls": 14,
    "interpretation_calls": 14,
    "narration_calls": 0,
    "retry_calls": 0,
    "input_tokens": 26111,
    "output_tokens": 2654,
    "calls_per_turn": 0.5185185185185185,
    "input_tokens_per_turn": 967.074074074074,
    "output_tokens_per_turn": 98.29629629629629,
    "average_latency_ms": 1137.7451555583523,
    "maximum_latency_ms": 2912.667099997634,
    "failed_turns": [
      7,
      8
    ],
    "high_cost_outliers": [
      {
        "turn": 1,
        "elapsed_ms": 2912.667099997634,
        "calls": 1,
        "input_tokens": 1711
      },
      {
        "turn": 1,
        "elapsed_ms": 2471.3910999998916,
        "calls": 1,
        "input_tokens": 1713
      },
      {
        "turn": 11,
        "elapsed_ms": 2333.687900012592,
        "calls": 1,
        "input_tokens": 1897
      }
    ]
  }
}
```

Compared with the historical matched 27-turn R2C workload: 14 calls, 0 narration, 0 retries, 26,094 input and 2,630 output tokens. Final workload uses the same question order; compare actual totals above. Provider timing is observed latency, not a statistically controlled benchmark. final_provider_usage.json isolates the final run; live_usage.jsonl and all_attempt_provider_cost.json retain all exploratory/qualification costs. Do not mistake cumulative usage for final-run usage.

Failed attempts remain in live_attempt_1, live_attempt_2, qualification_before_generic_compatibility_fix and live_attempt_4. One intermediate run required strict-social narration/retry for the lost preference referent; the final run does not. Requalification runs are distinct experiments, not retries inside a turn.
