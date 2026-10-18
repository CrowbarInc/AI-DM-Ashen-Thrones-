# PR-DY live turn results

Server: `http://127.0.0.1:8765/` with the disposable data directory. Submissions were made through the existing chat box. No stored interpretation was injected.

State before the first player message, from `state_before_live_turn.json`: turn 1, time_pressure 1, scene `frontier_gate`, after `start_campaign`. Opening narration was refused (`input-token ceiling`) and the player saw: "The action was resolved, but live narration was not requested because it would exceed the provider budget."

## Turn 1 — inspect

Player text: "I take a closer look at the notice board."

- Communication mode: AUTO
- Raw interpretation: `raw_live_responses.json` turn 2. Mode `IN_WORLD_ACTION`, status `INTERPRETED`, one component INSPECT `notice_board`
- Eligibility: `ELIGIBLE_FOR_VALIDATION`
- Bridge: investigate, target `notice_board`, `visible_surface_inspection` false
- Resolver: kind `discover_clue`, action `notice_board`
- Player-visible text: "You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates."
- Provider: interpretation sent, 700 / 187 / 887. Narration refused before send. Tokens for that refusal are unavailable.
- State after this action: turn advanced, clue `notice_patrol_route` later present as discovered. Final session is turn 3 because the next action also committed.

## Turn 2 — follow-up conversation

Player text: "I ask the captain what he thinks happened to them."

- Communication mode: AUTO
- Raw interpretation: ASK `guard_captain`. The summary says the player is asking about the missing patrol. The word "them" was not given an entity id by the player.
- Eligibility: `ELIGIBLE_FOR_VALIDATION`
- Bridge: question, target `guard_captain`
- Resolver: kind `question`, action `guard_captain`
- Player-visible text: Guard Captain mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."
- Provider: interpretation sent, 724 / 198 / 922. Narration purpose `strict_social` refused before send.
- The reply repeats the discovered clue. It does not add a new patrol fact.

## After both actions

Disposable `session.json`: `turn_counter` 3 (opening start counts as the first increment, then inspect, then ask), `clocks.time_pressure` 3, `active_scene_id` `frontier_gate`, `clue_knowledge.notice_patrol_route.state` `discovered` with the mud-track sentence.

Both gameplay turns completed the path from browser text through live interpretation, bridge, resolver, persistence, and on-screen text. Model narration was not sent. The visible sentences are resolver text.

These turns are automated verification. HUMAN PLAYTEST: NOT YET PERFORMED.
