# Campaign

Campaign: PR-EG-R2C-R2 — Reference Eligibility & Resolver Handoff
Identifier: `pr_eg_r2c_r2_reference_eligibility_20261017`
Date: 2026-10-17
Generated: 2026-10-17T13:12:19.959684+00:00
Purpose: Focused repair and qualification; stop after R2C-R2 and await external review.

# Executive Summary

**B — REPAIR QUALIFIED WITH LIMITATIONS; R2C CLOSURE RECOMMENDED.** Engine grounding now reconciles provider unresolved-reference annotations before interpretation eligibility and at the stored-record bridge. Existing addressee grounding and authored topic selection determine eligibility; the existing social resolver retains disclosure and immutable speech adoption. Bare repetition after an unresolved clarification repeats the actual GM question and preserves pending intent.



Relevant regression: {'passed': 584, 'failed': 25} before → {'passed': 650, 'failed': 25} after; no new failure identities or lost baseline passes. All 66 focused checks pass. All 15 unchanged R1 holdouts pass. Final independent N01–N05 pass, as do C01–C03, S01–S05 and L01–L02. The initial F07 retention expectation is preserved as failed and superseded; it is not counted as passing independent final evidence.



Final fresh production /api/chat: 16 primary + 13 secondary turns; 29/29 provenance/relevance/state audits pass. 18 interpretation calls, 0 narration calls, 0 retries; 34,351 input / 3,412 output tokens; mean 1.68s, maximum 3.34s per turn.



Qualification is bounded to the recorded scenes and configured route. Unclassified unsupported annotations remain conservative; arbitrary semantic grounding and unlimited memory are not established. Stop after R2C-R2 and await external review. Do not begin R3.

Objective status: `B — REPAIR QUALIFIED WITH LIMITATIONS; R2C CLOSURE RECOMMENDED`.

# Changes Made

## Production changes

- Reference reconciliation using existing grounding/selector and unresolved clarification continuity.

## Validation changes

- T01–T28, adversarial/status controls and frozen expectations; retain failed evidence.

## Tooling changes

- Production HTTP runner, exact baseline/final comparison and provenance/state/cost audits.

## Documentation changes

- All 25 requested numbered reports.

## Generated artifacts

- Provider journals, full transcripts/states, source hashes/diffs, JUnit identities and failed-attempt archives.

# What Was Tested

- **Focused tests:** 66 focused tests pass; R1 15/15; final independent N01–N05 5/5.
- **Broader relevant tests:** {'passed': 584, 'failed': 25} → {'passed': 650, 'failed': 25}
- **Full suite:** Not run; relevant family only.
- **Runtime validation:** 16 primary + 13 secondary fresh-provider production HTTP turns; 29/29 audits pass.
- **Model/runtime boundary:** Configured gpt-4.1-mini; actual Responses interpretation, no live doubles/replay.
- **New regressions:** []
- **Pre-existing failures:** 25 unchanged identities; report 16/final.xml.
- **Self-contained bundle review:** Verify all 25 reports, source hashes, baseline/final identities, retained failures, frozen expectations and full fresh-provider transcripts/states/usage; no credentials or active campaign saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- External review of R2C-R2 repair, evidence and closure recommendation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Bounded lexical/symbolic grounding; unsupported unclassified annotations remain conservative.
- F07 old retention expectation is superseded and preserved as failed; new independent N01–N05 qualify final behavior.

## Pre-existing baseline

- 25 inherited relevant-family failures remain outside scope.

# Missing Concepts / Future Capabilities

- Arbitrary semantic entity grounding and unlimited conversation memory were not added.

# What This Campaign Does NOT Prove

- All repository tests passing, arbitrary annotation understanding, unrestricted generated-speech safety, unlimited memory or process-restart persistence.

# Recommended Next Step

Recommend R2C closure with documented limitations after external review. Stop after R2C-R2; do not proceed to R3.

# Review Bundle Contents

