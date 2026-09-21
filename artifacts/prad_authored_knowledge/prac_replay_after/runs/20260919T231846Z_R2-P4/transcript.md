# R2-P4 — p4_immersion

Objective: Glance at the notice and receive an observation of that object.
Family: round1_comparison
Turns: 1
Completed: True

## Turn 1

### Player

I glance at the notice.

### GM

The missing patrol was last seen taking the northwest mud track past the crates. The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".

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
- playability_overall: `{"score": 75, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 47, "text_preview": "The missing patrol was last seen taking the northwest mud track past the crates. The pause snaps when a nearby guard points with his spear-butt instead of waiti"}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["glance", "notice"], "gm_terms": ["before", "board", "butt", "choose", "crates", "gate", "guard", "he", "his", "instead", "last", "missing", "mud", "nearby", "northwest", "one", "past", "patrol", "pause", "pick"], "direct_answer_score": 23, "player_intent_score": 9}}}`
