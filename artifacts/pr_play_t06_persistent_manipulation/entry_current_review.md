# Campaign

Campaign: PR-PLAY T04 Local Physical-Action Completion
Identifier: `pr_play_t04_local_action`
Date: 2026-11-09
Generated: 2026-11-09T05:20:00+00:00
Purpose: Authorize simple approach and contact with an accessible current-scene object as a transient outcome, without a scene transition or persistent mutation.

# Executive Summary

Original T04 HTTP refusal is replaced by an authoritative approach and contact: You walk over to the notice board and rest a hand on its frame. You remain in Cinderwatch Gate District. The unique local-object hit was previously declined before any physical outcome. The existing local-interaction owner now records that transient outcome when visibility and authored interactability are both positive. Three production files change. Combined tests 408 passed / 17 failed of 425; the 17 are a subset of the prior 20. Only T04 changes in the twelve-turn replay. T05 clue and T06 refusal stay. Zero live provider calls.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/local_interaction.py adds resolve_transient_local_action. conversational_orchestration.py consults it from the local-presence owner. api.py publishes the sealed narration through the existing immutable acceptance path.

## Validation changes

- 12 new local-action HTTP and resolver tests. One post-NPC handoff assertion now expects the repaired completion. Established main, authority, pre-seal, and T05 selections rerun.

## Tooling changes

- Provider-free twelve-turn runner under artifacts/pr_play_t04_local_action/run_sequence.py.

## Documentation changes

- Eleven reports and a prepended NEXT_SESSION entry. Historical NEXT_SESSION bytes remain the file suffix.

## Generated artifacts

- T04 before/after traces, twelve-turn comparison, source manifests, logical production diff, and junit.

# What Was Tested

- **Focused tests:** 12/12 new local-action tests. Post-NPC handoff and 15 T05 composition tests pass. Physical module 32/32.
- **Broader relevant tests:** Combined 425: 408 passed / 17 failed / 0 errors / 0 skipped. Main 222/13 unchanged. Authority 142/4. Pre-seal 17/0. No new failure identity.
- **Full suite:** Not run
- **Runtime validation:** Original T04 HTTP path completes approach and contact, stays in frontier_gate, seals the narration, and does not disclose the patrol clue. Twelve-turn published text changes only at T04. T05 clue, T06 refusal, T09 recall, and T11 travel remain.
- **Model/runtime boundary:** Zero live provider calls, retries, or added prompts. Twelve-turn network block list empty.
- **New regressions:** None in the established selection. Three prior greeting/refusal failures were not reproduced and are not claimed as a classification repair.
- **Pre-existing failures:** Seventeen baseline identities remain, including obsolete public-resolution assertions, the stew mismatch, and authority/publication KeyErrors.
- **Self-contained bundle review:** Reopen the archive and confirm the milestone, T04 before/after sentences, twelve-turn change limited to T04, 408/17 regression record, source manifests, and the preserved NEXT_SESSION suffix.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

No human decision is required before the next planned step.

# Known Problems / Unresolved Findings

## Campaign-specific

- Low-stakes approach and contact only. Copying, taking, opening, and the experimental physical owner remain outside this outcome. Scene JSON has no accessible:true flag; positive authored-interactable evidence is required.

## Pre-existing baseline

- T01/T07 missing narration; T02 unhelpful NPC; T06 persistent copying; T08 generic acknowledgment; T10 trade; T12 operational refusal; seventeen baseline failures.

# Missing Concepts / Future Capabilities

- No general physics engine, persistent gesture position, or unrestricted multi-action planner.

# What This Campaign Does NOT Prove

- Broad playability, independent held-out generalization, full-suite acceptance, live-provider behavior, or a Gameplay Benchmark result.

# Recommended Next Step

Exactly one proposed next action: investigate T06 copying the patrol warning onto clothing through its existing unsupported-manipulation owner. Preserve T04 and T05. Do not begin automatically.

# Review Bundle Contents

Bundle file count: `35`
Bundle ZIP size: `000000412133` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/ROOT_CAUSE.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/ROOT_CAUSE.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/ACTION_CONTRACT.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/ACTION_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/IMPLEMENTATION.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/IMPLEMENTATION.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/T04_BEFORE_AFTER.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/T04_BEFORE_AFTER.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/NEGATIVE_CONTROLS.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/NEGATIVE_CONTROLS.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/REGRESSION_RESULTS.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/TWELVE_TURN_COMPARISON.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/TWELVE_TURN_COMPARISON.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/PERFORMANCE.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/PERFORMANCE.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/NEXT_STEP_DECISION.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/INTEGRITY.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/INTEGRITY.md`.
- `support/game/local_interaction.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `game/local_interaction.py`.
- `support/game/conversational_orchestration.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `game/conversational_orchestration.py`.
- `support/game/api.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `game/api.py`.
- `support/tests/test_pr_play_t04_local_action.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `tests/test_pr_play_t04_local_action.py`.
- `support/tests/test_pr_play_post_npc_handoff.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `tests/test_pr_play_post_npc_handoff.py`.
- `support/docs/NEXT_SESSION.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/review_handoff_standard.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `docs/review_handoff_standard.md`.
- `support/artifacts/pr_play_t04_local_action/before/t04_before.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/before/t04_before.json`.
- `support/artifacts/pr_play_t04_local_action/t04_after.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/t04_after.json`.
- `support/artifacts/pr_play_t04_local_action/t04_comparison.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/t04_comparison.json`.
- `support/artifacts/pr_play_t04_local_action/twelve_turn_comparison.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/twelve_turn_comparison.json`.
- `support/artifacts/pr_play_t04_local_action/after/twelve_turn/sequence_summary.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/after/twelve_turn/sequence_summary.json`.
- `support/artifacts/pr_play_t04_local_action/before_source_manifest.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/before_source_manifest.json`.
- `support/artifacts/pr_play_t04_local_action/after_source_manifest.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/after_source_manifest.json`.
- `support/artifacts/pr_play_t04_local_action/source_changes.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/source_changes.json`.
- `support/artifacts/pr_play_t04_local_action/production.diff`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/production.diff`.
- `support/artifacts/pr_play_t04_local_action/entry_identity.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/entry_identity.json`.
- `support/artifacts/pr_play_t04_local_action/test_results.json`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/test_results.json`.
- `support/artifacts/pr_play_t04_local_action/after_regression_junit.xml`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/after_regression_junit.xml`.
- `support/artifacts/pr_play_t04_local_action/run_sequence.py`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/run_sequence.py`.
- `support/artifacts/pr_play_t04_local_action/entry/docs/NEXT_SESSION.md`: Supports the local-action repair, its HTTP evidence, or its regression record. Canonical source: `artifacts/pr_play_t04_local_action/entry/docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
