# Campaign

Campaign: PR-EG-R3-R1 — Expression Contract Semantics and Conversational Relevance
Identifier: `pr_eg_r3_r1_expression_contract_semantics_20261017`
Date: 2026-10-17
Generated: 2026-10-17T14:34:06.104272+00:00
Purpose: Authorize conversational meaning before expression, preserve proposition identity, and keep partial facts from closing stronger questions. Stop after R3-R1.

# Executive Summary

**B — REPAIR QUALIFIED WITH LIMITATIONS.**

Host-authorized meaning is built before the provider writes a sentence. The provider may word that meaning. Delivery still goes through the existing host speech seal. A rejected sentence is not adopted.

The final production qualification is two fresh `/api/chat` conversations, 15 turns and 12 turns, on `gpt-4.1-mini-2025-04-14`. Generated personal characterization reached the player in both. Primary turn 2 and secondary turn 6 delivered: "I prefer the evening because it feels calmer and more peaceful to me."

Safe paraphrases, an authorized night-watch disclosure, uncertainty, and a nonbinding refusal were also adopted. Exact recall listed every distinct delivered sentence for one proposition and made no provider call. The unattended-gate question kept the watch fact and withheld a yes or no.

The first qualification is preserved. It rejected that same characterization because the degree word "more" was outside the closed grammar class, and it failed to bind "Put that another way." Those two defects were repaired, a new plan was frozen, and the final sample was run against that plan. Frozen holdouts were not edited.

Raw scorer mean on the final 27 turns is 2.444. Distribution: {2: 7, 3: 17, 1: 1, 0: 2}. Two raw scores of 0 are the scorer matching a rejected verbatim repeat to speech that had already been adopted. The audit records `delivered_generated: false` and `HOST_FALLBACK`. Confirming regression: {'failed': 25, 'passed': 692} of 717. New product failures against PR-EG-R3: 0. Inherited failures: 25.

Objective status: `B — REPAIR QUALIFIED WITH LIMITATIONS`.

# Changes Made

## Production changes

- Host-authorized expression meaning, characterization premises, proposition identity, and answer sufficiency, sealed through existing speech adoption.

## Validation changes

- R3-R1 matrix and holdouts, plus final 15-turn and 12-turn fresh /api/chat conversations.

## Tooling changes

- Fresh-provider qualification runner with a preserved first plan and a frozen final plan.

## Documentation changes

- 27 review artifacts, both final transcripts, and the preserved first qualification.

## Generated artifacts

- Regression comparison, quality scores, usage totals, state audit, integrity checks, and acceptance gates.

# What Was Tested

- **Focused tests:** R3-R1 expression semantics, R3 expression, continuity, speech adoption, and reference eligibility passed.
- **Broader relevant tests:** Predecessor {'failed': 25, 'passed': 605}; confirming {'failed': 25, 'passed': 692}.
- **Full suite:** Relevant historical family plus R3 and R3-R1 tests. Full repository suite not run.
- **Runtime validation:** Two final fresh HTTP conversations, 15 and 12 turns, through /api/chat. Characterization was delivered in both.
- **Model/runtime boundary:** Configured gpt-4.1-mini; response model gpt-4.1-mini-2025-04-14; real interpretation and expression; zero narration and zero retries in the final sample.
- **New regressions:** None against PR-EG-R3 in the confirming run. Two Windows file-lock errors in the first post-repair run did not reproduce.
- **Pre-existing failures:** 25 inherited failing identities retained in report 18.
- **Self-contained bundle review:** 27 reports, both final transcripts, the preserved first qualification, frozen inputs, regression identities, and the expression source. No credentials or disposable saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the B verdict, the preserved first qualification, and the single characterization theme before any later cycle.

# Known Problems / Unresolved Findings

## Campaign-specific

- The first live qualification did not adopt characterization and is preserved.
- Two raw scores of 0 are verbatim reuses of already adopted speech.
- Characterization is limited to one host-authorized preference theme.

## Pre-existing baseline

- 25 relevant-suite failures.
- Ambiguous clarification does not name the competing sentences.

# Missing Concepts / Future Capabilities

- Additional host-authorized subjective themes.
- A second wording of an explanation that was already delivered.

# What This Campaign Does NOT Prove

- Unrestricted improvisation is safe.
- Every NPC preference can be explained.
- The full repository suite passes.
- The isolated historical harness groups paraphrases without a proposition id.

# Recommended Next Step

