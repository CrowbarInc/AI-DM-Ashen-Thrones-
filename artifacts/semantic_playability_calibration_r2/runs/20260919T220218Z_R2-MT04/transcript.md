# R2-MT04 — lirael_redirect_lead_policy

Objective: Ask after Lirael, then pursue only official follow-up permitted by RC-21.
Family: multi_turn_arc
Turns: 7
Completed: True

## Turn 1

### Player

I ask the nearest guard, "Where can I find Lirael?"

### GM

Gate Guard says, "I do not know enough to answer that."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 78, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "Gate Guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["find", "guard", "lirael", "nearest", "where"], "gm_terms": ["answer", "enough", "gate", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 2

### Player

If you mentioned the notice board, I'll check that. What should I look for there?

### GM

A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain watches with hard, tired discipline, while Tavern Runner trades hot stew and rumors near the rain barrel.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `investigate`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "investigate", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 82, "rating": "strong", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain "}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["board", "check", "i'll", "look", "mentioned", "notice", "what"], "gm_terms": ["along", "barrel", "board", "captain", "cluster", "crowd", "discipline", "eye", "gate", "guard", "hard", "hot", "keeps", "line", "manages", "muddy", "near", "one", "rain", "refugees"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 3

### Player

I read the notice board.

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
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "investigate", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 68, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:observation_request_not_fulfilled"], "evidence": {"request_kind": "observation", "player_terms": ["board", "notice", "read"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 23, "player_intent_score": 4}}}`

## Turn 4

### Player

You said I'd find help near the board. Is Lirael actually here, or was that just talk?

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
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "investigate", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 57, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["actually", "board", "find", "help", "lirael", "near", "said", "talk"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 5

### Player

I look for Lirael among the crowd.

### GM

You scan the crowd gathered at the muddy gate line, but among the ragged watchers, refugees, and the bustle around the notice board, no sign of Lirael emerges. The tavern runner near the rain barrel seems engaged in trading rumors and might have overheard something useful about Lirael's whereabouts or contacts to pursue.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `investigate`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "investigate", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 53, "text_preview": "You scan the crowd gathered at the muddy gate line, but among the ragged watchers, refugees, and the bustle around the notice board, no sign of Lirael emerges. "}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["among", "crowd", "lirael", "look"], "gm_terms": ["among", "around", "barrel", "board", "bustle", "contacts", "crowd", "emerges", "engaged", "gate", "gathered", "line", "lirael", "lirael's", "muddy", "near", "notice", "overheard", "pursue", "ragged"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 6

### Player

I'll pursue whatever official follow-up exists from that conversation.

### GM

The guard says, "I do not know enough to answer that."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `interact`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "interact", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 73, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["conversation", "exists", "follow", "i'll", "official", "pursue", "whatever"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 7

### Player

Has a new person appeared because someone named Lirael, or am I still dealing with the same gate crowd?

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 57, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["appeared", "because", "crowd", "dealing", "gate", "lirael", "named", "person", "same", "someone", "still"], "gm_terms": ["answer", "enough", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 9}}}`
