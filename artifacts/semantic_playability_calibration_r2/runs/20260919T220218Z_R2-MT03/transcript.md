# R2-MT03 — runner_rumor_decline_path

Objective: Talk to the tavern runner about stew and street rumor, declining the official patrol path.
Family: multi_turn_arc
Turns: 7
Completed: True

## Turn 1

### Player

I glance around for someone selling food or gossip rather than official business.

### GM

Amid the steady rain pattering against soot-dark stone, your gaze shifts past the official gate guard and serjeant to the edge of the crowd where a tavern runner hawks hot stew and whispered tidings for coin. The runner’s eager cries slice through the clamorous gate district, a sharp contrast to the heavy presence of guards controlling the muddy chokepoint. Nearby, one figure in threadbare clothes lingers unusually still, watching faces and packs more than the queue, while ragged refugees and travelers edge closer, their eyes wary. Though chatter about taxes and curfew bubbles around, the tavern runner’s murmurs seem hungrier for stories than official business, offering a promising source of gossip if you dare approach.

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
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 118, "text_preview": "Amid the steady rain pattering against soot-dark stone, your gaze shifts past the official gate guard and serjeant to the edge of the crowd where a tavern runne"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["around", "business", "food", "glance", "gossip", "official", "rather", "selling", "someone"], "gm_terms": ["against", "amid", "approach", "around", "bubbles", "business", "chatter", "chokepoint", "clamorous", "closer", "clothes", "coin", "contrast", "controlling", "cries", "crowd", "curfew", "dare", "dark", "district"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 2

### Player

I walk over to the tavern runner. "What's in the stew, and what rumors are worth a coin?"

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 76, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "FAIL", "passed": false, "reason_codes": ["malformed_output:broken_refusal_fragment"], "evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "evidence": {"request_kind": "question", "player_terms": ["coin", "over", "rumors", "runner", "stew", "tavern", "walk", "what", "what's", "worth"], "gm_terms": ["answer", "cannot", "runner", "says", "tavern", "what"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 3

### Player

I'm not here for the missing patrol. Tell me what travelers are actually talking about.

### GM

"Travelers around here mostly grumble about the new taxes and stricter curfew rules," the tavern runner murmurs, voice low and cautious. "But the quiet talk, what slips through the cracks, is how the Ash Compact census delays have snarled the eastern caravan choke point. Beyond that, whispers brush against darker rumors—shadows moving in the gate district, uneasy eyes watching the crowd, and a certain threadbare figure who doesn’t quite fit."

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "narration_ctx_frontier_gate_travelers_around_here_mostly_grumble_about_the_n", "title": "\"travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 88, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 72, "text_preview": "\"Travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious. \"But the quiet talk, wh"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["actually", "missing", "patrol", "talking", "tell", "travelers", "what"], "gm_terms": ["against", "around", "ash", "beyond", "brush", "caravan", "cautious", "census", "certain", "choke", "compact", "cracks", "crowd", "curfew", "darker", "delays", "district", "doesn", "eastern", "eyes"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 4

### Player

If you were going to point me at that notice board, don't. I want street rumor, not the posted warning.

### GM

Tavern Runner mutters,

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "narration_ctx_frontier_gate_travelers_around_here_mostly_grumble_about_the_n", "title": "\"travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 70, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "FAIL", "passed": false, "reason_codes": ["malformed_output:dangling_speech_attribution"], "evidence": {"gm_word_count": 3, "text_preview": "Tavern Runner mutters,"}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["board", "don't", "going", "notice", "point", "posted", "rumor", "street", "want", "warning"], "gm_terms": ["mutters", "runner", "tavern"], "direct_answer_score": 20, "player_intent_score": 9}}}`

## Turn 5

### Player

See that ragged stranger hanging back from the queue? What's their story?

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
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "narration_ctx_frontier_gate_travelers_around_here_mostly_grumble_about_the_n", "title": "\"travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 67, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "FAIL", "passed": false, "reason_codes": ["malformed_output:broken_refusal_fragment"], "evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what.\""}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "evidence": {"request_kind": "question", "player_terms": ["back", "hanging", "queue", "ragged", "story", "stranger", "what's"], "gm_terms": ["answer", "cannot", "runner", "says", "tavern", "what"], "direct_answer_score": 17, "player_intent_score": 9}}}`

## Turn 6

### Player

You mentioned travelers talking. Repeat the most useful thing you already told me.

### GM

"Travelers around here mostly grumble about the new taxes and stricter curfew rules," the tavern runner murmurs, voice low and cautious. "But beneath the grumbling, there's quiet talk of shadows creeping through the gate district—uneasy glances, people vanishing, and a threadbare figure who doesn't quite belong watching from the edges."

### Evidence

- semantic_result: `PASS`
- api_ok: `True`
- resolution.kind: `social_probe`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "tavern_runner", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "narration_ctx_frontier_gate_travelers_around_here_mostly_grumble_about_the_n", "title": "\"travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 87, "rating": "strong", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "strong"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 51, "text_preview": "\"Travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious. \"But beneath the grumbl"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "action_or_statement", "player_terms": ["already", "mentioned", "most", "repeat", "talking", "thing", "told", "travelers", "useful"], "gm_terms": ["around", "belong", "beneath", "cautious", "creeping", "curfew", "district", "doesn't", "edges", "figure", "gate", "glances", "grumble", "grumbling", "low", "mostly", "murmurs", "new", "people", "quiet"], "direct_answer_score": 23, "player_intent_score": 18}}}`

## Turn 7

### Player

I'll stay at the gate a bit longer instead of entering Cinderwatch.

### GM

You act on that move, and your position changes with that movement.

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `scene_transition`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": null, "active_interaction_kind": null, "interaction_mode": "none", "engagement_level": "none"}`
- scene: `frontier_gate` -> `market_quarter`
- lead_registry: `[{"id": "muddy_footprints_northwest", "title": "The runner heard the patrol vanished near muddy footprints northwest of the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "narration_ctx_frontier_gate_travelers_around_here_mostly_grumble_about_the_n", "title": "\"travelers around here mostly grumble about the new taxes and stricter curfew rules,\" the tavern runner murmurs, voice low and cautious", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 72, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 12, "text_preview": "You act on that move, and your position changes with that movement."}}, "player_intent_addressed": {"status": "FAIL", "passed": false, "reason_codes": ["intent_addressed:player_action_or_request_lost"], "evidence": {"request_kind": "action_or_statement", "player_terms": ["cinderwatch", "entering", "gate", "i'll", "instead", "longer", "stay"], "gm_terms": ["act", "changes", "move", "movement", "position"], "direct_answer_score": 23, "player_intent_score": 9}}}`
