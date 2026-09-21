# Validation Evidence: retrospective_playability_20260917T221002Z

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Four fixed playability scenarios that originally produced overall PASS results despite preserved semantic failures.
Runtime path: In-process POST /api/chat playability runner with campaign resets.
GM boundary: Configured live AI-GM runtime preserved by the original observability campaign.
Player inputs: Fixed scripted prompts; no reactive selection. Classification uncertainty is explicit where normality was not reviewed.
Runs / turns: 4 / 7
Automated conclusion: Historical evaluator schema v2 marked every preserved turn overall PASS. Later human review rejected five interactions, and four known failure shapes entered the accepted semantic calibration corpus.
Result counts: `{"PASS": 7}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_0`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`
Run / turn: `20260917T221002Z_p3_logical_escalation` / `0`
Input classification: `runtime_discovered, representative_player_behavior, classification_uncertain_human_review`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> What do I see at the gate?

GM output (exact):

> The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": null}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 78}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 78}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "I press again: what is actually posted on the notice?", "next_selection_reason": "fixed_script_next_turn"}`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Evaluator disagreement: `{"calibration_reference": null, "historical_result_rewritten": false, "human_status": "UNREVIEWED", "later_evaluator_result": null, "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": false, "present": false}`

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

Example: `historical:20260917T221002Z:p2_respect_intent:turn_1`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p2_respect_intent/transcript.json`
Run / turn: `20260917T221002Z_p2_respect_intent` / `1`
Input classification: `runtime_discovered, boundary_case, classification_uncertain_human_review`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> Who exactly was seen near the dye vats?

GM output (exact):

> "From what I gathered, a ragged, quick-footed figure was spotted lingering near the dye vats just before the patrol disappeared. No one caught a name or face, but the crowd talks of a shadowy presence—someone who might be tied to the thief you asked about earlier." "If you want to know more, you’d do well to check by the old milestone where the patrol was last seen."

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": null}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 78}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 78}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "fixed_script_complete"}`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Evaluator disagreement: `{"calibration_reference": null, "historical_result_rewritten": false, "human_status": "UNREVIEWED", "later_evaluator_result": null, "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": false, "present": false}`

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `historical:20260917T221002Z:p1_direct_answer:turn_0`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`
Run / turn: `20260917T221002Z_p1_direct_answer` / `0`
Input classification: `runtime_discovered, representative_player_behavior`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> Who commands the watch here?

GM output (exact):

> Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_001_unanswered_direct_question"}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 69}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 69}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "Who stole the relic from the chapel?", "next_selection_reason": "fixed_script_next_turn"}`
Human review: `HUMAN_REJECTED` - The watch-command question was not meaningfully answered.
Evaluator disagreement: `{"calibration_reference": "case_001_unanswered_direct_question", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `historical:20260917T221002Z:p1_direct_answer:turn_1`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`
Run / turn: `20260917T221002Z_p1_direct_answer` / `1`
Input classification: `runtime_discovered, boundary_case`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> Who stole the relic from the chapel?

GM output (exact):

> Tavern Runner says, "No. I cannot answer that from what."

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_002_broken_refusal_non_answer"}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 67}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 67}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "fixed_script_complete"}`
Human review: `HUMAN_REJECTED` - The reply is a broken refusal/non-answer.
Evaluator disagreement: `{"calibration_reference": "case_002_broken_refusal_non_answer", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

Example: `historical:20260917T221002Z:p1_direct_answer:turn_0`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`
Run / turn: `20260917T221002Z_p1_direct_answer` / `0`
Input classification: `runtime_discovered, representative_player_behavior`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> Who commands the watch here?

GM output (exact):

> Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_001_unanswered_direct_question"}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 69}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 69}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "Who stole the relic from the chapel?", "next_selection_reason": "fixed_script_next_turn"}`
Human review: `HUMAN_REJECTED` - The watch-command question was not meaningfully answered.
Evaluator disagreement: `{"calibration_reference": "case_001_unanswered_direct_question", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_1`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`
Run / turn: `20260917T221002Z_p3_logical_escalation` / `1`
Input classification: `runtime_discovered, boundary_case, stress_probe`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> I press again: what is actually posted on the notice?

GM output (exact):

> Tavern Runner mutters,

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_003_truncated_output"}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 67}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 67}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "fixed_script_complete"}`
Human review: `HUMAN_REJECTED` - The output is truncated and does not fulfill the notice observation.
Evaluator disagreement: `{"calibration_reference": "case_003_truncated_output", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### Stress Probe

Selection: first example labeled stress_probe

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_1`
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`
Run / turn: `20260917T221002Z_p3_logical_escalation` / `1`
Input classification: `runtime_discovered, boundary_case, stress_probe`
Selection rationale: fixed_script_position; no reactive policy rationale existed

Player input (exact):

> I press again: what is actually posted on the notice?

GM output (exact):

> Tavern Runner mutters,

Automated result: `PASS`
Mandatory gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_003_truncated_output"}`
Diagnostic result: `{"passed": true, "rating": "acceptable", "score": 67}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"passed": true, "rating": "acceptable", "score": 67}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "fixed_script_complete"}`
Human review: `HUMAN_REJECTED` - The output is truncated and does not fulfill the notice observation.
Evaluator disagreement: `{"calibration_reference": "case_003_truncated_output", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

## All Evaluator Disagreements

### historical:20260917T221002Z:p1_direct_answer:turn_0

Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`
Player classification: `runtime_discovered, representative_player_behavior`
Player (exact): Who commands the watch here?
GM (exact): Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.
Original automated result: `PASS`
Original gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_001_unanswered_direct_question"}`
Human review: `HUMAN_REJECTED` - The watch-command question was not meaningfully answered.
History: `{"calibration_reference": "case_001_unanswered_direct_question", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### historical:20260917T221002Z:p1_direct_answer:turn_1

Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`
Player classification: `runtime_discovered, boundary_case`
Player (exact): Who stole the relic from the chapel?
GM (exact): Tavern Runner says, "No. I cannot answer that from what."
Original automated result: `PASS`
Original gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_002_broken_refusal_non_answer"}`
Human review: `HUMAN_REJECTED` - The reply is a broken refusal/non-answer.
History: `{"calibration_reference": "case_002_broken_refusal_non_answer", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### historical:20260917T221002Z:p2_respect_intent:turn_0

Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p2_respect_intent/transcript.json`
Player classification: `runtime_discovered, representative_player_behavior`
Player (exact): Tell me about the thief.
GM (exact): Tavern Runner says, "No. I cannot answer that from what."
Original automated result: `PASS`
Original gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_002_broken_refusal_non_answer"}`
Human review: `HUMAN_REJECTED` - The reply is a broken refusal/non-answer.
History: `{"calibration_reference": "case_002_broken_refusal_non_answer", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### historical:20260917T221002Z:p3_logical_escalation:turn_1

Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`
Player classification: `runtime_discovered, boundary_case, stress_probe`
Player (exact): I press again: what is actually posted on the notice?
GM (exact): Tavern Runner mutters,
Original automated result: `PASS`
Original gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_003_truncated_output"}`
Human review: `HUMAN_REJECTED` - The output is truncated and does not fulfill the notice observation.
History: `{"calibration_reference": "case_003_truncated_output", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

### historical:20260917T221002Z:p4_immersion:turn_0

Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p4_immersion/transcript.json`
Player classification: `runtime_discovered, representative_player_behavior`
Player (exact): I glance at the notice.
GM (exact): The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".
Original automated result: `PASS`
Original gates: `{"availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2", "later_calibration_case_id": "case_004_observation_not_fulfilled"}`
Human review: `HUMAN_REJECTED` - The notice observation is redirected into a menu-like instruction instead of being fulfilled.
History: `{"calibration_reference": "case_004_observation_not_fulfilled", "historical_result_rewritten": false, "human_status": "HUMAN_REJECTED", "later_evaluator_result": "FAIL", "original_overall_result": "PASS", "original_semantic_result": null, "policy_changed_after_source_run": true, "present": true}`

## Missing Concepts / Future Capabilities

- **mandatory_noncompensatory_semantic_gates**: Historical aggregate PASS compensated for failed intent axes and malformed output. This capability was added later; historical results remain unchanged here. Status: LATER_CALIBRATED_SEPARATELY.

## What This Does Not Prove

- This retrospective proves what the preserved transcripts and historical evaluator reported; it does not reproduce the run.
- Historical evaluator schema v2 had no semantic_result or mandatory-gate fields, which are reported as unavailable rather than reconstructed.
- Current calibration references are annotations beside, not replacements for, historical PASS results.
- The fixed prompts do not establish reactive or representative-human behavior.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
