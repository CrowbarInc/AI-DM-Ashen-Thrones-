# Cycle D Visibility Fallback Contraction Closure

Date: 2026-05-13

## Executive Summary

Visibility fallback contraction is ready to close.

The extracted boundary now keeps visibility fallback helper code focused on pure route, payload, metadata, and telemetry shaping. The final emission gate remains the orchestration owner for fallback selection, prose calls, output mutation, metadata writes, tag/debug mutation, logging calls, and route sequencing. This preserves the final-emission behavior contract while reducing inline payload construction around the visibility, first-mention, and referential-clarity replacement paths.

Recommendation: close visibility fallback contraction now and move to the next cluster.

## Helpers And Types Added

`game/final_emission_visibility_fallback.py` now owns typed helper objects for visibility fallback orchestration payloads:

- `VisibilityValidationObservation`
- `VisibilityPreRouteValidationContext`
- `VisibilityDefaultMetadataPayload`
- `VisibilityFirstMentionDefaultMetadataPayload`
- `VisibilityPreRouteMetadataContext`
- `VisibilityRouteMetadataOutcome`
- `VisibilityReplacementAnnotations`
- `VisibilityHardReplacementPlan`
- `VisibilitySelectedFallback`
- `VisibilityFirstMentionMetadataPayload`
- `FirstMentionSelectedFallbackMetadataPayload`
- `ReferentialClaritySelectedFallbackMetadataPayload`
- `FirstMentionReplacementLoggingPayload`
- `ReferentialClarityReplacementLoggingPayload`
- `VisibilityHardReplacementLoggingPayload`
- `VisibilityHardReplacementContext`
- `VisibilityNonReplacementRouteContext`
- `VisibilityFallbackSelectionInputs`
- `VisibilityRouteDispatchContext`
- `VisibilityRouteDecisionInputs`
- `VisibilityEnforcementStageContext`

Key pure builders include:

- `build_visibility_validation_observation`
- `build_visibility_pre_route_validation_context`
- `build_visibility_default_metadata_payload`
- `build_visibility_first_mention_default_metadata_payload`
- `build_visibility_pre_route_metadata_context`
- `build_visibility_route_decision_inputs`
- `build_visibility_enforcement_stage_context`
- `route_visibility_enforcement_after_failed_validation`
- `classify_visibility_fallback_owner_bucket`
- `build_visibility_route_metadata_outcome`
- `build_visibility_replacement_annotations`
- `build_visibility_hard_replacement_plan`
- `visibility_selected_fallback_from_tuple`
- `build_visibility_first_mention_metadata_payload`
- `build_first_mention_selected_fallback_metadata_payload`
- `build_referential_clarity_selected_fallback_metadata_payload`
- `build_first_mention_replacement_logging_payload`
- `build_referential_clarity_replacement_logging_payload`
- `build_visibility_hard_replacement_logging_payload`
- `build_visibility_hard_replacement_context`
- `build_visibility_non_replacement_route_context`
- `build_visibility_fallback_selection_inputs`
- `build_visibility_route_dispatch_context`
- `stamp_visibility_fallback_metadata`

## Telemetry Added

The visibility contraction added and locked explicit visibility fallback evidence:

- `visibility_fallback_owner_bucket`
- `visibility_fallback_pool`
- `visibility_fallback_kind`

Owner-bucket classification is centralized in `classify_visibility_fallback_owner_bucket`, with values preserved for:

- opening visibility fallback ownership
- strict-social visibility fallback ownership
- sealed-gate visibility fallback ownership
- unknown/none visibility fallback ownership

Failure classifier, dashboard, and golden replay projections now preserve this evidence alongside existing sealed fallback owner evidence.

## Behavior Guarantees

The contraction intentionally preserves these boundaries:

- No emitted text changes.
- No fallback prose was moved into `game/final_emission_visibility_fallback.py`.
- Fallback selection remains in `game/final_emission_gate.py`.
- Output writes remain in `game/final_emission_gate.py`.
- Metadata writes remain in `game/final_emission_gate.py`, except for the existing visibility metadata stamper called by the gate.
- Tag/debug mutation remains in `game/final_emission_gate.py`.
- `log_final_emission_decision(...)` and `log_final_emission_trace(...)` calls remain in `game/final_emission_gate.py`.
- Route branching remains in `game/final_emission_gate.py`, with pure decision/dispatch helpers used as inputs.
- `fallback_source`, `fallback_family`, `visibility_fallback_owner_bucket`, and `sealed_fallback_owner_bucket` values are preserved.

## Tests Run

Focused closure tests passed:

- `tests/test_final_emission_visibility.py -q`: passed, 49 tests
- `tests/test_final_emission_gate.py -q`: passed, 281 tests
- `tests/test_golden_replay.py -q`: passed, 29 tests
- `tests/test_failure_classifier.py -q`: passed, 53 tests
- `tests/test_failure_dashboard_controlled_failures.py -q`: passed, 19 tests
- `tests/test_failure_classification_contract.py -q`: passed, 22 tests

## What Remains In `final_emission_gate.py`

`game/final_emission_gate.py` still owns:

- `_standard_visibility_safe_fallback`
- `_apply_visibility_enforcement`
- first-mention and referential-clarity enforcement sequencing
- output writes to `player_facing_text`
- fallback selection and fallback prose calls
- metadata writes and metadata stamping calls
- tag/debug mutation
- `log_final_emission_decision(...)` calls
- `log_final_emission_trace(...)` calls
- route branching and returns
- visibility-safe fallback tuple production

This is intentional: the gate remains the canonical final-emission orchestrator.

## Remaining Risks

Remaining risks are known and acceptable for closure:

- `_standard_visibility_safe_fallback` is still a large branch body. Extracting it further would risk moving fallback selection or prose ownership, so it should not be part of visibility fallback contraction closure.
- Legacy tuple shape remains at the selection boundary, but `VisibilitySelectedFallback` wraps it immediately for extracted payload paths. A broader tuple retirement should be a separate migration.
- First-mention and referential-clarity enforcement bodies remain large because they still own validation, route returns, writes, and fallback calls.
- Local referential substitution still has its own inline logging payload for the non-fallback local-repair success path. It is adjacent but not part of selected-fallback replacement closure.
- The helper module includes interaction-pattern regexes used for route decisions. This is selector logic, not prose authorship, and is covered by no-prose-literal guard tests.

## Recommended Next Cluster

Move to the next cluster rather than continue visibility fallback contraction.

Recommended next cluster: local referential-clarity repair payloads and logging, if the goal is to keep shrinking final-emission enforcement bodies without touching fallback prose or selection. The highest-value follow-up is to inventory local substitution metadata/logging as its own seam, not as part of visibility fallback closure.
