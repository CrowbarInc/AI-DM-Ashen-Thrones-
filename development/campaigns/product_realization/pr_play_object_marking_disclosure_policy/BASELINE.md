# Baseline

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

Branch `feature/product-realization`; HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Entry status: entry_git_status.txt. All 1587 protected source/test/data/tool hashes: before_manifest.json. Before edits, 72 inspection/removal, 76 marking/atomic, 52 identity, 50 inventory/snapshot and 143 preservation passed. Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failures: []; newly passing: [].

Exact baseline failures:

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

Code/report cross-check: object_marking.inspect_markings exposes full active records (including private authorization/request lineage) to trusted internal callers and validates historical receipts. It is not a player projection. Mark records have no visibility classification and exact MARK_FIELDS validation precludes casually appending per-mark fields. Existing row-level opaque fields are preserved. Identity validation is owned by object_instances; observation reuses its validator without copying receipt history. Existing context caller_id strings are trusted assertions, not authentication. No reset/clean/stash/revert/checkout/commit/push performed.
