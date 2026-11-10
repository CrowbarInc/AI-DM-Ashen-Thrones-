# Campaign

Campaign: PR-PLAY Adjacent Regression Reconciliation
Identifier: `pr_play_adjacent_regression`
Date: 2026-11-08
Generated: 2026-11-08T22:45:00+00:00
Purpose: Classify the twelve adjacent HTTP failures from the post-NPC handoff repair without changing production behavior.

# Executive Summary

Audit verdict A/PASS. The targeted handoff repair is accepted. The game is not playable. Live provider calls: 0. PR-PLAY-80 was not opened. The same 176-test selection failed the same 12 assertions. All 12 match a pre-handoff package that keeps authored travel and removes the handoff symbols. Zero are new regressions. Eight fail because the player body empties resolution while the log still has the kind or transition. Three publish stubs: Glassport crews, pocketing the brass token, and four new overseers. The roster case still publishes the observe stock. The seven handoff tests passed. T05 still appends the stock jab sentence.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No test expectation or fixture was changed. The existing 176-test selection was rerun: 12 failed, 0 errors, 0 skipped. The seven handoff tests passed.

## Tooling changes

- No changes in this category.

## Documentation changes

- Added the reports under development/campaigns/product_realization/pr_play_adjacent_regression/.
- Prepended the audit result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added the classification matrix, the current and pre-handoff captures, and the junit files under artifacts/pr_play_adjacent_regression/.
- Generated this review handoff.

# What Was Tested

- **Focused tests:** 7 passed, 0 failed. Provider-free /api/chat handoff controls.
- **Broader relevant tests:** 176 adjacent tests, 12 failed, 0 errors, 0 skipped. All 12 are preexisting. The known provider_context_projection, gm_only, and social_context KeyErrors were not in this selection and were not rerun.
- **Full suite:** Not run.
- **Runtime validation:** The notice approach, read, sleeve copy, and recall were printed again with provider calls disabled. T04 stays local. T05 publishes the clue and the jab sentence. T06 declines. T09 recalls the disclosed clue. Travel reaches Old Milestone. The glass observatory stays unestablished. The retreat stays unsupported.
- **Model/runtime boundary:** Live provider calls: 0. OpenAI construction was blocked. No Gameplay Benchmark was run.
- **New regressions:** None. The twelve failures match the pre-handoff package.
- **Pre-existing failures:** All 12 adjacent HTTP assertions. The three baseline KeyErrors remain outside this selection. The worktree was already dirty.
- **Self-contained bundle review:** The bundle contains the audit reports, the classification matrix, and the current and pre-handoff captures. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept the four route corrections.
- Do not treat A/PASS as a claim that the game is playable.
- Do not open PR-PLAY-80 from this handoff.
- The brass-token stub is a preexisting publication defect. It is deferred, not folded into the next sentence edit.

# Known Problems / Unresolved Findings

## Campaign-specific

- T05 publishes the authorized clue and then the stock sentence about someone jabbing at the board.

## Pre-existing baseline

- Twelve HTTP assertions fail. Eight are an empty public resolution object. Three publish model stubs. The roster inspection publishes the observe stock.
- Naming the hidden brass token publishes a sentence that the player pockets it. The sealed fact is not added to revealed state.
- The worktree was already dirty. HEAD does not uniquely identify the executable source.

# Missing Concepts / Future Capabilities

- A byte-for-byte saved copy of the dirty tree from the moment before the handoff edit. The comparison package was reconstructed outside the repository.
- An Ashen Thrones Gameplay Benchmark. None was run.

# What This Campaign Does NOT Prove

- It does not prove the game is playable.
- It does not retire the twelve tests.
- It does not prove the reconstructed orchestration file is a byte-for-byte pre-edit copy. The twelve HTTP captures on that package match the current captures.
- The seven handoff tests were authored with the repair. They are not an independent holdout.
- It does not authorize PR-PLAY-80, AT-OPT-07, or a live-play session.

# Recommended Next Step

Remove the stock diegetic sentence that follows an authorized clue publication. Do not start that repair from this handoff. Do not open PR-PLAY-80. Do not start AT-OPT-07. Do not launch live play from this result.

# Review Bundle Contents

Bundle file count: `16`
Bundle ZIP size: `000000089809` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/FAILURE_INVENTORY.md`: Individual record for each of the twelve assertions. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/FAILURE_INVENTORY.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/BASELINE_RECONSTRUCTION.md`: How the pre-handoff package was built without touching the worktree. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/BASELINE_RECONSTRUCTION.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/CONTRACT_ANALYSIS.md`: Player DTO, inspection, and travel contracts against the assertions. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/CONTRACT_ANALYSIS.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/TARGETED_REPAIR_VERIFICATION.md`: T04, T05, T06, T09, and the negative controls. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/TARGETED_REPAIR_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/NEXT_STEP_DECISION.md`: Acceptance of the handoff repair and the single next action. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_adjacent_regression/INTEGRITY.md`: Branch, worktree preservation, and zero live calls. Canonical source: `development/campaigns/product_realization/pr_play_adjacent_regression/INTEGRITY.md`.
- `support/artifacts/pr_play_adjacent_regression/classification_matrix.json`: Machine-readable classification of every failed assertion. Canonical source: `artifacts/pr_play_adjacent_regression/classification_matrix.json`.
- `support/artifacts/pr_play_adjacent_regression/current_capture.json`: Raw engine fields and projected HTTP bodies on the current tree. Canonical source: `artifacts/pr_play_adjacent_regression/current_capture.json`.
- `support/artifacts/pr_play_adjacent_regression/historical_capture.json`: The same capture on the pre-handoff package. Canonical source: `artifacts/pr_play_adjacent_regression/historical_capture.json`.
- `support/artifacts/pr_play_adjacent_regression/overlay_manifest.json`: Which source versions the comparison package executed. Canonical source: `artifacts/pr_play_adjacent_regression/overlay_manifest.json`.
- `support/artifacts/pr_play_adjacent_regression/adjacent_focus_junit.xml`: 176 tests, 12 failures, 0 errors, 0 skipped. Canonical source: `artifacts/pr_play_adjacent_regression/adjacent_focus_junit.xml`.
- `support/artifacts/pr_play_adjacent_regression/handoff_junit.xml`: Seven handoff controls passed. Canonical source: `artifacts/pr_play_adjacent_regression/handoff_junit.xml`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this audit. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
