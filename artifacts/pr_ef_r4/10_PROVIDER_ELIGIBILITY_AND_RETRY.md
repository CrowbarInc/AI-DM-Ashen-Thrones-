# 10 — Provider Eligibility and Retry Audit

## When narration is unnecessary

`social_narration_unnecessary` is true only when all of these hold:

- `social.target_resolved` is true
- `topic_revealed` is empty
- `incidental_subjective_allowed` is not true
- `npc_speech_authority` is `none`
- `reply_plan_kind` is `consequential_information_request`

Then `deterministic_provider_skip_line` returns the safe line with reason `determined_nonresolution`, `allow_regeneration` is false, and the retry loop logs `[RETRY SKIPPED: DETERMINED NONRESOLUTION]` before another provider call.

This is an outcome constraint. It is not a text pattern and it is not “every unknown question.”

## Deliberately not skipped

- `genuine_uncertainty`, including speech authority `none`. Live case B used this plan. The first narration failed `question_rule:first_sentence_not_explicit_answer`. The retry was sent. The accepted line was `Sergeant Mara shakes their head. "I don't know."` An alternative was acceptable, so skipping would have been wrong.
- `claim_only` / `harmless_subjective_response_permitted`. Characterization stays on the provider path.
- A revealed authored topic. The existing recall skip still returns that line and does not call strict-social. Live turn 3 and performance case A did this (interpretation only).
- `authoritative_answer_available`. Live turn 6 had this plan, speech authority `none`, and no revealed topic. Narration and one retry still ran (51,910 input tokens) and the emitted line was the safe refusal. The plan said an answer was available, so the skip did not apply. This is the remaining expensive shape.

## Retry discipline

Retries remain when the previous output failed a recoverable validation rule and the plan is not the closed consequential-information plan. Case B is that case: 1 interpretation, 1 strict-social, 1 retry.

Retries are not added for formatting success. Ambiguous clarification, GM description, clue delivery, conditional refusal, and the authored follow-up made no narration and no retry.

A separate forced malformed-output probe was not run. Case B is the live recoverable-failure measurement.

## Calls that stayed

Interpretation remains one call per interpreted turn. Deterministic move and the conditional made zero provider calls. No second interpreter was added.
