# PR-CY Live Verification Report

Mode: LIVE SOCIAL EFFICIENCY VERIFICATION.

Provider: OpenAI Responses API. Startup preflight was skipped; the first billable calls were gameplay generation calls.

Model requirement: gpt-4.1-mini-2025-04-14. Configured model knobs: `{"MODEL_NAME": "gpt-4.1-mini", "DEFAULT_MODEL_NAME": "gpt-4.1-mini", "HIGH_PRECISION_MODEL_NAME": "gpt-4.1-mini", "RETRY_ESCALATION_MODEL_NAME": "gpt-4.1-mini"}`.

Completed gameplay turns: 2.

Provider requests: 3.

Actual input tokens: 97946.

Actual output tokens: 1670.

Total tokens: 99616.

Reduced-context eligibility: selected on Turn 1 only. Turn 2 retained prior conversation in `recent_log`, but `provider_context_projection` was not selected and `active_interlocutor` was null in the provider payload.

Historical PR-CQ first preference request: 30877 input tokens, 30943 total tokens, 0 retries.

PR-CY first preference request: 27442 input tokens, 109 output tokens, 27551 total tokens.

Actual measured input reduction: 3435 tokens (11.12%).

Retry overhead: PR-CY retries 1 vs PR-CQ first-turn retries 0.

Turn 2 validation finding: both provider candidates were rejected as `unauthorized_resolution_decision_fact`. The retry text was a qualified, ordinary follow-up about rain discomfort and vigilance, yet was rejected as `unsupported_narrator_lead` and finalized as the evasive fallback `Guard Captain says, "I cannot answer that from what is settled here."`

Decision: E - VALIDATION FALSE POSITIVES.
