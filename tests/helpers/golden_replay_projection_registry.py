"""Protected field extraction registry for golden replay projection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FieldClassification = Literal[
    "direct_runtime_fem",
    "derived_runtime_fem",
    "snapshot_transcript",
    "trace_debug",
    "derived_text",
    "synthetic_default_only",
]


@dataclass(frozen=True)
class _FlatObservedFieldExtractor:
    """Read-side 1:1 flat observed-key projection from FEM or sanitizer trace."""

    observed_key: str
    source: str  # "fem" | "sanitizer_trace"
    source_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class _SanitizerLineageObservedExtractor:
    """Sanitizer lineage observed key with trace lookup and context fallback."""

    observed_key: str
    trace_key: str
    fallback_context_key: str


@dataclass(frozen=True)
class _ProtectedExtractionSpec:
    """Registry-backed extraction metadata for one protected observation path."""

    path: str
    source: str
    fem_source_keys: tuple[str, ...] = ()
    sanitizer_lineage_trace_key: str = ""
    sanitizer_lineage_context_key: str = ""
    trace_container: str = ""
    raw_presence: str = "none"
    normalized_presence: bool = False
    unavailable_key: str = ""


def _flat_extractor_source_keys(extractor: _FlatObservedFieldExtractor) -> tuple[str, ...]:
    return extractor.source_keys or (extractor.observed_key,)


def _protected_extraction_spec(
    path: str,
    *,
    source: str,
    fem_source_keys: tuple[str, ...] = (),
    sanitizer_lineage_trace_key: str = "",
    sanitizer_lineage_context_key: str = "",
    trace_container: str = "",
    raw_presence: str = "none",
    normalized_presence: bool = False,
    unavailable_key: str = "",
) -> _ProtectedExtractionSpec:
    return _ProtectedExtractionSpec(
        path=path,
        source=source,
        fem_source_keys=fem_source_keys,
        sanitizer_lineage_trace_key=sanitizer_lineage_trace_key,
        sanitizer_lineage_context_key=sanitizer_lineage_context_key,
        trace_container=trace_container,
        raw_presence=raw_presence,
        normalized_presence=normalized_presence,
        unavailable_key=unavailable_key,
    )


# Registry-backed extraction specs -- one entry per protected path (AO1).
_PROTECTED_EXTRACTION_SPECS: dict[str, _ProtectedExtractionSpec] = {
    "resolution_kind": _protected_extraction_spec("resolution_kind", source="resolution"),
    "route_kind": _protected_extraction_spec(
        "route_kind",
        source="route",
        raw_presence="route",
        unavailable_key="route_kind",
    ),
    "selected_speaker_id": _protected_extraction_spec(
        "selected_speaker_id",
        source="speaker",
        raw_presence="speaker",
        unavailable_key="selected_speaker_id",
    ),
    "final_emitted_source": _protected_extraction_spec(
        "final_emitted_source",
        source="fem_flat",
        fem_source_keys=("final_emitted_source", "final_route", "upstream_prepared_emission_source"),
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="final_emitted_source",
    ),
    "final_emission_mutation_lineage": _protected_extraction_spec(
        "final_emission_mutation_lineage",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "response_type_required": _protected_extraction_spec(
        "response_type_required",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_required",
    ),
    "response_type_candidate_ok": _protected_extraction_spec(
        "response_type_candidate_ok",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_candidate_ok",
    ),
    "response_type_repair_used": _protected_extraction_spec(
        "response_type_repair_used",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_repair_used",
    ),
    "response_type_repair_kind": _protected_extraction_spec("response_type_repair_kind", source="fem_flat"),
    "upstream_prepared_emission_used": _protected_extraction_spec(
        "upstream_prepared_emission_used",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_valid": _protected_extraction_spec(
        "upstream_prepared_emission_valid",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_source": _protected_extraction_spec(
        "upstream_prepared_emission_source",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_reject_reason": _protected_extraction_spec(
        "upstream_prepared_emission_reject_reason",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "sanitizer_empty_fallback_used": _protected_extraction_spec(
        "sanitizer_empty_fallback_used",
        source="sanitizer_trace",
    ),
    "sanitizer_empty_fallback_source": _protected_extraction_spec(
        "sanitizer_empty_fallback_source",
        source="sanitizer_trace",
    ),
    "sanitizer_empty_fallback_owner": _protected_extraction_spec(
        "sanitizer_empty_fallback_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_lineage_mode": _protected_extraction_spec(
        "sanitizer_lineage_mode",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_mode",
        sanitizer_lineage_context_key="sanitizer_mode",
    ),
    "sanitizer_lineage_changed_count": _protected_extraction_spec(
        "sanitizer_lineage_changed_count",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_changed_count",
        sanitizer_lineage_context_key="sanitizer_changed_count",
    ),
    "sanitizer_lineage_dropped_count": _protected_extraction_spec(
        "sanitizer_lineage_dropped_count",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_dropped_count",
        sanitizer_lineage_context_key="sanitizer_dropped_count",
    ),
    "sanitizer_lineage_empty_fallback_used": _protected_extraction_spec(
        "sanitizer_lineage_empty_fallback_used",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_empty_fallback_used",
        sanitizer_lineage_context_key="sanitizer_empty_fallback_used",
    ),
    "sanitizer_lineage_legacy_rewrite_active": _protected_extraction_spec(
        "sanitizer_lineage_legacy_rewrite_active",
        source="sanitizer_lineage_legacy",
        sanitizer_lineage_trace_key="sanitizer_lineage_legacy_rewrite_active",
    ),
    "sanitizer_strict_social_fallback_used": _protected_extraction_spec(
        "sanitizer_strict_social_fallback_used",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_selection_owner": _protected_extraction_spec(
        "sanitizer_strict_social_selection_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_prose_owner": _protected_extraction_spec(
        "sanitizer_strict_social_prose_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_source": _protected_extraction_spec(
        "sanitizer_strict_social_source",
        source="sanitizer_trace",
    ),
    "opening_recovered_via_fallback": _protected_extraction_spec(
        "opening_recovered_via_fallback",
        source="fem_flat",
    ),
    "opening_fallback_authorship_source": _protected_extraction_spec(
        "opening_fallback_authorship_source",
        source="fem_flat",
    ),
    "opening_fallback_owner_bucket": _protected_extraction_spec(
        "opening_fallback_owner_bucket",
        source="fem_opening_bucket",
    ),
    "sealed_fallback_owner_bucket": _protected_extraction_spec(
        "sealed_fallback_owner_bucket",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_owner_bucket": _protected_extraction_spec(
        "visibility_fallback_owner_bucket",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_replacement_applied": _protected_extraction_spec(
        "visibility_replacement_applied",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_pool": _protected_extraction_spec(
        "visibility_fallback_pool",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_kind": _protected_extraction_spec(
        "visibility_fallback_kind",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "fallback_family": _protected_extraction_spec(
        "fallback_family",
        source="fallback_family",
        raw_presence="fem_dual_family",
        normalized_presence=True,
        unavailable_key="fallback_family",
    ),
    "fallback_temporal_frame": _protected_extraction_spec(
        "fallback_temporal_frame",
        source="fem_flat",
    ),
    "trace.canonical_entry.target_actor_id": _protected_extraction_spec(
        "trace.canonical_entry.target_actor_id",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.canonical_entry.target_source": _protected_extraction_spec(
        "trace.canonical_entry.target_source",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.canonical_entry.reason": _protected_extraction_spec(
        "trace.canonical_entry.reason",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.social_contract_trace.route_selected": _protected_extraction_spec(
        "trace.social_contract_trace.route_selected",
        source="trace_leaf",
        trace_container="social_contract_trace",
    ),
    "final_text": _protected_extraction_spec("final_text", source="final_text"),
    "scaffold_leakage": _protected_extraction_spec("scaffold_leakage", source="scaffold"),
}

# Neutral flat defaults for protected observation paths (None unless overridden).
_PROTECTED_FLAT_DEFAULT_OVERRIDES: dict[str, Any] = {
    "final_text": "",
    "scaffold_leakage": False,
}

# Trace container presence/unavailable policy (parent containers under observed["trace"]).
_TRACE_CONTAINER_RAW_PRESENCE: tuple[tuple[str, str], ...] = (
    ("trace.canonical_entry", "canonical_entry"),
    ("trace.turn_trace", "turn_trace"),
    ("trace.social_contract_trace", "social_contract_trace"),
)
_TRACE_CONTAINER_UNAVAILABLE_KEYS: frozenset[str] = frozenset(
    key for key, _container in _TRACE_CONTAINER_RAW_PRESENCE
)


@dataclass(frozen=True)
class _ExtractionSourceOwnership:
    """Canonical read-side ownership metadata for one extraction source kind."""

    source_path: str
    source_family: str
    field_owner_group: str
    classification: FieldClassification
    test_owner: str


_EXTRACTION_SOURCE_OWNERSHIP: dict[str, _ExtractionSourceOwnership] = {
    "resolution": _ExtractionSourceOwnership(
        source_path="payload.resolution.kind",
        source_family="payload_resolution",
        field_owner_group="runtime_resolution_payload",
        classification="direct_runtime_fem",
        test_owner="test_golden_replay_projection.py",
    ),
    "route": _ExtractionSourceOwnership(
        source_path=(
            "trace.social_contract_trace.route_selected -> snap.debug.resolution_compact.kind "
            "-> payload.resolution.kind"
        ),
        source_family="trace_or_snapshot_route",
        field_owner_group="replay_route_projection",
        classification="snapshot_transcript",
        test_owner="test_cf1_route_and_trace_precedence.py",
    ),
    "speaker": _ExtractionSourceOwnership(
        source_path=(
            "social_contract_trace speaker keys -> transcript snapshot -> resolution.social.npc_id"
        ),
        source_family="trace_or_snapshot_speaker",
        field_owner_group="replay_speaker_projection",
        classification="snapshot_transcript",
        test_owner="test_cf1_speaker_projection_precedence.py",
    ),
    "fem_flat": _ExtractionSourceOwnership(
        source_path="FEM sidecar (read_fem_from_turn_for_replay)",
        source_family="fem_metadata",
        field_owner_group="final_emission_metadata",
        classification="direct_runtime_fem",
        test_owner="test_final_emission_meta.py",
    ),
    "sanitizer_trace": _ExtractionSourceOwnership(
        source_path="payload.metadata.sanitizer_trace",
        source_family="sanitizer_trace",
        field_owner_group="sanitizer_projection",
        classification="direct_runtime_fem",
        test_owner="test_golden_replay_fallback_sanitizer_projection.py",
    ),
    "sanitizer_lineage": _ExtractionSourceOwnership(
        source_path="sanitizer_trace key -> sanitizer lineage context fallback",
        source_family="sanitizer_lineage",
        field_owner_group="sanitizer_projection",
        classification="derived_runtime_fem",
        test_owner="test_golden_replay_fallback_sanitizer_projection.py",
    ),
    "sanitizer_lineage_legacy": _ExtractionSourceOwnership(
        source_path="sanitizer_trace key -> derived from sanitizer_lineage_mode",
        source_family="sanitizer_lineage",
        field_owner_group="sanitizer_projection",
        classification="derived_runtime_fem",
        test_owner="test_golden_replay_fallback_sanitizer_projection.py",
    ),
    "fem_opening_bucket": _ExtractionSourceOwnership(
        source_path="read_opening_fallback_owner_bucket_for_replay(FEM)",
        source_family="fem_owner_bucket_read_view",
        field_owner_group="owner_bucket_read_views",
        classification="derived_runtime_fem",
        test_owner="test_golden_replay_fallback_opening_projection.py",
    ),
    "fallback_family": _ExtractionSourceOwnership(
        source_path="project_replay_fallback_family_from_fem -> lineage bridge",
        source_family="fem_fallback_family_compatibility",
        field_owner_group="replay_fallback_family_projection",
        classification="derived_runtime_fem",
        test_owner="test_cf1_fallback_family_precedence.py",
    ),
    "final_text": _ExtractionSourceOwnership(
        source_path="snap.gm_text",
        source_family="snapshot_text",
        field_owner_group="replay_snapshot_text_projection",
        classification="snapshot_transcript",
        test_owner="test_golden_replay_projection.py",
    ),
    "scaffold": _ExtractionSourceOwnership(
        source_path="final_text_has_scaffold_leakage(final_text)",
        source_family="derived_text_quality",
        field_owner_group="replay_text_quality_projection",
        classification="derived_text",
        test_owner="test_golden_replay_projection.py",
    ),
    "trace_leaf": _ExtractionSourceOwnership(
        source_path="debug trace container leaf",
        source_family="debug_trace",
        field_owner_group="replay_trace_projection",
        classification="trace_debug",
        test_owner="test_golden_replay_projection.py",
    ),
}

_FIELD_OWNER_GROUP_BY_PATH: dict[str, str] = {
    "response_type_required": "response_type_metadata",
    "response_type_candidate_ok": "response_type_metadata",
    "response_type_repair_used": "response_type_metadata",
    "response_type_repair_kind": "response_type_metadata",
    "upstream_prepared_emission_used": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_valid": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_source": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_metadata",
    "opening_recovered_via_fallback": "opening_fallback_metadata",
    "opening_fallback_authorship_source": "opening_fallback_metadata",
    "opening_fallback_owner_bucket": "owner_bucket_read_views",
    "sealed_fallback_owner_bucket": "sealed_fallback_metadata",
    "visibility_fallback_owner_bucket": "visibility_fallback_metadata",
    "visibility_replacement_applied": "visibility_fallback_metadata",
    "visibility_fallback_pool": "visibility_fallback_metadata",
    "visibility_fallback_kind": "visibility_fallback_metadata",
}


def protected_flat_observation_default(path: str) -> Any:
    """Return the neutral flat default for a protected observation path."""
    return _PROTECTED_FLAT_DEFAULT_OVERRIDES.get(path)


def protected_observation_flat_registry_paths() -> tuple[str, ...]:
    """Return sorted flat (non-dotted) protected extraction registry paths."""
    return tuple(sorted(path for path in _PROTECTED_EXTRACTION_SPECS if "." not in path))


def protected_observation_default_row() -> dict[str, Any]:
    """Neutral defaults for every flat protected observation registry path."""
    return {
        path: protected_flat_observation_default(path)
        for path in protected_observation_flat_registry_paths()
    }


def observed_projection_schema_defaults() -> dict[str, Any]:
    """Schema-aligned defaults for synthetic observed replay rows."""
    return {
        **protected_observation_default_row(),
        "trace": {
            "canonical_entry": {},
            "turn_trace": {},
            "social_contract_trace": {},
        },
        "unavailable": [],
    }


def protected_flat_extraction_sources() -> frozenset[str]:
    """Return extraction source kinds used by flat (non-dotted) protected paths."""
    return frozenset(
        spec.source for path, spec in _PROTECTED_EXTRACTION_SPECS.items() if "." not in path
    )


def protected_trace_extraction_sources() -> frozenset[str]:
    """Return extraction source kinds used by dotted protected paths."""
    return frozenset(
        spec.source for path, spec in _PROTECTED_EXTRACTION_SPECS.items() if "." in path
    )


def protected_trace_container_raw_presence() -> tuple[tuple[str, str], ...]:
    """Return ``(raw_presence_key, trace_container_key)`` rows for trace parents."""
    return _TRACE_CONTAINER_RAW_PRESENCE


def protected_trace_container_unavailable_keys() -> frozenset[str]:
    """Return trace parent keys listed in ``unavailable`` when containers are empty."""
    return _TRACE_CONTAINER_UNAVAILABLE_KEYS


def protected_extraction_source_ownership(source: str) -> _ExtractionSourceOwnership:
    """Return canonical ownership metadata for an extraction source kind."""
    return _EXTRACTION_SOURCE_OWNERSHIP[source]


def protected_field_owner_group(path: str) -> str:
    """Return the canonical field-owner group for a protected observation path."""
    spec = _PROTECTED_EXTRACTION_SPECS[path]
    return _FIELD_OWNER_GROUP_BY_PATH.get(
        path,
        _EXTRACTION_SOURCE_OWNERSHIP[spec.source].field_owner_group,
    )


def protected_observation_extraction_registry() -> dict[str, _ProtectedExtractionSpec]:
    """Return the canonical protected-field extraction registry (AO1)."""
    return dict(_PROTECTED_EXTRACTION_SPECS)


def protected_observation_extraction_source_by_path() -> dict[str, str]:
    """Return ``path -> extraction source`` from the protected extraction registry."""
    return {path: spec.source for path, spec in _PROTECTED_EXTRACTION_SPECS.items()}


def _validate_protected_extraction_source_ownership() -> None:
    registry_sources = {spec.source for spec in _PROTECTED_EXTRACTION_SPECS.values()}
    ownership_sources = set(_EXTRACTION_SOURCE_OWNERSHIP)
    if registry_sources != ownership_sources:
        missing = sorted(registry_sources - ownership_sources)
        extra = sorted(ownership_sources - registry_sources)
        raise AssertionError(
            "Protected extraction source ownership must cover every registry source; "
            f"missing={missing!r} extra={extra!r}"
        )


def _fem_flat_extractors_from_registry() -> tuple[_FlatObservedFieldExtractor, ...]:
    extractors: list[_FlatObservedFieldExtractor] = []
    for spec in _PROTECTED_EXTRACTION_SPECS.values():
        if spec.source != "fem_flat":
            continue
        extractors.append(
            _FlatObservedFieldExtractor(
                spec.path,
                "fem",
                spec.fem_source_keys or (spec.path,),
            )
        )
    return tuple(extractors)


def _sanitizer_trace_extractors_from_registry() -> tuple[_FlatObservedFieldExtractor, ...]:
    return tuple(
        _FlatObservedFieldExtractor(spec.path, "sanitizer_trace")
        for spec in _PROTECTED_EXTRACTION_SPECS.values()
        if spec.source == "sanitizer_trace"
    )


def _sanitizer_lineage_extractors_from_registry() -> tuple[_SanitizerLineageObservedExtractor, ...]:
    return tuple(
        _SanitizerLineageObservedExtractor(
            spec.path,
            spec.sanitizer_lineage_trace_key,
            spec.sanitizer_lineage_context_key,
        )
        for spec in _PROTECTED_EXTRACTION_SPECS.values()
        if spec.source == "sanitizer_lineage"
    )


_validate_protected_extraction_source_ownership()

_FEM_FLAT_OBSERVED_EXTRACTORS = _fem_flat_extractors_from_registry()
_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS = _sanitizer_trace_extractors_from_registry()
_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS = _sanitizer_lineage_extractors_from_registry()

# Compatibility aliases for legacy importers (derived from registry specs).
_HANDLED_FLAT_PROTECTED_SOURCES = protected_flat_extraction_sources()
_TRACE_NEST_PROTECTED_SOURCES = protected_trace_extraction_sources()
