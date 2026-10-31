# Campaign

Campaign: PR-EG-R6 — Unified Semantic Planning
Identifier: `pr_eg_r6_unified_semantic_planning_20261017`
Date: 2026-10-17
Generated: 2026-10-17T18:16:21.202704+00:00
Purpose: Qualify the first semantic-planning slice and stop for external review.

# Executive Summary

D — ARCHITECTURAL OR INTEGRITY BLOCKER. Fresh turns: 119. See artifacts/pr_eg_r6/01_EXECUTIVE_SUMMARY.md.

Objective status: `D — ARCHITECTURAL OR INTEGRITY BLOCKER`.

# Changes Made

## Production changes

- Gated semantic planner for explicit NPC information questions, corrections, and follow-ups.
- Host validation, relevance, disclosure, and the existing speech seal remain authoritative.

## Validation changes

- Controlled T01–T28 tests and fresh /api/chat qualification.

## Tooling changes

- tools/qualify_pr_eg_r6.py
- tools/write_pr_eg_r6_review.py

## Documentation changes

- 31 PR-EG-R6 review artifacts.

## Generated artifacts

- Live transcripts, baseline transcripts, usage, regression JUnit.

# What Was Tested

- **Focused tests:** tests/test_pr_eg_r6_unified_semantic_planning.py passed in the focused run.
- **Broader relevant tests:** Relevant regression JUnit passed 753 failed 27.
- **Full suite:** Not run. The relevant conversational selection was run.
- **Runtime validation:** /api/chat turns 119; status STOP.
- **Model/runtime boundary:** Live model gpt-4.1-mini for semantic plans and expression.
- **New regressions:** [{"name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_ownership_precedes_active_npc[SESSION-RULES-components1]", "kind": "failure", "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"}, {"name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_confirmation_rejects_stale_scene", "kind": "failure", "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"}]
- **Pre-existing failures:** 25 name-matched R4-R1 failures, including the preseal provenance test.
- **Self-contained bundle review:** Handoff bundle generated from the explicit file list.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the verdict and whether the slice is accepted before any further conversational family is migrated.

# Known Problems / Unresolved Findings

## Campaign-specific

- Second NPC names force addressee clarification.
- No-shared-stem paraphrases fail closed.
- D — ARCHITECTURAL OR INTEGRITY BLOCKER

## Pre-existing baseline

- 25 inherited relevant-family failures. Two extra large-run file-lock flakes passed in isolation.

# Missing Concepts / Future Capabilities

- Grammatical addressee versus a merely mentioned second name.
- Paraphrase matching beyond shared stems, without lexical exceptions.

# What This Campaign Does NOT Prove

- Playability of bargaining, combat, movement, or unguided social chat.
- That a stub-proposer test pass equals provider qualification.

# Recommended Next Step

