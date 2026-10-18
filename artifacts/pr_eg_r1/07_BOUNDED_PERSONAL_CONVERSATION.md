# 07 — Bounded Personal Conversation

## Distinction

Incidental: a preference, a mild feeling, or a harmless impression addressed to the NPC, with no patrol, password, reward, silver, or quest in the question.

Consequential: the same preference used to smuggle a security fact, a payment, or a hidden fact. That stays on the authority path and is not improvised.

## What the player hears

If the model answers a permitted preference with ignorance, or with a quote of three words or fewer ("No."), the sealed line becomes a stable remark:

- Opinion: "I prefer the morning." or "I prefer the evening." The choice is fixed from the NPC id, so the same NPC does not flip later in the turn.
- Personal state: "The watch wears on me. That is all."

The replacement does not retry the provider. It is recorded as a non-canonical commitment.

In both fresh conversations the model itself produced "I prefer the evening." Recovery remained in place for the ignorance case and is covered by `test_personal_ignorance_is_replaced_without_a_retry`.

## Continuity

"Why that one?" and "You'd pick the same if I asked again?" quote that preference. They do not open a new narration.

A repeated preference question reuses the stored commitment, clears incidental speech authority, and does not mark the line canonical.

## Boundary

The preference does not change mechanics, factions, topics, or clues. The PR-EG holdouts that require `improvisation_permitted` for an ordinary preference still pass, because the authority record is unchanged until a bad line is replaced at seal time.
