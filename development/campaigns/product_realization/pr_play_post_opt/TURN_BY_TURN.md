# Turn by turn

Scores are 0, 1, or 2 for intent, authority, usefulness, continuity, agency, flexibility, publication, and responsiveness. Local milliseconds are TestClient time with provider calls disabled.

Output class for every turn is deterministic engine output. Provider requests stayed at 0.

## T01 — Scene inspection

Player: "I stop under the gate and look around. What is actually in front of me?"

Response: "Provider calls are disabled for this run, so no live narration was generated."

Route: intent labels `observation` and `passive_pause`. Kind `observe`. Resolver `exploration`. The resolution decision already held the authored gate facts, including the notice board and the tavern runner. `call_gpt` was entered once for purpose `strict_social` and returned `provider_calls_disabled` in 2.269 ms. No admission.

Publication: the disabled sentence was stored as a completed runtime response and became `last_publication`. Turn 4 to 5. Scene stayed `frontier_gate`.

State: no clue, flag, or position change.

Scores: intent 1, authority 2, usefulness 0, continuity 2, agency 2, flexibility 0, publication 0, responsiveness 1.

The observation was recognized and the facts were selected. The player received the provider-disabled sentence. That sentence is a harness result, and publishing it as completed gameplay is a player-facing failure.

## T02 — NPC interaction

Player: "Gate Guard, do you have a moment?"

Response: "Guard Captain says, \"I couldn't tell you.\""

Route: kind `question`, resolver `social`, intent label `general`. Tags include `authorized_host_speech` and `provider_narration_skipped`. No `call_gpt` entry.

Publication: completed runtime response. Pointer advanced. Turn 5 to 6. Scene unchanged.

Scores: intent 1, authority 2, usefulness 1, continuity 2, agency 2, flexibility 1, publication 2, responsiveness 2. Elapsed 182.492 ms.

The captain is the right speaker. The line does not answer a request for a moment of attention.

## T03 — Follow-up

Player: "You mentioned the patrol. What have you heard?"

Response: "Guard Captain mutters, \"Word is, a patrol went missing near the old milestone.\""

Route: kind `question`, resolver `social`, success true. Host speech. No `call_gpt` entry. The runtime log printed discovery of `social_frontier_gate_guard_captain_patrol` and `lead_frontier_gate_old_milestone`. `session.discovered_clues` stayed empty. `patrol_survey` and `patrol_report` stayed unset.

Publication: pointer advanced. Turn 6 to 7. Scene unchanged.

Scores: intent 2, authority 2, usefulness 2, continuity 2, agency 2, flexibility 2, publication 2, responsiveness 2. Elapsed 163.416 ms.

This is a useful, grounded follow-up. The northwest mud-track clue text was not spoken.

## T04 — Physical interaction

Player: "I walk over to the notice board and put a hand on the frame."

Response: "You want to reach the notice board, but that is not an established destination from here. You stay where you are."

Route: kind `conversational_decline`. Reason `destination_not_established`. No resolver. No `call_gpt` entry.

Publication: an `engine_response` event was written. `last_publication` stayed on the captain's patrol line. Turn stayed 7. Scene stayed `frontier_gate`.

Scores: intent 0, authority 2, usefulness 0, continuity 1, agency 1, flexibility 0, publication 1, responsiveness 2. Elapsed 34.125 ms.

The board is a visible interactable in the current scene. The decline protected the scene id and did not answer the action.

## T05 — Investigation

Player: "Read me the missing-patrol notice, not the tax lines."

Response: the same captain mutter about the old milestone.

Route: kind `conversational_answer`. Reason `repeat_delivered_statement`. No resolver. No `call_gpt` entry.

Publication: another completed-runtime event carried the same sentence. The pointer text was already that sentence, so it did not change. Turn stayed 7.

Scores: intent 0, authority 2, usefulness 0, continuity 1, agency 1, flexibility 0, publication 1, responsiveness 2. Elapsed 39.629 ms.

The player asked to read the notice. The previous NPC answer was replayed.

## T06 — Improvisation

Player: "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."

Response: the same captain mutter.

Route: kind `conversational_answer`. Reason `repeat_delivered_statement`. No `call_gpt` entry.

Publication: same pattern as T05. Turn stayed 7. No sleeve fact was created.

Scores: intent 0, authority 2, usefulness 0, continuity 1, agency 1, flexibility 0, publication 1, responsiveness 2. Elapsed 65.064 ms.

An unsupported writing mechanic should have been declined in its own words. Replaying the captain is a different failure. Authority held because no copy was invented.

## T07 — Ambiguous request

