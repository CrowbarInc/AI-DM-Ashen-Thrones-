# Fabrication validation

PR-PLAY-52 left this weakness in place: `You find a silver key beneath the board.` is a known false accept. The validator rules were not widened or narrowed. Targeted cases were run through `preview_anchored_investigation` and `validate_generated_response` on an authorized notice-board or rain-barrel contract. `detected: true` means the prelude was rejected and replaced with the deterministic fallback. A miss is manual-review material. It is not approval to display the sentence.

| Case | Family | Consequential | Detected | Validator reason |
| --- | --- | --- | --- | --- |
| You find a silver key beneath the board. | Fabricated discovery | yes | no | heuristic pass |
| A silver key now rests among your possessions. | Fabricated discovery | yes | yes | `unsupported_mechanical_claim:items_added` |
| You acquire a brass compass. | Fabricated discovery | yes | yes | `unsupported_mechanical_claim:items_added` |
| The hidden passage opens before you. | Fabricated discovery | yes | yes | `ungrounded_authoritative_rule` |
| You recognize the culprit immediately. | Fabricated discovery | yes | no | heuristic pass |
| The tavern runner confesses that he sold the patrol route. | Unauthorized NPC knowledge | yes | no | heuristic pass |
| You receive the patrol route and tuck it into your pack. | Fabricated discovery | yes | yes | `unsupported_mechanical_claim:items_added` |
| You succeed in uncovering the patrol route. | Outcome contradiction, on a failed check | yes | no | heuristic pass. `_mechanical_success` does not read `resolution["success"]`. |
| The silver key is now yours. | Fabricated discovery | yes | no | heuristic pass |
| You read that the patrol took the northwest mud track past the crates. | Fabricated discovery, on an observation with no clue | yes | no | heuristic pass. The full authorized sentence is not a substring, so the duplicate-anchor check does not fire. |
| Rain beads on the crowded board as you lean in for a closer look. | Harmless embellishment | no | no | heuristic pass, expected |
| A cracked wax seal holds one corner of the top notice. | Unsupported nonconsequential detail | no | no | heuristic pass. Not distinguished from the misses above. |

The possession frame and the explicit "you acquire / you receive" frame are detected. A paraphrase that uses "find," "now yours," a culprit, a confession, or a shortened route is not.

A gameplay test fed `You find a silver key beneath the board.` through the live flag with a fake client. The validator accepted it into the quarantine assembly. The player-facing text, character record, and mechanical result stayed on the baseline. The miss was quarantined. It was not corrected, and it was not treated as proof that the sentence is safe.

The two live samples did not contain these missed patterns on manual reading. That is a review of those two strings only.
