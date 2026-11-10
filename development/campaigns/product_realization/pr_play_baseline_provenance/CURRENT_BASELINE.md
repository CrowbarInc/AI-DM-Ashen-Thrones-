# Current development baseline

Milestone `pr_play_baseline_provenance`. **Established for the exact selections below.** Capture `2026-11-09T01:15:10.953631+00:00`; branch `feature/product-realization`; HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Worktree dirty. Source aggregate SHA-256 `02fb4ccf8ae2d016aef1ba6b2d140279c04285e734cedf56764f8f3a1c8cf151`. Source snapshot SHA-256 `77b551a3ab7b9f2e22a5e243d15e53814b51563e21f541216429cf7609be73e5`. Local dependency versions recorded; no installation or provider changes.

356 tests: 333 passed, 23 failed, zero errors/skips. First run 219/235 passed, 16 failed. Second run 114/121 passed, 7 failed. Exact collected node IDs/outcomes/durations and source binding are in `test_results.json`; failures retain complete tracebacks. Sequential pytest execution, isolated runtime storage, test fixture model stubs, production provider dispatch disabled, nonloopback network blocked. Loopback remains available for Windows asyncio/TestClient. Both runs report no protected changes, additions or external connection attempts.

## Selections and commands

Run from repository root with `.\.venv\Scripts\python.exe artifacts/pr_play_baseline_provenance/run_baseline.py`, then `run_authority.py`. These evidence scripts apply the recorded flags and guards before imports and call pytest with these exact arguments. Basetemp directories are cycle-owned disposable paths; historical output paths must not be reused as basetemp.

```json
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
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_baseline_provenance\\baseline_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\baseline_provenance_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

```json
{
  "executable": "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
  "args": [
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
    "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_baseline_provenance\\authority\\recovery_junit.xml",
    "--basetemp=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\baseline_authority_pytest",
    "-p",
    "no:cacheprovider"
  ]
}
```

The original 176 adjacent tests remain 164 passed / 12 failed; all seven post-NPC controls pass. The two expanded immutability/perception modules add 52 tests: 48 pass / four fail. The separate formerly green 118-test authority/publication selection is now 114 passed / four failed; three explicitly selected known KeyError tests also fail, making 114/121 passing in that run. One call-phase failure is a TestClient portal exception. The four newly failing authority nodes were rerun once sequentially with captures; all four failed again, including the repeated TestClient portal exception; exact results: `{"name": "pytest", "errors": "0", "failures": "4", "skipped": "0", "tests": "4", "time": "29.624", "timestamp": "2026-11-08T20:23:38.878707-05:00", "hostname": "DESKTOP-NG8DRCH"}`. Follow-up commands/results/captures are under authority_followup and in test_results.json. This is current baseline evidence, not proof of which prior edit caused the differences. AT-OPT-06 same-scene/real-transition protection remains covered by the original focused slice. Accepted-text retry/fallback/preservation and sensory-grounding unit controls pass in their exercised cases, subject to the failures listed below.

## Failure classifications

| Exact assertion/test identity | Baseline classification |
|---|---|
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_abstract_reference_does_not_become_physical` | known publication-authority defect |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_hidden_object_is_not_revealed_by_naming` | known publication-authority defect |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_creates_no_world_facts` | known publication-authority defect |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock` | known obsolete assertion |
| `tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working` | known obsolete assertion |
| `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver` | known obsolete assertion |
| `tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing` | known obsolete assertion |
| `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid` | newly observed response mismatch; historical origin unverified |
| `tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one` | newly observed obsolete assertion (PR-PLAY-67 public resolution) |
| `tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded` | newly observed obsolete assertion (PR-PLAY-67 public resolution) |
| `tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive` | newly observed obsolete assertion (PR-PLAY-67 public resolution) |
| `tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish` | newly observed authority/publication mismatch; historical origin unverified |
| `tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances` | newly observed TestClient portal exception; follow-up recorded separately |
| `tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication` | newly observed authority/publication mismatch; historical origin unverified |
| `tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal` | newly observed authority/publication mismatch; historical origin unverified |
| `tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context` | known unrelated failure (AT-OPT-06 recorded KeyError) |
| `tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop` | known unrelated failure (AT-OPT-06 recorded KeyError) |
| `tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload` | known unrelated failure (AT-OPT-06 recorded KeyError) |

The nine original and three newly observed public-resolution failures concern stopping assertions conflicting with PR-PLAY-67. Assertions after those stopping points remain unexecuted; prose quality is not accepted by classification. The new raw-chat mismatch expects a stew-cost inability sentence and receives `Tavern Runner mutters, "Word is, hot stew and rumors for coin."` Historical origin and full semantic implications are unverified; it is not attributed to this cycle or the conversational repair. Additional authority failures involve duplicate-refusal publication, two-refusal progression (initial portal exception), save/reload refusal-log classification, and fallback last-publication behavior. The follow-up preserves exact responses/state and distinguishes repeated mismatches from the initial transport exception; these are unresolved current-baseline findings, not confirmed new regressions. The three known unrelated failures are the recorded provider_context_projection, gm_only and social_context KeyErrors. No expectation was changed.

## Current behavior and limits

T04 local-object approach, T05 authorized notice disclosure, T06 unsupported physical-action routing and T09 grounded notice recall pass. Explicit NPC repetition, genuine NPC follow-up, unknown destination, hidden information, genuine travel and publication refusal remain verified in seven unchanged focused HTTP tests.

T04/T06 lack meaningful physical completion. T05 still appends the unrelated stock jab sentence. Other turns in the twelve-turn scenario remain inadequate; that full scenario was not rerun. No playability, full-suite, live-model or independent-generalization claim is made.

Passing behavior, obsolete assertions, known publication defects, known unrelated failures, newly observed failures and unverified behavior are separate categories in machine evidence. Provider-free stubs demonstrate production publication-path behavior, not the frequency of live-model invention. No full frozen holdout rerun is claimed; frozen fixtures/results remain preserved. A failing baseline is usable when source identities and exact failure identities are preserved; it is not acceptance of those defects.
