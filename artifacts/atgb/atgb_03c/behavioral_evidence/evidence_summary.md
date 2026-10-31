# Validation Evidence: atgb_03c_live_baseline_continuation

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: S04 full trial 2 and S05-S10 trial 1; 24 fixture turns; all conversational outcomes unscored
Runtime path: Production POST /api/chat through approved TestClient worker in fresh isolated frozen-baseline stores
GM boundary: Live-enabled OpenAI gpt-4.1-mini with existing host-owned replies and model roles; no browser UI validation
Player inputs: Approved fixed benchmark lines; previously exposed held-out scenarios remain labeled
Runs / turns: 7 / 24
Automated conclusion: Runtime capture only. No evaluator or human success/failure classifications were made. Empty selected outcome categories mean unmeasured, not zero gameplay failures.
Result counts: `{"UNAVAILABLE": 24}`

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

- **Opening context delivery**: Approved silent-reset worker does not deliver authored opening before fixture turns; S07/S09 carry setup limitations. Status: Recorded; no behavioral change.

## What This Does Not Prove

- All human judgments pending; no gameplay score or measured success/failure counts.
- Opening-dependent criteria require uncertain/not evaluated when unsupported.
- No independent generalization, conversational improvement, rendered UI or SDK transport retry claim.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
