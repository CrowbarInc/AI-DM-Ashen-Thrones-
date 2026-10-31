# Campaign

Campaign: PR-BR Novel Authority Live Validation
Identifier: `pr-br-novel-authority-live-validation`
Date: 2026-10-03
Generated: 2026-10-03T18:18:24.892851+00:00
Purpose: Bounded 8-turn live probe of whether model generation behaves competently through the GM resolution decision architecture, in novel domains.

# Executive Summary

Eight isolated novel-domain gameplay turns scored 4 PASS and 4 FAIL. When the decision was attached, it authorized the authored facts, and bounded incidental play plus authorized movement succeeded. The kiln, dye vat, and chapel bell generations were competent and were then replaced by the canned sentence "No one here can answer that from what is settled here" after semantic_identity_mismatch. Social and movement turns never received a GMResolutionDecision, because attachment returns once a contract already exists. On that path, Nessa stated an unauthored organization as known fact. Decision B: localized defects. Return to targeted implementation. No production edits, no reruns, no 4x10 gate, no human playtest, and no PR-BS.

Objective status: `measured_defects_for_targeted_implementation`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Ran 8 isolated live gameplay turns. No production code was changed after the results.

## Tooling changes

- Added a validation harness and local trace summarizers under artifacts/pr_br_novel_authority_probe/. These are not production.

## Documentation changes

- Wrote the 18-section validation report beside the turn artifacts.

## Generated artifacts

- artifacts/pr_br_novel_authority_probe/20261003T181221Z/ holds initial states, contracts, decisions, generations, validation metadata, committed states, and the report.

# What Was Tested

- **Focused tests:** Not run. This cycle was live measurement only.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** 8 isolated POST /api/chat turns. Manual 4 PASS / 4 FAIL. Passes: turns 3, 5, 6, 8. Fails: turns 1, 2, 4, 7.
- **Model/runtime boundary:** 8 gameplay turns. 11 generation calls, including 3 retries. 1 interpretation call. 1 startup preflight. 0 evaluator-model calls. 0 reruns. 0 gate sessions.
- **New regressions:** No production patch. Live defects are semantic-identity rejection collapsing three competent answers, and missing decisions on prebuilt social and movement contracts.
- **Pre-existing failures:** The 8/40 gate still stands as prior evidence of generic nonresolution and consequential invention. This probe did not rerun that gate. Location desync did not appear here.
- **Self-contained bundle review:** Bundle contains the validation report, all 8 turn artifacts, call logs, and the three production modules that explain the observed attachment and validation behavior.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- B. LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.
- Next implementation should attach GMResolutionDecision when a contract already exists, and should stop sentence-level semantic_identity_mismatch from replacing a matched answer with the canned nonresolution line.
- Do not start PR-BS, a 4x10 gate, or a human playtest on this evidence.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turns 1, 4, and 7 generated competent answers, then semantic_identity_mismatch replaced them with one canned sentence.
- Turns 2, 3, 6, and 8 have no GMResolutionDecision because the contract already existed.
- Turn 2 states that the Violet Compact is known to gather at the docks or the market.
- Retry prompts on turns 1, 4, and 7 omitted the contract and the decision.

## Pre-existing baseline

- The second full gate remained 8/40 with consequential invention and generic nonresolution. This cycle did not rerun it.

# Missing Concepts / Future Capabilities

- Decision attachment on routes that construct the Resolution Contract before attach_interaction_obligation.
- A realization rule that allows answering that something is not firing, or that no one knows who, without contradicting a positive cracked fact.
- Partial-response preservation so one mismatched sentence does not discard the authorized sentences.

# What This Campaign Does NOT Prove

- Does not prove multi-turn continuity.
- Does not prove a release threshold.
- Does not rerun the 4x10 gate.
- Does not authorize a human playtest.
- Does not show that turns 3 and 8 were protected by the decision layer. That layer was absent on those routes.

# Recommended Next Step

Targeted implementation of decision attachment on prebuilt contracts, and of semantic-identity handling for negated answers and neighboring sentences. Remeasure after that. Do not open PR-BS.

# Review Bundle Contents

Bundle file count: `62`
Bundle ZIP size: `000000327134` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/validation_report.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/validation_report.md`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/generation_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/generation_calls.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/interpretation_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/interpretation_calls.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/preflight_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/preflight_calls.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/run_manifest.json`: Exact model-call counts and per-turn status. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/run_manifest.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/trace_summary.txt`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/trace_summary.txt`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/committed_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/generations.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/gm_output.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/initial_state.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/resolution.json`.
- `support/artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/turn_record.json`.
- `support/artifacts/pr_br_novel_authority_probe/run_probes.py`: Exact seeds, player lines, and capture path for the eight turns. Canonical source: `artifacts/pr_br_novel_authority_probe/run_probes.py`.
- `support/game/gm_resolution_decision.py`: Production module that shows decision attachment or narration rejection for this run. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/live_resolution.py`: Production module that shows decision attachment or narration rejection for this run. Canonical source: `game/live_resolution.py`.
- `support/game/immutable_valid_response.py`: Production module that shows decision attachment or narration rejection for this run. Canonical source: `game/immutable_valid_response.py`.

## Explicit omissions

- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_02_02_unsupported_consequential_question/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_03_03_npc_claim_uncertainty/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_04_04_observation_vs_inference/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_05_05_bounded_incidental_improvisation/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_06_06_authorized_movement/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_07_07_semantic_strengthening_pressure/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/interpretation_calls.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/completed.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/completed.json; canonical reference retained
- `artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_08_08_background_npc/interpretations.json`: duplicate content of artifacts/pr_br_novel_authority_probe/20261003T181221Z/turn_01_01_authorized_consequential_fact/interpretations.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
