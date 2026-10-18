# 04 — Dialogue Authority Design

The record lives on `social["dialogue_authority"]` and is built by `game/dialogue_authority.py`. It does not write world facts. `canonical` is always false.

## A. Established facts

Canonical topic text and resolver results. When the topic sentence supports the requested information and is not hedged, posture is `established` and `answer_relation` is `sufficient`. The existing authored realization line is still the player-facing answer. Narration is not skipped for that delivery, so the first statement of a sufficient topic still uses the provider (`test_dialogue_still_uses_the_provider`).

## B. Player-visible facts

Facts already in the scene or already revealed. This cycle does not speak a scene sentence as if the NPC said it. `visible_supporting_sentence` can find a public sentence, and `build_dialogue_authority` accepts a scene, but the spoken determined line does not include that sentence. Putting the scene sentence into the fallback collided with validation and with the captured-failure test that forbids “north road” in a rejected stub.

## C. NPC knowledge

What this turn’s topic and request allow the speaker to use. A topic that does not support the request is not knowledge of the answer. Speech authority and the reply plan remain the resolver’s. The authority record does not raise them.

## D. NPC beliefs and opinions

`personal_state` and `opinion` questions, when the plan is not a genuine refusal, are posture `belief`. Improvisation is permitted. The resulting sentence is a commitment of kind `opinion`, not a world fact. An established factual topic is not stored as a commitment.

## E. Incidental characterization

Scope `incidental_speech` when improvisation is permitted. Manner, a short feeling, or a nonbinding preference may be said. The prompt tells the model that this speech is not canonical. Validation still rejects the consequential-claim patterns and internal authority wording.

## F. Proposed consequential facts

Promises, mysteries, relationships, rumors, surveillance gaps, and ownership gaps without a supporting topic are posture `unestablished`. Hidden requests are posture `withheld`. These are narration-determined. The NPC does not get to establish them by speaking. `dialogue_rejection_reasons` flags phrases such as a patrol schedule, a secret allegiance, a payment, a quest, a password disclosure, a marriage, or a new key.

## G. Hidden or restricted information

Kind `hidden` (password, secret, allegiance, Ash Cowl) is withheld even if the reply plan function itself stays `genuine_uncertainty` for compatibility with the existing subjective-follow-up tests. The spoken line is “I couldn’t answer that.” The plan function was not changed to reclassify “secretly” or “promise”; those tests require the older plan labels. The posture and the determined line carry the restriction.

## What an NPC says versus what the world establishes

The player-facing line is speech. `remember_dialogue_commitment` writes it under `conversational_context.dialogue_commitments` with `canonical: false`. It does not update NPC topics, clues, factions, or clocks. Clocks on an executed social ask still move through the existing passive tick. That tick is not this record.
