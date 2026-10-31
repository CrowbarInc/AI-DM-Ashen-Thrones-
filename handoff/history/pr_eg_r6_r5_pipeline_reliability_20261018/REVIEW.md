# Campaign

Campaign: PR-EG-R6-R5 — Conversational Pipeline Reliability
Identifier: `pr_eg_r6_r5_pipeline_reliability_20261018`
Date: 2026-10-18
Generated: 2026-10-19T01:02:01.408662+00:00
Purpose: End-to-end causal diagnosis of player-facing dialogue loss. No production repair and no PR-EH.

# Executive Summary

**B — DIAGNOSIS SUPPORTED WITH LIMITATIONS.** Production replies succeed on 59/164 frozen turns (36.0%). Validation is 18/54. Corrections are 0/25. Restricted text was not disclosed. Substituting a host-authorized plan raises validation to 44/54 (I8) and 45/54 with expression off (I10B). Correcting every upstream input and still running authorization reaches 32/54 (I9). Question-only and source-only substitutions lose successes (net -2 and -3); both together gain 8, with 7 only in the combination. Source-id filtering changes nothing (I4 net 0). The loss is in referent bind, witness checks, and question-to-source correspondence. Expression is not the main loss. Human review is pending. No production code was changed.

Objective status: `B — DIAGNOSIS SUPPORTED WITH LIMITATIONS`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Offline diagnostic tests for quotas, gold disclosure limits, and the ignorance rubric.

## Tooling changes

- Diagnostic harness, scorer, analyzer, and report writer under experiments/pr_eg_r6_r5.

## Documentation changes

- Artifacts 01-37 and a 32-item human review packet marked pending.

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** tests/test_pr_eg_r6_r5_diagnostic.py: 4 passed.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** 164 real-provider baseline turns; 756 validation intervention rows; 54 expression-control calls. 0 restricted disclosures.
- **Model/runtime boundary:** gpt-4.1-mini (gpt-4.1-mini-2025-04-14); semantic temperature 0; SDK retries disabled.
- **New regressions:** No production modules were modified.
- **Pre-existing failures:** Working tree already had 1765 dirty entries at baseline capture. Full suite not reassessed.
- **Self-contained bundle review:** 37 numbered artifacts, frozen corpus hash, raw baseline and paired intervention rows, and manifest hashes.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Adjudicate the 32-item packet.
- Accept or reject the repair order: bind/witness first, joint correspondence second, expression guard third.
- Do not start PR-EH from this packet alone.

# Known Problems / Unresolved Findings

## Campaign-specific

- Human review pending.
- F18 covers 20 of 105 baseline failures.
- Two validation turns never entered the planner.
- c06t06 is PARTIAL with no eligible source.
- I6 on compact payloads patches coverage() only.
- Schema-rejected intervention file is archived and not scored.

## Pre-existing baseline

- Extensive unrelated working-tree changes predate this cycle.
- Unified semantic planning defaults off; this baseline enabled it as the current information path.

# Missing Concepts / Future Capabilities

- A measured local patch for bind and named coverage.
- Human adjudication of F18.

# What This Campaign Does NOT Prove

- That a specific patch will reach the I8 rate.
- Production readiness, holdout improvement, or a reason to replace the expression boundary.

# Recommended Next Step

