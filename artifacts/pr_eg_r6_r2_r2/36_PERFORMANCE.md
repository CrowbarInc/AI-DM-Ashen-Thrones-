# 36 — Performance

{
  "primary": {
    "turns": 150,
    "calls_per_turn": {
      "mean": 1.26,
      "median": 1.0,
      "p95": 2,
      "maximum": 2
    },
    "input_tokens_per_turn": {
      "mean": 3730.7933333333335,
      "median": 3463.5,
      "p95": 4016,
      "maximum": 30045
    },
    "output_tokens_per_turn": {
      "mean": 201.45333333333335,
      "median": 201.0,
      "p95": 280,
      "maximum": 333
    },
    "latency_ms": {
      "mean": 2538.4274240006926,
      "median": 2345.4469999996945,
      "p95": 4335.825200018007,
      "maximum": 5593.747400009306
    },
    "retry_calls": 0,
    "missing_usage_calls": 0,
    "calls_by_purpose": {
      "expression": 37,
      "semantic_plan": 149,
      "strict_social": 3
    },
    "strict_social_outliers": [
      {
        "conversation": "operation_4",
        "turn": 4,
        "latency_ms": 5593.747400009306,
        "calls": [
          {
            "purpose": "semantic_plan",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0ca8fc0b0d066c0a006ad3fcb45e2c87d2bc543cb4dd521366",
            "input_tokens": 2808,
            "output_tokens": 232,
            "total_tokens": 3040,
            "latency_ms": 2118.044,
            "usage_consistent": true
          },
          {
            "purpose": "strict_social",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0a6df48b37ac6332006ad3fcb7fdc887d29d794869d2aa6eec",
            "input_tokens": 27183,
            "output_tokens": 27,
            "total_tokens": 27210,
            "max_output_tokens": 600,
            "model_mismatch": false,
            "usage_consistent": true
          }
        ]
      },
      {
        "conversation": "operation_5",
        "turn": 4,
        "latency_ms": 5334.882600000128,
        "calls": [
          {
            "purpose": "semantic_plan",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_057e218de492ce04006ad3fcdadef087d2870a8c250a56bc30",
            "input_tokens": 2808,
            "output_tokens": 232,
            "total_tokens": 3040,
            "latency_ms": 2096.14,
            "usage_consistent": true
          },
          {
            "purpose": "strict_social",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_06ccd70c32fa1507006ad3fcdeb12087d29e776667d2e21dc8",
            "input_tokens": 27144,
            "output_tokens": 43,
            "total_tokens": 27187,
            "max_output_tokens": 600,
            "model_mismatch": false,
            "usage_consistent": true
          }
        ]
      },
      {
        "conversation": "operation_7",
        "turn": 4,
        "latency_ms": 5166.674100008095,
        "calls": [
          {
            "purpose": "semantic_plan",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0bb60ffbad6747ad006ad3fd22699887d2b419367749340045",
            "input_tokens": 2826,
            "output_tokens": 242,
            "total_tokens": 3068,
            "latency_ms": 2020.952,
            "usage_consistent": true
          },
          {
            "purpose": "strict_social",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0b3acf18b8c6e5fc006ad3fd25ea5487d2a9156f401cd852ab",
            "input_tokens": 27219,
            "output_tokens": 52,
            "total_tokens": 27271,
            "max_output_tokens": 600,
            "model_mismatch": false,
            "usage_consistent": true
          }
        ]
      }
    ]
  },
  "baseline": {
    "turns": 45,
    "calls_per_turn": {
      "mean": 1.4222222222222223,
      "median": 1,
      "p95": 2,
      "maximum": 2
    },
    "input_tokens_per_turn": {
      "mean": 3794.6222222222223,
      "median": 3337,
      "p95": 3664,
      "maximum": 33308
    },
    "output_tokens_per_turn": {
      "mean": 316.97777777777776,
      "median": 308,
      "p95": 576,
      "maximum": 617
    },
    "latency_ms": {
      "mean": 3883.7500244450184,
      "median": 3201.196899986826,
      "p95": 5707.354799989844,
      "maximum": 17538.373799994588
    },
    "retry_calls": 0,
    "missing_usage_calls": 0,
    "calls_by_purpose": {
      "expression": 18,
      "semantic_plan": 45,
      "strict_social": 1
    },
    "strict_social_outliers": [
      {
        "conversation": "continuity_2",
        "turn": 12,
        "latency_ms": 7100.786700000754,
        "calls": [
          {
            "purpose": "semantic_plan",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0c25c3dd118e745f006ad3f96ac67c87d2babeeff223b2725c",
            "input_tokens": 3506,
            "output_tokens": 286,
            "total_tokens": 3792,
            "latency_ms": 2669.774,
            "usage_consistent": true
          },
          {
            "purpose": "strict_social",
            "sent": true,
            "configured_model": "gpt-4.1-mini",
            "model": "gpt-4.1-mini-2025-04-14",
            "request_id": "resp_0e21d1a8d7ffd32f006ad3f9702f5887d2b9f204e543108c93",
            "input_tokens": 29802,
            "output_tokens": 41,
            "total_tokens": 29843,
            "max_output_tokens": 600,
            "model_mismatch": false,
            "usage_consistent": true
          }
        ]
      }
    ]
  },
  "predecessors": {
    "turns": 89,
    "calls_per_turn": {
      "mean": 1.3707865168539326,
      "median": 1,
      "p95": 2,
      "maximum": 2
    },
    "input_tokens_per_turn": {
      "mean": 2746.516853932584,
      "median": 2891,
      "p95": 3917,
      "maximum": 4045
    },
    "output_tokens_per_turn": {
      "mean": 186.1011235955056,
      "median": 173,
      "p95": 284,
      "maximum": 309
    },
    "latency_ms": {
      "mean": 2518.541417979005,
      "median": 2508.448500011582,
      "p95": 3839.4297000195365,
      "maximum": 5924.400499992771
    },
    "retry_calls": 0,
    "missing_usage_calls": 0,
    "calls_by_purpose": {
      "expression": 34,
      "semantic_plan": 88
    },
    "strict_social_outliers": []
  },
  "evaluation_calls_excluded": true,
  "all_observed_campaign_runs": {
    "baseline": {
      "turns": 45,
      "provider_calls": 64,
      "input_tokens": 170758,
      "output_tokens": 14264,
      "final_evidence": true
    },
    "final": {
      "turns": 150,
      "provider_calls": 189,
      "input_tokens": 559619,
      "output_tokens": 30218,
      "final_evidence": true
    },
    "pilot": {
      "turns": 5,
      "provider_calls": 7,
      "input_tokens": 10785,
      "output_tokens": 1714,
      "final_evidence": false
    },
    "pilot_3": {
      "turns": 5,
      "provider_calls": 6,
      "input_tokens": 10595,
      "output_tokens": 1799,
      "final_evidence": false
    },
    "pilot_5": {
      "turns": 5,
      "provider_calls": 6,
      "input_tokens": 10082,
      "output_tokens": 1543,
      "final_evidence": false
    },
    "pilot_7": {
      "turns": 5,
      "provider_calls": 7,
      "input_tokens": 12085,
      "output_tokens": 882,
      "final_evidence": false
    },
    "predecessors": {
      "turns": 89,
      "provider_calls": 122,
      "input_tokens": 244440,
      "output_tokens": 16563,
      "final_evidence": true
    },
    "pre_robustness_final": {
      "turns": 128,
      "provider_calls": 156,
      "input_tokens": 388162,
      "output_tokens": 25025,
      "final_evidence": false
    },
    "pre_robustness_predecessors": {
      "turns": 89,
      "provider_calls": 126,
      "input_tokens": 275555,
      "output_tokens": 16674,
      "final_evidence": false
    }
  },
  "cost_scope": "Final gameplay metrics exclude development/superseded/evaluation calls. Every recorded development and superseded run is separately totaled here; raw grading usage is preserved in independent_grades.jsonl and restart usage in restart/result.json. Abandoned stalled sandbox processes completed no turns."
}

Gameplay costs exclude pilots and grading. P95 latency target is 5,000 ms. Downstream strict_social calls are listed separately, not hidden in aggregate means.
