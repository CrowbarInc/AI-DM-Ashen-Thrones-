# Campaign

Campaign: PR-EG-R6-R4-R1 — Source-Grounded Semantic Alignment
Identifier: `pr_eg_r6_r4_r1_source_alignment_20261018`
Date: 2026-10-18
Generated: 2026-10-18T19:01:59.907709+00:00
Purpose: Focused architectural discovery and isolated prototype; no migration.

# Executive Summary

**C — INCONCLUSIVE / BELOW ACCEPTANCE. Do not integrate.** Reuse works as caching, but source anchoring does not establish semantic support. Human adjudication and defensible semantic extraction precision/recall are missing. No production migration or PR-EH work was performed.

| Arm | Strict case agreement | Class agreement | Exact content agreement | Rubric acceptance flags | Off-rubric positive predictions |
|---|---:|---:|---:|---:|---:|
| A | 48/170 (28.2%) | 58/170 (34.1%) | 75/170 (44.1%) | 18/30 (60.0%) | 4/30 (13.3%) |
| B | 58/170 (34.1%) | 128/170 (75.3%) | 83/170 (48.8%) | 96/134 (71.6%) | 85/134 (63.4%) |
| C | 64/170 (37.6%) | 123/170 (72.4%) | 87/170 (51.2%) | 76/120 (63.3%) | 71/120 (59.2%) |

Strict agreement requires frozen class, exact normalized answer values and required literal qualifiers. These are offline candidate predictions, never delivered facts. The frozen scorer flags full-sentence answers as extra values even when their source supports them: its false_acceptance/unsupported_inference fields are rubric flags, NOT measured semantic falsehood rates. No corrected scores replace frozen results. Zero canonical promotion and zero gameplay disclosures occur by construction, not evidence that predictions are safe to deploy. See 31 for metric limitations and 33 for dependence/label uncertainty.

Objective status: `C — INCONCLUSIVE / BELOW ACCEPTANCE`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Adversarial boundary tests

## Tooling changes

- Isolated frozen experiment and audit/report tools

## Documentation changes

- 39 numbered artifacts and independent human review packet

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** 20 boundary tests passed before freeze; 228 focused/current-correspondence/handoff tests passed at closeout.
- **Broader relevant tests:** Broader run including unified-planner and expression tests stalled after 77% progress and was interrupted; no complete verdict. Raw log preserved in verification_tests.txt.
- **Full suite:** Not run.
- **Runtime validation:** 570/570 parsed real provider calls, 510 paired arm-cases.
- **Model/runtime boundary:** gpt-4.1-mini; temperature 0; output cap 1800; no SDK retries.
- **New regressions:** Production code/state hashes unchanged.
- **Pre-existing failures:** Not globally reassessed.
- **Self-contained bundle review:** 39 numbered artifacts, frozen inputs, raw provider evidence and manifest hashes verified.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Adjudicate the stratified packet and judge whether further discovery is justified.

# Known Problems / Unresolved Findings

## Campaign-specific

- Human adjudication pending.
- Sparse source claim labels prevent semantic extraction precision/recall.
- Exact-match rubric and different A answer capacity limit interpretation.
- Network gold diagnostic rejected; local control only.
- Do not use frozen runner diagnostic network mode; use the offline diagnostic tool.

## Pre-existing baseline

- Prior working tree contains extensive unrelated changes.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Production readiness, semantic entailment verification, affordable authoring, universal security, or broad generalization.

# Recommended Next Step

