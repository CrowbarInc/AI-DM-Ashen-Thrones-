# Offline regression results

| Suite | Passed / failed | Inherited failures | New identities | Cleared vs preceding milestone | Changed diagnostics vs inherited | Changed diagnostics vs preceding |
|---|---:|---:|---:|---:|---:|---:|
| Combined regression | 455 / 17 | 17 | 0 | 4 | 11 | 10 |
| Focused regression | 470 / 1 | 1 | 0 | 0 | 1 | 1 |
| Scoped regression | 191 / 0 | 0 | 0 | 0 | 0 | 0 |
| Inspection admission | 64 / 0 | 0 | 0 | 0 | 0 | 0 |
| Statement ownership | 65 / 0 | 0 | 0 | 0 | 0 | 0 |
| NPC addressee and social commitment | 71 / 0 | 0 | 0 | 0 | 0 | 0 |
| Reconciliation acceptance | 37 / 0 | 0 | 0 | 0 | 0 | 0 |
| Historical recall | 71 / 0 | 0 | 0 | 0 | 0 | 0 |

All four legacy identities in [the reproduction report](FOUR_FAILURE_REPRODUCTION.md) executed and passed in the combined run. They are the complete set cleared from the immediately preceding failure list. The inherited combined and focused failure identities are retained.

The focused validation was restarted after correcting the diagnostic output directory setup. The complete focused JUnit in `evidence/final` supersedes the preliminary harness run.

The combined result has ten changed diagnostic messages compared with the preceding run, all due to process-specific Python object addresses. Compared with the older inherited baseline, those same address-bearing failures and one inherited refusal diagnostic differ. The inherited Gate Guard fallback fixture had the general speech refusal before the preceding milestone. It now gives the existing specific unresolved-person diagnostic.

The result JSONs include the exact before and after diagnostic text, historical identities and established selection arguments.

## Combined inherited failures

- `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`

Changed diagnostic identities compared with inherited

- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`

Changed diagnostic identities compared with previous

- `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`

## Focused inherited failures

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Changed diagnostic identities compared with inherited

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

Changed diagnostic identities compared with previous

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`
