# R2-MT03 — runner_rumor_decline_path

Objective: Talk to the tavern runner about stew and street rumor, declining the official patrol path.
Family: multi_turn_arc
Turns: 7
Completed: True

## Turn 1

### Player

I glance around for someone selling food or gossip rather than official business.

### GM

You glance around for someone selling food or gossip rather than official business, and you get an immediate read on what is there. The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 56, "text_preview": "You glance around for someone selling food or gossip rather than official business, and you get an immediate read on what is there. The pause snaps when a nearb"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "business", "food", "glance", "gossip", "official", "rather", "selling", "someone"], "gm_terms": ["around", "before", "board", "business", "butt", "choose", "food", "gate", "get", "glance", "gossip", "guard", "he", "his", "immediate", "instead", "nearby", "official", "one", "pause"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 2

### Player

I walk over to the tavern runner. "What's in the stew, and what rumors are worth a coin?"

### GM

Tavern Runner mutters,

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 76, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "FAIL", "passed": false, "reason_codes": ["malformed_output:dangling_speech_attribution"], "evidence": {"gm_word_count": 3, "text_preview": "Tavern Runner mutters,"}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "evidence": {"request_kind": "question", "player_terms": ["coin", "over", "rumors", "runner", "stew", "tavern", "walk", "what", "what's", "worth"], "gm_terms": ["mutters", "runner", "tavern"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 3

### Player

I'm not here for the missing patrol. Tell me what travelers are actually talking about.

### GM

Tavern Runner mutters, "Word is, follow the missing patrol rumor."

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit; social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}, {"clue_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 82, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner mutters, \"Word is, follow the missing patrol rumor.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["actually", "missing", "patrol", "talking", "tell", "travelers", "what"], "gm_terms": ["follow", "missing", "mutters", "patrol", "rumor", "runner", "tavern", "word"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 4

### Player

If you were going to point me at that notice board, don't. I want street rumor, not the posted warning.

### GM

Tavern Runner mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `social_probe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "tavern_runner", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit; social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}, {"clue_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 78, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 19, "text_preview": "Tavern Runner mutters, \"Word is, the missing patrol was last seen taking the northwest mud track past the crates.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:player_action_or_request_lost"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["board", "don't", "going", "notice", "point", "posted", "rumor", "street", "want", "warning"], "gm_terms": ["crates", "last", "missing", "mud", "mutters", "northwest", "past", "patrol", "runner", "seen", "taking", "tavern", "track", "word"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 5

### Player

See that ragged stranger hanging back from the queue? What's their story?

### GM

Tavern Runner tightens their jaw.

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit; social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}, {"clue_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 67, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 5, "text_preview": "Tavern Runner tightens their jaw."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "evidence": {"request_kind": "question", "player_terms": ["back", "hanging", "queue", "ragged", "story", "stranger", "what's"], "gm_terms": ["jaw", "runner", "tavern", "tightens"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 6

### Player

You mentioned travelers talking. Repeat the most useful thing you already told me.

### GM

"Like I said before," the tavern runner mutters, "the missing patrol was last spotted near some muddy footprints northwest of the crates by the gate. If you're looking for real travelers' talk beyond that, these parts are mostly fixated on that disappearance right now."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `social_probe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "tavern_runner", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit; social"}, {"id": "narration_ctx_frontier_gate_like_i_said_before_the_tavern_runner_mutters_the", "title": "\"like i said before,\" the tavern runner mutters, \"the missing patrol was last spotted near some muddy footprints northwest of the crates", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}, {"clue_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 78, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "\"Like I said before,\" the tavern runner mutters, \"the missing patrol was last spotted near some muddy footprints northwest of the crates by the gate. If you're "}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:player_action_or_request_lost"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["already", "mentioned", "most", "repeat", "talking", "thing", "told", "travelers", "useful"], "gm_terms": ["before", "beyond", "crates", "disappearance", "fixated", "footprints", "gate", "last", "like", "looking", "missing", "mostly", "muddy", "mutters", "near", "northwest", "now", "parts", "patrol", "real"], "direct_answer_score": 23, "player_intent_score": 9}}}`

## Turn 7

### Player

I'll stay at the gate a bit longer instead of entering Cinderwatch.

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
- interaction_after: `{"active_interaction_target_id": "gate_guard", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit; social"}, {"id": "narration_ctx_frontier_gate_like_i_said_before_the_tavern_runner_mutters_the", "title": "\"like i said before,\" the tavern runner mutters, \"the missing patrol was last spotted near some muddy footprints northwest of the crates", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}, {"clue_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "lead_frontier_gate_exit_follow_the_missing_patrol_rumor", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 83, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "Gate Guard mutters, \"Word is, captain Thoran commands the gate watch tonight.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["cinderwatch", "entering", "gate", "i'll", "instead", "longer", "stay"], "gm_terms": ["captain", "commands", "gate", "guard", "mutters", "thoran", "tonight", "watch", "word"], "direct_answer_score": 23, "player_intent_score": 18}}}`
