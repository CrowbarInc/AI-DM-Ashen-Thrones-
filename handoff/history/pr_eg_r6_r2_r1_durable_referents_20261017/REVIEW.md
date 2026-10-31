# Campaign

Campaign: PR-EG-R6-R2-R1 — Durable Conversational Referents and Correction Binding
Identifier: `pr_eg_r6_r2_r1_durable_referents_20261017`
Date: 2026-10-17
Generated: 2026-10-17T22:07:02.771927+00:00
Purpose: Repair and qualify durable host-owned question continuity without changing disclosure authority.

# Executive Summary

C — REFERENT CONTINUITY BELOW ACCEPTANCE. Implemented bounded host-owned question IDs, correction deltas, lineage, active focus, persisted answer statuses and post-seal commits under the existing default-off gate. Final regressions: 431 passed, 5 inherited failed, no new failures. Primary fresh-provider qualification: 120 turns / 8 groups; corrections 7/13, follow-ups 18/28, false clarifications 22/120. Additional unchanged predecessor holdouts: 29 turns / 2 groups. Separate-process save/load correction passed. Observed integrity checks passed within their documented scope. Acceptance thresholds remain unmet.

Objective status: `C — REFERENT CONTINUITY BELOW ACCEPTANCE`.

# Changes Made

## Production changes

- game/conversational_referents.py
- game/unified_semantic_planning.py
- game/conversational_continuity.py

## Validation changes

- 47 added controlled cases; final production HTTP and frozen holdouts; restart continuation.

## Tooling changes

- tools/qualify_pr_eg_r6_r2_r1.py
- tools/compare_pr_eg_r6_r2_r1.py
- tools/probe_pr_eg_r6_r2_r1_restart.py
- tools/assess_pr_eg_r6_r2_r1.py
- tools/write_pr_eg_r6_r2_r1_review.py

## Documentation changes

- 40 numbered review artifacts.

## Generated artifacts

- Baseline/final transcripts, raw provider proposals, metrics, gates, JUnit and source diffs.

# What Was Tested

- **Focused tests:** 47 new controlled cases pass; earlier 68 predecessor-focused cases pass.
- **Broader relevant tests:** 431 passed, 5 inherited failed, no new failures.
- **Full suite:** Not run.
- **Runtime validation:** 120 turns / 8 primary groups + 29 frozen predecessor turns / 2 groups + 1 process-restart turn.
- **Model/runtime boundary:** Real configured provider; deterministic tests and development pilots excluded from final evidence.
- **New regressions:** []
- **Pre-existing failures:** ['tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]', 'tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]', 'tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal', 'tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance']
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- External review of below-acceptance repair and failed holdout evidence.

# Known Problems / Unresolved Findings

## Campaign-specific

- Correction 53.8%, follow-up 64.3%, semantic binding 61.0%, false clarification 18.3%.
- Role reversals/relationship changes, wrong public-source correction, partial-status errors and generic clarifications remain.
- P95 latency 5.107 seconds misses 5-second target; one 33,411 input-token outlier.

## Pre-existing baseline

- Five selected test failures remain inherited; expanded baseline had six.

# Missing Concepts / Future Capabilities

- Reliable multi-argument speech semantics, targeted clarification and historical/temporal focus retention.

# What This Campaign Does NOT Prove

- A/B qualification, externally authored independent holdouts, unrestricted semantic correctness, full-state nonmutation, or full regression-suite health.

# Recommended Next Step

