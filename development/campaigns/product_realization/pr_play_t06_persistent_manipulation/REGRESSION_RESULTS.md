# Regression results

| Selection | Result |
|---|---|
| Historical predecessor reference | 408 passed / 17 failed of 425 |
| Fresh pre-production-edit baseline | 405 passed / 20 failed / 0 errors / 0 skipped (425 tests) |
| Final same 425 selected nodes | 405 passed / 20 failed / 0 errors / 0 skipped (425 tests) |
| New diagnostic manipulation tests | 6 passed / 0 failed / 0 errors / 0 skipped (6 tests) |
| Existing physical/persistence/authority | 93 passed / 0 failed / 0 errors / 0 skipped (93 tests) |

New failure identities: []. Resolved fresh identities: []. Collection errors are recorded as errors in the above JUnit; live provider calls 0. No production change exists to credit for differing results. Predecessor fluctuations are not repairs.

Commands (repository root):

```powershell
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py entry
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py baseline
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py before
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py persistence_controls
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py focused
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py final
.venv/Scripts/python.exe artifacts/pr_play_t06_persistent_manipulation/investigate.py after
```

The runner records executable and every exact pytest argument in *_command.json. The module/selected-node arguments come from predecessor main/authority commands plus pre-seal/T05/T04 modules; collection is asserted equal to all 425 predecessor JUnit node identities. Its tests include conversational handoff, inventory/mechanical, travel/transition, pre-seal closed-inspection, T04 and T05 controls. Tests run with fail-closed external-network and protected production-data guards; fixtures can use local provider stubs. Live providers are disabled and client construction is forbidden by existing pytest fixtures. Initial harness attempts hit the evidence-directory write guard before test execution; corrected to this cycle's evidence directory without weakening the guard. Two attempts passing all 425 individual node names stalled during collection and were interrupted without a completed test result; those aborted argument lists are retained in *_aborted_node_command.json. The established module arguments complete collection and verify the exact same node set. These setup/collection attempts are not passing or failing regression results.

Fresh baseline versus predecessor: new identities ["tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish", "tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication", "tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances"]; not reproduced []. Any differences predate production edits (none were made) and receive no repair credit.

The three recurring greeting/refusal cases are explicitly listed as previously failing (not repaired) in T04 REGRESSION_RESULTS.md. Fresh diagnostics repeat its events-file assertion, AnyIO portal RuntimeError, and missing OPERATIONAL_REFUSAL log entry. These are historical fluctuations relative to 408/17, not new failures caused by T06. Full exact assertions remain in the fresh JUnit.

Final failure identities:

- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working`
- `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing`
- `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded`
- `tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive`
- `tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish`
- `tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances`
- `tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication`
- `tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal`
- `tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`

Full diagnostics in baseline_junit.xml/after_junit.xml and logs; exact fresh differences in test_results.json. No full-suite, live-model, independent-generalization or gameplay benchmark claim.