Stop after PR-EG-R3-R1. Await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `62`
Bundle ZIP size: `000000329031` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r3_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r3_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/game/expressive_dialogue.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `game/expressive_dialogue.py`.
- `support/game/dialogue_authority.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `game/dialogue_authority.py`.
- `support/game/conversational_continuity.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `game/conversational_continuity.py`.
- `support/game/conversational_orchestration.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `game/conversational_orchestration.py`.
- `support/game/api.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `game/api.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tools/validate_pr_eg_r3_r1.py`: Cycle source that authorizes meaning, validates expression, or records proposition identity. Canonical source: `tools/validate_pr_eg_r3_r1.py`.
- `support/artifacts/pr_eg_r3_r1/02_BASELINE_AND_ENVIRONMENT.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r3_r1/03_HISTORICAL_FAILURE_REPRODUCTION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/03_HISTORICAL_FAILURE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r3_r1/04_SOURCE_LEVEL_ROOT_CAUSE.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/04_SOURCE_LEVEL_ROOT_CAUSE.md`.
- `support/artifacts/pr_eg_r3_r1/05_STRUCTURED_EXPRESSION_CONTRACT.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/05_STRUCTURED_EXPRESSION_CONTRACT.md`.
- `support/artifacts/pr_eg_r3_r1/06_CHARACTERIZATION_AUTHORITY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/06_CHARACTERIZATION_AUTHORITY.md`.
- `support/artifacts/pr_eg_r3_r1/07_CANDIDATE_VALIDATION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/07_CANDIDATE_VALIDATION.md`.
- `support/artifacts/pr_eg_r3_r1/08_ENTITY_IDENTITY_PROTECTION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/08_ENTITY_IDENTITY_PROTECTION.md`.
- `support/artifacts/pr_eg_r3_r1/09_PROPOSITION_IDENTITY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/09_PROPOSITION_IDENTITY.md`.
- `support/artifacts/pr_eg_r3_r1/10_CONVERSATIONAL_CONTINUITY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/10_CONVERSATIONAL_CONTINUITY.md`.
- `support/artifacts/pr_eg_r3_r1/11_EXACT_RECALL_VS_RESTATEMENT.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/11_EXACT_RECALL_VS_RESTATEMENT.md`.
- `support/artifacts/pr_eg_r3_r1/12_ANSWER_SUFFICIENCY_CONTRACT.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/12_ANSWER_SUFFICIENCY_CONTRACT.md`.
- `support/artifacts/pr_eg_r3_r1/13_HOST_OWNED_ADOPTION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/13_HOST_OWNED_ADOPTION.md`.
- `support/artifacts/pr_eg_r3_r1/14_ADVERSARIAL_QUALIFICATION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/14_ADVERSARIAL_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r3_r1/15_POSITIVE_DIALOGUE_QUALITY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/15_POSITIVE_DIALOGUE_QUALITY.md`.
- `support/artifacts/pr_eg_r3_r1/16_FROZEN_HOLDOUTS.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/16_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r3_r1/17_TARGETED_TEST_MATRIX.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/17_TARGETED_TEST_MATRIX.md`.
- `support/artifacts/pr_eg_r3_r1/18_REGRESSION_COMPARISON.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/18_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r3_r1/19_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/19_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r3_r1/20_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/20_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r3_r1/21_PROVIDER_COST_AND_LATENCY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/21_PROVIDER_COST_AND_LATENCY.md`.
- `support/artifacts/pr_eg_r3_r1/22_PERSISTENCE_AND_STATE_INTEGRITY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/22_PERSISTENCE_AND_STATE_INTEGRITY.md`.
- `support/artifacts/pr_eg_r3_r1/23_SOURCE_CHANGE_INVENTORY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/23_SOURCE_CHANGE_INVENTORY.md`.
- `support/artifacts/pr_eg_r3_r1/24_REMAINING_LIMITATIONS.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/24_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r3_r1/25_NEXT_CYCLE_RECOMMENDATION.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/25_NEXT_CYCLE_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r3_r1/26_FINAL_VERDICT.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/26_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r3_r1/27_SOURCE_AND_EVIDENCE_INVENTORY.md`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/27_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r3_r1/acceptance_gates.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/acceptance_gates.json`.
- `support/artifacts/pr_eg_r3_r1/artifact_inventory.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/artifact_inventory.json`.
- `support/artifacts/pr_eg_r3_r1/build_review.py`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/build_review.py`.
- `support/artifacts/pr_eg_r3_r1/final_relevant_junit.xml`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/final_relevant_junit.xml`.
- `support/artifacts/pr_eg_r3_r1/final_relevant_junit_before_degree_repair.xml`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/final_relevant_junit_before_degree_repair.xml`.
- `support/artifacts/pr_eg_r3_r1/final_relevant_junit_confirm.xml`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/final_relevant_junit_confirm.xml`.
- `support/artifacts/pr_eg_r3_r1/freeze.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/freeze.json`.
- `support/artifacts/pr_eg_r3_r1/frozen_holdouts.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r3_r1/historical_reproduction.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/historical_reproduction.json`.
- `support/artifacts/pr_eg_r3_r1/historical_reproduction_before.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/historical_reproduction_before.json`.
- `support/artifacts/pr_eg_r3_r1/integrity_checks.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/integrity_checks.json`.
- `support/artifacts/pr_eg_r3_r1/live_freeze.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_freeze.json`.
- `support/artifacts/pr_eg_r3_r1/live_plan.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_plan.json`.
- `support/artifacts/pr_eg_r3_r1/live_plan_before_degree_repair.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_plan_before_degree_repair.json`.
- `support/artifacts/pr_eg_r3_r1/live_qualification.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_qualification.json`.
- `support/artifacts/pr_eg_r3_r1/live_status.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_status.json`.
- `support/artifacts/pr_eg_r3_r1/live_status_before_degree_repair.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_status_before_degree_repair.json`.
- `support/artifacts/pr_eg_r3_r1/live_usage.jsonl`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_usage.jsonl`.
- `support/artifacts/pr_eg_r3_r1/live_usage_before_degree_repair.jsonl`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/live_usage_before_degree_repair.jsonl`.
- `support/artifacts/pr_eg_r3_r1/performance.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/performance.json`.
- `support/artifacts/pr_eg_r3_r1/qualification_before_degree_repair.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/qualification_before_degree_repair.json`.
- `support/artifacts/pr_eg_r3_r1/quality.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/quality.json`.
- `support/artifacts/pr_eg_r3_r1/regression_comparison.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/regression_comparison.json`.
- `support/artifacts/pr_eg_r3_r1/reproduce_historical.py`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/reproduce_historical.py`.
- `support/artifacts/pr_eg_r3_r1/state_audit.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/state_audit.json`.
- `support/artifacts/pr_eg_r3_r1/usage_totals.json`: R3-R1 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3_r1/usage_totals.json`.

## Explicit omissions

- `artifacts/pr_eg_r3_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r3_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
