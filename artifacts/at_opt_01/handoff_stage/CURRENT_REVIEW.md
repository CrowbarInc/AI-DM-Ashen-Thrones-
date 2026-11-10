# Campaign

Campaign: AT-OPT-01 Runtime Cost Attribution and Routing Audit
Identifier: `at_opt_01`
Date: 2026-11-08
Generated: 2026-11-08T17:45:00+00:00
Purpose: Read-only audit of why PR-PLAY-79D-F3 sent one 22777-input primary narration, where tokens and latency actually go, and which single later experiment is justified.

# Executive Summary

Verdict B/PARTIAL. The F3 step-back was one gm.call_gpt primary_turn: 22777 input, 600 output, 23377 total, provider latency 5339.716 ms. Interpretation and the physical experiment were off, so the fast path stored operation unresolved, and disabling expression does not block primary narration. The 3000-token cycle cap was never installed; the HTTP script set 100000/200000 ceilings and admission allowed the estimate. The same sentence on the 79D-F host cost 72 tokens and was accepted. The F3 publication was a replaced fallback. Primary and retry calls dominate historical tokens; PR-PLAY-79 spent 131711 of 144968 tokens on five of them and published no narration. The captured prompt was not stored. A reconstruction puts the bulk in response_policy, instructions, and turn_packet. No production code changed. No live provider call. Do not start the recommended experiment automatically.

Objective status: `PARTIAL`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No tests, holdouts, or validators were run or edited.

## Tooling changes

- No changes in this category.

## Documentation changes

- Added the AT-OPT-01 audit reports under development/campaigns/product_realization/at_opt_01/.
- Prepended the AT-OPT-01 result to docs/NEXT_SESSION.md.

## Generated artifacts

- Added ledger, reconstruction, provenance, and coverage JSON under artifacts/at_opt_01/.
- Generated this review handoff. No provider ledger or campaign save was modified.

# What Was Tested

- **Focused tests:** Not run. This cycle is an evidence audit.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** No gameplay and no live provider call. Offline ledger parse plus one provider-disabled build_messages reconstruction against a temporary copy of the F3 snapshot.
- **Model/runtime boundary:** Historical ledgers only. Model on the F3 call was gpt-4.1-mini-2025-04-14. This audit sent no request.
- **New regressions:** No product code changed, so no new product regression was introduced by this cycle.
- **Pre-existing failures:** Not re-measured. Prior historical lanes remain as recorded in NEXT_SESSION.
- **Self-contained bundle review:** The bundle contains the eight audit reports, the ledger summary, the prompt reconstruction sizes, provenance, and the coverage statement. No standardized gameplay evidence packet was produced because this cycle did not play.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the B/PARTIAL verdict and the single recommended experiment before anyone starts AT-OPT-02.
- Do not treat the reconstructed prompt section sizes as the captured token bill.
- Do not set a 3000-token production cap on openings. Recorded openings are about 25294 input tokens.

# Known Problems / Unresolved Findings

## Campaign-specific

- The captured F3 prompt and the estimate passed to admit_request were not logged.
- Session narration_provider_calls counted 2 while the ledger shows 1 sent request.
- The saved GM route stamp says retry_escalation for a primary_turn spend.

## Pre-existing baseline

- Primary narration payloads are opening-scale, about 23000 to 29000 tokens, and several historical outputs were rejected or replaced.
- Browser paint time is not instrumented.
- The working tree was already dirty at entry. HEAD does not uniquely identify the executable source.

# Missing Concepts / Future Capabilities

- Pre-dispatch logging of the input estimate and per-section byte sizes, without prompt text.
- A sent-versus-attempted counter so an unsent retry is not reported as a second provider call.

# What This Campaign Does NOT Prove

- It does not prove a safe deletion inside response_policy or instructions.
- It does not prove that equal 25294 input counts are duplicate prompts.
- It does not prove browser paint latency.
- It does not prove exact accepted-line counts for 79A, 79B, or 79C beyond the handoff prose.
- It does not implement a routing or budget change.

# Recommended Next Step

Do not start it automatically. One later experiment: if the fast path leaves a retreat unresolved, do not call gm.call_gpt. Keep the existing one-expression path when the physical experiment is already on. When it is off, return the existing non-mutating sentence and do not move position. A provider-free test must also show that a primary estimate over a 3000-token verification ceiling is refused before dispatch. Do not open PR-PLAY-80.

# Review Bundle Contents

Bundle file count: `15`
Bundle ZIP size: `000000079706` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_01/01_executive_summary.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_01/01_executive_summary.md`.
- `support/development/campaigns/product_realization/at_opt_01/02_f3_incident.md`: F3 decision chain and publication outcome. Canonical source: `development/campaigns/product_realization/at_opt_01/02_f3_incident.md`.
- `support/development/campaigns/product_realization/at_opt_01/03_routing_inventory.md`: Dispatch owners, eligibility, and escalation conditions. Canonical source: `development/campaigns/product_realization/at_opt_01/03_routing_inventory.md`.
- `support/development/campaigns/product_realization/at_opt_01/04_cost_and_latency.md`: Per-cycle cost and latency tables. Canonical source: `development/campaigns/product_realization/at_opt_01/04_cost_and_latency.md`.
- `support/development/campaigns/product_realization/at_opt_01/05_context_composition.md`: Reconstructed prompt section sizes and growth limits. Canonical source: `development/campaigns/product_realization/at_opt_01/05_context_composition.md`.
- `support/development/campaigns/product_realization/at_opt_01/06_admission_budget.md`: Why the 3000-token cap did not bind. Canonical source: `development/campaigns/product_realization/at_opt_01/06_admission_budget.md`.
- `support/development/campaigns/product_realization/at_opt_01/07_optimization_plan.md`: Ranked candidates and the one recommended experiment. Canonical source: `development/campaigns/product_realization/at_opt_01/07_optimization_plan.md`.
- `support/development/campaigns/product_realization/at_opt_01/08_integrity.md`: Fingerprints, protected-file result, and evidence gaps. Canonical source: `development/campaigns/product_realization/at_opt_01/08_integrity.md`.
- `support/artifacts/at_opt_01/ledger_summary.json`: Machine-readable per-cycle ledger totals. Canonical source: `artifacts/at_opt_01/ledger_summary.json`.
- `support/artifacts/at_opt_01/prompt_reconstruction.json`: Reconstructed section byte sizes. Not the captured prompt. Canonical source: `artifacts/at_opt_01/prompt_reconstruction.json`.
- `support/artifacts/at_opt_01/provenance.json`: Source hashes and protected-file rehash. Canonical source: `artifacts/at_opt_01/provenance.json`.
- `support/artifacts/at_opt_01/evidence_coverage.json`: Explicit coverage and unknown list. Canonical source: `artifacts/at_opt_01/evidence_coverage.json`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this audit. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
