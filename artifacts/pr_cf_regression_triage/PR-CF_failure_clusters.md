# PR-CF Failure Clusters

Authoritative PR-CE broad result: 202 failures across 65 files. PR-CF diagnostic JUnit preserved the same 202/65 inventory shape, but 161 records are setup noise from the PR-CF basetemp parent omission; only the 41 non-noise failures are used as fresh assertion signatures.

## Counts By Signature

- H_ENV_BASETEMP_SETUP_NOISE: 161
- A_SOCIAL_REPLY_PLANNING: 12
- B_NARRATION_RESPONSE_PROJECTION: 8
- G_GOVERNANCE_EXPECTATION_DRIFT: 5
- D_REACTIVE_TURN_PIPELINE: 5
- C_SPEAKER_CONTRACT_MISMATCH: 4
- G_TEST_EXPECTATION_DRIFT: 4
- C_AUTHORITY_STATE_PROVENANCE: 1
- I_OTHER: 1
- F_LIVE_MODEL_GUARD: 1

## Largest Files

- tests/test_turn_pipeline_shared.py: 33
- tests/test_explicit_world_action_social_lock_override.py: 9
- tests/test_exploration_resolution.py: 7
- tests/test_investigation_result_provenance_non_invention.py: 7
- tests/test_later_turn_untargeted_observation_restacking.py: 7
- tests/test_golden_replay_structural_invariants.py: 6
- tests/test_agent_history_question_ownership.py: 5
- tests/test_by3_strict_social_semantic_mutation.py: 5
- tests/test_pr_bp_live_resolution_routing.py: 5
- tests/test_reactive_player_validation.py: 5
- tests/test_referenced_surface_grounding_inspection_resolution.py: 5
- tests/test_arrival_destination_realization.py: 4
- tests/test_dialogue_plan_final_emission_gate.py: 4
- tests/test_gauntlet_regressions.py: 4
- tests/test_post_return_observation_geographic_integrity.py: 4
- tests/test_prompt_context_narrative_roles.py: 4
- tests/test_social_question_relevance_answer_selection.py: 4
- tests/test_authored_knowledge_realization.py: 3
- tests/test_bound_speaker_knowledge_resolution.py: 3
- tests/test_compat_import_governance.py: 3

## Working Clusters

- A / SOCIAL REPLY PLANNING: reply_kind/refusal/unknown shifts, speaker grounding, dialogue establishment, social relevance HTTP narration.
- B / NARRATION RESPONSE PROJECTION: final_emitted_source and fallback-family changes, quoted NPC fallback accepted where tests expected closed non-speech output.
- C / AUTHORITY / PROVENANCE: speaker_contract mismatch, lead/provenance/state assertions, live-model guard breach in provider failure test.
- D / TURN PIPELINE: 33 turn_pipeline failures, plus current reproducible TestClient socketpair hang in representative rerun.
- E / EXPLORATION / INVESTIGATION: 7 exploration and 7 investigation files in the PR-CE failure inventory; PR-CF could not safely rerun HTTP-heavy cases after socketpair hang recurred.
- G / TEST EXPECTATION DRIFT: governance/import/prompt payload tests assert older allowlists, importer caps, and provider-visible guidance text.
- H / ENVIRONMENT / FIXTURE: PR-CF rerun basetemp setup noise, plus a separate current TestClient/socketpair hang reproduced after PR-CE.
