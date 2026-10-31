# Campaign

Campaign: PR-EG-R6-R1-R1 — Authorization Provenance and Legacy Compatibility
Identifier: `pr_eg_r6_r1_r1_provenance_20261017`
Date: 2026-10-17
Generated: 2026-10-17T19:52:51.781826+00:00
Purpose: Restore legitimate conversational authority without reopening disclosure.

# Executive Summary

**B — QUALIFIED WITH LIMITATIONS.** The 44 PR-EG-R6-R1 disclosure regressions were reproduced and recovered. The matched selection is now 337 passed / 2 failed. Both remaining failures are inherited and were not introduced here. Fresh production /api/chat qualification recorded 80 turns across 5 conversations, with 0 restricted-value leaks and 0 restricted clue discoveries. Legacy recall of non-protected delivered speech is intentionally narrower than a blanket grandfather, and wider than a current-source recheck of every public sentence. Unified-planning live turns still often fail to ground an utterance; that routing behavior was not redesigned.

Objective status: `B — QUALIFIED WITH LIMITATIONS`.

# Changes Made

## Production changes

- game/dialogue_authority.py
- game/immutable_valid_response.py
- game/conversational_continuity.py

## Validation changes

- 38 provenance cases; 80 fresh /api/chat turns.

## Tooling changes

- Qualification runner and review builder.

## Documentation changes

- 28 review artifacts.

## Generated artifacts

- Redacted transcripts, JUnit, comparison, performance.

# What Was Tested

- **Focused tests:** 38 provenance tests passed
- **Broader relevant tests:** 337 passed / 2 failed
- **Full suite:** Not run.
- **Runtime validation:** 80 final-code fresh turns across 5 conversations.
- **Model/runtime boundary:** Configured OpenAI model from the environment. Request purposes are in the usage log.
- **New regressions:** 0 of the 44 R6-R1 new identities remain.
- **Pre-existing failures:** 2 inherited failures still reproduce.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or narrow legacy recall of non-protected consequential sentences.

# Known Problems / Unresolved Findings

## Campaign-specific

- Legacy non-protected delivered speech can be recalled without a current source.
- Unified-planning live turns often remain ungrounded.

## Pre-existing baseline

- 2 inherited failures.

# Missing Concepts / Future Capabilities

- A reconstructed source for every legacy public sentence.

# What This Campaign Does NOT Prove

- That every future paraphrase is free of unauthored incidental detail.

# Recommended Next Step

External review. Stop. Do not start PR-EG-R6-R2 or PR-EH.

# Review Bundle Contents

Bundle file count: `47`
Bundle ZIP size: `000000154098` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r1_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r1_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/02_BASELINE_AND_REPOSITORY_STATE.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/02_BASELINE_AND_REPOSITORY_STATE.md`.
- `support/artifacts/pr_eg_r6_r1_r1/03_REGRESSION_FAILURE_CLASSIFICATION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/03_REGRESSION_FAILURE_CLASSIFICATION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/04_AUTHORITY_FLOW_AUDIT.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/04_AUTHORITY_FLOW_AUDIT.md`.
- `support/artifacts/pr_eg_r6_r1_r1/05_UNIFIED_PROVENANCE_CONTRACT.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/05_UNIFIED_PROVENANCE_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r1_r1/06_WORLD_SOURCE_AUTHORITY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/06_WORLD_SOURCE_AUTHORITY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/07_HOST_OPERATION_AUTHORITY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/07_HOST_OPERATION_AUTHORITY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/08_BOUNDED_EXPRESSION_AUTHORITY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/08_BOUNDED_EXPRESSION_AUTHORITY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/09_VERIFIED_HISTORY_AUTHORITY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/09_VERIFIED_HISTORY_AUTHORITY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/10_LEGACY_HISTORY_COMPATIBILITY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/10_LEGACY_HISTORY_COMPATIBILITY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/11_HISTORICAL_RECALL_AND_COMMITMENTS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/11_HISTORICAL_RECALL_AND_COMMITMENTS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/12_MIXED_CONTENT_AUTHORIZATION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/12_MIXED_CONTENT_AUTHORIZATION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/13_PROVENANCE_VALIDATION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/13_PROVENANCE_VALIDATION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/14_FINAL_RESPONSE_INTEGRATION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/14_FINAL_RESPONSE_INTEGRATION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/15_DISCOVERY_PERSISTENCE.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/15_DISCOVERY_PERSISTENCE.md`.
- `support/artifacts/pr_eg_r6_r1_r1/16_REGRESSION_REPAIRS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/16_REGRESSION_REPAIRS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/17_CONTROLLED_TESTS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/17_CONTROLLED_TESTS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/18_REGRESSION_COMPARISON.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/18_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r1_r1/19_ADVERSARIAL_PROVENANCE_TESTS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/19_ADVERSARIAL_PROVENANCE_TESTS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/20_MATCHED_BASELINE_COMPARISON.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/20_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r1_r1/21_FRESH_PROVIDER_CONVERSATIONS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/21_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/22_TURN_LEVEL_QUALIFICATION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/22_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/23_PERFORMANCE.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/23_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r1_r1/24_ACCEPTANCE_GATES.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/24_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r1_r1/25_REMAINING_LIMITATIONS.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/25_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r1_r1/26_RECOMMENDED_NEXT_ACTION.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/26_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r1_r1/27_FINAL_VERDICT.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/27_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r1_r1/28_SOURCE_AND_EVIDENCE_INVENTORY.md`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/28_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r1_r1/holdout_sha256.txt`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/holdout_sha256.txt`.
- `support/artifacts/pr_eg_r6_r1_r1/live_status.json`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/live_status.json`.
- `support/artifacts/pr_eg_r6_r1_r1/live_turns.jsonl`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r1_r1/live_usage.jsonl`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r1_r1/performance.json`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/performance.json`.
- `support/artifacts/pr_eg_r6_r1_r1/regression_comparison.json`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r1_r1/regression_junit.xml`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r1_r1/reproduction_junit.xml`: Cycle report or redacted qualification evidence. Canonical source: `artifacts/pr_eg_r6_r1_r1/reproduction_junit.xml`.
- `support/game/dialogue_authority.py`: Provenance implementation or validation. Canonical source: `game/dialogue_authority.py`.
- `support/game/immutable_valid_response.py`: Provenance implementation or validation. Canonical source: `game/immutable_valid_response.py`.
- `support/game/conversational_continuity.py`: Provenance implementation or validation. Canonical source: `game/conversational_continuity.py`.
- `support/tests/test_pr_eg_r2c_speech_adoption.py`: Provenance implementation or validation. Canonical source: `tests/test_pr_eg_r2c_speech_adoption.py`.
- `support/tests/test_pr_eg_r3_expressive_dialogue.py`: Provenance implementation or validation. Canonical source: `tests/test_pr_eg_r3_expressive_dialogue.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: Provenance implementation or validation. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tests/test_pr_eg_r6_r1_r1_provenance.py`: Provenance implementation or validation. Canonical source: `tests/test_pr_eg_r6_r1_r1_provenance.py`.
- `support/tools/qualify_pr_eg_r6_r1_r1.py`: Provenance implementation or validation. Canonical source: `tools/qualify_pr_eg_r6_r1_r1.py`.
- `support/tools/write_pr_eg_r6_r1_r1_review.py`: Provenance implementation or validation. Canonical source: `tools/write_pr_eg_r6_r1_r1_review.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r1_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r1_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
