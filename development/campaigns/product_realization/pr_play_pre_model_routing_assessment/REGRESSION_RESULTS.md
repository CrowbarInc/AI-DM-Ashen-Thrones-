# Current regression results

Commands (repository root):

```powershell
.venv/Scripts/python.exe -u artifacts/pr_play_pre_model_routing_assessment/run_regression.py combined
.venv/Scripts/python.exe -u artifacts/pr_play_pre_model_routing_assessment/run_regression.py focused
.venv/Scripts/python.exe -u artifacts/pr_play_pre_model_routing_assessment/assess.py
.venv/Scripts/python.exe artifacts/pr_play_pre_model_routing_assessment/benchmark.py
```

Copied the established offline regression runner into this milestone and changed only output/temp ownership. Selections are loaded verbatim from reliability-rebaseline command manifests. Combined/focused ran as independent processes/stores. Each pytest selection exits 1 due to inherited failures; runner comparison exits 0 when no new failure identities appear. No assertion or production repair was changed.

Combined: **455 passed / 17 failed / 472 collected**, elapsed 176.443s. Focused: **470 passed / 1 failed / 471 collected**, elapsed 316.599s. New identities: 0 combined, 0 focused. Historical missing identities: 0 / 0. Provider records 0 / 0; external network attempts 0 / 0. This reproduces historical combined 455/17 and focused 470/1 by identities, not counts alone.

Combined failures:

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

Focused failures:

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

JUnit XML contains exact current assertions. These are inherited product/contract test disagreements recorded by the baseline; no new environmental collection failures occurred. Existing Starlette/httpx deprecation and deliberately skipped upstream preflight warnings are environmental diagnostics, not live readiness evidence.

Assessment instrumentation setup: the initial launch was refused by the storage guard because the new evidence directory had not been explicitly configured. Fixed only the driver evidence-root environment before imports. An initial instrument had no worker-thread profiling; it was superseded with threading profiling and an explicit sentinel call counter (HTTP middleware can convert sentinel exceptions into generic error JSON). Added a Prayer book control and accessible-door control before the final matrix. The reported final 72 traces contain no execution errors, no external attempts, no provider records and unchanged protected hashes. These were offline instrument corrections, never repeated live calls. The final matrix supersedes intermediate trace files.

No full-suite or gameplay-benchmark claim. Current regression tests are unchanged; the new matrix is an observational assessment, not a repair acceptance pass.
