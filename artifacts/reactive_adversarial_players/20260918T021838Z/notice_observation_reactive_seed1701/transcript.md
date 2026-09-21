# Reactive Simulation: notice_observation

Strategy: reactive
Seed: 1701
Objective: Read the concrete information posted on the gate notice.
Termination: objective_resolved
Valid Run: True

## Turn 1

Player: I inspect the notice closely and read what is posted.

Decision reason: `initial_objective:Read the concrete information posted on the gate notice.`

GM: The notice board lists taxes, curfew rules, and a warning about a missing patrol sharpens when you look again, and ash compact census delays have tightened the eastern caravan choke point still competes for notice.

Semantic result: `PASS`

Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 35, "text_preview": "The notice board lists taxes, curfew rules, and a warning about a missing patrol sharpens when you look again, and ash compact census delays have tightened the "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["again", "ash", "board", "caravan", "census", "choke", "compact", "competes", "curfew", "delays", "eastern", "lists", "look", "missing", "notice", "patrol", "point", "rules", "sharpens", "still"], "player_intent_score": 18, "player_terms": ["closely", "inspect", "notice", "posted", "read", "what"], "request_kind": "observation"}, "passed": true, "reason_codes": [], "status": "PASS"}}`

Diagnostic quality: `{"axis_scores": {"direct_answer": 23, "immersion": 22, "logical_escalation": 19, "player_intent": 18}, "passed": true, "rating": "strong", "score": 82}`

Classification: `E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED`
