# Simulation Run: 20260917T221002Z_p3_logical_escalation

Scenario: p3_logical_escalation
Objective: Logical-escalation axis: observation then pressed detail on the same topic.
Player: fixed scripted natural-language prompts
Transport: in-process TestClient `/api/chat`
Seed: none
Started: 2026-09-17T22:10:22.592189+00:00
Finished: 2026-09-17T22:10:34.418633+00:00
Result: PASS

## Turn 1

### PLAYER

What do I see at the gate?

### GM

The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".

### Runtime Notes

- api_ok: `True`
- api_error: `None`
- resolution_kind: `observe`
- dead_turn_visibility: `{"dead_turn_class": "none", "dead_turn_detected": false, "dead_turn_reason_codes": [], "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "manual_test_valid": true, "run_valid": true, "turn_index": 0, "turn_number_one_based": 1, "validation_playable": true}`
- playability_overall: `{"passed": true, "rating": "acceptable", "score": 78}`

## Turn 2

### PLAYER

I press again: what is actually posted on the notice?

### GM

Tavern Runner mutters,

### Runtime Notes

- api_ok: `True`
- api_error: `None`
- resolution_kind: `question`
- dead_turn_visibility: `{"dead_turn_class": "none", "dead_turn_detected": false, "dead_turn_reason_codes": [], "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "manual_test_valid": true, "run_valid": true, "turn_index": 1, "turn_number_one_based": 2, "validation_playable": true}`
- playability_overall: `{"passed": true, "rating": "acceptable", "score": 67}`

# Evaluation

Reported Result: PASS

The result above is copied from the existing playability evaluator: `summary.overall.passed` on the final turn, after existing dead-turn/gameplay validation exclusions are applied. No new semantic quality metric is applied by this transcript.

Overall: `{"passed": true, "rating": "acceptable", "score": 67}`

Failures:
- player_intent: weak (9/25).
- player_intent: GM misses obvious player topic anchors.
