# PR-PLAY-28 integration transcript

Transport: deterministic SDK/interpretation/expression stubs, real FastAPI application and opening renderer. Live-provider requests: 0.

## Mocked opening

Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

## Turn 1

Player: I approach the tavern runner and ask what they're offering.

NPC: Tavern Runner says, "I've got hot stew and rumors to share."

Resolved NPC: tavern_runner
Selected topic: None
Public source: {'source_id': 'scene:frontier_gate:visible:2', 'source_text': 'A tavern runner trades hot stew and rumors near the rain barrel.', 'npc_id': 'tavern_runner', 'relation': 'own_offerings', 'items': 'hot stew and rumors', 'text': 'I offer hot stew and rumors.'}
Evaluation stop: False
Overlay integrity: True

## Turn 2

Player: What sort of rumors have you heard?

NPC: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

Resolved NPC: tavern_runner
Selected topic: patrol_rumor
Public source: None
Evaluation stop: False
Overlay integrity: True

Turn 1 uses the established public offering fact. Turn 2 selects npc:tavern_runner:patrol_rumor with permission=true; category metadata is taken from the maintained campaign fixture, without editing the authored text/clue. NPC identity remains tavern_runner.

The second turn adds exactly social_lead_revealed(muddy_footprints_northwest) and social_extracted_lead(lead_frontier_gate_old_trading_crossroads). The latter is authorized by the scene discoverable/minimum-lead rule, not the patrol topic alone.

All character, campaign, combat and condition snapshots remain equal. World state equals the existing normal tick plus these two events. The exact overlay matches a reconstruction from pre-turn sources. Full persisted snapshots, authored scene, eligibility decisions, normalized/interpreted actions, target binding, disclosure payload, dialogue authority, expression validation, event provenance and evaluator receipt are retained in integration_broad.json.

integration_explicit.json preserves the specific patrol-question control. integration_restricted.json denies the conditional source, publishes existing uncertainty, and creates no clue overlay delta. Requiring a substantive answer correctly marks the restricted scenario as a conversational dead end; that is an expected safe result, not a successful disclosure.
