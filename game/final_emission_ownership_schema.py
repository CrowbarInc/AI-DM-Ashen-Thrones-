"""Narrow ownership and attribution schema vocabulary for final emission.

**Authority (CG-5):** runtime-owned split-owner tokens, fallback selection/content
owners, and opening/sealed/visibility owner-bucket string values.

**Does not own:** bucket mappers (``final_emission_owner_bucket_views``), FEM
packaging (``final_emission_meta``), attribution validation unions, or replay
contract mirrors (``failure_classification_contract`` re-exports for validation).

Registries:
``docs/audits/CG_attribution_contract_registry.md``,
``docs/audits/CG_failure_classification_authority_registry.md``

Constants and stable string tokens only. Stamp helpers, bucket mappers, and lineage
projection logic remain in :mod:`game.final_emission_meta` and
:mod:`game.final_emission_replay_projection`.
"""
from __future__ import annotations

from typing import Any

from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    GPT_BUDGET_OR_PROVIDER_FAILURE,
    LEGACY_DIEGETIC_FALLBACK,
    LEGACY_UNCLASSIFIED,
    PLANNER_CONVERGENCE_SEAM_FAILURE,
    PLAN_BACKED_GPT_REALIZATION,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
)

# --- Owner-bucket string values (Cycle BK1) ---

OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED = "upstream-prepared"
OPENING_FALLBACK_OWNER_SEALED_GATE = "sealed-gate"
OPENING_FALLBACK_OWNER_RETRY = "retry"
OPENING_FALLBACK_OWNER_STRICT_SOCIAL = "strict-social"
OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS = "unknown-ambiguous"

OPENING_FALLBACK_OWNER_BUCKETS: frozenset[str] = frozenset(
    {
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        OPENING_FALLBACK_OWNER_SEALED_GATE,
        OPENING_FALLBACK_OWNER_RETRY,
        OPENING_FALLBACK_OWNER_STRICT_SOCIAL,
        OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    }
)

SEALED_FALLBACK_OWNER_SEALED_GATE = "sealed-gate"
SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED = "strict-social-sealed"
SEALED_FALLBACK_OWNER_UNKNOWN_NONE = "unknown-none"
SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS = "unknown-ambiguous"

SEALED_FALLBACK_OWNER_BUCKETS: frozenset[str] = frozenset(
    {
        SEALED_FALLBACK_OWNER_SEALED_GATE,
        SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
        SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
        SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    }
)

VISIBILITY_FALLBACK_OWNER_SEALED_GATE = "sealed-gate"
VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY = "strict-social-visibility"
VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY = "opening-visibility"
VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE = "unknown-none"
VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS = "unknown-ambiguous"

VISIBILITY_FALLBACK_OWNER_BUCKETS: frozenset[str] = frozenset(
    {
        VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
        VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
        VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
        VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    }
)

# --- Canonical module-owner tokens (split-owner lineage / provenance) ---

OPENING_FALLBACK_SELECTION_OWNER: str = "game.final_emission_gate"
OPENING_FALLBACK_CONTENT_OWNER: str = "game.opening_deterministic_fallback"
OPENING_FAIL_CLOSED_CONTENT_OWNER: str = "game.final_emission_gate"

STRICT_SOCIAL_FALLBACK_SELECTION_OWNER: str = "game.final_emission_gate"
STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: str = "game.social_exchange_emission"

SANITIZER_FALLBACK_SELECTION_OWNER: str = "game.output_sanitizer"
SANITIZER_STRICT_SOCIAL_CONTENT_OWNER: str = "game.social_exchange_emission"

SEALED_FALLBACK_SELECTION_OWNER: str = OPENING_FALLBACK_SELECTION_OWNER
SEALED_FALLBACK_MODULE_CONTENT_OWNER: str = "game.final_emission_sealed_fallback"
SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: str = OPENING_FALLBACK_SELECTION_OWNER

