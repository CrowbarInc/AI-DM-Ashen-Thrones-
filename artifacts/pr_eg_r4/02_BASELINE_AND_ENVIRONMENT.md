# 02 — Baseline and Environment

Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Pre-existing dirty tree: `initial_git_status.txt`. Hashes of game, tests and campaign saves are in `environment.json`; preservation comparison is in `preservation_check.json`. A Git revision alone does not reproduce this working tree.

Python: 3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]; Windows-11-10.0.26200-SP0. Installed dependency versions: `dependency_versions.json`.

Safe configuration:

```json
{
  "MODEL_NAME": "gpt-4.1-mini",
  "DEFAULT_MODEL_NAME": null,
  "HIGH_PRECISION_MODEL_NAME": null,
  "RETRY_ESCALATION_MODEL_NAME": null,
  "ENABLE_MODEL_ROUTING": null,
  "ASHEN_DISABLE_PROVIDER_RETRIES": null
}
```

Provider: OpenAI Responses API. Engine configured gpt-4.1-mini; exact returned model IDs and request IDs preserved in usage logs. Player: gpt-4.1-mini; independent provider evaluator: gpt-4.1. No credentials included.

Live subprocess: provider/interpretation/expression enabled, upstream startup preflight skipped, timeout 45 seconds, explicit token/request ceilings, ASHEN_DATA_DIR points to disposable import state. SDK and production retry behavior unchanged. Narration routing uses current production configuration. Test defaults disable live calls.

Three new fixture overlays use the existing PR-EF/PR-DU courtyard seed; no active factions, avoiding unrelated passive agendas. Each independent conversation is seeded anew. Midpoint persistence and client recreation are recorded, not a full process-restart test.

Relevant baseline:

```json
{
  "counts": {
    "passed": 692,
    "failed": 25
  },
  "prior_counts": {
    "passed": 692,
    "failed": 25
  },
  "inherited": [
    "tests.test_by3_strict_social_semantic_mutation::test_by3_generate_repo_artifacts",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_report_schema_and_gap_closure",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_strict_social_hidden_mutation_detected",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_writer_raw_checkpoint_present_on_strict_social_turn",
    "tests.test_by3_strict_social_semantic_mutation::test_by3_wrong_speaker_fixture_has_attributable_trace",
    "tests.test_exploration_resolution::test_chat_exploration_parsed_routes_through_exploration",
    "tests.test_exploration_resolution::test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution",
    "tests.test_exploration_resolution::test_chat_observe_area_resolution_kwarg_to_build_messages",
    "tests.test_exploration_resolution::test_chat_quarterstaff_attack_mechanical_resolution_absent",
    "tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance",
    "tests.test_turn_pipeline_shared::test_chat_active_target_direct_command_routes_to_social_exchange",
    "tests.test_turn_pipeline_shared::test_chat_fallback_preserves_endpoint_specific_no_resolution_shape",
    "tests.test_turn_pipeline_shared::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels",
    "tests.test_turn_pipeline_shared::test_chat_known_follow_up_bypasses_uncertainty_fallback",
    "tests.test_turn_pipeline_shared::test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane",
    "tests.test_turn_pipeline_shared::test_chat_mixed_turn_preserves_embedded_adjudication_metadata",
    "tests.test_turn_pipeline_shared::test_chat_repeated_interruption_progresses_without_losing_dialogue_contract",
    "tests.test_turn_pipeline_shared::test_chat_social_exchange_blocks_advisory_prose_before_emit",
    "tests.test_turn_pipeline_shared::test_chat_social_exchange_invalid_blob_is_repaired_before_emit",
    "tests.test_turn_pipeline_shared::test_chat_social_pressure_line_prefers_dialogue_over_adjudication",
    "tests.test_turn_pipeline_shared::test_chat_targeted_retry_prefers_highest_priority_failure_first",
    "tests.test_turn_pipeline_shared::test_chat_targeted_retry_unresolved_question_only",
    "tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback",
    "tests.test_turn_pipeline_shared::test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback",
    "tests.test_turn_pipeline_shared::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback"
  ],
  "new": [],
  "resolved": []
}
```
