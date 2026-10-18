# 21 — Provider Cost and Latency

```json
{
  "turns": 24,
  "conversations": {
    "primary": 12,
    "secondary": 12
  },
  "exact_authorized": 24,
  "history_exact": 24,
  "fresh_rejected_expressions": 5,
  "safe_fallback_turns": [
    {
      "conversation": "secondary",
      "turn": 8
    }
  ],
  "reloads": [
    {
      "conversation": "primary",
      "turn": 6,
      "original_full_session_comparison": false,
      "delivered_context_exact": true,
      "saved_to_next_loaded_session_diff": [
        {
          "path": "/last_saved_at",
          "before": "2026-10-17T16:15:18.202858Z",
          "after": "2026-10-17T16:15:18.261703Z"
        }
      ]
    },
    {
      "conversation": "secondary",
      "turn": 6,
      "original_full_session_comparison": false,
      "delivered_context_exact": true,
      "saved_to_next_loaded_session_diff": [
        {
          "path": "/last_saved_at",
          "before": "2026-10-17T16:15:25.387658Z",
          "after": "2026-10-17T16:15:25.444914Z"
        }
      ]
    }
  ],
  "calls_by_purpose": {
    "expression": 9,
    "strict_social": 1,
    "retry_escalation": 1
  },
  "transmitted_calls": 11,
  "unsent_attempts": 0,
  "mean_turn_latency_ms": 994.9989541673858,
  "max_turn_latency_ms": 10702.392200008035,
  "seal_and_verify_mean_ms": 0.08884994999971241,
  "controlled_full_authorization_mean_ms": 9.16883699974278,
  "added_provider_calls_for_final_delivery": 0,
  "all_attempts": [
    {
      "path": "live_usage.jsonl",
      "sent": 9,
      "input_tokens": 59594,
      "output_tokens": 1293
    },
    {
      "path": "live_usage_attempt2.jsonl",
      "sent": 11,
      "input_tokens": 59919,
      "output_tokens": 1317
    },
    {
      "path": "live_usage_final.jsonl",
      "sent": 11,
      "input_tokens": 59915,
      "output_tokens": 1327
    }
  ]
}
```

Exact request IDs, returned models and token accounting are in live_usage_final.jsonl and metrics.json. Tokens are measured, not estimated dollar cost. Existing legacy unresolved-question retry still occurs on secondary turn 8; final authorization adds zero provider calls or retries. The microbenchmark measures seal+exact verification together and excludes provider validation; per-turn existing validation timing is retained in raw performance traces. No statistical latency claim or broad performance optimization.
