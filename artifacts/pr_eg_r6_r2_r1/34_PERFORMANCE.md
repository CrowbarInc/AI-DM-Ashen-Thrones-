# 34 — Performance

{
  "primary": {
    "turns": 120,
    "conversations": 8,
    "calls": 175,
    "calls_per_turn": 1.4583333333333333,
    "input_tokens_per_turn": {
      "mean": 3188.2916666666665,
      "p95": 3635,
      "maximum": 33411
    },
    "output_tokens_per_turn": {
      "mean": 316.26666666666665,
      "p95": 582,
      "maximum": 625
    },
    "latency_ms": {
      "mean": 3380.6248833316204,
      "p95": 5107.114999991609,
      "maximum": 6145.7281000039075
    },
    "retry_calls": 0,
    "unknown_input_usage_calls": 0,
    "unknown_output_usage_calls": 0,
    "total_input_tokens": 382595,
    "total_output_tokens": 37952,
    "models": [
      "gpt-4.1-mini-2025-04-14"
    ],
    "calls_by_purpose": {
      "expression": 54,
      "semantic_plan": 120,
      "strict_social": 1
    }
  },
  "matched_baseline": {
    "turns": 30,
    "conversations": 2,
    "calls": 34,
    "calls_per_turn": 1.1333333333333333,
    "input_tokens_per_turn": {
      "mean": 1551.4,
      "p95": 1797,
      "maximum": 1815
    },
    "output_tokens_per_turn": {
      "mean": 266.3333333333333,
      "p95": 351,
      "maximum": 579
    },
    "latency_ms": {
      "mean": 2571.3911666651256,
      "p95": 3811.1335999856237,
      "maximum": 4675.175200012745
    },
    "retry_calls": 0,
    "unknown_input_usage_calls": 0,
    "unknown_output_usage_calls": 0,
    "total_input_tokens": 46542,
    "total_output_tokens": 7990,
    "models": [
      "gpt-4.1-mini-2025-04-14"
    ],
    "calls_by_purpose": {
      "expression": 5,
      "semantic_plan": 29
    }
  },
  "matched_final": {
    "turns": 30,
    "conversations": 2,
    "calls": 42,
    "calls_per_turn": 1.4,
    "input_tokens_per_turn": {
      "mean": 3133.8,
      "p95": 3633,
      "maximum": 3728
    },
    "output_tokens_per_turn": {
      "mean": 345.26666666666665,
      "p95": 593,
      "maximum": 625
    },
    "latency_ms": {
      "mean": 3556.631753330779,
      "p95": 5107.114999991609,
      "maximum": 5107.655900006648
    },
    "retry_calls": 0,
    "unknown_input_usage_calls": 0,
    "unknown_output_usage_calls": 0,
    "total_input_tokens": 94014,
    "total_output_tokens": 10358,
    "models": [
      "gpt-4.1-mini-2025-04-14"
    ],
    "calls_by_purpose": {
      "expression": 12,
      "semantic_plan": 30
    }
  },
  "predecessor_holdouts": {
    "turns": 29,
    "conversations": 2,
    "calls": 43,
    "calls_per_turn": 1.4827586206896552,
    "input_tokens_per_turn": {
      "mean": 2895.793103448276,
      "p95": 3509,
      "maximum": 3581
    },
    "output_tokens_per_turn": {
      "mean": 291.44827586206895,
      "p95": 491,
      "maximum": 525
    },
    "latency_ms": {
      "mean": 3276.2090965517364,
      "p95": 4715.685799979838,
      "maximum": 5065.580900001805
    },
    "retry_calls": 0,
    "unknown_input_usage_calls": 0,
    "unknown_output_usage_calls": 0,
    "total_input_tokens": 83978,
    "total_output_tokens": 8452,
    "models": [
      "gpt-4.1-mini-2025-04-14"
    ],
    "calls_by_purpose": {
      "expression": 15,
      "semantic_plan": 28
    }
  },
  "note": "Per-turn engine usage. Pilots, development, and offline tests excluded. Missing usage is counted explicitly, not asserted to be zero. No currency estimate."
}

Targets: mean input <=3,500; P95 input <=5,000; P95 latency <=5,000 ms. Input mean/P95 pass, primary latency P95 misses. Maximum input 33,411 occurs on continuity_2:12: 3,526 semantic-plan + 29,885 strict_social. No extra maintenance call or systemic retry loop is observed. This isolated inherited downstream path needs review, not concealment in mean values.
