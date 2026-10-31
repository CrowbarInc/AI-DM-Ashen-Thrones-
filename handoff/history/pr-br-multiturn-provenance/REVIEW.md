# Campaign

Campaign: PR-BR Multi-turn Provenance and Recursive Authority
Identifier: `pr-br-multiturn-provenance`
Date: 2026-10-03
Generated: 2026-10-03T23:10:00Z
Purpose: Small multi-turn live validation of provenance survival and recursive authority. Two isolated four-turn sequences. No production edits.

# Executive Summary

Eight gameplay turns, two isolated sequences, scored 4 PASS and 4 FAIL. Linden's brine-cask statement stayed hearsay through movement, the osier-rack transition was recorded on GMResolutionDecision, and a footprint sentence was rejected. Sequence A did not hold. An unfired-jar inference was audited as authored world truth, the next turn used it as the event, and the following turn said it was clear the jar was never fired in a kiln while validation rejected the uncertainty sentence. Scene JSON did not gain the kiln fact. Narration and the audit label did. Exact model/API calls: 15 (8 initial generations, 4 retries, 2 interpretations, 1 preflight). Decision C. Multi-turn validation reproduced recursive authority failure. Return to architectural review.

Objective status: `recursive_authority_failure_reproduced_return_to_architectural_review`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Ran 8 gameplay turns in two isolated sequences. No failed turn was rerun. No production code was changed.

## Tooling changes

- Added a measurement harness under artifacts/pr_br_multiturn_provenance/. It is not production.

## Documentation changes

- Wrote the 22-section validation report beside the turn artifacts.

## Generated artifacts

- artifacts/pr_br_multiturn_provenance/20261003T223147Z/ holds both initial states, all eight turn artifacts, call logs, and the report.

# What Was Tested

- **Focused tests:** Not run. This cycle was live measurement only.
- **Broader relevant tests:** Not run. The 4x10 gate was not run.
- **Full suite:** Not run.
- **Runtime validation:** 8 POST /api/chat turns. Manual 4 PASS / 4 FAIL. Passes: A1, B1, B2, B4. Fails: A2, A3, A4, B3.
- **Model/runtime boundary:** 8 gameplay turns. 8 initial generation calls. 4 retry generation calls. 2 interpretation calls. 1 startup preflight. 0 other model calls. 15 total model/API calls. 0 reruns.
- **New regressions:** No production patch. Live finding: narrated-fact identity match labels causal add-ons as authored world truth, and preservation drops the hedged sentence.
- **Pre-existing failures:** Split-quotation attributed testimony and guard_captain versus gate_guard were not repaired, not reinterpreted, and did not appear in these scenes.
- **Self-contained bundle review:** Bundle contains the validation report, both initial states, all eight turn artifacts, call logs, the harness, and the production modules that classify narrated facts and preserve sentences.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- C. MULTI-TURN VALIDATION REPRODUCED RECURSIVE AUTHORITY FAILURE; RETURN TO ARCHITECTURAL REVIEW.
- Review classify_narrated_fact: a sentence that contains an authorized observation plus a new cause, certainty, or corroborating clue currently inherits world_truth when subject and value terms match.
- Review preservation: unsupported_narrator_lead removed the uncertainty sentences on A4 and kept the kiln certainty.
- B3 is a separate mixed-intent gap. Travel and the location mutation held. The thanks was not an obligation and was not spoken.
- Do not start a broader release-candidate gate, the 4x10 gate, or PR-BS on this evidence.

# Known Problems / Unresolved Findings

## Campaign-specific

- A2 audited the unfired/process-disruption sentence as authored_world_fact world_truth.
- A3 used leave-the-jar-unfired as the event and recorded only an unresolved actor.
- A4 emitted that it was clear the jar was never fired in a kiln and that the coil-pots show no signs of firing. The uncertainty sentence was rejected.
- Scene visible facts did not gain those propositions. Narration and later prompts did.
- B3 committed osier_rack and recorded the location mutation. The thanks and both referents were unspoken. Supporting obligations were empty.
- Rejected proposals and B1 incidental lines were not written to the bounded ledger.

