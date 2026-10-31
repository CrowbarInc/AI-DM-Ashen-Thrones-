# Campaign

Campaign: PR-EG-R6-R2 — Entity-Role Grounding and Semantic Relevance
Identifier: `pr_eg_r6_r2_grounding_20261017`
Date: 2026-10-17
Generated: 2026-10-17T21:30:10.232173+00:00
Purpose: Implement and qualify bounded semantic correspondence while preserving host authority.

# Executive Summary

**C — SEMANTIC GROUNDING BELOW ACCEPTANCE.** Implemented bounded entity-role and proposition correspondence under the existing R6 gate. 384 tests passed; 5 inherited failures; 0 new failures. Fresh production /api/chat recorded 122 turns across 9 conversations. Matching improved in selected cases, but correction and follow-up failures and clarification loops prevent qualification. No positive qualification is claimed.

Objective status: `C — SEMANTIC GROUNDING BELOW ACCEPTANCE`.

# Changes Made

## Production changes

- game/unified_semantic_planning.py
- game/semantic_correspondence.py

## Validation changes

- 37 new controlled cases, 120 target fresh turns, frozen holdouts.

## Tooling changes

- tools/qualify_pr_eg_r6_r2.py
- tools/baseline_pr_eg_r6_r2.py
- tools/compare_pr_eg_r6_r2.py
- tools/supplement_pr_eg_r6_r2.py
- tools/assess_pr_eg_r6_r2_local.py
- tools/controlled_compare_pr_eg_r6_r2.py
- tools/write_pr_eg_r6_r2_review.py

## Documentation changes

- 36 numbered review artifacts.

## Generated artifacts

- Transcripts, model traces, JUnit, matched comparisons, score audit and metrics.

# What Was Tested

- **Focused tests:** 68 focused tests passed.
- **Broader relevant tests:** 384 passed / 5 inherited failed
- **Full suite:** Not run.
- **Runtime validation:** 122 final-code fresh turns / 9 groups.
- **Model/runtime boundary:** Configured provider; actual model IDs in usage. Separate local transcript scoring is not human qualification.
- **New regressions:** []
- **Pre-existing failures:** ['tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]', 'tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal', 'tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance']
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review below-acceptance result and proposed architecture revision.

# Known Problems / Unresolved Findings

## Campaign-specific

- Corrections and follow-ups fail; generic clarification loops.
- Argument paraphrase and source interpretation remain limited.
- Observed latency and token targets passed; semantic quality remains below acceptance.

## Pre-existing baseline

- Five failures in expanded baseline selection; includes two previously known failures.

# Missing Concepts / Future Capabilities

- Durable delivered-question identities and robust semantic correction binding.

# What This Campaign Does NOT Prove

- A/B qualification, universal semantic correctness, external independent holdout authorship, or full arbitrary-state nonmutation.

# Recommended Next Step

