# Campaign

Campaign: PR-PLAY — Player-Facing Object Observation and Publication Integrity
Identifier: `pr_play_player_marking_observation`
Date: 2026-11-09
Generated: 2026-11-10T03:25:00+00:00
Purpose: Player-facing read of a committed marking and publication consistency with that commit

# Executive Summary

**A/PASS.** A player can examine the visible markings on an established carried object through the existing chat turn. The turn resolves the object, uses the existing disclosure service, and publishes only permitted current markings. Concealed, restricted, legacy, and removed markings stay out of the sentence. Observation does not write the character and survives save/reload and snapshots. A sealed sentence that contradicts a committed marking is not published; the character stays committed and the deterministic outcome is published instead. Twelve-turn text matches the immediate predecessor. Combined 408 passed / 17 failed before and after, same identities. Focused modules 574 passed inside a 596-passed run that also includes the new tests. Live provider calls 0. Next milestone: pr_play_grounded_marking_removal. Do not begin automatically.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/api.py
- game/storage.py
- game/marking_observation.py

## Validation changes

- 10 observation tests passed. The marking publication-failure test now expects the committed sentence and one marking.

## Tooling changes

- Cycle-local twelve-turn comparison and observation timing

## Documentation changes

- 17 milestone reports; historical NEXT_SESSION retained

## Generated artifacts

- Controlled HTTP loop, regression junit, twelve-turn comparison, and a fresh review archive

# What Was Tested

- **Focused tests:** Observation 10 passed. Grounded marking 12 passed. Focused command 596 passed, including predecessor modules 574 passed.
- **Broader relevant tests:** Combined before and after: 408 passed / 17 failed / 0 errors / 0 skipped (425 tests). New failing identities: none. Newly passing: none.
- **Full suite:** Not run
- **Runtime validation:** Controlled HTTP mark, observe, reload in a new process, remove, observe, and snapshot restore. Twelve-turn HTTP run. Publication fault injection.
- **Model/runtime boundary:** Zero provider calls; providers disabled and non-loopback sockets blocked.
- **New regressions:** []
- **Pre-existing failures:** The same 17 combined identities before and after. See REGRESSION_RESULTS.md.
- **Self-contained bundle review:** Reopen the archive and confirm milestone identity, the controlled HTTP loop, observation authority, confidentiality, publication repair, save/reload, snapshots, regressions, the twelve-turn comparison, ruleset portability, and the updated handoff.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No further authorization required for this bounded implementation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Natural-language removal is not implemented. A pronoun does not select an object. Ordinary observation does not certify that concealed markings are absent. Environmental materials, required consumption, and required mechanics stay unresolved.

## Pre-existing baseline

- Combined 17 failure identities. See REGRESSION_RESULTS.md.

# Missing Concepts / Future Capabilities

- Natural-language removal of a visible marking.

# What This Campaign Does NOT Prove

- Natural-language removal, environmental material inference, consumption, mechanical skill checks, a full suite, or live-model play.

# Recommended Next Step

Exactly one recommended next milestone: pr_play_grounded_marking_removal — natural-language removal of one visible marking through the existing removal service. Do not begin automatically.

# Review Bundle Contents

Bundle file count: `30`
Bundle ZIP size: `000000143453` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/BASELINE.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/BASELINE.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/OBSERVATION_INTEGRATION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/OBSERVATION_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/OBSERVATION_AUTHORITY.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/OBSERVATION_AUTHORITY.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/DISCLOSURE_PROJECTION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/DISCLOSURE_PROJECTION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/NARRATIVE_OBSERVATION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/NARRATIVE_OBSERVATION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/PUBLICATION_INTEGRITY.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/PUBLICATION_INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/CONTROLLED_HTTP_LOOP.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/CONTROLLED_HTTP_LOOP.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/CONFIDENTIALITY_VERIFICATION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/CONFIDENTIALITY_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/PERSISTENCE_VERIFICATION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/PERSISTENCE_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/PARAPHRASE_CONTROLS.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/PARAPHRASE_CONTROLS.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/RULESET_PORTABILITY.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/RULESET_PORTABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/REGRESSION_RESULTS.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/TWELVE_TURN_COMPARISON.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/TWELVE_TURN_COMPARISON.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/PERFORMANCE.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/PERFORMANCE.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/NEXT_STEP_DECISION.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_player_marking_observation/INTEGRITY.md`: Milestone report for player marking observation. Canonical source: `development/campaigns/product_realization/pr_play_player_marking_observation/INTEGRITY.md`.
- `support/artifacts/pr_play_player_marking_observation/controlled_http_loop.json`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/controlled_http_loop.json`.
- `support/artifacts/pr_play_player_marking_observation/twelve_turn_after.json`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/twelve_turn_after.json`.
- `support/artifacts/pr_play_player_marking_observation/performance.json`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/performance.json`.
- `support/artifacts/pr_play_player_marking_observation/regression_results.json`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/regression_results.json`.
- `support/artifacts/pr_play_player_marking_observation/source_changes.json`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/source_changes.json`.
- `support/artifacts/pr_play_player_marking_observation/before_combined_junit.xml`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/before_combined_junit.xml`.
- `support/artifacts/pr_play_player_marking_observation/after_combined_junit.xml`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/after_combined_junit.xml`.
- `support/artifacts/pr_play_player_marking_observation/after_focused_junit.xml`: Measured evidence or source for player marking observation. Canonical source: `artifacts/pr_play_player_marking_observation/after_focused_junit.xml`.
- `support/game/marking_observation.py`: Measured evidence or source for player marking observation. Canonical source: `game/marking_observation.py`.
- `support/tests/test_player_marking_observation.py`: Measured evidence or source for player marking observation. Canonical source: `tests/test_player_marking_observation.py`.
- `support/docs/NEXT_SESSION.md`: Measured evidence or source for player marking observation. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