VISIBILITY_FALLBACK_SELECTION_OWNER: str = "game.final_emission_visibility_fallback"
VISIBILITY_FALLBACK_CONTENT_OWNER_BY_BUCKET: dict[str, str] = {
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY: OPENING_FALLBACK_CONTENT_OWNER,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY: STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE: SEALED_FALLBACK_MODULE_CONTENT_OWNER,
}
VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER: str = SEALED_FALLBACK_MODULE_CONTENT_OWNER

SPEAKER_CONTRACT_ENFORCEMENT_LINEAGE_OWNER: str = "game.speaker_contract_enforcement"

UPSTREAM_FAST_FALLBACK_SELECTION_OWNER: str = "game.api"
UPSTREAM_FAST_FALLBACK_CONTENT_OWNER: str = "game.gm_retry"
UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER: str = "game.fallback_provenance_debug"

# BU10 — classifier/golden-replay contract lock for projected split-owner lineage fields.
ALLOWED_FALLBACK_SELECTION_OWNERS: frozenset[str] = frozenset(
    {
        OPENING_FALLBACK_SELECTION_OWNER,
        STRICT_SOCIAL_FALLBACK_SELECTION_OWNER,
        SANITIZER_FALLBACK_SELECTION_OWNER,
        SEALED_FALLBACK_SELECTION_OWNER,
        VISIBILITY_FALLBACK_SELECTION_OWNER,
        UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    }
)
ALLOWED_FALLBACK_CONTENT_OWNERS: frozenset[str] = frozenset(
    {
        OPENING_FALLBACK_CONTENT_OWNER,
        OPENING_FAIL_CLOSED_CONTENT_OWNER,
        STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        SANITIZER_FALLBACK_SELECTION_OWNER,
        SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER,
        *VISIBILITY_FALLBACK_CONTENT_OWNER_BY_BUCKET.values(),
    }
)

# --- Sanitizer trace short-name tokens (mapped to canonical owners at projection) ---

SANITIZER_TRACE_SELECTION_OWNER_SHORT: str = "output_sanitizer"
SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT: str = "strict_social_emission"

SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER: dict[str, str] = {
    SANITIZER_TRACE_SELECTION_OWNER_SHORT: SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT: SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
}

# Legacy short-name companions stamped alongside canonical ownership fields (BU6).
SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: str = "sanitizer_empty_fallback_owner_trace_short"
SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: str = (
    "sanitizer_strict_social_selection_owner_trace_short"
)
SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: str = (
    "sanitizer_strict_social_prose_owner_trace_short"
)

SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS: tuple[str, ...] = (
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
)


def normalize_sanitizer_trace_owner_to_lineage_owner(
    value: Any,
    *,
    default: str,
) -> str:
    """Map sanitizer trace owner token (short or canonical) to canonical ``game.*`` lineage owner."""
    if not isinstance(value, str) or not value.strip():
        return default
    raw = value.strip()
    mapped = SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER.get(raw)
    if mapped:
        return mapped
    if raw.startswith("game."):
        return raw
    return default


# --- Opening fallback authorship vocabulary ---

OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED: str = "upstream_prepared_opening_fallback"

OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES: frozenset[str] = frozenset(
    {
        "upstream_prepared",
        "upstream_prepared_opening_fallback",
    }
)

# Cycle AP1: retired gate-local opening composer authorship tokens (read-side only).
OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES: frozenset[str] = frozenset(
    {
        "compatibility_local",
        "compatibility_local_opening_deterministic",
    }
)

# --- Lineage attribution field names ---

OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS: tuple[str, ...] = (
    "fallback_authorship_source",
    "fallback_owner_bucket",
    "fallback_selection_owner",
    "fallback_content_owner",
)

# --- Governed realization fallback family tokens (re-exported for ownership surfaces) ---

GOVERNED_REALIZATION_FALLBACK_FAMILIES: frozenset[str] = frozenset(
    {
        PLAN_BACKED_GPT_REALIZATION,
        UPSTREAM_PREPARED_EMISSION,
        STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
        PLANNER_CONVERGENCE_SEAM_FAILURE,
        GPT_BUDGET_OR_PROVIDER_FAILURE,
        RETRY_TERMINAL_FALLBACK,
        GATE_TERMINAL_REPAIR,
        LEGACY_DIEGETIC_FALLBACK,
        LEGACY_UNCLASSIFIED,
    }
)


