# Campaign

Campaign: ATGB-01 Conversational Benchmark Design
Identifier: `atgb_01_conversational_benchmark_design`
Date: 2026-10-18
Generated: 2026-10-18T21:10:00+00:00
Purpose: Propose the first Ashen Thrones Gameplay Benchmark corpus, scoring rubric, execution model, and cadence for player-AI-DM communication. Design only. No corpus adoption, runner, scorer, provider call, or gameplay change.

# Executive Summary

Implementation outcome: a reviewable ATGB-01 design, a 10-scenario catalog of 37 scored turns, and a feasibility note that reuses chat, isolated storage, and the existing evidence packet. No production code, test, evaluator, or runner was added. Original reproduction: not applicable; this pass repairs no gameplay failure. Related generalization: not applicable. Independent generalization: not evaluated. Regression: not run; no product or test change. ATGB: no result. The corpus is proposed and is not adopted, so the evidence standard still forbids an ATGB claim. Known limitations: Frontier Gate facts and the current conversational owners bound the scenarios; held-out wording is visible in this review package so reviewers can judge it, and it is not yet in a reserved directory. Remaining uncertainty: adoption, trial count, held-out location, the live-call budget, and whether S07 should move into the reserved slice are open. No gameplay improvement is claimed. Deterministic success is not proposed as evidence of natural conversation.

Objective status: `PROPOSED — AWAITING REVIEW`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No test, evaluator, threshold, calibration case, protected replay, or playability scenario changed. evaluate_playability remains the playability contract and is not an ATGB verdict.

## Tooling changes

- No runner, scorer, or review-generator change. The existing ZIP sections carry the proposal, the unrun benchmark, and the open decisions.

## Documentation changes

- Added development/reports/atgb_01_conversational_benchmark_design.md as the proposed specification, scoring model, cadence, risks, hypothetical report, and open decisions.
- Added development/reports/atgb_01_scenario_catalog.md with 10 conversations and 37 scored turns.
- Added development/reports/atgb_01_implementation_feasibility.md.
- Updated docs/NEXT_SESSION.md so the next agent can find this proposal. The PR-BL product orientation and the unreconciliation with later PR-EG history remain pending maintenance.

## Generated artifacts

- Generated this review summary, manifest, and ZIP from the design proposal. No gameplay transcript was produced.

# What Was Tested

- **Focused tests:** Document review against the Constitution, the Validation Evidence Standard ATGB section, the playability contract, Product Realization validation, and the current Frontier Gate facts and conversational owners. No pytest suite.
- **Broader relevant tests:** Not run. Not required for a design package with no product or test change.
- **Full suite:** Not run.
- **Runtime validation:** No gameplay, provider, host-lane, or benchmark run. Original reproduction, related generalization, and independent generalization were not evaluated because this pass repairs no gameplay failure.
- **Model/runtime boundary:** No model was called. A provider call was not required and was not made.
- **New regressions:** None. No production or test change.
- **Pre-existing failures:** Not reassessed. The PR-BL session orientation remains unreconciliation with later PR-EG history.
- **Self-contained bundle review:** Not an automated gameplay bundle-only test. The ZIP packages the design, the catalog, and the feasibility note. It contains no gameplay transcript and claims no behavioral PASS.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Adopt or reject ATGB-01 as the reviewed corpus. Until adoption, no Ashen Thrones Gameplay Benchmark result may be claimed.
- Confirm Frontier Gate as the benchmark world.
- Confirm human rubric scoring, with playability output allowed only as adjacent telemetry.
- Confirm the reserved location data/validation/atgb/held_out/ and the rule that implementation work does not load or quote it.
- Choose one live trial or three for the first baseline, and set the provider-call budget.
- Decide whether a generic OOC acknowledgement that misses the question fails response success. The proposal says it does.
- Decide whether S07 stays development-visible or moves to held-out.
- Decide whether efficiency remains recorded-only in rubric 01.
- The NEXT_SESSION versus PR-EG orientation discrepancy is a separate maintenance item. This package does not decide it.

# Known Problems / Unresolved Findings

## Campaign-specific

- The corpus is not adopted. Reconsideration before adoption cannot produce an ATGB result and does not authorize a provider call.
- Held-out player lines are included in the review catalog so suitability can be judged. They are not yet isolated from ordinary implementation context.
- S09 does not require a two-NPC conversation system; a single clarification is the successful path. A future implementer could mistake that scenario for a crowd-simulation request.
- docs/NEXT_SESSION.md product orientation remains the 2026-09-26 PR-BL closeout. Later PR-EG history remains in handoff history. This design records that discrepancy and does not reconcile it.

## Pre-existing baseline

- Playability scoring, semantic calibration, protected replay, and replay failure classification keep their existing authorities.
- Curfew hours, stew price, diegetic time passage, compound multi-action execution, and richer pronoun continuity remain outside current authored behavior. The catalog treats grounded uncertainty or one clarification as success.

# Missing Concepts / Future Capabilities

- An adopted ATGB corpus, an isolated-store driver, and a human judgment sheet. None is implemented here.
- A provider price table. Future reports must say cost is unavailable when telemetry has no priced token counts.
- The review generator has no dedicated ATGB fields. This package uses the existing summary sections.

# What This Campaign Does NOT Prove

- That player-AI-DM communication improved.
- An Ashen Thrones Gameplay Benchmark result, a host-lane result, or a live-provider result.
- That the proposed scenarios pass on the current build.
- Mechanical correctness of combat, inventory, economy, character creation, equipment, or advancement.
- That playability PASS and ATGB acceptability are the same judgment.
- That deterministic host behavior is natural conversational competence.
- That the PR-BL session orientation and later PR-EG history agree.

# Recommended Next Step

Stop. Review the design package before any runner, scoring sheet, fixture split, or production change. Do not report an ATGB result from this proposal. The fresh human playtest recorded in NEXT_SESSION remains the product step; this design does not replace it and does not start PR-BM.

# Review Bundle Contents

Bundle file count: `8`
Bundle ZIP size: `000000071252` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Ten proposed conversations, 37 scored turns, facts, and pass criteria. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_01_implementation_feasibility.md`: Existing chat, reset, telemetry, and evidence-packet reuse, and the small driver that would still be required after adoption. Canonical source: `development/reports/atgb_01_implementation_feasibility.md`.
- `support/docs/validation_evidence_standard.md`: ATGB governance. This proposal does not adopt a corpus and does not amend the standard. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/playability_validation.md`: Playability remains evaluate_playability. ATGB must not become a second scorer. Canonical source: `docs/playability_validation.md`.
- `support/docs/NEXT_SESSION.md`: Points at the proposal and leaves the PR-BL versus PR-EG discrepancy unresolved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
