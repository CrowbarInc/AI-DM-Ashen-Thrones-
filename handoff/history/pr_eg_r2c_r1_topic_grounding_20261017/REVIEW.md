# Campaign

Campaign: PR-EG-R2C-R1 — Conversational Topic Grounding & Authorized Recall
Identifier: `pr_eg_r2c_r1_topic_grounding_20261017`
Date: 2026-10-17
Generated: 2026-10-17T10:33:32.800730+00:00
Purpose: Focused implementation and qualification; stop after R2C-R1 and await external review.

# Executive Summary

**C — REPAIR INCOMPLETE.** Topic selection ranks relevant authorized authored topics after speaker and answer-sufficiency checks. Immediate repetition and subject-specific historical lookup use actual delivered speech. GM recall retains attribution. The existing R2C host-owned adoption and rejected-candidate exclusion remain in force.

Combined regression: {'passed': 550, 'failed': 26} before; {'passed': 584, 'failed': 25} after. No existing expectation was changed. Newly failing: []. R2C H6 now passes unchanged; the original 19 failures and 6 additional inherited owner-suite failures remain.

Final fresh-provider production /api/chat: 15 primary + 12 secondary turns, 2 failing turns. Relevance/authority/history/state checks: 25/27. 14 provider calls, 0 narration calls, 0 retries. Independent holdouts: 15/15, including four final-revision independent cases.

Qualification is bounded to these fictional scenes and the configured provider route. The existing delivered-history store is capped at 32 records; this is not unlimited campaign memory or arbitrary semantic understanding. Stop after PR-EG-R2C-R1; await external review before R3.

Objective status: `C — REPAIR INCOMPLETE`.

# Changes Made

## Production changes

- Repair existing topic selection, delivered-reference grounding and authorized recall in three modules; preserve R2C adoption.

## Validation changes

- T01–T28 and five additional controls; unchanged historical H6; independent frozen holdouts.

## Tooling changes

- Cycle-specific fresh HTTP runner and evidence/review builders.

## Documentation changes

- 22 required review reports.

## Generated artifacts

- Exact baseline/final identities, failed/final live transcripts, source hashes/diffs and state/performance audits.

# What Was Tested

- **Focused tests:** T01–T28 plus five additional controls pass; unchanged H6 passes.
- **Broader relevant tests:** {'passed': 550, 'failed': 26} → {'passed': 584, 'failed': 25}; zero new failures.
- **Full suite:** Not run; combined relevant family only.
- **Runtime validation:** Two final fresh production HTTP conversations (15 + 12 turns): primary fails turns 7/8; secondary passes. Relevance/authority audited.
- **Model/runtime boundary:** Configured gpt-4.1-mini; real interpretation provider, no live doubles or replay.
- **New regressions:** []
- **Pre-existing failures:** Not reported.
- **Self-contained bundle review:** 20 required reports, source snapshots/diffs/hashes, exact baseline/final failures, frozen H6 failure and complete 27-turn real-provider HTTP results; no active saves or credentials.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- External review of R2C-R1 closure readiness and all preserved failed transcripts.

# Known Problems / Unresolved Findings

## Campaign-specific

- Final primary direct guard question is blocked by upstream unresolved subject reference; its immediate follow-up lacks the requested disclosure. Repeated live failure triggers the stop condition.
- Bounded lexical subject matching, 32-row history cap, controlled multi-speaker qualification only.
- Initial D/F short probes passed; extended frozen-baseline reproduction executed later.

## Pre-existing baseline

- 25 combined-family inherited failures; exact identities in report 14.

# Missing Concepts / Future Capabilities

- Unlimited historical memory and arbitrary semantic paraphrase qualification are outside this cycle.

# What This Campaign Does NOT Prove

- All repository tests passing, arbitrary generated-speech safety, unlimited recall, process-restart persistence or R3 readiness.

# Recommended Next Step

Stop after PR-EG-R2C-R1: live qualification fails. Await external review of the upstream reference-eligibility blocker; do not proceed to R3.

# Review Bundle Contents