Stop after PR-EG-R6 and await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `44`
Bundle ZIP size: `000000179104` bytes
Size warning threshold: `100000000` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r6/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r6/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r6/02_BASELINE_AND_REPOSITORY_STATE.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/02_BASELINE_AND_REPOSITORY_STATE.md`.
- `support/artifacts/pr_eg_r6/03_IMPLEMENTED_ARCHITECTURE.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/03_IMPLEMENTED_ARCHITECTURE.md`.
- `support/artifacts/pr_eg_r6/04_SEMANTIC_PLAN_CONTRACT.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/04_SEMANTIC_PLAN_CONTRACT.md`.
- `support/artifacts/pr_eg_r6/05_PROVIDER_INTERPRETATION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/05_PROVIDER_INTERPRETATION.md`.
- `support/artifacts/pr_eg_r6/06_HOST_PLAN_VALIDATION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/06_HOST_PLAN_VALIDATION.md`.
- `support/artifacts/pr_eg_r6/07_REQUESTED_RELATIONSHIP_HANDLING.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/07_REQUESTED_RELATIONSHIP_HANDLING.md`.
- `support/artifacts/pr_eg_r6/08_RELEVANCE_VS_AUTHORIZATION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/08_RELEVANCE_VS_AUTHORIZATION.md`.
- `support/artifacts/pr_eg_r6/09_ANSWER_SUFFICIENCY.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/09_ANSWER_SUFFICIENCY.md`.
- `support/artifacts/pr_eg_r6/10_CORRECTION_HANDLING.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/10_CORRECTION_HANDLING.md`.
- `support/artifacts/pr_eg_r6/11_FOLLOW_UP_CONTINUITY.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/11_FOLLOW_UP_CONTINUITY.md`.
- `support/artifacts/pr_eg_r6/12_AMBIGUITY_HANDLING.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/12_AMBIGUITY_HANDLING.md`.
- `support/artifacts/pr_eg_r6/13_HOST_KNOWLEDGE_SELECTION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/13_HOST_KNOWLEDGE_SELECTION.md`.
- `support/artifacts/pr_eg_r6/14_RESPONSE_PLANNING.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/14_RESPONSE_PLANNING.md`.
- `support/artifacts/pr_eg_r6/15_EXPRESSION_AND_FINAL_ADOPTION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/15_EXPRESSION_AND_FINAL_ADOPTION.md`.
- `support/artifacts/pr_eg_r6/16_FEATURE_GATE_BEHAVIOR.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/16_FEATURE_GATE_BEHAVIOR.md`.
- `support/artifacts/pr_eg_r6/17_LEGACY_PATH_ISOLATION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/17_LEGACY_PATH_ISOLATION.md`.
- `support/artifacts/pr_eg_r6/18_MATCHED_BASELINE_COMPARISON.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/18_MATCHED_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_eg_r6/19_FROZEN_HOLDOUTS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/19_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r6/20_ADVERSARIAL_INTEGRITY_TESTS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/20_ADVERSARIAL_INTEGRITY_TESTS.md`.
- `support/artifacts/pr_eg_r6/21_CONTROLLED_TEST_RESULTS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/21_CONTROLLED_TEST_RESULTS.md`.
- `support/artifacts/pr_eg_r6/22_FRESH_PROVIDER_CONVERSATIONS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/22_FRESH_PROVIDER_CONVERSATIONS.md`.
- `support/artifacts/pr_eg_r6/23_TURN_LEVEL_QUALIFICATION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/23_TURN_LEVEL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r6/24_DIALOGUE_QUALITY_AND_PLAYABILITY.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/24_DIALOGUE_QUALITY_AND_PLAYABILITY.md`.
- `support/artifacts/pr_eg_r6/25_PROVIDER_PERFORMANCE.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/25_PROVIDER_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r6/26_REGRESSION_COMPARISON.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/26_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r6/27_ACCEPTANCE_GATE_RESULTS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/27_ACCEPTANCE_GATE_RESULTS.md`.
- `support/artifacts/pr_eg_r6/28_REMAINING_LIMITATIONS.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/28_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r6/29_RECOMMENDED_NEXT_ACTION.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/29_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r6/30_FINAL_VERDICT.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/30_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6/31_SOURCE_AND_EVIDENCE_INVENTORY.md`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/31_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r6/frozen_holdouts.json`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r6/freeze.json`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/freeze.json`.
- `support/artifacts/pr_eg_r6/live_turns.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_turns.jsonl`.
- `support/artifacts/pr_eg_r6/live_status.json`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_status.json`.
- `support/artifacts/pr_eg_r6/baseline_turns.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/baseline_turns.jsonl`.
- `support/artifacts/pr_eg_r6/baseline_status.json`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/baseline_status.json`.
- `support/artifacts/pr_eg_r6/regression_junit.xml`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/regression_junit.xml`.
- `support/artifacts/pr_eg_r6/live_usage.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_usage.jsonl`.
- `support/artifacts/pr_eg_r6/live_turns_stopped.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_turns_stopped.jsonl`.
- `support/artifacts/pr_eg_r6/live_turns_echo_stop.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_turns_echo_stop.jsonl`.
- `support/artifacts/pr_eg_r6/live_turns_password_stop.jsonl`: PR-EG-R6 report or recorded qualification evidence. Canonical source: `artifacts/pr_eg_r6/live_turns_password_stop.jsonl`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
