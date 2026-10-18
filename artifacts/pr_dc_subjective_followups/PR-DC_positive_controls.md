# PR-DC Positive Controls

LIVE CALLS: 0

Direct classification calls `_bounded_social_reply_plan_for_missing_topic` with action type `question`. Routed classification uses `play_turn` on a fresh frontier-gate session with the Guard Captain already bound, except where the sentence itself establishes the target.

Claim-only scope means `harmless_subjective_response_permitted`, `incidental_subjective_allowed` true, `npc_speech_authority` `claim_only`, `objective_world_fact_authority` `none`, `durable_state_mutation_allowed` false, and `declared_claims_expected` false.

| # | Prompt | Direct plan | Routed resolver | Routed interlocutor | Routed plan | Scope |
|---|---|---|---|---|---|---|
| 1 | Does the rain make it harder to keep watch? | claim-only | social | guard_captain | claim-only | personal difficulty of the watch |
| 2 | Does it get any easier after a while? | claim-only | social | guard_captain | claim-only | personal adaptation |
| 3 | Is standing in the cold uncomfortable? | claim-only | social | guard_captain | claim-only | discomfort |
| 4 | Do long shifts leave you tired? | claim-only | none | none | none | see exception |
| 5 | Do you enjoy working at the gate? | claim-only | social | guard_captain | claim-only | enjoyment of the work |
| 6 | Does the noise bother you? | claim-only | social | guard_captain | claim-only | bother |
| 7 | Is the work stressful? | claim-only | social | guard_captain | claim-only | stress |
| 8 | Why do you prefer somewhere dry? | claim-only | social | guard_captain | claim-only | existing `prefer` pattern |
| 9 | Does the baker find early mornings tiring? | genuine_uncertainty | social | npc id absent after the turn; speakers [guard_captain] | genuine_uncertainty | exception |
| 10 | Does the innkeeper enjoy busy evenings? | genuine_uncertainty | social | guard_captain | genuine_uncertainty | exception |

Cases 1, 2, 3, 5, 6, 7, and 8 keep one allowed speaker, `[guard_captain]`, and do not set objective fact authority.

## Exceptions

Case 4 matches the fatigue frame inside the reply-plan function. The live entry reason is `travel_or_scene_transition_intent` because the existing freeform parser treats "leave" as travel. The reply plan never runs. Travel detection was not changed.

Case 9 names the baker as the experiencer. The third-person pattern keeps `genuine_uncertainty` and `npc_speech_authority` `none`. On the routed turn the social payload's `npc_id` is absent afterward and the active interaction target ends null. That target outcome was already present in the baseline capture. Speaker grounding was not edited. The captain is not given claim-only authority over the baker's fatigue.

Case 10 names the innkeeper. The routed interlocutor stays `guard_captain` with one allowed speaker, and the plan stays `genuine_uncertainty`. The captain is not authorized to report the innkeeper's enjoyment.

"Baker, do you find early mornings tiring?" would match the second-person fatigue frame. The control sentence does not use that form.
