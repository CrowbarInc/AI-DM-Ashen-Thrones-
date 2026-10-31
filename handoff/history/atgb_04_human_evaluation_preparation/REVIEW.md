# Campaign

Campaign: ATGB-04 Independent Human Evaluation Preparation
Identifier: `atgb_04_human_evaluation_preparation`
Date: 2026-10-18
Generated: 2026-10-18T22:46:21.588367+00:00
Purpose: Prepare the preserved conversational baseline for independent human judgment without gameplay changes or provider requests.

# Executive Summary

37 unique turns indexed exactly once: original S01–S03, S04 full trial 2, S05–S10 trial 1. Original partial S04 trial 1 remains separate. Extract the ZIP and open support/artifacts/atgb/atgb_04/README.md, then review.html or conversational_review.md. All human judgments are blank. S07/S09 opening delivery limits require special review. No gameplay-performance baseline is claimed. Existing packet empty outcome categories mean unmeasured, never zero failures.

Objective status: `REVIEW PACKAGE PREPARED; HUMAN EVALUATION PENDING`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No scenario, expectation, rubric, partition or benchmark version changes. Ten offline integrity/aggregation tests added.

## Tooling changes

- Two offline review preparation/aggregation tools; no gameplay imports or provider calls.

## Documentation changes

- ATGB-04 preparation report and current session orientation.

## Generated artifacts

- 37-turn index; complete HTML/Markdown conversations; blank forms; pending report; scenario qualifications; source hashes and standard ZIP.

# What Was Tested

- **Focused tests:** 10 tests passed. Offline JavaScript form collect/export/import and wrong-trial rejection passed. Exact source text, prior context, blank fields and null rates verified.
- **Broader relevant tests:** Not run; no gameplay code changed.
- **Full suite:** Not run.
- **Runtime validation:** No new gameplay execution or provider requests. Reuses preserved 37-turn evidence. HTML browser preview blocked by file: URL policy; rendered layout unverified.
- **Model/runtime boundary:** Original live-enabled production API evidence, gpt-4.1-mini, sampling uncontrolled; host-owned responses possible. ATGB-04 runs offline only.
- **New regressions:** No gameplay regression claim. Protected sources are byte-identical.
- **Pre-existing failures:** Original infrastructure stop, missing telemetry, S07/S09 opening delivery limits and extensive dirty worktree retained.
- **Self-contained bundle review:** verify_package.py checks ZIP CRC, required standard sections, source hashes, exact 37-turn/trial selection, prior context, blank form structure and null rates, and executes reporting from an isolated extraction. Existing outcome categories remain unmeasured.

# Behavioral Evidence

## Evidence Packet: atgb_03c_live_baseline_continuation

Runs / turns: `7` / `24`
Runtime/model boundary: Live-enabled OpenAI gpt-4.1-mini with existing host-owned replies and model roles; no browser UI validation

### Representative success

No example observed in this campaign.

### Representative failure

No example observed in this campaign.

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Independently enter interpretation, response, authority, severity, clarification, continuity and reviewer explanations. Retain separate reviewer exports and disagreements.
- Assess criterion support under S07/S09 opening limitations; never score missing setup automatically as gameplay failure.

# Known Problems / Unresolved Findings

## Campaign-specific

- All human judgments pending; no evaluated performance rates.
- Rendered HTML layout unverified; full Markdown review available.

## Pre-existing baseline

- S07/S09 opening not delivered before first turn; unsupported criteria require uncertain/not_evaluated.
- Held-out previously exposed; single environment and selected trials; bounded state evidence.

# Missing Concepts / Future Capabilities

- No opening injection, automated eligibility decision, LLM judge, new universal score or gameplay repair is implemented.

# What This Campaign Does NOT Prove

- Completed gameplay-performance baseline, gameplay improvement, independent unseen generalization, stable multi-trial performance, browser rendering, broad regression or SDK request bounds.

# Recommended Next Step

Stop and await independent human evaluation. Open support/artifacts/atgb/atgb_04/review.html or conversational_review.md, save the human export, then use the packaged reporting tool per README.md. No provider requests, reruns or new Product Realization campaign.

# Review Bundle Contents