Bundle file count: `162`
Bundle ZIP size: `000020238655` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r2c_r2/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r2c_r2/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r2c_r2/02_BASELINE_AND_ENVIRONMENT.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r2c_r2/03_HISTORICAL_FAILURE_REPRODUCTION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/03_HISTORICAL_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r2c_r2/04_REFERENCE_AUTHORITY_CONTRACT.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/04_REFERENCE_AUTHORITY_CONTRACT.md`.
- `support/artifacts/pr_eg_r2c_r2/05_ANNOTATION_RECONCILIATION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/05_ANNOTATION_RECONCILIATION.md`.
- `support/artifacts/pr_eg_r2c_r2/06_ADDRESSEE_AND_SUBJECT_GROUNDING.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/06_ADDRESSEE_AND_SUBJECT_GROUNDING.md`.
- `support/artifacts/pr_eg_r2c_r2/07_RESOLVER_HANDOFF.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/07_RESOLVER_HANDOFF.md`.
- `support/artifacts/pr_eg_r2c_r2/08_KNOWLEDGE_VS_REFERENCE.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/08_KNOWLEDGE_VS_REFERENCE.md`.
- `support/artifacts/pr_eg_r2c_r2/09_CONVERSATIONAL_CONTINUITY.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/09_CONVERSATIONAL_CONTINUITY.md`.
- `support/artifacts/pr_eg_r2c_r2/10_INFORMATION_INTEGRITY_PRESERVATION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/10_INFORMATION_INTEGRITY_PRESERVATION.md`.
- `support/artifacts/pr_eg_r2c_r2/11_CROSS_DOMAIN_SAFETY.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/11_CROSS_DOMAIN_SAFETY.md`.
- `support/artifacts/pr_eg_r2c_r2/12_SOURCE_CHANGE_INVENTORY.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/12_SOURCE_CHANGE_INVENTORY.md`.
- `support/artifacts/pr_eg_r2c_r2/13_TARGETED_TESTS.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/13_TARGETED_TESTS.md`.
- `support/artifacts/pr_eg_r2c_r2/14_ADVERSARIAL_ANNOTATIONS.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/14_ADVERSARIAL_ANNOTATIONS.md`.
- `support/artifacts/pr_eg_r2c_r2/15_FROZEN_HOLDOUTS.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/15_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r2c_r2/16_REGRESSION_COMPARISON.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/16_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r2c_r2/17_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/17_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r2c_r2/18_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/18_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r2c_r2/19_PROVIDER_PERFORMANCE.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/19_PROVIDER_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r2c_r2/20_STATE_INTEGRITY_AUDIT.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/20_STATE_INTEGRITY_AUDIT.md`.
- `support/artifacts/pr_eg_r2c_r2/21_REMAINING_LIMITATIONS.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/21_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r2c_r2/22_R2C_CLOSURE_ASSESSMENT.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/22_R2C_CLOSURE_ASSESSMENT.md`.
- `support/artifacts/pr_eg_r2c_r2/23_NEXT_CYCLE_RECOMMENDATION.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/23_NEXT_CYCLE_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r2c_r2/24_FINAL_VERDICT.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/24_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r2c_r2/25_SOURCE_AND_EVIDENCE_INVENTORY.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/25_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r2c_r2/acceptance_gates.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/acceptance_gates.json`.
- `support/artifacts/pr_eg_r2c_r2/adversarial.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/adversarial.py`.
- `support/artifacts/pr_eg_r2c_r2/adversarial_annotations.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/adversarial_annotations.json`.
- `support/artifacts/pr_eg_r2c_r2/after_reproduction.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/after_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r2/audit_evidence.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/audit_evidence.py`.
- `support/artifacts/pr_eg_r2c_r2/baseline.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/baseline.xml`.
- `support/artifacts/pr_eg_r2c_r2/baseline_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/baseline_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/before_reproduction.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/before_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r2/build_review.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/build_review.py`.
- `support/artifacts/pr_eg_r2c_r2/clarification_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/clarification_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/clarification_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/clarification_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r2/clarification_probe.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/clarification_probe.json`.
- `support/artifacts/pr_eg_r2c_r2/development_provider_cost.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/development_provider_cost.json`.
- `support/artifacts/pr_eg_r2c_r2/environment.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/environment.json`.
- `support/artifacts/pr_eg_r2c_r2/evaluate_predecessor_holdouts.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/evaluate_predecessor_holdouts.py`.
- `support/artifacts/pr_eg_r2c_r2/final.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final.xml`.
- `support/artifacts/pr_eg_r2c_r2/final_annotation_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_annotation_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/final_annotation_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_annotation_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r2/final_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/final_literal_qualified_live_usage.jsonl`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_literal_qualified_live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r2/final_live_usage.jsonl`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r2/final_provider_usage.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_provider_usage.json`.
- `support/artifacts/pr_eg_r2c_r2/final_qualified_live_usage.jsonl`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/final_qualified_live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r2/freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/frozen_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r2/grounding_trace.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/grounding_trace.json`.
- `support/artifacts/pr_eg_r2c_r2/historical_interpretation.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/historical_interpretation.json`.
- `support/artifacts/pr_eg_r2c_r2/intermediate_failure_audit.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/intermediate_failure_audit.json`.
- `support/artifacts/pr_eg_r2c_r2/literal_role_before.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/literal_role_before.json`.
- `support/artifacts/pr_eg_r2c_r2/literal_role_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/literal_role_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/literal_role_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/literal_role_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r2/live_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/live_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/live_plan.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_plan.json`.
- `support/artifacts/pr_eg_r2c_r2/live_qualification.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r2/live_semantic_audit.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_semantic_audit.json`.
- `support/artifacts/pr_eg_r2c_r2/live_status.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_status.json`.
- `support/artifacts/pr_eg_r2c_r2/live_usage.jsonl`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r2/original_holdout_final_attempt.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/original_holdout_final_attempt.json`.
- `support/artifacts/pr_eg_r2c_r2/performance.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/performance.json`.
- `support/artifacts/pr_eg_r2c_r2/predecessor_holdout_results.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/predecessor_holdout_results.json`.
- `support/artifacts/pr_eg_r2c_r2/primary_transcript.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/primary_transcript.md`.
- `support/artifacts/pr_eg_r2c_r2/probe_clarification.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/probe_clarification.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_live_usage.jsonl`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r2/qualification_source_hashes.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r2/regression_comparison.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/regression_comparison.json`.
- `support/artifacts/pr_eg_r2c_r2/regression_selection.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/regression_selection.json`.
- `support/artifacts/pr_eg_r2c_r2/reproduce.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/reproduce.py`.
- `support/artifacts/pr_eg_r2c_r2/run_final.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/run_final.py`.
- `support/artifacts/pr_eg_r2c_r2/secondary_transcript.md`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/secondary_transcript.md`.
- `support/artifacts/pr_eg_r2c_r2/source_changes.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/source_changes.json`.
- `support/artifacts/pr_eg_r2c_r2/state_audit.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/state_audit.json`.
- `support/artifacts/pr_eg_r2c_r2/status_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/status_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/status_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/status_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r2/targeted.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted.xml`.
- `support/artifacts/pr_eg_r2c_r2/targeted_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/targeted_final.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_final.xml`.
- `support/artifacts/pr_eg_r2c_r2/targeted_final_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_final_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/targeted_qualified.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_qualified.xml`.
- `support/artifacts/pr_eg_r2c_r2/targeted_qualified_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_qualified_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/targeted_results.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_results.json`.
- `support/artifacts/pr_eg_r2c_r2/targeted_status.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_status.xml`.
- `support/artifacts/pr_eg_r2c_r2/targeted_status_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/targeted_status_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/working_tree_before.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/working_tree_before.txt`.
- `support/artifacts/pr_eg_r2c_r2/diffs/conversational_continuity.py.diff`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/diffs/conversational_continuity.py.diff`.
- `support/artifacts/pr_eg_r2c_r2/diffs/live_chat_interpretation.py.diff`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/diffs/live_chat_interpretation.py.diff`.
- `support/artifacts/pr_eg_r2c_r2/diffs/player_interpretation_bridge.py.diff`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/diffs/player_interpretation_bridge.py.diff`.
- `support/artifacts/pr_eg_r2c_r2/diffs/test_pr_ef_r2_social_authority.py.diff`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/diffs/test_pr_ef_r2_social_authority.py.diff`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final.xml`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/final_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_plan.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_plan.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_qualification.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_status.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_status.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/source_hashes.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/adversarial_annotations.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/adversarial_annotations.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final.xml`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/final_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_plan.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_plan.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_qualification.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_semantic_audit.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_semantic_audit.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/performance.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/performance.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/qualification_source_hashes.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/qualification_source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/targeted_results.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/targeted_results.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/test_pr_eg_r2c_r2_reference_eligibility.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/test_pr_eg_r2c_r2_reference_eligibility.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final.xml`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final.xml`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_console.txt`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_console.txt`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_freeze.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_plan.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_plan.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_qualification.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_status.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/live_status.json`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/source_hashes.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r2/before_sources/game/conversational_continuity.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/before_sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r2c_r2/before_sources/game/live_chat_interpretation.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/before_sources/game/live_chat_interpretation.py`.
- `support/artifacts/pr_eg_r2c_r2/before_sources/game/player_interpretation_bridge.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/before_sources/game/player_interpretation_bridge.py`.
- `support/artifacts/pr_eg_r2c_r2/before_sources/tests/test_pr_ef_r2_social_authority.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/before_sources/tests/test_pr_ef_r2_social_authority.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/conversational_continuity.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/live_chat_interpretation.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/live_chat_interpretation.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/player_interpretation_bridge.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/player_interpretation_bridge.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/live_chat_interpretation.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/live_chat_interpretation.py`.
- `support/artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/player_interpretation_bridge.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/player_interpretation_bridge.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/api.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/api.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/conversational_orchestration.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/conversational_orchestration.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/dialogue_authority.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/dialogue_authority.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/immutable_valid_response.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/immutable_valid_response.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/ordinary_semantic_ownership.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/ordinary_semantic_ownership.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/player_interpretation_bridge.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/player_interpretation_bridge.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/provider_budget.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/provider_budget.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/social.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/social.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/game/storage.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/game/storage.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_du_player_pipeline.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_du_player_pipeline.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_gm_authority.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_gm_authority.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_r2_social_authority.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_r2_social_authority.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_r4_authorization.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_ef_r4_authorization.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_eg_r2c_r2_reference_eligibility.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_eg_r2c_r2_reference_eligibility.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tests/test_pr_eg_r2c_speech_adoption.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tools/build_review_handoff.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tools/build_review_handoff.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/tools/validate_pr_eg_r2c_r2.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/tools/validate_pr_eg_r2c_r2.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/adapter.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/adapter.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/eligibility.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/eligibility.py`.
- `support/artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/schema.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/sources/experiments/pr_do/schema.py`.
- `support/artifacts/pr_eg_r2c_r1/frozen_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/final_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/final_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/final_holdouts_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/final_holdouts_freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_holdouts_freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_holdouts_freeze.json`.
- `support/artifacts/pr_eg_r2c/frozen_holdouts.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r2c/freeze.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c/freeze.json`.
- `support/artifacts/run_r2c_r2_baseline.py`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/run_r2c_r2_baseline.py`.
- `support/artifacts/pr_eg_r2c_r2/artifact_inventory.json`: Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure. Canonical source: `artifacts/pr_eg_r2c_r2/artifact_inventory.json`.

