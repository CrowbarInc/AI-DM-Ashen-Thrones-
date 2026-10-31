# Reactive Simulation: patrol_knowledge

Strategy: reactive
Seed: 1701
Objective: Determine where the missing patrol was last seen without granting an NPC impossible knowledge.
Termination: objective_resolved
Valid Run: True

## Turn 1

Player: Runner, where exactly was the missing patrol last seen?

Decision reason: `initial_objective:Determine where the missing patrol was last seen without granting an NPC impossible knowledge.`

GM: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

Semantic result: `PASS`

Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 18, "text_preview": "Tavern Runner mutters, \"Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["crates", "footprints", "heard", "muddy", "mutters", "near", "northwest", "patrol", "runner", "tavern", "vanished", "word"], "player_intent_score": 23, "player_terms": ["exactly", "last", "missing", "patrol", "runner", "seen", "where"], "request_kind": "question"}, "passed": true, "reason_codes": [], "status": "PASS"}}`

Diagnostic quality: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 19, "player_intent": 23}, "passed": true, "rating": "strong", "score": 82}`

Classification: `E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED`
