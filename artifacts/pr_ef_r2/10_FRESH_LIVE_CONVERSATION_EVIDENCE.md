# 10 — Fresh Live Conversation Evidence

Three continuous eleven-turn production conversations are preserved. Samples 1/2 preceded final refinements; conversation_3 and originals_2 use exact final production code. The campaign remains initialized and persistent within each conversation; no reset between turns, no rewritten messages, no recorded provider outputs. HTTP uses FastAPI TestClient over actual /api/chat routing with storage redirected to disposable files. Every turn saves and reloads state; turn 6 explicitly round-trips conversational context. This is in-process ASGI HTTP, not a separately hosted server.

Full per-turn raw/normalized interpretation, routing, resolver, final seal, usage and state: transcript_audit.json and original JSON files.

## conversation_1.json — exact final code=False

### Turn 1 — PASS

Player: Could you describe our surroundings?

Response: You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate. A soot-streaked lantern burns beside the courtyard gate. The side gate is barred from the other side. Sergeant Mara looks concerned as she watches the road.

Result=conversational_answer; NPC=None; provider calls=1; latency=3512.264ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 2 — PASS

Player: What do I already know about that lantern?

Response: A soot-streaked lantern burns beside the courtyard gate. You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate.

Result=conversational_answer; NPC=None; provider calls=1; latency=2684.077ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 3 — PASS

Player: I ask Mara what troubles her.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=8780.435ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 4 — PASS

Player: Which road do you mean?

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=2; latency=5605.556ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 5 — PASS

Player: I ask Mara who forged the lantern.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=8657.363ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 6 — PASS

Player: GM, can you clarify what Mara just said?

Response: The street beyond the gate is the north road.

Result=conversational_answer; NPC=None; provider calls=1; latency=2345.589ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 7 — PASS

Player: I turn to Mara and ask about the north road.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=1; latency=4567.026ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 8 — PASS

Player: I inspect the courtyard lantern.

Response: A small maker's mark is stamped beneath the lantern.

Result=discover_clue; NPC=None; provider calls=1; latency=2928.141ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 9 — PASS

Player: Drop any outstanding request; keep what already happened.

Response: I've set aside the unexecuted intention. Anything already resolved still stands.

Result=conversational_answer; NPC=None; provider calls=1; latency=2449.314ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 10 — PASS

Player: I tell the sergeant to describe the courtyard.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=8722.757ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 11 — PASS

Player: I walk through the courtyard gate.

Response: You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road.

Result=scene_transition; NPC=None; provider calls=0; latency=252.639ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

## conversation_2.json — exact final code=False

### Turn 1 — PASS

Player: Could you describe our surroundings?

Response: You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate. A soot-streaked lantern burns beside the courtyard gate. The side gate is barred from the other side. Sergeant Mara looks concerned as she watches the road.

Result=conversational_answer; NPC=None; provider calls=1; latency=5935.431ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 2 — PASS

Player: What do I already know about that lantern?

Response: A soot-streaked lantern burns beside the courtyard gate. You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate.

Result=conversational_answer; NPC=None; provider calls=1; latency=2325.02ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 3 — PASS

Player: I ask Mara what troubles her.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=9184.294ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 4 — PASS

Player: Which road do you mean?

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=2; latency=5981.351ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 5 — PASS

Player: I ask Mara who forged the lantern.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=8357.017ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 6 — PASS

Player: GM, can you clarify what Mara just said?

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=conversational_answer; NPC=None; provider calls=1; latency=2398.205ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 7 — PASS

Player: I turn to Mara and ask about the north road.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=1; latency=2943.611ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 8 — PASS

Player: I inspect the courtyard lantern.

Response: A small maker's mark is stamped beneath the lantern.

Result=discover_clue; NPC=None; provider calls=1; latency=2783.799ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 9 — PASS

Player: Drop any outstanding request; keep what already happened.

Response: I've set aside the unexecuted intention. Anything already resolved still stands.

Result=conversational_answer; NPC=None; provider calls=1; latency=4128.475ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 10 — PASS

Player: I tell the sergeant to describe the courtyard.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=7106.139ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 11 — PASS

Player: I walk through the courtyard gate.

Response: You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road.

Result=scene_transition; NPC=None; provider calls=0; latency=308.024ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

## conversation_3.json — exact final code=True

### Turn 1 — PASS

Player: Could you describe our surroundings?

Response: You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate. A soot-streaked lantern burns beside the courtyard gate. The side gate is barred from the other side. Sergeant Mara looks concerned as she watches the road.

Result=conversational_answer; NPC=None; provider calls=1; latency=4148.943ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 2 — PASS

Player: What do I already know about that lantern?

Response: A soot-streaked lantern burns beside the courtyard gate. You are at Waystation courtyard. A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road. Visible points of interest: courtyard lantern. Known exits: Courtyard gate.

Result=conversational_answer; NPC=None; provider calls=1; latency=2188.611ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 3 — PASS

Player: I ask Mara what troubles her.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=7716.674ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 4 — PASS

Player: Which road do you mean?

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=2; latency=6619.842ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 5 — PASS

Player: I ask Mara who forged the lantern.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=7842.679ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 6 — PASS

Player: GM, can you clarify what Mara just said?

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=conversational_answer; NPC=None; provider calls=1; latency=2915.055ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 7 — PASS

Player: I turn to Mara and ask about the north road.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=1; latency=2740.175ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 8 — PASS

Player: I inspect the courtyard lantern.

Response: A small maker's mark is stamped beneath the lantern.

Result=discover_clue; NPC=None; provider calls=1; latency=2958.969ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 9 — PASS

Player: Drop any outstanding request; keep what already happened.

Response: I've set aside the unexecuted intention. Anything already resolved still stands.

Result=conversational_answer; NPC=None; provider calls=1; latency=2745.618ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 10 — PASS

Player: I tell the sergeant to describe the courtyard.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=9695.818ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 11 — PASS

Player: I walk through the courtyard gate.

Response: You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road.

Result=scene_transition; NPC=None; provider calls=0; latency=334.624ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

## originals_1.json — exact final code=False

### Turn 1 — PASS

Player: I ask Mara what troubles her.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=8379.993ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 2 — PASS

Player: I tell the sergeant to describe the courtyard.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=9960.658ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 3 — PASS

Player: I turn to Mara and ask about the north road.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=2; latency=6166.678ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

## originals_2.json — exact final code=True

### Turn 1 — PASS

Player: I ask Mara what troubles her.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=3; latency=11331.833ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 2 — PASS

Player: I tell the sergeant to describe the courtyard.

Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Result=question; NPC=sergeant_mara; provider calls=1; latency=2663.8ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.

### Turn 3 — PASS

Player: I turn to Mara and ask about the north road.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Result=question; NPC=sergeant_mara; provider calls=1; latency=6290.853ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.
