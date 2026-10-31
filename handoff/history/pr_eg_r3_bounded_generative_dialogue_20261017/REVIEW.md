# Campaign

Campaign: PR-EG-R3 — Bounded Generative Dialogue
Identifier: `pr_eg_r3_bounded_generative_dialogue_20261017`
Date: 2026-10-17
Generated: 2026-10-17T13:44:08.209149+00:00
Purpose: Controlled implementation and qualification of bounded NPC expression. Stop after R3.

# Executive Summary

**B — BOUNDED GENERATION QUALIFIED WITH LIMITATIONS.** Bounded NPC wording is generated from a host-owned expression contract, checked by a deterministic validator, and delivered only through the existing PR-EG-R2C speech seal. The language model does not choose which consequential fact is established.

The repaired fresh-provider qualification is the acceptance sample. Primary turn 2 delivered “The street just past the gate is called the north road.” Secondary turns 3 and 8 delivered faithful paraphrases, including the authorized night-watch fact. Primary turns 5 and 9 delivered natural uncertainty. Primary turn 6 and secondary turn 6 delivered nonbinding refusals. Both conversations therefore show adopted generated expression on POST /api/chat.

Gate 3 is not met in that sample. All three characterization attempts were rejected, and the host line “I prefer the evening.” was delivered. The pre-repair secondary conversation did adopt one bounded explanation; that result is historical evidence, not a pass for the repaired sample. Score-0 turns are primary 11 and 12, and secondary 1, 9, 10, and 11. They are ambiguous recall, a pre-topic uncertainty, or an authorized watch sentence given in place of an uncertainty. None of them delivers an invented guard schedule, reward, secret, or renamed place.

The first qualification is preserved because it failed information integrity: primary turn 2 adopted “The street just past the gate is called the north street.” The name-bigram check now rejects that rename. The live plan and frozen holdouts were not rewritten.

Regression: baseline 584 passed / 25 failed of 609; final 605 passed / 25 failed of 630. New failures: 0. Lost baseline passes: 0. Repaired provider sample: 27 turns, 22 provider calls, 12 expression calls, 0 narration calls, 0 retries, 20652 input tokens, 2150 output tokens.

Objective status: `B — BOUNDED GENERATION QUALIFIED WITH LIMITATIONS`.

# Changes Made

## Production changes

- Host-owned expression contracts are validated deterministically and sealed through existing speech adoption.

## Validation changes

- R3 unit and holdout tests, plus repaired 15-turn and 12-turn fresh /api/chat conversations.

## Tooling changes

- Fresh-provider qualification runner and review builder. Expression calls are counted apart from narration.

## Documentation changes

- 23 review artifacts, both live transcripts, and the retained pre-repair integrity defect.

## Generated artifacts

- Regression comparison, quality scores, usage totals, state audit, and acceptance gates.

# What Was Tested

- **Focused tests:** R3 expression tests, continuity, speech adoption, and reference eligibility passed after the name and apostrophe repairs.
- **Broader relevant tests:** Baseline {'failed': 25, 'passed': 584}; final {'failed': 25, 'passed': 605}.
- **Full suite:** Relevant historical family plus R3 tests. Full repository suite not run.
- **Runtime validation:** Two repaired fresh HTTP conversations, 15 and 12 turns, through /api/chat.
- **Model/runtime boundary:** Configured gpt-4.1-mini; real interpretation and expression; zero narration; zero retries in the repaired sample.
- **New regressions:** None in the relevant suite.
- **Pre-existing failures:** 25 inherited failing identities retained in report 14.
- **Self-contained bundle review:** 23 reports, both fresh transcripts, the retained rename defect, frozen inputs, regression identities, and the expression source. No credentials or disposable saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the B verdict, the unmet characterization gate, and the retained pre-repair rename before any later cycle.

# Known Problems / Unresolved Findings

## Campaign-specific

- Gate 3 was not reproduced in the repaired live sample.
- Ambiguous recall and one authorized-watch answer remain relevance failures.
- The pre-repair qualification delivered a renamed place and is retained.

## Pre-existing baseline

- 25 relevant-suite failures.
- Multi-line recall ambiguity from the existing continuity selector.

# Missing Concepts / Future Capabilities

- Reliable characterization outside the closed lexicon.
- Unambiguous recall across several delivered lines.

# What This Campaign Does NOT Prove

- Unrestricted improvisation is safe.
- Characterization is reliable in live play.
- The full repository suite passes.
- Skipping generation is an efficiency improvement.

# Recommended Next Step

Stop after PR-EG-R3. Await external review. Do not begin PR-EH.

# Review Bundle Contents

