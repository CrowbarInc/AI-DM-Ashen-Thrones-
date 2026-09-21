# R2-MT01 — notice_patrol_inquiry

Objective: Learn what the notice says about the missing patrol and decide whether to follow that lead.
Family: multi_turn_arc
Turns: 8
Completed: True

## Turn 1

### Player

I look around the gate.

### GM

A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain watches with hard, tired discipline, while Tavern Runner trades hot stew and rumors near the rain barrel.

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
- playability_overall: `{"score": 84, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain "}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "gate", "look"], "gm_terms": ["along", "barrel", "board", "captain", "cluster", "crowd", "discipline", "eye", "gate", "guard", "hard", "hot", "keeps", "line", "manages", "muddy", "near", "one", "rain", "refugees"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 2

### Player

I step closer and read the notice board carefully.

### GM

The guard says, "I do not know enough to answer that."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `None`
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
- playability_overall: `{"score": 73, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:observation_request_not_fulfilled"], "evidence": {"request_kind": "observation", "player_terms": ["board", "carefully", "closer", "notice", "read", "step"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 3

### Player

That missing patrol warning matters. What exactly does it say about where they were last seen?

### GM

The guard says, "I do not know enough to answer that."

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
- playability_overall: `{"score": 57, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["exactly", "last", "matters", "missing", "patrol", "seen", "they", "warning", "what", "where"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 4

### Player

I turn to the Guard Captain. "What's being done about the missing patrol?"

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
- playability_overall: `{"score": 76, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["captain", "done", "guard", "missing", "patrol", "turn", "what's"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 5

### Player

I don't want to rush the northwest track yet. Who last spoke to that patrol before they left?

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
- playability_overall: `{"score": 66, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["before", "don't", "last", "left", "northwest", "patrol", "rush", "spoke", "they", "track", "want"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 6

### Player

Earlier the notice mentioned a mud track. Is that still the official last position?

### GM

Guard Captain shakes their head. "I don't know."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `social_probe`
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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["earlier", "last", "mentioned", "notice", "official", "position", "still", "track"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 7

### Player

Fine. I'll follow the missing patrol rumor along that northwest mud track.

### GM

Guard Captain shakes their head. "I don't know."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `social_probe`
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
- playability_overall: `{"score": 60, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "fine", "follow", "i'll", "missing", "northwest", "patrol", "rumor", "track"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 20, "player_intent_score": 9}}}`

## Turn 8

### Player

After I start that way, I pause and check whether anything about the patrol warning has changed.

### GM

Guard Captain shakes their head. "I don't know."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `social_probe`
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
- playability_overall: `{"score": 60, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:observation_request_not_fulfilled"], "evidence": {"request_kind": "observation", "player_terms": ["after", "anything", "changed", "check", "patrol", "pause", "start", "warning", "whether"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 20, "player_intent_score": 9}}}`
