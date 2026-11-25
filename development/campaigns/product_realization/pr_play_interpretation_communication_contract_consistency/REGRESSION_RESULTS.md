# Regression results

Final commands:

```
.venv/Scripts/python.exe artifacts/pr_play_interpretation_communication_contract_consistency/run_acceptance.py
.venv/Scripts/python.exe artifacts/pr_play_interpretation_communication_contract_consistency/run_regression.py combined_final
.venv/Scripts/python.exe artifacts/pr_play_interpretation_communication_contract_consistency/run_regression.py focused_final
```

Exact argv, environment, JUnit, logs and failure identities are retained in acceptance_command.json, final_acceptance.xml, acceptance_final_isolated.log, final_regression/combined_final_*.json and final_regression/focused_run/focused_final_*.json. Existing historical selection is copied by test path, with fresh isolated storage, distinct basetemp and external networking blocked. Tests were not weakened.

| Selection | Historical | Final | New identities |
|---|---|---|---|
| Combined | 455 pass / 17 inherited fail | 455 pass / 17 fail | 0 |
| Focused | 470 pass / 1 inherited fail | 470 pass / 1 fail | 0 |
| Scoped final acceptance | No claim of historical equivalent | 191 pass / 0 fail | 0 unresolved |

Combined exact remaining failures:

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

Focused exact remaining failures:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Resolved historical identities: []; focused []. Comparison is by identity, not counts alone. Guarded regression provider records: combined 0, focused 0; external network attempts 0. No live provider calls.

Earlier development attempts are retained: the first acceptance exposed two real contract gaps (unsupported tail accepted by fuzzy target normalization; board-content question spent a turn), both repaired. An overlapping acceptance run had one pytest basetemp FileExistsError, an environmental collision; final acceptance uses an explicit independent basetemp. Early regression-runner argument extraction accidentally included a pytest option value as a test path; corrected to copy only test paths before final runs. These are not hidden or counted as successful final runs. The final-source runs above supersede development runs.
