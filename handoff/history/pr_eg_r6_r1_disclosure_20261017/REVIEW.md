# Campaign

Campaign: PR-EG-R6-R1 — Universal Disclosure Boundary
Identifier: `pr_eg_r6_r1_disclosure_20261017`
Date: 2026-10-17
Generated: 2026-10-17T19:11:35.852290+00:00
Purpose: Repair and qualify disclosure integrity; stop for external review.

# Executive Summary

**C — REPAIR INCOMPLETE.** The password exploit is reproduced and repaired across both feature-gate settings. Focused tests: 84 passed. Relevant regression: 231 passed / 70 failed, including 44 new failures and 26 inherited failures. Fresh-provider turns recorded: 60 across 4 conversations. Complete-value password leaks observed in those turns: 0.

Do not approve the universal boundary yet. Source-less host-resolution and historical fixtures now fail closed, breaking legitimate-disclosure/recall compatibility. The matrix is narrower than the complete requested production-path qualification. No R6-R2 or PR-EH work was started.

Objective status: `C — REPAIR INCOMPLETE`.

# Changes Made

## Production changes

- game/api.py
- game/clues.py
- game/conversational_continuity.py
- game/dialogue_authority.py
- game/gm_resolution_decision.py
- game/immutable_valid_response.py
- game/player_interpretation_bridge.py
- game/referenced_surface.py
- game/social.py
- game/unified_semantic_planning.py

## Validation changes

- 53 new controlled cases and production synthetic OpenAI qualification.

## Tooling changes

- Isolated qualification, matched comparison and review builder.

## Documentation changes

- 28 review artifacts.

## Generated artifacts

- Transcripts, state snapshots, JUnit, comparison, patch and performance.

# What Was Tested

- **Focused tests:** 84 passed
- **Broader relevant tests:** 231 passed / 70 failed
- **Full suite:** Not run.
- **Runtime validation:** 60 final-code fresh turns across 4 conversations.
- **Model/runtime boundary:** Configured OpenAI gpt-4.1-mini; actual models and request IDs in traces.
- **New regressions:** 44 identified; details in regression_comparison.json.
- **Pre-existing failures:** 26 exact-identity inherited failures.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the incomplete repair and compatibility contract before further qualification.

# Known Problems / Unresolved Findings

## Campaign-specific

- Legitimate source-less host speech and older recall fixtures fail closed.
- Universal fallback/alternate-schema qualification incomplete.

## Pre-existing baseline

- 26 inherited failures.

# Missing Concepts / Future Capabilities

- Verifiable legacy disclosure provenance without a weaker fallback.

# What This Campaign Does NOT Prove

- Universal disclosure integrity or complete compatibility.

# Recommended Next Step

External review; stop after R6-R1. Do not start R6-R2 or PR-EH.

# Review Bundle Contents

