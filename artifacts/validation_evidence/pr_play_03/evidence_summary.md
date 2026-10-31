# Validation Evidence: pr_play_03

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Historical failed opening and six offline host controls; no repair.
Runtime path: Production start_campaign endpoint function through SDK stub and real disposable stores; original saved session inspected.
GM boundary: One historical live call; zero new live calls. Synthetic response/control outputs explicitly labeled.
Player inputs: Captured Start button, empty input; synthetic SDK controls.
Runs / turns: 7 / 6
Automated conclusion: 27 host assertions and 38 existing tests pass; semantic opening failure remains; no repair-effect claim.
Result counts: `{"FAIL": 1, "UNAVAILABLE": 5}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `historical_start`
Source: `artifacts/pr_play_02/manual-20261026-201939.zip::data/session_log.jsonl`
Run / turn: `historical_start` / `1`
Input classification: `human_captured, representative_player_behavior, runtime_discovered`
Selection rationale: Not applicable.

Player input (exact):

> 

GM output (exact):

> No one here can answer that from what is settled here.

Automated result: `FAIL`
Mandatory gates: `{"availability": "No historical semantic scorer retained; no gameplay PASS asserted."}`
Diagnostic result: `{"finding": "opening success and text meaning examined separately"}`
Runtime validity: `{"rendered_ui": "unknown", "saved_response": true}`
Continuation: `"Stop for external review"`
Human review: `UNREVIEWED` - AI-assisted investigation; no authenticated human scorer. User reports original opening inadequate.
Evaluator disagreement: `{"history": "Original trace successful=true but user-reported and source-inspected output does not establish an opening.", "present": true}`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `historical_start`
Source: `artifacts/pr_play_02/manual-20261026-201939.zip::data/session_log.jsonl`
Run / turn: `historical_start` / `1`
Input classification: `human_captured, representative_player_behavior, runtime_discovered`
Selection rationale: Not applicable.

Player input (exact):

> 

GM output (exact):

> No one here can answer that from what is settled here.

Automated result: `FAIL`
Mandatory gates: `{"availability": "No historical semantic scorer retained; no gameplay PASS asserted."}`
Diagnostic result: `{"finding": "opening success and text meaning examined separately"}`
Runtime validity: `{"rendered_ui": "unknown", "saved_response": true}`
Continuation: `"Stop for external review"`
Human review: `UNREVIEWED` - AI-assisted investigation; no authenticated human scorer. User reports original opening inadequate.
Evaluator disagreement: `{"history": "Original trace successful=true but user-reported and source-inspected output does not establish an opening.", "present": true}`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

Example: `historical_start`
Source: `artifacts/pr_play_02/manual-20261026-201939.zip::data/session_log.jsonl`
Run / turn: `historical_start` / `1`
Input classification: `human_captured, representative_player_behavior, runtime_discovered`
Selection rationale: Not applicable.

Player input (exact):

> 

GM output (exact):

> No one here can answer that from what is settled here.

Automated result: `FAIL`
Mandatory gates: `{"availability": "No historical semantic scorer retained; no gameplay PASS asserted."}`
Diagnostic result: `{"finding": "opening success and text meaning examined separately"}`
Runtime validity: `{"rendered_ui": "unknown", "saved_response": true}`
Continuation: `"Stop for external review"`
Human review: `UNREVIEWED` - AI-assisted investigation; no authenticated human scorer. User reports original opening inadequate.
Evaluator disagreement: `{"history": "Original trace successful=true but user-reported and source-inspected output does not establish an opening.", "present": true}`

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

No example observed in this campaign.

### Stress Probe

Selection: first example labeled stress_probe

No example observed in this campaign.

## All Evaluator Disagreements

### historical_start

Source: `artifacts/pr_play_02/manual-20261026-201939.zip::data/session_log.jsonl`
Player classification: `human_captured, representative_player_behavior, runtime_discovered`
Player (exact): 
GM (exact): No one here can answer that from what is settled here.
Original automated result: `FAIL`
Original gates: `{"availability": "No historical semantic scorer retained; no gameplay PASS asserted."}`
Human review: `UNREVIEWED` - AI-assisted investigation; no authenticated human scorer. User reports original opening inadequate.
History: `{"history": "Original trace successful=true but user-reported and source-inspected output does not establish an opening.", "present": true}`

## Missing Concepts / Future Capabilities


## What This Does Not Prove

- Original raw provider output/request and provider finish details missing.
- No rendered UI, independent generalization, gameplay benchmark or repair validation.
- Original successful=true is runtime telemetry, not a semantic evaluator PASS.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
