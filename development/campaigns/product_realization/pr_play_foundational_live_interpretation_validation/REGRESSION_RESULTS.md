# Regression verification

Commands from repository root:

```powershell
.venv/Scripts/python.exe -u artifacts/pr_play_foundational_live_interpretation_validation/run_regression.py combined
.venv/Scripts/python.exe -u artifacts/pr_play_foundational_live_interpretation_validation/run_regression.py focused
.venv/Scripts/python.exe -u artifacts/pr_play_foundational_live_interpretation_validation/validate.py
```

Exact historical combined/focused selectors reused from reliability-rebaseline manifests. Separate isolated storage and evidence sinks; external network audit blocked, provider interpretation/expression disabled, credentials cleared before imports; game.config may reload local configuration, while the network audit guard prevents external dispatch. No live tests added. No assertions weakened or production files edited.

Combined: 455 passed / 17 inherited failures. Focused: 470 passed / 1 inherited failure. Scoped repair/grounding/uncertain-boundary/consequence/narration acceptance: 245 passed. Both historical failure identity sets match exactly, zero new and zero missing identities. Zero provider records and external network attempts in both lanes; scoped integrity in final_acceptance_integrity.json. No full-suite claim.

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

Focused inherited identities:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`
