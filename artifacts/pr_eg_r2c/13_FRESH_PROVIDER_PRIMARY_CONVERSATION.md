# 13 — Fresh-Provider Primary Conversation

FRESH actual FastAPI TestClient POST /api/chat?ui_mode=player. No provider replay/doubles. 15 independent campaign turns; real provider interpretation uses configured production route. Different speaker/order/wording in the secondary fixture. Complete result payloads, state diffs, history and usage are retained in live_qualification.json. Metrics: {"turns": 15, "provider_calls": 8, "interpretation_calls": 8, "narration_calls": 0, "retry_calls": 0, "input_tokens": 14874, "output_tokens": 1507, "avg_input_tokens": 991.6, "avg_output_tokens": 100.46666666666667, "calls_per_turn": 0.5333333333333333, "avg_latency_ms": 1395.9375133311066, "max_latency_ms": 3651.693299994804, "p50_latency_ms": 2000.4724999889731, "raw_failure_flags": 6, "failed_turns": [3, 7, 8, 13, 14]}. This conversation fails usable-dialogue qualification.

### Turn 1

PLAYER: I ask Sergeant Mara what the street beyond the gate is called.

DELIVERED: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Calls: 1; input/output: 1711/197; elapsed: 3651.7 ms; source: `social.topic_revealed:street`; raw flags: [].

### Turn 2

PLAYER: What did you mean by north road?

DELIVERED: Sergeant Mara says, "I meant this: Word is, the street beyond the gate is the north road."

Calls: 0; input/output: 0/0; elapsed: 92.2 ms; source: `dialogue_authority.reuse_prior_speech`; raw flags: [].

### Turn 3

PLAYER: Can you repeat that?

DELIVERED: Sergeant Mara says, "I couldn't tell you."

Calls: 0; input/output: 0/0; elapsed: 80.5 ms; source: `dialogue_authority.knowledge_posture`; raw flags: ['missing_requested_answer:north road'].

### Turn 4

PLAYER: I ask Sergeant Mara, do you prefer morning or evening?

DELIVERED: Sergeant Mara says, "I prefer the evening."

Calls: 1; input/output: 1892/175; elapsed: 2231.6 ms; source: `conversational_continuity.bounded_personal_line`; raw flags: [].

### Turn 5

PLAYER: Why do you prefer the evening?

DELIVERED: Sergeant Mara says, "I prefer the evening."

Calls: 0; input/output: 0/0; elapsed: 85.5 ms; source: `dialogue_authority.reuse_prior_speech`; raw flags: [].

### Turn 6

PLAYER: I ask Sergeant Mara who forged the lantern.

DELIVERED: Sergeant Mara says, "I couldn't tell you."

Calls: 1; input/output: 1885/185; elapsed: 2498.0 ms; source: `dialogue_authority.player_line`; raw flags: [].

### Turn 7

PLAYER: I ask Sergeant Mara whether guards watch the north gate at night.

DELIVERED: Sergeant Mara says, "I couldn't tell you."

Calls: 1; input/output: 1854/206; elapsed: 2980.8 ms; source: `dialogue_authority.knowledge_posture`; raw flags: ['missing_requested_answer:throughout the night'].

### Turn 8

PLAYER: What did you mean by that?

DELIVERED: Sergeant Mara says, "I meant that I don't know."

Calls: 0; input/output: 0/0; elapsed: 96.7 ms; source: `dialogue_authority.reuse_prior_speech`; raw flags: ['missing_requested_answer:throughout the night'].

### Turn 9

PLAYER: I ask Sergeant Mara when the gate is left unguarded.

DELIVERED: Sergeant Mara says, "I couldn't tell you."

Calls: 1; input/output: 1860/198; elapsed: 2366.5 ms; source: `dialogue_authority.knowledge_posture`; raw flags: [].

### Turn 10

PLAYER: Promise me a reward if I carry a message for you.

DELIVERED: Sergeant Mara says, "I can't promise you a reward for that."

Calls: 0; input/output: 0/0; elapsed: 30.6 ms; source: `conversational_decision:npc_request_declined`; raw flags: [].

### Turn 11

PLAYER: Swear you will pay me ten silver if I do it.

DELIVERED: Sergeant Mara says, "I can't promise you a reward for that."

Calls: 0; input/output: 0/0; elapsed: 29.9 ms; source: `conversational_decision:npc_request_declined`; raw flags: [].

### Turn 12

PLAYER: I ask Sergeant Mara what secret passage bypasses the gate.

DELIVERED: Sergeant Mara says, "I couldn't answer that."

Calls: 1; input/output: 1905/209; elapsed: 2460.1 ms; source: `dialogue_authority.player_line`; raw flags: [].

### Turn 13

PLAYER: I ask Sergeant Mara about the north road again.

DELIVERED: Sergeant Mara says, "I couldn't tell you."

Calls: 1; input/output: 1886/161; elapsed: 2000.5 ms; source: `dialogue_authority.knowledge_posture`; raw flags: ['missing_requested_answer:north road'].

### Turn 14

PLAYER: GM, what did Mara say about the road?

DELIVERED: Sergeant Mara said they could not answer that. They have not spoken again.

Calls: 0; input/output: 0/0; elapsed: 37.7 ms; source: `conversational_decision:gm_recall_of_npc_statement`; raw flags: ['missing_requested_answer:north road', 'delivered_history_mismatch'].

### Turn 15

PLAYER: I ask Sergeant Mara, do you still prefer the evening?

DELIVERED: Sergeant Mara says, "I prefer the evening."

Calls: 1; input/output: 1881/176; elapsed: 2296.7 ms; source: `dialogue_authority.reuse_prior_speech`; raw flags: [].
