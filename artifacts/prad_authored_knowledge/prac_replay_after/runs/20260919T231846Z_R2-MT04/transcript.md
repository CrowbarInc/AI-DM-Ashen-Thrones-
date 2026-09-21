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

The missing patrol was last seen taking the northwest mud track past the crates.

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
- playability_overall: `{"score": 71, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 14, "text_preview": "The missing patrol was last seen taking the northwest mud track past the crates."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["board", "check", "i'll", "look", "mentioned", "notice", "what"], "gm_terms": ["crates", "last", "missing", "mud", "northwest", "past", "patrol", "seen", "taking", "track"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 3

### Player

I read the notice board.

### GM

The missing patrol was last seen taking the northwest mud track past the crates.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `discover_clue`
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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 14, "text_preview": "The missing patrol was last seen taking the northwest mud track past the crates."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["board", "notice", "read"], "gm_terms": ["crates", "last", "missing", "mud", "northwest", "past", "patrol", "seen", "taking", "track"], "direct_answer_score": 23, "player_intent_score": 4}}}`

## Turn 4

### Player

You said I'd find help near the board. Is Lirael actually here, or was that just talk?

### GM

I can't swear to it, but no one here at the gate has direct knowledge or confirmation that Lirael is present. The notice board warns of a missing patrol and creates tension among the watchers here, yet mention of Lirael remains unverified and elusive. If you want a clearer path…

### Evidence

- semantic_result: `PASS`
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
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 50, "text_preview": "I can't swear to it, but no one here at the gate has direct knowledge or confirmation that Lirael is present. The notice board warns of a missing patrol and cre"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["actually", "board", "find", "help", "lirael", "near", "said", "talk"], "gm_terms": ["among", "board", "can't", "clearer", "confirmation", "creates", "direct", "elusive", "gate", "knowledge", "lirael", "mention", "missing", "notice", "one", "path", "patrol", "present", "remains", "swear"], "direct_answer_score": 22, "player_intent_score": 18}}}`

## Turn 5

### Player

I look for Lirael among the crowd.

### GM

You look for Lirael among the crowd, and you get an immediate read on what is there.

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
- playability_overall: `{"score": 82, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 17, "text_preview": "You look for Lirael among the crowd, and you get an immediate read on what is there."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["among", "crowd", "lirael", "look"], "gm_terms": ["among", "crowd", "get", "immediate", "lirael", "look", "read", "what"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 6

### Player

I'll pursue whatever official follow-up exists from that conversation.

### GM

You find no immediate official leads or personnel willing to provide formal updates here. The gate serjeant continues managing the crowd with a sharp eye on the roster board, but doesn't offer new information beyond what the notice board already showed: that the missing patrol w…

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
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 46, "text_preview": "You find no immediate official leads or personnel willing to provide formal updates here. The gate serjeant continues managing the crowd with a sharp eye on the"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["conversation", "exists", "follow", "i'll", "official", "pursue", "whatever"], "gm_terms": ["already", "beyond", "board", "continues", "crowd", "doesn't", "eye", "find", "formal", "gate", "immediate", "information", "leads", "managing", "missing", "new", "notice", "offer", "official", "patrol"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 7

### Player

Has a new person appeared because someone named Lirael, or am I still dealing with the same gate crowd?

### GM

No new person named Lirael has appeared among the gate crowd as far as anyone present can say. The gate serjeant and others here have no direct knowledge or confirmation that Lirael is currently at the Cinderwatch Gate District. The atmosphere remains tense around the missing pa…

### Evidence

- semantic_result: `PASS`
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
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 47, "text_preview": "No new person named Lirael has appeared among the gate crowd as far as anyone present can say. The gate serjeant and others here have no direct knowledge or con"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["appeared", "because", "crowd", "dealing", "gate", "lirael", "named", "person", "same", "someone", "still"], "gm_terms": ["among", "anyone", "appeared", "around", "atmosphere", "cinderwatch", "confirmation", "crowd", "currently", "direct", "district", "far", "gate", "knowledge", "lirael", "missing", "named", "new", "others", "pa"], "direct_answer_score": 22, "player_intent_score": 18}}}`
