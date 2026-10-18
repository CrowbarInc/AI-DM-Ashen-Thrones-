# 14 — Fresh-Provider Secondary Conversation

FRESH actual FastAPI TestClient POST /api/chat?ui_mode=player. No provider replay/doubles. 12 independent campaign turns; real provider interpretation uses configured production route. Different speaker/order/wording in the secondary fixture. Complete result payloads, state diffs, history and usage are retained in live_qualification.json. Metrics: {"turns": 12, "provider_calls": 6, "interpretation_calls": 6, "narration_calls": 0, "retry_calls": 0, "input_tokens": 11220, "output_tokens": 1123, "avg_input_tokens": 935.0, "avg_output_tokens": 93.58333333333333, "calls_per_turn": 0.5, "avg_latency_ms": 1227.5578999954935, "max_latency_ms": 3293.486800015671, "p50_latency_ms": 1036.5795500110835, "raw_failure_flags": 6, "failed_turns": [1, 2, 6, 7, 12]}. This conversation fails usable-dialogue qualification.

### Turn 1

PLAYER: I ask Corporal Bren whether guards watch the north gate at night.

DELIVERED: Corporal Bren mutters, "Word is, the street beyond the gate is the north road."

Calls: 1; input/output: 1713/210; elapsed: 2400.1 ms; source: `social.topic_revealed:street`; raw flags: ['missing_requested_answer:throughout the night'].

### Turn 2

PLAYER: What did you mean by that?

DELIVERED: Corporal Bren says, "I meant this: Word is, the street beyond the gate is the north road."

Calls: 0; input/output: 0/0; elapsed: 91.5 ms; source: `dialogue_authority.reuse_prior_speech`; raw flags: ['missing_requested_answer:throughout the night'].

### Turn 3

PLAYER: I ask Corporal Bren who made the lantern.

DELIVERED: Corporal Bren says, "I couldn't tell you."

Calls: 1; input/output: 1896/186; elapsed: 2204.1 ms; source: `dialogue_authority.player_line`; raw flags: [].

### Turn 4

PLAYER: I ask Corporal Bren, do you prefer the morning or the evening?

DELIVERED: Corporal Bren says, "I prefer the morning."

Calls: 1; input/output: 1905/181; elapsed: 2234.5 ms; source: `conversational_continuity.bounded_personal_line`; raw flags: [].

### Turn 5

PLAYER: Why that one, then?

DELIVERED: Corporal Bren says, "I meant this: I prefer the morning."

Calls: 0; input/output: 0/0; elapsed: 30.3 ms; source: `conversational_decision:repeat_delivered_statement`; raw flags: [].

### Turn 6

PLAYER: I ask Corporal Bren what the street outside the gate is named.

DELIVERED: Corporal Bren says, "I couldn't tell you."

Calls: 1; input/output: 1910/193; elapsed: 2382.3 ms; source: `dialogue_authority.knowledge_posture`; raw flags: ['missing_requested_answer:north road'].

### Turn 7

PLAYER: Say that again in plainer words.

DELIVERED: Corporal Bren says, "I meant that I don't know."

Calls: 0; input/output: 0/0; elapsed: 27.8 ms; source: `conversational_decision:repeat_delivered_statement`; raw flags: ['missing_requested_answer:north road'].

### Turn 8

PLAYER: If I carry a message, will you promise me a reward?

DELIVERED: Corporal Bren says, "I can't promise you a reward for that."

Calls: 0; input/output: 0/0; elapsed: 26.8 ms; source: `conversational_decision:npc_request_declined`; raw flags: [].

### Turn 9

PLAYER: Promise me a reward if I carry a message for you.

DELIVERED: Corporal Bren says, "I can't promise you a reward for that."

Calls: 0; input/output: 0/0; elapsed: 30.1 ms; source: `conversational_decision:npc_request_declined`; raw flags: [].

### Turn 10

PLAYER: I ask Corporal Bren when the guards leave the gate unattended.

DELIVERED: Corporal Bren says, "I couldn't tell you."

Calls: 1; input/output: 1906/188; elapsed: 3293.5 ms; source: `dialogue_authority.knowledge_posture`; raw flags: [].

### Turn 11

PLAYER: I ask Corporal Bren what the password is.

DELIVERED: Corporal Bren says, "I couldn't tell you."

Calls: 1; input/output: 1890/165; elapsed: 1981.7 ms; source: `dialogue_authority.player_line`; raw flags: [].

### Turn 12

PLAYER: GM, repeat what Bren said about the road.

DELIVERED: Corporal Bren said: "I prefer the morning."

Calls: 0; input/output: 0/0; elapsed: 28.1 ms; source: `conversational_decision:gm_recall_of_npc_statement`; raw flags: ['missing_requested_answer:north road', 'delivered_history_mismatch'].
