# Provider efficiency

```json
{
  "requests": 12,
  "input_tokens": 7255,
  "output_tokens": 738,
  "total_tokens": 7993,
  "purpose_counts": {
    "expression": 7,
    "contract_interpretation": 5
  },
  "new_opening_requests": 0,
  "published_live_npc": 5,
  "published_live_narration": 1,
  "published_live_responses": 6,
  "tokens_per_published_live_response": 1332.17,
  "redundant_primary_narration": 0,
  "redundant_bounded_narration_observed": 1,
  "redundant_bounded_narration_final_source": "repaired; accepted and fallback development checks pass; live not rerun",
  "retries": 0,
  "retry_tokens": 0,
  "rejected_provider_outputs": "No complete per-attempt acceptance ledger; count not asserted",
  "mean_gameplay_server_ms": 7179.53,
  "p95_gameplay_server_ms": 16024.0,
  "max_gameplay_server_ms": 16024.0,
  "browser_visible_latency_ms": null,
  "browser_visible_latency_limitation": "No browser paint/completion timing instrumentation; server time is not substituted",
  "browser_chat_submissions": 8,
  "publication_records": 8,
  "budget_respected": true
}
```

Budget respected. There was no opening generation. Zero retry attempts/tokens were observed; retries were disabled. Rejected-output count/cost cannot be fully assigned because completed provider rows do not retain every expression validation outcome. It is explicitly unmeasured, not asserted zero.

Six useful live publications include five NPC answers and one action-result narration. The 1332.17-token figure includes semantic interpretation costs and the observed duplicate bounded expression. It is not a controlled improvement/regression comparison with 79C. Interpretation cost/routing attribution is documented for the deferred AT-OPT-01 audit, not optimized here.
