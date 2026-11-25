# Regression results

Combined historical selection, before and after: **455/472 passed, 17 failed → 455/472 passed, 17 failed**. Exact failure identities match, new identities [].

Expanded focused selection: **470/471 passed, 1 failed → 470/471 passed, 1 failed**. The inherited failure is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution` (resolution missing `kind`). This was present before implementation. New focused failure identities []. The predecessor's 331-test focused subset remains passing within this selection; added coverage includes rules contracts, combat, skill checks, save/load, observation portability and authored retrieval. Importer coverage is separately in the new policy suite.

New policy tests are separate: **56/56 passed**, including 53 deterministic matrix cases and three aggregate/import/definition controls.

Commands: `.venv/Scripts/python.exe artifacts/pr_play_ruleset_equipment_policy_foundation/verify_gate.py combined_before` (and `combined_after`, `focused_before`, `focused_after`, `policy`). Exact pytest selections, environment, XML, logs, elapsed times, network audit and provider records are in the corresponding `_command.json`, `.xml`, `.log`, `_result.json` files. Both regressions ran in isolated development/tmp storage. External sockets/DNS were blocked, credentials removed, live interpretation/expression/retries/preflight disabled; experimental physical adjudication unset. Provider records and blocked external attempts: **0** for every completed selection. Regression tests may use local stubs.

The pre-existing modules were captured before implementation. Baseline processes started before the new module was written; neither selection imports the standalone policy. No existing assertion or fixture was changed.

Exact combined failures:

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
