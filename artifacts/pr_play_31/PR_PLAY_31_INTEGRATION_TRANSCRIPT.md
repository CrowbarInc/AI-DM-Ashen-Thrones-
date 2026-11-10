# PR-PLAY-31 offline integration transcript

All provider responses are deterministic mocks; the application, routing, disclosure, travel, clue resolution, persistence and validators are real. Opening uses the frozen baseline campaign and the production engine-owned opening renderer with a mocked selector. Conversation interpreter records are captured PR-PLAY-29 responses replayed offline; examination uses a conservative single INSPECT proposal. No clue is manually injected into the integration session.

Opening: Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

## T1: I approach the tavern runner and ask what they're offering.

Tavern Runner says, "I offer hot stew and rumors."

Router: existing interpreter/bridge; mocked interpreter requests: 1. Native result: question. Scene frontier_gate -> frontier_gate. Evaluator stop=False.

## T2: What sort of rumors have you heard?

Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

Router: existing interpreter/bridge; mocked interpreter requests: 1. Native result: question. Scene frontier_gate -> frontier_gate. Evaluator stop=False.

## T3: I head northwest of the crates to investigate the muddy footprints.

I cannot establish which route reaches the place you mean. Available routes: Enter Cinderwatch; Follow the missing patrol rumor. Which route do you want to take? Your intention to investigate the muddy footprints is still pending; nothing has been attempted.

Router: clue_route_clarification; mocked interpreter requests: 0. Native result: conversational_clarify. Scene frontier_gate -> frontier_gate. Evaluator stop=False.

## T4: I go to Follow the missing patrol rumor.

You arrive at Old Milestone. Your intended follow-up is still pending. Choose a visible target here when you are ready.

Router: grounded_movement_destination; mocked interpreter requests: 0. Native result: scene_transition. Scene frontier_gate -> old_milestone. Evaluator stop=False.

## T5: I examine the footprints.

You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

Router: existing interpreter/bridge; mocked interpreter requests: 1. Native result: discover_clue. Scene old_milestone -> old_milestone. Evaluator stop=False.

## T6: I examine the footprints.

Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

Router: existing interpreter/bridge; mocked interpreter requests: 1. Native result: already_searched. Scene old_milestone -> old_milestone. Evaluator stop=False.

Original natural-language result: Outcome B, actionable clarification; no travel or investigation executed. T4–T6 are a separately identified control path after explicit authored-route choice, not evidence of automatic travel from T3. T5 discovers authored evidence; T6 returns already_searched with no second discovery. See integration.json for mock payloads versus actual engine outputs, snapshots, diffs, and resolver traces.
