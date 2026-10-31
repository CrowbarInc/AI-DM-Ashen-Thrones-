# Campaign

Campaign: PR-EG-R6-R2-R2 — Semantic Operation Coherence and Multi-Role Propositions
Identifier: `pr_eg_r6_r2_r2_semantic_operations_20261017`
Date: 2026-10-17
Generated: 2026-10-17T23:02:12.111558+00:00
Purpose: Repair and qualify host-validated semantic operations while preserving disclosure and delivery authority.

# Executive Summary

C — SEMANTIC OPERATIONS BELOW ACCEPTANCE. Added named propositions, witnessed bounded role transformations, explicit malformed-plan handling and preserved host authority. 68/68 new controlled cases pass. Regression 485 passed / 19 failed: five inherited, fourteen explained status/target-contract expectation changes. Fresh primary 150 turns / 10 conversations; matched baseline 45 turns; predecessor supplements 89 turns. Explicit local classification 130/150, dependent binding 25/74, false clarification 16/150; optimistic correction/followup success bounds 5/23 and 20/51. Automated grading overcredits failures and is not reliable acceptance evidence; matched relevance and sufficiency improvement remain unverified. Observed integrity checks and separate-process save/load pass within their documented scope. Keep the existing feature gate default off.

Objective status: `C — SEMANTIC OPERATIONS BELOW ACCEPTANCE`.

# Changes Made

## Production changes

- game/semantic_operations.py
- game/conversational_referents.py
- game/semantic_correspondence.py
- game/unified_semantic_planning.py

## Validation changes

- tests/test_pr_eg_r6_r2_r2_operations.py

## Tooling changes

- tools/qualify_pr_eg_r6_r2_r2.py
- tools/audit_pr_eg_r6_r2_r2.py
- tools/assess_pr_eg_r6_r2_r2.py
- tools/probe_pr_eg_r6_r2_r2_restart.py
- tools/write_pr_eg_r6_r2_r2_review.py
- tools/local_pr_eg_r6_r2_r2_assessment.py

## Documentation changes

- 43 numbered review artifacts.

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** 68/68 new cases pass.
- **Broader relevant tests:** 485 passed / 19 failed; 5 inherited, 14 explained changed-contract expectations.
- **Full suite:** Not run.
- **Runtime validation:** 150 primary turns / 10 conversations; 45 matched baseline turns; 89 predecessor supplement turns.
- **Model/runtime boundary:** Real provider, production HTTP. Controlled tests, pilots and automated grading reported separately.
- **New regressions:** ['tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change0]', 'tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change1]', 'tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change2]', 'tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[correction]', 'tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[follow_up]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[forged]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[cross_conversation]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[stale]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[speaker]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[field]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[operation]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[unwitnessed]', 'tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[substitution]', 'tests.test_pr_eg_r6_r2_r1_referents::test_unqualified_historical_id_cannot_override_focus']
- **Pre-existing failures:** ['tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]', 'tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal', 'tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance']
- **Self-contained bundle review:** Structural package verification: ZIP CRC, manifest/source hashes, 43-artifact presence, UTF-8 summary/manifest agreement, excluded state/credentials, source/holdout freezes. All pass. This is not independent human review.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- External review of below-acceptance behavior and fourteen explained contract-expectation failures.

# Known Problems / Unresolved Findings

## Campaign-specific

- Provider classification, target choice and source-role interpretation remain fallible. Current-evidence spans do not independently prove unrestricted semantic entailment. Relationship-specific requested-role names can complicate relationship replacement and source-role alignment. Existing scope prefilter can miss unfamiliar bare corrections. Named-role ontology alignment across independent source interpretations can fail. Historical speech clarification uses bounded question context but does not add a new verified-history retrieval path. Multiple direct sources can still trigger generic clarification. Only finite state projections are measured. New holdouts are internally authored; automated grading shares the configured model and can itself err. Fourteen existing assertions now disagree with deliberate noncritical contract changes. The stricter historical-ID rejection is a design choice, not mandated by the no-legacy-topic-override invariant; an explicitly traced host recovery deserves external review. Keep gate off.

## Pre-existing baseline

- Five inherited selected-suite failures.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- A/B qualification, independent human grading, externally authored holdouts, unrestricted state/disclosure integrity, or full-suite health.

# Recommended Next Step

Stop after PR-EG-R6-R2-R2. Await external review of failed transcripts, source-contract coherence and explained regression identities. Do not begin PR-EH or tune against the now-exposed holdouts.

# Review Bundle Contents

