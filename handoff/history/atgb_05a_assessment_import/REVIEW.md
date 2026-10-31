# Campaign

Campaign: ATGB-05A Assessment Import and Initial Setup Closure
Identifier: `atgb_05a_assessment_import`
Date: 2026-10-18
Generated: 2026-10-18T23:12:00.570302+00:00
Purpose: Complete the blocked ATGB-05 provisional assessment import and verify initial ATGB v1 setup closure.

# Executive Summary

Original assessment files found at workspace root and preserved byte-identically. All 37 selected review IDs/trials match; rubric consistency and all summary aggregates agree without identified discrepancies. Provisional counts: interpretation 18/16/3, response 10/25/2, authority 35/0/2 (pass/fail/uncertain). S03.4/S05.4 authority uncertainty and six S07/S09 setup qualifications remain intact. ChatGPT (GPT-6) AI-assisted provenance and false human attestation are preserved; existing human-reporting rejection is verified. Initial ATGB v1 operational setup is complete, authenticated human scoring pending, conversational competence not established. Historical evidence-packet empty outcome categories mean unmeasured human findings, never zero failures. No gameplay or live-provider execution.

Objective status: `COMPLETE: PROVISIONAL IMPORT VERIFIED; INITIAL OPERATIONAL SETUP CLOSED; AUTHENTICATED HUMAN SCORING PENDING`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No rubric, corpus, expectations, human-review semantics or benchmark framework changed. Offline import-integrity checks added as campaign evidence only.

## Tooling changes

- No reusable reporting implementation modified; campaign-local verification scripts only.

## Documentation changes

- ATGB-05 report and NEXT_SESSION now record verified provisional import and operational setup closure. Earlier blocked pass retained as history.

## Generated artifacts

- Byte-identical original evaluation copies, source hashes, import verification, entry preservation snapshot, test results and standard handoff ZIP.

# What Was Tested

- **Focused tests:** 21 existing offline human-review/handoff tests passed. Import checks found no discrepancies; all summary counts and determinate denominators agree. All 1,620 entry-protected and 609 original ATGB-05 protected files unchanged.
- **Broader relevant tests:** Not run; no gameplay changes.
- **Full suite:** Not run.
- **Runtime validation:** No new gameplay or provider execution. Existing human-report tool rejects the exact original false-attestation assessment. Extracted ZIP review checked separately.
- **Model/runtime boundary:** Reuses ATGB-03/03C captured live-enabled API baseline and supplied ChatGPT (GPT-6) provisional transcript assessment. No new model requests.
- **New regressions:** No gameplay change or broad regression claim. Protected production and baseline hashes unchanged.
- **Pre-existing failures:** ATGB-03B routing-metadata expectation and missing answer_sufficiency failures remain documented; reset-write failures are separate environment history.
- **Self-contained bundle review:** Extracted ZIP: check CRC, canonical SHA-256 hashes, required sections, 37 selected trial IDs, exact preserved assessment bytes and verified summary counts; execute existing human reporter with original false-attestation input and require rejection with no report output.

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

- Review provisional judgments and remaining authority/setup uncertainties. A human must independently review before explicit attestation in a separate review file.
- Review proposed conversational investigation priorities before beginning the next Product Realization investigation.

# Known Problems / Unresolved Findings

## Campaign-specific

- No import discrepancies identified; consistency verification is not human adjudication.
- Authenticated human scoring remains pending; provisional assessment must not be imported as human-approved results.

## Pre-existing baseline

- S03.4/S05.4 faction-state changes unresolved; authority uncertain, not confirmed violations.
- S07/S09 opening delivery limited; unsupported criteria not scored as failures merely for missing setup.
- SDK transport retries not independently counted; historical accounting scopes differ.
- Single environment/trials, bounded state and exposed held-out content limit claims.
- Extensive pre-existing dirty worktree retained.

# Missing Concepts / Future Capabilities

- No new scoring authority, framework, production repair, architectural migration or ATGB development campaign.

# What This Campaign Does NOT Prove

- Authenticated human scoring, evaluator infallibility, conversational competence/playability, improvement from repairs, unseen generalization, full-suite regression success or SDK transport bounds.

