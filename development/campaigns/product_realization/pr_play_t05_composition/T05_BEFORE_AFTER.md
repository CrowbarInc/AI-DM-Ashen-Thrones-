# Original HTTP T05 before and after

Request: Read me the missing-patrol notice, not the tax lines.

Authorized notice_patrol_route clue: The missing patrol was last seen taking the northwest mud track past the crates.

| Stage | Before | After |
|---|---|---|
| Initial candidate | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. |
| Composed candidate | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates.  Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. |
| Pre-seal candidate | The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. |
| Accepted and published | The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. | You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates. |
| Stock renderer invoked | Yes | No |
| Hard validation / digest | Pass / verified | Pass / verified |
| Publication pointer | Exact accepted text above | Exact accepted text above |

Both runs use the same seed and all twelve original utterances. T05 stays in frontier_gate, character/inventory byte-equivalent in state comparison; it reveals the same selected clue, sets the same resolver state changes and advances the same turn. Full session/world/log changes include ordinary simulation and conversation/publication bookkeeping, not invented acquisition or travel. Momentum bookkeeping records new_information instead of synthetic consequence_or_opportunity, retaining the established cadence. The selected clue itself is the new information beat.

Before/after accepted text equals HTTP player-facing text and last_publication.visible; each accepted integrity digest independently verifies. t05_before.json and t05_after.json preserve full authority, scene/history, response, stages and state. t05_comparison.json is the compact comparison. No accepted response is changed after sealing.
