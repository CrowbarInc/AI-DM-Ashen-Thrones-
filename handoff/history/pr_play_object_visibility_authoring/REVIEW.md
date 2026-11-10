# Campaign

Campaign: PR-PLAY — Trusted Visibility Classification and Revision Lifecycle
Identifier: `pr_play_object_visibility_authoring`
Date: 2026-11-09
Generated: 2026-11-10T00:23:35.451217+00:00
Purpose: Bounded trusted authoring, persistence and integration planning

# Executive Summary

**A/PASS for bounded trusted internal classification.**

93 focused authoring tests passed. Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failing identities: []; newly passing: [].

observation: 88 before / 88 after; inspection: 72 before / 72 after; marking: 76 before / 76 after; identity: 52 before / 52 after; inventory_snapshot: 50 before / 50 after; preservation: 143 before / 143 after. Supplemental disclosure before: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests); after: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests). New failures: [].

Authoritative visible/concealed/restricted metadata now changes through one trusted internal operation, with stable object/mark IDs, preserved content/extensions, exact revision lifecycle and shared atomic durable receipts. Existing whole-character HTTP editing now refuses classification insertion/change/drop/rebinding; unchanged metadata survives reorder and ordinary edits. Its compare/save shares the existing lane and persistence guard so a concurrent edit cannot erase a classification. Historical snapshot observation and replay, negative authority, atomic failure and hidden-output controls pass. Twelve player-visible turns unchanged. Live provider calls **0**.

Trusted internal Python assertions only; no authenticated decision issuer or cryptographic grant. Upstream owns classification basis, access, physical eligibility and mechanics. Single-process FIFO/persistence guard; no multi-process lost-update, multi-file crash-atomic or global exactly-once across snapshot rollback guarantee. File fsync required; Windows directory fsync unavailable/best effort; permission-bit preservation does not guarantee custom ACL/ownership metadata. Receipts grow for the saved timeline lifetime; no pruning. No player observation, conversational marking/classification, T06 completion, fabricated equipment/materials or provider use. No full-suite, independent holdout, live-model or broad gameplay-improvement claim.

Exactly one recommended next milestone: `pr_play_grounded_marking_action_integration` — a bounded end-to-end player copy action over an explicitly established existing target, disclosed source and usable medium, with truthful missing-prerequisite handling for original T06. No general object-framework expansion.

Objective status: `A/PASS — bounded internal classification`.

# Changes Made

## Production changes

- game/api.py
- game/object_marking.py

## Validation changes

- 93 focused authoring tests passed.

## Tooling changes

- Cycle-local guarded runner and evidence/archive scripts

## Documentation changes

- 15 reports; historical NEXT_SESSION retained

## Generated artifacts

- Bounded evidence and fresh standard review exports

# What Was Tested

- **Focused tests:** 93 focused authoring tests passed.
- **Broader relevant tests:** Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failing identities: []; newly passing: []. observation: 88 before / 88 after; inspection: 72 before / 72 after; marking: 76 before / 76 after; identity: 52 before / 52 after; inventory_snapshot: 50 before / 50 after; preservation: 143 before / 143 after. Supplemental disclosure before: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests); after: 238 passed / 2 failed / 0 errors / 0 skipped (240 tests). New failures: [].
- **Full suite:** Not run
- **Runtime validation:** Real atomic failures/reload/snapshot timelines and unchanged twelve HTTP turns
- **Model/runtime boundary:** Zero provider calls; disabled providers and non-loopback audit guard
- **New regressions:** []
- **Pre-existing failures:** - tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated
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
- **Self-contained bundle review:** CRC, canonical/evidence hashes, classification/authority/replay/persistence/disclosure/regression/T06/handoff claims reopened.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No further authorization required for this bounded implementation.

# Known Problems / Unresolved Findings

## Campaign-specific

- Trusted internal Python assertions only; no authenticated decision issuer or cryptographic grant. Upstream owns classification basis, access, physical eligibility and mechanics. Single-process FIFO/persistence guard; no multi-process lost-update, multi-file crash-atomic or global exactly-once across snapshot rollback guarantee. File fsync required; Windows directory fsync unavailable/best effort; permission-bit preservation does not guarantee custom ACL/ownership metadata. Receipts grow for the saved timeline lifetime; no pruning. No player observation, conversational marking/classification, T06 completion, fabricated equipment/materials or provider use. No full-suite, independent holdout, live-model or broad gameplay-improvement claim.

## Pre-existing baseline

