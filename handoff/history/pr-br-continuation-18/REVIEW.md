# Campaign

Campaign: PR-BR Continuation 18 — Immutable Valid Response Boundary and Bounded Regeneration
Identifier: `pr-br-continuation-18`
Date: 2026-10-01
Generated: 2026-10-01T22:54:09.093891+00:00
Purpose: Preserve a hard-valid generated response, regenerate once when it is hard-invalid, and emit a minimal safe nonresolution only after both attempts fail. Replay the 16 C17 turns. Six focused live turns. No independent smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

Hard-valid text is now sealed and emitted unchanged. The 16-turn replay preserves 12/12 eligible lines and blocks 4/4 hard-invalid initials. The seven downstream-created failures stay eliminated. Six live turns all matched the accepted text exactly. Two hard-invalid initials were regenerated once and the retry was sealed. Final manual PASS was 5/6. One unauthored closing time inside guard dialogue reached the player. READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: YES. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/immutable_valid_response.py seals an accepted response, hard-validates, retries once, and emits a narrow safe line.
- game/api.py runs that lifecycle on contract-bearing narration and skips the quality tournament once sealed.
- Post-acceptance mutators return the sealed text. best_safe and satisfaction no longer choose the emitted line.

## Validation changes

- tests/test_pr_br_continuation18_immutable_boundary.py replays 16 turns, the seven downstream failures, the four hard-invalid initials, and the stubbed /api/chat path.
- Focused band including Continuations 14-16 and 18 passed 183 tests with 0 failures.

## Tooling changes

- tools/run_pr_br_continuation18_live.py runs at most six focused live turns.

## Documentation changes

- docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md Continuation 18 section.

## Generated artifacts

- artifacts/pr_br_continuation18/20261001T225126Z live transcript, turns, and cost summary.

# What Was Tested

- **Focused tests:** Continuation 18 immutability, replay, retry, state-commit, and raw chat stub tests passed.
- **Broader relevant tests:** 183 passed, 0 failed in the last combined Continuation 14-18 band. An earlier 189-test Continuation 12-16 band also passed. Full suite not run.
- **Full suite:** Not run.
- **Runtime validation:** 6 completed live turns. 2 interpretation calls. 8 gameplay-generation calls, of which 2 were regenerations. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 2 interpretation calls. 8 gameplay-generation calls. 0 evaluator model calls. 2 regenerations. 0 aborted.
- **New regressions:** None in the deterministic band. Live turn 3 preserved an unauthored third-bell closing inside guard dialogue.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- An independent 10-turn smoke is the next measurement. Do not run it in this cycle.
- Turn 3 shows a clock inside NPC dialogue that hard validation does not yet reject.
- Turn 2's contract target became a slice of the previous answer.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Unauthored schedule language inside NPC dialogue can be sealed.
- A follow-up contract target can be the previous sentence rather than the interlocutor.
- The local evaluator false-failed three hedged but usable live answers.

## Pre-existing baseline

- Scene openings and turns without a contract operation still use the legacy emission path.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health. The smoke was not run.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.
- Does not prove every unauthored NPC claim is blocked. Turn 3 emitted a third-bell closing.

# Recommended Next Step

External review. Do not close PR-BR. Do not start PR-BS. The next cycle may run one independent 10-turn smoke. Do not run the six live turns again in this cycle.

# Review Bundle Contents

Bundle file count: `10`
Bundle ZIP size: `000000071143` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.
- `support/game/immutable_valid_response.py`: Accepted response, hard validation, one retry, and safe nonresolution. Canonical source: `game/immutable_valid_response.py`.
- `support/tests/test_pr_br_continuation18_immutable_boundary.py`: 16-turn replay, seven downstream fixtures, four hard-invalid fixtures, and stub paths. Canonical source: `tests/test_pr_br_continuation18_immutable_boundary.py`.
- `support/tools/run_pr_br_continuation18_live.py`: Six-turn focused live session. Canonical source: `tools/run_pr_br_continuation18_live.py`.
- `support/artifacts/pr_br_continuation18/20261001T225126Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation18/20261001T225126Z/transcript.md`.
- `support/artifacts/pr_br_continuation18/20261001T225126Z/turns.json`: Accepted versus emitted text, provenance, and retry feedback. Canonical source: `artifacts/pr_br_continuation18/20261001T225126Z/turns.json`.
- `support/artifacts/pr_br_continuation18/20261001T225126Z/summary.json`: Generation, interpretation, and regeneration counts. Canonical source: `artifacts/pr_br_continuation18/20261001T225126Z/summary.json`.
- `support/artifacts/pr_br_continuation18/20261001T225126Z/generation_calls.json`: Per-call generation excerpts and retry reasons. Canonical source: `artifacts/pr_br_continuation18/20261001T225126Z/generation_calls.json`.

## Explicit omissions

- `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: duplicate content of docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
