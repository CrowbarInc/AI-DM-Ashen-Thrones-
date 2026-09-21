# R2-MT01-AM — notice_patrol_inquiry_return_captain_answer_roster_inspection_stew_relevance_world_action_override

Objective: Learn the missing-patrol route, pursue it, investigate, return, observe, reread the board, bind the Guard Captain, receive a legitimate first-ask answer, inspect the referenced roster, look around, ask the tavern runner what stew costs, glance back at the notice board, then take one more natural action.
Family: multi_turn_arc
Turns: 14
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

You lean in under the drizzling rain to scan the notice board's posted bulletins. Taxes have risen again, tightening the purse strings in Cinderwatch. The new curfew rules impose earlier lockdowns, meant to curb recent unrest. A stark warning captures your attention most: a patrol has gone missing. The announcement states the patrol was last seen taking the northwest mud track past the crates near the eastern gate. Nearby, a gate serjeant keeps a wary eye on the crowd while glancing occasionally at a roster board. This thread of worry hangs heavy amid the bustle of refugees and travelers pressing through.

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
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 101, "text_preview": "You lean in under the drizzling rain to scan the notice board's posted bulletins. Taxes have risen again, tightening the purse strings in Cinderwatch. The new c"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["board", "carefully", "closer", "notice", "read", "step"], "gm_terms": ["again", "amid", "announcement", "attention", "board", "board's", "bulletins", "bustle", "captures", "cinderwatch", "crates", "crowd", "curb", "curfew", "drizzling", "earlier", "eastern", "eye", "gate", "glancing"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 3

### Player

Fine. I'll follow the missing patrol rumor along that northwest mud track.

### GM

You arrive at the Old Milestone, a weathered stone leaning beside the northwest mud track. The ground around the marker is churned with faint, overlapping footprints that fade into the scrub brush. Rainwater pools on the path, and beyond the milestone, the track narrows and becomes unclear through mud and dense undergrowth, making further travel uncertain from here.

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 58, "text_preview": "You arrive at the Old Milestone, a weathered stone leaning beside the northwest mud track. The ground around the marker is churned with faint, overlapping footp"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "fine", "follow", "i'll", "missing", "northwest", "patrol", "rumor", "track"], "gm_terms": ["around", "arrive", "becomes", "beside", "beyond", "brush", "churned", "dense", "fade", "faint", "footprints", "further", "ground", "leaning", "making", "marker", "milestone", "mud", "narrows", "northwest"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 4

### Player

I look around.

### GM

In Old Milestone, a weathered milestone leans beside the northwest mud track, where the road thins into scrub and standing rainwater

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
- playability_overall: `{"score": 72, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 21, "text_preview": "In Old Milestone, a weathered milestone leans beside the northwest mud track, where the road thins into scrub and standing rainwater"}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:observation_request_not_fulfilled"], "evidence": {"request_kind": "observation", "player_terms": ["around", "look"], "gm_terms": ["beside", "leans", "milestone", "mud", "northwest", "old", "rainwater", "road", "scrub", "standing", "thins", "track", "weathered", "where"], "direct_answer_score": 23, "player_intent_score": 9}}}`

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

The notice board remains the same: a weathered wooden plank listing the current taxes, curfew regulations, and a posted warning about the missing patrol last seen taking the northwest mud track past the crates. No new postings have been added since you last checked.

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
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "The notice board remains the same: a weathered wooden plank listing the current taxes, curfew regulations, and a posted warning about the missing patrol last se"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["again", "board", "notice", "read"], "gm_terms": ["added", "board", "checked", "crates", "curfew", "current", "last", "listing", "missing", "mud", "new", "northwest", "notice", "past", "patrol", "plank", "posted", "postings", "regulations", "remains"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 9

### Player

I turn to the Guard Captain. "What's being done about the missing patrol?"

### GM

Guard Captain mutters, "Word is, we're keeping a tight watch on the northwest mud track where the patrol was last seen,."

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
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 21, "text_preview": "Guard Captain mutters, \"Word is, we're keeping a tight watch on the northwest mud track where the patrol was last seen,.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["captain", "done", "guard", "missing", "patrol", "turn", "what's"], "gm_terms": ["captain", "guard", "keeping", "last", "mud", "mutters", "northwest", "patrol", "seen", "tight", "track", "watch", "we're", "where", "word"], "direct_answer_score": 22, "player_intent_score": 18}}}`

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

You take another slow turn along the muddy gate line under the withering rain. Threadbare watchers and refugees press close, faces drawn and wary from the dim news and cramped conditions. The gate serjeant methodically scans the roster board, keeping the watch organized yet wary. The tavern runner hawks hot stew and whispered tidings by the rain barrel, while streams of refugees and wagons shuffled slowly past the choke at the gate. The notice board continues to display the same weathered proclamations: taxes, curfew mandates, and the stark warning about a patrol missing beyond the northwest mud track by the crates. The air holds a taut silence broken only by the murmur of the uneasy crowd and the creak of gate mechanics. No new faces of note emerge from the milling cluster, nor do you detect a shift in the watch's posture.

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 142, "text_preview": "You take another slow turn along the muddy gate line under the withering rain. Threadbare watchers and refugees press close, faces drawn and wary from the dim n"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["after", "again", "around", "gate", "look"], "gm_terms": ["air", "along", "another", "barrel", "beyond", "board", "broken", "choke", "close", "cluster", "conditions", "continues", "cramped", "crates", "creak", "crowd", "curfew", "detect", "dim", "display"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 12

### Player

I step over to the tavern runner and ask what the stew costs.

### GM

Tavern Runner says, "No. I cannot answer that from what."

### Evidence

- semantic_result: `FAIL`
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
- playability_overall: `{"score": 82, "rating": "strong", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "FAIL", "passed": false, "reason_codes": ["malformed_output:broken_refusal_fragment"], "evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["costs", "over", "runner", "step", "stew", "tavern", "what"], "gm_terms": ["answer", "cannot", "runner", "says", "tavern", "what"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 13

### Player

I glance back at the notice board after that.

### GM

The notice board still displays its weathered proclamations clearly under the rain: new taxes levied on the dwindling trade, strict curfew hours imposed, and a stark warning about the missing patrol last seen taking the northwest mud track past the crates. No fresh updates have…

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
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 45, "text_preview": "The notice board still displays its weathered proclamations clearly under the rain: new taxes levied on the dwindling trade, strict curfew hours imposed, and a "}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["after", "back", "board", "glance", "notice"], "gm_terms": ["board", "clearly", "crates", "curfew", "displays", "dwindling", "fresh", "hours", "imposed", "its", "last", "levied", "missing", "mud", "new", "northwest", "notice", "past", "patrol", "proclamations"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 14

### Player

I step back to the tavern runner and ask who last checked that board.

### GM

Tavern Runner mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 19, "text_preview": "Tavern Runner mutters, \"Word is, the missing patrol was last seen taking the northwest mud track past the crates.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["back", "board", "checked", "last", "runner", "step", "tavern"], "gm_terms": ["crates", "last", "missing", "mud", "mutters", "northwest", "past", "patrol", "runner", "seen", "taking", "tavern", "track", "word"], "direct_answer_score": 23, "player_intent_score": 18}}}`
