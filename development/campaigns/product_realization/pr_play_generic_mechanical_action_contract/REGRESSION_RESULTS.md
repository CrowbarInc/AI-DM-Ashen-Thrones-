# Regression results

Selections come from the predecessor command files. The runner is `artifacts/pr_play_generic_mechanical_action_contract/run_regression.py`. Storage is isolated per phase. Live interpretation, expression generation, and provider retries are disabled. Upstream preflight is skipped. `ASHEN_DISABLE_PROVIDER_CALLS` is left unset so existing operational-refusal tests keep their previous environment. External sockets other than localhost are blocked. The new contract file is not inside these selections and is reported separately: 79 tests, exit 0, 80/80 evidence rows.

## Combined

| Phase | Tests | Passed | Failed | New identities | Missing identities | Provider records | Elapsed |
|---|---:|---:|---:|---|---|---:|---:|
| Predecessor | 472 | 455 | 17 | — | — | 0 | prior milestone |
| Before | 472 | 455 | 17 | none | none | 0 | 1027.8 s |
| After | 472 | 455 | 17 | none | none | 0 | 1149.2 s |

The before failure identities, unchanged from the predecessor:

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

No assertion in those files was weakened or deleted for this milestone. No frozen historical fixture was edited.

## Focused

| Phase | Tests | Passed | Failed | New identities | Missing identities | Provider records | Elapsed |
|---|---:|---:|---:|---|---|---:|---:|
| Predecessor | 471 | 470 | 1 | — | — | 0 | prior milestone |
| Before | 471 | 470 | 1 | none | none | 0 | 2082.1 s |
| After | 471 | 470 | 1 | none | none | 0 | 809.3 s |

The before and predecessor failure is only `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. Provider records on the before run: 0. External network attempts: 0. The after run uses the same selection.

Covered by those selections: campaign creation, campaign ruleset binding, ruleset registry, ruleset contract, Pathfinder equipment policy, character persistence, inventory identity, action admission, compound-action guard, travel, NPC retrieval, conversational continuity, marking, publication reconciliation, durable retries, save/reload, and existing Pathfinder mechanics. The exact node ids are the predecessor command JSON files.
