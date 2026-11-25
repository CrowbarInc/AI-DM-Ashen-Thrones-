# Regression

Commands:

```
python artifacts/pr_play_controlled_model_intent_and_grounding_evaluation/run_regression.py combined_close
python artifacts/pr_play_controlled_model_intent_and_grounding_evaluation/run_regression.py focused_close
python -m pytest tests/test_controlled_model_intent_evaluation.py -q --tb=short -p no:cacheprovider
```

Selections and environment match the narration-turn-integrity runner, which loads the reliability-rebaseline command lists. Storage was isolated. External sockets other than loopback were audit-blocked. The API key was removed for these processes. `ASHEN_DISABLE_PROVIDER_CALLS` stayed unset, matching that runner. Live interpretation, expression generation, provider retries, and upstream preflight were disabled.

Combined: 472 tests, 455 passed / 17 failed, 435.5 seconds, exit 1. Provider records 0. External attempts: none. New identities: none. Missing predecessor identities: none.

Focused: 471 tests, 470 passed / 1 failed, 804.5 seconds, exit 1. Provider records 0. External attempts: none. New identities: none. Missing predecessor identities: none.

The single focused failure remains:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

The seventeen combined failures are the same identities recorded for `pr_play_ai_dm_reliability_rebaseline` and repeated by `pr_play_provider_disabled_narration_turn_integrity`:

- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`

No new regression. Tests were not weakened. The new harness file is outside those selections. Its five tests passed separately, with provider calls 0. This does not certify the full repository.
