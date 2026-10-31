# Generated Environment Dependency Ledger

Scope: gameplay-relevant environment introduced by narration, especially the northwest travel output on log entry 06, plus the board details that later actions used.

`frontier_gate` authored interactables: `notice_board` only.
`frontier_gate` authored exits: `Enter Cinderwatch` → `market_quarter`; `Follow the missing patrol rumor` → `old_milestone`.
`old_milestone` authored visible facts: a weathered stone milestone, churned mud prints, and a track that becomes unclear. Interactables: `milestone`, `prints`. No crates, sheds, lanterns, or banners.

| Element | Turn introduced | Authored in current scene? | Authored in destination scene? | Present in state before that turn? | Interactable? | Visible fact? | Clue? | Lead? | Generated only in prose? | Player later interacted? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Curfew-hour schedule | 01 | No. Board lists "curfew rules" / "curfews" only | No | No | No | No | No | No | Yes | Turn 02 asks for times and districts |
| Northwest mud track as a place the player has read | 01 | The phrase is inside undiscovered clue `notice_patrol_route`, not a visible fact | `old_milestone` summary names the northwest mud track | Clue text exists; not discovered | No | No | Yes, undiscovered until turn 02 | Lead row created on turn 02; `related_scene_ids` is only `frontier_gate` | Narrated before discovery | Used after turn 02 makes it authoritative |
| Crates as a landmark in the clue | 02 discovery; prose on 01 and 06 | Only inside the clue sentence | No | After turn 02, as clue text | No | No | Yes, as words in `notice_patrol_route` | Same lead | The clue is authored. "Passing them now" is not | Turn 07, "as I pass the crates" |
| Weather-beaten crates piled at the edge of the gate district | 06 | No | No | No | No | No | No | No | Yes | Turn 07 |
| Storage sheds | 06 | No | No | No | No | No | No | No | Yes | No |
| Flickering lanterns on crooked poles | 06 | No | No | No | No | No | No | No | Yes | No |
| Broken patrol banners on nails in crates | 06 | No | No | No | No | No | No until this turn's `discoverable_clues_add` writes a banner sentence into the overlay | No | Yes, then copied into overlay | Turn 08 |
| Arrival in the stretch where the soldiers were last seen | 06 | No | `old_milestone` is that geography and was not entered | No | No | Overlay `visible_facts_add` writes an arrival sentence on this same turn | The clue says the patrol was seen there. It does not say the player has arrived | No | Yes, and then adopted as overlay | Turns 07–09 presuppose it |
| Unseen watcher on the path | 06 `hidden_facts_add` | No | No | No | No | Hidden overlay only | No | No | Model scene_update. Not shown in player text | No |
| Banner sigils matching uniforms | 06 overlay, repeated on 08 and 09 | No | No | No | No | Overlay only | Overlay `discoverable_clues_add` only | No | Yes | Turn 08 studies "one of the broken banners" from the player-facing prose, not from this hidden string |
| Gate serjeant, roster board, runner, notice board, crowd | 00 | Yes | n/a | Yes | Board only | Yes | Board reveals the patrol clue | n/a | No | Turns 01–03 |

Chain the ledger is meant to show:

```text
turn 06 prose creates crates-being-passed, banners, sheds, lanterns, and arrival
        ↓
turn 07 player refers to passing the crates
        ↓
no crate interactable; adjudication does not inspect one
        ↓
anti-reset guard line is replaced by the patrol clue
        ↓
turn 08 player refers to a broken banner
        ↓
no banner target; custom action; empty speaker label says "The guard"
        ↓
turn 09 player continues "the path"
        ↓
still unparsed; same guard line; overlay keeps the arrival
```

Sheds and lanterns were generated and never referenced again. They show the same invention without a later dependency.

Do not promote those nouns into interactables. The player referred to them because the narration had just asserted them.
