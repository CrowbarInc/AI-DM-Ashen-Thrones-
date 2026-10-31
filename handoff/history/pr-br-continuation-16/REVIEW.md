# Campaign

Campaign: PR-BR Continuation 16 — Interaction Completion, Explicit Discourse Transitions & Structural Response Integrity
Identifier: `pr-br-continuation-16`
Date: 2026-10-01
Generated: 2026-10-01T11:35:36.208082+00:00
Purpose: Make interaction completion, current-turn discourse precedence, and structural candidate validity explicit. Replay the failed smoke. Six focused live turns. No independent smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

Structural completion now blocks attribution shells, player-text fallback splices, stale interlocutors, and passive-scene substitutions in deterministic replay. The 350-test band passed. Live contracts were 6/6, but final manual PASS was 2/6. A quoted manner line, a false find-them rejection, and a guard line spoken for the watcher all reached the player. Telemetry caught 1 of 4 manual degradations. READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: NO. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/interaction_completion.py judges ASK payload, attribution shells, nonverbal resolution, discourse binding, and structural degradation.
- game/resolution_contract.py applies current-turn discourse before rank and refuses structurally invalid challengers.
- game/live_resolution.py does not voice a subject that repeats the player's own opening.
- game/discourse_state.py clears a rejected interlocutor and can adopt the emitted speaker.
- game/dialogue_social_plan.py treats a manner tail with no proposition as a bare attribution shell.

## Validation changes

- tests/test_pr_br_continuation16_interaction_completion.py replays all ten smoke turns, structural variants, and the stubbed /api/chat path.
- Broader band: 350 passed, 0 failed.

## Tooling changes

- tools/run_pr_br_continuation16_live.py runs at most six focused live turns.

## Documentation changes

- docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md Continuation 16 section.

## Generated artifacts

- artifacts/pr_br_continuation16 live transcript, manual review, junit, and provenance.

# What Was Tested

- **Focused tests:** Continuation 16 interaction-completion, discourse, shell, leakage, and ten-turn replay tests passed inside the 350-test band.
- **Broader relevant tests:** 350 passed, 0 failed, 0 skipped. Junit artifacts/pr_br_continuation16/junit.xml.
- **Full suite:** Not run.
- **Runtime validation:** 6 completed live turns. 2 interpretation calls. 6 generation calls. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 2 interpretation calls. 6 generation calls. 0 evaluator model calls. 0 retries. 0 aborted.
- **New regressions:** None in the deterministic band. Live final manual PASS was 2/6.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Independent 10-turn smoke is not ready. Live structural failures recurred.
- Do not retune the locate cue or the quoted-manner check and rerun these six turns in this cycle.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- A quoted manner sentence still counts as ASK payload.
- The word find plus the current speaker's name can discard a real inability.
- Emission can speak as a different NPC when the line does not use a Name-says frame.
- A successful notice reading can be prefixed with Nothing here matches that.

## Pre-existing baseline

- The grounding lock can still replace a mixed invented-and-authored inspection with the visible-fact closer.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health. The smoke was not run.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.
- Does not prove live attribution shells are gone. Turn 1 emitted a quoted manner line.

# Recommended Next Step

External review. Do not close PR-BR. Do not start PR-BS. Do not run another independent smoke or the six live turns again in this cycle.

# Review Bundle Contents

Bundle file count: `21`
Bundle ZIP size: `000000210517` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`.
- `support/game/interaction_completion.py`: Interaction completion, discourse binding, and structural degradation. Canonical source: `game/interaction_completion.py`.
- `support/game/resolution_contract.py`: Current-turn precedence and structural validity before rank. Canonical source: `game/resolution_contract.py`.
- `support/game/live_resolution.py`: Player-opening subjects are not voiced. Canonical source: `game/live_resolution.py`.
- `support/game/discourse_state.py`: Rejected interlocutor is cleared. Canonical source: `game/discourse_state.py`.
- `support/game/dialogue_social_plan.py`: Manner tails with no proposition are attribution shells. Canonical source: `game/dialogue_social_plan.py`.
- `support/game/api_turn_support.py`: Discourse commit receives the emitted line and the referent catalog. Canonical source: `game/api_turn_support.py`.
- `support/tests/test_pr_br_continuation16_interaction_completion.py`: Ten smoke replays, variants, and stubbed chat. Canonical source: `tests/test_pr_br_continuation16_interaction_completion.py`.
- `support/tests/test_pr_br_continuation15_content_clarification.py`: Continuation 15 regressions. Canonical source: `tests/test_pr_br_continuation15_content_clarification.py`.
- `support/tests/test_pr_br_continuation14_resolution_content.py`: Continuation 14 regressions. Canonical source: `tests/test_pr_br_continuation14_resolution_content.py`.
- `support/artifacts/pr_br_continuation16/junit.xml`: 350 passed, 0 failed. Canonical source: `artifacts/pr_br_continuation16/junit.xml`.
- `support/artifacts/pr_br_continuation16/manual_review.md`: Manual review of the six live turns. Canonical source: `artifacts/pr_br_continuation16/manual_review.md`.
- `support/artifacts/pr_br_continuation16/provenance.json`: HEAD and cost bounds. Canonical source: `artifacts/pr_br_continuation16/provenance.json`.
- `support/artifacts/pr_br_continuation16/20261001T113214Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation16/20261001T113214Z/transcript.md`.
- `support/artifacts/pr_br_continuation16/20261001T113214Z/turns.json`: Per-turn contracts and candidate transitions. Canonical source: `artifacts/pr_br_continuation16/20261001T113214Z/turns.json`.
- `support/artifacts/pr_br_continuation16/20261001T113214Z/summary.json`: Call counts. Canonical source: `artifacts/pr_br_continuation16/20261001T113214Z/summary.json`.
- `support/artifacts/pr_br_continuation16/20261001T113214Z/generation_calls.json`: Generated candidates before final emission. Canonical source: `artifacts/pr_br_continuation16/20261001T113214Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation16/20261001T113214Z/interpretation_calls.json`: Structured interpretation outputs. Canonical source: `artifacts/pr_br_continuation16/20261001T113214Z/interpretation_calls.json`.
- `support/tools/run_pr_br_continuation16_live.py`: Six-turn cap and the live shapes. Canonical source: `tools/run_pr_br_continuation16_live.py`.

## Explicit omissions

- `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: duplicate content of docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
