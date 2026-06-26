"""Synthetic observed rows, drift row builders, and replay probe helpers (CG-2).

**Authority:** derives test data only; does not own taxonomy vocabulary.
Registry: ``docs/audits/CG_failure_classification_authority_registry.md``"""
from __future__ import annotations

from typing import Any, Mapping

from game.attribution_read_views import (
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_SELECTION_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import FailureClassification, classify_replay_failure
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    OPENING_FALLBACK_FAMILY,
    OPENING_SUCCESS_REPAIR_KIND,
    fail_closed_opening_observed_fields,
    successful_opening_observed_fields,
)
from tests.helpers.replay_observed_row_fixtures import (
    SyntheticObservedRowProfile,
    observed_dashboard_probe_row,
    observed_failure_row,
)

def _observed_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **fields: Any,
) -> dict[str, Any]:
    if profile == "dashboard_probe":
        return observed_dashboard_probe_row(**fields)
    return observed_failure_row(**fields)


def observed_opening_fallback_row(
    *,
    owner_bucket: bool = False,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for canonical successful opening fallback."""
    return _observed_row(
        profile=profile,
        **successful_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides),
    )


def observed_fail_closed_opening_fallback_row(
    *,
    owner_bucket: bool = False,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for sealed/fail-closed opening fallback."""
    return _observed_row(
        profile=profile,
        **fail_closed_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides),
    )