Stop after PR-EG-R6-R4-R1 and await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `83`
Bundle ZIP size: `000001111363` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r4_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r4_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r4_r1/02_REPOSITORY_BASELINE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/02_REPOSITORY_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/03_HISTORICAL_FAILURE_REVIEW.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/03_HISTORICAL_FAILURE_REVIEW.md`.
- `support/artifacts/pr_eg_r6_r4_r1/04_CURRENT_SEMANTIC_PIPELINE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/04_CURRENT_SEMANTIC_PIPELINE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/05_EXPERIMENTAL_HYPOTHESIS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/05_EXPERIMENTAL_HYPOTHESIS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/06_ARCHITECTURE_SPECIFICATIONS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/06_ARCHITECTURE_SPECIFICATIONS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/07_SOURCE_EXTRACTION_CONTRACT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/07_SOURCE_EXTRACTION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/08_MULTI-FACT_SOURCES.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/08_MULTI-FACT_SOURCES.md`.
- `support/artifacts/pr_eg_r6_r4_r1/09_QUALIFIER_PRESERVATION.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/09_QUALIFIER_PRESERVATION.md`.
- `support/artifacts/pr_eg_r6_r4_r1/10_PROVENANCE_AND_AUTHORITY.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/10_PROVENANCE_AND_AUTHORITY.md`.
- `support/artifacts/pr_eg_r6_r4_r1/11_HOST_VALIDATION.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/11_HOST_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r4_r1/12_VALIDATION_TRUST_LEVELS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/12_VALIDATION_TRUST_LEVELS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/13_QUESTION_ALIGNMENT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/13_QUESTION_ALIGNMENT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/14_MULTI-ROLE_ALIGNMENT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/14_MULTI-ROLE_ALIGNMENT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/15_PARTIAL_ANSWERS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/15_PARTIAL_ANSWERS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/16_RELATED_NONANSWERS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/16_RELATED_NONANSWERS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/17_CONFLICTING_EVIDENCE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/17_CONFLICTING_EVIDENCE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/18_OPEN-WORLD_GENERALIZATION.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/18_OPEN-WORLD_GENERALIZATION.md`.
- `support/artifacts/pr_eg_r6_r4_r1/19_CORPUS_DESIGN.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/19_CORPUS_DESIGN.md`.
- `support/artifacts/pr_eg_r6_r4_r1/20_REUSE_EXPERIMENT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/20_REUSE_EXPERIMENT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/21_FROZEN_PARTITIONS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/21_FROZEN_PARTITIONS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/22_GROUND_TRUTH.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/22_GROUND_TRUTH.md`.
- `support/artifacts/pr_eg_r6_r4_r1/23_HUMAN_ADJUDICATION_PACKET.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/23_HUMAN_ADJUDICATION_PACKET.md`.
- `support/artifacts/pr_eg_r6_r4_r1/24_EXPERIMENTAL_FAIRNESS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/24_EXPERIMENTAL_FAIRNESS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/25_PROVIDER_EVIDENCE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/25_PROVIDER_EVIDENCE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/26_FAILURE_TAXONOMY.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/26_FAILURE_TAXONOMY.md`.
- `support/artifacts/pr_eg_r6_r4_r1/27_SECURITY_EXPERIMENTS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/27_SECURITY_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/28_HOST_VALIDATION_RESULTS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/28_HOST_VALIDATION_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/29_ANNOTATION_COST.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/29_ANNOTATION_COST.md`.
- `support/artifacts/pr_eg_r6_r4_r1/30_PERFORMANCE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/30_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/31_QUALITY_METRICS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/31_QUALITY_METRICS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/32_COMPARATIVE_RESULTS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/32_COMPARATIVE_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/33_STATISTICAL_LIMITATIONS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/33_STATISTICAL_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/34_ARCHITECTURE_DECISION.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/34_ARCHITECTURE_DECISION.md`.
- `support/artifacts/pr_eg_r6_r4_r1/35_PRODUCTION_INTEGRATION_READINESS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/35_PRODUCTION_INTEGRATION_READINESS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/36_REMAINING_UNKNOWNS.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/36_REMAINING_UNKNOWNS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/37_RECOMMENDED_NEXT_CYCLE.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/37_RECOMMENDED_NEXT_CYCLE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/39_SOURCE_AND_EVIDENCE_INVENTORY.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/39_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r4_r1/adjudication_packet.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/adjudication_packet.json`.
- `support/artifacts/pr_eg_r6_r4_r1/authorization_record.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/authorization_record.json`.
- `support/artifacts/pr_eg_r6_r4_r1/baseline.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/baseline.json`.
- `support/artifacts/pr_eg_r6_r4_r1/baseline_status.txt`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/baseline_status.txt`.
- `support/artifacts/pr_eg_r6_r4_r1/blocked_attempt_inventory.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/blocked_attempt_inventory.json`.
- `support/artifacts/pr_eg_r6_r4_r1/development.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/development.json`.
- `support/artifacts/pr_eg_r6_r4_r1/development_console.txt`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/development_console.txt`.
- `support/artifacts/pr_eg_r6_r4_r1/extraction_records.jsonl`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/extraction_records.jsonl`.
- `support/artifacts/pr_eg_r6_r4_r1/focused_tests.txt`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/focused_tests.txt`.
- `support/artifacts/pr_eg_r6_r4_r1/freeze.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/freeze.json`.
- `support/artifacts/pr_eg_r6_r4_r1/gold_diagnostic.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/gold_diagnostic.json`.
- `support/artifacts/pr_eg_r6_r4_r1/grading_audit.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/grading_audit.json`.
- `support/artifacts/pr_eg_r6_r4_r1/historical_examples.jsonl`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/historical_examples.jsonl`.
- `support/artifacts/pr_eg_r6_r4_r1/historical_inventory.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/historical_inventory.json`.
- `support/artifacts/pr_eg_r6_r4_r1/holdout.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/holdout.json`.
- `support/artifacts/pr_eg_r6_r4_r1/human_review_packet.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/human_review_packet.json`.
- `support/artifacts/pr_eg_r6_r4_r1/payload_audit.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/payload_audit.json`.
- `support/artifacts/pr_eg_r6_r4_r1/per_case_results.jsonl`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/per_case_results.jsonl`.
- `support/artifacts/pr_eg_r6_r4_r1/primary_console.txt`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/primary_console.txt`.
- `support/artifacts/pr_eg_r6_r4_r1/production_integrity.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/production_integrity.json`.
- `support/artifacts/pr_eg_r6_r4_r1/provider_calls.jsonl`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/provider_calls.jsonl`.
- `support/artifacts/pr_eg_r6_r4_r1/reuse_results.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/reuse_results.json`.
- `support/artifacts/pr_eg_r6_r4_r1/security_results.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/security_results.json`.
- `support/artifacts/pr_eg_r6_r4_r1/source_inventory.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/source_inventory.json`.
- `support/artifacts/pr_eg_r6_r4_r1/summary.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/summary.json`.
- `support/artifacts/pr_eg_r6_r4_r1/validation.json`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/validation.json`.
- `support/artifacts/pr_eg_r6_r4_r1/verification_tests.txt`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `artifacts/pr_eg_r6_r4_r1/verification_tests.txt`.
- `support/experiments/pr_eg_r6_r4_r1/__init__.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `experiments/pr_eg_r6_r4_r1/__init__.py`.
- `support/experiments/pr_eg_r6_r4_r1/CONTRACT.md`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `experiments/pr_eg_r6_r4_r1/CONTRACT.md`.
- `support/experiments/pr_eg_r6_r4_r1/corpus.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `experiments/pr_eg_r6_r4_r1/corpus.py`.
- `support/experiments/pr_eg_r6_r4_r1/engine.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `experiments/pr_eg_r6_r4_r1/engine.py`.
- `support/experiments/pr_eg_r6_r4_r1/run.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `experiments/pr_eg_r6_r4_r1/run.py`.
- `support/game/dialogue_authority.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `game/dialogue_authority.py`.
- `support/game/immutable_valid_response.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `game/immutable_valid_response.py`.
- `support/game/semantic_correspondence.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `game/semantic_correspondence.py`.
- `support/game/semantic_operations.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `game/semantic_operations.py`.
- `support/game/unified_semantic_planning.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `game/unified_semantic_planning.py`.
- `support/tests/test_pr_eg_r6_r4_r1_alignment.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `tests/test_pr_eg_r6_r4_r1_alignment.py`.
- `support/tools/audit_pr_eg_r6_r4_r1.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `tools/audit_pr_eg_r6_r4_r1.py`.
- `support/tools/diagnostic_pr_eg_r6_r4_r1.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `tools/diagnostic_pr_eg_r6_r4_r1.py`.
- `support/tools/report_pr_eg_r6_r4_r1.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `tools/report_pr_eg_r6_r4_r1.py`.
- `support/tools/verify_pr_eg_r6_r4_r1.py`: Reviewable frozen experiment, raw evidence or focused source. Canonical source: `tools/verify_pr_eg_r6_r4_r1.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r4_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r4_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
