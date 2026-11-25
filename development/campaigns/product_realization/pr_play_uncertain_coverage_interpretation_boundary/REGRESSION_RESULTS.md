# Regression results

Commands (repository root, offline audit-guarded isolated stores):

```powershell
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/validate.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/validate_adapter.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/validate_grounding.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/run_regression.py combined
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/run_regression.py focused
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/baseline.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/after.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/controls.py
.venv/Scripts/python.exe -u artifacts/pr_play_uncertain_coverage_interpretation_boundary/benchmark.py
```

Combined: 455 passed / 17 failed / 472. Focused: 470 passed / 1 failed / 471. Both exactly match inherited failure identities from the authoritative previous/rebaseline selections; zero new or missing identities. No assertion weakened. Combined/focused launched as independent stores/processes. Final reference-validation tightening was followed by acceptance/adapter reruns; it cannot affect the old disabled path because that path has no record.

Combined inherited identities:

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

Focused inherited identity:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Pytest acceptance: 133/0; adapter: 9/0; strengthened grounding rerun: 4/0. JUnit XML, logs, command/result manifests and provider/network guards are included. Provider records and external network attempts: zero. Starlette/httpx deprecation and skipped upstream preflight warnings do not establish live readiness. No full-suite claim.
