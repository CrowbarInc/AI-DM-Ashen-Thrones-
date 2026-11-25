# Regression verification

Final commands (repository root):

```powershell
.venv/Scripts/python.exe -u artifacts/pr_play_unresolved_action_consequence_integrity/validate_final.py
.venv/Scripts/python.exe -u artifacts/pr_play_unresolved_action_consequence_integrity/run_regression.py combined_final
.venv/Scripts/python.exe -u artifacts/pr_play_unresolved_action_consequence_integrity/run_regression.py focused_final
.venv/Scripts/python.exe artifacts/pr_play_unresolved_action_consequence_integrity/reproduce.py final_after
.venv/Scripts/python.exe artifacts/pr_play_unresolved_action_consequence_integrity/benchmark.py
.venv/Scripts/python.exe artifacts/pr_play_unresolved_action_consequence_integrity/validate_truth.py
.venv/Scripts/python.exe artifacts/pr_play_unresolved_action_consequence_integrity/validate_controls.py
```

Acceptance/regression selection: 245 passed, zero failed. Includes prior A4/B1 boundary/real-adapter tests, compound/negation, carried-object and information/grounding controls, provider narration integrity, plus the new consequence tests. No assertions weakened. New test count and exact parametrizations are in final_acceptance.xml. Two canonical truth rechecks and all 39 scoped controls pass after test-only strengthening: true/false facts use canonical world_state.flags, and numbered evidence files preserve initial, duplicate and repeated snapshots instead of overwriting them. See controls_recheck.xml and controls_recheck/*.json. Production source was unchanged.

Combined: 455 passed / 17 inherited failures. Focused: 470 passed / 1 inherited failure. Zero new failure identities. Historical identities are compared as sets, not just counts, with the established reliability-rebaseline command/result manifests. Final selectors are unchanged. Interim runs are retained as developmental evidence; final_* results control the verdict.

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

External network audit guards record zero attempts. Provider records are zero in final regression lanes. Live preflight is intentionally skipped. No full-suite or gameplay-benchmark claim.
