# Campaign

Campaign: Confirmed Baseline Repair
Identifier: `confirmed_baseline_repair_20260919`
Date: 2026-09-19
Generated: 2026-09-19T16:34:18.819777+00:00
Purpose: Repair only eight root causes confirmed against current product and architecture authority.

# Executive Summary

The suite moved from 36 to 23 failures with no new final failures. Seven RCs are complete. RC-04 is partial: its production FEM bypass is repaired, while its aggregate test remains red solely for two frozen test-only imports. RC-17 no longer crashes and emits the canonical unresolved NPC-pursuit fallback. RC-12 preserves Old Milestone destination context. Thirteen expected failing tests became green; no validation authority, semantic evaluator behavior, policy question, or unresolved case changed.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- Repaired NPC-pursuit fallback, destination grounding, policy provenance routing, visibility stamping ownership, and narrative-authenticity dependency direction.

## Validation changes

- Corrected canonical attribution interpretation, removed retired projection alias, and restored protected assertion recurrence routing.

## Tooling changes

- Added JUnit-backed repair ledger generator.

## Documentation changes

- Added canonical repair report.

## Generated artifacts

- Added pre/post JUnit, repair ledger, updated queue status, and review handoff.

# What Was Tested

- **Focused tests:** All directly repaired cluster tests and broader social, scene, visibility, attribution, narrative-authenticity, replay, recurrence, and layer-boundary suites passed except known out-of-scope reds.
- **Broader relevant tests:** Visibility and recurrence regression passes were clean after correcting an over-broad first implementation.
- **Full suite:** Pre: 6,445 collected, 6,310 passed, 36 failed, 99 skipped. Post: 6,445 collected, 6,323 passed, 23 failed, 99 skipped.
- **Runtime validation:** RC-17 reaches npc_pursuit_neutral_fallback without NameError; RC-12 emits destination-grounded Old Milestone narration.
- **Model/runtime boundary:** No model invocation occurred.
- **New regressions:** None in final JUnit. One intermediate transcript-order failure passed immediately in isolation and on final rerun.
- **Pre-existing failures:** Twenty-three remain intentionally outside repair scope or in RC-04's cleanup-only residue.
- **Self-contained bundle review:** PASS: the bundle contains the report, queue outcomes, complete repair ledger, frozen cleanup/policy inputs, and machine-readable pre/post baselines.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- RC-10 local raw-token policy.
- RC-21 destination redirect lead authority.

# Known Problems / Unresolved Findings

## Campaign-specific

- RC-04 aggregate test remains red for frozen test-only imports.

## Pre-existing baseline

- RC-11 and RC-13 remain unresolved; validation cleanup and governance drift remain.

# Missing Concepts / Future Capabilities

- Validation cleanup, governance repair, policy resolution, Calibration Round 2, State-to-Narration Consistency, and browser validation remain out of scope.

# What This Campaign Does NOT Prove

- That the remaining 23 failures are production defects.
- That stale tests or governance metadata have been repaired.
- That evaluator policy or validation authority changed.

# Recommended Next Step

Review the 36-to-23 repair delta, then authorize a separate Validation Cleanup and Governance Repair campaign.

# Review Bundle Contents

Bundle file count: `9`
Bundle ZIP size: `000000311695` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/confirmed_baseline_repair.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/confirmed_baseline_repair.md`.
- `support/artifacts/confirmed_baseline_repair/repair_ledger.json`: Accounts for all RC outcomes and the exact failure delta. Canonical source: `artifacts/confirmed_baseline_repair/repair_ledger.json`.
- `support/artifacts/confirmed_baseline_repair/pre_repair_suite.xml`: Authoritative starting baseline. Canonical source: `artifacts/confirmed_baseline_repair/pre_repair_suite.xml`.
- `support/artifacts/confirmed_baseline_repair/post_repair_suite.xml`: Authoritative ending baseline. Canonical source: `artifacts/confirmed_baseline_repair/post_repair_suite.xml`.
- `support/artifacts/baseline_triage/confirmed_repair_queue.json`: Preserves original queue and implementation outcomes. Canonical source: `artifacts/baseline_triage/confirmed_repair_queue.json`.
- `support/artifacts/baseline_triage/validation_cleanup_queue.json`: Shows work deliberately left untouched. Canonical source: `artifacts/baseline_triage/validation_cleanup_queue.json`.
- `support/artifacts/baseline_triage/policy_decisions.md`: Shows decisions deliberately left unresolved. Canonical source: `artifacts/baseline_triage/policy_decisions.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
