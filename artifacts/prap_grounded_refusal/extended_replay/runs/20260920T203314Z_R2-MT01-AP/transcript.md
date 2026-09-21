# R2-MT01-AP — notice_patrol_inquiry_return_captain_answer_roster_inspection_stew_relevance_world_action_question_sufficiency_investigation_provenance_refusal_grammar

Objective: Learn the missing-patrol route, pursue it, investigate, return, observe, reread the board, bind the Guard Captain, receive a legitimate first-ask answer, inspect the referenced roster, look around, ask the tavern runner what stew costs, glance back at the notice board, ask who last checked that board, thank the runner and look toward the gate line, then take one more natural action.
Family: multi_turn_arc
Turns: 16
Completed: True

## Turn 1

### Player

I look around the gate.

### GM

Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "Gate Guard mutters, \"Word is, captain Thoran commands the gate watch tonight.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "gate", "look"], "gm_terms": ["captain", "commands", "gate", "guard", "mutters", "thoran", "tonight", "watch", "word"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 2

### Player

I step closer and read the notice board carefully.

### GM

The missing patrol was last seen taking the northwest mud track past the crates.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `discover_clue`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "observe", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 77, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 14, "text_preview": "The missing patrol was last seen taking the northwest mud track past the crates."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["board", "carefully", "closer", "notice", "read", "step"], "gm_terms": ["crates", "last", "missing", "mud", "northwest", "past", "patrol", "seen", "taking", "track"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 3

### Player

Fine. I'll follow the missing patrol rumor along that northwest mud track.

### GM

You arrive at the Old Milestone, a weathered stone marker leaning beside the northwest mud track. The mud around it is churned with faint, overlapping footprints that quickly fade into the scrub. The track continues just a short distance past the milestone before rainwater pools and dense brush obscure the way forward.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `scene_transition`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": null, "interaction_mode": "none", "engagement_level": "none"}`
- scene: `frontier_gate` -> `old_milestone`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 52, "text_preview": "You arrive at the Old Milestone, a weathered stone marker leaning beside the northwest mud track. The mud around it is churned with faint, overlapping footprint"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "fine", "follow", "i'll", "missing", "northwest", "patrol", "rumor", "track"], "gm_terms": ["around", "arrive", "before", "beside", "brush", "churned", "continues", "dense", "distance", "fade", "faint", "footprints", "forward", "leaning", "marker", "milestone", "mud", "northwest", "obscure", "old"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 4

### Player

I look around.

### GM

A weathered stone milestone leans beside the northwest mud track holds the eye, while the track continues a short way past the stone before rainwater and brush make the next step unclear stays impossible to ignore.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `observe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "observe", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `old_milestone` -> `old_milestone`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 77, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 36, "text_preview": "A weathered stone milestone leans beside the northwest mud track holds the eye, while the track continues a short way past the stone before rainwater and brush "}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:observation_request_not_fulfilled"], "evidence": {"request_kind": "observation", "player_terms": ["around", "look"], "gm_terms": ["before", "beside", "brush", "continues", "eye", "holds", "ignore", "impossible", "leans", "make", "milestone", "mud", "next", "northwest", "past", "rainwater", "short", "stays", "step", "stone"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 5

### Player

I examine the milestone.

### GM

You examine the milestone, and you turn up a concrete clue.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `discover_clue`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "observe", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `old_milestone` -> `old_milestone`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 81, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "You examine the milestone, and you turn up a concrete clue."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["examine", "milestone"], "gm_terms": ["clue", "concrete", "examine", "milestone", "turn", "up"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 6

### Player

I'll head back to the gate.

### GM

You act on that decision and leave along the available path.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `scene_transition`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": null, "interaction_mode": "none", "engagement_level": "none"}`
- scene: `old_milestone` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 72, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "You act on that decision and leave along the available path."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:player_action_or_request_lost"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["back", "gate", "head", "i'll"], "gm_terms": ["act", "along", "available", "decision", "leave", "path"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 7

### Player

I look around.

### GM

As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 79, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 29, "text_preview": "As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster bo"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "look"], "gm_terms": ["along", "board", "cluster", "crowd", "eye", "gate", "keeps", "line", "manages", "muddy", "one", "refugees", "roster", "scene", "serjeant", "threadbare", "watch", "watchers"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 8

### Player

I read the notice board again.

### GM

The missing patrol was last seen taking the northwest mud track past the crates.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `already_searched`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "observe", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 77, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 14, "text_preview": "The missing patrol was last seen taking the northwest mud track past the crates."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["again", "board", "notice", "read"], "gm_terms": ["crates", "last", "missing", "mud", "northwest", "past", "patrol", "seen", "taking", "track"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 9

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 76, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 8, "text_preview": "Guard Captain shakes their head. \"I don't know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["captain", "done", "guard", "missing", "patrol", "turn", "what's"], "gm_terms": ["captain", "don't", "guard", "head", "know", "shakes"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 10

### Player

If the watch already has a commander on this, I'll check the roster board the serjeant is watching.

### GM

On closer inspection, a gate serjeant manages the crowd and keeps one eye on the roster board. Closer looking yields nothing further.

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 22, "text_preview": "On closer inspection, a gate serjeant manages the crowd and keeps one eye on the roster board. Closer looking yields nothing further."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["already", "board", "check", "commander", "i'll", "roster", "serjeant", "watch", "watching"], "gm_terms": ["board", "closer", "crowd", "eye", "further", "gate", "inspection", "keeps", "looking", "manages", "nothing", "one", "roster", "serjeant", "yields"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 11

### Player

I look around the gate again after that.

### GM

As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 29, "text_preview": "As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster bo"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["after", "again", "around", "gate", "look"], "gm_terms": ["along", "board", "cluster", "crowd", "eye", "gate", "keeps", "line", "manages", "muddy", "one", "refugees", "roster", "scene", "serjeant", "threadbare", "watch", "watchers"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 12

### Player

I step over to the tavern runner and ask what the stew costs.

### GM

Tavern Runner says, "No. I cannot answer that from what I know."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "tavern_runner", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 82, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what I know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["costs", "over", "runner", "step", "stew", "tavern", "what"], "gm_terms": ["answer", "cannot", "know", "runner", "says", "tavern", "what"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 13

### Player

I glance back at the notice board after that.

### GM

You glance at the notice board again, noting the familiar listings of taxes, curfew rules, and the warning about the missing patrol. The roster board remains unchanged; the patrol's positions are vacant as search parties are still in the process of forming. Nearby, the persistent murmur of the tavern runner hawking hot stew drifts through the damp air, mingling with the murmurs of the crowd wary of the unsettled situation. The muddy line of refugees and watchers remains tense as rain lightly patters down, thickening the suspense around the missing patrol's fate.

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `already_searched`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": "investigate", "interaction_mode": "activity", "engagement_level": "focused"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 92, "text_preview": "You glance at the notice board again, noting the familiar listings of taxes, curfew rules, and the warning about the missing patrol. The roster board remains un"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["after", "back", "board", "glance", "notice"], "gm_terms": ["again", "air", "around", "board", "crowd", "curfew", "damp", "down", "drifts", "familiar", "fate", "forming", "glance", "hawking", "hot", "lightly", "line", "listings", "mingling", "missing"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 14

### Player

I step back to the tavern runner and ask who last checked that board.

### GM

Tavern Runner says, "No. I cannot answer that from what I know."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `question`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "tavern_runner", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 82, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what I know.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["back", "board", "checked", "last", "runner", "step", "tavern"], "gm_terms": ["answer", "cannot", "know", "runner", "says", "tavern", "what"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 15

### Player

I thank the runner and look toward the gate line again.

### GM

On closer inspection, threadbare watchers and refugees cluster along the muddy gate line. Closer looking yields nothing further.

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 18, "text_preview": "On closer inspection, threadbare watchers and refugees cluster along the muddy gate line. Closer looking yields nothing further."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["again", "gate", "line", "look", "runner", "thank", "toward"], "gm_terms": ["along", "closer", "cluster", "further", "gate", "inspection", "line", "looking", "muddy", "nothing", "refugees", "threadbare", "watchers", "yields"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 16

### Player

I walk a few steps along the muddy gate line and listen.

### GM

You step quietly along the muddy gate line, the soft patter of rain mixing with murmurs from the cluster of threadbare watchers and ragged refugees. Their conversations are fragmented and low, dwelling on rumors, the scarcity of supplies, and fleeting whispers about the missing…

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
- lead_registry: `[{"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "milestone_mud_prints", "title": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "You step quietly along the muddy gate line, the soft patter of rain mixing with murmurs from the cluster of threadbare watchers and ragged refugees. Their conve"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "gate", "line", "listen", "muddy", "steps", "walk"], "gm_terms": ["along", "cluster", "conversations", "dwelling", "fleeting", "fragmented", "gate", "line", "low", "missing", "mixing", "muddy", "murmurs", "patter", "quietly", "ragged", "rain", "refugees", "rumors", "scarcity"], "direct_answer_score": 23, "player_intent_score": 18}}}`
