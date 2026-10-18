# 05 — Continuous Ten-Turn Transcript

Final-code HTTP replay of captured live interpretations. One campaign; no reset between turns; save/load at turn six. External calls in replay: zero. Full decisions, state keys, resolutions and context are in the corresponding JSON.

## Turn 1

Player: Could you describe our surroundings?

GM: You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate. A soot-streaked lantern burns beside the courtyard gate. The side gate is barred from the other side. Sergeant Mara looks concerned as she watches the road.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 0 -> 0. World changed: False. HTTP: 200. Replay latency: 26.133 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 2

Player: What do I already know about that lantern?

GM: From what has already been established: You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate. A soot-streaked lantern burns beside the courtyard gate. The side gate is barred from the other side. Sergeant Mara looks concerned as she watches the road.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 0 -> 0. World changed: False. HTTP: 200. Replay latency: 9.218 ms. Provider calls: 0.

Classification: PASS WITH RESPONSE LIMITATION (broad restatement of established text).

## Turn 3

Player: Does Sergeant Mara appear concerned?

GM: Sergeant Mara looks concerned as she watches the road.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 0 -> 0. World changed: False. HTTP: 200. Replay latency: 10.626 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 4

Player: I ask Sergeant Mara where the street leads.

GM: Sergeant Mara turns toward you, her gaze steady yet shadowed with concern. "The street just beyond the gate is the north road," she says quietly. "It's the main passage leading northward from this waystation." Her voice carries the weight of watchfulness as she keeps an eye on the soot-streaked lantern flickering beside the courtyard gate.

Decision: resolver / question. Resolution: question. Turn counter: 0 -> 1. World changed: True. HTTP: 200. Replay latency: 157.924 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 5

Player: Which road do you mean?

GM: Sergeant Mara says, "Word is, the street beyond the gate is the north road."

Decision: resolver / question. Resolution: question. Turn counter: 1 -> 2. World changed: True. HTTP: 200. Replay latency: 134.74 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 6

Player: GM, can you clarify what Mara just said?

GM: The street beyond the gate is the north road.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 2 -> 2. World changed: False. HTTP: 200. Replay latency: 53.315 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 7

Player: I inspect the courtyard lantern.

GM: You inspect courtyard lantern. A small maker's mark is stamped beneath the lantern.

Decision: resolver / discover_clue. Resolution: discover_clue. Turn counter: 2 -> 3. World changed: True. HTTP: 200. Replay latency: 115.159 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 8

Player: Why did I find that mark?

GM: From what has already been established: You inspect courtyard lantern. A small maker's mark is stamped beneath the lantern.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 3 -> 3. World changed: False. HTTP: 200. Replay latency: 31.04 ms. Provider calls: 0.

Classification: PASS WITH RESPONSE LIMITATION (broad restatement of established text).

## Turn 9

Player: Actually, never mind the inspection; leave it alone.

GM: I've set aside the unexecuted intention. Anything already resolved still stands.

Decision: GM / ANSWER. Resolution: conversational_answer. Turn counter: 3 -> 3. World changed: False. HTTP: 200. Replay latency: 31.355 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Turn 10

Player: I walk through the courtyard gate.

GM: You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road.

Decision: resolver / scene_transition. Resolution: scene_transition. Turn counter: 3 -> 4. World changed: True. HTTP: 200. Replay latency: 175.889 ms. Provider calls: 0.

Classification: PASS for routing, authority and continuity in this recorded-input sequence.

## Fresh live result

Both preceding fresh live runs completed ten HTTP requests and preserved GM-turn world-state invariants, but turn five emitted 'No one here can answer that from what is settled here.' This is a behavioral FAIL despite successful HTTP delivery. The final live run correctly disclosed the lantern mark at turn seven and moved at turn ten. The final NPC recall correction was verified by replay and tests, not by a third fresh live campaign.
