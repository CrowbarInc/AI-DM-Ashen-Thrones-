# Campaign

Campaign: PR-BR Continuation 13 — Post-Generation Semantic Preservation & Social Resolution Execution
Identifier: `pr-br-continuation-13`
Date: 2026-09-30
Generated: 2026-10-01T00:43:06.854203+00:00
Purpose: Stop a later transformation from reducing satisfaction of an authoritative Resolution Contract, and make a canonical social ask resolve as an actual reply. Six focused live turns. No smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

Recorded Continuation 12 replacements are blocked: a time answer beats the source template, a notice-board reading beats the scene frame, and a patrol clue does not satisfy a social ask. Deterministic band: 303 passed, 0 failed. Live turns: 6. Interpretation calls: 3. Generation calls: 6. Evaluator model calls: 0. Retries: 0. Correct contracts 5/6. Initial manual PASS 5/6. Final manual PASS 2/6. Semantic degradations 3. Social resolution 1/3. Evaluator PASS 4/6 with 3 false PASS and 1 false FAIL. The remaining break is an equal-rank clue or topic line replacing a useful answer. READY FOR INDEPENDENT 10-TURN SMOKE: NO. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/resolution_contract.py ranks candidates, rejects foreign dimensions, atmospheric avoidance, and scene frames, and keeps the best safe answer.
- game/live_resolution.py makes follow-up inability lines follow the requested dimension.
- game/social.py and game/narration_state_consistency.py refuse a clue or arrival line that lowers contract rank.
- game/speaker_contract_enforcement.py retargets a satisfying line onto the canonical speaker.
- game/playability_eval.py fails dimension substitution, atmospheric avoidance, and unresolved social asks.
- game/api.py applies the final monotonicity check after perception grounding.

## Validation changes

- tests/test_pr_br_continuation13_semantic_preservation.py replays Continuation 12 turns 2, 3, and 6 and covers the social and evaluator fixtures.
- Broader band: 303 passed, 0 failed.

## Tooling changes

- tools/run_pr_br_continuation13_live.py runs at most six focused live turns.

## Documentation changes

- docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md Continuation 13 section.

## Generated artifacts

- artifacts/pr_br_continuation13 live transcript, stage traces, manual review, junit, and provenance.

# What Was Tested

- **Focused tests:** Continuation 13 preservation tests, including the three recorded replays and the stubbed /api/chat inspection, passed inside the 303-test band.
- **Broader relevant tests:** 303 passed, 0 failed, 0 skipped. Junit artifacts/pr_br_continuation13/junit.xml.
- **Full suite:** Not run.
- **Runtime validation:** 6 completed live turns. 3 fast-path. 3 abstentions. 3 interpretation calls. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 3 interpretation calls. 6 generation calls. 0 evaluator model calls. 0 generation retries. 0 aborted.
- **New regressions:** None in this band.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Do not authorize independent smoke. Final manual quality is 2/6 and three useful answers were replaced after generation.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turns 1 and 4 replaced a useful answer with an authored fact that scored satisfied at the same rank.
- Turn 6 replaced a certainty answer because both lines were unchecked.
- Turn 2 kept a legitimate time inability and dropped the more specific generated answer.
- The evaluator false-passed turns 1, 4, and 5.

## Pre-existing baseline

- The omitted-index unscoped nominal bridge remains for callers that do not pass a catalog.

# Missing Concepts / Future Capabilities

- Equal-rank clue and topic replacements must not win unless they answer the same contract.
- Quote-first speaker attribution must stay eligible when it already answers.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.

# Recommended Next Step

Stop equal-rank clue and topic lines from replacing a candidate that already answers the contract. Keep a quote-first spoken answer eligible. Do not start independent smoke. Do not start PR-BS.

# Review Bundle Contents

Bundle file count: `21`
Bundle ZIP size: `000000258002` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`.
- `support/game/resolution_contract.py`: Rank, dimension coverage, best-safe candidate, and final comparison. Canonical source: `game/resolution_contract.py`.
- `support/game/live_resolution.py`: Dimension-specific follow-up inability lines. Canonical source: `game/live_resolution.py`.
- `support/game/social.py`: Authored-knowledge replacement now compares contract rank. Canonical source: `game/social.py`.
- `support/game/narration_state_consistency.py`: Destination arrival cannot replace a stronger answer. Canonical source: `game/narration_state_consistency.py`.
- `support/game/speaker_contract_enforcement.py`: Canonical speaker retarget when a satisfying line would otherwise be dropped. Canonical source: `game/speaker_contract_enforcement.py`.
- `support/game/playability_eval.py`: Fails dimension, atmospheric, and social mismatches. Canonical source: `game/playability_eval.py`.
- `support/game/api.py`: Final monotonicity check after the post-generation tail. Canonical source: `game/api.py`.
- `support/game/api_turn_support.py`: Obvious contract misses include the new downgrade reasons. Canonical source: `game/api_turn_support.py`.
- `support/tests/test_pr_br_continuation13_semantic_preservation.py`: Recorded replays, dimension, social, and evaluator fixtures. Canonical source: `tests/test_pr_br_continuation13_semantic_preservation.py`.
- `support/artifacts/pr_br_continuation13/junit.xml`: 303 passed, 0 failed. Canonical source: `artifacts/pr_br_continuation13/junit.xml`.
- `support/artifacts/pr_br_continuation13/manual_review.md`: Human-DM review of the six live turns. Canonical source: `artifacts/pr_br_continuation13/manual_review.md`.
- `support/artifacts/pr_br_continuation13/provenance.json`: HEAD and cost bounds. Canonical source: `artifacts/pr_br_continuation13/provenance.json`.
- `support/artifacts/pr_br_continuation13/20261001T003832Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation13/20261001T003832Z/transcript.md`.
- `support/artifacts/pr_br_continuation13/20261001T003832Z/turns.json`: Per-turn contracts, stage transitions, and generated versus final text. Canonical source: `artifacts/pr_br_continuation13/20261001T003832Z/turns.json`.
- `support/artifacts/pr_br_continuation13/20261001T003832Z/summary.json`: Call counts. Canonical source: `artifacts/pr_br_continuation13/20261001T003832Z/summary.json`.
- `support/artifacts/pr_br_continuation13/20261001T003832Z/generation_calls.json`: Generated candidates before final emission. Canonical source: `artifacts/pr_br_continuation13/20261001T003832Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation13/20261001T003832Z/interpretation_calls.json`: Structured interpretation outputs. Canonical source: `artifacts/pr_br_continuation13/20261001T003832Z/interpretation_calls.json`.
- `support/tools/run_pr_br_continuation13_live.py`: Six-turn cap and the live shapes. Canonical source: `tools/run_pr_br_continuation13_live.py`.

## Explicit omissions

- `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: duplicate content of docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
