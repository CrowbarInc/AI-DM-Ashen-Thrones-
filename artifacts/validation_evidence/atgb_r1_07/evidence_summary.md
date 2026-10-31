# Validation Evidence: atgb_r1_07

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Recorded and substituted interpretations across three preserved failures; host structural contract only.
Runtime path: Production request construction -> stub wire -> adapter -> conversational decision
GM boundary: No model/provider calls; explicit counterfactuals
Player inputs: Preserved text, synthetic controls
Runs / turns: 6 / 6
Automated conclusion: Host contract assertions passed; live selection unproven.
Result counts: `{"NOT_EVALUATED": 6}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

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

No example observed in this campaign.

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities


## What This Does Not Prove

- No new live result, semantic evaluator, human review, benchmark performance or independent generalization.
- Six offline arms over three historical inputs; recorded-output arms remain redundant clarification.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