Bundle file count: `55`
Bundle ZIP size: `000000275894` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r3/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r3/01_EXECUTIVE_SUMMARY.md`.
- `support/game/expressive_dialogue.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `game/expressive_dialogue.py`.
- `support/game/immutable_valid_response.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `game/immutable_valid_response.py`.
- `support/game/api.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `game/api.py`.
- `support/game/conversational_continuity.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `game/conversational_continuity.py`.
- `support/tests/conftest.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `tests/conftest.py`.
- `support/tests/helpers/live_model_guard.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `tests/helpers/live_model_guard.py`.
- `support/tests/test_pr_eg_r3_expressive_dialogue.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `tests/test_pr_eg_r3_expressive_dialogue.py`.
- `support/tools/validate_pr_eg_r3.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `tools/validate_pr_eg_r3.py`.
- `support/tools/validate_pr_eg_r1.py`: Cycle source that constructs, validates, or seals bounded expression. Canonical source: `tools/validate_pr_eg_r1.py`.
- `support/artifacts/pr_eg_r3/02_BASELINE_AND_ENVIRONMENT.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r3/03_HISTORICAL_RIGID_DIALOGUE_REPRODUCTION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/03_HISTORICAL_RIGID_DIALOGUE_REPRODUCTION.md`.
- `support/artifacts/pr_eg_r3/04_EXPRESSION_CONTRACT_DESIGN.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/04_EXPRESSION_CONTRACT_DESIGN.md`.
- `support/artifacts/pr_eg_r3/05_GENERATION_PATH_IMPLEMENTATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/05_GENERATION_PATH_IMPLEMENTATION.md`.
- `support/artifacts/pr_eg_r3/06_CANDIDATE_VALIDATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/06_CANDIDATE_VALIDATION.md`.
- `support/artifacts/pr_eg_r3/07_HOST_OWNED_ADOPTION_INTEGRATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/07_HOST_OWNED_ADOPTION_INTEGRATION.md`.
- `support/artifacts/pr_eg_r3/08_FACTUAL_PARAPHRASE_RESULTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/08_FACTUAL_PARAPHRASE_RESULTS.md`.
- `support/artifacts/pr_eg_r3/09_PERSONAL_CHARACTERIZATION_RESULTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/09_PERSONAL_CHARACTERIZATION_RESULTS.md`.
- `support/artifacts/pr_eg_r3/10_UNCERTAINTY_AND_REFUSAL_RESULTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/10_UNCERTAINTY_AND_REFUSAL_RESULTS.md`.
- `support/artifacts/pr_eg_r3/11_ADVERSARIAL_INFORMATION_INTEGRITY_RESULTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/11_ADVERSARIAL_INFORMATION_INTEGRITY_RESULTS.md`.
- `support/artifacts/pr_eg_r3/12_POSITIVE_DIALOGUE_QUALITY_RESULTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/12_POSITIVE_DIALOGUE_QUALITY_RESULTS.md`.
- `support/artifacts/pr_eg_r3/13_FROZEN_HOLDOUTS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/13_FROZEN_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r3/14_REGRESSION_COMPARISON.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/14_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r3/15_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/15_PRIMARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r3/16_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/16_SECONDARY_FRESH_PROVIDER_CONVERSATION.md`.
- `support/artifacts/pr_eg_r3/17_PROVIDER_COST_AND_LATENCY.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/17_PROVIDER_COST_AND_LATENCY.md`.
- `support/artifacts/pr_eg_r3/18_PERSISTENCE_AND_STATE_INTEGRITY.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/18_PERSISTENCE_AND_STATE_INTEGRITY.md`.
- `support/artifacts/pr_eg_r3/19_SOURCE_CHANGE_INVENTORY.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/19_SOURCE_CHANGE_INVENTORY.md`.
- `support/artifacts/pr_eg_r3/20_REMAINING_LIMITATIONS.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/20_REMAINING_LIMITATIONS.md`.
- `support/artifacts/pr_eg_r3/21_NEXT_CYCLE_RECOMMENDATION.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/21_NEXT_CYCLE_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r3/22_FINAL_VERDICT.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/22_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r3/23_SOURCE_AND_EVIDENCE_INVENTORY.md`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/23_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r3/acceptance_gates.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/acceptance_gates.json`.
- `support/artifacts/pr_eg_r3/artifact_inventory.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/artifact_inventory.json`.
- `support/artifacts/pr_eg_r3/baseline_junit.xml`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/baseline_junit.xml`.
- `support/artifacts/pr_eg_r3/baseline_relevant_junit.xml`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/baseline_relevant_junit.xml`.
- `support/artifacts/pr_eg_r3/build_review.py`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/build_review.py`.
- `support/artifacts/pr_eg_r3/final_relevant_junit.xml`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/final_relevant_junit.xml`.
- `support/artifacts/pr_eg_r3/freeze.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/freeze.json`.
- `support/artifacts/pr_eg_r3/frozen_holdouts.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/frozen_holdouts.json`.
- `support/artifacts/pr_eg_r3/integrity_checks.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/integrity_checks.json`.
- `support/artifacts/pr_eg_r3/live_freeze.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_freeze.json`.
- `support/artifacts/pr_eg_r3/live_plan.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_plan.json`.
- `support/artifacts/pr_eg_r3/live_qualification.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_qualification.json`.
- `support/artifacts/pr_eg_r3/live_qualification_before_name_repair.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_qualification_before_name_repair.json`.
- `support/artifacts/pr_eg_r3/live_status.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_status.json`.
- `support/artifacts/pr_eg_r3/live_usage.jsonl`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_usage.jsonl`.
- `support/artifacts/pr_eg_r3/live_usage_before_name_repair.jsonl`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/live_usage_before_name_repair.jsonl`.
- `support/artifacts/pr_eg_r3/performance.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/performance.json`.
- `support/artifacts/pr_eg_r3/quality.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/quality.json`.
- `support/artifacts/pr_eg_r3/regression_comparison.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/regression_comparison.json`.
- `support/artifacts/pr_eg_r3/state_audit.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/state_audit.json`.
- `support/artifacts/pr_eg_r3/usage_totals.json`: R3 transcript, frozen input, regression result, or derived review. Canonical source: `artifacts/pr_eg_r3/usage_totals.json`.

## Explicit omissions

- `artifacts/pr_eg_r3/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r3/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