## Pre-existing baseline

- Split quotation / attributed-testimony edge case remains unrepaired.
- guard_captain versus gate_guard addressability mismatch remains unrepaired.

# Missing Concepts / Future Capabilities

- A narrated sentence needs a split between the authorized observation and any additional cause, certainty, or corroborating clue.
- Hedged unknown-cause or unknown-actor sentences should not be deleted as narrator leads while the assertive version of the same idea is kept.
- Rejected consequential proposals and accepted mundane incidental details need a ledger if later turns are to respect them as policy rather than as raw transcript.
- A mixed utterance still needs one supporting social obligation when travel is the primary act.

# What This Campaign Does NOT Prove

- Does not prove the commit store will adopt the kiln sentence on a fifth turn. Scene JSON did not adopt it in four turns.
- Does not prove a rejected footprint would be blocked later. The rejection was not stored, and no fifth turn was run.
- Does not rerun the 4x10 gate.
- Does not show the two known deterministic failures are fixed.
- Does not authorize PR-BS or a broader release-candidate gate.

# Recommended Next Step

C. MULTI-TURN VALIDATION REPRODUCED RECURSIVE AUTHORITY FAILURE; RETURN TO ARCHITECTURAL REVIEW.

# Review Bundle Contents

Bundle file count: `86`
Bundle ZIP size: `000001242529` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/validation_report.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/validation_report.md`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/control/ack.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/control/ack.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/control/status.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/control/status.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/generation_calls.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/generation_calls.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/interpretation_calls.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/interpretation_calls.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/preflight_calls.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/preflight_calls.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/run_manifest.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/run_manifest.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A0_authoritative.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A0_authoritative.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A0_initial_state.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A0_initial_state.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/interpretations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/interpretations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B0_authoritative.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B0_authoritative.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B0_initial_state.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B0_initial_state.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generation_prompts.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generation_prompts.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/gm_output.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/interpretations.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/interpretations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/resolution.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/resolution.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/state_after.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/state_after.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/turn_record.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/campaign.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/campaign.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/character.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/character.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/combat.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/combat.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/conditions.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/conditions.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/clay_shed.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/clay_shed.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/frontier_gate.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/frontier_gate.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/market_quarter.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/market_quarter.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/old_milestone.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/old_milestone.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/session.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/session.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/session_log.jsonl`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/session_log.jsonl`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/world.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/world.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/combat.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/combat.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/osier_rack.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/osier_rack.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/seat_shop.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/seat_shop.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/session.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/session.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/session_log.jsonl`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/session_log.jsonl`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/world.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/world.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/summary_rows.json`: Saved multi-turn live evidence: state, contract, decision, generation, or call log. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/summary_rows.json`.
- `support/artifacts/pr_br_multiturn_provenance/run_live.py`: Measurement harness. Fresh seeds, carried state, and capture path. Not production. Canonical source: `artifacts/pr_br_multiturn_provenance/run_live.py`.
- `support/game/gm_resolution_decision.py`: Narrated-fact classification, identity match, narrator-lead rejection, and movement decision reconciliation. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/immutable_valid_response.py`: Bounded sentence preservation that kept the initial generation after retry failure on A2-A4. Canonical source: `game/immutable_valid_response.py`.

## Explicit omissions

- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A0_authoritative.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/interpretations.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/interpretations.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/interpretations.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B0_authoritative.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/interpretations.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/interpretations.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/interpretations.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/completed.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A1/completed.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/state_before.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/state_after.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/campaign.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/campaign.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/character.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/character.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/conditions.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/conditions.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/frontier_gate.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/frontier_gate.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/market_quarter.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/market_quarter.json; canonical reference retained
- `artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_b/data/scenes/old_milestone.json`: duplicate content of artifacts/pr_br_multiturn_provenance/20261003T223147Z/storage_a/data/scenes/old_milestone.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
