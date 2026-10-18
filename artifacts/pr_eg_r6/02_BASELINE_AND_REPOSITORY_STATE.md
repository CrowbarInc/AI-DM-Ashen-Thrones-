# 02 — Baseline and Repository State

Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` on `feature/product-realization`.

The worktree already contained uncommitted predecessor work. This cycle did not revert or commit it.

```
M artifacts/by2/protected_semantic_mutation_report.json
 M artifacts/by2/protected_semantic_mutation_report.md
 M artifacts/by3/strict_social_semantic_mutation_report.json
 M artifacts/by3/strict_social_semantic_mutation_report.md
 M artifacts/golden_replay/bug_recurrence_event_log.json
 M artifacts/golden_replay/bug_recurrence_history.json
 M artifacts/golden_replay/bug_recurrence_history.md
 M artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json
 M artifacts/golden_replay/bug_recurrence_session_event_log.json
 M artifacts/golden_replay/owner_drift_hotspots.json
 M artifacts/golden_replay/owner_drift_hotspots.md
 M artifacts/golden_replay/owner_drift_risk.json
 M artifacts/golden_replay/owner_drift_risk.md
 M artifacts/golden_replay/recurrence_trajectory_history.json
 M artifacts/golden_replay/replay_failure_report.md
 M data/combat.json
 M data/session.json
 M data/session_log.jsonl
 M data/world.json
 M docs/audits/BQ16_recurrence_graduation_audit.md
 M docs/audits/BQC4_final_graduation_decision.md
 M docs/audits/BQC5_effectiveness_validation.md
 M game/adjudication.py
 M game/anti_reset_emission_guard.py
 M game/api.py
 M game/api_turn_support.py
 M game/bounded_improvisation.py
 M game/dialogue_social_plan.py
 M game/final_emission_gate.py
 M game/final_emission_response_type.py
 M game/final_emission_strict_social_stack.py
 M game/final_emission_visibility_fallback.py
 M game/gm.py
 M game/gm_retry.py
 M game/intent_parser.py
 M game/interaction_context.py
 M game/interaction_routing.py
 M game/models.py
 M game/narration_state_consistency.py
 M game/noncombat_resolution.py
 M game/perception_grounding.py
 M game/playability_eval.py
 M game/prompt_context.py
 M game/response_policy_enforcement.py
 M game/scene_destination_binding.py
 M game/social.py
 M game/social_exchange_emission.py
 M game/social_exchange_fallback_catalog.py
 M game/social_exchange_policy.py
 M game/speaker_contract_enforcement.py
 M game/storage.py
 M game/upstream_response_repairs.py
 M handoff/CURRENT_REVIEW.md
 M handoff/CURRENT_REVIEW.zip
 M handoff/REVIEW_MANIFEST.json
 M tests/conftest.py
 M tests/helpers/reactive_player.py
 M tests/helpers/turn_pipeline_http_fixtures.py
 M tests/test_broad_address_social_bid.py
 M tests/test_exploration_resolution.py
 M tests/test_model_routing_escalation.py
 M tests/test_model_routing_runtime.py
 M tests/test_social.py
 M tests/test_social_exchange_emission.py
 M tests/test_social_question_relevance_answer_selection.py
 M tests/test_transcript_regression.py
 M tests/test_turn_pipeline_shared.py
 M tests/test_upstream_dependent_run_bhc2.py
 M tools/run_playability_validation.py
?? PR-BS_cooperative_gm_micro_live_validation.md
?? PR-BS_cooperative_realization_discovery.md
?? PR-BS_decision_facing_answer_recipe_implementation.md
?? PR-BT_epistemic_guidance_delta.json
?? PR-BT_policy_instruction_deduplication_implementation.md
?? PR-BT_policy_instruction_semantic_diff.md
?? PR-BT_provider_context_canonicalization_discovery.md
?? PR-BT_provider_deduplication_micro_live_validation.md
?? PR-BT_provider_payload_inventory.json
?? PR-BT_regression_completion_gate.md
?? PR-BT_selective_epistemic_guidance_differential_discovery.md
?? PR-BT_selective_epistemic_guidance_restoration_implementation.md
?? PR-BT_selective_epistemic_protocol_diff.md
?? PR-BT_selective_epistemic_restoration_final_micro_live.md
?? PR-BU_PR-BT_final_repaired_chain_micro_live.md
?? PR-BU_final_lexical_scope_false_rejection_repair.md
?? PR-BU_lexical_scope_control_flow_after.md
?? PR-BU_narration_claim_composition_repair.md
?? PR-BU_narration_validator_control_flow.md
?? PR-BU_narration_validator_control_flow_after.md
?? PR-BU_qualified_inference_complement_authorization.md
?? PR-BU_qualified_inference_control_flow_after.md
?? PR-BU_validator_semantic_matrix.json
?? PR-BU_validator_semantic_matrix_after.json
?? PR-BU_validator_semantic_matrix_complement_after.json
?? PR-BU_validator_semantic_matrix_lexical_scope_after.json
?? PR
```

Historical figures were not treated as current. The relevant regression selection from PR-EG-R4 was rerun in this worktree: 753 passed, 27 failed. The PR-EG-R4-R1 repaired JUnit had 25 failures. Failures whose test names are absent from that set: [
  {
    "name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_ownership_precedes_active_npc[SESSION-RULES-components1]",
    "kind": "failure",
    "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"
  },
  {
    "name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_confirmation_rejects_stale_scene",
    "kind": "failure",
    "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"
  }
].

Two of those names, when rerun alone, passed. Their first-run messages were Windows `PermissionError` on `session.json` replacement, not assertion changes.

Provider model for this qualification: `gpt-4.1-mini`. Flag: `ASHEN_UNIFIED_SEMANTIC_PLANNING`, default off. Existing flags `ASHEN_DISABLE_LIVE_INTERPRETATION`, `ASHEN_DISABLE_EXPRESSION_GENERATION`, and `ASHEN_DISABLE_PROVIDER_CALLS` remain the live-call switches.

Frozen holdout hash `2c1ae752be2eb9d31b04f3e6de9f8baa8da0cf57107dcade667a075883545032` matches the recorded freeze `2c1ae752be2eb9d31b04f3e6de9f8baa8da0cf57107dcade667a075883545032`: True. Bytes 5604.
