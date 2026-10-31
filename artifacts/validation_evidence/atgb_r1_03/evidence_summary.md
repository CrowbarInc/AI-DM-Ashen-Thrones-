# Validation Evidence: atgb_r1_03

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Original S08.2, independent repeat, specified paraphrase and pending-action control attempt.
Runtime path: game.api.chat(ChatRequest); production live interpretation and emission; direct callable, not HTTP.
GM boundary: Actual provider calls for L1-L3; L4 invalid disabled interpretation.
Player inputs: Fixed authorized existing inputs; no exploratory scenarios.
Runs / turns: 4 / 4
Automated conclusion: D inconclusive: two provider failures, one inadequate live paraphrase, one invalid mutated control.
Result counts: `{"FAIL": 3, "INVALID_RUN": 1}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `L1`
Source: `artifacts/atgb/atgb_r1_03/L1/response.json`
Run / turn: `L1` / `2`
Input classification: `representative_player_behavior, boundary_case`
Selection rationale: Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.

Player input (exact):

> I meant the people, not the weather.

GM output (exact):

> I couldn't interpret that just now, so no gameplay action was taken.

Automated result: `FAIL`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "INDETERMINATE"}, "interpretation": {"status": "INDETERMINATE"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "INDETERMINATE"}}`
Diagnostic result: `{"application_admissions": 1, "authority": "PASS", "authority_scope": "Exact attempted isolated execution only; not broad assurance.", "changed_domains": ["log"], "clocks_after": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "clocks_before": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "completed_provider_responses": 0, "dispatched": 1, "end_to_end_ms": 1781.25, "estimated_cost": null, "evidence_selection": "INDETERMINATE", "failed_dispatches": 1, "final_response": "I couldn't interpret that just now, so no gameplay action was taken.", "input_tokens": null, "interpretation": "INDETERMINATE", "note": "Provider failure before model interpretation: APIConnectionError. Host fallback inadequate for the request; not evidence of a conversational model defect.", "output_tokens": null, "pending_intentions": {"last_executed_intention": {"after": null, "before": null}, "pending_clarification": {"after": null, "before": null}, "pending_intention": {"after": null, "before": null}}, "player_input": "I meant the people, not the weather.", "response_adequacy": "FAIL", "routing": "INDETERMINATE", "session_changed_keys": [], "total_tokens": null, "trace_functions": ["public_conversation_evidence", "request_interpretation", "interpret_production_turn"], "trial": "L1", "turn_counter_after": 0, "turn_counter_before": 0, "world_changed_keys": []}`
Runtime validity: `"INCOMPLETE provider failure"`
Continuation: `null`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Evaluator disagreement: `null`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `L4`
Source: `artifacts/atgb/atgb_r1_03/L4/response.json`
Run / turn: `L4` / `1`
Input classification: `synthetic_positive_control, boundary_case`
Selection rationale: Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.

Player input (exact):

> Instead, make that a question about the lamp.

GM output (exact):

> The action was resolved, but live narration was not requested because it would exceed the provider budget.

Automated result: `INVALID_RUN`
Mandatory gates: `{"authority": {"status": "FAIL (invalid live-control setup)"}, "evidence_selection": {"status": "INDETERMINATE (no live selection)"}, "interpretation": {"status": "INDETERMINATE (no model interpretation)"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "FAIL in disabled-interpretation fallback; live control INDETERMINATE"}}`
Diagnostic result: `{"application_admissions": 0, "authority": "FAIL (invalid live-control setup)", "authority_scope": "Exact attempted isolated execution only; not broad assurance.", "changed_domains": ["session", "world", "log"], "clocks_after": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 1, "unrest": 0}, "clocks_before": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "completed_provider_responses": 0, "dispatched": 0, "end_to_end_ms": 406.866, "estimated_cost": null, "evidence_selection": "INDETERMINATE (no live selection)", "failed_dispatches": 0, "final_response": "The action was resolved, but live narration was not requested because it would exceed the provider budget.", "input_tokens": 0, "interpretation": "INDETERMINATE (no model interpretation)", "note": "INVALID LIVE CONTROL: fixture import activated experiments/pr_dq/__init__.py environment defaults. Live interpretation skipped; generic resolution consumed a turn, cleared pending intention and updated factions. Narration refused before admission by existing input-token ceiling.", "output_tokens": 0, "pending_intentions": {"last_executed_intention": {"after": {"operation": null, "scene_id": "waystation_courtyard", "status": "executed", "target": null, "text": "Instead, make that a question about the lamp."}, "before": null}, "pending_clarification": {"after": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}, "before": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}}, "pending_intention": {"after": null, "before": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}}}, "player_input": "Instead, make that a question about the lamp.", "response_adequacy": "FAIL", "routing": "FAIL in disabled-interpretation fallback; live control INDETERMINATE", "session_changed_keys": ["_runtime_canonical_ctir_stamp_v1", "_runtime_canonical_ctir_v1", "_runtime_narration_plan_bundle_stamp_v1", "_runtime_narration_plan_bundle_v1", "_runtime_progression_nodes_fingerprint_v1", "bounded_improvisation", "character_name", "clocks", "conversational_context", "debug_traces", "discourse_focus", "emergent_actor_debug", "interaction_context", "interpretation_telemetry", "last_action_debug", "last_bounded_improvisation_promotion", "last_saved_at", "last_turn_response_policy", "lead_registry", "narration_temporal_provenance", "npc_runtime", "runtime_scene_overlays", "scene_runtime", "scene_state", "turn_counter"], "total_tokens": 0, "trace_functions": ["interpret_production_turn"], "trial": "L4", "turn_counter_after": 1, "turn_counter_before": 0, "world_changed_keys": ["event_log", "factions"]}`
Runtime validity: `"INVALID live control; test environment leakage"`
Continuation: `null`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Evaluator disagreement: `null`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

