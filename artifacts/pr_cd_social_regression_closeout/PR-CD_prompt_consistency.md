# PR-CD Prompt Consistency

Scope: current PR-CC deterministic projection and provider instruction surface. No live provider calls were made.

## Representative current guidance

`game/prompt_context.py` projects this guidance when `dialogue_social_plan` is present:

```text
DIALOGUE SOCIAL PLAN (HARD RULE): When top-level dialogue_social_plan is present, it is the ONLY dialogue/social planning source for this turn.
```

```text
INCIDENTAL SOCIAL REPLY AUTHORITY: If dialogue_social_plan.reply_plan_kind is harmless_subjective_response_permitted, lack of an authored preference is not a refusal requirement.
```

The same instruction permits bounded personal opinion, preference, recommendation, reaction, or an admission that the NPC has not tried/seen it, while preserving objective truth, durable trait/state, quest evidence, and declared-claim boundaries.

It also states that if the plan kind is `consequential_information_request`, `genuine_refusal`, or `genuine_uncertainty`, the model should preserve that limit and not convert it into helpful invention, and that prior evasive dialogue in `recent_log` does not by itself force a new refusal when the current plan permits a subjective reply.

## Agreement between plan and guidance

For the reconstructed PR-CA turns:

- T2 and T3 have `reply_plan_kind=harmless_subjective_response_permitted`, `reply_kind=answer`, `npc_speech_authority=claim_only`, `objective_world_fact_authority=none`, `declared_claims_expected=false`, and `durable_state_mutation_allowed=false`.
- Provider guidance agrees with those fields: harmless subjective speech is permitted as NPC speech only.
- T1 and T4 have `reply_plan_kind=genuine_uncertainty`, so provider guidance preserves uncertainty rather than inventing a preference or treating the player's premise as fact.

## Required checks

- Social reply plan and generation guidance agree: pass for T2/T3; T1 is a projection limitation because the plan does not enter the harmless-subjective lane.
- Harmless subjective permission is visible: pass when `reply_plan_kind=harmless_subjective_response_permitted`.
- Generic missing-topic refusal instructions are absent from the PR-CC lane: pass; current missing-topic guidance no longer says missing authored topic alone requires refusal.
- Objective world restrictions remain intact: pass; subjective permission carries `objective_world_fact_authority=none`.
- Genuine refusal instructions remain intact: pass; `genuine_refusal` remains a distinct plan kind and restricted/password controls pass.
- Previous evasions do not become mandatory behavior: pass in prompt text and T2/T3 projection.
- Structured declaration machinery does not leak into narration-only generation for this lane: pass in projection; harmless subjective turns expect no declared claims.

## Limitation

The prompt surface is consistent with T2/T3 PR-CA repair, but the T1 classifier misses a preference phrasing ("which loaf do you usually keep for yourself?"). That is not a contradiction in provider guidance; it is a deterministic planning coverage gap.