## Explicit omissions

- `artifacts/pr_eg_r2c_r2/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r2c_r2/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/clarification_probe.json`: duplicate content of artifacts/pr_eg_r2c_r2/clarification_probe.json; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_clarification_fix/live_usage.jsonl`: duplicate content of artifacts/pr_eg_r2c_r2/live_usage.jsonl; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/acceptance_gates.json`: duplicate content of artifacts/pr_eg_r2c_r2/acceptance_gates.json; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_status.json`: duplicate content of artifacts/pr_eg_r2c_r2/live_status.json; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/qualification_live_usage.jsonl`: duplicate content of artifacts/pr_eg_r2c_r2/qualification_live_usage.jsonl; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/final_live_usage.jsonl`: duplicate content of artifacts/pr_eg_r2c_r2/final_live_usage.jsonl; canonical reference retained
- `artifacts/pr_eg_r2c_r2/qualification_before_status_fix/sources/game/conversational_continuity.py`: duplicate content of artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/conversational_continuity.py; canonical reference retained
- `artifacts/pr_eg_r2c_r2/sources/game/conversational_continuity.py`: duplicate content of artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/conversational_continuity.py; canonical reference retained
- `artifacts/pr_eg_r2c_r2/sources/game/live_chat_interpretation.py`: duplicate content of artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/sources/game/live_chat_interpretation.py; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