def fallback_owner_bucket_registry_surface() -> dict[str, dict[str, str]]:
    """Named constant→value maps for each fallback owner-bucket family (diagnostic only)."""
    return {
        "opening": {
            "OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            "OPENING_FALLBACK_OWNER_SEALED_GATE": OPENING_FALLBACK_OWNER_SEALED_GATE,
            "OPENING_FALLBACK_OWNER_RETRY": OPENING_FALLBACK_OWNER_RETRY,
            "OPENING_FALLBACK_OWNER_STRICT_SOCIAL": OPENING_FALLBACK_OWNER_STRICT_SOCIAL,
            "OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS": OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        },
        "sealed": {
            "SEALED_FALLBACK_OWNER_SEALED_GATE": SEALED_FALLBACK_OWNER_SEALED_GATE,
            "SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED": SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            "SEALED_FALLBACK_OWNER_UNKNOWN_NONE": SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
            "SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS": SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        },
        "visibility": {
            "VISIBILITY_FALLBACK_OWNER_SEALED_GATE": VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            "VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY": VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
            "VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY": VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
            "VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE": VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
            "VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS": VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        },
    }


def ownership_schema_registry_surface() -> dict[str, object]:
    """Diagnostic registry for narrow ownership schema vocabulary (BU5)."""
    return {
        "opening_fallback_owner_buckets": sorted(OPENING_FALLBACK_OWNER_BUCKETS),
        "sealed_fallback_owner_buckets": sorted(SEALED_FALLBACK_OWNER_BUCKETS),
        "visibility_fallback_owner_buckets": sorted(VISIBILITY_FALLBACK_OWNER_BUCKETS),
        "fallback_owner_bucket_registries": fallback_owner_bucket_registry_surface(),
        "opening_fallback_selection_owner": OPENING_FALLBACK_SELECTION_OWNER,
        "opening_fallback_content_owner": OPENING_FALLBACK_CONTENT_OWNER,
        "strict_social_fallback_selection_owner": STRICT_SOCIAL_FALLBACK_SELECTION_OWNER,
        "strict_social_fallback_content_owner": STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        "sanitizer_fallback_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
        "sanitizer_strict_social_content_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        "sealed_fallback_selection_owner": SEALED_FALLBACK_SELECTION_OWNER,
        "sealed_fallback_module_content_owner": SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        "visibility_fallback_selection_owner": VISIBILITY_FALLBACK_SELECTION_OWNER,
        "visibility_fallback_content_owner_by_bucket": dict(
            sorted(VISIBILITY_FALLBACK_CONTENT_OWNER_BY_BUCKET.items())
        ),
        "visibility_fallback_default_content_owner": VISIBILITY_FALLBACK_DEFAULT_CONTENT_OWNER,
        "allowed_fallback_selection_owners": sorted(ALLOWED_FALLBACK_SELECTION_OWNERS),
        "allowed_fallback_content_owners": sorted(ALLOWED_FALLBACK_CONTENT_OWNERS),
        "upstream_fast_fallback_selection_owner": UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        "upstream_fast_fallback_content_owner": UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        "upstream_fast_fallback_provenance_packager": UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER,
        "speaker_contract_enforcement_lineage_owner": SPEAKER_CONTRACT_ENFORCEMENT_LINEAGE_OWNER,
        "sanitizer_trace_owner_to_lineage_owner": dict(SANITIZER_TRACE_OWNER_TO_LINEAGE_OWNER),
        "sanitizer_trace_owner_legacy_short_fields": list(SANITIZER_TRACE_OWNER_LEGACY_SHORT_FIELDS),
        "ownership_lineage_attribution_fields": list(OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS),
        "realization_fallback_family_field": REALIZATION_FALLBACK_FAMILY_FIELD,
        "governed_realization_fallback_families": sorted(GOVERNED_REALIZATION_FALLBACK_FAMILIES),
        "opening_fallback_authorship_upstream_prepared": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        "opening_fallback_legacy_compatibility_local_authorship_sources": sorted(
            OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES
        ),
    }
