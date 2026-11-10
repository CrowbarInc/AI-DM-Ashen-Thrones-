# Regression results

Before production edits: branch/HEAD/dirty status saved; all 1,294 predecessor source-manifest hashes match. Two historical selections rerun unchanged with fail-closed nonloopback network guards, provider disable flags, and existing storage isolation. Original three defects reproduce in the first selection. No reset/reconstruction was used.

| Selection | Before | After | Collection errors/skips |
|---|---:|---:|---:|
| Main, 235 | 219 pass / 16 fail | 222 pass / 13 fail | 0/0 |
| Authority, 146 (121 established + 25 mechanical) | 139/7 | 139/7 | 0/0 |
| Established, 356 | 333/23 | 336/20 | 0/0 |
| Expanded, 381 | 358/23 | 361/20 | 0/0 |
| Added final, 17 | See draft note | 17/0 | 0/0 |
| Existing + added, 398 | — | 378/20 | 0/0 |

Newly failing assertions: **none**. Resolved identities (all original HTTP publication defects):

- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_abstract_reference_does_not_become_physical`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_creates_no_world_facts`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_hidden_object_is_not_revealed_by_naming`

Unchanged known failures:

- `tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one`
- `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing`
- `tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish`
- `tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal`
- `tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication`
- `tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working`

All twenty retained failures have identical assertion/raise identities and normalized diagnostics. Only generated turn_id UUIDs and hexadecimal object addresses are normalized; full raw tracebacks remain intact. Known categories: twelve obsolete public-resolution assertions, one stew mismatch, four authority/refusal/publication nodes (including the known AnyIO portal exception), three unrelated KeyErrors. No new failure is declared obsolete to excuse a regression.

Added-test draft: 6/11 before implementation; first after run 14/3. The three new HTTP assertions incorrectly required total world equality, while both unchanged baseline and after captures show normal faction pressure/event-log updates. The final assertions compare every other world key, character, event content, resolution, hidden state and publication. Final 17/17. Tests were authored during this repair; no frozen fixture/old assertion was edited. All intermediate commands, JUnit, traces and source draft remain available; draft/final counts are not an exact same-test-source improvement claim.

Commands from repository root, .venv/Scripts/python.exe:

```powershell
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_audit.py before
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_controls.py before
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_audit.py after
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_controls.py after
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_focused.py focused_final
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_sequence.py before
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/run_sequence.py after
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/analyze_results.py
.\.venv\Scripts\python.exe artifacts/pr_play_preseal_authority/compare_assertions.py
```

Exact pytest module/node selections, flags, basetemp, collected IDs and executable are in each run's command.json/collected_nodes.json; copied from the predecessor selection without changing old tests. The three original HTTP cases are part of main; controls include conversational handoff, immutable/mechanical authority, negative controls and AT-OPT-06 transition tests. Scripts use separate cycle outputs and isolated storage and execute sequentially. Each execution integrity report records zero protected-file modifications and external network attempts. Live provider calls: **0**. No full-suite, live-model or Gameplay Benchmark run.

Machine results: test_results.json and assertion_comparison.json under artifacts/pr_play_preseal_authority/.
