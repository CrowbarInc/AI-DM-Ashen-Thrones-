# PR-PLAY-24 scenario

Published opening (exact):

> Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

Authoritative same-scene NPC catalog:

- gate_guard: Gate Guard; location=frontier_gate
- gate_serjeant: Gate Serjeant; location=frontier_gate
- tavern_runner: Tavern Runner; location=frontier_gate

Selected: Tavern Runner (tavern_runner). Published explicitly; catalog kind=npc, authored location=frontier_gate, canonical addressability confirmed using existing is_actor_addressable_in_current_scene before submission. No NPC or access state was created for the test. Public state also supplies scene-addressable actors; full public snapshots and target rows are preserved.

Exact initial action:

> I approach the tavern runner and ask what they're offering.

Question asks only for already advertised offerings, not a purchase, price, quest or travel.

Closed follow-up decision tree, authored before live execution: after a successful nonpartial response, reject generic uncertainty; stew -> ingredients, rumor -> source, stated price -> inclusions, patrol -> last known location. No matching useful answer -> stop. Check production request budget before constructing any follow-up. No judge call.

Actual follow-up: none. First response was generic uncertainty and all three requests had been consumed. One reset/new_campaign plus one start_campaign; one ordinary action. The FiveTurnGameplay fixture/worker contract was reused for server compatibility; this controller never runs its five-turn action loop.
