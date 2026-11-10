# Semantic authority model

`SemanticAuthority` in `game/consequential_narration_validation.py` is a read-only snapshot. Building it does not write campaign state and does not authorize a discovery.

| Slot | Meaning | Source on an anchored investigation |
| --- | --- | --- |
| Observable scene facts | What the player can already perceive | Public visible facts |
| Authorized discoveries | Text the engine has revealed | Newly revealed clues and previously known clues |
| Authorized outcomes | Facts from completed resolution | Engine status sentences, success flag, mechanical fallback text |
| Restricted facts | Explicit withholdings supplied by the caller | Empty on the quarantined projection, which omits hidden fields |
| Narrative embellishment | Not stored | A sentence with no consequential claim |

Structured grants sit beside the prose: `items_added`, `items_removed`, `routes_unlocked`, `objectives_completed`, `conditions_applied`, `conditions_removed`, and authorized dialogue. An inventory sentence is supported only by `items_added`. Overlap with a clue sentence is not an item grant. That is why "You receive the patrol route and tuck it into your pack." stays unauthorized after the route clue is known.

Ordinary description does not have to appear in campaign state. "A cracked wax seal holds one corner of the top notice." has no acquisition, discovery, confession, or outcome frame, so it is embellishment.

The model restricts consequential claims. It does not require every sensory detail to be pre-authored.
