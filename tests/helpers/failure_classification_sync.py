"""Branch-local contract ↔ classifier alignment checks (Cycle T2).

Centralizes taxonomy sync assertions so contract constant changes and classifier
rule tables stay aligned without scattering duplicate checks across test files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NamedTuple, NotRequired, Sequence, get_origin, get_type_hints

from game.attribution_read_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
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
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from game.attribution_read_views import SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.failure_classification_contract import (
    ALLOWED_CLASSIFICATION_ROW_FIELDS,
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_PRIMARY_OWNERS,
    ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SECONDARY_OWNERS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    CLASSIFIER_EVIDENCE_EXTENSION_FIELDS,
    CLASSIFIER_EVIDENCE_FIELDS,
    LEGACY_RESPONSE_TYPE_REPAIR_KINDS,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
    OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
    PROTECTED_CLASSIFIER_EVIDENCE_FIELDS,
    REQUIRED_CLASSIFICATION_FIELDS,
)
from tests.helpers.failure_classifier import (
    CATEGORY_RULES,
    FailureClassification,
    INVESTIGATION_TARGETS,
    PRIMARY_OWNER_RULES,
    SECONDARY_OWNER_RULES,
    classify_replay_failure,
    validate_failure_classification_row,
)
from tests.helpers.golden_replay_projection import (
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
)
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


# --- BU15 cross-family split-owner acceptance matrix (canonical owner literals) ---


class SplitOwnerAcceptanceRow(NamedTuple):
    """One accepted split-owner fallback family row for cross-surface alignment checks."""

    matrix_id: str
    family: str
    event_kind: str
    fallback_kind: str | None
    mutation_kind: str | None
    fallback_selection_owner: str | None
    fallback_content_owner: str | None
    owner_bucket_field: str | None
    owner_bucket: str | None
    repair_kind: str | None
    stage: str | None
    dashboard_case_id: str | None


def split_owner_acceptance_matrix_rows() -> tuple[SplitOwnerAcceptanceRow, ...]:
    """Return the canonical BU15 split-owner acceptance matrix in stable order."""
    return SPLIT_OWNER_ACCEPTANCE_MATRIX


def split_owner_acceptance_matrix_row_ids() -> tuple[str, ...]:
    """Return stable matrix row ids for parametrized tests."""
    return tuple(row.matrix_id for row in SPLIT_OWNER_ACCEPTANCE_MATRIX)


SPLIT_OWNER_ACCEPTANCE_MATRIX: tuple[SplitOwnerAcceptanceRow, ...] = (
    SplitOwnerAcceptanceRow(
        matrix_id="scene_opening",
        family="opening",
        event_kind="fallback_selected",
        fallback_kind="scene_opening",
        mutation_kind=None,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="opening_fallback_owner_bucket",
        owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        repair_kind="opening_deterministic_fallback",
        stage="gate",
        dashboard_case_id="scene_opening_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="opening_failed_closed",
        family="opening",
        event_kind="fallback_selected",
        fallback_kind="opening_failed_closed",
        mutation_kind=None,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FAIL_CLOSED_CONTENT_OWNER,
        owner_bucket_field="opening_fallback_owner_bucket",
        owner_bucket=OPENING_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="opening_deterministic_fallback_failed_closed",
        stage="gate",
        dashboard_case_id="opening_failed_closed_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="visibility_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=VISIBILITY_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="visibility_enforcement",
        stage="gate",
        dashboard_case_id="visibility_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="first_mention_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=FIRST_MENTION_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="first_mention_enforcement",
        stage="gate",
        dashboard_case_id="first_mention_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="referential_clarity_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=REFERENTIAL_CLARITY_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        repair_kind="referential_clarity_enforcement",
        stage="gate",
        dashboard_case_id="referential_clarity_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="referential_local_substitution",
        family="visibility",
        event_kind="mutation",
        fallback_kind=None,
        mutation_kind="referential_clarity_local_substitution_mutation",
        fallback_selection_owner=None,
        fallback_content_owner=None,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        repair_kind="referential_clarity_local_substitution",
        stage="gate",
        dashboard_case_id="referential_local_substitution_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sanitizer_empty_output",
        family="sanitizer",
        event_kind="fallback_selected",
        fallback_kind="sanitizer_empty_output",
        mutation_kind=None,
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        owner_bucket_field=None,
        owner_bucket=None,
        repair_kind="sanitizer_empty_output",
        stage="sanitizer",
        dashboard_case_id="sanitizer_empty_output_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sanitizer_strict_social",
        family="sanitizer",
        event_kind="fallback_selected",
        fallback_kind="sanitizer_strict_social",
        mutation_kind=None,
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        owner_bucket_field=None,
        owner_bucket=None,
        repair_kind="strict_social_repair",
        stage="sanitizer",
        dashboard_case_id="sanitizer_strict_social_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="upstream_fast_fallback",
        family="upstream_fast",
        event_kind="fallback_selected",
        fallback_kind="upstream_fast_fallback",
        mutation_kind=None,
        fallback_selection_owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        owner_bucket_field=None,
        owner_bucket="retry",
        repair_kind=None,
        stage="retry",
        dashboard_case_id="upstream_fast_fallback_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_social_interlocutor",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_social_interlocutor_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_passive_scene_pressure",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_passive_scene_pressure_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_npc_pursuit_neutral",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_npc_pursuit_neutral_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_anti_reset_continuation",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_anti_reset_continuation_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_global_scene",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_global_scene_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_unknown_replacement",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_unknown_replacement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_or_global_replacement_legacy",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind="sealed_or_global_replacement",
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id=None,
    ),
)


_SEALED_MATRIX_FINAL_EMITTED_SOURCES: dict[str, str] = {
    "sealed_social_interlocutor": "social_interlocutor_minimal_fallback",
    "sealed_passive_scene_pressure": "passive_scene_pressure_fallback",
    "sealed_npc_pursuit_neutral": "npc_pursuit_neutral_fallback",
    "sealed_anti_reset_continuation": "anti_reset_local_continuation_fallback",
    "sealed_global_scene": "global_scene_fallback",
    "sealed_unknown_replacement": "unclassified_terminal_fallback",
    "sealed_or_global_replacement_legacy": "global_scene_fallback",
}

# BU17: legacy matrix rows stay in the acceptance matrix for classifier vocabulary only.
SPLIT_OWNER_LEGACY_MATRIX_ROWS: dict[str, str] = {
    "sealed_or_global_replacement_legacy": (
        "Synthetic classifier vocabulary only; production FEM maps global_scene_fallback "
        "to sealed_global_scene_fallback. Dashboard and FEM projection probes intentionally "
        "excluded; classifier coverage remains in "
        "test_failure_classifier.py::test_failure_classifier_accepts_sealed_family_runtime_lineage_split_owners."
    ),
}

# Rows validated via synthetic observed-row builders only; production FEM maps to modern subkinds.
SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS: dict[str, str] = {
    matrix_id: reason
    for matrix_id, reason in SPLIT_OWNER_LEGACY_MATRIX_ROWS.items()
}

_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS: dict[str, Any] = {
    "final_route": "replaced",
    "final_emitted_source": "global_scene_fallback",
    "visibility_fallback_pool": "global_scene_narrative",
    "visibility_fallback_kind": "narrative_safe_fallback",
}


def split_owner_matrix_row_by_id(matrix_id: str) -> SplitOwnerAcceptanceRow:
    """Return one canonical matrix row by id."""
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        if row.matrix_id == matrix_id:
            return row
    raise KeyError(f"unknown split-owner matrix row: {matrix_id!r}")


def split_owner_matrix_legacy(row: SplitOwnerAcceptanceRow) -> bool:
    """Return True when a matrix row is synthetic-only legacy vocabulary."""
    return row.matrix_id in SPLIT_OWNER_LEGACY_MATRIX_ROWS


def split_owner_fem_projection_excluded(row: SplitOwnerAcceptanceRow) -> bool:
    """Return True when production FEM projection is intentionally out of scope for a row."""
    return split_owner_matrix_legacy(row)


def split_owner_fem_projection_exclusion_reason(row: SplitOwnerAcceptanceRow) -> str | None:
    """Return the documented exclusion reason when FEM projection is out of scope."""
    return SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS.get(row.matrix_id)


def split_owner_fem_meta_from_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build synthetic FEM/meta dict for production replay projection from a matrix row."""
    if split_owner_fem_projection_excluded(row):
        reason = split_owner_fem_projection_exclusion_reason(row)
        raise ValueError(f"matrix row {row.matrix_id!r} has no FEM projection fixture: {reason}")

    from tests.helpers.golden_replay_fixtures import fem_payload
    from tests.helpers.opening_fallback_evidence import (
        fail_closed_opening_fem_meta,
        successful_opening_fem_meta,
    )

    if row.matrix_id == "scene_opening":
        return successful_opening_fem_meta(
            response_type_repair_kind=row.repair_kind,
            fallback_temporal_frame="first_impression",
        )
    if row.matrix_id == "opening_failed_closed":
        return fail_closed_opening_fem_meta(
            opening_recovered_via_fallback=True,
            fallback_family_used="scene_opening",
        )
    if row.matrix_id == "visibility_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            visibility_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "first_mention_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            first_mention_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "referential_clarity_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            referential_clarity_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "referential_local_substitution":
        return fem_payload(
            final_route="accept_candidate",
            referential_clarity_local_substitution_applied=True,
            referential_clarity_local_substitution_token="she",
            referential_clarity_local_substitution_replacement="The Tavern Runner",
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "sanitizer_empty_output":
        return fem_payload(
            final_emitted_source="generated_candidate",
            sanitizer_empty_fallback_used=True,
            sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
            sanitizer_empty_fallback_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
            final_emission_mutation_lineage=[
                "pre_gate_sanitizer",
                "sanitizer_empty_fallback",
                "finalize_packaging",
            ],
        )
    if row.matrix_id == "sanitizer_strict_social":
        return fem_payload(
            final_emitted_source="generated_candidate",
            strict_social_active=True,
            sanitizer_strict_social_fallback_used=True,
            sanitizer_strict_social_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
            sanitizer_strict_social_prose_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source=None,
            upstream_prepared_emission_reject_reason=None,
        )
    if row.matrix_id == "upstream_fast_fallback":
        return fem_payload(
            final_emitted_source="generated_candidate",
            fallback_provenance_trace={
                "source": "fallback",
                "stage": "fallback_selector",
                "content_fingerprint": "abc123",
                "gate_exit_vs_selector_match": True,
            },
        )
    if row.family == "sealed":
        return fem_payload(
            final_route="replaced",
            final_emitted_source=_SEALED_MATRIX_FINAL_EMITTED_SOURCES[row.matrix_id],
            sealed_fallback_owner_bucket=row.owner_bucket,
            realization_fallback_family="gate_terminal_repair",
        )
    raise ValueError(f"unsupported matrix row for FEM projection: {row.matrix_id!r}")


def split_owner_sanitizer_projection_metadata(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build sanitizer_trace metadata for golden replay sanitizer-family matrix rows."""
    if row.matrix_id == "sanitizer_empty_output":
        return {
            "sanitizer_trace": {
                "sanitizer_boundary_mode": "strip_only",
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
            }
        }
    if row.matrix_id == "sanitizer_strict_social":
        return {
            "sanitizer_trace": {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_strict_social_fallback_used": True,
                "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
                "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            }
        }
    raise ValueError(f"unsupported sanitizer matrix row: {row.matrix_id!r}")


def split_owner_projection_turn_kwargs(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build kwargs for :func:`project_synthetic_turn` from a canonical matrix row."""
    if split_owner_fem_projection_excluded(row):
        reason = split_owner_fem_projection_exclusion_reason(row)
        raise ValueError(f"matrix row {row.matrix_id!r} has no projection turn fixture: {reason}")

    from tests.helpers.golden_replay_fixtures import minimal_gm_output_payload

    kwargs: dict[str, Any] = {
        "scenario_id": f"matrix_fem_{row.matrix_id}",
        "gm_text": {
            "scene_opening": "The road opens under morning light.",
            "opening_failed_closed": "The road opens under sealed gate light.",
            "referential_local_substitution": "The Tavern Runner says she will return.",
            "sanitizer_strict_social": 'The runner says, "No names."',
        }.get(row.matrix_id, "Synthetic split-owner projection line."),
    }
    fem_meta = split_owner_fem_meta_from_matrix_row(row)
    if row.family == "sanitizer":
        kwargs["payload"] = minimal_gm_output_payload(
            fem_meta=fem_meta,
            metadata=split_owner_sanitizer_projection_metadata(row),
        )
        kwargs["player_text"] = "Ask the runner." if row.matrix_id == "sanitizer_strict_social" else "Wait."
        kwargs["resolution"] = {"kind": "question" if row.matrix_id == "sanitizer_strict_social" else "observe"}
    else:
        kwargs["fem_meta"] = fem_meta
        if row.matrix_id == "upstream_fast_fallback":
            kwargs["player_text"] = "Wait."
            kwargs["resolution"] = {"kind": "observe"}
    return kwargs


def project_split_owner_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Project one matrix row through production golden replay FEM/replay projection."""
    from tests.helpers.golden_replay_fixtures import project_synthetic_turn

    return project_synthetic_turn(**split_owner_projection_turn_kwargs(row))


def assert_split_owner_matrix_fem_projection(
    row: SplitOwnerAcceptanceRow,
    observed: Mapping[str, Any],
) -> None:
    """Assert production FEM/replay projection matches the canonical matrix row."""
    if row.owner_bucket_field is not None and row.owner_bucket is not None:
        assert observed.get(row.owner_bucket_field) == row.owner_bucket

    if row.event_kind == "mutation":
        event = next(
            item
            for item in observed.get("runtime_lineage_events") or []
            if item.get("event_kind") == "mutation" and item.get("mutation_kind") == row.mutation_kind
        )
        assert_split_owner_matrix_lineage_event(row, event)
        return

    event = next(
        item
        for item in observed.get("runtime_lineage_events") or []
        if item.get("event_kind") == "fallback_selected"
    )
    assert_split_owner_matrix_lineage_event(row, event)


def split_owner_matrix_dashboard_expected_dict(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build controlled-dashboard expected classifier fields from a matrix row."""
    expected: dict[str, Any] = {
        "category": "replay_drift",
        "primary_owner": "replay",
        "secondary_owner": "emission",
        "severity": "medium",
        "investigate_first": "tests/helpers/golden_replay.py",
    }
    if row.family == "opening":
        expected["emission_sublayer"] = "opening_fallback"
    elif row.event_kind == "mutation":
        pass
    elif row.family == "sanitizer":
        expected["emission_sublayer"] = (
            "strict_social_replacement" if row.matrix_id == "sanitizer_strict_social" else "sanitizer"
        )
    elif row.family in {"visibility", "sealed"}:
        if row.family == "sealed" and row.matrix_id not in {
            "sealed_global_scene",
            "sealed_unknown_replacement",
        }:
            expected["emission_sublayer"] = "fallback_behavior"
        else:
            expected["emission_sublayer"] = "terminal_fallback"

    if row.fallback_selection_owner is not None:
        expected["fallback_selection_owner"] = row.fallback_selection_owner
    if row.fallback_content_owner is not None:
        expected["fallback_content_owner"] = row.fallback_content_owner
    if row.owner_bucket_field is not None and row.owner_bucket is not None:
        expected[row.owner_bucket_field] = row.owner_bucket
    if row.repair_kind is not None:
        expected["repair_kind"] = row.repair_kind

    if row.matrix_id in {
        "visibility_enforcement",
        "first_mention_enforcement",
        "referential_clarity_enforcement",
    }:
        expected.update(
            {
                "visibility_fallback_pool": "global_scene_narrative",
                "visibility_fallback_kind": "narrative_safe_fallback",
            }
        )
    if row.matrix_id == "visibility_enforcement":
        expected["visibility_replacement_applied"] = True
    if row.matrix_id == "sanitizer_strict_social":
        expected.update(
            {
                "sanitizer_strict_social_fallback_used": True,
                "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            }
        )
    if row.matrix_id == "sanitizer_empty_output":
        expected.update(
            {
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
            }
        )
    return expected


def split_owner_matrix_controlled_failure_cases() -> tuple[
    tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]],
    ...,
]:
    """Build dashboard controlled probes for matrix rows with dashboard_case_id."""
    cases: list[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        if row.dashboard_case_id is None:
            continue
        cases.append(
            (
                row.dashboard_case_id,
                split_owner_observed_row_from_matrix_row(row, profile="dashboard_probe"),
                split_owner_matrix_classifier_drift_row(row),
                split_owner_matrix_dashboard_expected_dict(row),
            )
        )
    return tuple(cases)


def split_owner_lineage_event_from_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build one runtime lineage event from a canonical matrix row."""
    if row.event_kind == "mutation":
        return make_runtime_lineage_event(
            event_kind="mutation",
            stage=row.stage or "gate",
            owner=OPENING_FALLBACK_SELECTION_OWNER,
            mutation_kind=row.mutation_kind,
            source="She",
        )
    if row.family == "opening":
        authorship = (
            OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
            if row.fallback_kind == "scene_opening"
            else None
        )
        return opening_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            fallback_owner_bucket=str(row.owner_bucket),
            fallback_authorship_source=authorship,
            repair_kind=row.repair_kind,
        )
    if row.family == "visibility" and row.event_kind == "fallback_selected":
        return visibility_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            repair_kind=str(row.repair_kind),
            fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
        )
    if row.family == "sanitizer":
        return sanitizer_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            repair_kind=row.repair_kind,
        )
    if row.family == "upstream_fast":
        return upstream_fast_fallback_selected_lineage_event()
    if row.family == "sealed":
        return sealed_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            fallback_owner_bucket=str(row.owner_bucket),
        )
    raise ValueError(f"unsupported matrix row: {row.matrix_id!r}")


def split_owner_observed_row_from_matrix_row(
    row: SplitOwnerAcceptanceRow,
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
) -> dict[str, Any]:
    """Build one classifier/dashboard observed row from a canonical matrix row."""
    dashboard_overrides: dict[str, Any] = {}
    if profile == "dashboard_probe":
        if row.matrix_id == "sanitizer_strict_social":
            dashboard_overrides = {
                SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
            }
        elif row.matrix_id == "sanitizer_empty_output":
            dashboard_overrides = {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_lineage_empty_fallback_used": True,
            }

    if row.matrix_id == "referential_local_substitution":
        return observed_referential_local_substitution_classifier_row(
            profile=profile,
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    if row.family == "opening":
        return observed_opening_family_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            opening_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == VISIBILITY_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            visibility_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == FIRST_MENTION_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            first_mention_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == REFERENTIAL_CLARITY_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            referential_clarity_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "sanitizer":
        return observed_sanitizer_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            repair_kind=row.repair_kind,
            **dashboard_overrides,
        )
    if row.family == "upstream_fast":
        return observed_upstream_fast_split_owner_row(profile=profile, **dashboard_overrides)
    if row.family == "sealed":
        return observed_sealed_family_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            final_emitted_source=_SEALED_MATRIX_FINAL_EMITTED_SOURCES[row.matrix_id],
            fallback_content_owner=str(row.fallback_content_owner),
            sealed_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    raise ValueError(f"unsupported matrix row: {row.matrix_id!r}")


def split_owner_matrix_classifier_drift_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build the replay drift row used by classifier/dashboard matrix probes."""
    if row.event_kind == "mutation":
        return exact_value_drift_row(
            "referential_clarity_local_substitution_applied",
            expected=False,
            actual=True,
            reason=f"{row.matrix_id} referential local substitution drift probe",
        )
    return exact_value_drift_row(
        "fallback_content_owner",
        expected=row.fallback_selection_owner,
        actual=row.fallback_content_owner,
        reason=f"{row.matrix_id} split owner projection changed",
    )


def assert_split_owner_matrix_lineage_event(
    row: SplitOwnerAcceptanceRow,
    event: Mapping[str, Any],
) -> None:
    """Assert one lineage event matches the canonical matrix row."""
    assert event.get("event_kind") == row.event_kind
    if row.stage is not None:
        assert event.get("stage") == row.stage
    if row.event_kind == "mutation":
        assert event.get("mutation_kind") == row.mutation_kind
        assert event.get("owner") == OPENING_FALLBACK_SELECTION_OWNER
        return
    assert event.get("fallback_kind") == row.fallback_kind
    assert event.get("fallback_selection_owner") == row.fallback_selection_owner
    assert event.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket is not None and event.get("fallback_owner_bucket") is not None:
        assert event.get("fallback_owner_bucket") == row.owner_bucket
    if row.repair_kind is not None and event.get("repair_kind") is not None:
        assert event.get("repair_kind") == row.repair_kind


def assert_split_owner_matrix_classifier_row(
    row: SplitOwnerAcceptanceRow,
    classified_row: Mapping[str, Any],
) -> None:
    """Assert one classifier/dashboard row matches the canonical matrix row."""
    if row.event_kind == "mutation":
        if row.owner_bucket_field is not None:
            assert classified_row.get(row.owner_bucket_field) == row.owner_bucket
        if row.repair_kind is not None:
            assert classified_row.get("repair_kind") == row.repair_kind
        return
    assert classified_row.get("fallback_selection_owner") == row.fallback_selection_owner
    assert classified_row.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket_field is not None:
        assert classified_row.get(row.owner_bucket_field) == row.owner_bucket
    if row.repair_kind is not None:
        assert classified_row.get("repair_kind") == row.repair_kind


def assert_split_owner_matrix_dashboard_expected(
    row: SplitOwnerAcceptanceRow,
    expected: Mapping[str, Any],
) -> None:
    """Assert controlled dashboard expected dict matches matrix owner literals."""
    if row.event_kind == "mutation":
        assert expected.get(row.owner_bucket_field) == row.owner_bucket
        if row.repair_kind is not None:
            assert expected.get("repair_kind") == row.repair_kind
        return
    if row.fallback_selection_owner is not None:
        assert expected.get("fallback_selection_owner") == row.fallback_selection_owner
    if row.fallback_content_owner is not None:
        assert expected.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket_field is not None:
        assert expected.get(row.owner_bucket_field) == row.owner_bucket
    if row.repair_kind is not None:
        assert expected.get("repair_kind") == row.repair_kind


# BU19: empty — every non-legacy row uses "{matrix_id}_split_owner".
SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES: dict[str, tuple[str, str]] = {}


def split_owner_dashboard_case_id_default(matrix_id: str) -> str:
    """Return the canonical dashboard probe id for a matrix row."""
    return f"{matrix_id}_split_owner"


def split_owner_expected_dashboard_case_id(row: SplitOwnerAcceptanceRow) -> str | None:
    """Return the expected dashboard probe id for a matrix row (None when legacy/excluded)."""
    if split_owner_matrix_legacy(row):
        return None
    return split_owner_dashboard_case_id_default(row.matrix_id)


def split_owner_matrix_dashboard_case_id_misalignments() -> list[str]:
    """Return dashboard_case_id drift messages; empty when ids match {matrix_id}_split_owner."""
    misalignments: list[str] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        expected = split_owner_expected_dashboard_case_id(row)
        if expected is None:
            if row.dashboard_case_id is not None:
                misalignments.append(
                    f"{row.matrix_id!r} is legacy/excluded but dashboard_case_id={row.dashboard_case_id!r}"
                )
            continue
        if row.dashboard_case_id != expected:
            misalignments.append(
                f"{row.matrix_id!r} dashboard_case_id={row.dashboard_case_id!r} "
                f"expected {expected!r}"
            )
    return misalignments


def assert_split_owner_matrix_dashboard_case_id_parity() -> None:
    """Assert every dashboard-covered matrix row uses {matrix_id}_split_owner."""
    misalignments = split_owner_matrix_dashboard_case_id_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"split-owner dashboard case id parity drift:\n{joined}")


def split_owner_sealed_matrix_rows_requiring_dashboard_probe() -> tuple[SplitOwnerAcceptanceRow, ...]:
    """Return sealed-family matrix rows that must have dashboard controlled probes (BU17)."""
    return tuple(
        row
        for row in SPLIT_OWNER_ACCEPTANCE_MATRIX
        if row.family == "sealed" and not split_owner_matrix_legacy(row)
    )


def render_split_owner_acceptance_matrix_report() -> str:
    """Render a concise markdown report of the canonical BU15/BU16/BU17/BU18/BU19 matrix."""
    lines = [
        "# BU15/BU16/BU17/BU18/BU19 Split-Owner Acceptance Matrix",
        "",
        "Canonical cross-family owner literals shared by classifier, dashboard, golden replay FEM "
        "projection, runtime lineage summary, and attribution inventory tests.",
        "",
        "| matrix_id | family | event_kind | fallback/mutation kind | selection_owner | content_owner | "
        "owner_bucket_field | owner_bucket | repair_kind | dashboard_case_id | fem_projection |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        kind = row.fallback_kind or row.mutation_kind or ""
        fem_status = "excluded" if split_owner_fem_projection_excluded(row) else "matrix_fem"
        lines.append(
            f"| {row.matrix_id} | {row.family} | {row.event_kind} | {kind} | "
            f"{row.fallback_selection_owner or ''} | {row.fallback_content_owner or ''} | "
            f"{row.owner_bucket_field or ''} | {row.owner_bucket or ''} | "
            f"{row.repair_kind or ''} | {row.dashboard_case_id or ''} | {fem_status} |"
        )
    lines.append("")
    lines.append(f"Total rows: {len(SPLIT_OWNER_ACCEPTANCE_MATRIX)}")
    lines.append(f"Dashboard probes: {len(split_owner_matrix_controlled_failure_cases())}")
    sealed_dashboard_rows = split_owner_sealed_matrix_rows_requiring_dashboard_probe()
    lines.append(
        f"Sealed subkind dashboard parity: {sum(1 for row in sealed_dashboard_rows if row.dashboard_case_id)}"
        f"/{len(sealed_dashboard_rows)} non-legacy rows"
    )
    if SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES:
        lines.append("")
        lines.append("## Dashboard case id aliases (BU18)")
        for matrix_id, (case_id, rationale) in SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES.items():
            lines.append(f"- `{matrix_id}` -> `{case_id}`: {rationale}")
    if SPLIT_OWNER_LEGACY_MATRIX_ROWS:
        lines.append("")
        lines.append("## Legacy matrix rows (BU17 synthetic-only)")
        for matrix_id, reason in SPLIT_OWNER_LEGACY_MATRIX_ROWS.items():
            lines.append(f"- `{matrix_id}`: {reason}")
    if SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS:
        lines.append("")
        lines.append("## FEM projection exclusions")
        for matrix_id, reason in SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS.items():
            lines.append(f"- `{matrix_id}`: {reason}")
    lines.extend(split_owner_acceptance_matrix_report_footer_lines())
    return "\n".join(lines)


def split_owner_acceptance_matrix_report_footer_lines() -> list[str]:
    """Return maintainer footer lines appended to the checked-in matrix report."""
    return [
        "",
        "## Split-owner matrix change workflow (BU22)",
        "",
        "Canonical source: `SPLIT_OWNER_ACCEPTANCE_MATRIX` in "
        "`tests/helpers/failure_classification_sync.py`. "
        "Full checklist: `docs/audits/README.md`.",
        "",
        "1. Update `SPLIT_OWNER_ACCEPTANCE_MATRIX` (no production emission changes for matrix-only edits).",
        "2. Update dashboard evidence cells only if dashboard strings changed "
        "(`tests/test_failure_dashboard_controlled_failures.py`).",
        "3. Regenerate and validate: "
        "`python scripts/refresh_split_owner_acceptance_matrix.py` "
        "(or `make split-owner-matrix-refresh`).",
        "4. Partial modes: `--write-report-only`, `--check-only`, `--skip-pytest`.",
        "5. Run focused classifier/dashboard/projection tests only when behavior changed.",
        "",
        "## Maintainer commands (BU20/BU21/BU23/BU24)",
        "",
        "Full refresh (Windows-native; default):",
        "",
        "```bash",
        "python scripts/refresh_split_owner_acceptance_matrix.py",
        "```",
        "",
        "Unix/mac/Git Bash equivalent:",
        "",
        "```bash",
        "make split-owner-matrix-refresh",
        "```",
        "",
        "Report only / check only:",
        "",
        "```bash",
        "python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only",
        "python scripts/refresh_split_owner_acceptance_matrix.py --check-only",
        "python scripts/refresh_split_owner_acceptance_matrix.py --skip-pytest",
        "```",
        "",
        "Contract gate only (also in CI convergence-checks and default fast lane):",
        "",
        "```bash",
        "python scripts/check_split_owner_acceptance_matrix.py",
        "# or",
        "make split-owner-matrix-check",
        "# or",
        "python -m pytest tests/test_split_owner_acceptance_matrix_contract.py -q -m split_owner_matrix_contract",
        "```",
    ]


SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH = "docs/audits/BU15_split_owner_acceptance_matrix.md"
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS = 16
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS = 15
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS = 15
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS = 1
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_SEALED_NON_LEGACY_DASHBOARD_ROWS = 6


def split_owner_acceptance_matrix_counts() -> dict[str, int]:
    """Return live split-owner matrix row counts for contract/CI gates."""
    rows = SPLIT_OWNER_ACCEPTANCE_MATRIX
    legacy_rows = [row for row in rows if split_owner_matrix_legacy(row)]
    dashboard_rows = [row for row in rows if row.dashboard_case_id is not None]
    fem_rows = [row for row in rows if not split_owner_fem_projection_excluded(row)]
    sealed_dashboard_rows = split_owner_sealed_matrix_rows_requiring_dashboard_probe()
    return {
        "total_rows": len(rows),
        "dashboard_covered_rows": len(dashboard_rows),
        "fem_projection_rows": len(fem_rows),
        "legacy_only_rows": len(legacy_rows),
        "dashboard_probes": len(split_owner_matrix_controlled_failure_cases()),
        "sealed_non_legacy_dashboard_rows": sum(
            1 for row in sealed_dashboard_rows if row.dashboard_case_id is not None
        ),
    }


def split_owner_acceptance_matrix_report_text(*, repo_root: Path | None = None) -> str:
    """Read the checked-in split-owner acceptance matrix report from disk."""
    from pathlib import Path as _Path

    root = repo_root if repo_root is not None else _Path(__file__).resolve().parents[2]
    report_path = root / SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH
    return report_path.read_text(encoding="utf-8").replace("\r\n", "\n")


def split_owner_acceptance_matrix_classifier_builder_misalignments() -> list[str]:
    """Return classifier/dashboard builder drift messages without running classification."""
    misalignments: list[str] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        try:
            observed = split_owner_observed_row_from_matrix_row(row)
            drift = split_owner_matrix_classifier_drift_row(row)
        except Exception as exc:  # pragma: no cover - defensive contract surface
            misalignments.append(f"{row.matrix_id!r} builder failed: {exc}")
            continue
        if not observed:
            misalignments.append(f"{row.matrix_id!r} observed row builder returned empty payload")
        if not drift.get("field_path"):
            misalignments.append(f"{row.matrix_id!r} classifier drift row missing field_path")
        if row.event_kind != "mutation" and row.dashboard_case_id is not None:
            event = (observed.get("runtime_lineage_events") or [None])[0]
            if not isinstance(event, dict):
                misalignments.append(f"{row.matrix_id!r} dashboard probe missing runtime_lineage_events[0]")
            else:
                try:
                    assert_split_owner_matrix_lineage_event(row, event)
                except AssertionError as exc:
                    misalignments.append(f"{row.matrix_id!r} embedded lineage drift: {exc}")
    return misalignments


def split_owner_acceptance_matrix_contract_misalignments(
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Return split-owner matrix contract drift messages; empty when BU20-locked."""
    from pathlib import Path as _Path

    misalignments: list[str] = []

    if SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES:
        misalignments.append(
            "SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES must remain empty after BU19; "
            f"got {sorted(SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES)!r}"
        )

    misalignments.extend(split_owner_matrix_dashboard_case_id_misalignments())

    counts = split_owner_acceptance_matrix_counts()
    expected_counts = {
        "total_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS,
        "dashboard_covered_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
        "fem_projection_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS,
        "legacy_only_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS,
        "dashboard_probes": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
        "sealed_non_legacy_dashboard_rows": (
            SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_SEALED_NON_LEGACY_DASHBOARD_ROWS
        ),
    }
    for key, expected in expected_counts.items():
        actual = counts[key]
        if actual != expected:
            misalignments.append(f"{key} expected {expected}, got {actual}")

    if counts["dashboard_probes"] != counts["dashboard_covered_rows"]:
        misalignments.append(
            "dashboard_probes must equal dashboard_covered_rows; "
            f"probes={counts['dashboard_probes']} covered={counts['dashboard_covered_rows']}"
        )
    if counts["fem_projection_rows"] + counts["legacy_only_rows"] != counts["total_rows"]:
        misalignments.append(
            "fem_projection_rows + legacy_only_rows must equal total_rows; "
            f"fem={counts['fem_projection_rows']} legacy={counts['legacy_only_rows']} "
            f"total={counts['total_rows']}"
        )

    legacy_matrix_ids = {
        row.matrix_id for row in SPLIT_OWNER_ACCEPTANCE_MATRIX if split_owner_matrix_legacy(row)
    }
    if legacy_matrix_ids != set(SPLIT_OWNER_LEGACY_MATRIX_ROWS):
        misalignments.append(
            "legacy matrix rows must match SPLIT_OWNER_LEGACY_MATRIX_ROWS; "
            f"matrix={sorted(legacy_matrix_ids)!r} registry={sorted(SPLIT_OWNER_LEGACY_MATRIX_ROWS)!r}"
        )

    rendered = render_split_owner_acceptance_matrix_report()
    on_disk = split_owner_acceptance_matrix_report_text(repo_root=repo_root)
    if rendered != on_disk:
        root = repo_root if repo_root is not None else _Path(__file__).resolve().parents[2]
        misalignments.append(
            f"{SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH} is out of date; "
            f"regenerate with render_split_owner_acceptance_matrix_report() "
            f"(repo root {root})"
        )

    misalignments.extend(split_owner_acceptance_matrix_classifier_builder_misalignments())
    return misalignments


def assert_split_owner_acceptance_matrix_contract(*, repo_root: Path | None = None) -> None:
    """Assert BU20 split-owner matrix/report/dashboard/FEM/classifier builder contract."""
    misalignments = split_owner_acceptance_matrix_contract_misalignments(repo_root=repo_root)
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"split-owner acceptance matrix contract drift:\n{joined}")


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


def known_failure_categories() -> tuple[str, ...]:
    """Return contract-locked failure categories in stable order."""
    return tuple(sorted(ALLOWED_FAILURE_CATEGORIES))


def classifier_evidence_field_paths() -> frozenset[str]:
    """Return the contract-locked classifier evidence field paths."""
    return frozenset(CLASSIFIER_EVIDENCE_FIELDS)


def protected_replay_classifier_evidence_field_paths() -> frozenset[str]:
    """Return protected classifier evidence paths derived from protected replay projection."""
    return protected_classifier_evidence_field_paths()


def failure_dashboard_evidence_manifest() -> tuple[tuple[str, str], ...]:
    """Return the contract-owned dashboard Evidence-column manifest."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_MANIFEST

    return FAILURE_DASHBOARD_EVIDENCE_MANIFEST


def failure_dashboard_evidence_row_keys() -> tuple[str, ...]:
    """Return dashboard Evidence-column row keys in contract order."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS

    return FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS


def failure_dashboard_evidence_labels() -> tuple[str, ...]:
    """Return dashboard Evidence-column labels in contract order."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_LABELS

    return FAILURE_DASHBOARD_EVIDENCE_LABELS


def known_owner_buckets() -> dict[str, tuple[str, ...]]:
    """Return contract-locked fallback owner bucket taxonomies."""
    return {
        "opening": tuple(sorted(ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS)),
        "sealed": tuple(sorted(ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS)),
        "visibility": tuple(sorted(ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS)),
    }


def expected_investigation_targets() -> dict[str, str]:
    """Derive classifier investigation targets from the public contract."""
    return {
        category: target
        for category, target in MAJOR_OWNER_INVESTIGATION_TARGETS.items()
        if category != "replay"
    } | {"replay_drift": MAJOR_OWNER_INVESTIGATION_TARGETS["replay"]}


def failure_classification_row_contract_fields() -> dict[str, frozenset[str]]:
    """Return contract-locked classifier row field sets for sync and validation."""
    return {
        "required": REQUIRED_CLASSIFICATION_FIELDS,
        "optional_evidence": OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
        "allowed": ALLOWED_CLASSIFICATION_ROW_FIELDS,
    }


def failure_classification_typeddict_field_sets() -> tuple[frozenset[str], frozenset[str]]:
    """Return (required, optional) field names from ``FailureClassification`` annotations."""
    required: set[str] = set()
    optional: set[str] = set()
    for name, hint in get_type_hints(FailureClassification, include_extras=True).items():
        if get_origin(hint) is NotRequired:
            optional.add(name)
        else:
            required.add(name)
    return frozenset(required), frozenset(optional)


def failure_classification_row_contract_misalignments() -> list[str]:
    """Return row-contract drift messages; empty when TypedDict matches contract."""
    misalignments: list[str] = []
    contract = failure_classification_row_contract_fields()
    typed_required, typed_optional = failure_classification_typeddict_field_sets()
    allowed_typeddict = typed_required | typed_optional

    if contract["required"] != typed_required:
        misalignments.append(
            "FailureClassification required TypedDict fields must match REQUIRED_CLASSIFICATION_FIELDS; "
            f"missing_from_typeddict={sorted(contract['required'] - typed_required)!r} "
            f"extra_in_typeddict={sorted(typed_required - contract['required'])!r}"
        )
    if contract["optional_evidence"] != typed_optional:
        misalignments.append(
            "FailureClassification NotRequired TypedDict fields must match OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS; "
            f"missing_from_typeddict={sorted(contract['optional_evidence'] - typed_optional)!r} "
            f"extra_in_typeddict={sorted(typed_optional - contract['optional_evidence'])!r}"
        )
    if allowed_typeddict != contract["allowed"]:
        misalignments.append(
            "FailureClassification.__annotations__ must cover required ∪ optional contract fields; "
            f"missing_from_typeddict={sorted(contract['allowed'] - allowed_typeddict)!r} "
            f"extra_in_typeddict={sorted(allowed_typeddict - contract['allowed'])!r}"
        )

    return misalignments


def assert_failure_classification_row_contract_locked() -> None:
    """Assert FailureClassification TypedDict mirrors the public row contract."""
    misalignments = failure_classification_row_contract_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"failure classification row contract misalignment:\n{joined}")


def classification_contract_summary() -> dict[str, Any]:
    """Compact summary of contract/classifier taxonomy surfaces."""
    buckets = known_owner_buckets()
    rule_categories = {rule[2] for rule in CATEGORY_RULES}
    return {
        "failure_category_count": len(ALLOWED_FAILURE_CATEGORIES),
        "primary_owner_count": len(ALLOWED_PRIMARY_OWNERS),
        "category_rule_count": len(CATEGORY_RULES),
        "category_rule_categories": len(rule_categories),
        "investigation_target_count": len(INVESTIGATION_TARGETS),
        "required_field_count": len(REQUIRED_CLASSIFICATION_FIELDS),
        "opening_owner_bucket_count": len(buckets["opening"]),
        "sealed_owner_bucket_count": len(buckets["sealed"]),
        "visibility_owner_bucket_count": len(buckets["visibility"]),
        "runtime_response_type_repair_kind_count": len(ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS),
        "legacy_response_type_repair_kind_count": len(LEGACY_RESPONSE_TYPE_REPAIR_KINDS),
    }


def expected_failure_classification_row_fields() -> dict[str, tuple[str, ...]]:
    """Return contract-locked required and optional evidence field names for dashboard rows."""
    fields = failure_classification_row_contract_fields()
    return {
        "required": tuple(sorted(fields["required"])),
        "optional_evidence": tuple(sorted(fields["optional_evidence"])),
        "allowed": tuple(sorted(fields["allowed"])),
    }


def failure_dashboard_row_shape_errors(row: Mapping[str, Any]) -> list[str]:
    """Return row-shape validation errors; empty when the row matches the contract."""
    return validate_failure_classification_row(row)


def assert_failure_dashboard_row_shape(row: Mapping[str, Any]) -> None:
    """Assert one classifier/dashboard row satisfies the shared row-shape contract."""
    errors = failure_dashboard_row_shape_errors(row)
    if errors:
        joined = "; ".join(errors)
        raise AssertionError(f"invalid failure dashboard row shape: {joined}")


def protected_observation_registry_summary() -> dict[str, Any]:
    """Compact summary of the protected golden replay observation field registry."""
    registry = protected_observation_field_registry()
    paths = protected_observation_field_paths()
    structural_paths = tuple(
        field.path for field in registry if field.drift_bucket == "structural_drift"
    )
    semantic_paths = tuple(
        field.path for field in registry if field.drift_bucket == "semantic_drift"
    )
    return {
        "protected_field_count": len(registry),
        "structural_field_count": len(structural_paths),
        "semantic_field_count": len(semantic_paths),
        "protected_classifier_evidence_count": len(protected_replay_classifier_evidence_field_paths()),
        "protected_classifier_evidence_excluded_count": len(protected_classifier_evidence_excluded_paths()),
        "paths_unique": len(set(paths)) == len(paths),
        "paths_sorted": list(paths) == sorted(paths),
        "fallback_family_bucket": protected_observation_drift_bucket("fallback_family"),
        "scaffold_leakage_bucket": protected_observation_drift_bucket("scaffold_leakage"),
    }


def contract_classifier_misalignments(
    *,
    category_rules: Sequence[tuple[str, tuple[str, ...], str, str]] | None = None,
    primary_owner_rules: Mapping[str, str] | None = None,
    secondary_owner_rules: Mapping[str, str | None] | None = None,
    investigation_targets: Mapping[str, str] | None = None,
) -> list[str]:
    """Return human-readable misalignment messages; empty when aligned."""
    rules = list(category_rules if category_rules is not None else CATEGORY_RULES)
    primary = dict(primary_owner_rules if primary_owner_rules is not None else PRIMARY_OWNER_RULES)
    secondary = dict(secondary_owner_rules if secondary_owner_rules is not None else SECONDARY_OWNER_RULES)
    targets = dict(investigation_targets if investigation_targets is not None else INVESTIGATION_TARGETS)
    expected_targets = expected_investigation_targets()

    misalignments: list[str] = []

    if targets != expected_targets:
        missing = sorted(set(expected_targets) - set(targets))
        extra = sorted(set(targets) - set(expected_targets))
        changed = sorted(
            key
            for key in set(expected_targets) & set(targets)
            if expected_targets[key] != targets[key]
        )
        if missing:
            misalignments.append(f"investigation_targets missing keys: {missing!r}")
        if extra:
            misalignments.append(f"investigation_targets unexpected keys: {extra!r}")
        for key in changed:
            misalignments.append(
                "investigation_targets drift for "
                f"{key!r}: expected {expected_targets[key]!r}, got {targets[key]!r}"
            )

    for rule_name, _needles, category, source_family in rules:
        if category not in ALLOWED_FAILURE_CATEGORIES:
            misalignments.append(
                f"CATEGORY_RULES[{rule_name!r}] category {category!r} not in ALLOWED_FAILURE_CATEGORIES"
            )
        if source_family not in ALLOWED_SOURCE_FAMILY_TAGS:
            misalignments.append(
                f"CATEGORY_RULES[{rule_name!r}] source_family {source_family!r} not in ALLOWED_SOURCE_FAMILY_TAGS"
            )

    for category, owner in primary.items():
        if owner not in ALLOWED_PRIMARY_OWNERS:
            misalignments.append(
                f"PRIMARY_OWNER_RULES[{category!r}] owner {owner!r} not in ALLOWED_PRIMARY_OWNERS"
            )
        if category not in ALLOWED_PRIMARY_OWNERS and category not in ALLOWED_FAILURE_CATEGORIES:
            misalignments.append(
                f"PRIMARY_OWNER_RULES key {category!r} is neither a contract category nor primary owner"
            )

    for category in ALLOWED_FAILURE_CATEGORIES:
        if category not in primary:
            misalignments.append(f"missing PRIMARY_OWNER_RULES entry for category {category!r}")

    for category, owner in secondary.items():
        if owner is not None and owner not in ALLOWED_SECONDARY_OWNERS:
            misalignments.append(
                f"SECONDARY_OWNER_RULES[{category!r}] owner {owner!r} not in ALLOWED_SECONDARY_OWNERS"
            )
        if category not in ALLOWED_FAILURE_CATEGORIES and category not in ALLOWED_PRIMARY_OWNERS:
            misalignments.append(
                f"SECONDARY_OWNER_RULES key {category!r} is neither a contract category nor primary owner"
            )

    rule_categories = {rule[2] for rule in rules}
    for category in sorted(rule_categories):
        if category not in targets:
            misalignments.append(f"missing investigation target for CATEGORY_RULES category {category!r}")

    runtime_kinds = {
        "answer_upstream_prepared_repair",
        "action_outcome_upstream_prepared_repair",
        "strict_social_dialogue_repair",
        "dialogue_minimal_repair",
    }
    if not runtime_kinds <= ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS:
        missing = sorted(runtime_kinds - ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS)
        misalignments.append(f"ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS missing {missing!r}")
    if "thin_answer" not in LEGACY_RESPONSE_TYPE_REPAIR_KINDS:
        misalignments.append("LEGACY_RESPONSE_TYPE_REPAIR_KINDS must include 'thin_answer'")
    if "thin_answer" in ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS:
        misalignments.append("ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS must not include legacy 'thin_answer'")

    if "upstream_prepared_emission" not in ALLOWED_PRIMARY_OWNERS:
        misalignments.append("ALLOWED_PRIMARY_OWNERS must include 'upstream_prepared_emission'")
    if "upstream_prepared_emission" not in ALLOWED_SOURCE_FAMILY_TAGS:
        misalignments.append("ALLOWED_SOURCE_FAMILY_TAGS must include 'upstream_prepared_emission'")

    return misalignments


_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT = 29


def dashboard_evidence_manifest_misalignments() -> list[str]:
    """Return dashboard evidence manifest drift messages; empty when AK3/AO3-locked."""
    from tests.failure_classification_contract import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS as contract_labels,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST as contract_manifest,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as contract_row_keys,
        failure_dashboard_evidence_manifest,
    )
    from tests.helpers.failure_dashboard_report import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS as dashboard_labels,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST as dashboard_manifest,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as dashboard_row_keys,
    )

    misalignments: list[str] = []

    if failure_dashboard_evidence_manifest() != contract_manifest:
        misalignments.append("failure_dashboard_evidence_manifest() must return FAILURE_DASHBOARD_EVIDENCE_MANIFEST")

    if dashboard_manifest != contract_manifest:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_MANIFEST unchanged"
        )
    if dashboard_row_keys != contract_row_keys:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS unchanged"
        )
    if dashboard_labels != contract_labels:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_LABELS unchanged"
        )

    manifest_keys = tuple(row_key for _label, row_key in contract_manifest)
    if manifest_keys != contract_row_keys:
        misalignments.append("FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS must match manifest row keys")

    if len(contract_row_keys) != _EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT:
        misalignments.append(
            f"dashboard evidence manifest must contain {_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT} row keys, "
            f"got {len(contract_row_keys)}"
        )

    dashboard_only = sorted(set(contract_row_keys) - CLASSIFIER_EVIDENCE_FIELDS)
    if dashboard_only:
        misalignments.append(f"dashboard evidence keys outside classifier evidence: {dashboard_only!r}")

    return misalignments


