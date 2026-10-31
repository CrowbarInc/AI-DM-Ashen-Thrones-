# Campaign

Campaign: PR-EG-R6-R4 — Authorized Evidence Correspondence Reassessment
Identifier: `pr_eg_r6_r4_correspondence_20261018`
Date: 2026-10-18
Generated: 2026-10-18T15:46:13.985280+00:00
Purpose: Architectural discovery and controlled experiment; no production migration.

# Executive Summary

No production migration is justified. The primary comparison isolates correspondence using gold question meanings and identical eligible prose. B requires authored facts, while C must validate AI proposals against those facts. B recovers structured answers cheaply but loses prose-only cases; C mostly fails its proposal contract. Actual production interpretations reduce B substantially.

| Architecture | Supported answer success | Relevance | Sufficiency | Acceptance errors | Rejections of answerable cases |
|---|---:|---:|---:|---:|---:|
| A | 158/168 (94.0%) | 165/168 (98.2%) | 160/168 (95.2%) | 0 | 3 |
| B | 160/168 (95.2%) | 160/168 (95.2%) | 160/168 (95.2%) | 0 | 8 |
| C | 53/168 (31.5%) | 53/168 (31.5%) | 85/168 (50.6%) | 0 | 83 |


This table covers 168 nonambiguous cases. All 176 cases and the excluded ambiguity diagnostics are preserved. B/C consumed a gold ambiguity bit that the A kernel did not: that defect prevents using the eight ambiguity cases as evidence of superiority. A is the unchanged production correspondence kernel/prompt inside a shared aggregator, not a full production rewrite or /api/chat qualification.

Verdict: **C — INCONCLUSIVE / FURTHER DISCOVERY REQUIRED**. There were zero tested source-access violations; semantic correctness and low manual authoring burden remain unresolved. Do not begin PR-EH.

