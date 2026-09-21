# R2-P4 — p4_immersion

Objective: Glance at the notice and receive an observation of that object.
Family: round1_comparison
Turns: 1
Completed: True

## Turn 1

### Player

I glance at the notice.

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
- playability_overall: `{"score": 75, "rating": "acceptable", "passed": true, "semantic_result": "PASS", "diagnostic_quality_rating": "acceptable"}`
- mandatory_gates: `{"malformed_output": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"gm_word_count": 44, "text_preview": "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain "}}, "player_intent_addressed": {"status": "PASS", "passed": true, "reason_codes": [], "evidence": {"request_kind": "observation", "player_terms": ["glance", "notice"], "gm_terms": ["along", "barrel", "board", "captain", "cluster", "crowd", "discipline", "eye", "gate", "guard", "hard", "hot", "keeps", "line", "manages", "muddy", "near", "one", "rain", "refugees"], "direct_answer_score": 23, "player_intent_score": 9}}}`
