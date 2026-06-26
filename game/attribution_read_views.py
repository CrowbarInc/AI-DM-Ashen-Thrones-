"""Delegate-only read facade for attribution lookups and owner-bucket projections.

**Authority (CG-5):** none — re-exports only. Canonical bucket strings live in
``game.final_emission_ownership_schema``; mappers in
``game.final_emission_owner_bucket_views``. Attribution contract **validates**
mirrored bucket sets imported via ``failure_classification_contract``.

Registries:
``docs/audits/CG_attribution_contract_registry.md``,
``docs/audits/CG_failure_classification_authority_registry.md``

This module adds **no** ownership authority, write paths, or mapper logic.
"""
from __future__ import annotations

from game.final_emission_owner_bucket_views import (
    OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES,
    OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
    OPENING_FALLBACK_OWNER_BUCKETS,
    OPENING_FALLBACK_OWNER_RETRY,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_STRICT_SOCIAL,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
    opening_fallback_owner_bucket_from_fields,
    opening_fallback_owner_bucket_from_meta,
    sealed_fallback_owner_bucket_from_fields,
    visibility_fallback_owner_bucket_from_fields,
)
from game.final_emission_ownership_schema import (
    ALLOWED_FALLBACK_CONTENT_OWNERS,
    ALLOWED_FALLBACK_SELECTION_OWNERS,
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_SELECTION_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
    fallback_owner_bucket_registry_surface,
    ownership_schema_registry_surface,
)

__all__ = [
    "ALLOWED_FALLBACK_CONTENT_OWNERS",
    "ALLOWED_FALLBACK_SELECTION_OWNERS",
    "OPENING_FAIL_CLOSED_CONTENT_OWNER",
    "OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES",
    "OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED",
    "OPENING_FALLBACK_CONTENT_OWNER",
    "OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES",
    "OPENING_FALLBACK_OWNER_BUCKETS",
    "OPENING_FALLBACK_OWNER_RETRY",
    "OPENING_FALLBACK_OWNER_SEALED_GATE",
    "OPENING_FALLBACK_OWNER_STRICT_SOCIAL",
    "OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED",
    "OPENING_FALLBACK_SELECTION_OWNER",
    "SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_FALLBACK_SELECTION_OWNER",
    "SANITIZER_STRICT_SOCIAL_CONTENT_OWNER",
    "SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD",
    "SANITIZER_TRACE_SELECTION_OWNER_SHORT",
    "SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT",
    "SEALED_FALLBACK_MODULE_CONTENT_OWNER",
    "SEALED_FALLBACK_OWNER_BUCKETS",
    "SEALED_FALLBACK_OWNER_SEALED_GATE",
    "SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED",
    "SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "SEALED_FALLBACK_OWNER_UNKNOWN_NONE",
    "SEALED_FALLBACK_SELECTION_OWNER",
    "SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER",
    "STRICT_SOCIAL_FALLBACK_CONTENT_OWNER",
    "STRICT_SOCIAL_FALLBACK_SELECTION_OWNER",
    "UPSTREAM_FAST_FALLBACK_CONTENT_OWNER",
    "UPSTREAM_FAST_FALLBACK_SELECTION_OWNER",
    "VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER",
    "VISIBILITY_FALLBACK_OWNER_BUCKETS",
    "VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY",
    "VISIBILITY_FALLBACK_OWNER_SEALED_GATE",
    "VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY",
    "VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE",
    "VISIBILITY_FALLBACK_SELECTION_OWNER",
    "attribution_read_views_surface",
    "fallback_owner_bucket_registry_surface",
    "opening_fallback_owner_bucket_from_fields",
    "opening_fallback_owner_bucket_from_meta",
    "ownership_schema_registry_surface",
    "sealed_fallback_owner_bucket_from_fields",
    "visibility_fallback_owner_bucket_from_fields",
]

_LINEAGE_VOCABULARY_KEYS: tuple[str, ...] = (
    "allowed_fallback_selection_owners",
    "allowed_fallback_content_owners",
    "ownership_lineage_attribution_fields",
    "opening_fallback_selection_owner",
    "opening_fallback_content_owner",
    "strict_social_fallback_selection_owner",
    "strict_social_fallback_content_owner",
    "sanitizer_fallback_selection_owner",
    "sanitizer_strict_social_content_owner",
    "sealed_fallback_selection_owner",
    "sealed_fallback_module_content_owner",
    "visibility_fallback_selection_owner",
    "visibility_fallback_content_owner_by_bucket",
    "visibility_fallback_default_content_owner",
    "upstream_fast_fallback_selection_owner",
    "upstream_fast_fallback_content_owner",
)


def attribution_read_views_surface() -> dict[str, object]:
    """Diagnostic registry for BV10 Phase 2 attribution read facade (no live payload reads)."""
    schema_surface = ownership_schema_registry_surface()
    return {
        "facade": "game.attribution_read_views",
        "delegate_modules": [
            "game.final_emission_ownership_schema",
            "game.final_emission_owner_bucket_views",
        ],
        "bucket_mappers": [
            "opening_fallback_owner_bucket_from_fields",
            "opening_fallback_owner_bucket_from_meta",
            "visibility_fallback_owner_bucket_from_fields",
            "sealed_fallback_owner_bucket_from_fields",
        ],
        "opening_fallback_owner_buckets": sorted(OPENING_FALLBACK_OWNER_BUCKETS),
        "sealed_fallback_owner_buckets": sorted(SEALED_FALLBACK_OWNER_BUCKETS),
        "visibility_fallback_owner_buckets": sorted(VISIBILITY_FALLBACK_OWNER_BUCKETS),
        "allowed_fallback_selection_owners": sorted(ALLOWED_FALLBACK_SELECTION_OWNERS),
        "allowed_fallback_content_owners": sorted(ALLOWED_FALLBACK_CONTENT_OWNERS),
        "lineage_owner_vocabulary": {
            key: schema_surface[key] for key in _LINEAGE_VOCABULARY_KEYS if key in schema_surface
        },
        "fallback_owner_bucket_registries": fallback_owner_bucket_registry_surface(),
    }
