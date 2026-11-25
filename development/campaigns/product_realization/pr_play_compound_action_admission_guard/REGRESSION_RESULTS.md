# Regression results

Combined exact same selection/environment: 425 tests, **408 passed /17 failed before and after**, zero errors, identical failure sets. `regression_comparison.json` contains all identities; no new/resolved identities. Commands, XML and logs are retained. Invalid initial missing-basetemp-parent run is separately labeled in BASELINE.

Original focused 19 modules: **611 passed /0 failed**. Expanded final focused 25 modules: **744 passed /2 failed** among 746 cases. Inherited failures: ordinary semantic negated-travel wording (fresh saved-source baseline 8/9, same failure) and classification HTTP fallback (also in combined baseline). No assertion weakened. `focused_final_summary.json` distinguishes subprocess return status from authoritative pytest status; an early harness exit propagation bug has been fixed.

Dedicated guard + parser + destination selection: 96 cases, **95 passed /1 failed**; all **29 new guard tests pass**. The sole destination Stone Boar failure reproduces on saved pre-change source: 66/67 parser/destination cases, same identity. See baseline_extra and dedicated_verified XML. Supplemental tests are not counted as newly passing existing tests.

Failure identities (combined):
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

Live provider calls zero. Controlled HTTP budget records zero. Focused at-gate budget tests leave two ledger records from local `invoke()` stubs returning `_usage(...)`; no SDK calls or external socket attempts. No global experimental physical gate; individual existing tests exercise their own scoped gates. Machine evidence: `artifacts/pr_play_compound_action_admission_guard/` (repository relative). Final sources: `game/api.py`, `game/conversational_orchestration.py`; tests: `tests/test_compound_action_admission.py`. Task-start snapshots and milestone-only diffs preserve the distinction from earlier dirty work.
