# Campaign

Campaign: PR-PLAY — Grounded Physical Marking Action Integration
Identifier: `pr_play_grounded_marking_action_integration`
Date: 2026-11-09
Generated: 2026-11-10T01:34:27.802275+00:00
Purpose: Bounded end-to-end grounded physical marking during ordinary HTTP play

# Executive Summary

**A/PASS.** A natural-language marking action now runs in the existing chat turn. It binds an established object, medium, and disclosed text, commits through the existing marking and visibility services, and publishes only after the save. Controlled HTTP copy persists, reloads, replays without a duplicate, restores from snapshots, and is recovered by internal observation. Original T06 is recognized and left unresolved: no garment, medium, or marking is invented. Combined 408 passed / 17 failed before and after, same identities. Focused predecessor selection 574 passed. Live provider calls 0. Next milestone: pr_play_player_marking_observation. Do not begin automatically.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/api.py
- game/marking_action.py

## Validation changes

- 12 grounded marking tests passed. T06, T04, and post-NPC assertions now expect the grounded unresolved sentence.

## Tooling changes

- Cycle-local HTTP sequence, performance, and regression runners

## Documentation changes

- 18 milestone reports; historical NEXT_SESSION retained

## Generated artifacts

- Bounded HTTP, regression, and hash evidence plus a fresh review archive

# What Was Tested

- **Focused tests:** 12 passed / 0 failed (grounded marking). Focused predecessor selection after: 574 passed / 0 failed.
- **Broader relevant tests:** Combined before and after: 408 passed / 17 failed / 0 errors / 0 skipped (425 tests). New failing identities: none. Newly passing: none. Disclosure historical pair unchanged: 238 passed / 2 failed of 240.
- **Full suite:** Not run
- **Runtime validation:** Controlled HTTP success, original twelve-turn HTTP run, save/reload, snapshots, observation, idempotent replay, and failure injection.
- **Model/runtime boundary:** Zero provider calls; providers disabled and non-loopback sockets blocked.
- **New regressions:** []
- **Pre-existing failures:** The same 17 combined identities before and after. Historical disclosure KeyError character_secret pair. See REGRESSION_RESULTS.md.
- **Self-contained bundle review:** Reopen the archive and confirm milestone identity, controlled HTTP success, original T06, mutation, visibility, observation, idempotency, save/reload, snapshots, publication ordering, regressions, ruleset portability, and the updated handoff.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No further authorization required for this bounded implementation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Player HTTP projections do not disclose markings. Environmental materials are not inferred. Required consumption and required mechanics stay unresolved. The in-memory request cache returns the first body for a repeated client request id.

## Pre-existing baseline

- Combined 17 failure identities and the disclosure character_secret pair. See REGRESSION_RESULTS.md.

# Missing Concepts / Future Capabilities

- Player-facing observation of a committed marking.

# What This Campaign Does NOT Prove

- A player HTTP observation route, environmental material inference, consumption, mechanical skill checks, full suite, or live-model play.

# Recommended Next Step

Exactly one recommended next milestone: pr_play_player_marking_observation — player-facing read of an already committed marking through the existing observation and disclosure path. Do not begin automatically.

# Review Bundle Contents

Bundle file count: `37`
Bundle ZIP size: `000000177879` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/BASELINE.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/BASELINE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/CONTROLLED_SUCCESS.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/CONTROLLED_SUCCESS.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/GAMEPLAY_INTEGRATION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/GAMEPLAY_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/INTEGRITY.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/INTENT_RECOGNITION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/INTENT_RECOGNITION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/MUTATION_INTEGRATION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/MUTATION_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/NARRATIVE_PUBLICATION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/NARRATIVE_PUBLICATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/NEXT_STEP_DECISION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/OBJECT_RESOURCE_RESOLUTION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/OBJECT_RESOURCE_RESOLUTION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/ORIGINAL_T06.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/ORIGINAL_T06.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PARAPHRASE_CONTROLS.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PARAPHRASE_CONTROLS.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PERFORMANCE.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PERFORMANCE.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PREREQUISITE_ADJUDICATION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/PREREQUISITE_ADJUDICATION.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/REGRESSION_RESULTS.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/RULESET_PORTABILITY.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/RULESET_PORTABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/TURN_ATOMICITY.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/TURN_ATOMICITY.md`.
- `support/development/campaigns/product_realization/pr_play_grounded_marking_action_integration/TWELVE_TURN_COMPARISON.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/TWELVE_TURN_COMPARISON.md`.
- `support/artifacts/pr_play_grounded_marking_action_integration/source_changes.json`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/source_changes.json`.
- `support/artifacts/pr_play_grounded_marking_action_integration/regression_results.json`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/regression_results.json`.
- `support/artifacts/pr_play_grounded_marking_action_integration/twelve_turn_after.json`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/twelve_turn_after.json`.
- `support/artifacts/pr_play_grounded_marking_action_integration/performance.json`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/performance.json`.
- `support/artifacts/pr_play_grounded_marking_action_integration/marking_action_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/marking_action_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/before_combined_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/before_combined_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/after_combined_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/after_combined_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/before_focused_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/before_focused_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/after_focused_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/after_focused_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/before_visibility_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/before_visibility_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/after_visibility_junit.xml`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/after_visibility_junit.xml`.
- `support/artifacts/pr_play_grounded_marking_action_integration/entry_production_hashes.txt`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/entry_production_hashes.txt`.
- `support/artifacts/pr_play_grounded_marking_action_integration/entry_head.txt`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/entry_head.txt`.
- `support/artifacts/pr_play_grounded_marking_action_integration/entry_branch.txt`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `artifacts/pr_play_grounded_marking_action_integration/entry_branch.txt`.
- `support/game/marking_action.py`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `game/marking_action.py`.
- `support/tests/test_grounded_marking_action.py`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `tests/test_grounded_marking_action.py`.
- `support/docs/NEXT_SESSION.md`: Milestone report or measured evidence for grounded marking action integration. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

- `development/campaigns/product_realization/pr_play_grounded_marking_action_integration/SUMMARY.md`: duplicate content of development/campaigns/product_realization/pr_play_grounded_marking_action_integration/SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