Bundle file count: `121`
Bundle ZIP size: `000007540814` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r2c_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r2c_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r2c_r1/02_BASELINE_AND_ENVIRONMENT.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r2c_r1/03_HISTORICAL_FAILURE_REPRODUCTION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/03_HISTORICAL_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r2c_r1/04_TOPIC_GROUNDING_ARCHITECTURE.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/04_TOPIC_GROUNDING_ARCHITECTURE.md`.
- `support/artifacts/pr_eg_r2c_r1/05_CONVERSATIONAL_REFERENCE_GROUNDING.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/05_CONVERSATIONAL_REFERENCE_GROUNDING.md`.
- `support/artifacts/pr_eg_r2c_r1/06_AUTHORIZED_INFORMATION_RETRIEVAL.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/06_AUTHORIZED_INFORMATION_RETRIEVAL.md`.
- `support/artifacts/pr_eg_r2c_r1/07_DELIVERED_HISTORY_RETRIEVAL.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/07_DELIVERED_HISTORY_RETRIEVAL.md`.
- `support/artifacts/pr_eg_r2c_r1/08_GM_RECALL.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/08_GM_RECALL.md`.
- `support/artifacts/pr_eg_r2c_r1/09_INFORMATION_INTEGRITY_PRESERVATION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/09_INFORMATION_INTEGRITY_PRESERVATION.md`.
- `support/artifacts/pr_eg_r2c_r1/10_PERSISTENCE_QUALIFICATION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/10_PERSISTENCE_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r2c_r1/11_SOURCE_CHANGE_INVENTORY.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/11_SOURCE_CHANGE_INVENTORY.md`.
- `support/artifacts/pr_eg_r2c_r1/12_TARGETED_TEST_RESULTS.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/12_TARGETED_TEST_RESULTS.md`.
- `support/artifacts/pr_eg_r2c_r1/13_FROZEN_HOLDOUTS.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/13_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r2c_r1/14_REGRESSION_COMPARISON.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/14_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r2c_r1/15_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/15_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r2c_r1/16_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/16_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r2c_r1/17_PROVIDER_PERFORMANCE.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/17_PROVIDER_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r2c_r1/18_STATE_INTEGRITY_AUDIT.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/18_STATE_INTEGRITY_AUDIT.md`.
- `support/artifacts/pr_eg_r2c_r1/19_REMAINING_LIMITATIONS.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/19_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r2c_r1/20_NEXT_CYCLE_RECOMMENDATION.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/20_NEXT_CYCLE_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r2c_r1/21_FINAL_VERDICT.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/21_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r2c_r1/acceptance_gates.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/acceptance_gates.json`.
- `support/artifacts/pr_eg_r2c_r1/active_data_historical_comparison.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/active_data_historical_comparison.json`.
- `support/artifacts/pr_eg_r2c_r1/after_reproduction.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/after_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r1/all_attempt_provider_cost.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/all_attempt_provider_cost.json`.
- `support/artifacts/pr_eg_r2c_r1/audit_evidence.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/audit_evidence.py`.
- `support/artifacts/pr_eg_r2c_r1/audit_session_state.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/audit_session_state.py`.
- `support/artifacts/pr_eg_r2c_r1/baseline.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/baseline.xml`.
- `support/artifacts/pr_eg_r2c_r1/baseline_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/baseline_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/before_reproduction.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/before_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r1/build_review.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/build_review.py`.
- `support/artifacts/pr_eg_r2c_r1/complete_final.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/complete_final.xml`.
- `support/artifacts/pr_eg_r2c_r1/complete_final_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/complete_final_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/environment.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/environment.json`.
- `support/artifacts/pr_eg_r2c_r1/evaluate_holdouts.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/evaluate_holdouts.py`.
- `support/artifacts/pr_eg_r2c_r1/extended_historical_reproduction.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/extended_historical_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r1/extended_reproduction.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/extended_reproduction.py`.
- `support/artifacts/pr_eg_r2c_r1/final.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final.xml`.
- `support/artifacts/pr_eg_r2c_r1/final_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/final_holdouts.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/final_holdouts_freeze.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_holdouts_freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/final_provider_usage.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_provider_usage.json`.
- `support/artifacts/pr_eg_r2c_r1/final_reproduction.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_reproduction.json`.
- `support/artifacts/pr_eg_r2c_r1/final_verified.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_verified.xml`.
- `support/artifacts/pr_eg_r2c_r1/final_verified_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/final_verified_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/freeze.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/frozen_holdouts.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/holdout_results.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/holdout_results.json`.
- `support/artifacts/pr_eg_r2c_r1/live_freeze.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/live_plan.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_plan.json`.
- `support/artifacts/pr_eg_r2c_r1/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r1/live_semantic_audit.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_semantic_audit.json`.
- `support/artifacts/pr_eg_r2c_r1/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_status.json`.
- `support/artifacts/pr_eg_r2c_r1/live_usage.jsonl`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r1/performance.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/performance.json`.
- `support/artifacts/pr_eg_r2c_r1/post.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/post.xml`.
- `support/artifacts/pr_eg_r2c_r1/post_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/post_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/qualification_final.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_final.xml`.
- `support/artifacts/pr_eg_r2c_r1/qualification_final_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_final_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/qualification_holdouts.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_holdouts.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_holdouts_freeze.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_holdouts_freeze.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_source_hashes.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r1/regression_comparison.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r2c_r1/reproduce.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/reproduce.py`.
- `support/artifacts/pr_eg_r2c_r1/run_baseline.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/run_baseline.py`.
- `support/artifacts/pr_eg_r2c_r1/run_supplementary.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/run_supplementary.py`.
- `support/artifacts/pr_eg_r2c_r1/session_state_audit.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/session_state_audit.json`.
- `support/artifacts/pr_eg_r2c_r1/source_changes.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/source_changes.json`.
- `support/artifacts/pr_eg_r2c_r1/state_audit.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/state_audit.json`.
- `support/artifacts/pr_eg_r2c_r1/supplementary_baseline.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/supplementary_baseline.xml`.
- `support/artifacts/pr_eg_r2c_r1/supplementary_baseline_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/supplementary_baseline_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/supplementary_comparison.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/supplementary_comparison.json`.
- `support/artifacts/pr_eg_r2c_r1/supplementary_final.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/supplementary_final.xml`.
- `support/artifacts/pr_eg_r2c_r1/supplementary_final_console.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/supplementary_final_console.txt`.
- `support/artifacts/pr_eg_r2c_r1/target.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/target.xml`.
- `support/artifacts/pr_eg_r2c_r1/target_final.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/target_final.xml`.
- `support/artifacts/pr_eg_r2c_r1/target_verified.xml`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/target_verified.xml`.
- `support/artifacts/pr_eg_r2c_r1/working_tree_before.txt`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/working_tree_before.txt`.
- `support/artifacts/pr_eg_r2c_r1/before_sources/game/conversational_continuity.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/before_sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r2c_r1/before_sources/game/dialogue_authority.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/before_sources/game/dialogue_authority.py`.
- `support/artifacts/pr_eg_r2c_r1/before_sources/game/social.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/before_sources/game/social.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/api.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/api.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/conversational_continuity.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/dialogue_authority.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/dialogue_authority.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/immutable_valid_response.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/immutable_valid_response.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/social.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/social.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/game/storage.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/game/storage.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/tests/test_pr_du_player_pipeline.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/tests/test_pr_du_player_pipeline.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/tests/test_pr_ef_gm_authority.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/tests/test_pr_ef_gm_authority.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/tests/test_pr_eg_r2c_speech_adoption.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/artifacts/pr_eg_r2c_r1/sources/tools/validate_pr_eg_r2c_r1.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/sources/tools/validate_pr_eg_r2c_r1.py`.
- `support/artifacts/pr_eg_r2c_r1/diffs/conversational_continuity.py.diff`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/diffs/conversational_continuity.py.diff`.
- `support/artifacts/pr_eg_r2c_r1/diffs/dialogue_authority.py.diff`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/diffs/dialogue_authority.py.diff`.
- `support/artifacts/pr_eg_r2c_r1/diffs/social.py.diff`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/diffs/social.py.diff`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_1/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_1/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_1/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_1/live_status.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_1/live_usage.jsonl`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_2/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_2/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_2/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_2/live_status.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_2/live_usage.jsonl`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_2/live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_semantic_audit.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_semantic_audit.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/live_status.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/performance.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/performance.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/qualification_source_hashes.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/qualification_source_hashes.json`.
- `support/artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/state_audit.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/state_audit.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_4/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_4/live_qualification.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_4/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_4/live_status.json`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_4/live_usage.jsonl`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_4/live_usage.jsonl`.
- `support/artifacts/pr_eg_r2c_r1/live_attempt_4/qualification_source_hashes.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/live_attempt_4/qualification_source_hashes.json`.
- `support/artifacts/pr_eg_r2c/frozen_holdouts.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r2c/freeze.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/freeze.json`.
- `support/artifacts/pr_eg_r2c/live_qualification.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/live_qualification.json`.
- `support/artifacts/pr_eg_r2c/live_status.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/live_status.json`.
- `support/artifacts/pr_eg_r2c/performance.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/performance.json`.
- `support/artifacts/pr_eg_r2c/regression_comparison.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/regression_comparison.json`.
- `support/artifacts/pr_eg_r2c/sources/tests/test_pr_eg_r2c_speech_adoption.py`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c/sources/tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/artifacts/pr_eg_r2c_r1/22_SOURCE_AND_EVIDENCE_INVENTORY.md`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/22_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r2c_r1/artifact_inventory.json`: R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit. Canonical source: `artifacts/pr_eg_r2c_r1/artifact_inventory.json`.

## Explicit omissions

- `artifacts/pr_eg_r2c_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r2c_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_1/live_freeze.json`: duplicate content of artifacts/pr_eg_r2c_r1/live_freeze.json; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_1/live_plan.json`: duplicate content of artifacts/pr_eg_r2c_r1/live_plan.json; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_2/live_freeze.json`: duplicate content of artifacts/pr_eg_r2c_r1/live_freeze.json; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_2/live_plan.json`: duplicate content of artifacts/pr_eg_r2c_r1/live_plan.json; canonical reference retained
- `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/final_verified.xml`: duplicate content of artifacts/pr_eg_r2c_r1/final_verified.xml; canonical reference retained
- `artifacts/pr_eg_r2c_r1/qualification_before_generic_compatibility_fix/final_verified_console.txt`: duplicate content of artifacts/pr_eg_r2c_r1/final_verified_console.txt; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_4/complete_final.xml`: duplicate content of artifacts/pr_eg_r2c_r1/complete_final.xml; canonical reference retained
- `artifacts/pr_eg_r2c_r1/live_attempt_4/complete_final_console.txt`: duplicate content of artifacts/pr_eg_r2c_r1/complete_final_console.txt; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
