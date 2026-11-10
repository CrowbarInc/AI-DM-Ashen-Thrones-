# Validation Evidence: PR-PLAY-70

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Two mutually exclusive persisted responses to uncertain patrol evidence, each with a distinct supported follow-up.
Runtime path: Actual localhost TCP action/chat/state/snapshot endpoints; browser evidence separate.
GM boundary: Deterministic consequence publication; optional provider candidates shadow-only.
Player inputs: Developer scripted plausible button actions plus duplicate/incompatible stress probes.
Runs / turns: 2 / 19
Automated conclusion: Narrow branching contract passes; overall B/PARTIAL due qualified startup/browser/provider/performance evidence.
Result counts: `{"PASS": 19}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

Example: `survey_01`
Source: `artifacts/pr_play_70/http_survey.json`
Run / turn: `c888e50f94efdde16548b49b` / `1`
Input classification: `representative_player_behavior, synthetic_positive_control`
Selection rationale: Scripted canonical sequence to demonstrate exclusivity and persisted follow-up; not human-captured play.

Player input (exact):

> I examine the notice board.

GM output (exact):

> You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Automated result: `PASS`
Mandatory gates: `{"isolation": {"basis": "complete serialized response sentinel scan", "status": "PASS"}, "publication": {"basis": "exact trusted authored consequence or required discovery text", "status": "PASS"}}`
Diagnostic result: `{"scope": "narrow scripted branch contract"}`
Runtime validity: `{"basis": "HTTP 200 with persisted server state", "status": "VALID_RUN"}`
Continuation: `{"action": {"text": "I follow the missing patrol rumor."}}`
Human review: `UNREVIEWED` - No external human review recorded.
Evaluator disagreement: `{"present": false}`

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

No example observed in this campaign.

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

No example observed in this campaign.

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

No example observed in this campaign.

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

No example observed in this campaign.

### Stress Probe

Selection: first example labeled stress_probe

Example: `survey_05`
Source: `artifacts/pr_play_70/http_survey.json`
Run / turn: `c888e50f94efdde16548b49b` / `5`
Input classification: `stress_probe, synthetic_negative_control`
Selection rationale: Scripted canonical sequence to demonstrate exclusivity and persisted follow-up; not human-captured play.

Player input (exact):

> Survey the uncertain trail yourself

GM output (exact):

> That choice is not available here. No consequence was applied.

Automated result: `PASS`
Mandatory gates: `{"isolation": {"basis": "complete serialized response sentinel scan", "status": "PASS"}, "publication": {"basis": "exact trusted authored consequence or required discovery text", "status": "PASS"}}`
Diagnostic result: `{"scope": "narrow scripted branch contract"}`
Runtime validity: `{"basis": "HTTP 200 with persisted server state", "status": "VALID_RUN"}`
Continuation: `{"action": {"action_type": "exploration", "exploration_action": {"id": "patrol_report", "label": "Return to report the uncertain trail to the watch", "prompt": "Return to report the uncertain trail to the watch", "type": "custom"}, "intent": "Return to report the uncertain trail to the watch"}}`
Human review: `UNREVIEWED` - No external human review recorded.
Evaluator disagreement: `{"present": false}`

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities

- **Normal browser campaign creation and save-slot resume**: Browser harness seeded clean prestarted campaigns and reloaded actual UI. Status: NOT_DEMONSTRATED.

## What This Does Not Prove

- No independent holdout or human-realism claim.
- Provider candidates were not published.
- Normal screenshots clipped by host viewport; browser visible latency unmeasured.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
