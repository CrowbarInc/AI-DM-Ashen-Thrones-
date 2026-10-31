# Campaign

Campaign: PR-BS Cooperative GM Micro-Live Validation
Identifier: `pr-bs-cooperative-gm-micro-live`
Date: 2026-10-04
Generated: 2026-10-05T00:58:00.231194+00:00
Purpose: PR-BS. MODE: MICRO LIVE. MODEL/API CALLS: YES. Three semantic probes of the decision-facing answer recipe. No repairs, no commit, no push.

# Executive Summary

PR-BS. MODE: MICRO LIVE. MODEL/API CALLS: YES. Total model calls: 5 (2 preflights + 3 gameplay generations, 0 retries, 0 interpretation calls). Measured tokens, excluding one overwritten startup preflight: input 78,260; output 1,051; total 79,311. Gameplay generation tokens: input 78,236; output 1,049; total 79,285. Mean tokens per gameplay turn: 26,428.33. First-pass acceptance rate: 3/3. Useful first-pass response rate: 3/3. Retry rate: 0/3. Quality: Q3=3, Q2=0, Q1=0, Q0=0. Architecture status: A — PR-BR REMAINS CLOSED. Decision: A — PR-BS COOPERATIVE-GM SLICE SUCCEEDS. Generation input tokens were 25,208, 27,795, and 25,233, at the low end of the PR-BR 25k–33k band. This sample is directional only.

Objective status: `cooperative_gm_slice_succeeds`.

# Changes Made

## Production changes

- No production code was changed in this block.

## Validation changes

- Ran three live semantic probes: bounded yoke/hanger interpretation, mundane baker conversation, and a deliberate-cutting hypothesis on a fresh chapel scene.

## Tooling changes

- Added artifacts/pr_bs_cooperative_gm_micro_live/run_probes.py as a measurement harness. It does not change prompts, validators, or retry behavior.

## Documentation changes

- Added PR-BS_cooperative_gm_micro_live_validation.md.

## Generated artifacts

- Recorded raw generations, recipes, contracts, decisions, validation, C18 comparisons, state snapshots, and token measurements under artifacts/pr_bs_cooperative_gm_micro_live/evidence/.

# What Was Tested

- **Focused tests:** Not run. This block was live measurement only. Deterministic recipe tests were not rerun.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** Three live gameplay turns, one initial generation each, zero retries. P1, P2, and P3 all accepted on the first generation.
- **Model/runtime boundary:** MODEL/API CALLS: YES. Gameplay model gpt-4.1-mini-2025-04-14. Total model calls executed: 5. Measured input tokens 78,260; output tokens 1,051; total tokens 79,311. The first process preflight usage was overwritten and is excluded.
- **New regressions:** None observed in the three probes. No validator or prompt was changed.
- **Pre-existing failures:** Default faction pressure and agenda_progress advance by 1 on each turn through the existing world clock. That halt in the first process was a harness classification, and P1 was not rerun.
- **Self-contained bundle review:** Bundle includes the micro-live report, the harness, per-probe contracts, decisions, recipes, raw generations, validation, C18 comparisons, state snapshots, and token measurements.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- A — PR-BS COOPERATIVE-GM SLICE SUCCEEDS. Keep the answer-recipe direction.
- Architecture status: A — PR-BR REMAINS CLOSED.
- First-pass acceptance 3/3, useful first-pass 3/3, retry rate 0/3, Q3=3.
- Close this slice. Do not open retry redesign or payload canonicalization from this sample.

# Known Problems / Unresolved Findings

## Campaign-specific

- Probe 3's contract operation was perceive, so the recipe did not coach hypothesis language. The model still answered with uncertainty and the hypothesis stayed hypothesis.
- Probe 2 audit rows label spoken sentences epistemic_status world_truth while authority and persistence remain claim_only. Those rows were not written to scene facts or temporal provenance.
- Full generation input remains 25,208 to 27,795 tokens, inside the prior 25k–33k band.

## Pre-existing baseline

- Default world factions tick pressure and agenda_progress by 1 each turn.
- The first startup preflight token usage was not retained after the continuation overwrote model_calls.json.

# Missing Concepts / Future Capabilities

- Statistical confidence. Three turns cannot prove a general first-pass rate.
- Retry remaining-authority guidance. No retry occurred, so that path was not measured.
- Further provider-context canonicalization beyond the authority slice.

# What This Campaign Does NOT Prove