Review PR-EG-R6-R2-R1 externally; keep feature default off. Stop; do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `153`
Bundle ZIP size: `000001969498` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r2_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r2_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6/frozen_holdouts.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2/frozen_holdouts.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2_r1/02_BASELINE_AND_REPOSITORY_STATE.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/02_BASELINE_AND_REPOSITORY_STATE.md`.
- `support/artifacts/pr_eg_r6_r2_r1/03_FAILURE_REPRODUCTION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/03_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/04_CONVERSATIONAL_STATE_INVENTORY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/04_CONVERSATIONAL_STATE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/05_DURABLE_REFERENT_CONTRACT.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/05_DURABLE_REFERENT_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r1/06_REFERENT_IDENTITY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/06_REFERENT_IDENTITY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/07_REFERENT_LIFECYCLE.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/07_REFERENT_LIFECYCLE.md`.
- `support/artifacts/pr_eg_r6_r2_r1/08_ACTIVE_QUESTION_TRACKING.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/08_ACTIVE_QUESTION_TRACKING.md`.
- `support/artifacts/pr_eg_r6_r2_r1/09_CORRECTION_OPERATIONS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/09_CORRECTION_OPERATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/10_CORRECTION_LINEAGE.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/10_CORRECTION_LINEAGE.md`.
- `support/artifacts/pr_eg_r6_r2_r1/11_CORRECTION_EXAMPLES.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/11_CORRECTION_EXAMPLES.md`.
- `support/artifacts/pr_eg_r6_r2_r1/12_FOLLOW_UP_BINDING.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/12_FOLLOW_UP_BINDING.md`.
- `support/artifacts/pr_eg_r6_r2_r1/13_FOLLOW_UP_SEMANTICS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/13_FOLLOW_UP_SEMANTICS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/14_FOLLOW_UP_AFTER_UNCERTAINTY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/14_FOLLOW_UP_AFTER_UNCERTAINTY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/15_FOLLOW_UP_AFTER_PARTIAL_ANSWER.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/15_FOLLOW_UP_AFTER_PARTIAL_ANSWER.md`.
- `support/artifacts/pr_eg_r6_r2_r1/16_MULTIPLE_REFERENT_RESOLUTION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/16_MULTIPLE_REFERENT_RESOLUTION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/17_SPEAKER_AND_ADDRESSEE_CONTINUITY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/17_SPEAKER_AND_ADDRESSEE_CONTINUITY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/18_CLARIFICATION_DISCIPLINE.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/18_CLARIFICATION_DISCIPLINE.md`.
- `support/artifacts/pr_eg_r6_r2_r1/19_PROVIDER_INPUT_CONTRACT.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/19_PROVIDER_INPUT_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r1/20_PROVIDER_OUTPUT_CONTRACT.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/20_PROVIDER_OUTPUT_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r2_r1/21_HOST_VALIDATION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/21_HOST_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/22_TRANSACTIONAL_REFERENT_UPDATES.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/22_TRANSACTIONAL_REFERENT_UPDATES.md`.
- `support/artifacts/pr_eg_r6_r2_r1/23_SAVE_LOAD_INTEGRITY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/23_SAVE_LOAD_INTEGRITY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/24_RETENTION_AND_COMPACTION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/24_RETENTION_AND_COMPACTION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/25_RESPONSE_PLANNING.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/25_RESPONSE_PLANNING.md`.
- `support/artifacts/pr_eg_r6_r2_r1/26_LEGACY_PATH_ISOLATION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/26_LEGACY_PATH_ISOLATION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/27_INTEGRITY_PRESERVATION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/27_INTEGRITY_PRESERVATION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/28_CONTROLLED_TESTS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/28_CONTROLLED_TESTS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/29_FROZEN_HOLDOUTS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/29_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/30_MATCHED_BASELINE_COMPARISON.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/30_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2_r1/31_FRESH_PROVIDER_CONVERSATIONS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/31_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/32_TURN_LEVEL_QUALIFICATION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/32_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/33_DIALOGUE_QUALITY_AND_PLAYABILITY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/33_DIALOGUE_QUALITY_AND_PLAYABILITY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/34_PERFORMANCE.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/34_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r2_r1/35_REGRESSION_COMPARISON.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/35_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r2_r1/36_ACCEPTANCE_GATES.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/36_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r2_r1/37_REMAINING_LIMITATIONS.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/37_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r2_r1/38_RECOMMENDED_NEXT_ACTION.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/38_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r2_r1/39_FINAL_VERDICT.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/39_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r2_r1/40_SOURCE_AND_EVIDENCE_INVENTORY.md`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/40_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r2_r1/acceptance_gates.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/acceptance_gates.json`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline/qualification_plan.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_head.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_head.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_junit.xml`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_sources/game/conversational_continuity.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_sources/game/semantic_correspondence.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_sources/game/semantic_correspondence.py`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_sources/game/unified_semantic_planning.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_sources/game/unified_semantic_planning.py`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_tests.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_tests_unrestricted.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_tests_unrestricted.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/baseline_unsandboxed_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/baseline_unsandboxed_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/controlled_junit.xml`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/controlled_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r1/controlled_matched_comparison.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/controlled_matched_comparison.json`.
- `support/artifacts/pr_eg_r6_r2_r1/controlled_tests.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/controlled_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/conversational_continuity_changes.diff`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/conversational_continuity_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r1/conversational_referents_changes.diff`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/conversational_referents_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r1/failure_reproduction.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/failure_reproduction.json`.
- `support/artifacts/pr_eg_r6_r2_r1/final/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/final/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/final/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/final/qualification_plan.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r1/final/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/final/starting_source_hashes.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r1/final_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/final_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/focus_tests.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/focus_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/freeze.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/freeze.json`.
- `support/artifacts/pr_eg_r6_r2_r1/frozen_holdouts.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6_r2_r1/holdout_results.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/holdout_results.json`.
- `support/artifacts/pr_eg_r6_r2_r1/integrity_results.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/integrity_results.json`.
- `support/artifacts/pr_eg_r6_r2_r1/performance.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/performance.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot/starting_source_hashes.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot/starting_source_hashes.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_console_2.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_console_2.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_console_3.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_console_3.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_console_4.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_console_4.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_console_5.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_console_5.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_1/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_1/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_2/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_2/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_2/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_3/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_contract_3/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_contract_3/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_schema_rejection/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_schema_rejection/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/pilot_schema_rejection/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/pilot_schema_rejection/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_status.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_status.json`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_turns.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/qualification_plan.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/qualification_plan.json`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/predecessor_holdouts_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/quality_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/quality_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/quality_metrics.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/quality_metrics.json`.
- `support/artifacts/pr_eg_r6_r2_r1/raw_examples.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/raw_examples.json`.
- `support/artifacts/pr_eg_r6_r2_r1/regression_comparison.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r2_r1/regression_junit.xml`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r2_r1/regression_tests.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/regression_tests.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/repository_status.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/repository_status.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/restart/result.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/restart/result.json`.
- `support/artifacts/pr_eg_r6_r2_r1/restart/semantic_traces.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/restart/semantic_traces.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/restart/usage.jsonl`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/restart/usage.jsonl`.
- `support/artifacts/pr_eg_r6_r2_r1/restart_console.txt`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/restart_console.txt`.
- `support/artifacts/pr_eg_r6_r2_r1/semantic_correspondence_changes.diff`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/semantic_correspondence_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r1/state_inventory.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/state_inventory.json`.
- `support/artifacts/pr_eg_r6_r2_r1/turn_scores.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/turn_scores.json`.
- `support/artifacts/pr_eg_r6_r2_r1/unified_semantic_planning_changes.diff`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/unified_semantic_planning_changes.diff`.
- `support/artifacts/pr_eg_r6_r2_r1/verdict.json`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `artifacts/pr_eg_r6_r2_r1/verdict.json`.
- `support/game/conversational_continuity.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/conversational_continuity.py`.
- `support/game/conversational_orchestration.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/conversational_orchestration.py`.
- `support/game/conversational_referents.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/conversational_referents.py`.
- `support/game/dialogue_authority.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/dialogue_authority.py`.
- `support/game/discourse_state.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/discourse_state.py`.
- `support/game/expressive_dialogue.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/expressive_dialogue.py`.
- `support/game/immutable_valid_response.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/immutable_valid_response.py`.
- `support/game/storage.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/storage.py`.
- `support/game/unified_semantic_planning.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/tests/test_pr_eg_r2c_r2_reference_eligibility.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r2c_r2_reference_eligibility.py`.
- `support/tests/test_pr_eg_r2c_speech_adoption.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/tests/test_pr_eg_r3_expressive_dialogue.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r3_expressive_dialogue.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tests/test_pr_eg_r4_r1_delivery_integrity.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r4_r1_delivery_integrity.py`.
- `support/tests/test_pr_eg_r6_r1_disclosure_boundary.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_disclosure_boundary.py`.
- `support/tests/test_pr_eg_r6_r1_r1_provenance.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r1_r1_provenance.py`.
- `support/tests/test_pr_eg_r6_r2_grounding.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_grounding.py`.
- `support/tests/test_pr_eg_r6_r2_r1_referents.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r6_r2_r1_referents.py`.
- `support/tests/test_pr_eg_r6_unified_semantic_planning.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_pr_eg_r6_unified_semantic_planning.py`.
- `support/tests/test_social_question_relevance_answer_selection.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tests/test_social_question_relevance_answer_selection.py`.
- `support/tools/assess_pr_eg_r6_r2_r1.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/assess_pr_eg_r6_r2_r1.py`.
- `support/tools/compare_pr_eg_r6_r2_r1.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/compare_pr_eg_r6_r2_r1.py`.
- `support/tools/probe_pr_eg_r6_r2_r1_restart.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/probe_pr_eg_r6_r2_r1_restart.py`.
- `support/tools/qualify_pr_eg_r6.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/qualify_pr_eg_r6.py`.
- `support/tools/qualify_pr_eg_r6_r2.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2.py`.
- `support/tools/qualify_pr_eg_r6_r2_r1.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/qualify_pr_eg_r6_r2_r1.py`.
- `support/tools/write_pr_eg_r6_r2_r1_review.py`: Durable referent source, preserved predecessor or qualification evidence. Canonical source: `tools/write_pr_eg_r6_r2_r1_review.py`.
- `support/artifacts/pr_eg_r6_r2_r1/evidence_inventory.json`: Hashed complete evidence list. Canonical source: `artifacts/pr_eg_r6_r2_r1/evidence_inventory.json`.

## Explicit omissions

- `artifacts/pr_eg_r6_r2_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r2_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r6_r2_r1/pilot_contract_1/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r1/pilot_contract_2/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r1/pilot_contract_3/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r1/pilot_schema_rejection/qualification_plan.json`: duplicate content of artifacts/pr_eg_r6_r2_r1/pilot/qualification_plan.json; canonical reference retained
- `artifacts/pr_eg_r6_r2_r1/predecessor_holdouts/starting_source_hashes.json`: duplicate content of artifacts/pr_eg_r6_r2_r1/final/starting_source_hashes.json; canonical reference retained
- `game/semantic_correspondence.py`: duplicate content of artifacts/pr_eg_r6_r2_r1/baseline_sources/game/semantic_correspondence.py; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
