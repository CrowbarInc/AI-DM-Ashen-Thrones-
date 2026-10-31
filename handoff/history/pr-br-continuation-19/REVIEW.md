# Campaign

Campaign: PR-BR Continuation 19 — Hard-Authority Boundary and Contract Canonicalization Closeout
Identifier: `pr-br-continuation-19`
Date: 2026-10-01
Generated: 2026-10-02T00:25:08.201879+00:00
Purpose: Reject ungrounded authoritative operational rules before C18 seals them, and canonicalize source follow-ups and social questions. Four focused live turns. No independent smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

C18's seal-or-retry lifecycle is unchanged. Ungrounded schedules, access rules, and official levies are hard-invalid and retry once. Grounded rules, NPC rumors, and bounded incidental detail stay valid. The 267-test band passed, including the 16-turn historical replay. Four live turns kept exact accepted text and emitted no unauthorized world rule. Two live contracts were not canonical: a source follow-up stayed on content, and an unbound ask of an unlisted merchant sealed the safe line. READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: NO. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/proposition_authority.py classifies schedules, access rules, levies, and incidental detail with PR-BN kinds.
- game/immutable_valid_response.py rejects ungrounded authoritative rules and retries once without rewriting the sentence.
- game/resolution_contract.py binds clause-sized claims by id and keeps social questions as ask.
- game/bounded_improvisation.py treats official levies as stronger than mundane prices.

## Validation changes

- tests/test_pr_br_continuation19_hard_authority.py covers third-bell, grounded, rumor, bounded, price, temporal, access, source follow-up, ask/act, the six C18 turns, and stubbed /api/chat.
- Broader band: 267 passed, 0 failed. Continuations 12-16 and 18 included.

## Tooling changes

- tools/run_pr_br_continuation19_live.py runs at most four focused live turns.

## Documentation changes

- docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md Continuation 19 section.

## Generated artifacts

- artifacts/pr_br_continuation19/20261002T002239Z live transcript, turns, authority review, and cost summary.

# What Was Tested

- **Focused tests:** Continuation 19 authority, claim binding, ask/act, and raw chat stub tests passed.
- **Broader relevant tests:** 267 passed, 0 failed. Full suite not run.
- **Full suite:** Not run.
- **Runtime validation:** 4 completed live turns. 1 interpretation call. 6 gameplay-generation calls, of which 2 were regenerations. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 1 interpretation call. 6 gameplay-generation calls. 0 evaluator model calls. 2 regenerations. 0 aborted.
- **New regressions:** None in the deterministic band. Live turn 2 kept dimension content. Live turn 3 sealed a safe nonresolution after an unbound ask.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Do not run an independent 10-turn smoke from this result.
- Live turn 3 shows a fast-path ask with no interlocutor for a person who is not in the scene.
- Live turn 2 did not select the source dimension when no active claim existed.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Source follow-up without a stored claim can remain dimension content.
- Ask with a null interlocutor can be returned instead of abstaining, and both generations can stay on the previous NPC.

## Pre-existing baseline

- Scene openings and turns without a contract operation still use the legacy emission path.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health. The smoke was not run.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.
- Does not prove every live social follow-up selects the source dimension.

# Recommended Next Step

External review. Do not close PR-BR. Do not start PR-BS. Do not run the independent smoke or the four live turns again in this cycle.

# Review Bundle Contents

Bundle file count: `21`
Bundle ZIP size: `000000164239` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.
- `support/game/immutable_valid_response.py`: C18 seal, hard validation, one retry, and the new ungrounded-rule reason. Canonical source: `game/immutable_valid_response.py`.
- `support/game/proposition_authority.py`: PR-BN proposition classification for schedules, access, levies, and incidental detail. Canonical source: `game/proposition_authority.py`.
- `support/game/bounded_improvisation.py`: PR-BN kinds and official-levy check. Canonical source: `game/bounded_improvisation.py`.
- `support/game/resolution_contract.py`: Claim identity, source follow-up, and ask versus act canonicalization. Canonical source: `game/resolution_contract.py`.
- `support/game/interpretation_proposal.py`: Fast-path families and claim-target identity. Canonical source: `game/interpretation_proposal.py`.
- `support/game/interaction_completion.py`: Terminal ask versus act, with open limited to a real object. Canonical source: `game/interaction_completion.py`.
- `support/game/discourse_state.py`: Active-claim extraction and epistemic status. Canonical source: `game/discourse_state.py`.
- `support/tests/test_pr_br_continuation19_hard_authority.py`: Third-bell, controls, variants, C18 replay, and stubbed /api/chat. Canonical source: `tests/test_pr_br_continuation19_hard_authority.py`.
- `support/tests/test_pr_br_continuation18_immutable_boundary.py`: C18 immutability, 16-turn replay, and rejected-claim persistence. Canonical source: `tests/test_pr_br_continuation18_immutable_boundary.py`.
- `support/tests/test_pr_br_continuation16_interaction_completion.py`: C16 interaction completion regressions. Canonical source: `tests/test_pr_br_continuation16_interaction_completion.py`.
- `support/tests/test_pr_br_continuation15_content_clarification.py`: C15 content clarification regressions. Canonical source: `tests/test_pr_br_continuation15_content_clarification.py`.
- `support/tests/test_pr_br_continuation14_resolution_content.py`: C14 resolution content regressions. Canonical source: `tests/test_pr_br_continuation14_resolution_content.py`.
- `support/tools/run_pr_br_continuation19_live.py`: Four-turn focused live session. Canonical source: `tools/run_pr_br_continuation19_live.py`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/transcript.md`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/turns.json`: Contracts, authority review, provenance, and accepted versus emitted text. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/turns.json`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/summary.json`: Generation, interpretation, and regeneration counts. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/summary.json`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/generation_calls.json`: Per-call generation excerpts and retry reasons. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation19/20261002T002239Z/interpretation_calls.json`: The one live interpretation proposal. Canonical source: `artifacts/pr_br_continuation19/20261002T002239Z/interpretation_calls.json`.

## Explicit omissions

- `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: duplicate content of docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
