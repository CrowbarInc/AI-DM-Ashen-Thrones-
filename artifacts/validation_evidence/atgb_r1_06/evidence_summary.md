# Validation Evidence: ATGB-R1-06

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Offline analysis of three preserved completed correction trials; no new executions
Runtime path: Historical direct game.api.chat production route; current pass JSON/source inspection only
GM boundary: Historical production interpretation, orchestration and final emission
Player inputs: Preserved fixed original and paraphrase inputs
Runs / turns: 3 / 3
Automated conclusion: B — Conditional causal proposal; not a repair measurement
Result counts: `{"FAIL": 3}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `L3`
Source: `artifacts/atgb/atgb_r1_03/L3/response.json`
Run / turn: `L3` / `2`
Input classification: `representative_player_behavior, boundary_case`
Selection rationale: Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.

Player input (exact):

> No, I was asking about the people, not the weather.

GM output (exact):

> Do you want a description of the people present at the gate district instead of the weather?

Automated result: `FAIL`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "FAIL"}, "interpretation": {"status": "PASS (correct subject; unnecessary clarification posture)"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "INDETERMINATE"}}`
Diagnostic result: `{"application_admissions": 1, "authority": "PASS", "authority_scope": "Exact attempted isolated execution only; not broad assurance.", "changed_domains": ["session", "log"], "clocks_after": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "clocks_before": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "completed_provider_responses": 1, "dispatched": 1, "end_to_end_ms": 3459.428, "estimated_cost": null, "evidence_selection": "FAIL", "failed_dispatches": 0, "final_response": "Do you want a description of the people present at the gate district instead of the weather?", "input_tokens": 2008, "interpretation": "PASS (correct subject; unnecessary clarification posture)", "note": "GM/CLARIFICATION, evidence_refs=[], no unresolved references. Bridge NEEDS_CLARIFICATION stops before revision gate. No mechanical misrouting observed, but repaired seam not exercised.", "output_tokens": 212, "pending_intentions": {"last_executed_intention": {"after": null, "before": null}, "pending_clarification": {"after": null, "before": null}, "pending_intention": {"after": null, "before": null}}, "player_input": "No, I was asking about the people, not the weather.", "response_adequacy": "FAIL", "routing": "INDETERMINATE", "session_changed_keys": ["conversational_context", "last_saved_at"], "total_tokens": 2220, "trace_functions": ["public_conversation_evidence", "request_interpretation", "interpret_production_turn", "_pending_revision_decision", "_communication_decision", "decision_from_interpretation_record", "_nonmutating_conversational_decision_response"], "trial": "L3", "turn_counter_after": 0, "turn_counter_before": 0, "world_changed_keys": []}`
Runtime validity: `"VALID live completed paraphrase"`
Continuation: `null`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Evaluator disagreement: `null`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `L3`
Source: `artifacts/atgb/atgb_r1_03/L3/response.json`
Run / turn: `L3` / `2`
Input classification: `representative_player_behavior, boundary_case`
Selection rationale: Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.

Player input (exact):

> No, I was asking about the people, not the weather.

GM output (exact):

> Do you want a description of the people present at the gate district instead of the weather?

Automated result: `FAIL`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "FAIL"}, "interpretation": {"status": "PASS (correct subject; unnecessary clarification posture)"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "INDETERMINATE"}}`
Diagnostic result: `{"application_admissions": 1, "authority": "PASS", "authority_scope": "Exact attempted isolated execution only; not broad assurance.", "changed_domains": ["session", "log"], "clocks_after": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "clocks_before": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "completed_provider_responses": 1, "dispatched": 1, "end_to_end_ms": 3459.428, "estimated_cost": null, "evidence_selection": "FAIL", "failed_dispatches": 0, "final_response": "Do you want a description of the people present at the gate district instead of the weather?", "input_tokens": 2008, "interpretation": "PASS (correct subject; unnecessary clarification posture)", "note": "GM/CLARIFICATION, evidence_refs=[], no unresolved references. Bridge NEEDS_CLARIFICATION stops before revision gate. No mechanical misrouting observed, but repaired seam not exercised.", "output_tokens": 212, "pending_intentions": {"last_executed_intention": {"after": null, "before": null}, "pending_clarification": {"after": null, "before": null}, "pending_intention": {"after": null, "before": null}}, "player_input": "No, I was asking about the people, not the weather.", "response_adequacy": "FAIL", "routing": "INDETERMINATE", "session_changed_keys": ["conversational_context", "last_saved_at"], "total_tokens": 2220, "trace_functions": ["public_conversation_evidence", "request_interpretation", "interpret_production_turn", "_pending_revision_decision", "_communication_decision", "decision_from_interpretation_record", "_nonmutating_conversational_decision_response"], "trial": "L3", "turn_counter_after": 0, "turn_counter_before": 0, "world_changed_keys": []}`
Runtime validity: `"VALID live completed paraphrase"`
Continuation: `null`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Evaluator disagreement: `null`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

No example observed in this campaign.

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

No example observed in this campaign.

### Stress Probe

Selection: first example labeled stress_probe

No example observed in this campaign.

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities

- **Distinct conversational correction and genuine GM clarification need**: Three preserved interpretations understand the corrected subject and redundantly confirm it. Status: Proposed clarification within existing owner; not implemented.

## What This Does Not Prove

- All runtime behavior is historical; zero new calls or gameplay tests.
- Human review UNREVIEWED; historical criteria judgments preserved.
- No measured repair benefit or independent generalization.
- Raw R1-03 L3 contradicts the earlier claim that revision guard was not reached.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
