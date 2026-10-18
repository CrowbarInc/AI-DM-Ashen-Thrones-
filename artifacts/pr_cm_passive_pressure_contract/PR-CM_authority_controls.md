# PR-CM authority controls

No scheduler, probability, validator, or authority owner was added. Existing grounded-observation tests were not edited.

| Control | Where it is checked | Result |
| --- | --- | --- |
| Scene tension does not authorize new NPCs | Single-wait test and controls A–C. NPC ids stay `guard_captain` and `tavern_runner`. | Holds. |
| Visible guards do not automatically approach | Default NPCs stay `available` at `frontier_gate`. The obsolete approach lexicon is rejected by the assertions. | Holds. |
| Rumor text does not become quoted NPC dialogue | Tense visible facts include a rumor sentence. Player text has no quotation marks and is not social dialogue. | Holds. |
| Passive waiting does not invent clues | `discovered_clues` and `discovered_clue_ids` stay empty on the wait fixtures. | Holds. |
| Faction pressure events stay out of player narration unless projected | Event sentences are in `event_log` and `world_tick_events`. The sealed lamp line and the rain line do not contain them. The grounded stall restates a visible fact, not the faction sentence. | Holds. |
| Provider prose does not authorize state mutation | The stub line is kept when it is hard-valid. Faction pressure and the mobile move change only through `advance_world_tick`. | Holds. |
| Quiet waiting remains permissible | Control A keeps `The lamp stays steady over the desk.` when nothing is due. | Holds. |

Existing grounded-observation file, unchanged by PR-CM:

`tests/test_grounded_observation_non_invention.py`: 11 passed, 2 failed.

The two failures are the same follow-up sentences PR-CL already recorded:

- `test_frontier_gate_post_return_observe_does_not_invent_confrontation`
- `test_milestone_examine_does_not_keep_invented_inscription`

They fail on later clue wording after the anti-invention check. PR-CM did not touch that path.
