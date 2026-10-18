# 10 — Commitment Retention

## Delivered exchanges

- Key: `conversational_context.delivered_exchanges`
- Cap: 8 rows.
- When the cap is exceeded, the oldest GM row is dropped. An NPC statement is dropped only when every remaining row is NPC speech.
- The same turn, player text, and delivered text are not appended twice.
- A line that matches internal-authority wording is stored as GM, not as an NPC commitment.
- Established facts such as the north road are not copied into the commitment list. The exchange itself carries them so a follow-up can quote them.

This is why a courtyard description plus a gate crossing no longer erases the road sentence before the player asks about it from the street.

## Dialogue commitments

- Cap: 24 rows, 8 active rows per NPC. Unchanged output cap from PR-EG; the retained list is now trimmed to the same ceiling, dropping non-active rows first.
- An active row with the same NPC, subject, and text is reused instead of duplicated.
- `canonical` is always false.
- Established world facts are not written as commitments.
- A rejected provider candidate is never passed to `remember_dialogue_commitment`. Only the sealed player-facing line is.

## Save and load

The holdout saves and reloads one exchange. The list length stays 1. A password from a rejected narration fixture is not present in the saved context.