def classifier_evidence_manifest_misalignments() -> list[str]:
    """Return manifest drift messages; empty when AK2/AO2 evidence sets are locked."""
    misalignments: list[str] = []

    if CLASSIFIER_EVIDENCE_FIELDS != OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS:
        misalignments.append(
            "CLASSIFIER_EVIDENCE_FIELDS must equal OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS"
        )

    derived_protected_overlap = protected_classifier_evidence_field_paths()
    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS != derived_protected_overlap:
        misalignments.append(
            "PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must equal protected_classifier_evidence_field_paths(); "
            f"contract_only={sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS - derived_protected_overlap)!r} "
            f"derived_only={sorted(derived_protected_overlap - PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)!r}"
        )

    if len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS) != 32:
        misalignments.append(
            f"PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must contain 32 fields, got {len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)}"
        )
    if len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS) != 16:
        misalignments.append(
            f"CLASSIFIER_EVIDENCE_EXTENSION_FIELDS must contain 16 fields, got {len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)}"
        )

    overlap = PROTECTED_CLASSIFIER_EVIDENCE_FIELDS & CLASSIFIER_EVIDENCE_EXTENSION_FIELDS
    if overlap:
        misalignments.append(f"protected overlap and extension sets must be disjoint; overlap={sorted(overlap)!r}")

    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS != CLASSIFIER_EVIDENCE_FIELDS:
        misalignments.append("CLASSIFIER_EVIDENCE_FIELDS must equal protected overlap | extension")

    protected_flat_paths = {path for path in protected_observation_field_paths() if "." not in path}
    expected_protected_overlap = protected_flat_paths & CLASSIFIER_EVIDENCE_FIELDS
    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS != expected_protected_overlap:
        misalignments.append(
            "PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must equal flat protected paths ∩ classifier evidence; "
            f"manifest_only={sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS - expected_protected_overlap)!r} "
            f"expected_only={sorted(expected_protected_overlap - PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)!r}"
        )

    excluded_only = protected_classifier_evidence_excluded_paths() - protected_flat_paths
    if excluded_only:
        misalignments.append(
            "protected classifier evidence exclusions must be flat protected paths; "
            f"invalid_exclusions={sorted(excluded_only)!r}"
        )
    ineligible_flat = protected_flat_paths - derived_protected_overlap
    if ineligible_flat != protected_classifier_evidence_excluded_paths():
        misalignments.append(
            "protected classifier evidence exclusions must equal flat protected paths not in overlap; "
            f"expected_excluded={sorted(protected_classifier_evidence_excluded_paths())!r} "
            f"actual_ineligible={sorted(ineligible_flat)!r}"
        )

    misalignments.extend(dashboard_evidence_manifest_misalignments())
    misalignments.extend(failure_classification_row_contract_misalignments())

    return misalignments


def assert_classifier_evidence_manifest_locked() -> None:
    """Assert AK2 classifier evidence manifest matches contract and dashboard surfaces."""
    misalignments = classifier_evidence_manifest_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"classifier evidence manifest misalignment:\n{joined}")
    assert_failure_classification_row_contract_locked()


def assert_contract_classifier_alignment() -> None:
    """Assert classifier rule tables remain aligned with contract constants."""
    misalignments = contract_classifier_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"failure classification contract/classifier misalignment:\n{joined}")
    assert_classifier_evidence_manifest_locked()