Stop after PR-EG-R6-R5 and await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `56`
Bundle ZIP size: `000000406762` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r5/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r5/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r5/02_REPOSITORY_BASELINE.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/02_REPOSITORY_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r5/03_PRODUCTION_PIPELINE_MAP.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/03_PRODUCTION_PIPELINE_MAP.md`.
- `support/artifacts/pr_eg_r6_r5/04_INSTRUMENTATION_AUDIT.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/04_INSTRUMENTATION_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r5/05_EVALUATION_CONTRACT.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/05_EVALUATION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r5/06_CORPUS_DESIGN.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/06_CORPUS_DESIGN.md`.
- `support/artifacts/pr_eg_r6_r5/07_CONVERSATIONAL_CONTEXT.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/07_CONVERSATIONAL_CONTEXT.md`.
- `support/artifacts/pr_eg_r6_r5/08_WORLD_FIXTURES.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/08_WORLD_FIXTURES.md`.
- `support/artifacts/pr_eg_r6_r5/09_GROUND_TRUTH.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/09_GROUND_TRUTH.md`.
- `support/artifacts/pr_eg_r6_r5/10_FROZEN_PARTITIONS.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/10_FROZEN_PARTITIONS.md`.
- `support/artifacts/pr_eg_r6_r5/11_PRODUCTION_BASELINE.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/11_PRODUCTION_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r5/12_GOLD_INTERVENTION_HARNESS.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/12_GOLD_INTERVENTION_HARNESS.md`.
- `support/artifacts/pr_eg_r6_r5/13_INTENT_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/13_INTENT_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/14_REFERENT_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/14_REFERENT_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/15_QUESTION_PROPOSITION_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/15_QUESTION_PROPOSITION_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/16_SOURCE_RETRIEVAL_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/16_SOURCE_RETRIEVAL_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/17_SOURCE_PROPOSITION_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/17_SOURCE_PROPOSITION_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/18_CORRESPONDENCE_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/18_CORRESPONDENCE_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/19_SUFFICIENCY_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/19_SUFFICIENCY_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/20_AUTHORIZED_PLAN_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/20_AUTHORIZED_PLAN_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/21_COMBINED_UPSTREAM_INTERVENTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/21_COMBINED_UPSTREAM_INTERVENTION.md`.
- `support/artifacts/pr_eg_r6_r5/22_EXPRESSION_CONTROL.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/22_EXPRESSION_CONTROL.md`.
- `support/artifacts/pr_eg_r6_r5/23_PAIRED_RESULTS.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/23_PAIRED_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r5/24_INTERACTION_EFFECTS.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/24_INTERACTION_EFFECTS.md`.
- `support/artifacts/pr_eg_r6_r5/25_FIRST_FAILURE_ATTRIBUTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/25_FIRST_FAILURE_ATTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r5/26_SECURITY_VERIFICATION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/26_SECURITY_VERIFICATION.md`.
- `support/artifacts/pr_eg_r6_r5/27_PLAYER_FACING_QUALITY.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/27_PLAYER_FACING_QUALITY.md`.
- `support/artifacts/pr_eg_r6_r5/28_INDEPENDENT_EVALUATION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/28_INDEPENDENT_EVALUATION.md`.
- `support/artifacts/pr_eg_r6_r5/29_HUMAN_REVIEW_PACKET.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/29_HUMAN_REVIEW_PACKET.md`.
- `support/artifacts/pr_eg_r6_r5/30_PERFORMANCE.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/30_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r5/31_BOTTLENECK_CONTRIBUTION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/31_BOTTLENECK_CONTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`.
- `support/artifacts/pr_eg_r6_r5/33_ARCHITECTURE_DECISION.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/33_ARCHITECTURE_DECISION.md`.
- `support/artifacts/pr_eg_r6_r5/34_REMAINING_UNKNOWNS.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/34_REMAINING_UNKNOWNS.md`.
- `support/artifacts/pr_eg_r6_r5/35_RECOMMENDED_NEXT_CYCLE.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/35_RECOMMENDED_NEXT_CYCLE.md`.
- `support/artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r5/37_SOURCE_AND_EVIDENCE_INVENTORY.md`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/37_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r5/freeze.json`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/freeze.json`.
- `support/artifacts/pr_eg_r6_r5/repository_baseline.json`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/repository_baseline.json`.
- `support/artifacts/pr_eg_r6_r5/summary.json`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/summary.json`.
- `support/artifacts/pr_eg_r6_r5/first_failures.json`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/first_failures.json`.
- `support/artifacts/pr_eg_r6_r5/human_review_packet.json`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/human_review_packet.json`.
- `support/artifacts/pr_eg_r6_r5/baseline.jsonl`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/baseline.jsonl`.
- `support/artifacts/pr_eg_r6_r5/interventions.jsonl`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/interventions.jsonl`.
- `support/artifacts/pr_eg_r6_r5/expression_control.jsonl`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/expression_control.jsonl`.
- `support/artifacts/pr_eg_r6_r5/baseline_ledger_collision.jsonl`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/baseline_ledger_collision.jsonl`.
- `support/artifacts/pr_eg_r6_r5/interventions_schema_rejected.jsonl`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `artifacts/pr_eg_r6_r5/interventions_schema_rejected.jsonl`.
- `support/experiments/pr_eg_r6_r5/__init__.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/__init__.py`.
- `support/experiments/pr_eg_r6_r5/gold.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/gold.py`.
- `support/experiments/pr_eg_r6_r5/score.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/score.py`.
- `support/experiments/pr_eg_r6_r5/run.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/run.py`.
- `support/experiments/pr_eg_r6_r5/analyze.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/analyze.py`.
- `support/experiments/pr_eg_r6_r5/report.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `experiments/pr_eg_r6_r5/report.py`.
- `support/tests/test_pr_eg_r6_r5_diagnostic.py`: PR-EG-R6-R5 diagnostic evidence or source. Canonical source: `tests/test_pr_eg_r6_r5_diagnostic.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r5/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r5/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
