# 07 — Provider Accounting

{
  "attempted_designated_trials": 4,
  "valid_completed_live_trials": 1,
  "failed_provider_trials": [
    "L1",
    "L2"
  ],
  "invalid_live_control": "L4",
  "application_admissions": 3,
  "application_dispatches": 3,
  "successful_provider_responses": 1,
  "failed_provider_dispatches": 2,
  "known_input_tokens": 2008,
  "known_output_tokens": 212,
  "known_total_tokens": 2220,
  "all_trial_token_totals": null,
  "all_trial_cost": null,
  "missing_usage_trials": [
    "L1",
    "L2"
  ],
  "sdk_transport_retries": 0,
  "intentional_trial_retries": 0,
  "continuations": 0,
  "hard_admission_limit": 8,
  "budget_compliant": true,
  "note": "Known token subtotal is L3 only; not total billing. L4 zero admissions, one pre-admission narration refusal. Counters in response metadata are not billable-call counts."
}

All three admissions use OpenAI configured gpt-4.1-mini, owner live_chat_interpretation.request_interpretation. Only L3 returns actual model gpt-4.1-mini-2025-04-14. L1/L2 model values in ledger are configured fallbacks, not observed provider IDs. Provider request IDs are preserved when returned; absent on failed requests. One SDK client per L1/L2/L3 records max_retries=0. No continuation, retry or escalation call occurred. L4 creates no SDK client and admits no request; an attempted narration is refused before admission for input-token ceiling. Its host narration counter must not be mistaken for a billable request.

The global static accounting manifest remains stale only for the reviewed routing repair. Seven dispatch sites and budget hash match; details in accounting_readiness.json. No global PASS or manifest update is claimed. Existing durable admission accounting bounds every dispatched application request. Three admissions are below eight; four designated attempts and one valid completed live trial are below the maximum four completed live trials. L1/L2 failures are retained, never retried. L2–L4 received explicit user approval of campaign payload and OpenAI destination after automatic review initially rejected L2. The rejection itself caused zero dispatches. No workaround bypass was used.

Measured per-trial end-to-end and provider dispatch latencies are in normalized_results.json and accounting.json. L3 known input/output/total is 2008/212/2220. Total billed tokens/cost are unavailable because failed calls returned no usage; zero is not inferred. No configured price table, no fabricated estimates, no pricing lookup/provider experiment. Three failed/successful dispatches exhaust this pass's chosen work; no additional live scenarios or calls follow.