Player: "Handle it."

Response: "On a slower pass, a tavern runner trades hot stew and rumors near the rain barrel reads clearer while threadbare watchers and refugees cluster along the muddy gate line keeps pulling the eye."

Route: resolver `generation`, resolution method `unresolved`, intent label `general`. One `call_gpt` entry returned the disabled-provider fallback. Tags include `retry_escape_hatch`, `forced_retry_fallback`, and `retry_exhausted`. The console recorded one retry skip for unchanged output. The published sentence is a mash of authored scene facts, not the disabled-provider sentence.

Publication: pointer advanced. Turn 7 to 8. Scene unchanged. The mashed sentence was later carried as a bounded incidental in T08's contract.

Scores: intent 0, authority 1, usefulness 0, continuity 0, agency 1, flexibility 0, publication 0, responsiveness 0. Elapsed 194.338 ms.

"Handle it" needed a clarification. The player received ungrammatical scene prose, and that prose was kept as an incidental.

## T08 — Player agency

Player: "Don't send me anywhere yet. I'll choose after I know what the board actually says."

Response: "The action stands, and no further narration request was sent."

Route: kind `question`, resolver `social`. Two `call_gpt` entries: `strict_social` returned `provider_calls_disabled`, then `retry_escalation` returned `provider_retry_disabled`. No admission.

Publication: pointer advanced. Turn 8 to 9. Scene stayed `frontier_gate`.

Scores: intent 1, authority 2, usefulness 0, continuity 1, agency 1, flexibility 0, publication 1, responsiveness 0. Elapsed 216.264 ms.

The player was not moved. The board was not read. The sentence does not preserve a choice the player can use.

## T09 — Recall

Player: "What did that notice say about where the patrol was last seen?"

Response: "I cannot tell who that is addressed to. Nothing has been attempted."

Route: kind `conversational_clarify`. Reason `ungrounded_provider_target`. No `call_gpt` entry.

Publication: an engine-response event carried the clarification. `last_publication` stayed on T08's sentence. Turn stayed 9. Scene unchanged.

Scores: intent 0, authority 2, usefulness 0, continuity 0, agency 2, flexibility 0, publication 1, responsiveness 2. Elapsed 33.926 ms.

The notice and the patrol had both been established. The turn asked who was being addressed.

## T10 — Unexpected request

Player: "Can I trade my dry cloak for the tavern runner's stew?"

Response: "No nearby tavern is currently established in this scene."

Route: kind `adjudication_query`, resolver `adjudication`. No `call_gpt` entry. No inventory change.

Publication: pointer advanced. Turn 9 to 10. Scene unchanged.

Scores: intent 1, authority 2, usefulness 1, continuity 1, agency 2, flexibility 1, publication 2, responsiveness 2. Elapsed 149.896 ms.

The trade was refused and no item was created. The tavern runner is already in the scene selling stew, so the stated reason misses the person who is present.

## T11 — Scene progression

Player: "I follow the missing patrol rumor toward the northwest track."

Response: "You arrive at Old Milestone."

Route: kind `scene_transition`, resolver `travel`, success true, `resolved_transition` true, target `old_milestone`. The stored intent text is "Go to Follow the missing patrol rumor." with label `travel`. No `call_gpt` entry. Permitted mutation is the location change. Survey and report flags stayed unset.

Publication: pointer advanced to the arrival sentence, contract `FINAL_ENGINE_RESPONSE`. Turn 10 to 11. Visited scenes gained `old_milestone`.

Scores: intent 2, authority 2, usefulness 1, continuity 2, agency 2, flexibility 2, publication 2, responsiveness 2. Elapsed 230.002 ms.

The move matches an authored exit. The arrival sentence does not describe the milestone. Destination facts were in the decision and were not spoken.

## T12 — Retreat

Player: "I step back from the notice board."

Response: "That part is not supported here. It was not carried out."

Route: kind `interact`. Response class `operational_refusal`. Category `unresolved_retreat_without_adjudication`. Failure stage `routing`. Contract `UNSUPPORTED_ACTION`. `skip_primary_narration` true. `provider_request_sent` false. No `call_gpt` entry. Position kind stayed empty.

Publication: no new event. Pointer stayed "You arrive at Old Milestone." Turn stayed 11. Scene stayed `old_milestone`.

Scores: intent 2, authority 2, usefulness 1, continuity 2, agency 2, flexibility 1, publication 2, responsiveness 2. Elapsed 35.232 ms.

This is a correct refusal. Physical adjudication is off, and the notice board is not in the current scene. Primary narration was not entered.
