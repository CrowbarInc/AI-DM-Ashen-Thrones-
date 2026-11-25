# Offline regressions

| Suite | Previous passes / failures | Current passes / failures | New identities | Removed identities | Changed inherited messages |
|---|---:|---:|---:|---:|---:|
| Combined | 455 / 17 | 451 / 21 | 4 | 0 | 11 |
| Focused | 470 / 1 | 470 / 1 | 0 | 0 | 0 |
| Scoped | 191 / 0 | 191 / 0 | 0 | 0 | 0 |
| Inspection | 64 / 0 | 64 / 0 | 0 | 0 | 0 |
| Ownership | 65 / 0 | 65 / 0 | 0 | 0 | 0 |
| Historical recall | 71 / 0 | 71 / 0 | 0 | 0 | — |
| New milestone acceptance | — | 71 / 0 | — | — | — |

Each result JSON includes the exact JUnit identities, original and current diagnostic messages, the established selection and final source hashes. All suites ran offline. No external network transport attempt was recorded.

## New failure identities

- `tests.test_pr_eb_conversational_continuity::test_pr_eb_active_npc_followup_routes_to_existing_social_resolver`
- `tests.test_pr_play_post_npc_handoff::test_explicit_repetition_stays_with_the_captain`
- `tests.test_pr_play_post_npc_handoff::test_recorded_handoff_leaves_the_previous_npc_line`
- `tests.test_pr_play_t04_local_action::test_l_npc_dialogue_is_not_fixture_contact`

The active-Mara case expects the bare “Which captain?” fragment to execute as dialogue. Its fixture sets interaction focus without a delivered exchange that establishes what the fragment is following up on. The other three cases start with a seeded publication attributed to “Gate Guard”, with no grounded Guard Captain exchange. They expect “You mentioned the patrol. What have you heard?” to acquire the captain and publish his line. The host now declines to assign that addressee. The new handoff control uses a genuinely resolved captain exchange and exercises the same follow-up and subsequent notice recall.

The old tests and assertions were preserved. The new failures are compatibility expectations at the repaired boundary. The altered inherited messages are retained verbatim in `evidence/delivery/*/result.json`.

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

## Focused inherited failures

- `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`
