# Simulation Run: 20260918T011644Z_p4_immersion

Scenario: p4_immersion
Objective: Immersion axis: minimal diegetic beat (GM text comes from the engine).
Player: fixed scripted natural-language prompts
Transport: in-process TestClient `/api/chat`
Seed: none
Started: 2026-09-18T01:17:14.181837+00:00
Finished: 2026-09-18T01:17:22.713322+00:00
Semantic Result: PASS

# Result

Semantic Result: PASS

Mandatory Gates:
- malformed_output: `PASS` ()
- player_intent_addressed: `PASS` ()

Diagnostic Quality: `{"axis_scores": {"direct_answer": 23, "immersion": 24, "logical_escalation": 19, "player_intent": 9}, "passed": true, "rating": "acceptable", "score": 75}`

## Turn 1

### PLAYER

I glance at the notice.

### GM

A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain watches with hard, tired discipline, while Tavern Runner trades hot stew and rumors near the rain barrel.

### Runtime Notes

- api_ok: `True`
- api_error: `None`
- resolution_kind: `observe`
- dead_turn_visibility: `{"dead_turn_class": "none", "dead_turn_detected": false, "dead_turn_reason_codes": [], "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "manual_test_valid": true, "run_valid": true, "turn_index": 0, "turn_number_one_based": 1, "validation_playable": true}`
- playability_overall: `{"diagnostic_quality_rating": "acceptable", "passed": true, "rating": "acceptable", "score": 75, "semantic_result": "PASS"}`
- semantic_result: `"PASS"`
- mandatory_gates: `{"malformed_output": {"evidence": {"gm_word_count": 44, "text_preview": "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["along", "barrel", "board", "captain", "cluster", "crowd", "discipline", "eye", "gate", "guard", "hard", "hot", "keeps", "line", "manages", "muddy", "near", "one", "rain", "refugees"], "player_intent_score": 9, "player_terms": ["glance", "notice"], "request_kind": "observation"}, "passed": true, "reason_codes": [], "status": "PASS"}}`

# Evaluation

Reported Result: PASS

The result above is copied from the playability evaluator's semantic authority. Mandatory gate failures are not overridden by diagnostic quality scores.

Overall: `{"diagnostic_quality_rating": "acceptable", "passed": true, "rating": "acceptable", "score": 75, "semantic_result": "PASS"}`
Mandatory Gates: `{"malformed_output": {"evidence": {"gm_word_count": 44, "text_preview": "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare watchers and refugees cluster along the muddy gate line. Guard Captain "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["along", "barrel", "board", "captain", "cluster", "crowd", "discipline", "eye", "gate", "guard", "hard", "hot", "keeps", "line", "manages", "muddy", "near", "one", "rain", "refugees"], "player_intent_score": 9, "player_terms": ["glance", "notice"], "request_kind": "observation"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic Quality: `{"axis_scores": {"direct_answer": 23, "immersion": 24, "logical_escalation": 19, "player_intent": 9}, "passed": true, "rating": "acceptable", "score": 75}`

Failures:
- player_intent: weak (9/25).
- player_intent: GM misses obvious player topic anchors.
