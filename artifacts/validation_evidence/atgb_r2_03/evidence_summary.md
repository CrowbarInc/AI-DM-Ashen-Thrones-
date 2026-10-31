# Validation Evidence: atgb_r2_03

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Four historical turns reconstructed; 16 deterministic decision controls plus offline adapter and authorization controls. No repair implemented.
Runtime path: Original captured API logs plus current production function replay, in-memory copies only
GM boundary: Historical live interpretations retained; no new model call or final API emission
Player inputs: Fixed authored historical ATGB input, not human-captured live play
Runs / turns: 2 / 4
Automated conclusion: C — live interpretation dependency; historical failures are not repair-effect results
Result counts: `{"FAIL": 4}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `S02.2`
Source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`
Run / turn: `artifacts/atgb/atgb_03/S02/result.json` / `2`
Input classification: `representative_player_behavior`
Selection rationale: Fixed authored ATGB line; not a new human-captured utterance.

Player input (exact):

> When does the curfew start?

GM output (exact):

> The notice board lists taxes, curfew rules, and a warning about a missing patrol.

Automated result: `FAIL`
Mandatory gates: `{"historical_unavailability": {"reason": "No new standard gate scoring performed", "status": "UNAVAILABLE"}}`
Diagnostic result: `{"status": "NOT_RUN"}`
Runtime validity: `"captured"`
Continuation: `"Historical sequence only; no new gameplay execution"`
Human review: `UNREVIEWED` - New causal assessment awaits external review; imported historical rubric preserved
Evaluator disagreement: `{"present": false, "rationale": "No new evaluator comparison performed"}`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `S02.2`
Source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`
Run / turn: `artifacts/atgb/atgb_03/S02/result.json` / `2`
Input classification: `representative_player_behavior`
Selection rationale: Fixed authored ATGB line; not a new human-captured utterance.

Player input (exact):

> When does the curfew start?

GM output (exact):

> The notice board lists taxes, curfew rules, and a warning about a missing patrol.

Automated result: `FAIL`
Mandatory gates: `{"historical_unavailability": {"reason": "No new standard gate scoring performed", "status": "UNAVAILABLE"}}`
Diagnostic result: `{"status": "NOT_RUN"}`
Runtime validity: `"captured"`
Continuation: `"Historical sequence only; no new gameplay execution"`
Human review: `UNREVIEWED` - New causal assessment awaits external review; imported historical rubric preserved
Evaluator disagreement: `{"present": false, "rationale": "No new evaluator comparison performed"}`

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


## What This Does Not Prove

- Original full provider requests unavailable; current request reconstruction is not historical capture.
- Historical imported assessment is AI-assisted, not authenticated human review.
- No live improvement, benchmark score, independent generalization or broad regression claim.
- S05 account ambiguity is material; do not invent a unique topic.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
