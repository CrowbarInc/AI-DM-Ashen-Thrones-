# R2-MT06 — hidden_fact_probe

Objective: Observe the square and probe for hidden facts without receiving GM-only leakage.
Family: multi_turn_arc
Turns: 6
Completed: True

## Turn 1

### Player

I look around the square carefully, especially the edges and rooftops.

### GM

You look around the square carefully, especially the edges and rooftops, and you get an immediate read on what is there. high above, the slate rooftops bear dark rivulets from the persistent drizzle, shadowing narrow alleys where dark shapes flicker—watchers or scavengers, impossible to tell leaves at a glance and cuts through the crowd and stops at your shoulder. "You're asking the wrong questions out loud," they murmur. "Walk with me if you want the next name.".

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `observe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "observe", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 83, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 78, "text_preview": "You look around the square carefully, especially the edges and rooftops, and you get an immediate read on what is there. high above, the slate rooftops bear dar"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "carefully", "edges", "especially", "look", "rooftops", "square"], "gm_terms": ["above", "alleys", "around", "asking", "bear", "carefully", "crowd", "cuts", "dark", "drizzle", "edges", "especially", "flicker", "get", "glance", "high", "immediate", "impossible", "leaves", "look"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 2

### Player

Is someone from a noble house watching new arrivals?

### GM

high above, the slate rooftops bear dark rivulets from the persistent drizzle, shadowing narrow alleys where dark shapes flicker—watchers or scavengers, impossible to tell leaves at a glance and comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail.".

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 81, "rating": "strong", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 50, "text_preview": "high above, the slate rooftops bear dark rivulets from the persistent drizzle, shadowing narrow alleys where dark shapes flicker—watchers or scavengers, impossi"}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["arrivals", "house", "noble", "someone", "watching"], "gm_terms": ["above", "alleys", "ask", "bear", "before", "comes", "dark", "drizzle", "enough", "flicker", "glance", "high", "impossible", "leaves", "lose", "narrow", "now", "pause", "persistent", "rivulets"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 3

### Player

I watch the threadbare figure who isn't moving with the queue. What are they actually doing?

### GM

The murmur around you never tightens into a single clear voice on that point.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `social_probe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 71, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 14, "text_preview": "The murmur around you never tightens into a single clear voice on that point."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["actually", "doing", "figure", "isn't", "moving", "queue", "they", "threadbare", "watch", "what"], "gm_terms": ["around", "clear", "murmur", "never", "point", "single", "tightens", "voice"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 4

### Player

Do you know if anyone above the lane is matching faces to a written list?

### GM

The moment passes without anyone stepping forward to own that thread.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 80, "rating": "strong", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The moment passes without anyone stepping forward to own that thread."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["above", "anyone", "faces", "know", "lane", "list", "matching", "written"], "gm_terms": ["anyone", "forward", "moment", "own", "passes", "stepping", "thread", "without"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 5

### Player

I ask the Guard Captain whether Ash Cowl smugglers are scouting the crowd for talent.

### GM

Guard Captain shakes their head. "I don't know."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "guard_captain", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 79, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["captain", "cowl", "crowd", "guard", "scouting", "smugglers", "talent", "whether"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 20, "player_intent_score": 18}}}`

## Turn 6

### Player

What have I actually confirmed with my own eyes, not rumor?

### GM

Guard Captain shakes their head. "I don't know."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "guard_captain", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 57, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["actually", "confirmed", "eyes", "rumor", "what"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 17, "player_intent_score": 9}}}`
