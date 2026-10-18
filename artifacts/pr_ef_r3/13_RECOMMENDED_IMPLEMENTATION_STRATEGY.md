# 13 — Recommended Implementation Strategy

Chosen option: **B — contract consolidation.** Not started in this cycle.

## Boundaries

Produce one authorization record inside the existing resolution contract, after interpretation and lexical grounding, before `select_ordinary_resolver` and before `advance_world_tick`.

The record states addressee status, resolved id only when status is resolved, owner, purpose, allowed operation, execution eligibility, and mutation eligibility. Later stages read it. They do not invent a replacement addressee or a replacement owner.

Concrete rules:

- Explicit non-unique person reference plus more than one visible person: status ambiguous, mutation eligibility false, no resolver, no tick. The clarification names the visible people.
- One visible person and a non-unique phrase: clarify, and the clarification may name that person. Still no tick until the player confirms. This is stricter than a human might be. It matches the invariant that an unresolved consequential target does not execute. A clear proper name remains immediate. The fresh "I ask Sergeant Mara" probe stays eligible.
- Provider id versus unresolved lexical person: the lexical status wins. The id may be stored as a candidate. It is not the interlocutor.
- Recipient versus a single direct-address ASK: conflict, not a silent GM answer and not a silent execution.
- Blocked interpretation text is the reply unless the authorization record independently classifies a GM answer with selected evidence.
- Purpose EXPLANATION does not append the cause sentence unless the question asked for a cause.
- Correction reads a pending unexecuted ask, including a normal ask, and either rewrites it or asks what to revise. It does not describe a visible object as the fulfillment of "make that a question."
- Narration is not called when the record's only legal output is an authored sentence or the safe line.
- Incidental NPC color, if a later cycle allows it, is a non-persisted proposal on this record. It is not a topic and not a tick. This cycle does not build that lane. It only requires the record to be able to express it so the safe line is not the only unknown-answer behavior forever.

## Files and components

- `game/ordinary_semantic_ownership.py` — stop the bridge id from clearing an unresolved explicit addressee. This is the case A write.
- `game/conversational_orchestration.py` — owner conflicts, explanation suffix, correction against a real pending ask, and the EXECUTE path's rewrite of purpose to ACTION.
- `game/player_interpretation_bridge.py` — reject or mark ambiguous when the lexical nominal is non-unique, even if an id was supplied. Eligibility's unresolved list remains a second check, not the only check.
- `game/api.py` — do not increment the turn counter or call `advance_world_tick` unless mutation eligibility is true. Do not replace a blocked clarification with a second decision unless the record says to.
- `game/immutable_valid_response.py` — safe line uses only a speaker the record bound. Skip the provider when the line is already determined.
- `game/live_resolution.py` — leave resolver modes. Do not open unrestricted improvisation. A later change may attach a non-persisted proposal only when the record allows it.
- `game/live_chat_interpretation.py` — keep the one interpretation call. Do not add a routing component. Prompt text is not the repair. The instructions already say not to guess an id and not to turn GM talk into ASK. The model does both. The engine has to notice.

Resolvers in `game/social.py`, travel, exploration, combat, and `game/world.py` stay. Their inputs become the authorization record's allowed operation and resolved id.

## Migration

No parallel pipeline. The current contract object gains the status fields. Callers that read `interlocutor_id` alone must treat a missing id plus status ambiguous as "do not run," not as "pick the active interlocutor." Existing tests that bind Mara from an explicit ask should keep passing. Tests that only asserted a bridge id overwrite an unresolved person need to expect a clarification.

Ship the tick gate and the addressee rule together. Shipping the tick gate alone does not stop a wrong GM answer. Shipping the addressee rule without the tick gate leaves a clarification that still advances factions if some other path falls through.

## Acceptance

- "I ask one of them what happened," with two visible NPCs, clarifies and does not change turn counter, time pressure, or faction pressure. This holds when the provider names one of the ids and when it names none.
- "I ask Sergeant Mara what happened" still reaches the social resolver.
- "I ask the sergeant who owns the lantern" asks the sergeant or clarifies. It does not answer as the GM from empty evidence.
- "What does she mean by the road?" does not append the cause template. Quotation and GM explanation are distinguishable.
- "Instead, make that a question about the lamp," after an unexecuted ask, revises that ask or asks what to revise. It does not answer with the lantern's visible-fact sentence.
- An authored topic still answers without a narration call. A move that is already deterministic still uses zero provider calls.
- A knowledge-gap ask does not call strict-social and retry when the safe line is already determined.
- No hidden fact is disclosed. Invented owners, orders, and causes still fail validation.
- The existing eighteen-file family does not gain failing identities. Full-suite safety is not claimed until that family is run on the implementation.

## Non-goals

No production change in this cycle. No prompt rewrite as the fix. No new conversational handler module. No new NPC dialogue feature beyond what the record must be able to say. No world-generation mechanic. No campaign-start workflow. No UI work. No broad regression cleanup. No provider-optimization project beyond not calling narration for a determined line. No PR-EG.