Objective status: `C — INCONCLUSIVE / FURTHER DISCOVERY REQUIRED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Isolated correspondence tests

## Tooling changes

- Experiment, audit and reporting scripts

## Documentation changes

- 35 numbered review artifacts

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** 197 local experiment tests passed before live calls.
- **Broader relevant tests:** 317 passed, 2 failed (Windows temp-file atomic-replace permissions), 4 deselected. Interrupted retries recorded in verification_status.json.
- **Full suite:** Not run.
- **Runtime validation:** 466 official logical provider calls; 176 core cases, 22 secondary interpretations, 35 supplemental probes.
- **Model/runtime boundary:** gpt-4.1-mini, temperature 0, max output 1800
- **New regressions:** No production changes; regression qualification incomplete.
- **Pre-existing failures:** Not reassessed globally.
- **Self-contained bundle review:** ZIP readability, all non-null manifest SHA-256 values, frozen input hashes, numbered artifact count and source-inventory hashes verified. The manifest intentionally has no self-hash.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Whether to authorize a new discovery cycle using repaired development contracts and independently reviewed fresh holdouts.

# Known Problems / Unresolved Findings

## Campaign-specific

- Post hoc ambiguity exclusion and scorer clarification limit comparability.
- Supplemental paraphrases broaden coverage after primary exposure; no replacement holdout claim.
- C proposal contract mostly failed; B depends on manual source facts.

## Pre-existing baseline

- Production conversational qualification remains below target.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Production readiness, affordable annotation, universal semantic security or broad open-world generalization.

# Recommended Next Step

Stop after PR-EG-R6-R4; await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `84`
Bundle ZIP size: `000000572724` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r4/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r4/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r4/02_REPOSITORY_BASELINE.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/02_REPOSITORY_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r4/03_CURRENT_SOURCE-RESOLUTION_AUDIT.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/03_CURRENT_SOURCE-RESOLUTION_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r4/04_HISTORICAL_FAILURE_INVENTORY.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/04_HISTORICAL_FAILURE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r4/05_FAILURE_TAXONOMY.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/05_FAILURE_TAXONOMY.md`.
- `support/artifacts/pr_eg_r6_r4/06_EVALUATION_CONTRACT.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/06_EVALUATION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r4/07_ANSWER-CLASS_DEFINITIONS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/07_ANSWER-CLASS_DEFINITIONS.md`.
- `support/artifacts/pr_eg_r6_r4/08_ARCHITECTURE_A_SPECIFICATION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/08_ARCHITECTURE_A_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r4/09_ARCHITECTURE_B_SPECIFICATION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/09_ARCHITECTURE_B_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r4/10_ARCHITECTURE_C_SPECIFICATION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/10_ARCHITECTURE_C_SPECIFICATION.md`.
- `support/artifacts/pr_eg_r6_r4/11_EXPERIMENTAL_CONDITIONS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/11_EXPERIMENTAL_CONDITIONS.md`.
- `support/artifacts/pr_eg_r6_r4/12_QUESTION_INTERPRETATION_CONTROL.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/12_QUESTION_INTERPRETATION_CONTROL.md`.
- `support/artifacts/pr_eg_r6_r4/13_SOURCE_RETRIEVAL_CONTROL.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/13_SOURCE_RETRIEVAL_CONTROL.md`.
- `support/artifacts/pr_eg_r6_r4/14_CORPUS_AND_GROUND_TRUTH.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/14_CORPUS_AND_GROUND_TRUTH.md`.
- `support/artifacts/pr_eg_r6_r4/15_FROZEN_HOLDOUTS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/15_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6_r4/16_OPEN-WORLD_GENERALIZATION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/16_OPEN-WORLD_GENERALIZATION.md`.
- `support/artifacts/pr_eg_r6_r4/17_ROLE_PRESERVATION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/17_ROLE_PRESERVATION.md`.
- `support/artifacts/pr_eg_r6_r4/18_PARAPHRASE_AND_ENTAILMENT.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/18_PARAPHRASE_AND_ENTAILMENT.md`.
- `support/artifacts/pr_eg_r6_r4/19_PARTIAL_ANSWERS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/19_PARTIAL_ANSWERS.md`.
- `support/artifacts/pr_eg_r6_r4/20_RELATED_NONANSWERS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/20_RELATED_NONANSWERS.md`.
- `support/artifacts/pr_eg_r6_r4/21_NEGATION_AND_QUALIFIERS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/21_NEGATION_AND_QUALIFIERS.md`.
- `support/artifacts/pr_eg_r6_r4/22_CONFLICTING_EVIDENCE.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/22_CONFLICTING_EVIDENCE.md`.
- `support/artifacts/pr_eg_r6_r4/23_SECURITY_EXPERIMENTS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/23_SECURITY_EXPERIMENTS.md`.
- `support/artifacts/pr_eg_r6_r4/24_PROVIDER_EVIDENCE.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/24_PROVIDER_EVIDENCE.md`.
- `support/artifacts/pr_eg_r6_r4/25_COST_AND_LATENCY.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/25_COST_AND_LATENCY.md`.
- `support/artifacts/pr_eg_r6_r4/26_PER-CASE_RESULTS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/26_PER-CASE_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r4/27_FAILURE_ATTRIBUTION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/27_FAILURE_ATTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r4/28_COMPARISON_MATRIX.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/28_COMPARISON_MATRIX.md`.
- `support/artifacts/pr_eg_r6_r4/29_STATISTICAL_LIMITATIONS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/29_STATISTICAL_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r4/30_ARCHITECTURE_DECISION.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/30_ARCHITECTURE_DECISION.md`.
- `support/artifacts/pr_eg_r6_r4/31_INTEGRATION_READINESS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/31_INTEGRATION_READINESS.md`.
- `support/artifacts/pr_eg_r6_r4/32_REMAINING_UNKNOWNS.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/32_REMAINING_UNKNOWNS.md`.
- `support/artifacts/pr_eg_r6_r4/33_RECOMMENDED_NEXT_CYCLE.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/33_RECOMMENDED_NEXT_CYCLE.md`.
- `support/artifacts/pr_eg_r6_r4/34_FINAL_VERDICT.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/34_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r4/35_SOURCE_AND_EVIDENCE_INVENTORY.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/35_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r4/adapter_correction.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/adapter_correction.json`.
- `support/artifacts/pr_eg_r6_r4/baseline.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/baseline.json`.
- `support/artifacts/pr_eg_r6_r4/baseline_status.txt`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/baseline_status.txt`.
- `support/artifacts/pr_eg_r6_r4/bundle_verification.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/bundle_verification.json`.
- `support/artifacts/pr_eg_r6_r4/development.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/development.json`.
- `support/artifacts/pr_eg_r6_r4/freeze.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/freeze.json`.
- `support/artifacts/pr_eg_r6_r4/historical_inventory.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/historical_inventory.json`.
- `support/artifacts/pr_eg_r6_r4/historical_raw_examples.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/historical_raw_examples.jsonl`.
- `support/artifacts/pr_eg_r6_r4/holdout.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/holdout.json`.
- `support/artifacts/pr_eg_r6_r4/interrupted_verification_tests.txt`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/interrupted_verification_tests.txt`.
- `support/artifacts/pr_eg_r6_r4/invalid_initial_attempts.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/invalid_initial_attempts.jsonl`.
- `support/artifacts/pr_eg_r6_r4/paraphrases.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/paraphrases.json`.
- `support/artifacts/pr_eg_r6_r4/paraphrase_freeze.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/paraphrase_freeze.json`.
- `support/artifacts/pr_eg_r6_r4/paraphrase_results.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/paraphrase_results.jsonl`.
- `support/artifacts/pr_eg_r6_r4/per_case_results.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/per_case_results.jsonl`.
- `support/artifacts/pr_eg_r6_r4/primary.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/primary.jsonl`.
- `support/artifacts/pr_eg_r6_r4/production_integrity.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/production_integrity.json`.
- `support/artifacts/pr_eg_r6_r4/secondary.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/secondary.jsonl`.
- `support/artifacts/pr_eg_r6_r4/source_inventory.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/source_inventory.json`.
- `support/artifacts/pr_eg_r6_r4/summary.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/summary.json`.
- `support/artifacts/pr_eg_r6_r4/supplemental.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/supplemental.json`.
- `support/artifacts/pr_eg_r6_r4/supplemental_freeze.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/supplemental_freeze.json`.
- `support/artifacts/pr_eg_r6_r4/supplemental_results.jsonl`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/supplemental_results.jsonl`.
- `support/artifacts/pr_eg_r6_r4/validation.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/validation.json`.
- `support/artifacts/pr_eg_r6_r4/verification_status.json`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/verification_status.json`.
- `support/artifacts/pr_eg_r6_r4/verification_tests.txt`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `artifacts/pr_eg_r6_r4/verification_tests.txt`.
- `support/experiments/pr_eg_r6_r4/challenges.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/challenges.py`.
- `support/experiments/pr_eg_r6_r4/corpus.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/corpus.py`.
- `support/experiments/pr_eg_r6_r4/engine.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/engine.py`.
- `support/experiments/pr_eg_r6_r4/run.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/run.py`.
- `support/experiments/pr_eg_r6_r4/__init__.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/__init__.py`.
- `support/experiments/pr_eg_r6_r4/CONTRACT.md`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r4/CONTRACT.md`.
- `support/tests/test_pr_eg_r6_r4_correspondence.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tests/test_pr_eg_r6_r4_correspondence.py`.
- `support/tools/audit_pr_eg_r6_r4.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/audit_pr_eg_r6_r4.py`.
- `support/tools/report_pr_eg_r6_r4.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/report_pr_eg_r6_r4.py`.
- `support/tools/supplement_pr_eg_r6_r4.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/supplement_pr_eg_r6_r4.py`.
- `support/game/semantic_correspondence.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/semantic_correspondence.py`.
- `support/game/semantic_operations.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/semantic_operations.py`.
- `support/game/unified_semantic_planning.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/game/dialogue_authority.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/dialogue_authority.py`.
- `support/game/social.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/social.py`.
- `support/game/immutable_valid_response.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/immutable_valid_response.py`.
- `support/game/config.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `game/config.py`.
- `support/experiments/pr_eg_r6_r3/common.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `experiments/pr_eg_r6_r3/common.py`.
- `support/tools/qualify_pr_eg_r6_r2_r1.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/qualify_pr_eg_r6_r2_r1.py`.
- `support/tools/qualify_pr_eg_r6_r3_r1.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/qualify_pr_eg_r6_r3_r1.py`.
- `support/tools/qualify_pr_eg_r6.py`: Reproducible PR-EG-R6-R4 discovery and raw evidence. Canonical source: `tools/qualify_pr_eg_r6.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r4/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r4/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
