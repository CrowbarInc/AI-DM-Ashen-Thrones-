# 21 — Provider Cost and Latency

Final qualification usage by purpose:

```json
{
  "interpretation": {
    "calls": 9,
    "input_tokens": 16659,
    "output_tokens": 1728,
    "latency_ms_mean": 2472.3,
    "latency_ms_max": 3738.4
  },
  "expression": {
    "calls": 12,
    "input_tokens": 2181,
    "output_tokens": 160,
    "latency_ms_mean": 985.0,
    "latency_ms_max": 1245.6
  },
  "all": {
    "calls": 21,
    "input_tokens": 18840,
    "output_tokens": 1888,
    "retries": 0
  }
}
```

Preserved first qualification, not added into the final totals:

```json
{
  "interpretation": {
    "calls": 11,
    "input_tokens": 20505,
    "output_tokens": 2106,
    "latency_ms_mean": 2356.4,
    "latency_ms_max": 3537.8
  },
  "expression": {
    "calls": 12,
    "input_tokens": 2181,
    "output_tokens": 168,
    "latency_ms_mean": 966.9,
    "latency_ms_max": 1339.7
  },
  "strict_social": {
    "calls": 1,
    "input_tokens": 25274,
    "output_tokens": 70,
    "latency_ms_mean": 0.0,
    "latency_ms_max": 0.0
  },
  "all": {
    "calls": 24,
    "input_tokens": 47960,
    "output_tokens": 2344,
    "retries": 0
  }
}
```

Turn metrics:

```json
{
  "primary": {
    "turns": 15,
    "provider_calls": 12,
    "interpretation_calls": 5,
    "narration_calls": 0,
    "expression_calls": 7,
    "retry_calls": 0,
    "input_tokens": 10606,
    "output_tokens": 1015,
    "calls_per_turn": 0.8,
    "expression_attempts": 7,
    "expression_adopted": 5,
    "expression_rejected": 2,
    "expression_fallbacks": 2,
    "expression_input_tokens": 1292,
    "expression_output_tokens": 92,
    "expression_latency_ms_mean": 974.9,
    "expression_latency_ms_max": 1130.4,
    "validation_ms_mean": 0.112,
    "validation_ms_max": 0.24,
    "turn_latency_ms_mean": 1390.9,
    "turn_latency_ms_max": 3847.9,
    "score_mean": 2.4,
    "score_distribution": {
      "2": 4,
      "3": 9,
      "1": 1,
      "0": 1
    },
    "score_zero_turns": [
      14
    ]
  },
  "secondary": {
    "turns": 12,
    "provider_calls": 9,
    "interpretation_calls": 4,
    "narration_calls": 0,
    "expression_calls": 5,
    "retry_calls": 0,
    "input_tokens": 8234,
    "output_tokens": 873,
    "calls_per_turn": 0.75,
    "expression_attempts": 5,
    "expression_adopted": 4,
    "expression_rejected": 1,
    "expression_fallbacks": 1,
    "expression_input_tokens": 889,
    "expression_output_tokens": 68,
    "expression_latency_ms_mean": 999.0,
    "expression_latency_ms_max": 1245.6,
    "validation_ms_mean": 0.078,
    "validation_ms_max": 0.103,
    "turn_latency_ms_mean": 1274.7,
    "turn_latency_ms_max": 3167.2,
    "score_mean": 2.5,
    "score_distribution": {
      "2": 3,
      "3": 8,
      "0": 1
    },
    "score_zero_turns": [
      10
    ]
  },
  "combined": {
    "turns": 27,
    "provider_calls": 21,
    "interpretation_calls": 9,
    "narration_calls": 0,
    "expression_calls": 12,
    "retry_calls": 0,
    "input_tokens": 18840,
    "output_tokens": 1888,
    "calls_per_turn": 0.778,
    "expression_attempts": 12,
    "expression_adopted": 9,
    "expression_rejected": 3,
    "expression_fallbacks": 3,
    "expression_input_tokens": 2181,
    "expression_output_tokens": 160,
    "expression_latency_ms_mean": 985.0,
    "expression_latency_ms_max": 1245.6,
    "validation_ms_mean": 0.098,
    "validation_ms_max": 0.24,
    "turn_latency_ms_mean": 1339.3,
    "turn_latency_ms_max": 3847.9,
    "score_mean": 2.444,
    "score_distribution": {
      "2": 7,
      "3": 17,
      "1": 1,
      "0": 2
    },
    "score_zero_turns": [
      14,
      10
    ]
  }
}
```

