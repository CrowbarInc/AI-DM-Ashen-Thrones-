"""Read-only ownership projection vocabulary (delegate facade).

Canonical tokens remain on :mod:`game.final_emission_ownership_schema`. This module
groups read-side projection vocabulary for replay lineage, sanitizer trace mapping,
and runtime telemetry — without write stamps or mapper authority.

Phase 2 will route ``runtime_lineage_telemetry``, ``output_sanitizer`` read constants,
and replay projection internals here.
"""
from __future__ import annotations

from game.final_emission_ownership_schema import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS,
    SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    SPEAKER_CONTRACT_ENFORCEMENT_LINEAGE_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_SELECTION_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_CONTENT_OWNER_BY_BUCKET,
    VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
    normalize_sanitizer_trace_owner_to_lineage_owner,
    ownership_schema_registry_surface,
)

__all__ = [
    "OPENING_FAIL_CLOSED_CONTENT_OWNER",
    "OPENING_FALLBACK_CONTENT_OWNER",
    "OPENING_FALLBACK_SELECTION_OWNER",
    "OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS",
    "SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_FALLBACK_SELECTION_OWNER",
    "SANITIZER_STRICT_SOCIAL_CONTENT_OWNER",
    "SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS",
    "SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER",
    "SANITIZER_TRACE_SELECTION_OWNER_SHORT",
    "SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT",
    "SEALED_FALLBACK_MODULE_CONTENT_OWNER",
    "SEALED_FALLBACK_SELECTION_OWNER",
    "SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER",
    "SPEAKER_CONTRACT_ENFORCEMENT_LINEAGE_OWNER",
    "STRICT_SOCIAL_FALLBACK_CONTENT_OWNER",
    "STRICT_SOCIAL_FALLBACK_SELECTION_OWNER",
    "UPSTREAM_FAST_FALLBACK_CONTENT_OWNER",
    "UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER",
    "UPSTREAM_FAST_FALLBACK_SELECTION_OWNER",
    "VISIBILITY_FALLBACK_CONTENT_OWNER_BY_BUCKET",
    "VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER",
    "VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY",
    "VISIBILITY_FALLBACK_OWNER_SEALED_GATE",
    "VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY",
    "VISIBILITY_FALLBACK_SELECTION_OWNER",
    "lineage_owner_vocabulary",
    "normalize_sanitizer_trace_owner_to_lineage_owner",
    "ownership_projection_views_surface",
    "sanitizer_trace_owner_vocabulary",
]

_LINEAGE_VOCABULARY_KEYS: tuple[str, ...] = (
    "allowed_fallback_selection_owners",
    "allowed_fallback_content_owners",
    "ownership_lineage_attribution_fields",
    "opening_fallback_selection_owner",
    "opening_fallback_content_owner",
    "opening_fail_closed_content_owner",
    "strict_social_fallback_selection_owner",
    "strict_social_fallback_content_owner",
    "sanitizer_fallback_selection_owner",
    "sanitizer_strict_social_content_owner",
    "sealed_fallback_selection_owner",
    "sealed_fallback_module_content_owner",
    "sealed_fallback_unknown_content_owner",
    "visibility_fallback_selection_owner",
    "visibility_fallback_content_owner_by_bucket",
    "visibility_fallback_default_content_owner",
    "upstream_fast_fallback_selection_owner",
    "upstream_fast_fallback_content_owner",
    "upstream_fast_fallback_provenance_packager",
    "speaker_contract_enforcement_lineage_owner",
)

_SANITIZER_VOCABULARY_KEYS: tuple[str, ...] = (
    "sanitizer_trace_owner_to_lineage_owner",
    "sanitizer_trace_owner_legacy_short_fields",
)


def lineage_owner_vocabulary() -> dict[str, object]:
    """Read-side split-owner / lineage projection vocabulary (diagnostic registry)."""
    surface = ownership_schema_registry_surface()
    return {key: surface[key] for key in _LINEAGE_VOCABULARY_KEYS if key in surface}


def sanitizer_trace_owner_vocabulary() -> dict[str, object]:
    """Read-side sanitizer trace short-name → lineage owner projection vocabulary."""
    surface = ownership_schema_registry_surface()
    return {
        key: surface[key]
        for key in _SANITIZER_VOCABULARY_KEYS
        if key in surface
    }


def ownership_projection_views_surface() -> dict[str, object]:
    """Diagnostic registry for BV10 Phase 2 ownership projection facade."""
    return {
        "facade": "game.ownership_projection_views",
        "delegate_module": "game.final_emission_ownership_schema",
        "lineage_owner_vocabulary": lineage_owner_vocabulary(),
        "sanitizer_trace_owner_vocabulary": sanitizer_trace_owner_vocabulary(),
        "ownership_lineage_attribution_fields": list(OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS),
        "normalize_sanitizer_trace_owner_to_lineage_owner": normalize_sanitizer_trace_owner_to_lineage_owner,
    }
