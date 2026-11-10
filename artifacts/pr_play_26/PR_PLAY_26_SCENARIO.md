# PR-PLAY-26 scenario

Actual opening:

Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

Available same-scene NPC catalog: gate_guard, gate_serjeant, tavern_runner. Tavern Runner (tavern_runner) selected because explicitly published, addressable in frontier_gate and authoritative, with public offerings and existing patrol_rumor topic. No NPC/topic/state was fabricated.

Public fact: A tavern runner trades hot stew and rumors near the rain barrel.

Existing topic: [{"id": "patrol_rumor", "text": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "clue_id": "muddy_footprints_northwest"}]

Initial action: I approach the tavern runner and ask what they're offering.

Conditional follow-up: only after useful first answer, valid accessible target, no hard stop and at least two requests remaining. If rumors offered, intended question: What sort of rumors have you heard? Actual follow-up: NOT SUBMITTED because expression validation rejected. Two requests remained.
