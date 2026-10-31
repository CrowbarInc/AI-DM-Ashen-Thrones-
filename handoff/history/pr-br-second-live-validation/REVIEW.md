# Campaign

Campaign: PR-BR Second Limited Live Validation
Identifier: `pr-br-second-live-validation`
Date: 2026-10-03
Generated: 2026-10-03T19:08:26.178014+00:00
Purpose: Fresh 8-turn live measurement of GMResolutionDecision attachment, semantic fidelity, retry context, and the known mixed social/travel resolver path.

# Executive Summary

Eight fresh isolated gameplay turns scored 5 PASS and 3 FAIL. Every Resolution Contract carried a GMResolutionDecision whose contract_id matched. The first validation's missing-decision gap and the sentence-local negation reject did not recur, and the generic no-answer line was not emitted. The sluice turn still rejected a correct unknown-cause sentence as an event-site location fill, then preservation removed that sentence and kept a missing-patrol lead. The sail-loft move committed, while the decision recorded no location mutation and narration added an upward stair. The mixed thanks-and-courtyard line selected travel and moved; it did not reproduce the six social-blocks-travel failures, and it dropped the thanks. Exact model/API calls: 11 (8 initial generations, 1 retry, 1 interpretation, 1 preflight). Recommendation: localized defects. Return to targeted implementation. The six scene-transition tests remain unrepaired.

Objective status: `measured_localized_defects_for_targeted_implementation`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Ran 8 isolated live gameplay turns. No production code was changed.

## Tooling changes

- Added a measurement harness under artifacts/pr_br_second_live_validation/. It is not production.

## Documentation changes

- Wrote the 20-section validation report beside the turn artifacts.

## Generated artifacts

- artifacts/pr_br_second_live_validation/20261003T190253Z/ holds initial states, contracts, decisions, generations, validation metadata, committed states, and the report.

# What Was Tested

- **Focused tests:** Not run. This cycle was live measurement only.
- **Broader relevant tests:** Not run. The six scene-transition failures were not rerun and not patched.
- **Full suite:** Not run.
- **Runtime validation:** 8 isolated POST /api/chat turns. Manual 5 PASS / 3 FAIL. Passes: turns 2, 3, 4, 5, 8. Fails: turns 1, 6, 7.
- **Model/runtime boundary:** 8 gameplay turns. 8 initial generation calls. 1 retry generation call. 1 interpretation call. 1 startup preflight. 11 total model/API calls. 0 reruns. 0 gate sessions.
- **New regressions:** No production patch. Live defects are an event-site false reject plus preservation of the wrong sentence, a movement decision with empty permitted mutations, and a mixed utterance contracted as travel only.
- **Pre-existing failures:** Six failures remain in tests/test_scene_transition_authority.py. Probe 7 did not reproduce social-blocks-travel. It selected travel, committed the courtyard, and omitted the thanks. Those six tests were not repaired.
- **Self-contained bundle review:** Bundle contains the validation report, all 8 turn artifacts, call logs, the harness, and the production modules that implement qualifier checks, preservation, and resolver selection.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- B. SECOND LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.
- Next implementation should stop the event-site pattern from rejecting an unknown cause, actor, and time, and should keep preservation from deleting that sentence while retaining an unrelated lead.
- Movement decisions should record the location mutation the travel resolver commits, so arrival narration is not steered by the departure stair.
- Mixed social-and-travel ownership remains a separate question. Probe 7 did not reproduce the six social-blocks-travel failures. Do not treat those tests as fixed.
- Do not start a multi-turn validation, the 4x10 gate, a human playtest, or PR-BS on this evidence.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turn 1 rejected the unseen-cause sentence as unauthorized_qualifier:location, then bounded preservation removed it and kept a missing-patrol lead.
- Turn 1 retry context included the contract and the decision. The retry generation was empty (malformed_or_truncated).
- Turns 6 and 7 record permitted_state_mutations as empty and outcome consequentially_unresolved after a committed scene_transition.
- Turn 6 narration adds a stair that leads upward after arrival in the sail loft.
- Turn 7 contract subject is travel. The thanks is not narrated. Social did not block the move.

## Pre-existing baseline

- Six tests in tests/test_scene_transition_authority.py still fail when a social contract blocks travel. They were not rerun and not repaired.
- The second full gate remained 8/40. This cycle did not rerun it.

# Missing Concepts / Future Capabilities

- Unknown-cause wording such as remain unseen must count as an unresolved slot, and happened-here must not match that wording.
- A committed scene_transition should be a permitted location mutation on the decision that narrates the arrival.
- A separate review of mixed-utterance ownership, using the six existing scene-transition failures as the social-blocks-travel evidence.

# What This Campaign Does NOT Prove

- Does not prove multi-turn continuity.
- Does not prove the six scene-transition tests would pass.
- Does not rerun the 4x10 gate.
- Does not authorize a human playtest or PR-BS.
- Does not show that an empty retry can repair a false qualifier reject. Preservation edited the first generation instead.

# Recommended Next Step

B. SECOND LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.

# Review Bundle Contents

Bundle file count: `61`
Bundle ZIP size: `000000334753` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/validation_report.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/validation_report.md`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/generation_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/generation_calls.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/interpretation_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/interpretation_calls.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/preflight_calls.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/preflight_calls.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/run_manifest.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/run_manifest.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/committed_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/committed_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/generations.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/generations.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/gm_output.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/gm_output.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/initial_state.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/initial_state.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/resolution.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/resolution.json`.
- `support/artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/turn_record.json`: Saved live-probe evidence for external review. Canonical source: `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/turn_record.json`.
- `support/artifacts/pr_br_second_live_validation/run_probes.py`: Exact fresh seeds, player lines, and capture path for the eight turns. Canonical source: `artifacts/pr_br_second_live_validation/run_probes.py`.
- `support/game/gm_resolution_decision.py`: Event-site qualifier check and decision attachment used by these turns. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/immutable_valid_response.py`: Retry context and bounded sentence preservation used on turn 1. Canonical source: `game/immutable_valid_response.py`.
- `support/game/ordinary_semantic_ownership.py`: Resolver selection that followed contract subject on every turn, including probe 7. Canonical source: `game/ordinary_semantic_ownership.py`.

## Explicit omissions

- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_02_02_prebuilt_social_unsupported_world_fact/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_03_03_negated_unrelated_predicate/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_04_04_multi_sentence_observation/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_05_05_background_npc_improvisation/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_06_06_clean_authorized_movement/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_07_07_mixed_social_and_declared_movement/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/interpretations.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/completed.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/turn_01_01_established_condition_unknown_cause/completed.json; canonical reference retained
- `artifacts/pr_br_second_live_validation/20261003T190253Z/turn_08_08_valid_answer_consequential_temptation/interpretations.json`: duplicate content of artifacts/pr_br_second_live_validation/20261003T190253Z/interpretation_calls.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
