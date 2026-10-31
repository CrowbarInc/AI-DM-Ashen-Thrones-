# Campaign

Campaign: PR-EG-R6-R3-R1 — Host-Constrained Candidate Integration
Identifier: `pr_eg_r6_r3_r1_candidate_integration_20261017`
Date: 2026-10-17
Generated: 2026-10-18T02:29:55.191375+00:00
Purpose: Integrate host-constrained candidate selection into the production conversational pipeline without bypassing authorization.

# Executive Summary

Host-constrained candidate selection is now a third routing mode. It is off unless `ASHEN_HOST_CONSTRAINED_CANDIDATES` is set, and it still ends in the existing source, disclosure, and sealed-response pipeline.

On 150 fresh `/api/chat` turns, integrity held: 0 unauthorized disclosures, 0 canonical mutations, 0 clue discoveries, and 0 final-response mismatches. Conversational gates did not. Independent labels scored operation classification 99/150, role preservation 83/150, answer success 70/150, corrections 13/25, and follow-ups 26/50. A 60-turn matched comparison did not beat the existing semantic planner.

Verdict: C — BELOW ACCEPTANCE. The gate stays off. Do not begin PR-EH.

Objective status: `C — BELOW ACCEPTANCE`.

# Changes Made

## Production changes

- game/host_constrained_candidates.py
- game/unified_semantic_planning.py

## Validation changes

- tests/test_pr_eg_r6_r3_r1_candidates.py

## Tooling changes

- tools/qualify_pr_eg_r6_r3_r1.py
- tools/score_pr_eg_r6_r3_r1.py
- tools/write_pr_eg_r6_r3_r1_review.py

## Documentation changes

- 36 numbered review artifacts.

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** 68 candidate tests passed without network calls.
- **Broader relevant tests:** Semantic planner, operation, disclosure, and provenance suites passed except the 14 previously explained contract failures.
- **Full suite:** Not run.
- **Runtime validation:** 150 fresh /api/chat turns and 60 matched planner turns, real provider.
- **Model/runtime boundary:** Configured repo model, temperature 0 for candidate selection.
- **New regressions:** []
- **Pre-existing failures:** 14 R6-R2-R2 contract tests still expect clarification and receive unknown.
- **Self-contained bundle review:** Structural package verification only. This is not independent human review.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Whether to keep developing candidate selection or leave the existing semantic planner as the only gated path.
- Whether the unqualified-historical-id test should stay stricter than silent-focus preservation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Matched production correctness did not improve.
- Candidate input tokens miss the p95 budget.
- Public facts are often dropped because source interpretations are missing.

## Pre-existing baseline

- Fourteen red contract tests remain fail-closed unknowns.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Human playability, a 90% operation rate, or a cost reduction against the current planner.

# Recommended Next Step

Stop after PR-EG-R6-R3-R1. Leave the candidate gate off. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `53`
Bundle ZIP size: `000001895305` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r3_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r3_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/02_REPOSITORY_BASELINE.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/02_REPOSITORY_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r3_r1/03_ARCHITECTURE_C_PROTOTYPE_AUDIT.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/03_ARCHITECTURE_C_PROTOTYPE_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r3_r1/04_PRODUCTION_INTEGRATION_DESIGN.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/04_PRODUCTION_INTEGRATION_DESIGN.md`.
- `support/artifacts/pr_eg_r6_r3_r1/05_FEATURE_GATE_STRATEGY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/05_FEATURE_GATE_STRATEGY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/06_CANDIDATE_GENERATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/06_CANDIDATE_GENERATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/07_CANDIDATE_REPRESENTATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/07_CANDIDATE_REPRESENTATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/08_PROVIDER_SELECTION_CONTRACT.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/08_PROVIDER_SELECTION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r3_r1/09_HOST_VALIDATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/09_HOST_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/10_NEW_QUESTIONS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/10_NEW_QUESTIONS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/11_CORRECTIONS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/11_CORRECTIONS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/12_MULTI_ROLE_PROPOSITIONS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/12_MULTI_ROLE_PROPOSITIONS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/13_FOLLOW_UPS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/13_FOLLOW_UPS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/14_GENUINE_AMBIGUITY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/14_GENUINE_AMBIGUITY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/15_UNSUPPORTED_TRANSFORMATIONS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/15_UNSUPPORTED_TRANSFORMATIONS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/16_OPEN_WORLD_GENERALIZATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/16_OPEN_WORLD_GENERALIZATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/17_SOURCE_RESOLUTION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/17_SOURCE_RESOLUTION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/18_DISCLOSURE_AUTHORIZATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/18_DISCLOSURE_AUTHORIZATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/19_ANSWER_SUFFICIENCY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/19_ANSWER_SUFFICIENCY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/20_FINAL_RESPONSE_INTEGRITY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/20_FINAL_RESPONSE_INTEGRITY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/21_REFERENT_PERSISTENCE.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/21_REFERENT_PERSISTENCE.md`.
- `support/artifacts/pr_eg_r6_r3_r1/22_LEGACY_REGRESSION_DISPOSITION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/22_LEGACY_REGRESSION_DISPOSITION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/23_CONTROLLED_TESTS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/23_CONTROLLED_TESTS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/24_FROZEN_HOLDOUTS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/24_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/25_MATCHED_PRODUCTION_COMPARISON.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/25_MATCHED_PRODUCTION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r3_r1/26_FRESH_PROVIDER_QUALIFICATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/26_FRESH_PROVIDER_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/27_INDEPENDENT_EVALUATION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/27_INDEPENDENT_EVALUATION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/28_DIALOGUE_QUALITY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/28_DIALOGUE_QUALITY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/29_PERFORMANCE.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/29_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r3_r1/30_REGRESSION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/30_REGRESSION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/31_ACCEPTANCE_GATES.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/31_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r3_r1/32_FAILURE_ATTRIBUTION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/32_FAILURE_ATTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/33_REMAINING_LIMITATIONS.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/33_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r3_r1/34_RECOMMENDED_NEXT_ACTION.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/34_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r3_r1/35_FINAL_VERDICT.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/35_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r3_r1/36_SOURCE_AND_EVIDENCE_INVENTORY.md`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/36_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r3_r1/freeze.json`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/freeze.json`.
- `support/artifacts/pr_eg_r6_r3_r1/frozen_production_holdouts.json`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/frozen_production_holdouts.json`.
- `support/artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r3_r1/fresh/live_usage.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/fresh/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r3_r1/fresh/live_status.json`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/fresh/live_status.json`.
- `support/artifacts/pr_eg_r6_r3_r1/fresh/semantic_traces.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/fresh/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r3_r1/matched_planner/live_turns.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/matched_planner/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r3_r1/matched_planner/live_usage.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/matched_planner/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r3_r1/matched_planner/live_status.json`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/matched_planner/live_status.json`.
- `support/artifacts/pr_eg_r6_r3_r1/matched_candidate_60.jsonl`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `artifacts/pr_eg_r6_r3_r1/matched_candidate_60.jsonl`.
- `support/game/host_constrained_candidates.py`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `game/host_constrained_candidates.py`.
- `support/game/unified_semantic_planning.py`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/tests/test_pr_eg_r6_r3_r1_candidates.py`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `tests/test_pr_eg_r6_r3_r1_candidates.py`.
- `support/tools/qualify_pr_eg_r6_r3_r1.py`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `tools/qualify_pr_eg_r6_r3_r1.py`.
- `support/tools/score_pr_eg_r6_r3_r1.py`: PR-EG-R6-R3-R1 integration and production-path evidence. Canonical source: `tools/score_pr_eg_r6_r3_r1.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r3_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r3_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