Bundle file count: `195`
Bundle ZIP size: `000003766228` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r2_r2/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r2_r2/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6/frozen_holdouts.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2/frozen_holdouts.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2_r1/frozen_holdouts.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2_r2/02_REPOSITORY_AND_BASELINE_STATE.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/02_REPOSITORY_AND_BASELINE_STATE.md`.
- `support/artifacts/pr_eg_r6_r2_r2/03_FAILURE_REPRODUCTION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/03_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/04_CURRENT_CONTRACT_AUDIT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/04_CURRENT_CONTRACT_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/05_SEMANTIC_OPERATION_TAXONOMY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/05_SEMANTIC_OPERATION_TAXONOMY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/06_OPERATION_CLASSIFICATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/06_OPERATION_CLASSIFICATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/07_MULTI_ROLE_PROPOSITION_CONTRACT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/07_MULTI_ROLE_PROPOSITION_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/08_ROLE_REPRESENTATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/08_ROLE_REPRESENTATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/09_ROLE_IDENTITY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/09_ROLE_IDENTITY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/10_CORRECTION_TRANSFORMATIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/10_CORRECTION_TRANSFORMATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/11_CORRECTION_VALIDATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/11_CORRECTION_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/12_ROLE_REVERSAL.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/12_ROLE_REVERSAL.md`.
- `support/artifacts/pr_eg_r6_r2_r2/13_SUBJECT_OBJECT_CORRECTIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/13_SUBJECT_OBJECT_CORRECTIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/14_RELATIONSHIP_CORRECTIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/14_RELATIONSHIP_CORRECTIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/15_FOLLOW_UP_OPERATIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/15_FOLLOW_UP_OPERATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/16_FOLLOW_UP_BINDING.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/16_FOLLOW_UP_BINDING.md`.
- `support/artifacts/pr_eg_r6_r2_r2/17_FOLLOW_UP_AFTER_UNCERTAINTY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/17_FOLLOW_UP_AFTER_UNCERTAINTY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/18_FOLLOW_UP_AFTER_PARTIAL_ANSWER.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/18_FOLLOW_UP_AFTER_PARTIAL_ANSWER.md`.
- `support/artifacts/pr_eg_r6_r2_r2/19_ANSWER_STATUS_CONTRACT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/19_ANSWER_STATUS_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/20_ANSWER_STATUS_VALIDATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/20_ANSWER_STATUS_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/21_MALFORMED_PROVIDER_OUTPUT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/21_MALFORMED_PROVIDER_OUTPUT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/22_BOUNDED_RECOVERY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/22_BOUNDED_RECOVERY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/23_CLARIFICATION_DISCIPLINE.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/23_CLARIFICATION_DISCIPLINE.md`.
- `support/artifacts/pr_eg_r6_r2_r2/24_PROVIDER_INPUT_OUTPUT_CONTRACT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/24_PROVIDER_INPUT_OUTPUT_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/25_HOST_VALIDATION_ORDER.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/25_HOST_VALIDATION_ORDER.md`.
- `support/artifacts/pr_eg_r6_r2_r2/26_REFERENT_PERSISTENCE.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/26_REFERENT_PERSISTENCE.md`.
- `support/artifacts/pr_eg_r6_r2_r2/27_LEGACY_ROUTING.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/27_LEGACY_ROUTING.md`.
- `support/artifacts/pr_eg_r6_r2_r2/28_CONTROLLED_TESTS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/28_CONTROLLED_TESTS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/29_FROZEN_HOLDOUTS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/29_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/30_ADVERSARIAL_QUALIFICATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/30_ADVERSARIAL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/31_MATCHED_BASELINE_COMPARISON.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/31_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2_r2/32_FRESH_PROVIDER_CONVERSATIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/32_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/33_INDEPENDENT_ASSESSMENT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/33_INDEPENDENT_ASSESSMENT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/34_TURN_LEVEL_QUALIFICATION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/34_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/35_DIALOGUE_QUALITY_AND_PLAYABILITY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/35_DIALOGUE_QUALITY_AND_PLAYABILITY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/36_PERFORMANCE.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/36_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r2_r2/37_REGRESSION_COMPARISON.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/37_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2_r2/38_ACCEPTANCE_GATES.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/38_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r2_r2/39_FAILURE_ATTRIBUTION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/39_FAILURE_ATTRIBUTION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/40_REMAINING_LIMITATIONS.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/40_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r2/41_RECOMMENDED_NEXT_ACTION.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/41_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r2_r2/42_FINAL_VERDICT.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/42_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r2_r2/43_SOURCE_AND_EVIDENCE_INVENTORY.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/43_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r2_r2/acceptance_gates.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/acceptance_gates.json`.
- `support/artifacts/pr_eg_r6_r2_r2/adversarial_contract_results.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/adversarial_contract_results.json`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/qualification_plan.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_grading_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_grading_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_head.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_head.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_junit.xml`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/conversational_continuity.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/conversational_referents.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/conversational_referents.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/dialogue_authority.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/dialogue_authority.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/immutable_valid_response.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/immutable_valid_response.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/semantic_correspondence.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/semantic_correspondence.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_sources/game/unified_semantic_planning.py`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_sources/game/unified_semantic_planning.py`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_tests.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_tests_unsandboxed.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_tests_unsandboxed.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/baseline_unsandboxed_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/baseline_unsandboxed_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/caller_inventory.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/caller_inventory.json`.
- `support/artifacts/pr_eg_r6_r2_r2/campaign_request.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/campaign_request.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/controlled_junit.xml`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/controlled_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r2/controlled_tests.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/controlled_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/conversational_referents_changes.diff`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/conversational_referents_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r2/failure_attribution.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/failure_attribution.json`.
- `support/artifacts/pr_eg_r6_r2_r2/final/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/final/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/final/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/final/qualification_plan.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r2/final/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/final/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/final_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/final_source_freeze.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/final_source_freeze.json`.
- `support/artifacts/pr_eg_r6_r2_r2/focus_junit.xml`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/focus_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r2/focus_tests.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/focus_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/focus_tests_unsandboxed.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/focus_tests_unsandboxed.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/freeze.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/freeze.json`.
- `support/artifacts/pr_eg_r6_r2_r2/frozen_holdouts.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_blind_map.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_blind_map.json`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_completed_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_completed_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_criteria.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_criteria.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_final_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_final_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_more_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_more_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/grading_payloads.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/grading_payloads.json`.
- `support/artifacts/pr_eg_r6_r2_r2/holdout_results.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/holdout_results.json`.
- `support/artifacts/pr_eg_r6_r2_r2/independent_grades.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/independent_grades.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/integrity_results.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/integrity_results.json`.
- `support/artifacts/pr_eg_r6_r2_r2/late_validation_audit.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/late_validation_audit.json`.
- `support/artifacts/pr_eg_r6_r2_r2/local_assessment.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/local_assessment.json`.
- `support/artifacts/pr_eg_r6_r2_r2/matched_comparison.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/matched_comparison.json`.
- `support/artifacts/pr_eg_r6_r2_r2/performance.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/performance.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/qualification_plan.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_2_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_2_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_3/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_3/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_3/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_3/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_3/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_3/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_3/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_3/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_3/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_3/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_4_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_4_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_5/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_5/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_5/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_5/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_5/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_5/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_5/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_5/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_5/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_5/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_7/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_7/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_7/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_7/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_7/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_7/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_7/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_7/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_7/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_7/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pilot_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pilot_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_final/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_final/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_final/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_final/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_final/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_final/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_final/starting_source_hashes.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_final/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/qualification_plan.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/pre_robustness_source_freeze.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/pre_robustness_source_freeze.json`.
- `support/artifacts/pr_eg_r6_r2_r2/predecessors/live_status.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/predecessors/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r2/predecessors/live_turns.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/predecessors/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/predecessors/live_usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/predecessors/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/predecessors/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/predecessors/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/predecessors_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/predecessors_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/preimplementation_contract_audit.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/preimplementation_contract_audit.md`.
- `support/artifacts/pr_eg_r6_r2_r2/preimplementation_failures.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/preimplementation_failures.json`.
- `support/artifacts/pr_eg_r6_r2_r2/preimplementation_source_inventory.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/preimplementation_source_inventory.json`.
- `support/artifacts/pr_eg_r6_r2_r2/quality_metrics.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/quality_metrics.json`.
- `support/artifacts/pr_eg_r6_r2_r2/refinal_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/refinal_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/regression_comparison.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r2_r2/regression_junit.xml`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r2/regression_tests.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/regression_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/repository_status.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/repository_status.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/repredecessors_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/repredecessors_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/restart/result.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/restart/result.json`.
- `support/artifacts/pr_eg_r6_r2_r2/restart/semantic_traces.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/restart/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/restart/usage.jsonl`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/restart/usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r2/restart_console.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/restart_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/robustness_refreeze.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/robustness_refreeze.json`.
- `support/artifacts/pr_eg_r6_r2_r2/runtime_probe.txt`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/runtime_probe.txt`.
- `support/artifacts/pr_eg_r6_r2_r2/semantic_contract.md`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/semantic_contract.md`.
- `support/artifacts/pr_eg_r6_r2_r2/semantic_correspondence_changes.diff`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/semantic_correspondence_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r2/semantic_operations_changes.diff`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/semantic_operations_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r2/turn_scores.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/turn_scores.json`.
- `support/artifacts/pr_eg_r6_r2_r2/unified_semantic_planning_changes.diff`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/unified_semantic_planning_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r2/verdict.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/verdict.json`.
- `support/artifacts/pr_eg_r6_r2_r2/verified_predecessor_metrics.json`: Semantic operation source or preserved qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r2/verified_predecessor_metrics.json`.
- `support/game/api.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/api.py`.
- `support/game/conversational_orchestration.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/conversational_orchestration.py`.
- `support/game/conversational_referents.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/conversational_referents.py`.
- `support/game/semantic_correspondence.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/semantic_correspondence.py`.
- `support/game/semantic_operations.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/semantic_operations.py`.
- `support/game/social.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/social.py`.
- `support/game/storage.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/storage.py`.
- `support/game/unified_semantic_planning.py`: Semantic operation source or preserved qualification evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/tests/test_pr_eg_dialogue_quality.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_dialogue_quality.py`.
- `support/tests/test_pr_eg_r1_continuity.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r1_continuity.py`.
- `support/tests/test_pr_eg_r2c_r2_reference_eligibility.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r2c_r2_reference_eligibility.py`.
- `support/tests/test_pr_eg_r2c_speech_adoption.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/tests/test_pr_eg_r3_expressive_dialogue.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r3_expressive_dialogue.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tests/test_pr_eg_r4_r1_delivery_integrity.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r4_r1_delivery_integrity.py`.
- `support/tests/test_pr_eg_r6_r1_disclosure_boundary.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_disclosure_boundary.py`.
- `support/tests/test_pr_eg_r6_r1_r1_provenance.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_r1_provenance.py`.
- `support/tests/test_pr_eg_r6_r2_grounding.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_grounding.py`.
- `support/tests/test_pr_eg_r6_r2_r1_referents.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_r1_referents.py`.
- `support/tests/test_pr_eg_r6_r2_r2_operations.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_r2_operations.py`.
- `support/tests/test_pr_eg_r6_unified_semantic_planning.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_pr_eg_r6_unified_semantic_planning.py`.
- `support/tests/test_social_question_relevance_answer_selection.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tests/test_social_question_relevance_answer_selection.py`.
- `support/tools/assess_pr_eg_r6_r2_r2.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/assess_pr_eg_r6_r2_r2.py`.
- `support/tools/audit_pr_eg_r6_r2_r2.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/audit_pr_eg_r6_r2_r2.py`.
- `support/tools/local_pr_eg_r6_r2_r2_assessment.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/local_pr_eg_r6_r2_r2_assessment.py`.
- `support/tools/probe_pr_eg_r6_r2_r2_restart.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/probe_pr_eg_r6_r2_r2_restart.py`.
- `support/tools/qualify_pr_eg_r6.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/qualify_pr_eg_r6.py`.
- `support/tools/qualify_pr_eg_r6_r2.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2.py`.
- `support/tools/qualify_pr_eg_r6_r2_r1.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2_r1.py`.
- `support/tools/qualify_pr_eg_r6_r2_r2.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2_r2.py`.
- `support/tools/write_pr_eg_r6_r2_r2_review.py`: Semantic operation source or preserved qualification evidence. Canonical source: `tools/write_pr_eg_r6_r2_r2_review.py`.
- `support/artifacts/pr_eg_r6_r2_r2/evidence_inventory.json`: Complete hashed evidence inventory. Canonical source: `artifacts/pr_eg_r6_r2_r2/evidence_inventory.json`.

## Explicit omissions

- `artifacts/pr_eg_r6_r2_r2/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r2_r2/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pilot_3/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pilot_3_console.txt`: duplicate content of artifacts/pr_eg_r6_r2_r2/pilot_2_console.txt; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pilot_5/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pilot_7/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pre_robustness_final/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/final/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/starting_source_hashes.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/pre_robustness_final/starting_source_hashes.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/predecessors/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/pre_robustness_predecessors/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r2/predecessors/starting_source_hashes.json`: duplicate content of artifacts/pr_eg_r6_r2_r2/final/starting_source_hashes.json; canonical reference retained
- `game/conversational_continuity.py`: duplicate content of artifacts/pr_eg_r6_r2_r2/baseline_sources/game/conversational_continuity.py; canonical reference retained
- `game/dialogue_authority.py`: duplicate content of artifacts/pr_eg_r6_r2_r2/baseline_sources/game/dialogue_authority.py; canonical reference retained
- `game/immutable_valid_response.py`: duplicate content of artifacts/pr_eg_r6_r2_r2/baseline_sources/game/immutable_valid_response.py; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
