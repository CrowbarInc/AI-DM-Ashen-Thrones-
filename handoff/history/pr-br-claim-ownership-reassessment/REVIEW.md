# Campaign

Campaign: PR-BR Claim Ownership, Proposition Decomposition, and Temporal Authority
Identifier: `pr-br-claim-ownership-reassessment`
Date: 2026-10-03
Generated: 2026-10-04T04:30:00+00:00
Purpose: Architectural reassessment of who owns semantic claims that reach the player, after the four-turn live run reproduced authority laundering. Discovery only. No production edits and no model calls.

# Executive Summary

Narration still creates the consequential proposition, and sentence-level alias overlap can stamp that whole sentence as authored world truth. NarratedClaim is an annotated sentence. The temporal ledger is written after seal and is not read by authorization. The GM Resolution Decision already claims this ownership and does not exercise it before prose. Decision A: salvage by making that decision own the complete consequential claim set before narration.

Objective status: `architecture_salvageable_by_decision_owned_claim_set_before_narration`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- No changes in this category.

## Documentation changes

- Wrote the architectural review and the four-turn proposition timeline from saved artifacts only.

## Generated artifacts

- handoff/CURRENT_REVIEW.md, handoff/REVIEW_MANIFEST.json, and handoff/CURRENT_REVIEW.zip package this review with the live-run report, temporal ledgers, and the production modules that match, classify, and persist claims.

# What Was Tested

- **Focused tests:** Not run. This cycle is review only.
- **Broader relevant tests:** Not run. The 333-test result cited here is the prior localized-repair campaign, not a new run.
- **Full suite:** Not run.
- **Runtime validation:** None. Zero gameplay turns and zero model calls in this cycle. Findings use the completed 20261004T035044Z four-turn run.
- **Model/runtime boundary:** 0 gameplay turns. 0 generation calls. 0 retry calls. 0 interpretation calls. 0 preflight calls. 0 other calls. 0 total model/API calls.
- **New regressions:** No production patch.
- **Pre-existing failures:** The four-turn live result remains 0 PASS / 4 FAIL. Turn 2 routing is classified as a separate local defect and was not redesigned here.
- **Self-contained bundle review:** The bundle contains the architectural review, the proposition timeline, the live validation report and temporal ledgers, the prior 333-test campaign summary, the claim-control tests that stayed green, and the production modules that construct the decision, match semantic identity, classify narrated sentences, and write temporal provenance.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- A. CURRENT ARCHITECTURE IS SALVAGEABLE BY MAKING THE GM RESOLUTION DECISION OWN THE COMPLETE CONSEQUENTIAL CLAIM SET BEFORE NARRATION.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turn 3 stamped 'sudden, violent pressure seems a likely cause' as authored world truth because observation aliases matched the sentence.
- NarratedClaim recorded one object for that sentence and copied the observation identity onto it.
- gm_inferences stayed empty. The player hypothesis was stored and then ignored by authorization.
- Uncertainty suppressed accounting for the wear/pressure alternatives, the disturbance absence, and the witness lead.
- Turn 4 NPC color was classified claim_only and persisted in neither ledger.
- Turn 2 mis-bound the hypothetical as a place/addressee problem. That defect is local routing.

## Pre-existing baseline

- The 333/333 deterministic band did not compose fast-path contract construction with unrestricted prose and post-seal ledger writes.

# Missing Concepts / Future Capabilities

- A RealizationClaim owned by the decision before narration, with actor, relation, object, cause, time, polarity, and modality.
- Monotonic authority: co-occurrence and paraphrase do not promote a hypothesis.
- Separate accounting for gameplay leads and negative evidence.
- One persistence consumer for accepted NPC claims and bounded incidentals.

# What This Campaign Does NOT Prove

- Does not implement the claim set, a prompt change, or a validator change.
- Does not prove a residual regex could be extended to cover the next paraphrase.
- Does not rerun the four turns or the 4x10 gate.
- Does not authorize PR-BS.
- Does not treat Turn 2 routing as the same defect as proposition laundering.

# Recommended Next Step

Implement only the decision-owned consequential claim set in section 21 of the architectural review. Deterministic tests on the saved Turn 3 sentence come before any further live call.

# Review Bundle Contents

Bundle file count: `17`
Bundle ZIP size: `000000143079` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_claim_ownership_reassessment/ARCHITECTURAL_REVIEW.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_claim_ownership_reassessment/ARCHITECTURAL_REVIEW.md`.
- `support/artifacts/pr_br_claim_ownership_reassessment/PROPOSITION_TIMELINE.md`: Proposition-level timeline for Turns 1-4, including authority changes. Canonical source: `artifacts/pr_br_claim_ownership_reassessment/PROPOSITION_TIMELINE.md`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/validation_report.md`: Measured 0 PASS / 4 FAIL report for the run this review explains. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/validation_report.md`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/run_manifest.json`: Exact call counts, inputs, and emitted text. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/run_manifest.json`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/turn_1/temporal_provenance_after.json`: Turn 1 ledger: speculation active claim, empty gm_inferences, rejected great-force row. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/turn_1/temporal_provenance_after.json`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/turn_2/temporal_provenance_after.json`: Turn 2 ledger: player hypothesis stored and not promoted. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/turn_2/temporal_provenance_after.json`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/turn_3/temporal_provenance_after.json`: Turn 3 ledger: gm_inferences still empty after the likely-cause sentence. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/turn_3/temporal_provenance_after.json`.
- `support/artifacts/pr_br_final_live_validation/20261004T035044Z/turn_4/temporal_provenance_after.json`: Turn 4 ledger: accepted_incidentals still empty. Canonical source: `artifacts/pr_br_final_live_validation/20261004T035044Z/turn_4/temporal_provenance_after.json`.
- `support/artifacts/pr_br_claim_ownership_reassessment/prior_333_test_record.md`: Records the 333/333 deterministic result that preceded the 0/4 live run. Canonical source: `artifacts/pr_br_claim_ownership_reassessment/prior_333_test_record.md`.
- `support/tests/test_pr_br_claim_control_slice2.py`: Shows the hand-built paraphrases the green tests actually reject. Canonical source: `tests/test_pr_br_claim_control_slice2.py`.
- `support/game/gm_resolution_decision.py`: Decision construction, semantic identity match, NarratedClaim, audit, and temporal writer. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/proposition_authority.py`: Older sentence classifier whose hedge and non-assertion rules drop or soften consequential sentences. Canonical source: `game/proposition_authority.py`.
- `support/game/resolution_contract.py`: Interpretation dimension pattern and contract construction that dropped Turn 1's infer request. Canonical source: `game/resolution_contract.py`.
- `support/game/discourse_state.py`: Active-claim commit and emitted NPC-claim focus. Canonical source: `game/discourse_state.py`.
- `support/game/bounded_improvisation.py`: Improvisation ledger that stayed empty on the Turn 4 NPC claim. Canonical source: `game/bounded_improvisation.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
