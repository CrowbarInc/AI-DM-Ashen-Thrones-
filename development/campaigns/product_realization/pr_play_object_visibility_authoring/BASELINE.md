# Baseline

Milestone: `pr_play_object_visibility_authoring`. Date: 2026-11-09.

Branch `feature/product-realization`; HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Entry dirty status and all protected file hashes are in entry_git_status.txt/before_manifest.json. observation: 88 before / 88 after; inspection: 72 before / 72 after; marking: 76 before / 76 after; identity: 52 before / 52 after; inventory_snapshot: 50 before / 50 after; preservation: 143 before / 143 after.

Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failing identities: []; newly passing: [].

Supplemental disclosure before: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests); after: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests). New failures: [].

Exact current baseline failures:

- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock
- tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working
- tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver
- tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing
- tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid
- tests/test_perception_narration_authority_audible_non_invention.py::test_player_seeks_whisper_does_not_create_one
- tests/test_perception_narration_authority_audible_non_invention.py::test_http_empty_listen_complete_and_grounded
- tests/test_perception_narration_authority_audible_non_invention.py::test_http_authorized_speech_can_survive
- tests/test_pr_play_79df3_classification.py::test_duplicate_refusal_does_not_publish
- tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances
- tests/test_pr_play_79df3_classification.py::test_save_reload_keeps_the_preceding_publication
- tests/test_pr_play_79df3_classification.py::test_http_fallback_is_not_an_operational_refusal
- tests/test_pr_de_exact_contract_deduplication.py::test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context
- tests/test_pr_de_exact_contract_deduplication.py::test_full_context_classes_stay_unprojected_while_mirrors_drop
- tests/test_manual_play_latency.py::test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload

Verified-code discrepancies: original architecture proposed a session ledger; shipped ledger is character.object_marking_receipts to keep one-file atomicity. Architecture phase 3 described player inspection; shipped observation remains internal. Old exact marking validation rejected inert per-mark unknown fields; this cycle preserves them while validating required fields. Existing /api/character allowed raw visibility replacement; this cycle closes that specific client bypass. No frozen historical files were edited. Source inspection and complete pre-edit runs preceded production edits.
