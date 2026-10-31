# Campaign

Campaign: ATGB-05 Baseline Preservation and NEXT_SESSION Reconciliation
Identifier: `atgb_05_baseline_preservation`
Date: 2026-10-18
Generated: 2026-10-18T23:01:34.966460+00:00
Purpose: Preserve baseline and reconcile current development orientation; import independent AI assessment when original files are available.

# Executive Summary

37 authoritative turns and all 609 protected files are unchanged. NEXT_SESSION now reflects Reconciliation closure and later Product Realization through PR-EG discovery. The two named assessment files could not be located, including the parent project directory and 136 ZIPs. Reported totals are preserved as unverified request metadata, not original evaluator judgments. Human attestation remains false. No gameplay or provider execution. Historical behavioral-packet empty outcome categories mean unmeasured human findings, never zero failures or evidence of success.

Objective status: `PARTIAL: BASELINE PRESERVED AND HANDOFF RECONCILED; ASSESSMENT IMPORT BLOCKED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No benchmark inputs, expectations, rubric or attestation semantics changed. Existing offline tests run.

## Tooling changes

- No reusable benchmark/reporting implementation changed; one campaign-local offline preservation verifier added.

## Documentation changes

- Reconciled NEXT_SESSION; archived prior orientation; ATGB-05 status, missing-import record and three diagnostic recommendations.

## Generated artifacts

- 609-file preservation snapshot; request-reported metadata with false attestation; integrity and test results; standard review export.

# What Was Tested

- **Focused tests:** 21 existing offline review/handoff tests passed; 609 protected file hashes unchanged; exact 37-turn text/state/trial checks passed; false-attestation rejection verified.
- **Broader relevant tests:** Not run; no gameplay change.
- **Full suite:** Not run.
- **Runtime validation:** No gameplay or provider execution; reuses preserved captured evidence. Initial system-temp bundle extraction hit sandbox ACL PermissionError; workspace-local extraction and isolated offline reporting passed.
- **Model/runtime boundary:** Original live-enabled API baseline only. AI assessment files missing, so individual judgments cannot be verified.
- **New regressions:** No gameplay regression claim; protected production and evidence hashes unchanged.
- **Pre-existing failures:** ATGB-03B routing-metadata expectation and missing answer_sufficiency failures remain documented; environment reset failures separate.
- **Self-contained bundle review:** Offline extraction checks ZIP CRC and all packaged canonical hashes, required review sections, exact 37 unique turns with original/continuation trial provenance, setup qualifications and explicit missing-assessment status.

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

- Locate/provide the original AI assessment artifacts; clarify discrepancies if import checks reveal any.
- Review the provisional investigation priorities. No gameplay repair decision is implemented; human scoring remains separate.

# Known Problems / Unresolved Findings

## Campaign-specific

- Original ATGB_04_review_judgments.json and ATGB_04_review_summary.md missing. Import and individual/count agreement checks incomplete.
- Request-reported aggregate totals do not substitute for original judgments.

## Pre-existing baseline

- S03.4/S05.4 faction flags unresolved, not confirmed violations.
- S07/S09 opening delivery limits; unsupported criteria uncertain/not evaluated.
- SDK retries outside application admission counts; accounting version boundary preserved.
- Human scoring pending; exposed held-out content is not unseen generalization.
- Extensive pre-existing dirty worktree retained.

# Missing Concepts / Future Capabilities

- No completed assessment import is claimed; missing individual judgments are not recreated.
- No new infrastructure, gameplay repairs, production migration or PR-EH.

# What This Campaign Does NOT Prove

- Verified assessment coverage or aggregate agreement, authenticated human scoring, conversational competence, playability, repair effectiveness, unseen generalization, broad/full regression, or SDK transport request bounds.

# Recommended Next Step

Review this partial handoff; provide or locate original assessment JSON and summary for import and consistency checks. Then scope the recommended conversational pipeline investigations. No repairs, provider calls, migration or new benchmark infrastructure campaign in this pass.

# Review Bundle Contents

Bundle file count: `123`
Bundle ZIP size: `000000710139` bytes
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
- `support/artifacts/atgb/atgb_05/focused_tests.txt`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/focused_tests.txt`.
- `support/artifacts/atgb/atgb_05/focused_tests.xml`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/focused_tests.xml`.
- `support/artifacts/atgb/atgb_05/NEXT_SESSION_before.md`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/NEXT_SESSION_before.md`.
- `support/artifacts/atgb/atgb_05/preservation_before.json`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/preservation_before.json`.
- `support/artifacts/atgb/atgb_05/requested_assessment_metadata.json`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/requested_assessment_metadata.json`.
- `support/artifacts/atgb/atgb_05/user_request.txt`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/user_request.txt`.
- `support/artifacts/atgb/atgb_05/validation_results.json`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/validation_results.json`.
- `support/artifacts/atgb/atgb_05/verify_preservation.py`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `artifacts/atgb/atgb_05/verify_preservation.py`.
- `support/data/validation/review_handoffs/atgb_05_baseline_preservation.json`: Explicit ATGB-05 evidence, current product status, or integrity record. Missing original assessment remains explicit. Canonical source: `data/validation/review_handoffs/atgb_05_baseline_preservation.json`.
- `support/artifacts/atgb/atgb_05/verify_bundle.py`: Offline ZIP verification evidence and reproducible campaign-local verifier. Canonical source: `artifacts/atgb/atgb_05/verify_bundle.py`.
- `support/artifacts/atgb/atgb_05/bundle_verification.json`: Offline ZIP verification evidence and reproducible campaign-local verifier. Canonical source: `artifacts/atgb/atgb_05/bundle_verification.json`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
