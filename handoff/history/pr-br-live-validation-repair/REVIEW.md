# Campaign

Campaign: PR-BR Live-Validation Repair
Identifier: `pr-br-live-validation-repair`
Date: 2026-10-03
Generated: 2026-10-03T18:46:26.933035+00:00
Purpose: Review the localized repair of GMResolutionDecision attachment, sentence-safe fidelity, and retry context after the 4 PASS / 4 FAIL live validation.

# Executive Summary

The live failures came from two implementation defects: prebuilt Resolution Contracts returned before a GMResolutionDecision was attached, and sentence-local validation rejected competent narration by treating any negation or entity mention as a full restatement of every authorized fact. Retry then asked for a repair without the contract or the decision. This repair attaches a decision to every existing contract without rebuilding it, scopes negation to the predicate it actually negates, allows multi-sentence realization and unknown cause/actor/time, keeps contract and decision on the retry note, and preserves already-valid sentences under the existing C18 seal. Deterministic tests cover the four live failures and the four live passes. Exact model/API call count: 0. Recommendation: proceed to a second limited live validation.

Objective status: `repaired_for_second_limited_live_validation`.

# Changes Made

## Production changes

- Existing Resolution Contracts now receive a GMResolutionDecision instead of returning before attachment. Matching decisions are kept. Contracts are not rebuilt.
- Resolver replacement copies a decision whose contract_id matches the carried contract.
- A discarded fast-path contract also drops its decision before a rebuild.
- Narration prompts include the contract and the compact decision.
- Negation is predicate-scoped. Entity mention is not a full fact claim. Neighboring sentences may realize one authorized answer. Unknown cause, actor, and time do not negate an established condition.
- Polar questions record a direct authorized fact or a derived denial for the asked predicate.
- Hard-invalid retry feedback includes the contract, the decision, and the validation failure.
- After a failed retry, violating sentences can be dropped and the remainder revalidated and sealed. An established observation is used before the generic no-answer line.

## Validation changes

- Added deterministic tests for attachment on fresh, social, movement, perception, clarification, and retry contracts.
- Added the four live-failure regressions and the four live-pass preservations, the latter with decisions attached.
- Added novel-domain, retry-context, bounded-preservation, and fallback tests.

## Tooling changes

- No new tooling. Review handoff uses the existing builder.

## Documentation changes

- Added the live-validation repair implementation report.

## Generated artifacts

- No gameplay artifacts. No probe rerun. No 4x10 gate.

# What Was Tested

- **Focused tests:** 22 passed: tests/test_pr_br_live_validation_attachment_repair.py. Slice 1-3 passed: 9 + 7 + 7.
- **Broader relevant tests:** Final combined run: 365 tests, 359 passed, 6 failed. Passed: C18-C27, resolution contract, bounded improvisation authority, realization authority and provenance, state authority, unparsed movement, unresolved travel narration. C19 grounded third-bell reply stays valid; ungrounded third-bell still regenerates.
- **Full suite:** Not run.
- **Runtime validation:** Deterministic pytest only. No live gameplay.
- **Model/runtime boundary:** Exact model/API call count: 0. No eight-probe rerun. No 4x10 gate. No human playtest.
- **New regressions:** None in the repaired narration and attachment suites.
- **Pre-existing failures:** 6 failures in tests/test_scene_transition_authority.py. They assert resolution.kind travel or a destination scene change and observe social_probe or the current scene. select_ordinary_resolver still owns that choice. This repair attaches a decision to the contract the resolver already selected. Seven other tests in that file passed.
- **Self-contained bundle review:** Handoff generated from the explicit source list only.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Authorize a second limited live validation of the same eight probes. Do not start with the 4x10 gate.
- Decide separately whether mixed farewell-plus-travel lines should select the travel resolver. That is existing contract ownership, not this decision-attachment repair.

# Known Problems / Unresolved Findings

## Campaign-specific

- Negation scope is clause-local. It is not general English semantics.
- Derived denial applies to the asked polar predicate. It is not a physical inference engine.
- Actor, time, cause, meeting-place, and residue checks are small structural patterns.
- Bounded repair drops whole violating sentences and then reseals. It does not rewrite inside a sentence.

## Pre-existing baseline

- Six scene-transition authority tests still expect travel to override a social contract on mixed farewell lines.
- Historical saved-gate turns still lack reconstructable decision identities.

# Missing Concepts / Future Capabilities

- A second limited live measurement of the same eight probes.
- A separate review of mixed social-and-travel resolver selection, if those six tests are still desired behavior.

# What This Campaign Does NOT Prove

- Does not prove a second live 8-turn result.
- Does not prove general natural-language entailment.
- Does not change resolver ownership.
- Does not authorize the 4x10 gate, human playtest, or PR-BS.

# Recommended Next Step

A. LOCALIZED LIVE-VALIDATION DEFECTS ARE REPAIRED; PROCEED TO A SECOND LIMITED LIVE VALIDATION.

# Review Bundle Contents

Bundle file count: `10`
Bundle ZIP size: `000000156133` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_live_validation_repair/implementation_report.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_live_validation_repair/implementation_report.md`.
- `support/game/live_resolution.py`: Existing-contract return now attaches or keeps the matching GMResolutionDecision. Canonical source: `game/live_resolution.py`.
- `support/game/gm_resolution_decision.py`: Predicate-scoped negation, multi-sentence fidelity, unknown qualifiers, derived denial, retry context, and observation fallback. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/immutable_valid_response.py`: Retry feedback, bounded sentence preservation, decision review, and C18 seal. Canonical source: `game/immutable_valid_response.py`.
- `support/game/ordinary_semantic_ownership.py`: Carried resolutions keep the matching decision, and a discarded contract drops its decision. Canonical source: `game/ordinary_semantic_ownership.py`.
- `support/game/prompt_context.py`: Narration payload includes the contract and the decision. Canonical source: `game/prompt_context.py`.
- `support/game/api.py`: Procedural interpretation rebuild drops a stale decision with the discarded contract. Canonical source: `game/api.py`.
- `support/tests/test_pr_br_live_validation_attachment_repair.py`: Deterministic coverage of the four live failures, four live passes, attachment, retry, and bounded repair. Canonical source: `tests/test_pr_br_live_validation_attachment_repair.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
