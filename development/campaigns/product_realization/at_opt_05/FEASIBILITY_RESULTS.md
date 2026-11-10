# Feasibility results

Provider calls: 0. OpenAI was not constructed. `call_gpt` was replaced with a raiser and was not entered. Serialization is `json.dumps(..., ensure_ascii=False)` of the two-message list. The admission estimate is `(blob_bytes // 3) + 64`. Hypothetical compact sizes are not provider-token savings. The script is `artifacts/at_opt_05/analyze_compact_eligibility.py`.

## F3 request sizes

| Build | Blob bytes | Estimate | Instructions | Compact selected |
| --- | ---: | ---: | ---: | --- |
| Attached auto, step-back | 80,403 | 26,865 | 78 | No |
| Attached forced compact | 70,263 | 23,485 | 18 | Forced, not selected |
| Attached profile `full` | 80,403 | 26,865 | 78 | No. The gate also blocks auto, so the two payloads match |
| Detached auto, step-back | 50,793 | 16,995 | 9 | Yes |
| Detached profile `full` | 60,827 | 20,339 | 67 | No |
| Detached auto versus detached full | −10,034 (16.50%) | −3,344 |  | Compact is already the auto path when the plan is gone |

Attached forced compact versus attached auto: −10,140 bytes (12.61%), estimate −3,380. Authority loss is in `SEMANTIC_COMPARISON.md`. Transition information is not lost by that swap: the false location-change object remains.

## Scenario matrix

Attached rows use the examine-turn plan. Detached rows are the no-resolution shape. Confidence is high for the measured gate, and lower for any claim about unstored historical prompts.

| Scenario | Transition flag | Compact | Selected path | Bytes | Authority note | Justified? | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Step back, attached | Required, same scene | No | Full, 78 lines | 80,403 | False location change | Gate is not a real transition | High |
| Step back, detached | Null | Yes | Compact, 9 lines | 50,793 | Plan and CTIR are gone, so this is a different request | Compact is already production for this shape | High |
| Look at the notice board, attached | Required, same scene | No | Full | 80,409 | Same stamp | Not a scene change | High |
| Look, detached | Null | Yes | Compact | 50,801 | Same as detached step-back | Inspection does not need the false flag | High |
| Push the nearest crate, attached | Required, same scene | No | Full | 80,390 | Same stamp | Physical action did not set the node | High |
| Push, detached | Null | Yes | Compact | 50,767 |  |  | High |
| Hello, Gate Guard, attached | Required, same scene | No | Full, 80 lines | 81,651 | Also follow-up pressure | Dialogue stays full even after a flag fix | High |
| Hello, detached | Null | No | Full, 69 lines | 62,043 | Follow-up pressure | Gate is doing separate work | High |
| What do I see?, attached | Required, same scene | No | Full | 84,834 | Also uncertainty | Question stays full after a flag fix | High |
| What do I see?, detached | Null | No | Full, 67 lines | 65,238 | Uncertainty |  | High |
| Patrol recall, attached | Required, same scene | No | Full, 79 lines | 82,890 | Only the advance flag | Would become compact if the flag alone were fixed | High on the gate, low on safety |
| Patrol recall, detached | Null | Yes | Compact, 11 lines | 53,443 | No plan | Already compact without a CTIR plan | Medium |
| Walk through the gate, attached | Required, same scene | No | Full | 80,454 | Utterance did not change the node | The sentence is not the signal | High |
| Walk through the gate, detached | Null | Yes | Compact, 9 lines | 50,860 | No resolution, so no travel node | A travel sentence alone does not protect full instructions | High |
| Wait and listen, attached | Required, same scene | No | Full, 80 lines | 80,710 | Ordinary continuation | Full list is not required by a scene change | High |
| Wait, detached | Null | Yes | Compact, 11 lines | 51,098 |  |  | High |

Failed or rejected narration was not replayed. Code says a matching stamp reuses the bundle, and a non-dict resolution detaches it. Post-turn `http_data/session.json` still contains the same-scene node. That file’s CTIR was not at the object this scan treated as the session root, so it is not proof of a particular failure path.

Post-transition continuation with a real scene change was not in these snapshots. The synthetic negative control covers that shape.

## Negative control

`resolved_transition` plus `target_scene_id` `old_milestone`, and `arrived_at_scene` plus that target, both set `transition_required` with different before and after scenes. Mode is `transition`. The compact gate stays closed because `must_advance_scene` copies the flag. Compact should remain disallowed there. `activate_scene_id` and a differing `scene_id` also stay required, with mode left at `continuation`. Those are still real scene signals. A same-scene id is not.

## Ordinary control

Detached “I wait and listen.” and detached “I look closely at the notice board.” select compact today. Attached “I wait and listen.” is ordinary gameplay carrying a false required location change. The full list is not justified by a scene change. It is also not safe to delete, because the visibility and first-mention lines are only on that list.

## Safety limit

The 10,140-byte figure is a forced compact payload on one reconstruction. It is not a measured provider saving. Selecting that payload on plan-backed turns would drop authority-critical instructions. The detached compact path is already live for no-resolution narration and is a different object, because the plan is absent.
