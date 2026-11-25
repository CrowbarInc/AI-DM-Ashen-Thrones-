# Regression results

| Suite | Baseline pass/fail | Final pass/fail | New | Prior failures absent |
|---|---:|---:|---:|---:|
| Combined | 455/17 | 455/17 | 0 | 0 |
| Focused | 470/1 | 470/1 | 0 | 0 |
| Scoped | 191/0 | 191/0 | 0 | 0 |
| Additional continuity | 180/16 | 180/16 | 0 | 0 |

## Combined

- Inherited `tests.test_manual_play_latency::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`
- Inherited `tests.test_perception_narration_authority_audible_non_invention::test_http_authorized_speech_can_survive`
- Inherited `tests.test_perception_narration_authority_audible_non_invention::test_http_empty_listen_complete_and_grounded`
- Inherited `tests.test_perception_narration_authority_audible_non_invention::test_player_seeks_whisper_does_not_create_one`
- Inherited `tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- Inherited `tests.test_pr_de_exact_contract_deduplication::test_full_context_classes_stay_unprojected_while_mirrors_drop`
- Inherited `tests.test_pr_de_exact_contract_deduplication::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context`
- Inherited `tests.test_pr_play_39_action_admission::test_sequence_patrol_travel_reaches_the_movement_resolver`
- Inherited `tests.test_pr_play_39_action_admission::test_sequence_unsupported_actions_invent_nothing`
- Inherited `tests.test_pr_play_79df3_classification::test_http_fallback_is_not_an_operational_refusal`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_frontier_gate_roster_http_does_not_use_observe_stock`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_general_authored_alias_binds`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_general_failed_inspection_then_observe_uses_current_scene`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_general_narration_only_object_does_not_gain_authority`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_general_readable_surface_communicates_contents`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_general_unknown_player_named_object_is_not_instantiated`
- Inherited `tests.test_referenced_surface_grounding_inspection_resolution::test_observe_stock_replacement_keeps_notice_board_working`

## Focused

- Inherited `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`

## Scoped

All test identities passed.

## Additional continuity

- Inherited `tests.test_followup_topic_continuity_public_clue_paraphrase::test_they_go_and_who_did_it_do_not_inherit_watch_last_answer`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_T17_actual_http_pending_clarification[Can you repeat that?]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_T17_actual_http_pending_clarification[Say that again in simpler words.]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_T17_actual_http_pending_clarification[What did you mean by that?]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T05-I ask Sergeant Mara about that place.-annotations4-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T06-I ask one of them about the north gate.-annotations5-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T09-I ask Sergeant Mara about the absent king.-annotations6-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T10-I ask Sergeant Mara who made the north gate.-annotations2-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T11-I ask Sergeant Mara what the north gate password is.-annotations3-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T14-I ask Sergeant Mara whether guards watch the north gate at night.-annotations0-Guards watch the north gate throughout the night.]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_http_resolver_handoff[T25-I ask Sergeant Mara whether guards watch the north gate at night.-annotations1-Guards watch the north gate throughout the night.]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_irrelevant_annotations_reach_existing_resolver[obsidian palace]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_irrelevant_annotations_reach_existing_resolver[weather]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_structured_role_and_stale_status_http[CLARIFICATION_REQUIRED-refs1-sergeant_mara]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_structured_role_and_stale_status_http[CLARIFICATION_REQUIRED-refs2-None]`
- Inherited `tests.test_pr_eg_r2c_r2_reference_eligibility::test_structured_role_and_stale_status_http[INTERPRETED-refs0-None]`

The additional continuity comparison uses an isolated import of the three pre-change source modules, with exact bytes verified against the prior milestone hash inventory. Current and baseline runners preserve the same test selection and storage/network guards.
