# Validation Evidence: ATGB-R1-05

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: L1/L2 original S08.2 correction and L4 pending ASK revision only
Runtime path: game.api.chat(ChatRequest) with readiness.guarded_trial; direct callable, live OpenAI interpretation
GM boundary: Production host orchestration and existing final-emission boundary
Player inputs: Three exact user-specified inputs
Runs / turns: 3 / 3
Automated conclusion: AI-assisted B — Partial; authenticated human review pending
Result counts: `{"FAIL": 2, "PASS": 1}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

Example: `ATGB-R1-05-L4`
Source: `artifacts/atgb/atgb_r1_05/L4/response.json`
Run / turn: `L4` / `2`
Input classification: `synthetic_positive_control, boundary_case`
Selection rationale: User-specified fixed reproduction/control; no generated player.

Player input (exact):

> Instead, make that a question about the lamp.

GM output (exact):

> I've revised that unexecuted intention. It has not been attempted. Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.

Automated result: `PASS`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "PASS"}, "interpretation": {"status": "PASS"}, "response_adequacy": {"status": "PASS"}, "routing": {"status": "PASS"}}`
Diagnostic result: `{"reason": "No playability scorer invoked", "status": "NOT_RUN"}`
Runtime validity: `{"live_model": true, "preflight": "ready", "status": "VALID"}`
Continuation: `{"action": "STOP", "reason": "Specified trial complete; no automatic continuation"}`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Evaluator disagreement: `{"calibration_reference": null, "history": [], "present": false}`

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `ATGB-R1-05-L1`
Source: `artifacts/atgb/atgb_r1_05/L1/response.json`
Run / turn: `L1` / `2`
Input classification: `representative_player_behavior, boundary_case`
Selection rationale: User-specified fixed reproduction/control; no generated player.

Player input (exact):

> I meant the people, not the weather.

GM output (exact):

> Do you mean to clarify that your previous reference was to the people present rather than the weather conditions?

Automated result: `FAIL`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "FAIL"}, "interpretation": {"status": "PASS"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "PASS"}}`
Diagnostic result: `{"reason": "No playability scorer invoked", "status": "NOT_RUN"}`
Runtime validity: `{"live_model": true, "preflight": "ready", "status": "VALID"}`
Continuation: `{"action": "STOP", "reason": "Specified trial complete; no automatic continuation"}`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Evaluator disagreement: `{"calibration_reference": null, "history": [], "present": false}`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `ATGB-R1-05-L1`
Source: `artifacts/atgb/atgb_r1_05/L1/response.json`
Run / turn: `L1` / `2`
Input classification: `representative_player_behavior, boundary_case`
Selection rationale: User-specified fixed reproduction/control; no generated player.

Player input (exact):

> I meant the people, not the weather.

GM output (exact):

> Do you mean to clarify that your previous reference was to the people present rather than the weather conditions?

Automated result: `FAIL`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "FAIL"}, "interpretation": {"status": "PASS"}, "response_adequacy": {"status": "FAIL"}, "routing": {"status": "PASS"}}`
Diagnostic result: `{"reason": "No playability scorer invoked", "status": "NOT_RUN"}`
Runtime validity: `{"live_model": true, "preflight": "ready", "status": "VALID"}`
Continuation: `{"action": "STOP", "reason": "Specified trial complete; no automatic continuation"}`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Evaluator disagreement: `{"calibration_reference": null, "history": [], "present": false}`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

No example observed in this campaign.

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

Example: `ATGB-R1-05-L4`
Source: `artifacts/atgb/atgb_r1_05/L4/response.json`
Run / turn: `L4` / `2`
Input classification: `synthetic_positive_control, boundary_case`
Selection rationale: User-specified fixed reproduction/control; no generated player.

Player input (exact):

> Instead, make that a question about the lamp.

GM output (exact):

> I've revised that unexecuted intention. It has not been attempted. Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.

Automated result: `PASS`
Mandatory gates: `{"authority": {"status": "PASS"}, "evidence_selection": {"status": "PASS"}, "interpretation": {"status": "PASS"}, "response_adequacy": {"status": "PASS"}, "routing": {"status": "PASS"}}`
Diagnostic result: `{"reason": "No playability scorer invoked", "status": "NOT_RUN"}`
Runtime validity: `{"live_model": true, "preflight": "ready", "status": "VALID"}`
Continuation: `{"action": "STOP", "reason": "Specified trial complete; no automatic continuation"}`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Evaluator disagreement: `{"calibration_reference": null, "history": [], "present": false}`

### Stress Probe

Selection: first example labeled stress_probe

No example observed in this campaign.

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities


## What This Does Not Prove

- Narrow three-trial validation, no full benchmark score or broad conversational reliability.
- No authenticated human scoring; provisional criteria analysis only.
- L4 topic/recipient conflation and later execution untested.
- Cost unavailable; no controlled performance baseline.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