External review of PR-EG-R6-R2. Keep default gate off. Stop; do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `120`
Bundle ZIP size: `000001679125` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r2/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r2/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r2/02_BASELINE_AND_REPOSITORY_STATE.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/02_BASELINE_AND_REPOSITORY_STATE.md`.
- `support/artifacts/pr_eg_r6_r2/03_FAILURE_REPRODUCTION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/03_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r6_r2/04_ENTITY_ROLE_CONTRACT.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/04_ENTITY_ROLE_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2/05_ADDRESSEE_GROUNDING.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/05_ADDRESSEE_GROUNDING.md`.
- `support/artifacts/pr_eg_r6_r2/06_RELATIONSHIP_ARGUMENT_GROUNDING.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/06_RELATIONSHIP_ARGUMENT_GROUNDING.md`.
- `support/artifacts/pr_eg_r6_r2/07_SEMANTIC_PROPOSITION_REPRESENTATION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/07_SEMANTIC_PROPOSITION_REPRESENTATION.md`.
- `support/artifacts/pr_eg_r6_r2/08_SOURCE_PROPOSITION_REPRESENTATION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/08_SOURCE_PROPOSITION_REPRESENTATION.md`.
- `support/artifacts/pr_eg_r6_r2/09_SEMANTIC_RELEVANCE.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/09_SEMANTIC_RELEVANCE.md`.
- `support/artifacts/pr_eg_r6_r2/10_SEMANTIC_MATCHING_ARCHITECTURE.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/10_SEMANTIC_MATCHING_ARCHITECTURE.md`.
- `support/artifacts/pr_eg_r6_r2/11_PROVIDER_RESPONSIBILITIES.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/11_PROVIDER_RESPONSIBILITIES.md`.
- `support/artifacts/pr_eg_r6_r2/12_HOST_RESPONSIBILITIES.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/12_HOST_RESPONSIBILITIES.md`.
- `support/artifacts/pr_eg_r6_r2/13_CANDIDATE_SOURCE_SELECTION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/13_CANDIDATE_SOURCE_SELECTION.md`.
- `support/artifacts/pr_eg_r6_r2/14_ANSWER_SUFFICIENCY.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/14_ANSWER_SUFFICIENCY.md`.
- `support/artifacts/pr_eg_r6_r2/15_CORRECTION_SEMANTICS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/15_CORRECTION_SEMANTICS.md`.
- `support/artifacts/pr_eg_r6_r2/16_CORRECTION_TARGET_BINDING.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/16_CORRECTION_TARGET_BINDING.md`.
- `support/artifacts/pr_eg_r6_r2/17_FOLLOW_UP_CONTINUITY.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/17_FOLLOW_UP_CONTINUITY.md`.
- `support/artifacts/pr_eg_r6_r2/18_CLARIFICATION_QUALITY.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/18_CLARIFICATION_QUALITY.md`.
- `support/artifacts/pr_eg_r6_r2/19_RESPONSE_PLANNING.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/19_RESPONSE_PLANNING.md`.
- `support/artifacts/pr_eg_r6_r2/20_AUTHORIZATION_PRESERVATION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/20_AUTHORIZATION_PRESERVATION.md`.
- `support/artifacts/pr_eg_r6_r2/21_LEGACY_PATH_ISOLATION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/21_LEGACY_PATH_ISOLATION.md`.
- `support/artifacts/pr_eg_r6_r2/22_FEATURE_GATE_BEHAVIOR.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/22_FEATURE_GATE_BEHAVIOR.md`.
- `support/artifacts/pr_eg_r6_r2/23_CONTROLLED_TEST_RESULTS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/23_CONTROLLED_TEST_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r2/24_INDEPENDENT_HOLDOUTS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/24_INDEPENDENT_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6_r2/25_ADVERSARIAL_SEMANTIC_TESTS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/25_ADVERSARIAL_SEMANTIC_TESTS.md`.
- `support/artifacts/pr_eg_r6_r2/26_MATCHED_BASELINE_COMPARISON.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/26_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2/27_FRESH_PROVIDER_CONVERSATIONS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/27_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6_r2/28_TURN_LEVEL_QUALIFICATION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/28_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r2/29_DIALOGUE_QUALITY_AND_PLAYABILITY.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/29_DIALOGUE_QUALITY_AND_PLAYABILITY.md`.
- `support/artifacts/pr_eg_r6_r2/30_PERFORMANCE.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/30_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r2/31_REGRESSION_COMPARISON.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/31_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2/32_ACCEPTANCE_GATES.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/32_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r2/33_REMAINING_LIMITATIONS.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/33_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r2/34_RECOMMENDED_NEXT_ACTION.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/34_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r2/35_FINAL_VERDICT.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/35_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r2/36_SOURCE_AND_EVIDENCE_INVENTORY.md`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/36_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r2/acceptance_gates.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/acceptance_gates.json`.
- `support/artifacts/pr_eg_r6_r2/baseline_junit.xml`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/baseline_junit.xml`.
- `support/artifacts/pr_eg_r6_r2/baseline_repository.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/baseline_repository.json`.
- `support/artifacts/pr_eg_r6_r2/baseline_tests.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/baseline_tests.txt`.
- `support/artifacts/pr_eg_r6_r2/controlled_matched_comparison.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/controlled_matched_comparison.json`.
- `support/artifacts/pr_eg_r6_r2/external_audit_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/external_audit_status.json`.
- `support/artifacts/pr_eg_r6_r2/failure_reproduction.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/failure_reproduction.json`.
- `support/artifacts/pr_eg_r6_r2/focused_junit.xml`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/focused_junit.xml`.
- `support/artifacts/pr_eg_r6_r2/focused_tests.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/focused_tests.txt`.
- `support/artifacts/pr_eg_r6_r2/freeze.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/freeze.json`.
- `support/artifacts/pr_eg_r6_r2/frozen_holdouts.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2/holdout_results.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/holdout_results.json`.
- `support/artifacts/pr_eg_r6_r2/integrity_results.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/integrity_results.json`.
- `support/artifacts/pr_eg_r6_r2/judge_scores.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/judge_scores.json`.
- `support/artifacts/pr_eg_r6_r2/judge_usage.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/judge_usage.json`.
- `support/artifacts/pr_eg_r6_r2/live_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/live_console.txt`.
- `support/artifacts/pr_eg_r6_r2/live_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/live_status.json`.
- `support/artifacts/pr_eg_r6_r2/live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/live_usage.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2/local_assessment_method.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/local_assessment_method.json`.
- `support/artifacts/pr_eg_r6_r2/matched_legacy_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_legacy_console.txt`.
- `support/artifacts/pr_eg_r6_r2/matched_r2_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r2_console.txt`.
- `support/artifacts/pr_eg_r6_r2/matched_r6_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r6_console.txt`.
- `support/artifacts/pr_eg_r6_r2/performance.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/performance.json`.
- `support/artifacts/pr_eg_r6_r2/pilot_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/pilot_console.txt`.
- `support/artifacts/pr_eg_r6_r2/pilot_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/pilot_status.json`.
- `support/artifacts/pr_eg_r6_r2/pilot_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/pilot_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/planning_changes.diff`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/planning_changes.diff`.
- `support/artifacts/pr_eg_r6_r2/primary_live_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/primary_live_status.json`.
- `support/artifacts/pr_eg_r6_r2/primary_live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/primary_live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/qualification_plan.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2/quality_metrics.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/quality_metrics.json`.
- `support/artifacts/pr_eg_r6_r2/regression_comparison.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r2/regression_junit.xml`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r2/regression_tests.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/regression_tests.txt`.
- `support/artifacts/pr_eg_r6_r2/semantic_traces.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2/source_locations.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/source_locations.json`.
- `support/artifacts/pr_eg_r6_r2/supplement_console.txt`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement_console.txt`.
- `support/artifacts/pr_eg_r6_r2/matched_legacy/live_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_legacy/live_status.json`.
- `support/artifacts/pr_eg_r6_r2/matched_legacy/live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_legacy/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_legacy/live_usage.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_legacy/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_legacy/qualification_plan.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_legacy/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2/matched_r2/live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r2/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_r2/live_usage.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r2/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_r2/qualification_plan.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r2/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2/matched_r2/semantic_traces.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r2/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_r6/live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r6/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_r6/live_usage.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r6/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2/matched_r6/qualification_plan.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/matched_r6/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2/supplement/live_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement/live_status.json`.
- `support/artifacts/pr_eg_r6_r2/supplement/live_turns.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2/supplement/live_usage.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2/supplement/qualification_plan.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2/supplement/semantic_traces.jsonl`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/supplement/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2/baseline_sources/game/unified_semantic_planning.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/baseline_sources/game/unified_semantic_planning.py`.
- `support/game/unified_semantic_planning.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/game/semantic_correspondence.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `game/semantic_correspondence.py`.
- `support/tests/test_pr_eg_r6_r2_grounding.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_grounding.py`.
- `support/tools/qualify_pr_eg_r6_r2.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2.py`.
- `support/tools/baseline_pr_eg_r6_r2.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/baseline_pr_eg_r6_r2.py`.
- `support/tools/compare_pr_eg_r6_r2.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/compare_pr_eg_r6_r2.py`.
- `support/tools/supplement_pr_eg_r6_r2.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/supplement_pr_eg_r6_r2.py`.
- `support/tools/assess_pr_eg_r6_r2_local.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/assess_pr_eg_r6_r2_local.py`.
- `support/tools/controlled_compare_pr_eg_r6_r2.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/controlled_compare_pr_eg_r6_r2.py`.
- `support/tools/write_pr_eg_r6_r2_review.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tools/write_pr_eg_r6_r2_review.py`.
- `support/game/dialogue_authority.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `game/dialogue_authority.py`.
- `support/game/immutable_valid_response.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `game/immutable_valid_response.py`.
- `support/game/conversational_continuity.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `game/conversational_continuity.py`.
- `support/tests/test_pr_eg_r2c_speech_adoption.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/tests/test_pr_eg_r2c_r2_reference_eligibility.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r2c_r2_reference_eligibility.py`.
- `support/tests/test_pr_eg_r3_expressive_dialogue.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r3_expressive_dialogue.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tests/test_pr_eg_r4_r1_delivery_integrity.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r4_r1_delivery_integrity.py`.
- `support/tests/test_pr_eg_r6_unified_semantic_planning.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r6_unified_semantic_planning.py`.
- `support/tests/test_pr_eg_r6_r1_disclosure_boundary.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_disclosure_boundary.py`.
- `support/tests/test_pr_eg_r6_r1_r1_provenance.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_r1_provenance.py`.
- `support/tests/test_social_question_relevance_answer_selection.py`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `tests/test_social_question_relevance_answer_selection.py`.
- `support/artifacts/pr_eg_r6/frozen_holdouts.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6/freeze.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6/freeze.json`.
- `support/artifacts/pr_eg_r6_r1_r1/regression_comparison.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r1_r1/live_status.json`: R6-R2 implementation, preserved baseline, or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/live_status.json`.
- `support/artifacts/pr_eg_r6_r2/evidence_inventory.json`: Hashed source and evidence manifest. Canonical source: `artifacts/pr_eg_r6_r2/evidence_inventory.json`.

## Explicit omissions

- `artifacts/pr_eg_r6_r2/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r2/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r6_r2/matched_r2/live_status.json`: duplicate content of artifacts/pr_eg_r6_r2/matched_legacy/live_status.json; canonical reference retained
- `artifacts/pr_eg_r6_r2/matched_r6/live_status.json`: duplicate content of artifacts/pr_eg_r6_r2/matched_legacy/live_status.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
