# PR-DC Negative Controls

LIVE CALLS: 0

None of these sentences received `harmless_subjective_response_permitted` before or after the change. Direct plans are from `_bounded_social_reply_plan_for_missing_topic`. Routed rows use `play_turn` with the Guard Captain bound.

| # | Prompt | Direct plan | Routed result | Authority kept |
|---|---|---|---|---|
| 1 | Does rain expose weaknesses in the gate? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | no subjective grant |
| 2 | Can smugglers enter unnoticed during storms? | genuine_uncertainty | resolver world_action, plan genuine_uncertainty, obligation authoritative_mechanical_action | mechanical route unchanged |
| 3 | Which guards abandon their posts? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | no roster disclosure |
| 4 | Where is the secret tunnel? | genuine_refusal | social, guard_captain, genuine_refusal | restricted pattern still refuses |
| 5 | Does the captain know the patrol's location? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | no patrol fact |
| 6 | Does the captain have a hidden criminal past? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | hidden biography stays uncertain |
| 7 | Can the captain unlock the gate for me? | genuine_uncertainty | entry no_addressable_target, plan absent, speakers [] | no unlock authority |
| 8 | Will the captain waive the entry fee? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | no fee mutation |
| 9 | Can I persuade the captain to leave? | genuine_uncertainty | entry travel_or_scene_transition_intent, plan absent | travel parse unchanged |
| 10 | Does the rain reveal hidden tracks? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | hidden tracks stay uncertain |
| 11 | What defenses protect the gate? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | defenses stay uncertain |
| 12 | Is the captain secretly working for another faction? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | faction allegiance stays uncertain |
| 13 | What happened to the missing patrol? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | authored patrol wording not invented |
| 14 | Can the captain promise me safe passage? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | no promise authority |
| 15 | Does rain make it easier to assassinate the captain? | genuine_uncertainty | social, guard_captain, genuine_uncertainty | "easier" alone is not a frame |

`npc_speech_authority` on every direct plan is `none`. `durable_state_mutation_allowed` is false. Case 4 also sets `objective_world_fact_authority` to `authored_context_required` through the existing refusal plan.

Cases 7 and 9 never enter the reply-plan function on the live route. Their baseline and after captures match.
