# Regression results

| Selection | Before pass/fail | After pass/fail |
|---|---:|---:|
| Main, 235 | 222/13 | 222/13 |
| Authority, 146 | 139/7 | 139/7 |
| Pre-seal authority, 17 | 17/0 | 17/0 |
| Established baseline, 356 (excludes 25 mechanical cases) | 336/20 | 336/20 |
| Expanded audit, 381 | 361/20 | 361/20 |
| Expanded plus pre-seal, 398 | 378/20 | 378/20 |
| New composition, 15 | 7/8 | 15/0 |
| Combined post-repair, 413 | — | 393/20 |

Current entry hashes match all 1,294 predecessor hashes, including requirements.txt and pytest.ini. The fresh baseline matches the historical 378/20; it was not assumed. No changed old test outcomes, resolved old failures, new old-test failures, collection errors or skips. Failure identities and normalized diagnostics match; normalization only removes hyphenated UUIDs, generated 32-hex turn_id fields and hexadecimal object addresses. Full tracebacks and commands are preserved. The initial 15-test draft assumed no momentum tag. Scenario verification exposed the cadence dependency, so two assertions now require the existing new_information tag for the real clue. Final identical test bytes run against this cycle's preserved pre-edit enforcement function in memory (7/8) and final production (15/0); no historical files are checked out or overwritten. All intermediate results and the initial test draft remain preserved. This is a current-entry function replay, not a reopened historical provenance investigation. No old/frozen assertion is relabeled to excuse a regression.

Known failure identities:

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

The before authority runner was invoked with before/authority, and its existing /authority suffix produced before/authority/authority. This naming discrepancy does not change selection or results. A new test module was added while that pre-edit run was executing; its integrity log records only the addition, no preexisting-file mutation, and the collected historical nodes do not include it. The original focused/new-test before runs finish before production edits. The final new-test-source before replay loads only the preserved current-entry enforcement function in memory; final HTTP and all regression after runs use production unchanged.

All runners set provider-disable flags, block external sockets and isolate storage. Live provider calls **0**; network attempts **0**. Commands from repository root, .venv/Scripts/python.exe:

```powershell
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_sequence.py traced_before
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_sequence.py after_final
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_audit.py before
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_audit.py after_final
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_controls.py before/authority
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_controls.py after_final
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_focused.py focused_before
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_focused.py focused_final
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_composition.py new_before_final
.venv/Scripts/python.exe artifacts/pr_play_t05_composition/run_composition.py new_after_final
```

Exact pytest argument arrays and executable paths follow (also each command.json):

### before

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_79a_continuity.py",
    "tests/test_pr_eb_conversational_continuity.py",
    "tests/test_pr_eg_r1_continuity.py",
    "tests/test_referenced_surface_grounding_inspection_resolution.py",
    "tests/test_pr_play_39_action_admission.py",
    "tests/test_at_opt_02_retreat_and_budget.py",
    "tests/test_at_opt_04_mixed_key_policy.py",
    "tests/test_at_opt_06_instruction_eligibility.py",
    "tests/test_at_opt_06_same_scene_transition.py",
    "tests/test_narrative_planning_transition_node.py",
    "tests/test_prompt_context_transition_node_consumption.py",
    "tests/test_pr_ed_provider_efficiency.py",
    "tests/test_pr_br_continuation18_immutable_boundary.py",
    "tests/test_perception_narration_authority_audible_non_invention.py",
    "tests/test_pr_play_post_npc_handoff.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\before\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_main_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### before/authority/authority

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_46_mechanical_boundary.py",
    "tests/test_pr_play_79df3_classification.py",
    "tests/test_pr_play_79b_integration.py",
    "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate",
    "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone",
    "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome",
    "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context",
    "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop",
    "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\before\\authority\\authority\\recovery_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_authority_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### focused_before

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_preseal_authority.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\focused_before\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_focused_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### after_final

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_79a_continuity.py",
    "tests/test_pr_eb_conversational_continuity.py",
    "tests/test_pr_eg_r1_continuity.py",
    "tests/test_referenced_surface_grounding_inspection_resolution.py",
    "tests/test_pr_play_39_action_admission.py",
    "tests/test_at_opt_02_retreat_and_budget.py",
    "tests/test_at_opt_04_mixed_key_policy.py",
    "tests/test_at_opt_06_instruction_eligibility.py",
    "tests/test_at_opt_06_same_scene_transition.py",
    "tests/test_narrative_planning_transition_node.py",
    "tests/test_prompt_context_transition_node_consumption.py",
    "tests/test_pr_ed_provider_efficiency.py",
    "tests/test_pr_br_continuation18_immutable_boundary.py",
    "tests/test_perception_narration_authority_audible_non_invention.py",
    "tests/test_pr_play_post_npc_handoff.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\after_final\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_main_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### after_final/authority

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_46_mechanical_boundary.py",
    "tests/test_pr_play_79df3_classification.py",
    "tests/test_pr_play_79b_integration.py",
    "tests/test_pr_play_76_physical.py::test_flag_off_does_not_adjudicate",
    "tests/test_pr_play_79c_publication.py::test_step_back_after_approach_names_the_milestone",
    "tests/test_pr_play_79c_publication.py::test_physical_publication_matches_the_outcome",
    "tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context",
    "tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop",
    "tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\after_final\\authority\\recovery_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_authority_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### focused_final

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_preseal_authority.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\focused_final\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_focused_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### new_before_final

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_t05_composition.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\new_before_final\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_new_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

### new_after_final

```text
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
    "tests/test_pr_play_t05_composition.py",
    "-q",
    "--tb=long",
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_t05_composition\\new_after_final\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\t05_composition_new_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```
