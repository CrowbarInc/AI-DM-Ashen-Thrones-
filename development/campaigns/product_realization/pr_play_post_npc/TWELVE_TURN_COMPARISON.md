# Twelve-turn comparison

Same frontier-gate seed, same twelve utterances, provider calls disabled. Before: `artifacts/pr_play_post_npc/baseline_trace.json`. After: `artifacts/pr_play_post_npc/corrected_trace.json`, the solo rerun after restoring `data/scenes/frontier_gate.json`.

| Turn | Before | After | Usefulness |
|---|---|---|---|
| T01 | Disabled-narration sentence | Same | Still inadequate |
| T02 | Captain: "I couldn't tell you." | Same | Unchanged |
| T03 | Captain: patrol missing near the old milestone | Same | Meaningful, unchanged |
| T04 | `destination_not_established` | `local_object_not_a_destination` | Routing repaired. Grounded limitation. No touch outcome, no move, no clue |
| T05 | Captain sentence repeated | `discover_clue` for `notice_patrol_route` | Meaningful clue, plus the existing stock jab sentence |
| T06 | Captain sentence repeated | `unsupported_physical_manipulation` | Routing repaired. Authorized limitation. No inventory change |
| T07 | Mashed incidental about stew and a rain barrel | Disabled-narration sentence | Still inadequate. The sentence changed |
| T08 | "The action stands..." | Same | Still inadequate |
| T09 | `ungrounded_provider_target` | `already_searched` inspect | Meaningful recall of the disclosed clue |
| T10 | No nearby tavern | Same | Unchanged refusal |
| T11 | Arrive at Old Milestone | Same | Travel preserved |
| T12 | Unsupported retreat sentence | Same | Operational refusal preserved |

## Scores

| Metric | Before | After |
|---|---:|---:|
| Turns attempted | 12 | 12 |
| Correctly classified intents | unavailable as a full-set score | the four repaired turns are local contact, inspection, unsupported physical, and grounded recall |
| Correct gameplay owners selected | unavailable as a full-set score | T04 local decline, T05 discover clue, T06 physical decline, T09 already-searched inspect |
| Meaningful gameplay responses | unavailable as a full-set score | T03, T05, T09, and T11 are meaningful. T04 and T06 are authorized limitations. T01, T07, and T08 are not |
| Repeated-statement misroutes | 2 | 0 |
| Destination misclassifications | 1 | 0 |
| Ungrounded-target misclassifications | 1 | 0 |
| Operational refusals | 1 | 1 |
| Published fallbacks | 3 | 3 |
| Session-pointer advances | 7 recorded by the prior evaluation | 8 publication-text changes in the corrected trace. The baseline trace proxy counted 6, so this column is not the same method as the recorded 7 |
| Unauthorized state changes | 0 on the recorded failure turns | 0 on T04, T05, T06, and T09 |
| Live provider dispatches | 0 | 0 |

`call_gpt` was entered 4 times before and 4 times after, and returned before dispatch both times. The purpose list changed from `strict_social, primary_turn, strict_social, retry_escalation` to `strict_social, primary_turn, primary_turn, retry_escalation`.

## Critical distinction

T04 and T06 reach the correct owner and stop. They do not become successful physical play. T05 and T09 produce the authorized notice text. T05 is not a clean publication because the stock diegetic sentence is still appended.