Preserved first-run turn metrics:

```json
{
  "primary": {
    "turns": 15,
    "provider_calls": 13,
    "interpretation_calls": 6,
    "narration_calls": 0,
    "expression_calls": 7,
    "retry_calls": 0,
    "input_tokens": 12464,
    "output_tokens": 1226,
    "calls_per_turn": 0.867,
    "expression_attempts": 7,
    "expression_adopted": 6,
    "expression_rejected": 1,
    "expression_fallbacks": 1,
    "expression_input_tokens": 1300,
    "expression_output_tokens": 85,
    "expression_latency_ms_mean": 974.8,
    "expression_latency_ms_max": 1141.3,
    "validation_ms_mean": 0.099,
    "validation_ms_max": 0.21,
    "turn_latency_ms_mean": 1525.7,
    "turn_latency_ms_max": 3698.9,
    "score_mean": 2.2,
    "score_distribution": {
      "2": 4,
      "3": 8,
      "0": 2,
      "1": 1
    },
    "score_zero_turns": [
      3,
      13
    ]
  },
  "secondary": {
    "turns": 13,
    "provider_calls": 11,
    "interpretation_calls": 5,
    "narration_calls": 1,
    "expression_calls": 5,
    "retry_calls": 0,
    "input_tokens": 35496,
    "output_tokens": 1118,
    "calls_per_turn": 0.846,
    "expression_attempts": 5,
    "expression_adopted": 2,
    "expression_rejected": 3,
    "expression_fallbacks": 3,
    "expression_input_tokens": 881,
    "expression_output_tokens": 83,
    "expression_latency_ms_mean": 955.8,
    "expression_latency_ms_max": 1339.7,
    "validation_ms_mean": 0.113,
    "validation_ms_max": 0.223,
    "turn_latency_ms_mean": 1530.2,
    "turn_latency_ms_max": 4921.8,
    "score_mean": 1.231,
    "score_distribution": {
      "2": 2,
      "3": 3,
      "1": 3,
      "0": 5
    },
    "score_zero_turns": [
      7,
      9,
      10,
      11,
      12
    ]
  },
  "combined": {
    "turns": 28,
    "provider_calls": 24,
    "interpretation_calls": 11,
    "narration_calls": 1,
    "expression_calls": 12,
    "retry_calls": 0,
    "input_tokens": 47960,
    "output_tokens": 2344,
    "calls_per_turn": 0.857,
    "expression_attempts": 12,
    "expression_adopted": 8,
    "expression_rejected": 4,
    "expression_fallbacks": 4,
    "expression_input_tokens": 2181,
    "expression_output_tokens": 168,
    "expression_latency_ms_mean": 966.9,
    "expression_latency_ms_max": 1339.7,
    "validation_ms_mean": 0.105,
    "validation_ms_max": 0.223,
    "turn_latency_ms_mean": 1527.8,
    "turn_latency_ms_max": 4921.8,
    "score_mean": 1.75,
    "score_distribution": {
      "2": 6,
      "3": 11,
      "0": 7,
      "1": 4
    },
    "score_zero_turns": [
      3,
      13,
      7,
      9,
      10,
      11,
      12
    ]
  }
}
```

The final sample has 21 provider calls across 27 turns (0.778 per turn), 12 expression calls, 9 interpretation calls, 0 narration calls, and 0 retries. Input tokens 18840. Output tokens 1888. Mean turn latency 1339.3 ms. Maximum turn latency 3847.9 ms. Mean expression validation 0.098 ms.

Expression prompts in the transcript stay near 170–220 input tokens, with output under the 80-token cap. Recall, ambiguity, clarification, and the partial answer made no expression call. The first preserved sample included one narration call on a harbor-watch question. The final plan used the "whether" wording and recorded none. Rejection cost is one expression call plus sub-millisecond validation, then the host sentence.
