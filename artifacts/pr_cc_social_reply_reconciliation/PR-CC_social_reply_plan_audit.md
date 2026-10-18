# PR-CC Social Reply Plan Audit

Baseline finding confirmed:
- The no-topic social branch previously called `_social_payload_with_reply_expectation(... topic_revealed=False ...)`.
- `_infer_reply_expectation` returned `reply_kind=refusal` for direct questions without a revealed topic.
- The result hint projected "No new information was revealed" and instructed refusal/uncertainty/inability.

Repair:
- `_bounded_social_reply_plan_for_missing_topic` now classifies missing-topic social turns into bounded plan kinds.
- `_apply_social_reply_plan` projects the chosen kind onto the existing social payload.
- No new authority owner was introduced; the plan is still social resolver output consumed by existing noncombat, CTIR, and dialogue plan paths.

Positive lane:
- Harmless subjective requests produce:
  - `reply_plan_kind=harmless_subjective_response_permitted`
  - `reply_kind=answer`
  - `incidental_subjective_allowed=true`
  - `npc_speech_authority=claim_only`
  - `objective_world_fact_authority=none`
  - `declared_claims_expected=false`
  - `durable_state_mutation_allowed=false`

Protected lanes:
- Restricted requests produce genuine refusal.
- Consequential requests produce unknown/consequential plan codes and require authored context for objective fact authority.
- Ordinary unknown factual requests no longer become refusal merely because a topic row is missing.
