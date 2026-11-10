# Playability assessment

The session is not a natural conversation. Two turns gave the player something they could use. The rest stalled, repeated, or published a fallback.

## Intent comprehension

T03 and T11 were understood and carried through. T12 was understood as an unsupported retreat. T01 was labeled observation, and the authored facts were selected, and the spoken result ignored that selection. T02 reached the captain and answered a different question. T04, T05, T06, and T09 were captured by conversational orchestration and never reached the object the player named. T07 was unresolved. T08 was treated as a social question. T10 was treated as a tavern-location query.

## Narrative usefulness

Useful: T03. Partially useful: T02, T10, T11, T12. The other seven turns do not tell the player what they asked to know or what happened to the action. T01, T07, and T08 are deterministic fallbacks. Their wording is not evidence of live-model prose.

## Continuity

The scene id, the authored exit, and the survey and report flags stayed consistent. The captain's patrol sentence stayed available and was then reused against new intents. T09 could not recall the notice that T03 and the opening publication had already named. T07's mashed sentence was retained as a bounded incidental and appeared in later contracts.

## Player agency

T11 went where the player asked. T04 and T12 stayed put when the engine declined. T08 did not travel, and it also did not read the board the player was waiting on. No turn chose a later destination for the player. Several turns removed the player's ability to act on the notice by answering as if the captain were still the subject.

## NPC interaction

One greeting and one follow-up stayed with the Guard Captain and used host speech. The follow-up is grounded in the milestone rumor. The greeting is a refusal to tell. Later notice and recall lines were not a continued conversation with the captain; they were new actions that the conversation layer still answered.

## Adjudication

T10 refused a trade and created no item. T12 refused the retreat and did not move position. T06 did not invent a writing result. T04 declined a walk to a visible object as if it were travel. T11 applied one permitted location mutation. Hidden scene facts and the harness canaries stayed out of the player text.

## Responsiveness

Total local time was 1,598.794 ms across 12 turns. The slowest turn was T01 at 254.410 ms. The fastest was T09 at 33.926 ms. Four `call_gpt` entries returned inside the disabled-provider or retry-disabled path. T07 recorded one retry escape. T08 recorded one retry escalation. No provider latency, no browser paint, and no simulated-provider delay were measured. These times are not live-play latency.

## Overall

A player can get one grounded answer and can take the authored road to Old Milestone. A player cannot look around, read the notice, recall it, or try a reasonable extra action without hitting a repeat, a misrouted decline, or a fallback sentence. That is enough to call the current default continuation substantially unplayable as a conversation. It is not a claim about an unseen live narration.
