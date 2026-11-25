# pr_play_purpose_tail_destination_binding_integrity

**A/PASS.**

The three purpose-tail requests now arrive at Old Milestone. Each commits one trail travel and no social action. A host failure to bind a destination no longer spends a turn.

## Before

From Market Quarter, all three were one complete MOVE. The route `leave_for_seek_the_fortress_trail` was selected. The destination phrase still contained the purpose tail, so `reconcile_scene_transition_destination` cleared the target. `resolved_transition` stayed false. The scene stayed `market_quarter`. Turn, tick, and pressure each increased by 1. The reply was "You try to move, but no reachable destination is established from here."

## Repair

The first incorrect decision is destination extraction, not MOVE classification. `destination_phrase_respecting_purpose_tail` drops a structural reason or participle only when the remainder is the place the catalog names. An authored name that contains those words is kept whole.

The first unauthorized commitment is `_commit_chat_action_time` after that cleared target. `host_destination_binding_failed` returns the existing unknown-destination decline before the commit. Skill checks, incompatible blocks, and a failed route/destination invariant still use the existing commit path.

## After

| Request | Scene | Spend | Social |
| --- | --- | --- | --- |
| looking for the guard | old_milestone | 1/1/1 | none |
| so I can persuade the guard | old_milestone | 1/1/1 | none |
| because I want to persuade the guard | old_milestone | 1/1/1 | none |

New acceptance **60/60**. Compound rerun **87/87**, with looking-for now an authorized arrival. Movement **109/109**. Disjunction script **52/53**, only the obsolete compound-travel assertion. Duplicate checks 66, 97, and 117. Unauthorized consequences **0**. Provider calls **0**. Expenditure **$0.00**.

Regression: Combined 455/17, Focused 470/1, Scoped 191/0. New failure identities **0**.

## Residuals that spend nothing

`to look for work` is still an inspection cue. `because I want to speak with someone` and `with the intention of speaking to someone` still ask which person is meant. Neither spends a turn.

Recommended next step: a fresh independent 20-turn live-play validation, under a separate spending ceiling. Do not start it from this milestone.
