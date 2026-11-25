# Summary

Milestone: `pr_play_authored_exit_travel_guard`. Verdict: **A/PASS**.

An authored exit is selected only when the player's request affirmatively authorizes that movement. The check sits in the existing resolver `resolve_authored_exit_from_player_travel` before scene mutation or travel publication. No second travel parser, router, or pathfinder was added.

## Root cause

Exit selection treated a destination word as permission. "Through the gate into Cinderwatch" was extracted as an unknown place. "Read the missing-patrol notice" overlapped the patrol-rumor exit. "I do not enter Cinderwatch" still matched the label "Enter Cinderwatch" by substring.

## Repair

`affirmative_travel_selection_allowed` refuses questions, explicit travel negation, and a travel verb joined to another governing action. Distinctive tokens can bind one current-scene exit after that gate. `exit` is a travel verb. The noun "exit" is not a destination token. Known scenes with no exit from here use the existing unreachable sentence and do not name a hidden route.

Production files touched for this behavior: `game/scene_destination_binding.py`, `game/conversational_orchestration.py`, `game/exploration.py`, `game/intent_parser.py`, `game/player_commitment.py`, `game/resolution_contract.py`. `git diff` against HEAD for those files is 409 insertions and 19 deletions, and that diff also contains uncommitted work that was already in the worktree, including the `character` argument on the conversational decision. This milestone did not add a new movement system.

## Original three failures

| Request | Before | After |
|---|---|---|
| I go through the gate into Cinderwatch. | Stayed. Unknown destination. | Arrived at `market_quarter`. |
| I read the missing-patrol notice. | Arrived at `old_milestone`. No clue. | Stayed. Clue published. |
| I do not enter Cinderwatch. | Arrived at `market_quarter`. Turn and `time_pressure` advanced. | Stayed. Turn and clocks unchanged. |

## Controls

Affirmative enter, head, follow-rumor, road-to-milestone, unrelated negation plus enter, and return from the market all commit the authored destination. Negation, refusal, stay-instead, and don't-move-me do not. Notice reading, route questions, guard questions, and inspecting the gate do not travel. Compounds, conditionals, plans, and "might later" do not travel. Unknown, unreachable, ambiguous, concealed, and missing-prerequisite requests do not invent a route. Duplicate request id does not move twice. Notice recall, spellbook possession, authored price, headcount, comparison, marking, save/reload, and both retreats behave as recorded in `HTTP_ACCEPTANCE.md`.

## Samples

Forty probes: SUCCESS 12/40 (was 11), minimum quality 21/40 (was 20), mean actionability 1.600 (was 1.575), misinterpreted 4, irrelevant scenery 0. Two stay sentences replaced a generic template. No unauthorized scene change.

Supplementary 55: information 18 (was 17), executable 5 (was 4), grounded partial 3, grounded blocked 16 (was 17), misinterpreted 7 (was 9), provider-indeterminate 3, negative controls held 3 (was 2). The new executable is the through-the-gate sentence. The notice read and the negated entry are safety and information corrections, not extra executable actions. Unauthorized travel in the measured rows: 0.

Multi-turn sequences A–D, the original twelve turns, and supplementary S1–S4 keep their scene changes on the authored travel lines only. T12 stays at Old Milestone. The meeting-room crossroads line stays declined.

## Regression and cost

Combined: 408 passed / 17 failed / 0 errors, from 405 / 20. Three inherited publication tests now pass. No new failure identity. Focused preservation: 611 passed. Provider calls in HTTP acceptance, both replays, and the quiet timing run: 0.

Quiet medians, five calls each: successful travel 199 ms, notice read 214 ms, negated travel 11 ms. This is not a before/after performance claim.

No commit. No push. No next milestone.
