"""Protected field extraction registry for golden replay projection."""
from __future__ import annotations

from dataclasses import dataclass

from tests.helpers.golden_replay_projection_fields import PROTECTED_OBSERVATION_FIELDS


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


def _validate_protected_extraction_registry() -> None:
    registry_paths = {field.path for field in PROTECTED_OBSERVATION_FIELDS}
    spec_paths = set(_PROTECTED_EXTRACTION_SPECS)
    if registry_paths != spec_paths:
        missing = sorted(registry_paths - spec_paths)
        extra = sorted(spec_paths - registry_paths)
        raise AssertionError(
            "Protected extraction registry must cover every PROTECTED_OBSERVATION_FIELDS path; "
            f"missing={missing!r} extra={extra!r}"
        )


def protected_observation_extraction_registry() -> dict[str, _ProtectedExtractionSpec]:
    """Return the canonical protected-field extraction registry (AO1)."""
    return dict(_PROTECTED_EXTRACTION_SPECS)


def protected_observation_extraction_source_by_path() -> dict[str, str]:
    """Return ``path -> extraction source`` from the protected extraction registry."""
    return {path: spec.source for path, spec in _PROTECTED_EXTRACTION_SPECS.items()}


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


_validate_protected_extraction_registry()

_FEM_FLAT_OBSERVED_EXTRACTORS = _fem_flat_extractors_from_registry()
_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS = _sanitizer_trace_extractors_from_registry()
_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS = _sanitizer_lineage_extractors_from_registry()
