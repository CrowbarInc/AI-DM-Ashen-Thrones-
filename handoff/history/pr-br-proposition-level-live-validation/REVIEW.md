# Campaign

Campaign: PR-BR Proposition-Level Claim Control Live Validation
Identifier: `pr-br-proposition-level-live-validation`
Date: 2026-10-03
Generated: 2026-10-04T02:17:52.098419+00:00
Purpose: Six-turn multi-turn live validation of authority laundering, epistemic continuity, free-text fact boundaries, and natural bounded GM speech.

# Executive Summary

Six turns scored 3 PASS and 3 FAIL. Authority laundering did not recur: the A2 presupposition never became world truth, and B1-B2 preserved the C19 free-text boundary. A3 exposed a high-severity localized defect: correct unknown-cause, actor, and sequence sentences were rejected while an unsupported star-chart lead survived preservation. Temporal provenance stayed absent. B3 preserved mundane improvisation with bounded claim authority but emitted malformed quotation after preservation. Exact calls: 6 initial, 4 retry, 4 interpretation, 1 preflight, 0 other, 15 total. Decision B: return to targeted implementation.

Objective status: `localized_high_severity_epistemic_defects_without_laundering`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Ran exactly six gameplay turns across two fresh three-turn sequences.
- No turn reruns, exploratory gameplay, 4x10 gate, commit, or push.

## Tooling changes

- Added a measurement-only harness under artifacts/pr_br_proposition_live_validation/.

## Documentation changes

- Added the required 19-section validation report and exact call accounting.

## Generated artifacts

- The stamped evidence directory contains complete per-turn states, contracts, decisions, generations, retries, audits, final responses, and provenance captures.

# What Was Tested

- **Focused tests:** Not run; this cycle was live validation only.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** 6/6 HTTP gameplay turns completed once. Manual 3 PASS / 3 FAIL: A2, B1, B2 pass; A1, A3, B3 fail.
- **Model/runtime boundary:** 6 initial generation calls, 4 retry generation calls, 4 interpretation calls, 1 preflight call, 0 other model calls, 15 total.
- **New regressions:** No production patch. Live defects are uncertainty rejection, missing temporal provenance, and malformed/incompletely audited preserved output.
- **Pre-existing failures:** The original 8/40 gate and older uncertainty-sensitive attachment failures remain prior evidence; neither was rerun.
- **Self-contained bundle review:** Bundle includes the report, exact initial states, all six API responses and turn traces, full generation/retry prompts and results, committed states, call manifest, production freeze hashes, and the harness.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- B. LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.
- Confirm A3 as high severity because correct uncertainty was rejected while an unsupported lead survived.
- Do not start PR-BS or a broader release-candidate gate.

# Known Problems / Unresolved Findings

## Campaign-specific

- A1 did not provide useful qualified inference.
- A3 rejected correct unknown-cause/actor/sequence text twice.
- Temporal provenance and active claim remained absent across Sequence A.
- B3 preservation emitted malformed quotation and incomplete final claim accounting.

## Pre-existing baseline

- Original 8/40 gate failures remain historical comparison evidence.
- Known older uncertainty-sensitive failures were not repaired or rerun in this cycle.

# Missing Concepts / Future Capabilities

- Uncertainty-safe evidential classification.
- Cross-turn persistence of GM inference and player hypothesis without promotion.
- Syntax- and claim-complete bounded sentence preservation.

# What This Campaign Does NOT Prove

- Does not prove release-candidate readiness.
- Does not prove broad multi-turn playability beyond these six turns.
- Does not rerun the 4x10 gate.
- Does not authorize PR-BS.

# Recommended Next Step

Target uncertainty/evidential validation, temporal provenance persistence, follow-up referent binding, and preservation completeness; then run focused deterministic tests.

# Review Bundle Contents

Bundle file count: `59`
Bundle ZIP size: `000001104412` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/validation_report.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/validation_report.md`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/preflight_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/preflight_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/production_freeze_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/production_freeze_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/run_manifest.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/run_manifest.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/run_setup.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/run_setup.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_A_initial_state.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_A_initial_state.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_B_initial_state.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_B_initial_state.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/api_response.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/api_response.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/authoritative_state_after.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/authoritative_state_after.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/generation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/generation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/gm_output.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/gm_output.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/interpretation_calls.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/interpretation_calls.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/player_input.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/player_input.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/resolution.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/resolution.json`.
- `support/artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/trace_index.json`: Exact initial state, turn trace, model-call record, committed state, or freeze evidence. Canonical source: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/trace_index.json`.
- `support/artifacts/pr_br_proposition_live_validation/run_validation.py`: Exact fresh scenes, six player turns, call instrumentation, and capture procedure. Canonical source: `artifacts/pr_br_proposition_live_validation/run_validation.py`.

## Explicit omissions

- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/production_freeze_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/production_freeze_after.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_A_initial_state.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A1/authoritative_state_after.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A3/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_A2/authoritative_state_after.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/sequence_B_initial_state.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/authoritative_state_after.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/interpretation_calls.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B1/interpretation_calls.json; canonical reference retained
- `artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B3/authoritative_state_before.json`: duplicate content of artifacts/pr_br_proposition_live_validation/20261004T021456Z/turn_B2/authoritative_state_after.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
