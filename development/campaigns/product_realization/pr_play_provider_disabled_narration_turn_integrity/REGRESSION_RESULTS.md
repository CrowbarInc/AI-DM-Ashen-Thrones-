# Regression

Commands:

```
python artifacts/pr_play_provider_disabled_narration_turn_integrity/run_regression.py combined_close
python artifacts/pr_play_provider_disabled_narration_turn_integrity/run_regression.py focused_close
python -m pytest tests/test_provider_narration_turn_integrity.py tests/test_unique_carried_object_reference.py tests/test_unmatched_person_reference.py tests/test_uncommitted_action_admission.py
```

63/63 acceptance and preservation tests; 21/21 independent gameplay checks across 14 HTTP requests. Combined: 455 passed / 17 failed. Focused: 470 passed / 1 failed. Exact failure identities match the recorded baseline; no new identities.

Combined: 472 tests, 162.5 seconds, exit 1; provider records 0, external attempts []. New identities: []; missing predecessor identities: [].

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

Focused: 471 tests, 307.8 seconds, exit 1; provider records 0, external attempts []. New identities: []; missing identities: [].

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Selections are loaded from the reliability-rebaseline command JSON. Frozen fixtures and historical expectations were not edited. An initial completed combined run was 454 passed / 18 failed, with one genuinely new identity: tests.test_pr_play_t05_composition::test_original_t05_http_acceptance_and_publication. The trace showed selected-information composition metadata was incorrectly conditional on a momentum clock that the now-withheld look-around no longer advanced. Moving that existing information-precedence guard before the due check repaired it; the original test was not weakened. The failed result and repaired composition tests are packaged. Earlier candidate combined/focused processes were interrupted while the boundary and a measured recent-action timestamp drift were refined; partial dots are not completed test counts. A first authoring run hit the deliberate live-call guard and is excluded. The new rain-barrel test initially expected generic recovery text; the existing finalizer correctly selected the exact authored visible fact. Its assertion now requires that exact grounded fact, committed search, one turn and failure metadata.

This does not certify the full repository. Failures are inherited only by exact recorded identity comparison.