No example observed in this campaign.

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

Example: `L4`
Source: `artifacts/atgb/atgb_r1_03/L4/response.json`
Run / turn: `L4` / `1`
Input classification: `synthetic_positive_control, boundary_case`
Selection rationale: Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.

Player input (exact):

> Instead, make that a question about the lamp.

GM output (exact):

> The action was resolved, but live narration was not requested because it would exceed the provider budget.

Automated result: `INVALID_RUN`
Mandatory gates: `{"authority": {"status": "FAIL (invalid live-control setup)"}, "evidence_selection": {"status": "INDETERMINATE (no live selection)"}, "interpretation": {"status": "INDETERMINATE (no model interpretation)"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "FAIL in disabled-interpretation fallback; live control INDETERMINATE"}}`
Diagnostic result: `{"application_admissions": 0, "authority": "FAIL (invalid live-control setup)", "authority_scope": "Exact attempted isolated execution only; not broad assurance.", "changed_domains": ["session", "world", "log"], "clocks_after": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 1, "unrest": 0}, "clocks_before": {"danger": 0, "occult_instability": 0, "suspicion": 0, "time_pressure": 0, "unrest": 0}, "completed_provider_responses": 0, "dispatched": 0, "end_to_end_ms": 406.866, "estimated_cost": null, "evidence_selection": "INDETERMINATE (no live selection)", "failed_dispatches": 0, "final_response": "The action was resolved, but live narration was not requested because it would exceed the provider budget.", "input_tokens": 0, "interpretation": "INDETERMINATE (no model interpretation)", "note": "INVALID LIVE CONTROL: fixture import activated experiments/pr_dq/__init__.py environment defaults. Live interpretation skipped; generic resolution consumed a turn, cleared pending intention and updated factions. Narration refused before admission by existing input-token ceiling.", "output_tokens": 0, "pending_intentions": {"last_executed_intention": {"after": {"operation": null, "scene_id": "waystation_courtyard", "status": "executed", "target": null, "text": "Instead, make that a question about the lamp."}, "before": null}, "pending_clarification": {"after": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}, "before": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}}, "pending_intention": {"after": null, "before": {"choices": [{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}, {"entity_id": "corporal_bren", "label": "Corporal Bren"}], "clarification": "Which person do you mean?", "kind": "ambiguous_addressee", "operation": "ASK", "original_text": "I ask one of them what happened.", "scene_id": "waystation_courtyard", "status": "pending", "target_resolution": "ambiguous"}}}, "player_input": "Instead, make that a question about the lamp.", "response_adequacy": "FAIL", "routing": "FAIL in disabled-interpretation fallback; live control INDETERMINATE", "session_changed_keys": ["_runtime_canonical_ctir_stamp_v1", "_runtime_canonical_ctir_v1", "_runtime_narration_plan_bundle_stamp_v1", "_runtime_narration_plan_bundle_v1", "_runtime_progression_nodes_fingerprint_v1", "bounded_improvisation", "character_name", "clocks", "conversational_context", "debug_traces", "discourse_focus", "emergent_actor_debug", "interaction_context", "interpretation_telemetry", "last_action_debug", "last_bounded_improvisation_promotion", "last_saved_at", "last_turn_response_policy", "lead_registry", "narration_temporal_provenance", "npc_runtime", "runtime_scene_overlays", "scene_runtime", "scene_state", "turn_counter"], "total_tokens": 0, "trace_functions": ["interpret_production_turn"], "trial": "L4", "turn_counter_after": 1, "turn_counter_before": 0, "world_changed_keys": ["event_log", "factions"]}`
Runtime validity: `"INVALID live control; test environment leakage"`
Continuation: `null`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Evaluator disagreement: `null`

### Stress Probe

Selection: first example labeled stress_probe

No example observed in this campaign.

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities


## What This Does Not Prove

- No successful original-wording live reproduction.
- No valid live mechanical control.
- One related paraphrase is not independent generalization.
- L4 mutation prevents unconditional authority claim.
- Human review pending.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
