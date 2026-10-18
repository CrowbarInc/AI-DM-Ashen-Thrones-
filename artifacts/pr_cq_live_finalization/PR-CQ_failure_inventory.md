# PR-CQ Failure Inventory

No application repair was made. These are the live finalization misses that remain after the player-facing lines are accounted for.

## F1 — Patrol provider text still does not seal

Both turn 2 generations were `hard_invalid` with `unauthorized_resolution_decision_fact`.

Attempt 1 mixed the milestone with an order, the trading crossroads, a non-return, and negative evidence. Rejection of that draft is the gate doing the job it should do.

Attempt 2 still failed. "There's talk of a patrol missing near the old milestone." was coded `patrol_route_or_geography`. The same reply's "I don't know the details myself" was coded `ignorance_not_authorized_answer`. The selected authored sentence was not what the model wrote, and the paraphrase was not accepted.

The player received the fact only because `authored_answer_projection` ran after the retry. Provenance on that seal is labeled `safe_nonresolution`.

## F2 — The patrol turn still pays a full retry

The retry was a response to a genuinely invalid first draft, not a rejection of an already valid preference. It did not produce a sealable provider answer. It cost 43,043 tokens, 39.6% of this probe, and used the last request in the cap of 4.

Turn 1 did not have this failure. The preference sealed on attempt 1.

## F3 — Lead metadata splits the projected quote

`recent_contextual_leads` for the patrol line stores position `near the old milestone."` with the closing quote attached. Clue text and player text keep the authored sentence. This did not add a place.

## Not failures

- Turn 1 did not fall back to banner narration.
- The captain's shrug and gaze did not force a preference retry.
- Crossroads, non-return, negative evidence, and the ignorance denial are absent from the final line and from discovered clue text.
- The session did not record the patrol reveal while telling the player the captain cannot answer.
- Hidden facts, visible facts, NPC topic strings, and the character sheet were not rewritten.
- Production saves were not written. The worktree was not reset.
