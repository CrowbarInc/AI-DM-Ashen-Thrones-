# PR-PLAY-30 offline transcript

All provider behavior is mocked. Production API routing, authority, resolution and publication are real. No live output below.

## Mocked opening

Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

## Turn 1

Player: I approach the tavern runner and ask what they're offering.

Published: Tavern Runner says, "I've got hot stew and rumors to share."

HTTP 200; gameplay_completed=True; stop=False; turn counter 1 → 2.

## Turn 2

Player: What sort of rumors have you heard?

Published: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

HTTP 200; gameplay_completed=True; stop=False; turn counter 2 → 3.

## Turn 3

Player: I head northwest of the crates to investigate the muddy footprints.

Published: You want to reach investigate the muddy footprints, but that is not an established destination from here. You stay where you are.

HTTP 200; gameplay_completed=False; stop=True; turn counter 3 → 3.

Turn 3: conversational_decline / destination_not_established. No interpretation request/response, action decomposition, exploration resolver, roll, or narration-provider result exists. The harness-configured unused mock must not be reported as actual interpretation. No further scenario action submitted. Full raw evidence: offline_run.json; semantic_stop.json.
