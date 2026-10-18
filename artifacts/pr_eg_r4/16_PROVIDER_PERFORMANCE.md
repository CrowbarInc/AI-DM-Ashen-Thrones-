# 16 — Provider Performance

Engine-only per-turn latency excludes player/evaluator calls. Provider-call latency is separately preserved. Usage is provider-reported; null is unavailable, never zero. Costs are not priced because no price schedule was captured. Engine narration/retry purposes are taken from actual usage records.

```json
{
  "overall": {
    "turns": 69,
    "scored": 69,
    "quality_mean": 0.638,
    "quality_median": 1,
    "quality_distribution": {
      "1": 40,
      "0": 27,
      "2": 2
    },
    "quality_pass": 2,
    "playability_mean": 0.623,
    "playability_median": 1,
    "playability_distribution": {
      "1": 41,
      "0": 27,
      "2": 1
    },
    "playability_pass": 1,
    "engine_calls": 47,
    "purposes": {
      "interpretation": 28,
      "expression": 16,
      "strict_social": 1,
      "retry_escalation": 2
    },
    "input_tokens": 140305,
    "output_tokens": 8322,
    "latency_mean_ms": 1768.41,
    "latency_median_ms": 1515.25,
    "latency_p95_ms": 3305.97,
    "latency_max_ms": 14506.91
  },
  "breakdown": {
    "scene": {
      "A": {
        "turns": 60,
        "scored": 60,
        "quality_mean": 0.733,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 40,
          "0": 18,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.717,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 41,
          "0": 18,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 44,
        "purposes": {
          "interpretation": 28,
          "expression": 13,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 139634,
        "output_tokens": 8269,
        "latency_mean_ms": 1928.42,
        "latency_median_ms": 2185.755,
        "latency_p95_ms": 3305.97,
        "latency_max_ms": 14506.91
      },
      "B": {
        "turns": 9,
        "scored": 9,
        "quality_mean": 0,
        "quality_median": 0,
        "quality_distribution": {
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0,
        "playability_median": 0,
        "playability_distribution": {
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 3,
        "purposes": {
          "expression": 3
        },
        "input_tokens": 671,
        "output_tokens": 53,
        "latency_mean_ms": 701.7,
        "latency_median_ms": 144.28,
        "latency_p95_ms": 2076.99,
        "latency_max_ms": 2076.99
      }
    },
    "profile": {
      "casual": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.6,
        "quality_median": 1,
        "quality_distribution": {
          "0": 6,
          "1": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.6,
        "playability_median": 1,
        "playability_distribution": {
          "0": 6,
          "1": 9
        },
        "playability_pass": 0,
        "engine_calls": 10,
        "purposes": {
          "interpretation": 9,
          "expression": 1
        },
        "input_tokens": 18305,
        "output_tokens": 2150,
        "latency_mean_ms": 1643.21,
        "latency_median_ms": 2440.5,
        "latency_p95_ms": 2882.67,
        "latency_max_ms": 2882.67
      },
      "cooperative": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.867,
        "quality_median": 1,
        "quality_distribution": {
          "1": 13,
          "0": 2
        },
        "quality_pass": 0,
        "playability_mean": 0.867,
        "playability_median": 1,
        "playability_distribution": {
          "1": 13,
          "0": 2
        },
        "playability_pass": 0,
        "engine_calls": 10,
        "purposes": {
          "interpretation": 5,
          "expression": 5
        },
        "input_tokens": 10615,
        "output_tokens": 1259,
        "latency_mean_ms": 1741.16,
        "latency_median_ms": 2118.64,
        "latency_p95_ms": 3305.97,
        "latency_max_ms": 3305.97
      },
      "curious": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.867,
        "quality_median": 1,
        "quality_distribution": {
          "1": 9,
          "0": 4,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.8,
        "playability_median": 1,
        "playability_distribution": {
          "1": 10,
          "0": 4,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 11,
        "purposes": {
          "interpretation": 7,
          "expression": 4
        },
        "input_tokens": 14559,
        "output_tokens": 1685,
        "latency_mean_ms": 1572.77,
        "latency_median_ms": 1515.25,
        "latency_p95_ms": 3686.79,
        "latency_max_ms": 3686.79
      },
      "playful": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.6,
        "quality_median": 1,
        "quality_distribution": {
          "0": 6,
          "1": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.6,
        "playability_median": 1,
        "playability_distribution": {
          "0": 6,
          "1": 9
        },
        "playability_pass": 0,
        "engine_calls": 13,
        "purposes": {
          "interpretation": 7,
          "strict_social": 1,
          "retry_escalation": 2,
          "expression": 3
        },
        "input_tokens": 96155,
        "output_tokens": 3175,
        "latency_mean_ms": 2756.55,
        "latency_median_ms": 2872.07,
        "latency_p95_ms": 14506.91,
        "latency_max_ms": 14506.91
      },
      "skeptical": {
        "turns": 9,
        "scored": 9,
        "quality_mean": 0,
        "quality_median": 0,
        "quality_distribution": {
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0,
        "playability_median": 0,
        "playability_distribution": {
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 3,
        "purposes": {
          "expression": 3
        },
        "input_tokens": 671,
        "output_tokens": 53,
        "latency_mean_ms": 701.7,
        "latency_median_ms": 144.28,
        "latency_p95_ms": 2076.99,
        "latency_max_ms": 2076.99
      }
    },
    "category": {
      "clarification": {
        "turns": 42,
        "scored": 42,
        "quality_mean": 0.667,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 24,
          "0": 16,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.643,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 25,
          "0": 16,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 24,
        "purposes": {
          "interpretation": 17,
          "expression": 7
        },
        "input_tokens": 36016,
        "output_tokens": 4238,
        "latency_mean_ms": 1448.57,
        "latency_median_ms": 1414.7150000000001,
        "latency_p95_ms": 3101.61,
        "latency_max_ms": 3686.79
      },
      "followup": {
        "turns": 22,
        "scored": 22,
        "quality_mean": 0.591,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 13,
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.591,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 13,
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 19,
        "purposes": {
          "expression": 9,
          "interpretation": 7,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 97329,
        "output_tokens": 3050,
        "latency_mean_ms": 2258.26,
        "latency_median_ms": 1430.585,
        "latency_p95_ms": 3920.82,
        "latency_max_ms": 14506.91
      },
      "opening": {
        "turns": 4,
        "scored": 4,
        "quality_mean": 0.5,
        "quality_median": 0.5,
        "quality_distribution": {
          "1": 2,
          "0": 2
        },
        "quality_pass": 0,
        "playability_mean": 0.5,
        "playability_median": 0.5,
        "playability_distribution": {
          "1": 2,
          "0": 2
        },
        "playability_pass": 0,
        "engine_calls": 4,
        "purposes": {
          "interpretation": 4
        },
        "input_tokens": 6960,
        "output_tokens": 1034,
        "latency_mean_ms": 2827.36,
        "latency_median_ms": 2811.29,
        "latency_p95_ms": 3246.34,
        "latency_max_ms": 3246.34
      },
      "topic_change": {
        "turns": 1,
        "scored": 1,
        "quality_mean": 1,
        "quality_median": 1,
        "quality_distribution": {
          "1": 1
        },
        "quality_pass": 0,
        "playability_mean": 1,
        "playability_median": 1,
        "playability_distribution": {
          "1": 1
        },
        "playability_pass": 0,
        "engine_calls": 0,
        "purposes": {},
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_mean_ms": 189.32,
        "latency_median_ms": 189.32,
        "latency_p95_ms": 189.32,
        "latency_max_ms": 189.32
      }
    },
    "outcome": {
      "successful": {
        "turns": 2,
        "scored": 2,
        "quality_mean": 2,
        "quality_median": 2.0,
        "quality_distribution": {
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 1.5,
        "playability_median": 1.5,
        "playability_distribution": {
          "1": 1,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 3,
        "purposes": {
          "expression": 2,
          "interpretation": 1
        },
        "input_tokens": 2382,
        "output_tokens": 261,
        "latency_mean_ms": 2456.88,
        "latency_median_ms": 2456.88,
        "latency_p95_ms": 3686.79,
        "latency_max_ms": 3686.79
      },
      "failed": {
        "turns": 67,
        "scored": 67,
        "quality_mean": 0.597,
        "quality_median": 1,
        "quality_distribution": {
          "1": 40,
          "0": 27
        },
        "quality_pass": 0,
        "playability_mean": 0.597,
        "playability_median": 1,
        "playability_distribution": {
          "1": 40,
          "0": 27
        },
        "playability_pass": 0,
        "engine_calls": 44,
        "purposes": {
          "interpretation": 27,
          "expression": 14,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 137923,
        "output_tokens": 8061,
        "latency_mean_ms": 1747.86,
        "latency_median_ms": 1515.25,
        "latency_p95_ms": 3246.34,
        "latency_max_ms": 14506.91
      }
    }
  },
  "auxiliary": {
    "calls": 137,
    "input_tokens": 165713,
    "output_tokens": 23205
  },
  "auxiliary_models": [
    "gpt-4.1-2025-04-14",
    "gpt-4.1-mini-2025-04-14"
  ],
  "engine_models": [
    "gpt-4.1-mini-2025-04-14"
  ]
}
```

No systemic retry loop or turn-by-turn runaway prompt growth was observed. The outlier A_playful:11 entered strict_social with 25,817 input tokens, then retry_escalation with 28,430 and 26,831: 81,078 input tokens for an inadequate wrong-speaker response. Other interpretation prompts remain approximately 1.7–2.2k input tokens. One outlier is not evidence of a systemic loop. The frozen budgets were not exhausted; stopping was due to integrity.

`auxiliary_calls.jsonl` separates player generation and independent evaluation from gameplay costs. Failed sandbox connection and interrupted monitor attempt are excluded from target-corpus metrics and retained separately. Total campaign usage must include them; see `campaign_usage.json`.
