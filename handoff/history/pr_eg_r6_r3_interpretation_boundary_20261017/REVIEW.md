# Campaign

Campaign: PR-EG-R6-R3 — Conversational Interpretation Boundary Reassessment
Identifier: `pr_eg_r6_r3_interpretation_boundary_20261017`
Date: 2026-10-17
Generated: 2026-10-17T23:33:24.580953+00:00
Purpose: Compare structured planning, host compilation, and host-constrained candidate selection without a production rewrite.

# Executive Summary

**B — DECISION SUPPORTED WITH LIMITATIONS.** Architecture C, host-built candidates with provider selection, is the only option that materially improves referent binding under the pre-registered rule. On the frozen holdout it binds 22/30 dependent referents against Architecture A's 6/30 (paired net +16). Validation moves the same way (paired net +20). Security leaks are 0/396. The composite correction and follow-up scores are not a fair production comparison: A accepted 5/132 interpretations because production authorization rejects uncovered propositions, while C accepted 124/132 compiled selections. Absolute holdout correction success for C is still 6/13 and follow-up success 6/13. Ambiguity remains unsolved (C 2/13). Do not migrate production in this cycle.

Objective status: `B — DECISION SUPPORTED WITH LIMITATIONS`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- tests/test_pr_eg_r6_r3_harness.py

## Tooling changes

- experiments/pr_eg_r6_r3/corpus.py
- experiments/pr_eg_r6_r3/common.py
- experiments/pr_eg_r6_r3/architecture_a.py
- experiments/pr_eg_r6_r3/architecture_b.py
- experiments/pr_eg_r6_r3/architecture_c.py
- experiments/pr_eg_r6_r3/run_eval.py
- experiments/pr_eg_r6_r3/audit_grader.py
- experiments/pr_eg_r6_r3/CONTRACT.md
- tools/write_pr_eg_r6_r3_review.py

## Documentation changes

- 33 numbered review artifacts.

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** Harness tests passed without provider calls. Official comparison: 396 real provider calls.
- **Broader relevant tests:** The 14 inherited contract failures were re-read and not re-run. Five older inherited failures were not re-run.
- **Full suite:** Not run.
- **Runtime validation:** Isolated interpretation comparison, not production /api/chat qualification.
- **Model/runtime boundary:** gpt-4.1-mini, temperature 0, one call per turn, no retries.
- **New regressions:** []
- **Pre-existing failures:** 14 R6-R2-R2 contract-expectation failures plus 5 inherited failures.
- **Self-contained bundle review:** Structural package verification only. This is not independent human review.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Whether to authorize a gated Architecture C implementation that still ends in current bind and disclosure checks.

# Known Problems / Unresolved Findings

## Campaign-specific

- Composite success confounded by production source rejection on A.
- Ambiguity unsolved.
- Internal labels.
- C compiler does not yet pass production bind.

## Pre-existing baseline

- Fourteen red contract tests and five inherited failures.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Production qualification, human gold labels, equal acceptance gates, or ambiguity competence.

# Recommended Next Step

Stop after PR-EG-R6-R3. Await external review. Do not begin PR-EH or migrate the production planner.

# Review Bundle Contents

