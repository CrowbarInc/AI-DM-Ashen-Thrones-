# 17 — Provider Cost and Latency

Repaired usage by purpose:

```json
{
  "interpretation": {
    "calls": 10,
    "input_tokens": 18465,
    "output_tokens": 1957,
    "latency_ms": 22273.045000000002
  },
  "expression": {
    "calls": 12,
    "input_tokens": 2187,
    "output_tokens": 193,
    "latency_ms": 12583.574
  }
}
```

Pre-repair usage, retained separately and not added into the repaired totals:

```json
{
  "interpretation": {
    "calls": 11,
    "input_tokens": 20382,
    "output_tokens": 2096,
    "latency_ms": 27638.592
  },
  "expression": {
    "calls": 12,
    "input_tokens": 2152,
    "output_tokens": 203,
    "latency_ms": 13877.104000000001
  }
}
```

Turn-level metrics:

```json
{
  "primary": {
    "turns": 15,
    "provider_calls": 13,
    "interpretation_calls": 6,
    "narration_calls": 0,
    "expression_calls": 7,
    "retry_calls": 0,
    "input_tokens": 12414,
    "output_tokens": 1259,
    "calls_per_turn": 0.867,
    "expression_attempts": 7,
    "expression_adopted": 5,
    "expression_rejected": 2,
    "expression_fallbacks": 2,
    "expression_input_tokens": 1241,
    "expression_output_tokens": 100,
    "expression_latency_ms_mean": 1056.8,
    "expression_latency_ms_max": 1233.2,
    "validation_ms_mean": 0.095,
    "turn_latency_ms_mean": 1497.3,
    "turn_latency_ms_p50": 1190.3,
    "turn_latency_ms_max": 3674.1,
    "score_mean": 1.933,
    "score_distribution": {
      "2": 6,
      "3": 5,
      "1": 2,
      "0": 2
    },
    "score_zero_turns": [
      11,
      12
    ]
  },
  "secondary": {
    "turns": 12,
    "provider_calls": 9,
    "interpretation_calls": 4,
    "narration_calls": 0,
    "expression_calls": 5,
    "retry_calls": 0,
    "input_tokens": 8238,
    "output_tokens": 891,
    "calls_per_turn": 0.75,
    "expression_attempts": 5,
    "expression_adopted": 3,
    "expression_rejected": 2,
    "expression_fallbacks": 2,
    "expression_input_tokens": 946,
    "expression_output_tokens": 93,
    "expression_latency_ms_mean": 1037.2,
    "expression_latency_ms_max": 1099.4,
    "validation_ms_mean": 0.113,
    "turn_latency_ms_mean": 1198.7,
    "turn_latency_ms_p50": 1116.6,
    "turn_latency_ms_max": 2482.5,
    "score_mean": 1.417,
    "score_distribution": {
      "0": 4,
      "2": 3,
      "3": 3,
      "1": 2
    },
    "score_zero_turns": [
      1,
      9,
      10,
      11
    ]
  },
  "combined": {
    "turns": 27,
    "provider_calls": 22,
    "interpretation_calls": 10,
    "narration_calls": 0,
    "expression_calls": 12,
    "retry_calls": 0,
    "input_tokens": 20652,
    "output_tokens": 2150,
    "calls_per_turn": 0.815,
    "expression_attempts": 12,
    "expression_adopted": 8,
    "expression_rejected": 4,
    "expression_fallbacks": 4,
    "expression_input_tokens": 2187,
    "expression_output_tokens": 193,
    "expression_latency_ms_mean": 1048.6,
    "expression_latency_ms_max": 1233.2,
    "validation_ms_mean": 0.103,
    "turn_latency_ms_mean": 1364.6,
    "turn_latency_ms_p50": 1125.7,
    "turn_latency_ms_max": 3674.1,
    "score_mean": 1.704,
    "score_distribution": {
      "2": 9,
      "3": 8,
      "1": 4,
      "0": 6
    },
    "score_zero_turns": [
      11,
      12,
      1,
      9,
      10,
      11
    ]
  }
}
```

Expression prompts in the repaired sample stay in the low hundreds of input tokens, with output under the 80-token cap. Interpretation remains the larger call. No narration purpose and no retry purpose appear. Deterministic recall turns made zero provider calls. Turns that delivered an authorized fact without a rewording request also made zero expression calls. Skipping generation on those turns is not counted as an efficiency improvement. Rejection and fallback counts are in the metrics above. Validation overhead is sub-millisecond on the recorded attempts.