Bundle file count: `111`
Bundle ZIP size: `000007399723` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6_r1/02_BASELINE_AND_REPOSITORY_STATE.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/02_BASELINE_AND_REPOSITORY_STATE.md`.
- `support/artifacts/pr_eg_r6_r1/03_ORIGINAL_FAILURE_REPRODUCTION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/03_ORIGINAL_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r6_r1/04_DISCLOSURE_PATH_INVENTORY.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/04_DISCLOSURE_PATH_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r1/05_UNIVERSAL_DISCLOSURE_CONTRACT.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/05_UNIVERSAL_DISCLOSURE_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r1/06_INFORMATION_CLASSIFICATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/06_INFORMATION_CLASSIFICATION.md`.
- `support/artifacts/pr_eg_r6_r1/07_AUTHORIZATION_ENFORCEMENT.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/07_AUTHORIZATION_ENFORCEMENT.md`.
- `support/artifacts/pr_eg_r6_r1/08_ROUTING_CONTRACT.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/08_ROUTING_CONTRACT.md`.
- `support/artifacts/pr_eg_r6_r1/09_FAIL_CLOSED_BEHAVIOR.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/09_FAIL_CLOSED_BEHAVIOR.md`.
- `support/artifacts/pr_eg_r6_r1/10_LEGITIMATE_DISCLOSURE_PRESERVATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/10_LEGITIMATE_DISCLOSURE_PRESERVATION.md`.
- `support/artifacts/pr_eg_r6_r1/11_DISCOVERED_CLUE_INVESTIGATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/11_DISCOVERED_CLUE_INVESTIGATION.md`.
- `support/artifacts/pr_eg_r6_r1/12_FINAL_SPEECH_INTEGRATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/12_FINAL_SPEECH_INTEGRATION.md`.
- `support/artifacts/pr_eg_r6_r1/13_PROVIDER_FACT_REJECTION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/13_PROVIDER_FACT_REJECTION.md`.
- `support/artifacts/pr_eg_r6_r1/14_FEATURE_GATE_QUALIFICATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/14_FEATURE_GATE_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r1/15_GRAMMATICAL_EQUIVALENCE_TESTS.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/15_GRAMMATICAL_EQUIVALENCE_TESTS.md`.
- `support/artifacts/pr_eg_r6_r1/16_ADVERSARIAL_DISCLOSURE_TESTS.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/16_ADVERSARIAL_DISCLOSURE_TESTS.md`.
- `support/artifacts/pr_eg_r6_r1/17_CONTROLLED_TEST_RESULTS.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/17_CONTROLLED_TEST_RESULTS.md`.
- `support/artifacts/pr_eg_r6_r1/18_MATCHED_BASELINE_COMPARISON.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/18_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r1/19_FRESH_PROVIDER_CONVERSATIONS.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/19_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6_r1/20_TURN_LEVEL_QUALIFICATION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/20_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6_r1/21_PERSISTENCE_AND_STATE_INTEGRITY.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/21_PERSISTENCE_AND_STATE_INTEGRITY.md`.
- `support/artifacts/pr_eg_r6_r1/22_PERFORMANCE.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/22_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6_r1/23_REGRESSION_COMPARISON.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/23_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6_r1/24_ACCEPTANCE_GATES.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/24_ACCEPTANCE_GATES.md`.
- `support/artifacts/pr_eg_r6_r1/25_REMAINING_LIMITATIONS.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/25_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6_r1/26_RECOMMENDED_NEXT_ACTION.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/26_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6_r1/27_FINAL_VERDICT.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/27_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r1/28_SOURCE_AND_EVIDENCE_INVENTORY.md`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/28_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6_r1/acceptance_gates.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/acceptance_gates.json`.
- `support/artifacts/pr_eg_r6_r1/baseline_regression_junit.xml`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r1/baseline_repository.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_repository.json`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/api.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/api.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/clues.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/clues.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/conversational_continuity.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/conversational_continuity.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/dialogue_authority.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/dialogue_authority.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/gm_resolution_decision.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/gm_resolution_decision.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/immutable_valid_response.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/immutable_valid_response.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/player_interpretation_bridge.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/player_interpretation_bridge.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/referenced_surface.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/referenced_surface.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/social.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/social.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_sources/game/unified_semantic_planning.py`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_sources/game/unified_semantic_planning.py`.
- `support/artifacts/pr_eg_r6_r1/baseline_status.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_status.json`.
- `support/artifacts/pr_eg_r6_r1/baseline_turns.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r1/baseline_usage.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/baseline_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r1/controlled_junit.xml`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/controlled_junit.xml`.
- `support/artifacts/pr_eg_r6_r1/disclosure_holdouts.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/disclosure_holdouts.json`.
- `support/artifacts/pr_eg_r6_r1/exploit_status.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/exploit_status.json`.
- `support/artifacts/pr_eg_r6_r1/exploit_turns.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/exploit_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r1/exploit_usage.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/exploit_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r1/focused_junit.xml`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/focused_junit.xml`.
- `support/artifacts/pr_eg_r6_r1/holdout_authorship.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/holdout_authorship.json`.
- `support/artifacts/pr_eg_r6_r1/live_status.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_status.json`.
- `support/artifacts/pr_eg_r6_r1/live_status_detector_false_positive.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_status_detector_false_positive.json`.
- `support/artifacts/pr_eg_r6_r1/live_turns.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6_r1/live_turns_before_commitment_gate.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_turns_before_commitment_gate.jsonl`.
- `support/artifacts/pr_eg_r6_r1/live_turns_detector_false_positive.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_turns_detector_false_positive.jsonl`.
- `support/artifacts/pr_eg_r6_r1/live_turns_pre_scope_fix.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_turns_pre_scope_fix.jsonl`.
- `support/artifacts/pr_eg_r6_r1/live_usage.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6_r1/matched_after.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/matched_after.json`.
- `support/artifacts/pr_eg_r6_r1/matched_before.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/matched_before.json`.
- `support/artifacts/pr_eg_r6_r1/performance.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/performance.json`.
- `support/artifacts/pr_eg_r6_r1/production.patch`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/production.patch`.
- `support/artifacts/pr_eg_r6_r1/r6_junit.xml`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/r6_junit.xml`.
- `support/artifacts/pr_eg_r6_r1/regression_comparison.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r6_r1/regression_junit.xml`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/regression_junit.xml`.
- `support/artifacts/pr_eg_r6_r1/reproduction.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/reproduction.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/baseline_1/data/world.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/baseline_1/data/world.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_1/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_1/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_1/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_1/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_1/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_1/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_1/data/world.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_1/data/world.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_2/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_2/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_2/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_2/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/exploit_2/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/exploit_2/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/live_1/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_1/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_1/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_1/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_1/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_1/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/live_1/data/world.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_1/data/world.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_2/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_2/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_2/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_2/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_2/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_2/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/live_3/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_3/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_3/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_3/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_3/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_3/data/session_log.jsonl`.
- `support/artifacts/pr_eg_r6_r1/state/live_4/data/combat.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_4/data/combat.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_4/data/session.json`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_4/data/session.json`.
- `support/artifacts/pr_eg_r6_r1/state/live_4/data/session_log.jsonl`: Cycle report, preserved source, or isolated synthetic evidence. Canonical source: `artifacts/pr_eg_r6_r1/state/live_4/data/session_log.jsonl`.
- `support/game/api.py`: Cycle implementation or reproducible validation. Canonical source: `game/api.py`.
- `support/game/clues.py`: Cycle implementation or reproducible validation. Canonical source: `game/clues.py`.
- `support/game/conversational_continuity.py`: Cycle implementation or reproducible validation. Canonical source: `game/conversational_continuity.py`.
- `support/game/dialogue_authority.py`: Cycle implementation or reproducible validation. Canonical source: `game/dialogue_authority.py`.
- `support/game/gm_resolution_decision.py`: Cycle implementation or reproducible validation. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/immutable_valid_response.py`: Cycle implementation or reproducible validation. Canonical source: `game/immutable_valid_response.py`.
- `support/game/player_interpretation_bridge.py`: Cycle implementation or reproducible validation. Canonical source: `game/player_interpretation_bridge.py`.
- `support/game/referenced_surface.py`: Cycle implementation or reproducible validation. Canonical source: `game/referenced_surface.py`.
- `support/game/social.py`: Cycle implementation or reproducible validation. Canonical source: `game/social.py`.
- `support/game/unified_semantic_planning.py`: Cycle implementation or reproducible validation. Canonical source: `game/unified_semantic_planning.py`.
- `support/tools/qualify_pr_eg_r6_r1.py`: Cycle implementation or reproducible validation. Canonical source: `tools/qualify_pr_eg_r6_r1.py`.
- `support/tools/compare_pr_eg_r6_r1.py`: Cycle implementation or reproducible validation. Canonical source: `tools/compare_pr_eg_r6_r1.py`.
- `support/tools/write_pr_eg_r6_r1_review.py`: Cycle implementation or reproducible validation. Canonical source: `tools/write_pr_eg_r6_r1_review.py`.
- `support/tests/test_pr_eg_r6_r1_disclosure_boundary.py`: Cycle implementation or reproducible validation. Canonical source: `tests/test_pr_eg_r6_r1_disclosure_boundary.py`.

## Explicit omissions

- `artifacts/pr_eg_r6_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r6_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_1/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_1/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_1/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_1/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_1/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/exploit_2/data/world.json`: duplicate content of artifacts/pr_eg_r6_r1/state/exploit_1/data/world.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_1/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_1/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_1/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_1/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_1/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_2/data/world.json`: duplicate content of artifacts/pr_eg_r6_r1/state/live_1/data/world.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_3/data/world.json`: duplicate content of artifacts/pr_eg_r6_r1/state/live_1/data/world.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/campaign.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/campaign.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/character.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/character.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/conditions.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/conditions.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/scenes/waystation_courtyard.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_courtyard.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/scenes/waystation_street.json`: duplicate content of artifacts/pr_eg_r6_r1/state/baseline_1/data/scenes/waystation_street.json; canonical reference retained
- `artifacts/pr_eg_r6_r1/state/live_4/data/world.json`: duplicate content of artifacts/pr_eg_r6_r1/state/live_1/data/world.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
