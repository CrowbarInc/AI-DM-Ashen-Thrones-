# R2-P3 — p3_logical_escalation

Objective: Observe the gate, then press for what is posted on the notice.
Family: round1_comparison
Turns: 2
Completed: True

## Turn 1

### Player

What do I see at the gate?

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
- interaction_after: `{"active_interaction_target_id": "gate_guard", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "captain_thoran_watch", "title": "Captain Thoran commands the gate watch tonight.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 78, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "Gate Guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["gate", "what"], "gm_terms": ["answer", "enough", "gate", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 18}}}`

## Turn 2

### Player

I press again: what is actually posted on the notice?

### GM

Gate Guard says, "I do not know enough to answer that."

### Evidence

- semantic_result: `FAIL`
- api_ok: `True`
- resolution.kind: `investigate`
- parsed_intent: `null`
- normalized: `null`
- classification: `null`
- resolution_path: `null`
- interaction_after: `{"active_interaction_target_id": "gate_guard", "active_interaction_kind": "social", "interaction_mode": "social", "engagement_level": "engaged"}`
- scene: `frontier_gate` -> `frontier_gate`
- lead_registry: `[{"id": "captain_thoran_watch", "title": "Captain Thoran commands the gate watch tonight.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}, {"id": "minlead_exit_frontier_gate_old_milestone", "title": "Follow the missing patrol rumor", "type": "investigation", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "social"}, {"id": "notice_patrol_route", "title": "The missing patrol was last seen taking the northwest mud track past the crates.", "type": "rumor", "lifecycle": "discovered", "status": "active", "next_step": "", "discovery_source": "clue_explicit"}]`
- pending_leads: `[{"clue_id": "minlead_exit_frontier_gate_old_milestone", "text": "Follow the missing patrol rumor", "authoritative_lead_id": "minlead_exit_frontier_gate_old_milestone", "leads_to_scene": "old_milestone"}]`
- world_npcs: `[{"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "status": null}, {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "status": null}, {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "status": null}]`
- final_emission: `{}`
- playability_overall: `{"score": 58, "rating": "acceptable", "passed": false, "semantic_result": "FAIL", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 11, "text_preview": "Gate Guard says, \"I do not know enough to answer that.\""}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "question", "player_terms": ["actually", "again", "notice", "posted", "press", "what"], "gm_terms": ["answer", "enough", "gate", "guard", "know", "says"], "direct_answer_score": 17, "player_intent_score": 9}}}`
