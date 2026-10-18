# 16 — Secondary Fresh-Provider Conversation

FRESH: actual production /api/chat through FastAPI TestClient and the configured external provider; no interpretation/narration doubles or replay. Complete JSON preserves HTTP result, authority, adopted text, before/after history, world and commitment diffs, tokens and storage round-trips.

### Turn 1

Player: I ask Corporal Bren whether guards watch the north gate at night.

Delivered: Corporal Bren mutters, "Word is, guards watch the north gate throughout the night."

Topic: `night_watch`. Adopted source: `social.topic_revealed:night_watch`. Calls: 1; latency: 2471.4 ms. Failure flags: [].

### Turn 2

Player: What did you mean by that?

Delivered: Corporal Bren mutters, "Word is, guards watch the north gate throughout the night."

Topic: `None`. Adopted source: `dialogue_authority.reuse_prior_speech`. Calls: 0; latency: 83.7 ms. Failure flags: [].

### Turn 3

Player: I ask Corporal Bren who made the lantern.

Delivered: Corporal Bren says, "I couldn't tell you."

Topic: `None`. Adopted source: `dialogue_authority.player_line`. Calls: 1; latency: 2079.8 ms. Failure flags: [].

### Turn 4

Player: I ask Corporal Bren, do you prefer the morning or the evening?

Delivered: Corporal Bren says, "I prefer the morning."

Topic: `None`. Adopted source: `conversational_continuity.bounded_personal_line`. Calls: 1; latency: 2052.1 ms. Failure flags: [].

### Turn 5

Player: Why that one, then?

Delivered: Corporal Bren says, "I prefer the morning."

Topic: `None`. Adopted source: `conversational_decision:repeat_delivered_statement`. Calls: 0; latency: 28.4 ms. Failure flags: [].

### Turn 6

Player: I ask Corporal Bren what the street outside the gate is named.

Delivered: Corporal Bren mutters, "Word is, the street beyond the gate is the north road."

Topic: `street`. Adopted source: `social.topic_revealed:street`. Calls: 1; latency: 2015.1 ms. Failure flags: [].

### Turn 7

Player: Say that again in plainer words.

Delivered: Corporal Bren mutters, "Word is, the street beyond the gate is the north road."

Topic: `None`. Adopted source: `conversational_decision:repeat_delivered_statement`. Calls: 0; latency: 44.0 ms. Failure flags: [].

### Turn 8

Player: If I carry a message, will you promise me a reward?

Delivered: Corporal Bren says, "I can't promise you a reward for that."

Topic: `None`. Adopted source: `conversational_decision:npc_request_declined`. Calls: 0; latency: 27.3 ms. Failure flags: [].

### Turn 9

Player: Promise me a reward if I carry a message for you.

Delivered: Corporal Bren says, "I can't promise you a reward for that."

Topic: `None`. Adopted source: `conversational_decision:npc_request_declined`. Calls: 0; latency: 27.2 ms. Failure flags: [].

### Turn 10

Player: I ask Corporal Bren when the guards leave the gate unattended.

Delivered: Corporal Bren says, "I couldn't tell you."

Topic: `None`. Adopted source: `dialogue_authority.player_line`. Calls: 1; latency: 2059.2 ms. Failure flags: [].

### Turn 11

Player: I ask Corporal Bren what the password is.

Delivered: Corporal Bren says, "I couldn't tell you."

Topic: `None`. Adopted source: `dialogue_authority.player_line`. Calls: 1; latency: 2333.7 ms. Failure flags: [].

### Turn 12

Player: GM, repeat what Bren said about the road.

Delivered: Corporal Bren said: "Word is, the street beyond the gate is the north road."

Topic: `None`. Adopted source: `conversational_decision:gm_recall_of_npc_statement`. Calls: 0; latency: 33.9 ms. Failure flags: [].
