# Regression results

The deterministic suite selections came from the established regression commands. Results below are passes / failures.

| Suite | Historical | Final | New failures | Removed failures |
|---|---:|---:|---:|---:|
| Combined | 455 / 17 | 455 / 17 | 0 | 0 |
| Focused | 470 / 1 | 470 / 1 | 0 | 0 |
| Scoped | 191 / 0 | 191 / 0 | 0 | 0 |
| Historical recall acceptance | 71 / 0 | 71 / 0 | 0 | 0 |

All inherited failure identities match. The combined suite has the same primary assertion signatures and ten differences in verbose diagnostics, including source offsets, display ordering, generated identifiers and expanded response payloads. The focused roll-initiative test still fails the canonical-resolution key check. Its first reported missing key changed from label to combat because the assertion iterates a frozenset. The JSON preserves the exact before and after messages. The historical recall harness reran its own frozen replay and matched all 71 case identities. The distinct exact live-capture continuity sequence is covered by the acceptance suite.

Combined inherited failures by file and test name
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

The focused inherited identity is `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`.

The result files and JUnit XML are under evidence/regression. The complete comparison is in evidence/regression_comparison.json. External network attempts and provider calls were zero.
