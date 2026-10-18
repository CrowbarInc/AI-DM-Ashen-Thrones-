# 06 — Conversational Correction

## Topic correction

"I meant the road, not how you feel."

The feeling pattern is recognized before the revision lock. The delivered road sentence is quoted. The player does not hear an undo refusal. In the fifteen-turn conversation this turn used no provider call and did not change clocks, factions, or topics.

"I was asking about the road's name, not the lantern." in the second conversation likewise quotes the north road, not the later "I couldn't tell you."

## Pending intention

"Instead, make that a question about the lamp" and "I meant the side gate" still match the revision wording. Continuity does not capture them. The existing pending-revision path remains, including the PR-EF-R4 holdouts for revise, cannot-undo, and ask-what-to-change.

A pending move is not executed when the player revises it.

## Executed action

"Undo the walk" is not a topic correction. Continuity returns none. World time, the scene, and the resolver result stay as they are.

## Withdrawal

Withdrawal wording is unchanged. It is not treated as a new NPC ask.

## Save and load

The delivered-exchange list is part of `conversational_context`. The holdout reloads one exchange and does not duplicate it when the same turn, player text, and delivered text are recorded again. Commitments are not duplicated when the same NPC, subject, and text are remembered again.
