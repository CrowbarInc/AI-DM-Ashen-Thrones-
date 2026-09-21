# Reactive Simulation: patrol_knowledge

Strategy: adversarial
Seed: 1701
Objective: Determine where the missing patrol was last seen without granting an NPC impossible knowledge.
Termination: legitimate_boundary
Valid Run: True

## Turn 1

Player: Runner, where exactly was the missing patrol last seen?

Decision reason: `initial_objective:Determine where the missing patrol was last seen without granting an NPC impossible knowledge.`

GM: Tavern Runner grimaces. "Not something I can say here."

Semantic result: `FAIL`

Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 9, "text_preview": "Tavern Runner grimaces. \"Not something I can say here.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["grimaces", "runner", "say", "something", "tavern"], "player_intent_score": 23, "player_terms": ["exactly", "last", "missing", "patrol", "runner", "seen", "where"], "request_kind": "question"}, "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "status": "FAIL"}}`

Diagnostic quality: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 19, "player_intent": 23}, "passed": true, "rating": "strong", "score": 82}`

Classification: `A_KNOWN_EVALUATOR_DETECTED_FAILURE`