- Combined and supplemental unchanged baseline failure identities; see regression report.

# Missing Concepts / Future Capabilities

- Grounded player marking action and observation/publication integration.

# What This Campaign Does NOT Prove

- T06 completion, authenticated public grants, full suite, live-model or gameplay improvement.

# Recommended Next Step

Exactly one recommended next milestone: `pr_play_grounded_marking_action_integration` — a bounded end-to-end player copy action over an explicitly established existing target, disclosed source and usable medium, with truthful missing-prerequisite handling for original T06. No general object-framework expansion.

# Review Bundle Contents

Bundle file count: `227`
Bundle ZIP size: `000004748113` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/AUTHORITY_INTEGRATION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/AUTHORITY_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/BASELINE.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/BASELINE.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/IDEMPOTENCY_VERIFICATION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/IDEMPOTENCY_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/INTEGRITY.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/NEGATIVE_CONTROLS.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/NEGATIVE_CONTROLS.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/NEXT_STEP_DECISION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/OBSERVATION_INTEGRATION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/OBSERVATION_INTEGRATION.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/PERFORMANCE.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/PERFORMANCE.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/PERSISTENCE_VERIFICATION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/PERSISTENCE_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/REGRESSION_RESULTS.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/RULESET_PORTABILITY.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/RULESET_PORTABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/T06_INTEGRATION_MAP.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/T06_INTEGRATION_MAP.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/TWELVE_TURN_COMPARISON.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/TWELVE_TURN_COMPARISON.md`.
- `support/development/campaigns/product_realization/pr_play_object_visibility_authoring/VISIBILITY_CONTRACT.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `development/campaigns/product_realization/pr_play_object_visibility_authoring/VISIBILITY_CONTRACT.md`.
- `support/docs/NEXT_SESSION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/state_authority_model.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `docs/state_authority_model.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/review_handoff_standard.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `docs/review_handoff_standard.md`.
- `support/game/api.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/api.py`.
- `support/game/storage.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/storage.py`.
- `support/game/object_marking.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/object_marking.py`.
- `support/game/object_instances.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/object_instances.py`.
- `support/game/object_observation.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/object_observation.py`.
- `support/game/conversational_orchestration.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/conversational_orchestration.py`.
- `support/game/intent_parser.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/intent_parser.py`.
- `support/game/physical_adjudication.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/physical_adjudication.py`.
- `support/game/exploration.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/exploration.py`.
- `support/game/skill_checks.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/skill_checks.py`.
- `support/game/narration_authorization.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/narration_authorization.py`.
- `support/game/player_http_projection.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/player_http_projection.py`.
- `support/game/immutable_valid_response.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/immutable_valid_response.py`.
- `support/game/publication_contract.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/publication_contract.py`.
- `support/game/state_authority.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `game/state_authority.py`.
- `support/tests/test_object_visibility_authoring.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `tests/test_object_visibility_authoring.py`.
- `support/artifacts/pr_play_object_visibility_authoring/absence_semantics.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/absence_semantics.json`.
- `support/artifacts/pr_play_object_visibility_authoring/acceptance_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/acceptance_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/acceptance_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/acceptance_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/acceptance_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/acceptance_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/acceptance_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/acceptance_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_combined.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_combined.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_combined_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_combined_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_combined_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_combined_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_combined_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_combined_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_identity.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_identity.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_identity_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_identity_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_identity_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_identity_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_identity_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_identity_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inspection.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inspection.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inspection_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inspection_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inspection_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inspection_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inspection_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inspection_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_manifest.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_manifest.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_marking.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_marking.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_marking_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_marking_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_marking_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_marking_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_marking_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_marking_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_observation.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_observation.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_observation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_observation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_observation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_observation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_observation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_observation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_preservation.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_preservation.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_preservation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_preservation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_preservation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_preservation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_preservation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_preservation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/after_sequence.json.gz`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_sequence.json.gz`.
- `support/artifacts/pr_play_object_visibility_authoring/after_sequence.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_sequence.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_visibility.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_visibility.log`.
- `support/artifacts/pr_play_object_visibility_authoring/after_visibility_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_visibility_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_visibility_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_visibility_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/after_visibility_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/after_visibility_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/ambiguous_reconciliation.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/ambiguous_reconciliation.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_create.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_create.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_flush.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_flush.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_partial_write.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_partial_write.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_replace.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_replace.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_serialization.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_serialization.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_failure_sync.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_failure_sync.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_postcommit_open_directory.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_postcommit_open_directory.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_postcommit_sync_directory.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_postcommit_sync_directory.json`.
- `support/artifacts/pr_play_object_visibility_authoring/atomic_success.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/atomic_success.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_combined.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_combined.log`.
- `support/artifacts/pr_play_object_visibility_authoring/before_combined_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_combined_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_combined_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_combined_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_combined_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_combined_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_identity_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_identity_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_identity_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_identity_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_identity_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_identity_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inspection_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inspection_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inspection_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inspection_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inspection_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inspection_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_manifest.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_manifest.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_marking_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_marking_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_marking_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_marking_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_marking_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_marking_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_observation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_observation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_observation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_observation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_observation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_observation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_preservation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_preservation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_preservation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_preservation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_preservation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_preservation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/before_sequence.json.gz`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_sequence.json.gz`.
- `support/artifacts/pr_play_object_visibility_authoring/before_visibility.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_visibility.log`.
- `support/artifacts/pr_play_object_visibility_authoring/before_visibility_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_visibility_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_visibility_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_visibility_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/before_visibility_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/before_visibility_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_ambiguous.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_ambiguous.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_create.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_create.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_flush.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_flush.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_partial_write.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_partial_write.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_replace.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_replace.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_serialization.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_serialization.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_failure_sync.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_failure_sync.json`.
- `support/artifacts/pr_play_object_visibility_authoring/classification_timeline.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/classification_timeline.json`.
- `support/artifacts/pr_play_object_visibility_authoring/client_writer_serialization.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/client_writer_serialization.json`.
- `support/artifacts/pr_play_object_visibility_authoring/cross_object.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/cross_object.json`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_api.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_api.py`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_current_review.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_current_review.md`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_git_status.txt`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_git_status.txt`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_identity.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_identity.json`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_next_session.md`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_next_session.md`.
- `support/artifacts/pr_play_object_visibility_authoring/entry_object_marking.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/entry_object_marking.py`.
- `support/artifacts/pr_play_object_visibility_authoring/evidence_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/evidence_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/evidence_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/evidence_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/evidence_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/evidence_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/evidence_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/evidence_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/files_created.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/files_created.json`.
- `support/artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_acceptance_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/final_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/final_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/final_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/final_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/final_git_status.txt`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/final_git_status.txt`.
- `support/artifacts/pr_play_object_visibility_authoring/finalize.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/finalize.py`.
- `support/artifacts/pr_play_object_visibility_authoring/focused_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/focused_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/focused_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/focused_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/focused_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/focused_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/focused_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/focused_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/http_bypass_change.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/http_bypass_change.json`.
- `support/artifacts/pr_play_object_visibility_authoring/idempotency_controls.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/idempotency_controls.json`.
- `support/artifacts/pr_play_object_visibility_authoring/information_leakage.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/information_leakage.json`.
- `support/artifacts/pr_play_object_visibility_authoring/inspection_removal_timeline.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/inspection_removal_timeline.json`.
- `support/artifacts/pr_play_object_visibility_authoring/marking_round_trip.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/marking_round_trip.json`.
- `support/artifacts/pr_play_object_visibility_authoring/marking_snapshots.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/marking_snapshots.json`.
- `support/artifacts/pr_play_object_visibility_authoring/measure_performance.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/measure_performance.py`.
- `support/artifacts/pr_play_object_visibility_authoring/milestone_identity.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/milestone_identity.json`.
- `support/artifacts/pr_play_object_visibility_authoring/no_change_and_restricted.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/no_change_and_restricted.json`.
- `support/artifacts/pr_play_object_visibility_authoring/noninterference.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/noninterference.json`.
- `support/artifacts/pr_play_object_visibility_authoring/observation_performance.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/observation_performance.json`.
- `support/artifacts/pr_play_object_visibility_authoring/observation_portability_pf1e@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/observation_portability_pf1e@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/observation_portability_rules_light@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/observation_portability_rules_light@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/observation_portability_scifi@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/observation_portability_scifi@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/observation_timeline.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/observation_timeline.json`.
- `support/artifacts/pr_play_object_visibility_authoring/performance.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/performance.json`.
- `support/artifacts/pr_play_object_visibility_authoring/performance_measurement.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/performance_measurement.log`.
- `support/artifacts/pr_play_object_visibility_authoring/performance_refined.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/performance_refined.json`.
- `support/artifacts/pr_play_object_visibility_authoring/persistence_round_trip.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/persistence_round_trip.json`.
- `support/artifacts/pr_play_object_visibility_authoring/portability_pf1e@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/portability_pf1e@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/portability_rules_light@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/portability_rules_light@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/portability_scifi@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/portability_scifi@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/production.diff`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/production.diff`.
- `support/artifacts/pr_play_object_visibility_authoring/read_only.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/read_only.json`.
- `support/artifacts/pr_play_object_visibility_authoring/regression_results.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/regression_results.json`.
- `support/artifacts/pr_play_object_visibility_authoring/removal_failure_post_save.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/removal_failure_post_save.json`.
- `support/artifacts/pr_play_object_visibility_authoring/removal_failure_replace.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/removal_failure_replace.json`.
- `support/artifacts/pr_play_object_visibility_authoring/removal_failure_save.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/removal_failure_save.json`.
- `support/artifacts/pr_play_object_visibility_authoring/removal_failure_sync.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/removal_failure_sync.json`.
- `support/artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/run_checks.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/run_checks.py`.
- `support/artifacts/pr_play_object_visibility_authoring/seal_review.py`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/seal_review.py`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_combined.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_combined.log`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_combined_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_combined_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_combined_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_combined_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_combined_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_combined_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_identity_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_identity_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_identity_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_identity_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_identity_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_identity_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inspection_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_marking_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_marking_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_marking_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_marking_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_marking_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_marking_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_observation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_observation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_observation_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_observation_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_observation_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_observation_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_preservation.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_preservation.log`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_preservation_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_preservation_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_sequence.json.gz`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_sequence.json.gz`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_visibility.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_visibility.log`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_after_visibility_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/sealed_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/sealed_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/source_changes.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/source_changes.json`.
- `support/artifacts/pr_play_object_visibility_authoring/t06_source_map.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/t06_source_map.json`.
- `support/artifacts/pr_play_object_visibility_authoring/twelve_turn_comparison.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/twelve_turn_comparison.json`.
- `support/artifacts/pr_play_object_visibility_authoring/validation_interruptions.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/validation_interruptions.json`.
- `support/artifacts/pr_play_object_visibility_authoring/verified_authoring.log`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/verified_authoring.log`.
- `support/artifacts/pr_play_object_visibility_authoring/verified_authoring_command.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/verified_authoring_command.json`.
- `support/artifacts/pr_play_object_visibility_authoring/verified_authoring_execution.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/verified_authoring_execution.json`.
- `support/artifacts/pr_play_object_visibility_authoring/verified_authoring_junit.xml`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/verified_authoring_junit.xml`.
- `support/artifacts/pr_play_object_visibility_authoring/visibility_idempotency_controls.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/visibility_idempotency_controls.json`.
- `support/artifacts/pr_play_object_visibility_authoring/visibility_performance.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/visibility_performance.json`.
- `support/artifacts/pr_play_object_visibility_authoring/visibility_portability_pf1e@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/visibility_portability_pf1e@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/visibility_portability_rules_light@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/visibility_portability_rules_light@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/visibility_portability_scifi@1.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/visibility_portability_scifi@1.json`.
- `support/artifacts/pr_play_object_visibility_authoring/evidence_manifest.json`: Explicit source, contract or measured verification evidence for this bounded cycle. Canonical source: `artifacts/pr_play_object_visibility_authoring/evidence_manifest.json`.

## Explicit omissions

- `artifacts/pr_play_object_visibility_authoring/before_identity.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_identity.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_inspection.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_inspection.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_inventory_snapshot.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_marking.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_marking.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_observation.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_observation.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_preservation.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_preservation.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/before_sequence.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_sequence.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/http_bypass_drop.json`: duplicate content of artifacts/pr_play_object_visibility_authoring/http_bypass_change.json; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/http_bypass_duplicate.json`: duplicate content of artifacts/pr_play_object_visibility_authoring/http_bypass_change.json; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/http_bypass_insert.json`: duplicate content of artifacts/pr_play_object_visibility_authoring/http_bypass_change.json; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/http_bypass_rebind.json`: duplicate content of artifacts/pr_play_object_visibility_authoring/http_bypass_change.json; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/retry_sealed_after_preservation.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_preservation.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_identity.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_identity.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_inspection.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_inspection.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_inventory_snapshot.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_inventory_snapshot.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_marking.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_marking.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_observation.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_observation.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_after_sequence.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/after_sequence.log; canonical reference retained
- `artifacts/pr_play_object_visibility_authoring/sealed_authoring.log`: duplicate content of artifacts/pr_play_object_visibility_authoring/evidence_authoring.log; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
