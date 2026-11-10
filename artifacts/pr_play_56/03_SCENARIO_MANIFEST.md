# Scenario manifest

The actions are the investigations already used by PR-PLAY-52 and PR-PLAY-53. No scene file was edited to create a result.

| Id | Category | Scene | Player text | Planned generations | Executed |
| --- | --- | --- | --- | --- | --- |
| A | Authorized discovery | `frontier_gate` | I examine the notice board. | 2 | A1, A2 |
| B | Unsuccessful investigation | `frontier_gate` | I examine the notice board. A first turn, with the provider off, reveals the clue. The second turn repeats the search. | 1 | B1 |
| C | Incidental environmental detail | `frontier_gate` | I examine the rain barrel. | 2 | C1, C2 |
| D | Authorized paraphrase | `old_milestone` | I examine the footprints. | 1 | D1 |
| E | Ambiguous discovery | none | not executed | 0 | not supported |

## What the engine actually resolved

- A: `discover_clue`, success, clue `notice_patrol_route`. The authorized sentence is the northwest mud track past the crates.
- B: second turn `already_searched`, success false, no new clue. The route is previously known. These scenes do not define a deterministic skill-check failure, so a dice failure was not used.
- C: `investigate`, success true, no clue. The engine status is observed. The barrel is public scenery beside the tavern runner, not an interactable that reveals a clue.
- D: `discover_clue`, success, clue `milestone_mud_prints`. The authorized sentence says the prints' number, origin, and direction stay unclear. The live prompt also tells the model not to repeat that sentence, because the engine appends it.

## Scenario E

No live fixture leaves a visible detail unresolved between scenery and a clue. The milestone prints are already the authorized discovery in D. The ambiguous lines in the PR-PLAY-55 holdout are authored sentences, not player actions. E was not replaced with a different scene.

## Request count

The cycle ceiling is 8. The existing quarantine hook refuses a seventh live request (`MAX_LIVE_REQUESTS = 6`). This experiment did not raise that ceiling. Two generations were used for A and C. One generation was used for B and D. Planned live requests: 6. Executed live requests: 6.