Bundle file count: `105`
Bundle ZIP size: `000000632630` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_04_human_evaluation_preparation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_04_human_evaluation_preparation.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`.
- `support/artifacts/atgb/atgb_03/S01/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S01/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S01/result.json`.
- `support/artifacts/atgb/atgb_03/S01/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S01/transcript.md`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S02/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S02/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S02/result.json`.
- `support/artifacts/atgb/atgb_03/S02/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S02/transcript.md`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S03/result.json`.
- `support/artifacts/atgb/atgb_03/S03/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S03/transcript.md`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S04/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S04/result.json`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03/configuration_and_provenance.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/configuration_and_provenance.json`.
- `support/artifacts/atgb/atgb_03/scenario_status.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03/scenario_status.json`.
- `support/artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S04/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S04/result.json`.
- `support/artifacts/atgb/atgb_03c/S04/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S04/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S05/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S05/result.json`.
- `support/artifacts/atgb/atgb_03c/S05/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S05/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S05/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S05/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S06/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S06/result.json`.
- `support/artifacts/atgb/atgb_03c/S06/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S06/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S06/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S06/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S07/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S07/result.json`.
- `support/artifacts/atgb/atgb_03c/S07/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S07/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S07/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S07/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S08/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S08/result.json`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S08/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S08/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S09/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S09/result.json`.
- `support/artifacts/atgb/atgb_03c/S09/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S09/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S09/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S09/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S10/result.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S10/result.json`.
- `support/artifacts/atgb/atgb_03c/S10/transcript.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S10/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S10/worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/S10/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/baseline_coverage.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/baseline_coverage.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_review_source.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_review_source.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`.
- `support/artifacts/atgb/atgb_03c/opening_context.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/opening_context.json`.
- `support/artifacts/atgb/atgb_03c/provenance_before.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/provenance_before.json`.
- `support/artifacts/atgb/atgb_03c/provider_accounting.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/provider_accounting.json`.
- `support/artifacts/atgb/atgb_03c/scenario_readiness.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_03c/scenario_readiness.json`.
- `support/artifacts/atgb/atgb_04/README.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/README.md`.
- `support/artifacts/atgb/atgb_04/approved_rubric_excerpt.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/approved_rubric_excerpt.md`.
- `support/artifacts/atgb/atgb_04/blank_judgments.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/blank_judgments.json`.
- `support/artifacts/atgb/atgb_04/blank_scoring_forms.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/blank_scoring_forms.md`.
- `support/artifacts/atgb/atgb_04/check_form.cjs`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/check_form.cjs`.
- `support/artifacts/atgb/atgb_04/conversational_review.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/conversational_review.md`.
- `support/artifacts/atgb/atgb_04/evidence_provenance.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/evidence_provenance.md`.
- `support/artifacts/atgb/atgb_04/evidence_sources.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/evidence_sources.json`.
- `support/artifacts/atgb/atgb_04/focused_tests.txt`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/focused_tests.txt`.
- `support/artifacts/atgb/atgb_04/historical_S04_trial_1.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/historical_S04_trial_1.md`.
- `support/artifacts/atgb/atgb_04/package_review.py`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/package_review.py`.
- `support/artifacts/atgb/atgb_04/pending_report.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/pending_report.json`.
- `support/artifacts/atgb/atgb_04/preservation_before.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/preservation_before.json`.
- `support/artifacts/atgb/atgb_04/preservation_checks.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/preservation_checks.json`.
- `support/artifacts/atgb/atgb_04/review.html`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/review.html`.
- `support/artifacts/atgb/atgb_04/review_index.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/review_index.json`.
- `support/artifacts/atgb/atgb_04/review_index.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/review_index.md`.
- `support/artifacts/atgb/atgb_04/scenario_qualifications.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/scenario_qualifications.md`.
- `support/artifacts/atgb/atgb_04/validation_results.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/validation_results.json`.
- `support/artifacts/atgb/atgb_04/verify_package.py`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `artifacts/atgb/atgb_04/verify_package.py`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/corpus.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/visible/S01.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02a_readiness.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_02a_readiness.md`.
- `support/development/reports/atgb_03_initial_live_baseline.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_03_initial_live_baseline.md`.
- `support/development/reports/atgb_03c_live_baseline_continuation.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `development/reports/atgb_03c_live_baseline_continuation.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/product_realization_validation.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `docs/product_realization_validation.md`.
- `support/docs/review_handoff_standard.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `docs/review_handoff_standard.md`.
- `support/docs/validation_evidence_standard.md`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `docs/validation_evidence_standard.md`.
- `support/tests/test_atgb_human_review.py`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `tests/test_atgb_human_review.py`.
- `support/tools/atgb/prepare_human_review.py`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `tools/atgb/prepare_human_review.py`.
- `support/tools/atgb/report_human_review.py`: Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending. Canonical source: `tools/atgb/report_human_review.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