- Does not prove production readiness.
- Does not prove a 26–27% reduction in total provider tokens.
- Does not reopen PR-BR. No new authority, provenance, or C18 contradiction was observed.
- Does not show that the recipe explicitly coaches player-hypothesis turns. Probe 3 succeeded while the projected recipe was a perceive realization.

# Recommended Next Step

Close this PR-BS cooperative-GM slice and keep the answer-recipe direction. Do not start retry redesign or provider-context canonicalization from these three turns.

# Review Bundle Contents

Bundle file count: `37`
Bundle ZIP size: `000000166857` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/PR-BS_cooperative_gm_micro_live_validation.md`: Primary campaign standard/report used to orient the review. Canonical source: `PR-BS_cooperative_gm_micro_live_validation.md`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/run_probes.py`: Live harness: three probes, raw capture, C18 and authority stops. No production change. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/run_probes.py`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/harness_continuation.json`: Records the faction-clock halt and that P1 was not rerun. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/harness_continuation.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/model_calls.json`: Continuation preflight plus P2 and P3 provider usage, response ids, and latency. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/model_calls.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/preflight.json`: Continuation upstream preflight health record. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/preflight.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/run_finished.json`: Continuation finished with no halt after P2 and P3. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/run_finished.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/digest.json`: P1: Compact probe result: player line, acceptance, tokens, C18, temporal state. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/digest.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/validation.json`: P1: Exact attempt-1 audit, reasons, and acceptance. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/validation.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/c18.json`: P1: Accepted, sealed, and emitted strings plus mutation flag. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/c18.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/decision_facing_answer_recipe.json`: P1: Decision-facing recipe projected for the live turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/decision_facing_answer_recipe.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/resolution_contract.json`: P1: Live resolution contract for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/resolution_contract.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/gm_resolution_decision.json`: P1: Canonical GMResolutionDecision for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/gm_resolution_decision.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/raw_generation_attempt_1.json`: P1: Initial raw structured generation and provider usage. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/raw_generation_attempt_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json`: P1: Provider input, character count, and the recipe the model received. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/state_before.json`: P1: Scene, world, and provenance before the turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/state_before.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/state_after.json`: P1: Scene, world, and provenance after the turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/state_after.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/digest.json`: P2: Compact probe result: player line, acceptance, tokens, C18, temporal state. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/digest.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/validation.json`: P2: Exact attempt-1 audit, reasons, and acceptance. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/validation.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/c18.json`: P2: Accepted, sealed, and emitted strings plus mutation flag. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/c18.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/decision_facing_answer_recipe.json`: P2: Decision-facing recipe projected for the live turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/decision_facing_answer_recipe.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/resolution_contract.json`: P2: Live resolution contract for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/resolution_contract.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/gm_resolution_decision.json`: P2: Canonical GMResolutionDecision for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/gm_resolution_decision.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/raw_generation_attempt_1.json`: P2: Initial raw structured generation and provider usage. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/raw_generation_attempt_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/provider_request_attempt_generation_1.json`: P2: Provider input, character count, and the recipe the model received. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/provider_request_attempt_generation_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/state_before.json`: P2: Scene, world, and provenance before the turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/state_before.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/state_after.json`: P2: Scene, world, and provenance after the turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/state_after.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/digest.json`: P3: Compact probe result: player line, acceptance, tokens, C18, temporal state. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/digest.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/validation.json`: P3: Exact attempt-1 audit, reasons, and acceptance. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/validation.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/c18.json`: P3: Accepted, sealed, and emitted strings plus mutation flag. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/c18.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/decision_facing_answer_recipe.json`: P3: Decision-facing recipe projected for the live turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/decision_facing_answer_recipe.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/resolution_contract.json`: P3: Live resolution contract for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/resolution_contract.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/gm_resolution_decision.json`: P3: Canonical GMResolutionDecision for the probe. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/gm_resolution_decision.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/raw_generation_attempt_1.json`: P3: Initial raw structured generation and provider usage. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/raw_generation_attempt_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/provider_request_attempt_generation_1.json`: P3: Provider input, character count, and the recipe the model received. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/provider_request_attempt_generation_1.json`.
- `support/artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/state_after.json`: P3: Scene, world, and provenance after the turn. Canonical source: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/state_after.json`.

## Explicit omissions

- `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/state_before.json`: duplicate content of artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/state_before.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
