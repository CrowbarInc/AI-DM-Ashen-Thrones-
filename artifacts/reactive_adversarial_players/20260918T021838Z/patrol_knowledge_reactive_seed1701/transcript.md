# Reactive Simulation: patrol_knowledge

Strategy: reactive
Seed: 1701
Objective: Determine where the missing patrol was last seen without granting an NPC impossible knowledge.
Termination: legitimate_boundary
Valid Run: True

## Turn 1

Player: Runner, where exactly was the missing patrol last seen?

Decision reason: `initial_objective:Determine where the missing patrol was last seen without granting an NPC impossible knowledge.`

GM: Tavern Runner says, "No. I cannot answer that from what."

Semantic result: `FAIL`

Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what.\""}, "passed": false, "reason_codes": ["malformed_output:broken_refusal_fragment"], "status": "FAIL"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["answer", "cannot", "runner", "says", "tavern", "what"], "player_intent_score": 23, "player_terms": ["exactly", "last", "missing", "patrol", "runner", "seen", "where"], "request_kind": "question"}, "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "status": "FAIL"}}`

Diagnostic quality: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 19, "player_intent": 23}, "passed": true, "rating": "strong", "score": 82}`

Classification: `A_KNOWN_EVALUATOR_DETECTED_FAILURE`

## Turn 2

Player: One bounded answer: last reliable location, source, and uncertainty.

Decision reason: `repeat_after_malformed_output`

GM: "From what I heard," the tavern runner lowers their voice, glancing around nervously, "the missing patrol was last seen near some muddy footprints northwest of the crates, just outside the gate. But no one knows exactly what happened after that."

Semantic result: `PASS`

Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 40, "text_preview": "\"From what I heard,\" the tavern runner lowers their voice, glancing around nervously, \"the missing patrol was last seen near some muddy footprints northwest of "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["after", "around", "crates", "exactly", "footprints", "gate", "glancing", "happened", "heard", "knows", "last", "lowers", "missing", "muddy", "near", "nervously", "northwest", "one", "outside", "patrol"], "player_intent_score": 18, "player_terms": ["answer", "bounded", "last", "location", "reliable", "source", "uncertainty"], "request_kind": "action_or_statement"}, "passed": true, "reason_codes": [], "status": "PASS"}}`

Diagnostic quality: `{"axis_scores": {"direct_answer": 23, "immersion": 23, "logical_escalation": 23, "player_intent": 18}, "passed": true, "rating": "strong", "score": 87}`

Classification: `E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED`
