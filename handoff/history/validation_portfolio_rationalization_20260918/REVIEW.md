# Campaign

Campaign: Validation Portfolio Rationalization
Identifier: `validation_portfolio_rationalization_20260918`
Date: 2026-09-18
Generated: 2026-09-18T05:00:00+00:00
Purpose: Determine which validation families Ashen Thrones should carry into Product Realization and 1.0, with intentional claim boundaries and authority.

# Executive Summary

The audit identifies 19 validation families. RETAIN: component contracts, API integration, scenario spine, manual gauntlets, semantic calibration, reactive/adversarial players, Validation Evidence, and Review Handoff. CONSOLIDATE: replay diagnostics, N1 synthetic spine, and behavioral gauntlet. MODERNIZE: final emission, content lint, and architecture governance. RECLASSIFY: protected replay, playability, and synthetic sessions. QUARANTINE: ownership/import governance pending policy confirmation. RETIRE: historical BW/BZ closeout-document assertions after provenance review. The current 49-failure baseline maps to 7 likely product regressions, 9 likely architecture regressions, and 33 stale, administrative, registry, fixture, or uncertain failures. The target architecture preserves separate governance, structural, runtime, state/world, semantic, long-session, rendered-experience, and human-review layers without an aggregate quality score.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No validator, test, fixture, CI gate, evaluator, threshold, calibration policy, gameplay path, prompt, or semantic gate changed.
- Classified the existing portfolio and current red baseline without disabling or repairing failures.

## Tooling changes

- Added a registry validator and deterministic Markdown renderer for portfolio and failure-classification data.

## Documentation changes

- Added the primary rationalization report, generated family-registry view, failure summary, target architecture, staged plan, risks, and compact human decision surface.

## Generated artifacts

- Generated the current failure summary and standard review handoff from explicit canonical sources.

# What Was Tested

- **Focused tests:** 22 validation-portfolio and review-handoff focused tests passed.
- **Broader relevant tests:** 48 portfolio, review-handoff, evidence-standard, semantic-calibration, and reactive-player contract tests passed.
- **Full suite:** 49 failures from 6,433 collected cases, classified individually; no baseline failure was repaired or waived.
- **Runtime validation:** No gameplay rerun was performed; this architectural audit consumed preserved behavioral evidence.
- **Model/runtime boundary:** No model invocation occurred in this campaign.
- **New regressions:** No campaign-specific regression was found in focused verification.
- **Pre-existing failures:** 7 likely product, 9 likely architecture, 13 documentation drift, 9 registry/governance drift, 9 stale expectation, 1 stale fixture, and 1 uncertain.
- **Self-contained bundle review:** PASS: the final bundle contains the primary report, complete 19-family registry, exact 49-failure classification and summary, prior audit context, standards, tooling, and focused tests needed to answer the campaign review questions without repository archaeology.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Approve archival review followed by retirement of BW/BZ historical closeout-document assertions as current gates.
- Reaffirm which ownership facades and write-path rules remain intentional after Architecture Reconciliation before repairing or waiving violations.
- Confirm that automated playability PASS remains supporting evidence rather than an independent semantic campaign gate.
- Approve consolidation of replay projection/trend diagnostics under a named minimal authoritative invariant set while preserving unique recurrence history.

# Known Problems / Unresolved Findings

## Campaign-specific

- Failure root causes were classified by available evidence but not reproduced individually; 23 classifications are medium confidence and 2 are low confidence.

## Pre-existing baseline

- The repository full suite remains red with 49 failures; likely current product and architecture defects are prominently preserved in the classification.

# Missing Concepts / Future Capabilities

- State-to-narration and NPC/hidden-fact consistency authority.
- Rendered browser workflow validation.
- Long-session semantic continuity authority.
- Player-to-GM versus character authority and generalized ambiguity/clarification calibration.
- Trustworthy realistic-human-player evidence beyond manual sessions.

# What This Campaign Does NOT Prove

- That all 49 failure root causes are final or that any failing test may be ignored.
- That the proposed retirements, consolidations, modernizations, or reclassifications have been approved or implemented.
- Broad gameplay quality, state/narration consistency, rendered UI usability, or 1.0 readiness.
- That reduced maintenance cost is more important than unique evidence preservation.

# Recommended Next Step

Obtain human decisions on the four grouped questions, then execute only the approved staged rationalization work beginning with provenance-safe closeout assertion retirement and claim reclassification. Do not start Calibration Round 2 or new gap validators before review.

# Review Bundle Contents

Bundle file count: `13`
Bundle ZIP size: `000000070214` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/validation_portfolio_rationalization.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/validation_portfolio_rationalization.md`.
- `support/data/validation/validation_family_registry.json`: Machine-readable record for all 19 families and their claim, authority, disposition, risk, and rationale. Canonical source: `data/validation/validation_family_registry.json`.
- `support/docs/validation_family_registry.md`: Concise human-readable registry and disposition counts. Canonical source: `docs/validation_family_registry.md`.
- `support/artifacts/validation_portfolio/current_failure_classification.json`: Maps every observed full-suite failure to a family, likely cause, confidence, and rationale. Canonical source: `artifacts/validation_portfolio/current_failure_classification.json`.
- `support/artifacts/validation_portfolio/current_failure_summary.md`: Summarizes the exact 49-failure baseline by cause, confidence, and family. Canonical source: `artifacts/validation_portfolio/current_failure_summary.md`.
- `support/docs/validation_reliability_audit.md`: Provides traced PASS semantics, mock boundaries, and validation-lane reliability findings reused here. Canonical source: `docs/validation_reliability_audit.md`.
- `support/docs/simulated_playtest_observability_audit.md`: Provides the earlier evidence-producer and observability baseline. Canonical source: `docs/simulated_playtest_observability_audit.md`.
- `support/docs/validation_evidence_standard.md`: Defines inspectability requirements for behavioral claims. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/review_handoff_standard.md`: Defines delivery requirements used by this campaign. Canonical source: `docs/review_handoff_standard.md`.
- `support/tools/build_validation_portfolio.py`: Validates registry completeness and renders internally consistent summaries. Canonical source: `tools/build_validation_portfolio.py`.
- `support/tests/test_validation_portfolio.py`: Protects family coverage, disposition safeguards, failure reconciliation, architecture references, and handoff inclusion. Canonical source: `tests/test_validation_portfolio.py`.

## Explicit omissions

- `docs/validation_portfolio_rationalization.md`: duplicate content of docs/validation_portfolio_rationalization.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
