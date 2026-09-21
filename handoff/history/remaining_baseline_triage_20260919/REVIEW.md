# Campaign

Campaign: Remaining Baseline Triage and Root-Cause Confirmation
Identifier: `remaining_baseline_triage_20260919`
Date: 2026-09-19
Generated: 2026-09-19T15:43:43.244741+00:00
Purpose: Convert the 36-test red baseline into evidence-backed repair, cleanup, policy, and unresolved queues without repairing behavior.

# Executive Summary

The baseline remains 36 failures. The investigation maps every failure exactly once into 25 root-cause clusters: 4 product-defect failures, 10 architecture-defect failures, 3 validation-defect failures, 8 stale expectations, 1 stale fixture, 4 governance-drift failures, 4 policy-decision failures, and 2 unresolved failures. The six ownership/import failures split into current production facade violations, test-helper validation defects, registry drift, and direct unstamped writes. No repair was implemented.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- Added registry and queue generator plus five accounting tests.

## Documentation changes

- Added canonical triage report.

## Generated artifacts

- Added investigation registry, root-cause clusters, repair queue, cleanup queue, policy queue, and JUnit baselines.

# What Was Tested

- **Focused tests:** Five triage-tooling tests passed.
- **Broader relevant tests:** All 36 failures reproduced in the full pre-triage suite.
- **Full suite:** Pre: 6,440 collected, 6,305 passed, 36 failed, 99 skipped. Post: 6,445 collected, 6,310 passed, 36 failed, 99 skipped. The five added cases are passing triage-tooling tests.
- **Runtime validation:** Existing deterministic tests only; no runtime semantics changed.
- **Model/runtime boundary:** No model invocation occurred.
- **New regressions:** None; the exact failure set is unchanged.
- **Pre-existing failures:** All 36 failures remain intentionally unrepaired.
- **Self-contained bundle review:** PASS: report, per-test registry, queues, policy questions, and pre/post JUnit are bundled.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Define the permitted local raw-token boundary.
- Choose authoritative destination-redirect lead representation.

# Known Problems / Unresolved Findings

## Campaign-specific

- None reported.

## Pre-existing baseline

- RC-11 opening debug ordering and RC-13 long-session diagnostic divergence remain unresolved.

# Missing Concepts / Future Capabilities

- Repair implementation, validation cleanup, Calibration Round 2, State-to-Narration Consistency, and browser validation are out of scope.

# What This Campaign Does NOT Prove

- That all failures are production defects.
- That gameplay or architecture improved.
- That policy-decision or unresolved cases are safe to change.

# Recommended Next Step

Review the confirmed queue, then repair approved P0/P1 root causes in a separate campaign.

# Review Bundle Contents

Bundle file count: `11`
Bundle ZIP size: `000000321600` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/remaining_baseline_triage_and_root_cause_confirmation.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/remaining_baseline_triage_and_root_cause_confirmation.md`.
- `support/artifacts/baseline_triage/failure_investigation_registry.json`: Accounts for all failures and clusters with evidence. Canonical source: `artifacts/baseline_triage/failure_investigation_registry.json`.
- `support/artifacts/baseline_triage/confirmed_repair_queue.json`: Contains only confirmed product and architecture repairs. Canonical source: `artifacts/baseline_triage/confirmed_repair_queue.json`.
- `support/artifacts/baseline_triage/confirmed_repair_queue.md`: Readable repair queue. Canonical source: `artifacts/baseline_triage/confirmed_repair_queue.md`.
- `support/artifacts/baseline_triage/validation_cleanup_queue.json`: Separates non-product work. Canonical source: `artifacts/baseline_triage/validation_cleanup_queue.json`.
- `support/artifacts/baseline_triage/policy_decisions.md`: Preserves genuine project-intent questions. Canonical source: `artifacts/baseline_triage/policy_decisions.md`.
- `support/artifacts/baseline_triage/pre_triage_suite.xml`: Machine-readable starting baseline. Canonical source: `artifacts/baseline_triage/pre_triage_suite.xml`.
- `support/artifacts/baseline_triage/post_triage_suite.xml`: Machine-readable ending baseline. Canonical source: `artifacts/baseline_triage/post_triage_suite.xml`.
- `support/tests/test_remaining_baseline_triage.py`: Checks complete accounting and queue consistency. Canonical source: `tests/test_remaining_baseline_triage.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
