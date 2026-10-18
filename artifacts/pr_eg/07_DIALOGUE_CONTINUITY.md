# 07 — Dialogue Continuity

## What is retained

`remember_dialogue_commitment` stores a row on `session["conversational_context"]["dialogue_commitments"]` when the posture is not `established`.

- Belief becomes kind `opinion`.
- Withheld becomes `refusal`.
- Partial becomes `partial_answer`.
- Anything else becomes `admitted_uncertainty`.

Each row has npc id, subject, text (capped at 180 characters), turn, `canonical: false`, and status `active`. The call site is `_complete_opening_turn_persistence_like_chat`, using `player_text_for_eval` and the sealed player-facing line.

## How long

At most 8 active rows per NPC and 24 active rows in the session. The oldest active row is marked `expired`. A new line for the same NPC and subject marks the older row `revised` when the text differs. Expired and revised rows stay in the list so growth is bounded by the active cap, not by deleting history inside a session. The list itself is not trimmed. A very long campaign can accumulate revised rows. That bound is not a full memory policy.

## Save and load

The rows live on the session object that `save_session` already writes. `test_commitment_survives_save_shape_and_is_not_canonical` saves and reloads the row and checks `canonical` is false. The disposable live campaign was deleted with its temporary directory, so save/load was not re-demonstrated on that campaign.

## Revision and contradiction

A follow-up whose subject phrase is “that” reuses the latest active commitment for that NPC when building the determined line. An exact subject match is preferred. The commitment is not compared against later world facts by a new contradiction engine. If a later determined line differs, the older row is revised rather than merged into the world.

## Canonical

Never. Established factual answers are not stored as commitments, because the topic already is the canonical answer.

## Live continuity

Turn 3, “What did you mean by that?”, did not repeat the north road. It spent a narration and a retry and said “I couldn’t tell you.” Turn 12, after the player had left the courtyard, asked which person was meant instead of returning to the watch. The commitment store did not carry those turns. The follow-up never stayed on the social record that would have read it.
