# Campaign

Campaign: PR-BR Targeted Live-Validation Repair
Identifier: `pr-br-targeted-live-validation-repair`
Date: 2026-10-03
Generated: 2026-10-03T20:00:00Z
Purpose: Deterministic repair of the three second-live failures: unknown-slot qualifier safety, movement decision reconciliation, and mixed-intent obligation preservation. No model calls.

# Executive Summary

The three second-live failures are repaired deterministically. Unknown cause, actor, and time are no longer read as an event location when the sentence says they remain unseen. A resolved scene transition is copied into GMResolutionDecision after the resolver commits, with departure and destination facts tagged by scene. Mixed utterances keep one contract operation and a bounded supporting obligation; travel does not globally override social, and social does not erase committed travel. The six scene-transition regressions pass, as does a Turn 7 reproduction. Suite: 480 passed, 2 failed, 482 collected. The two failures are an ungrounded quoted rule whose closing quote is split off, and an interaction target cleared because guard_captain is not the roster id. Exact model/API calls: 0. Recommendation A.

Objective status: `localized_defects_repaired_for_small_multi_turn_validation`.

# Changes Made

## Production changes

- Event-site location is a verb complement, and unresolved cause, actor, and time stay unknown when the sentence says so.
- Hedged narrator leads without a speaker, quote, or hearsay verb are unsupported. Attributed NPC speech stays a claim.
- reconcile_movement_decision copies a resolved scene transition into the existing GMResolutionDecision after commit.
- executable_obligations records one primary act plus at most one supporting committed act. The contract operation is unchanged. One travel stage owns the scene write.

## Validation changes

- Added tests/test_pr_br_qualifier_movement_mixed_intent.py.
- The six tests in tests/test_scene_transition_authority.py now pass.

## Tooling changes

- No changes in this category.

## Documentation changes

- Wrote artifacts/pr_br_targeted_repair/IMPLEMENTATION_REPORT.md.

## Generated artifacts

- No changes in this category.

# What Was Tested

- **Focused tests:** Qualifier, movement fidelity, Turn 7, inverse mixed intent, and modality contrasts in tests/test_pr_br_qualifier_movement_mixed_intent.py. All passed.
- **Broader relevant tests:** Scene-transition authority, decision slices 1-3, live attachment, continuation 12-27, resolution contract, outcome precedence, interpretation proposal, model interpretation, unparsed movement, unresolved travel, state authority, bounded improvisation, and social interaction authority.
- **Full suite:** 480 passed, 2 failed, 482 collected in the targeted suite. Not the repository-wide suite. Not the 4x10 gate.
- **Runtime validation:** None. No isolated live probe and no multi-turn validation.
- **Model/runtime boundary:** 0 gameplay turns. 0 generation calls. 0 retry calls. 0 interpretation calls. 0 preflight calls. 0 total model/API calls.
- **New regressions:** Two tests in test_authoritative_lead_provenance_social_prose_non_ingestion.py fail. Authorizing every opening quote as testimony was tried and reverted because it cleared the C18 ungrounded-rule reject and the unauthored meeting-place reject.
- **Pre-existing failures:** test_calibration_http_captain_answer_does_not_mint_narration_ctx: narration is kept, CTIR records guard_captain, and a later entity rebuild clears the interaction target because that id is not in the gate_guard roster. synchronize_scene_addressability call sites are unchanged from HEAD.
- **Self-contained bundle review:** The bundle contains the implementation report, the new deterministic tests, and the production modules that implement qualifier checks, movement reconciliation, and mixed obligations.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- A. LOCALIZED DEFECTS ARE REPAIRED; PROCEED TO SMALL MULTI-TURN LIVE VALIDATION.
- Do not start the 4x10 gate, a human playtest, or PR-BS on this evidence.
- The split-quote harbor line is still removed as an ungrounded rule. Treating every opening quote as a claim reopened harder authority failures.
- The guard_captain interaction-target clear is an addressability rebuild against the roster id, not a mixed-intent loss.

# Known Problems / Unresolved Findings

## Campaign-specific

- Supporting social acts are narration obligations. They do not also run the social resolver as a second state write.
- Acknowledgment is hard-failed only at eight or more words.
- A quotation split before its closing mark is not reconstructed into attributed testimony.

## Pre-existing baseline

- test_calibration_http_captain_answer_does_not_mint_narration_ctx still fails on active_interaction_target_id.
- The 4x10 gate was not rerun.

# Missing Concepts / Future Capabilities

- A supporting social act does not create new persistent discourse state.
- Bare leave without to, for, or cross may not record travel.

# What This Campaign Does NOT Prove

- Does not prove multi-turn continuity.
- Does not rerun the 8-turn live probe.
- Does not rerun the 4x10 gate.
- Does not authorize a human playtest or PR-BS.

# Recommended Next Step

A. LOCALIZED DEFECTS ARE REPAIRED; PROCEED TO SMALL MULTI-TURN LIVE VALIDATION.

# Review Bundle Contents

Bundle file count: `11`
Bundle ZIP size: `000000147234` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_targeted_repair/IMPLEMENTATION_REPORT.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_targeted_repair/IMPLEMENTATION_REPORT.md`.
- `support/tests/test_pr_br_qualifier_movement_mixed_intent.py`: Qualifier, movement fidelity, Turn 7, inverse mixed intent, and modality contrasts. Canonical source: `tests/test_pr_br_qualifier_movement_mixed_intent.py`.
- `support/tests/test_scene_transition_authority.py`: The six previously failing mixed social and travel regressions. Canonical source: `tests/test_scene_transition_authority.py`.
- `support/game/gm_resolution_decision.py`: Unknown-slot and event-site checks, narrator-lead classification, and movement reconciliation. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/player_commitment.py`: Primary and supporting executable obligations, reusing C22 commitment modality. Canonical source: `game/player_commitment.py`.
- `support/game/resolution_contract.py`: Stores executable_obligations without replacing the single contract operation. Canonical source: `game/resolution_contract.py`.
- `support/game/ordinary_semantic_ownership.py`: Lets one travel stage run when a committed travel obligation is recorded. Canonical source: `game/ordinary_semantic_ownership.py`.
- `support/game/live_resolution.py`: Copies the obligation record onto Interaction Obligation. Canonical source: `game/live_resolution.py`.
- `support/game/api.py`: Passes the contract into the travel stage and reconciles the decision after the scene commit. Canonical source: `game/api.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