Bundle file count: `50`
Bundle ZIP size: `000000184663` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r3/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r3/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r3/02_REPOSITORY_BASELINE.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/02_REPOSITORY_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r3/03_HISTORICAL_FAILURE_INVENTORY.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/03_HISTORICAL_FAILURE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r3/04_FAILURE_TAXONOMY.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/04_FAILURE_TAXONOMY.md`.
- `support/artifacts/pr_eg_r6_r3/05_GRADER_RELIABILITY_AUDIT.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/05_GRADER_RELIABILITY_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r3/06_INDEPENDENT_EVALUATION_CONTRACT.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/06_INDEPENDENT_EVALUATION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r3/07_TEST_CORPUS_DESIGN.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/07_TEST_CORPUS_DESIGN.md`.
- `support/artifacts/pr_eg_r6_r3/08_CORPUS_PARTITIONING_AND_HASHES.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/08_CORPUS_PARTITIONING_AND_HASHES.md`.
- `support/artifacts/pr_eg_r6_r3/09_COMMON_EXPERIMENTAL_CONDITIONS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/09_COMMON_EXPERIMENTAL_CONDITIONS.md`.
- `support/artifacts/pr_eg_r6_r3/10_ARCHITECTURE_A_SPECIFICATION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/10_ARCHITECTURE_A_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r3/11_ARCHITECTURE_B_SPECIFICATION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/11_ARCHITECTURE_B_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r3/12_ARCHITECTURE_C_SPECIFICATION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/12_ARCHITECTURE_C_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r3/13_PROTOTYPE_ISOLATION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/13_PROTOTYPE_ISOLATION.md`.
- `support/artifacts/pr_eg_r6_r3/14_EXPERIMENTAL_OUTPUT_CONTRACT.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/14_EXPERIMENTAL_OUTPUT_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r3/15_PROVIDER_CALL_DISCIPLINE.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/15_PROVIDER_CALL_DISCIPLINE.md`.
- `support/artifacts/pr_eg_r6_r3/16_CORRECTION_EXPERIMENTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/16_CORRECTION_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r3/17_FOLLOW_UP_EXPERIMENTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/17_FOLLOW_UP_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r3/18_MULTI_ROLE_EXPERIMENTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/18_MULTI_ROLE_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r3/19_AMBIGUITY_EXPERIMENTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/19_AMBIGUITY_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r3/20_SECURITY_EXPERIMENTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/20_SECURITY_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r3/21_COST_AND_LATENCY.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/21_COST_AND_LATENCY.md`.
- `support/artifacts/pr_eg_r6_r3/22_GENERALIZATION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/22_GENERALIZATION.md`.
- `support/artifacts/pr_eg_r6_r3/23_PER_CASE_RESULTS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/23_PER_CASE_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r3/24_FAILURE_ATTRIBUTION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/24_FAILURE_ATTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r3/25_COMPARISON_MATRIX.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/25_COMPARISON_MATRIX.md`.
- `support/artifacts/pr_eg_r6_r3/26_STATISTICAL_LIMITATIONS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/26_STATISTICAL_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r3/27_REGRESSION_REVIEW.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/27_REGRESSION_REVIEW.md`.
- `support/artifacts/pr_eg_r6_r3/28_ARCHITECTURE_DECISION.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/28_ARCHITECTURE_DECISION.md`.
- `support/artifacts/pr_eg_r6_r3/29_IMPLEMENTATION_READINESS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/29_IMPLEMENTATION_READINESS.md`.
- `support/artifacts/pr_eg_r6_r3/30_REMAINING_UNKNOWNS.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/30_REMAINING_UNKNOWNS.md`.
- `support/artifacts/pr_eg_r6_r3/31_RECOMMENDED_NEXT_CYCLE.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/31_RECOMMENDED_NEXT_CYCLE.md`.
- `support/artifacts/pr_eg_r6_r3/32_FINAL_VERDICT.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/32_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r3/33_SOURCE_AND_EVIDENCE_INVENTORY.md`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/33_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r3/summary.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/summary.json`.
- `support/artifacts/pr_eg_r6_r3/freeze.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/freeze.json`.
- `support/artifacts/pr_eg_r6_r3/per_case_results.jsonl`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/per_case_results.jsonl`.
- `support/artifacts/pr_eg_r6_r3/grader_reliability_audit.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/grader_reliability_audit.json`.
- `support/artifacts/pr_eg_r6_r3/development_cases.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/development_cases.json`.
- `support/artifacts/pr_eg_r6_r3/validation_cases.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/validation_cases.json`.
- `support/artifacts/pr_eg_r6_r3/holdout_cases.json`: Interpretation-boundary comparison evidence. Canonical source: `artifacts/pr_eg_r6_r3/holdout_cases.json`.
- `support/experiments/pr_eg_r6_r3/CONTRACT.md`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/CONTRACT.md`.
- `support/experiments/pr_eg_r6_r3/corpus.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/corpus.py`.
- `support/experiments/pr_eg_r6_r3/architecture_a.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/architecture_a.py`.
- `support/experiments/pr_eg_r6_r3/architecture_b.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/architecture_b.py`.
- `support/experiments/pr_eg_r6_r3/architecture_c.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/architecture_c.py`.
- `support/experiments/pr_eg_r6_r3/common.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/common.py`.
- `support/experiments/pr_eg_r6_r3/run_eval.py`: Interpretation-boundary comparison evidence. Canonical source: `experiments/pr_eg_r6_r3/run_eval.py`.
- `support/tests/test_pr_eg_r6_r3_harness.py`: Interpretation-boundary comparison evidence. Canonical source: `tests/test_pr_eg_r6_r3_harness.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r3/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r3/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