# Recommended Next Step

Await review before the next Product Realization investigation. Recommended priority is corrections treated as mechanical revisions, then related nonanswers/reference loss and social remarks/clarification. Establish the earliest incorrect pipeline stage before selecting repairs. No new ATGB campaign or gameplay work starts here.

# Review Bundle Contents

Bundle file count: `125`
Bundle ZIP size: `000000753338` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_05_baseline_preservation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_05_baseline_preservation.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`.
- `support/artifacts/atgb/atgb_03/S01/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S01/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S01/result.json`.
- `support/artifacts/atgb/atgb_03/S01/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S01/transcript.md`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S02/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S02/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S02/result.json`.
- `support/artifacts/atgb/atgb_03/S02/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S02/transcript.md`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S03/result.json`.
- `support/artifacts/atgb/atgb_03/S03/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S03/transcript.md`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S04/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S04/result.json`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03/configuration_and_provenance.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/configuration_and_provenance.json`.
- `support/artifacts/atgb/atgb_03/scenario_status.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03/scenario_status.json`.
- `support/artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S04/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S04/result.json`.
- `support/artifacts/atgb/atgb_03c/S04/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S04/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S05/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S05/result.json`.
- `support/artifacts/atgb/atgb_03c/S05/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S05/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S05/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S05/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S06/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S06/result.json`.
- `support/artifacts/atgb/atgb_03c/S06/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S06/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S06/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S06/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S07/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S07/result.json`.
- `support/artifacts/atgb/atgb_03c/S07/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S07/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S07/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S07/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S08/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S08/result.json`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S08/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S08/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S09/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S09/result.json`.
- `support/artifacts/atgb/atgb_03c/S09/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S09/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S09/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S09/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S10/result.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S10/result.json`.
- `support/artifacts/atgb/atgb_03c/S10/transcript.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S10/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S10/worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/S10/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/baseline_coverage.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/baseline_coverage.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_review_source.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_review_source.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`.
- `support/artifacts/atgb/atgb_03c/opening_context.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/opening_context.json`.
- `support/artifacts/atgb/atgb_03c/provenance_before.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/provenance_before.json`.
- `support/artifacts/atgb/atgb_03c/provider_accounting.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/provider_accounting.json`.
- `support/artifacts/atgb/atgb_03c/scenario_readiness.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_03c/scenario_readiness.json`.
- `support/artifacts/atgb/atgb_04/README.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/README.md`.
- `support/artifacts/atgb/atgb_04/approved_rubric_excerpt.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/approved_rubric_excerpt.md`.
- `support/artifacts/atgb/atgb_04/blank_judgments.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/blank_judgments.json`.
- `support/artifacts/atgb/atgb_04/blank_scoring_forms.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/blank_scoring_forms.md`.
- `support/artifacts/atgb/atgb_04/check_form.cjs`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/check_form.cjs`.
- `support/artifacts/atgb/atgb_04/conversational_review.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/conversational_review.md`.
- `support/artifacts/atgb/atgb_04/evidence_provenance.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/evidence_provenance.md`.
- `support/artifacts/atgb/atgb_04/evidence_sources.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/evidence_sources.json`.
- `support/artifacts/atgb/atgb_04/focused_tests.txt`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/focused_tests.txt`.
- `support/artifacts/atgb/atgb_04/historical_S04_trial_1.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/historical_S04_trial_1.md`.
- `support/artifacts/atgb/atgb_04/package_review.py`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/package_review.py`.
- `support/artifacts/atgb/atgb_04/pending_report.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/pending_report.json`.
- `support/artifacts/atgb/atgb_04/preservation_before.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/preservation_before.json`.
- `support/artifacts/atgb/atgb_04/preservation_checks.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/preservation_checks.json`.
- `support/artifacts/atgb/atgb_04/review.html`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/review.html`.
- `support/artifacts/atgb/atgb_04/review_index.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/review_index.json`.
- `support/artifacts/atgb/atgb_04/review_index.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/review_index.md`.
- `support/artifacts/atgb/atgb_04/scenario_qualifications.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/scenario_qualifications.md`.
- `support/artifacts/atgb/atgb_04/validation_results.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/validation_results.json`.
- `support/artifacts/atgb/atgb_04/verify_package.py`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `artifacts/atgb/atgb_04/verify_package.py`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/corpus.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/visible/S01.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02a_readiness.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_02a_readiness.md`.
- `support/development/reports/atgb_03_initial_live_baseline.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_03_initial_live_baseline.md`.
- `support/development/reports/atgb_03c_live_baseline_continuation.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `development/reports/atgb_03c_live_baseline_continuation.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/product_realization_validation.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `docs/product_realization_validation.md`.
- `support/docs/review_handoff_standard.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `docs/review_handoff_standard.md`.
- `support/docs/validation_evidence_standard.md`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `docs/validation_evidence_standard.md`.
- `support/tests/test_atgb_human_review.py`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `tests/test_atgb_human_review.py`.
- `support/tools/atgb/prepare_human_review.py`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `tools/atgb/prepare_human_review.py`.
- `support/tools/atgb/report_human_review.py`: Preserved authoritative evidence or supporting authority; no new evaluator judgment inferred. Canonical source: `tools/atgb/report_human_review.py`.
- `support/development/reports/atgb_03b_provider_accounting_integrity.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `development/reports/atgb_03b_provider_accounting_integrity.md`.
- `support/development/reports/atgb_04_human_evaluation_preparation.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `development/reports/atgb_04_human_evaluation_preparation.md`.
- `support/artifacts/pr_ef_gm_authority/12_FINAL_RECOMMENDATION.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/pr_ef_gm_authority/12_FINAL_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r6_r4_r1/04_CURRENT_SEMANTIC_PIPELINE.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/pr_eg_r6_r4_r1/04_CURRENT_SEMANTIC_PIPELINE.md`.
- `support/artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r4_r1/37_RECOMMENDED_NEXT_CYCLE.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/pr_eg_r6_r4_r1/37_RECOMMENDED_NEXT_CYCLE.md`.
- `support/development/campaigns/reconciliation/AR-CA_campaign6_chassis_strategy_closeout.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `development/campaigns/reconciliation/AR-CA_campaign6_chassis_strategy_closeout.md`.
- `support/artifacts/atgb/atgb_05a/assessment_import_verification.json`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/assessment_import_verification.json`.
- `support/artifacts/atgb/atgb_05a/ATGB_05_report_before_05a.md`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/ATGB_05_report_before_05a.md`.
- `support/artifacts/atgb/atgb_05a/focused_tests.txt`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/focused_tests.txt`.
- `support/artifacts/atgb/atgb_05a/focused_tests.xml`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/focused_tests.xml`.
- `support/artifacts/atgb/atgb_05a/NEXT_SESSION_before_05a.md`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/NEXT_SESSION_before_05a.md`.
- `support/artifacts/atgb/atgb_05a/preservation_before.json`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/preservation_before.json`.
- `support/artifacts/atgb/atgb_05a/source_manifest.json`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/source_manifest.json`.
- `support/artifacts/atgb/atgb_05a/verify_import.py`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/verify_import.py`.
- `support/artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json`.
- `support/artifacts/atgb/atgb_05a/assessment/ATGB_04_review_summary.md`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `artifacts/atgb/atgb_05a/assessment/ATGB_04_review_summary.md`.
- `support/data/validation/review_handoffs/atgb_05a_assessment_import.json`: Original provisional evidence, byte-preservation provenance, current verification or explicitly historical pre-import orientation. Canonical source: `data/validation/review_handoffs/atgb_05a_assessment_import.json`.
- `support/artifacts/atgb/atgb_05a/verify_bundle.py`: Standalone offline ZIP integrity and false-human-attestation rejection evidence. Canonical source: `artifacts/atgb/atgb_05a/verify_bundle.py`.
- `support/artifacts/atgb/atgb_05a/bundle_verification.json`: Standalone offline ZIP integrity and false-human-attestation rejection evidence. Canonical source: `artifacts/atgb/atgb_05a/bundle_verification.json`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
