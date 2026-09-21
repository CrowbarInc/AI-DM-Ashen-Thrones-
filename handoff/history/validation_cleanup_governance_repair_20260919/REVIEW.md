# Campaign

Campaign: Validation Cleanup & Governance Repair
Identifier: `validation_cleanup_governance_repair_20260919`
Date: 2026-09-19
Generated: 2026-09-19T17:45:37.557914+00:00
Purpose: Repair the 17 authorized validation, fixture, expectation, governance, and test-only architecture failures while preserving six policy/unresolved reds.

# Executive Summary

The suite moved from 23 to 6 failures. All 17 authorized failures were cleaned with no contradictions, unexpected greens, or new reds. RC-04 test-only residue is gone without exemptions. The remaining six failures are exactly RC-10, RC-11, RC-13, and RC-21. Production behavior and validation authority did not change; no test was skipped, xfailed, deleted, or weakened for appearance.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- Added read-facade exports and routed narrative-authenticity telemetry through the declared observability facade; no gameplay semantics changed.

## Validation changes

- Modernized eight stale expectations, one fixture, three validator failures, four governance failures, and the RC-04 aggregate residue.

## Tooling changes

- Added JUnit-backed cleanup ledger and summary generation with three accounting locks.

## Documentation changes

- Added the canonical cleanup report and reconciled BQC4, BU4, and protected replay governance.

## Generated artifacts

- Added pre/post JUnit, cleanup ledger, cleanup summary, test-order observations, and review handoff.

# What Was Tested

- **Focused tests:** All actionable cleanup tests and their consumers passed. BV2C/BV10/BV14 synthetic invalid-import controls still detect violations.
- **Broader relevant tests:** Final-emission, replay projection, ownership registry, failure-classification, playability, social lead, and validation-layer suites passed outside the frozen cases.
- **Full suite:** Pre: 6,445 collected, 6,323 passed, 23 failed, 99 skipped. Post: 6,448 collected, 6,343 passed, 6 failed, 99 skipped; three new passing accounting tests explain collection growth.
- **Runtime validation:** No product runtime behavior was intentionally changed.
- **Model/runtime boundary:** No model invocation occurred.
- **New regressions:** None.
- **Pre-existing failures:** Six remain deliberately red: RC-10 and RC-21 policy cases; RC-11 and RC-13 unresolved investigations.
- **Self-contained bundle review:** PASS: the bundle contains the canonical report, exact JUnit baselines, complete ledger and summary, test-order observation, source cleanup queue, and frozen policy record.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- RC-10 local raw-token policy.
- RC-21 destination redirect lead authority.

# Known Problems / Unresolved Findings

## Campaign-specific

- None reported.

## Pre-existing baseline

- RC-11 opening acceptance sequence remains unresolved.
- RC-13 long-session diagnostic threshold remains unresolved.

# Missing Concepts / Future Capabilities

- Policy resolution, unresolved-root-cause investigation, dedicated test-isolation investigation, Calibration Round 2, and State-to-Narration Consistency remain out of scope.

# What This Campaign Does NOT Prove

- Which policy choice RC-10 or RC-21 should adopt.
- The root cause of RC-11 or RC-13.
- That the earlier non-repeating combat transcript symptom is systemic.

# Recommended Next Step

Review the trustworthy six-red baseline, then authorize one separate policy or unresolved-root-cause campaign.

# Review Bundle Contents

Bundle file count: `10`
Bundle ZIP size: `000000308676` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/validation_cleanup_and_governance_repair.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/validation_cleanup_and_governance_repair.md`.
- `support/artifacts/validation_cleanup/cleanup_ledger.json`: Accounts for all 17 actionable failures and their authority. Canonical source: `artifacts/validation_cleanup/cleanup_ledger.json`.
- `support/artifacts/validation_cleanup/cleanup_summary.json`: Reconciles exact pre/post counts and remaining reds. Canonical source: `artifacts/validation_cleanup/cleanup_summary.json`.
- `support/artifacts/validation_cleanup/pre_cleanup_suite.xml`: Authoritative starting baseline. Canonical source: `artifacts/validation_cleanup/pre_cleanup_suite.xml`.
- `support/artifacts/validation_cleanup/post_cleanup_suite.xml`: Authoritative ending baseline. Canonical source: `artifacts/validation_cleanup/post_cleanup_suite.xml`.
- `support/artifacts/validation_cleanup/test_order_observations.md`: Preserves the bounded mutable-state observation. Canonical source: `artifacts/validation_cleanup/test_order_observations.md`.
- `support/artifacts/baseline_triage/validation_cleanup_queue.json`: Preserves the authorized cleanup inventory. Canonical source: `artifacts/baseline_triage/validation_cleanup_queue.json`.
- `support/artifacts/baseline_triage/policy_decisions.md`: Preserves the policy decisions left open. Canonical source: `artifacts/baseline_triage/policy_decisions.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
