# Campaign

Campaign: RC-11 / RC-13 Expectation Maintenance & Governance Drift Triage
Identifier: `rc11_rc13_expectation_maintenance_20260919`
Date: 2026-09-19
Generated: 2026-09-19T19:00:00Z
Purpose: Modernize RC-11 and RC-13 expectations and triage the unrelated governance-document failure without changing product behavior or deciding RC-10/RC-21.

# Executive Summary

The baseline moved from seven failures to four. RC-11 now separately asserts identical accepted text/debug previews and the complete governed write-site attribution row, preserving both behavioral and provenance coverage. RC-13 derives its mutation aggregate from six named subtype caps, reconciles aggregate and subtype totals, rejects unknown kinds, and retains excessive-subtype controls. GD-01 was high-confidence STALE_EXPECTATION: its CO98 heading check lagged the active CO99 generated governance context, so only the validator advanced. Product behavior and validation authority did not change; no test was skipped, xfailed, or deleted. The four remaining failures are exactly RC-10 and RC-21 policy decisions; no unexplained technical defect remains red. The next justified campaign is policy resolution after review.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Modernized RC-11 behavioral/provenance assertions.
- Modernized RC-13 subtype-derived lineage profile and added two negative controls.
- Advanced GD-01 validator from CO98 to active CO99 context while preserving substantive governance locks.

## Tooling changes

- No changes in this category.

## Documentation changes

- Added canonical maintenance report, ledger, governance triage, baseline comparison, remaining-red audit, and command record.

## Generated artifacts

- Added pre/post and focused JUnit evidence.

# What Was Tested

- **Focused tests:** RC-11 family: 85 passed. RC-13 family: 18 passed. Governance family: 44 passed. Replay profile/boundary: 8 passed.
- **Broader relevant tests:** Opening fallback, attribution, replay projection, failure-classification governance, and replay ownership boundaries passed.
- **Full suite:** Pre: 6,448 collected, 6,342 passed, 7 failed, 99 skipped. Post: 6,450 collected, 6,347 passed, 4 failed, 99 skipped. Two new passing negative controls explain collection growth.
- **Runtime validation:** Existing deterministic 25-turn replay passed without runtime changes.
- **Model/runtime boundary:** No external model invocation; deterministic test stubs only.
- **New regressions:** None.
- **Pre-existing failures:** RC-10 (one) and RC-21 (three) remain intentionally red and untouched.
- **Self-contained bundle review:** PASS: report, ledger, GD-01 triage, exact baselines, remaining-red audit, commands, and focused evidence are bundled.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- RC-10 local raw-token boundary policy.
- RC-21 destination-redirect authority policy.

# Known Problems / Unresolved Findings

## Campaign-specific

- None reported.

## Pre-existing baseline

- RC-10: tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only
- RC-21: tests/test_social_destination_redirect_leads.py::test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry
- RC-21: tests/test_social_destination_redirect_leads.py::test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows
- RC-21: tests/test_social_destination_redirect_leads.py::test_destination_lead_distinct_from_existing_milestone_pending

# Missing Concepts / Future Capabilities

- Policy resolution, Calibration Round 2, State-to-Narration Consistency, and product realization are out of scope.

# What This Campaign Does NOT Prove

- Which RC-10 or RC-21 policy option should be selected.
- That policy resolution can occur without its own product and validation review.

# Recommended Next Step

Review the policy-only technical baseline, then authorize a separate RC-10 / RC-21 Policy Resolution campaign.

# Review Bundle Contents

Bundle file count: `13`
Bundle ZIP size: `000000293446` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/rc11_rc13_expectation_maintenance_and_governance_drift_triage.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/rc11_rc13_expectation_maintenance_and_governance_drift_triage.md`.
- `support/artifacts/expectation_maintenance/maintenance_ledger.json`: Records authority, old/new expectations, controls, and impact for all three cases. Canonical source: `artifacts/expectation_maintenance/maintenance_ledger.json`.
- `support/artifacts/expectation_maintenance/governance_drift_triage.json`: Documents GD-01 evidence, classification, confidence, and repair. Canonical source: `artifacts/expectation_maintenance/governance_drift_triage.json`.
- `support/artifacts/expectation_maintenance/baseline_comparison.json`: Reconciles exact pre/post suite counts. Canonical source: `artifacts/expectation_maintenance/baseline_comparison.json`.
- `support/artifacts/expectation_maintenance/remaining_red_audit.json`: Accounts for every final failure and technical-baseline status. Canonical source: `artifacts/expectation_maintenance/remaining_red_audit.json`.
- `support/artifacts/expectation_maintenance/commands_executed.md`: Preserves exact verification commands. Canonical source: `artifacts/expectation_maintenance/commands_executed.md`.
- `support/artifacts/expectation_maintenance/pre_maintenance_suite.xml`: Authoritative seven-red starting baseline. Canonical source: `artifacts/expectation_maintenance/pre_maintenance_suite.xml`.
- `support/artifacts/expectation_maintenance/post_maintenance_suite.xml`: Authoritative four-red ending baseline. Canonical source: `artifacts/expectation_maintenance/post_maintenance_suite.xml`.
- `support/artifacts/expectation_maintenance/focused_rc11.xml`: Opening and attribution family verification. Canonical source: `artifacts/expectation_maintenance/focused_rc11.xml`.
- `support/artifacts/expectation_maintenance/focused_rc13.xml`: Replay, projection, positive, and negative control verification. Canonical source: `artifacts/expectation_maintenance/focused_rc13.xml`.
- `support/artifacts/expectation_maintenance/focused_governance.xml`: Failure-classification and replay-boundary governance verification. Canonical source: `artifacts/expectation_maintenance/focused_governance.xml`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