def observed_legacy_opening_fallback_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for legacy compatibility-local opening fallback."""
    return _observed_row(
        profile=profile,
        **successful_opening_observed_fields(
            opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            **overrides,
        ),
    )


def observed_opening_authorship_compat_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return minimal observed-row evidence for compatibility-local opening authorship probes."""
    fields = {
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
        "fallback_family": OPENING_FALLBACK_FAMILY,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_opening_basis_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return minimal observed-row evidence for opening basis divergence probes."""
    fields = {
        "opening_recovered_via_fallback": True,
        "fallback_family": OPENING_FALLBACK_FAMILY,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def opening_family_fallback_selected_lineage_event(
    *,
    fallback_kind: str,
    fallback_content_owner: str,
    fallback_owner_bucket: str,
    fallback_authorship_source: str | None = None,
    repair_kind: str | None = None,
) -> dict[str, Any]:
    """Runtime lineage event with BU14 opening-family split-owner trifecta."""
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_kind=fallback_kind,
        fallback_owner_bucket=fallback_owner_bucket,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=fallback_content_owner,
        fallback_authorship_source=fallback_authorship_source,
        repair_kind=repair_kind,
    )


def observed_opening_family_split_owner_row(
    *,
    fallback_kind: str,
    fallback_content_owner: str,
    opening_fallback_owner_bucket: str,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for opening-family split-owner classifier/dashboard probes."""
    if fallback_kind == "scene_opening":
        fields = successful_opening_observed_fields(
            include_owner_bucket=True,
            opening_fallback_owner_bucket=opening_fallback_owner_bucket,
        )
        lineage_authorship = OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
        repair_kind = OPENING_SUCCESS_REPAIR_KIND
    elif fallback_kind == "opening_failed_closed":
        fields = fail_closed_opening_observed_fields(
            include_owner_bucket=True,
            opening_fallback_owner_bucket=opening_fallback_owner_bucket,
        )
        lineage_authorship = None
        repair_kind = fields.get("response_type_repair_kind")
    else:
        raise ValueError(f"unsupported opening-family fallback_kind: {fallback_kind!r}")

    fields["runtime_lineage_events"] = [
        opening_family_fallback_selected_lineage_event(
            fallback_kind=fallback_kind,
            fallback_content_owner=fallback_content_owner,
            fallback_owner_bucket=opening_fallback_owner_bucket,
            fallback_authorship_source=lineage_authorship,
            repair_kind=str(repair_kind) if repair_kind else None,
        )
    ]
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_global_replacement_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for global/gate terminal replacement."""
    fields = {
        "final_emitted_source": "global_scene_fallback",
        "fallback_family": "gate_terminal_repair",
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_social_fallback_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for strict-social fallback replacement probes."""
    fields = {
        "strict_social_active": True,
        "final_emitted_source": "strict_social_visibility_minimal",
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_sealed_replacement_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for sealed/global replacement owner-bucket checks."""
    fields = {"sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_SEALED_GATE}
    fields.update(overrides)
    return observed_global_replacement_row(profile=profile, **fields)


def sealed_family_fallback_selected_lineage_event(
    *,
    fallback_kind: str,
    fallback_content_owner: str,
    fallback_owner_bucket: str,
) -> dict[str, Any]:
    """Runtime lineage event with BU13 sealed-family split-owner trifecta."""
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_kind=fallback_kind,
        fallback_owner_bucket=fallback_owner_bucket,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=fallback_content_owner,
    )


def observed_sealed_family_split_owner_row(
    *,
    fallback_kind: str,
    final_emitted_source: str,
    fallback_content_owner: str,
    sealed_fallback_owner_bucket: str = SEALED_FALLBACK_OWNER_SEALED_GATE,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for sealed-family replacement split-owner classifier/dashboard probes."""
    fields: dict[str, Any] = {
        "final_route": "replaced",
        "final_emitted_source": final_emitted_source,
        "fallback_family": "gate_terminal_repair",
        "sealed_fallback_owner_bucket": sealed_fallback_owner_bucket,
        "runtime_lineage_events": [
            sealed_family_fallback_selected_lineage_event(
                fallback_kind=fallback_kind,
                fallback_content_owner=fallback_content_owner,
                fallback_owner_bucket=sealed_fallback_owner_bucket,
            )
        ],
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_visibility_replacement_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for visibility replacement owner-bucket checks."""
    fields = {
        "final_emitted_source": "global_scene_fallback",
        "visibility_fallback_owner_bucket": "sealed-gate",
        "visibility_replacement_applied": True,
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def visibility_family_fallback_selected_lineage_event(
    *,
    fallback_kind: str,
    repair_kind: str,
    fallback_owner_bucket: str,
    fallback_content_owner: str,
) -> dict[str, Any]:
    """Runtime lineage event with BU10 visibility-family split-owner trifecta."""
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind=fallback_kind,
        fallback_owner_bucket=fallback_owner_bucket,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=fallback_content_owner,
        repair_kind=repair_kind,
    )


def observed_visibility_family_hard_replacement_row(
    *,
    visibility_replacement_applied: bool = False,
    first_mention_replacement_applied: bool = False,
    referential_clarity_replacement_applied: bool = False,
    fallback_kind: str,
    repair_kind: str,
    visibility_fallback_owner_bucket: str = "sealed-gate",
    fallback_content_owner: str = SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for visibility-family hard-replacement split-owner probes."""
    fields: dict[str, Any] = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": visibility_replacement_applied,
        "first_mention_replacement_applied": first_mention_replacement_applied,
        "referential_clarity_replacement_applied": referential_clarity_replacement_applied,
        "visibility_fallback_owner_bucket": visibility_fallback_owner_bucket,
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
        "producer_repair_kind": repair_kind,
        "runtime_lineage_events": [
            visibility_family_fallback_selected_lineage_event(
                fallback_kind=fallback_kind,
                repair_kind=repair_kind,
                fallback_owner_bucket=visibility_fallback_owner_bucket,
                fallback_content_owner=fallback_content_owner,
            )
        ],
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def sanitizer_fallback_selected_lineage_event(
    *,
    fallback_kind: str,
    fallback_content_owner: str,
    repair_kind: str | None = None,
) -> dict[str, Any]:
    """Runtime lineage event with BU12 sanitizer-family split-owner trifecta."""
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="sanitizer",
        owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_kind=fallback_kind,
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=fallback_content_owner,
        repair_kind=repair_kind,
    )


def observed_sanitizer_split_owner_row(
    *,
    fallback_kind: str,
    fallback_content_owner: str,
    repair_kind: str | None = None,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for sanitizer split-owner classifier/dashboard probes."""
    fields: dict[str, Any] = {
        "final_emitted_source": "generated_candidate",
        "runtime_lineage_events": [
            sanitizer_fallback_selected_lineage_event(
                fallback_kind=fallback_kind,
                fallback_content_owner=fallback_content_owner,
                repair_kind=repair_kind,
            )
        ],
    }
    if fallback_kind == "sanitizer_strict_social":
        fields.update(
            {
                "strict_social_active": True,
                "sanitizer_strict_social_fallback_used": True,
                "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            }
        )
    elif fallback_kind == "sanitizer_empty_output":
        fields.update(
            {
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
            }
        )
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def upstream_fast_fallback_selected_lineage_event() -> dict[str, Any]:
    """Runtime lineage event with BU12 upstream-fast split-owner trifecta."""
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="retry",
        owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_kind="upstream_fast_fallback",
        fallback_owner_bucket="retry",
        fallback_selection_owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        source="fallback_provenance_trace",
    )


def observed_upstream_fast_split_owner_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for upstream-fast split-owner classifier/dashboard probes."""
    fields: dict[str, Any] = {
        "final_emitted_source": "generated_candidate",
        "runtime_lineage_events": [upstream_fast_fallback_selected_lineage_event()],
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_referential_local_substitution_classifier_row(
    *,
    visibility_fallback_owner_bucket: str = "strict-social-visibility",
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Observed-row evidence for referential local substitution producer/bucket probes."""
    fields: dict[str, Any] = {
        "final_route": "accept_candidate",
        "referential_clarity_local_substitution_applied": True,
        "visibility_fallback_owner_bucket": visibility_fallback_owner_bucket,
        "producer_repair_kind": "referential_clarity_local_substitution",
        "runtime_lineage_events": [
            make_runtime_lineage_event(
                event_kind="mutation",
                stage="gate",
                owner="game.final_emission_gate",
                mutation_kind="referential_clarity_local_substitution_mutation",
                source="She",
            )
        ],
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_sanitizer_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for sanitizer-classified failure probes."""
    fields = {
        "sanitizer_mode": "strip_only",
        "sanitizer_event_count": 2,
        "sanitizer_changed_count": 1,
        "sanitizer_rewrite_used": True,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_sanitizer_empty_fallback_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for sanitizer empty-fallback ownership probes."""
    fields = {
        "sanitizer_mode": "strip_only",
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
        SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
        "upstream_prepared_emission_used": False,
        "upstream_prepared_emission_valid": False,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_sanitizer_leakage_dashboard_row(
    *,
    profile: SyntheticObservedRowProfile = "dashboard_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return dashboard-shaped sanitizer leakage probe with lineage metadata present."""
    fields = {
        "sanitizer_mode": "strip_only",
        "sanitizer_event_count": 1,
        "sanitizer_changed_count": 0,
        "sanitizer_lineage_mode": "strip_only",
        "sanitizer_lineage_changed_count": 1,
        "sanitizer_lineage_dropped_count": 1,
        "sanitizer_lineage_empty_fallback_used": False,
        "sanitizer_lineage_legacy_rewrite_active": False,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_sanitizer_legacy_rewrite_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for legacy sanitizer rewrite diagnostic probes."""
    fields = {
        "sanitizer_lineage_mode": "legacy_sentence_rewrite",
        "sanitizer_lineage_changed_count": 1,
        "sanitizer_lineage_dropped_count": 0,
        "sanitizer_lineage_empty_fallback_used": False,
        "sanitizer_lineage_legacy_rewrite_active": True,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_response_type_repair_row(
    repair_kind: str,
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for response-type repair classifier probes."""
    fields = {
        "response_type_repair_used": True,
        "response_type_repair_kind": repair_kind,
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_upstream_prepared_emission_row(
    *,
    response_type_repair_kind: str,
    upstream_prepared_emission_source: str,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    response_type_repair_used: bool = True,
    upstream_prepared_emission_used: bool = True,
    upstream_prepared_emission_valid: bool = True,
    upstream_prepared_emission_reject_reason: str | None = None,
    final_emission_mutation_lineage: list[str] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for upstream-prepared emission classifier probes."""
    fields: dict[str, Any] = {
        "response_type_repair_used": response_type_repair_used,
        "response_type_repair_kind": response_type_repair_kind,
        "upstream_prepared_emission_used": upstream_prepared_emission_used,
        "upstream_prepared_emission_valid": upstream_prepared_emission_valid,
        "upstream_prepared_emission_source": upstream_prepared_emission_source,
    }
    if upstream_prepared_emission_reject_reason is not None:
        fields["upstream_prepared_emission_reject_reason"] = upstream_prepared_emission_reject_reason
    if final_emission_mutation_lineage is not None:
        fields["final_emission_mutation_lineage"] = final_emission_mutation_lineage
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_post_gate_mutation_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for post-gate mutation classifier/dashboard probes."""
    fields: dict[str, Any] = {"post_gate_mutation_detected": True}
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_opening_projection_missing_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for opening owner-bucket projection omission probes."""
    fields = {
        "unavailable": ["opening_fallback_owner_bucket"],
        "raw_signal_presence": {"opening_fallback_owner_bucket": True},
    }
    fields.update(overrides)
    return _observed_row(profile=profile, **fields)


def observed_speaker_mismatch_observed_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    selected_speaker_id: str = "guard",
    **overrides: Any,
) -> dict[str, Any]:
    """Return observed-row evidence for selected-speaker mismatch classifier probes."""
    return _observed_row(profile=profile, selected_speaker_id=selected_speaker_id, **overrides)


def replay_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any,
    reason: str = "exact value mismatch",
    drift_bucket: str = "structural_drift",
) -> dict[str, Any]:
    """Build one replay drift row dict for classifier/dashboard probes."""
    return {
        "field_path": field_path,
        "expected": expected,
        "actual": actual,
        "reason": reason,
        "drift_bucket": drift_bucket,
    }


def speaker_mismatch_drift_row(*, expected: str = "runner", actual: str = "guard") -> dict[str, Any]:
    """Shared selected-speaker mismatch drift row for dashboard/classifier probes."""
    return replay_drift_row("selected_speaker_id", expected=expected, actual=actual)


def global_fallback_source_drift_row(
    *,
    expected: Any = "generated_candidate",
    actual: Any = "global_scene_fallback",
    reason: str = "exact value mismatch",
) -> dict[str, Any]:
    """Shared final-emitted-source fallback drift row for dashboard/classifier probes."""
    return replay_drift_row("final_emitted_source", expected=expected, actual=actual, reason=reason)


def forbidden_global_fallback_source_drift_row() -> dict[str, Any]:
    """Shared forbidden global-scene-fallback drift row for classifier routing probes."""
    return global_fallback_source_drift_row(
        expected="anything except 'global_scene_fallback'",
        reason="forbidden value observed",
    )


def scaffold_leakage_drift_row(*, reason: str = "scaffold leakage mismatch") -> dict[str, Any]:
    """Shared scaffold-leakage drift row for dashboard/classifier probes."""
    return replay_drift_row(
        "scaffold_leakage",
        expected=False,
        actual=True,
        reason=reason,
        drift_bucket="semantic_drift",
    )


def response_type_repair_drift_row(*, reason: str = "exact value mismatch") -> dict[str, Any]:
    """Shared response-type repair drift row for dashboard/classifier probes."""
    return replay_drift_row("response_type_repair_used", expected=False, actual=True, reason=reason)


def projection_unavailable_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any = None,
    reason: str = "unexpected unavailable field",
) -> dict[str, Any]:
    """Shared projection-unavailable drift row for dashboard/classifier probes."""
    return replay_drift_row(field_path, expected=expected, actual=actual, reason=reason)


def post_gate_mutation_drift_row() -> dict[str, Any]:
    """Shared post-gate mutation drift row for dashboard/classifier probes."""
    return replay_drift_row("post_gate_mutation_detected", expected=False, actual=True)


def opening_recovered_drift_row() -> dict[str, Any]:
    """Shared opening-recovered drift row for opening fallback classifier probes."""
    return replay_drift_row("opening_recovered_via_fallback", expected=False, actual=True)


def route_mismatch_drift_row(*, expected: str, actual: str) -> dict[str, Any]:
    """Shared route-kind mismatch drift row for dashboard/classifier probes."""
    return replay_drift_row("route_kind", expected=expected, actual=actual)


def semantic_text_fragment_drift_row(*, expected: str, actual: str) -> dict[str, Any]:
    """Shared final-text semantic fragment drift row for dashboard/classifier probes."""
    return replay_drift_row(
        "final_text",
        expected=expected,
        actual=actual,
        reason="required text fragment missing",
        drift_bucket="semantic_drift",
    )


def exact_value_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any,
    reason: str = "exact value mismatch",
    drift_bucket: str = "structural_drift",
) -> dict[str, Any]:
    """Shared exact-value drift row for dashboard/classifier probes."""
    return replay_drift_row(
        field_path,
        expected=expected,
        actual=actual,
        reason=reason,
        drift_bucket=drift_bucket,
    )


def classify_replay_probe_row(
    *,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
    scenario_id: str,
    turn_index: int = 0,
) -> FailureClassification:
    """Classify one replay probe turn into a single dashboard row."""
    rows = classify_replay_failure(
        scenario_id=scenario_id,
        turn_index=turn_index,
        observed_turn=observed_turn,
        drift_rows=[drift_row],
    )
    if not rows:
        raise AssertionError("classify_replay_probe_row expected one classified row")
    return rows[0]

