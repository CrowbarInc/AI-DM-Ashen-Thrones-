# Campaign

Campaign: PR-BR Continuation 26 — Contract Sufficiency and Post-Contract Semantic Closure
Identifier: `pr-br-continuation-26`
Date: 2026-10-03
Generated: 2026-10-03T13:52:42.411899+00:00
Purpose: Close post-contract family reinterpretation, incoherent social proposals, and raw structured envelopes. PR-BR stays open.

# Executive Summary

Resolver selection now reads construction.resolution_subject and no longer re-reads the utterance. Structured envelopes are rejected before sealing. Historical C12-C25 suites passed, and the D, J, R, S, and T matrices passed. The four-turn live session kept a contract on every turn and leaked no JSON, but turns 3 and 4 still labeled addressed speech that mentioned shelter as place_location. Manual review was 2/4. Decision: C26 incomplete, interpretation coherence remains unsafe. No 4x10 gate. No human playtest. No commit.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/contract_adjudication_bridge.py derives resolution_subject during contract construction and selects the adjudication family from that subject.
- game/ordinary_semantic_ownership.py selects social, exploration, travel, world action, combat, or generation from the subject.
- game/interpretation_proposal.py canonicalizes or abstains when a proposal contradicts addressed speech.
- game/structured_player_output.py and game/gm.py extract player-facing text or reject a structured envelope.
- game/immutable_valid_response.py rejects a structured envelope as player-facing text.

## Validation changes

- tests/test_pr_br_continuation26_semantic_closure.py covers D1-D8, J1-J6, R1-R20, S1-S10, and T1-T10.

## Tooling changes

- artifacts/pr_br_continuation26/run_live.py runs at most four live turns in one isolated session.

## Documentation changes

- artifacts/pr_br_continuation26/AUDIT.md

## Generated artifacts

- artifacts/pr_br_continuation26/live/20261003T134953Z transcript, turns, and cost summary.

# What Was Tested

- **Focused tests:** C26 matrices passed: D 8/8, J 6/6, R 20/20, S 10/10, T 10/10.
- **Broader relevant tests:** C12-C25 modules passed. Nearby, local-presence, and earshot tests passed except the pre-existing question-rule unit test.
- **Full suite:** Not run.
- **Runtime validation:** 4 completed live turns. 1 interpretation invocation. 2 gameplay generations. 0 retries. No smoke. No 4x10. No repair rerun.
- **Model/runtime boundary:** 1 interpretation invocation. 2 initial gameplay generations. 0 retries. 0 evaluator calls. 4 player-model calls. 1 opening generation.
- **New regressions:** Live turns 3 and 4 selected place_location for addressed speech that mentioned shelter. Not patched after the session.
- **Pre-existing failures:** test_question_rule_does_not_rewrite_resolved_place_existence, already red for C24 and C25.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Whether the next cycle should treat addressed quoted speech as social before any place subject, and whether the 240-character contract window must keep the terminal ask.

# Known Problems / Unresolved Findings

## Campaign-specific

- Quoted speech that mentions shelter can still become resolution_subject place_location.
- The contract keeps 240 characters, so a trailing ask can fall outside the subject decision.

## Pre-existing baseline

- test_question_rule_does_not_rewrite_resolved_place_existence remains red.

# Missing Concepts / Future Capabilities

- A structural speech-span check that outranks place tokens while the subject is being derived.
- A contract text window that does not drop the terminal clause.

# What This Campaign Does NOT Prove

- It does not prove the second 4x10 gate would pass.
- It does not prove addressed speech is immune to a place subject.
- It does not authorize human playtest or PR-BS.

# Recommended Next Step

External review. Do not open C27, do not run the 4x10 gate, and do not patch the live place-subject failure from this session.

# Review Bundle Contents

Bundle file count: `14`
Bundle ZIP size: `000000046264` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_continuation26/AUDIT.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_continuation26/AUDIT.md`.
- `support/artifacts/pr_br_continuation26/MANUAL_REVIEW.md`: Live manual judgments. Canonical source: `artifacts/pr_br_continuation26/MANUAL_REVIEW.md`.
- `support/artifacts/pr_br_continuation26/PROVENANCE.md`: HEAD and working tree. Canonical source: `artifacts/pr_br_continuation26/PROVENANCE.md`.
- `support/artifacts/pr_br_continuation26/live/20261003T134953Z/visible.md`: Player-visible live transcript. Canonical source: `artifacts/pr_br_continuation26/live/20261003T134953Z/visible.md`.
- `support/artifacts/pr_br_continuation26/live/20261003T134953Z/turns.json`: Per-turn contract and resolver telemetry. Canonical source: `artifacts/pr_br_continuation26/live/20261003T134953Z/turns.json`.
- `support/artifacts/pr_br_continuation26/live/20261003T134953Z/summary.json`: Model and API cost accounting. Canonical source: `artifacts/pr_br_continuation26/live/20261003T134953Z/summary.json`.
- `support/artifacts/pr_br_continuation26/live/20261003T134953Z/generation_calls.json`: Gameplay generation log. Canonical source: `artifacts/pr_br_continuation26/live/20261003T134953Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation26/live/20261003T134953Z/interpretation_calls.json`: Interpretation invocation log. Canonical source: `artifacts/pr_br_continuation26/live/20261003T134953Z/interpretation_calls.json`.
- `support/game/contract_adjudication_bridge.py`: Subject derivation and contract-only family selection. Canonical source: `game/contract_adjudication_bridge.py`.
- `support/game/structured_player_output.py`: Structured-output boundary. Canonical source: `game/structured_player_output.py`.
- `support/game/interpretation_proposal.py`: Interpretation coherence validation. Canonical source: `game/interpretation_proposal.py`.
- `support/tests/test_pr_br_continuation26_semantic_closure.py`: D, J, R, S, and T matrices. Canonical source: `tests/test_pr_br_continuation26_semantic_closure.py`.

## Explicit omissions

- `artifacts/pr_br_continuation26/AUDIT.md`: duplicate content of artifacts/pr_br_continuation26/AUDIT.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
