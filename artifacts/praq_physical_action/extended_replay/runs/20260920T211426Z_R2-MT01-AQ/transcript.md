# R2-MT01-AQ — notice_patrol_inquiry_return_captain_answer_roster_inspection_stew_relevance_world_action_question_sufficiency_investigation_provenance_refusal_grammar_physical_action

Objective: Learn the missing-patrol route, pursue it, investigate, return, observe, reread the board, bind the Guard Captain, receive a legitimate first-ask answer, inspect the referenced roster, look around, ask the tavern runner what stew costs, glance back at the notice board, ask who last checked that board, thank the runner and look toward the gate line, walk a few steps along the muddy gate line and listen, then take one more natural action.
Family: multi_turn_arc
Turns: 17
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

You read the notice board pinned against the soot-dark stone of the gatehouse. It lists the latest taxes and curfew rules imposed on Cinderwatch, along with a stark warning: a patrol has gone missing. According to the notice, the last known route taken by the patrol was down the northwest mud track, passing the crates piled near the eastern choke point. The message urges caution and vigilance, suggesting the situation may be dire.

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
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 74, "text_preview": "You read the notice board pinned against the soot-dark stone of the gatehouse. It lists the latest taxes and curfew rules imposed on Cinderwatch, along with a s"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["board", "carefully", "closer", "notice", "read", "step"], "gm_terms": ["according", "against", "along", "board", "caution", "choke", "cinderwatch", "crates", "curfew", "dark", "dire", "down", "eastern", "gatehouse", "gone", "imposed", "known", "last", "latest", "lists"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 3

### Player

Fine. I'll follow the missing patrol rumor along that northwest mud track.

### GM

You act on that decision and leave along the available path.

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
- playability_overall: `{"score": 81, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "You act on that decision and leave along the available path."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "fine", "follow", "i'll", "missing", "northwest", "patrol", "rumor", "track"], "gm_terms": ["act", "along", "available", "decision", "leave", "path"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 4

### Player

I look around.

### GM

The mud around the marker is churned with faint overlapping prints that fade into the scrub holds the eye, while the track continues a short way past the stone before rainwater and brush make the next step unclear stays impossible to ignore.

### Evidence

- semantic_result: `PASS`
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
- playability_overall: `{"score": 86, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 42, "text_preview": "The mud around the marker is churned with faint overlapping prints that fade into the scrub holds the eye, while the track continues a short way past the stone "}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "look"], "gm_terms": ["around", "before", "brush", "churned", "continues", "eye", "fade", "faint", "holds", "ignore", "impossible", "make", "marker", "mud", "next", "overlapping", "past", "prints", "rainwater", "scrub"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 5

### Player

I examine the milestone.

### GM

Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 18, "text_preview": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["examine", "milestone"], "gm_terms": ["around", "direction", "faint", "mark", "milestone", "mud", "number", "old", "origin", "overlapping", "prints", "stay", "unclear"], "direct_answer_score": 23, "player_intent_score": 18}}}`

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

The notice board displays the current taxes, curfew regulations, and a posted warning concerning a missing patrol. Nearby, a gate serjeant continues to keep a watchful eye on the roster board, managing the restless crowd pressing in through the muddy gate district. Despite reviewing the board again, no new details have been added since your last glance.

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
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 57, "text_preview": "The notice board displays the current taxes, curfew regulations, and a posted warning concerning a missing patrol. Nearby, a gate serjeant continues to keep a w"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["again", "board", "notice", "read"], "gm_terms": ["added", "again", "board", "concerning", "continues", "crowd", "curfew", "current", "despite", "details", "displays", "district", "eye", "gate", "glance", "keep", "last", "managing", "missing", "muddy"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 9

### Player

I turn to the Guard Captain. "What's being done about the missing patrol?"

### GM

Guard Captain mutters, "Word is, we're treating the missing patrol very seriously,."

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "Guard Captain mutters, \"Word is, we're treating the missing patrol very seriously,.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["captain", "done", "guard", "missing", "patrol", "turn", "what's"], "gm_terms": ["captain", "guard", "missing", "mutters", "patrol", "seriously", "treating", "we're", "word"], "direct_answer_score": 17, "player_intent_score": 18}}}`

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

Tavern Runner grimaces. "Not something I can say here."

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
- playability_overall: `{"score": 79, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 9, "text_preview": "Tavern Runner grimaces. \"Not something I can say here.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["costs", "over", "runner", "step", "stew", "tavern", "what"], "gm_terms": ["grimaces", "runner", "say", "something", "tavern"], "direct_answer_score": 20, "player_intent_score": 18}}}`

## Turn 13

### Player

I glance back at the notice board after that.

### GM

The notice board remains unchanged, its posting firmly listing the current taxes, curfew regulations, and the warning about the missing patrol scheduled along the northwest mud track past the crates. The gate serjeant nearby continues his steady watch over the roster board, with…

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 43, "text_preview": "The notice board remains unchanged, its posting firmly listing the current taxes, curfew regulations, and the warning about the missing patrol scheduled along t"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["after", "back", "board", "glance", "notice"], "gm_terms": ["along", "board", "continues", "crates", "curfew", "current", "firmly", "gate", "his", "its", "listing", "missing", "mud", "nearby", "northwest", "notice", "over", "past", "patrol", "posting"], "direct_answer_score": 23, "player_intent_score": 18}}}`

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

I walk a few steps along the muddy gate line and listen

### GM

You pace alongside the muddy line where threadbare watchers and refugees cluster, tuning your ears to the murmurs and muted complaints. The rain splatters the grimy ground, mixing with the scent of damp cloth and woodsmoke. Among the crowd, soft, anxious whispers drift—talk of the missing patrol, concerns about tightened caravan delays to the east, and murmurings of the harsh new curfew rules pinned firmly on the notice board. However, no clear new intelligence reaches you amid the indistinct voices and the persistent drizzle. As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 114, "text_preview": "You pace alongside the muddy line where threadbare watchers and refugees cluster, tuning your ears to the murmurs and muted complaints. The rain splatters the g"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["along", "gate", "line", "listen", "muddy", "steps", "walk"], "gm_terms": ["along", "alongside", "amid", "among", "anxious", "board", "caravan", "clear", "cloth", "cluster", "complaints", "concerns", "crowd", "curfew", "damp", "delays", "drift", "drizzle", "ears", "east"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 17

### Player

I look toward the notice board again.

### GM

The notice board at the Cinderwatch Gate District remains firmly posted with the same announcements: updated taxes and curfew rules alongside a warning about the missing patrol. The roster board clearly notes the missing patrol was last seen scheduled along the northwest mud track past the crates. Nearby, the gate serjeant continues to monitor and update the roster without new patrol assignments appearing.

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
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 63, "text_preview": "The notice board at the Cinderwatch Gate District remains firmly posted with the same announcements: updated taxes and curfew rules alongside a warning about th"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["again", "board", "look", "notice", "toward"], "gm_terms": ["along", "alongside", "announcements", "appearing", "assignments", "board", "cinderwatch", "clearly", "continues", "crates", "curfew", "district", "firmly", "gate", "last", "missing", "monitor", "mud", "nearby", "new"], "direct_answer_score": 23, "player_intent_score": 18}}}`
