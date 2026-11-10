# Campaign

Campaign: PR-PLAY — Grounded Marking Removal and Lifecycle Closure
Identifier: `pr_play_grounded_marking_removal`
Date: 2026-11-09
Generated: 2026-11-10T04:05:39.602965+00:00
Purpose: Player-facing removal of one established visible marking through the existing chat turn and removal service

# Executive Summary

**A/PASS.** A player can create a visible marking, read it, wipe that one marking off in ordinary language, and read its absence. The removal commits through prepare_removal. Save, reload, and snapshot restore keep it removed. An exact retry does not remove it again. Concealed, restricted, and a second identical marking are not selected. A contradictory seal is replaced by the committed sentence. Twelve-turn text matches the immediate predecessor. Focused modules 611 passed. Combined before and after: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests), same identities. Live provider calls 0. The marking lifecycle can close as a bounded subsystem. Next milestone: pr_play_broad_gameplay_evaluation. Do not begin automatically.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/api.py
- game/marking_removal.py

## Validation changes

- 15 removal tests passed inside a 611-passed focused run.

## Tooling changes

- Cycle-local twelve-turn comparison and removal timing

## Documentation changes

- 20 milestone reports; historical NEXT_SESSION retained

## Generated artifacts

- Controlled lifecycle evidence, regression junit, twelve-turn comparison, and a fresh review archive

# What Was Tested

- **Focused tests:** Removal 15 passed. Observation 10 passed. Grounded marking 12 passed. Focused command 611 passed / 0 failed.
- **Broader relevant tests:** Combined before and after: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failing identities: none. Newly passing: none.
- **Full suite:** Not run
- **Runtime validation:** Controlled HTTP mark, observe, wipe, observe, reload, retry, and snapshot restore. Twelve-turn HTTP run. Publication and feasibility tests.
- **Model/runtime boundary:** Zero provider calls; providers disabled.
- **New regressions:** []
- **Pre-existing failures:** The same 20 combined identities before and after. Seventeen match the predecessor. Three classification tests had already failed in this cycle's before run. See REGRESSION_RESULTS.md.
- **Self-contained bundle review:** Reopen the archive and confirm milestone identity, the controlled HTTP lifecycle, target and marking resolution, physical feasibility, authoritative removal, publication integrity, confidentiality, save/reload and snapshots, regressions, the twelve-turn comparison, subsystem closure, and the updated handoff.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No further authorization required for this bounded implementation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Original T06 stays unresolved because no garment or medium is established. A pronoun does not select an object. Required consumption and required mechanics stay unresolved. Ordinary observation does not certify that concealed markings are absent.

## Pre-existing baseline

- Combined 20 failure identities. See REGRESSION_RESULTS.md.

# Missing Concepts / Future Capabilities

- A broader gameplay evaluation of the remaining twelve-turn gaps.

# What This Campaign Does NOT Prove

- Environmental material inference, consumption, mechanical skill checks, bulk removal, a full suite, live-model play, or all object interaction.

# Recommended Next Step

Exactly one recommended next milestone: pr_play_broad_gameplay_evaluation — one provider-free pass over the remaining twelve-turn gaps that names a single later integration target. Do not begin automatically.

# Review Bundle Contents

Bundle file count: `37`
Bundle ZIP size: `000000162590` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/AUTHORITY_AND_IDEMPOTENCY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/AUTHORITY_AND_IDEMPOTENCY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/BASELINE.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/BASELINE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/CONFIDENTIALITY_VERIFICATION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/CONFIDENTIALITY_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/CONTROLLED_HTTP_LIFECYCLE.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/CONTROLLED_HTTP_LIFECYCLE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/INTEGRITY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/INTENT_RECOGNITION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/INTENT_RECOGNITION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/NEXT_STEP_DECISION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/PARAPHRASE_CONTROLS.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/PARAPHRASE_CONTROLS.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/PERFORMANCE.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/PERFORMANCE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/PERSISTENCE_VERIFICATION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/PERSISTENCE_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/PHYSICAL_FEASIBILITY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/PHYSICAL_FEASIBILITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/PUBLICATION_INTEGRITY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/PUBLICATION_INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/REGRESSION_RESULTS.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/REMOVAL_INTEGRATION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/REMOVAL_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/RULESET_PORTABILITY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/RULESET_PORTABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/SUBSYSTEM_CLOSURE.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/SUBSYSTEM_CLOSURE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/TARGET_RESOLUTION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/TARGET_RESOLUTION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/TURN_ATOMICITY.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/TURN_ATOMICITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_removal/TWELVE_TURN_COMPARISON.md`: Milestone report or evidence for grounded marking removal. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_removal/TWELVE_TURN_COMPARISON.md`.
- `support/artifacts/pr_play_grounded_marking_removal/controlled_http_lifecycle.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/controlled_http_lifecycle.json`.
- `support/artifacts/pr_play_grounded_marking_removal/mixed_marking_controls.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/mixed_marking_controls.json`.
- `support/artifacts/pr_play_grounded_marking_removal/paraphrase_results.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/paraphrase_results.json`.
- `support/artifacts/pr_play_grounded_marking_removal/publication_and_feasibility.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/publication_and_feasibility.json`.
- `support/artifacts/pr_play_grounded_marking_removal/twelve_turn_after.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/twelve_turn_after.json`.
- `support/artifacts/pr_play_grounded_marking_removal/performance.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/performance.json`.
- `support/artifacts/pr_play_grounded_marking_removal/regression_results.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/regression_results.json`.
- `support/artifacts/pr_play_grounded_marking_removal/source_changes.json`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/source_changes.json`.
- `support/artifacts/pr_play_grounded_marking_removal/before_new_junit.xml`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/before_new_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_removal/before_combined_junit.xml`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/before_combined_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_removal/after_combined_junit.xml`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/after_combined_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_removal/after_focused_junit.xml`: Milestone report or evidence for grounded marking removal. Canonical source: `artifacts/pr_play_grounded_marking_removal/after_focused_junit.xml`.
- `support/game/marking_removal.py`: Milestone report or evidence for grounded marking removal. Canonical source: `game/marking_removal.py`.
- `support/tests/test_grounded_marking_removal.py`: Milestone report or evidence for grounded marking removal. Canonical source: `tests/test_grounded_marking_removal.py`.
- `support/docs/NEXT_SESSION.md`: Milestone report or evidence for grounded marking removal. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

- `development/campaigns/product_realization/pr_play_grounded_marking_removal/SUMMARY.md`: duplicate content of development/campaigns/product_realization/pr_play_grounded_marking_removal/SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
