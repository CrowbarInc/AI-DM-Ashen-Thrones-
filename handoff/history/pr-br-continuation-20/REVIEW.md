# Campaign

Campaign: PR-BR Continuation 20 — Incidental Entity Binding and Intent-Preserving Abstention
Identifier: `pr-br-continuation-20`
Date: 2026-10-01
Generated: 2026-10-02T01:06:52.834387+00:00
Purpose: Bind ordinary plausible incidental people through PR-BN, and keep the player's operation and dimension when entity or claim binding fails. Four focused live turns. No independent smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

C18's seal-or-retry lifecycle and C19's hard-authority boundary are unchanged. A proposed ordinary person in a populated scene can become a minimal incidental entity under PR-BN. Consequential and implausible references are not instantiated, and a failed explicit addressee does not restore the previous NPC. Source inquiry stays source when no claim is bound. The 281-test band passed. Four live turns bound a canonical runner, then the same porter, kept a source follow-up, and inspected the notice. Exact accepted text 4/4. READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: YES. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/incidental_entity.py classifies canonical, incidental, consequential, and unresolved references and persists a minimal incidental record through PR-BN.
- game/resolution_contract.py keeps operation and dimension independent of binding success and records entity_binding.
- game/interaction_completion.py treats an explicit new addressee as a proposal and does not fall back to the previous interlocutor.
- game/discourse_state.py persists an accepted incidental entity and clears a rejected explicit addressee.
- game/proposition_authority.py keeps non-operational hearsay as an NPC claim.

## Validation changes

- tests/test_pr_br_continuation20_incidental_entity.py covers cloth merchant, source without a claim, variants, implausible and consequential controls, stable identity, minimality, claim and authority, the C19 replay, and stubbed /api/chat.
- Broader band: 281 passed, 0 failed. Continuations 12-16, 18, 19, and 20 included.

## Tooling changes

- tools/run_pr_br_continuation20_live.py runs at most four focused live turns.

## Documentation changes

- docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md Continuation 20 section.

## Generated artifacts

- artifacts/pr_br_continuation20/20261002T010416Z live transcript, turns, manual review, and cost summary.

# What Was Tested

- **Focused tests:** Continuation 20 incidental binding, source preservation, controls, C19 replay, and stubbed /api/chat passed.
- **Broader relevant tests:** 281 passed, 0 failed. Full suite not run.
- **Full suite:** Not run.
- **Runtime validation:** 4 completed live turns. 1 interpretation call. 4 gameplay-generation calls. 0 regenerations. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 1 interpretation call. 4 gameplay-generation calls. 0 evaluator model calls. 0 regenerations. 0 aborted.
- **New regressions:** None in the deterministic band. Live turn 4 inspect did not fill an object target; the narration stayed on the notice board.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- An independent 10-turn smoke is the next evidence step. Do not run it from this cycle.
- Do not open Continuation 21 for the empty inspect target on 'look over the notice board' without a posted-reading clause.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- A bare 'look over the notice board' inspect does not fill the object target. The C19 wording that also reads what is posted still binds the board.

## Pre-existing baseline

- Scene openings and turns without a contract operation still use the legacy emission path.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health. The smoke was not run.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.
- Does not prove every live observation becomes an active claim.

# Recommended Next Step

External review, then an independent 10-turn smoke outside this cycle. Do not close PR-BR. Do not start PR-BS. Do not run the 4x10 gate.

# Review Bundle Contents

Bundle file count: `23`
Bundle ZIP size: `000000173309` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.
- `support/game/incidental_entity.py`: PR-BN incidental entity classification, minimal record, and persistence. Canonical source: `game/incidental_entity.py`.
- `support/game/resolution_contract.py`: Operation and dimension preserved independently of binding, with entity_binding on the contract. Canonical source: `game/resolution_contract.py`.
- `support/game/interaction_completion.py`: Explicit addressee precedence and stale-interlocutor suppression. Canonical source: `game/interaction_completion.py`.
- `support/game/discourse_state.py`: Accepted incidental persistence and rejected-addressee clearing. Canonical source: `game/discourse_state.py`.
- `support/game/live_resolution.py`: Applies the validated binding before generation. Canonical source: `game/live_resolution.py`.
- `support/game/scene_referent_catalog.py`: Established incidental entities re-enter the referent catalog. Canonical source: `game/scene_referent_catalog.py`.
- `support/game/immutable_valid_response.py`: C18 seal retained. Speaker constraint uses the incidental or proposed label. Canonical source: `game/immutable_valid_response.py`.
- `support/game/proposition_authority.py`: C19 boundary retained. Non-operational hearsay stays an NPC claim. Canonical source: `game/proposition_authority.py`.
- `support/game/bounded_improvisation.py`: PR-BN validator reused for incidental people. Canonical source: `game/bounded_improvisation.py`.
- `support/tests/test_pr_br_continuation20_incidental_entity.py`: Cloth merchant, source, variants, controls, stable identity, claims, C19 replay, and stubbed /api/chat. Canonical source: `tests/test_pr_br_continuation20_incidental_entity.py`.
- `support/tests/test_pr_br_continuation19_hard_authority.py`: C19 third-bell, grounded, and rumor regressions. Canonical source: `tests/test_pr_br_continuation19_hard_authority.py`.
- `support/tests/test_pr_br_continuation18_immutable_boundary.py`: C18 immutability, 16-turn replay, and the seven downstream failures. Canonical source: `tests/test_pr_br_continuation18_immutable_boundary.py`.
- `support/tools/run_pr_br_continuation20_live.py`: Four-turn focused live session. Canonical source: `tools/run_pr_br_continuation20_live.py`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/transcript.md`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/turns.json`: Contracts, binding, authority review, and accepted versus emitted text. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/turns.json`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/summary.json`: Generation, interpretation, and regeneration counts. Provenance HEAD. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/summary.json`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/manual_review.md`: Manual pass and evaluator comparison. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/manual_review.md`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/generation_calls.json`: Per-call generation excerpts. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation20/20261002T010416Z/interpretation_calls.json`: The live source follow-up proposal that did not replace source. Canonical source: `artifacts/pr_br_continuation20/20261002T010416Z/interpretation_calls.json`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/transcript.md`: C19 residual live evidence: content dimension and unbound cloth merchant. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/transcript.md`.

## Explicit omissions

- `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: duplicate content of docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
