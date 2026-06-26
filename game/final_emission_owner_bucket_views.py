"""Read-only owner-bucket projections over FEM fields.

Canonical bucket string values remain in :mod:`game.final_emission_ownership_schema`.
This module owns **read-side mapping only** — no stamps, routing, or write authority.

Write-time bucket stamping stays on :mod:`game.final_emission_meta`.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_ownership_schema import (
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
)

__all__ = [
    "OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES",
    "OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES",
    "OPENING_FALLBACK_OWNER_BUCKETS",
    "OPENING_FALLBACK_OWNER_RETRY",
    "OPENING_FALLBACK_OWNER_SEALED_GATE",
    "OPENING_FALLBACK_OWNER_STRICT_SOCIAL",
    "OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED",
    "SEALED_FALLBACK_OWNER_BUCKETS",
    "SEALED_FALLBACK_OWNER_SEALED_GATE",
    "SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED",
    "SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "SEALED_FALLBACK_OWNER_UNKNOWN_NONE",
    "VISIBILITY_FALLBACK_OWNER_BUCKETS",
    "VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY",
    "VISIBILITY_FALLBACK_OWNER_SEALED_GATE",
    "VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY",
    "VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS",
    "VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE",
    "opening_fallback_owner_bucket_from_fields",
    "opening_fallback_owner_bucket_from_meta",
    "sealed_fallback_owner_bucket_from_fields",
    "visibility_fallback_owner_bucket_from_fields",
]

_OPENING_FALLBACK_STRICT_SOCIAL_SIGNALS: frozenset[str] = frozenset(
    {
        "minimal_social_emergency_fallback",
        "strict_social_dialogue_repair",
        "strict_social_deterministic_fallback",
        "strict_social_replacement",
        "strict_social_terminal_fallback",
    }
)
_OPENING_FALLBACK_RETRY_SIGNALS: frozenset[str] = frozenset(
    {
        "retry_deterministic_fallback",
        "retry_terminal_fallback",
        "forced_retry_fallback",
        "retry_escape_hatch",
        "question_retry_fallback",
        "social_exchange_retry_fallback",
    }
)


def _opening_owner_norm(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_")


def _opening_owner_bool(value: Any) -> bool:
    return value is True


def opening_fallback_owner_bucket_from_fields(
    *,
    final_emitted_source: str | None = None,
    opening_recovered_via_fallback: bool | None = None,
    opening_fallback_authorship_source: str | None = None,
    response_type_repair_kind: str | None = None,
    fallback_family: str | None = None,
    fallback_temporal_frame: str | None = None,
) -> str:
    """Map existing opening fallback telemetry to one conservative owner bucket.

    Read-side only: this does not select, repair, or authorize fallback text.

    Retired compatibility-local authorship (``OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES``):
    production must not emit it; read-side handling exists only for legacy/test/replay evidence
    via the canonical token ``compatibility_local_opening_deterministic``; any injected legacy
    token maps to ``unknown-ambiguous`` by design. The shorter ``compatibility_local`` token was
    retired from this registry (CK Block 5) because it overlaps non-opening bucket vocabulary.
    """
    del fallback_temporal_frame  # Family/timeframe are insufficient ownership signals by themselves.

    final_source = _opening_owner_norm(final_emitted_source)
    authorship = _opening_owner_norm(opening_fallback_authorship_source)
    repair_kind = _opening_owner_norm(response_type_repair_kind)
    family = _opening_owner_norm(fallback_family)

    fail_closed = (
        repair_kind == "opening_deterministic_fallback_failed_closed"
        or "opening_fallback_failed_closed" in final_source
    )
    if fail_closed:
        return OPENING_FALLBACK_OWNER_SEALED_GATE

    if authorship in OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES:
        return OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS

    explicit_strict_social = (
        final_source in _OPENING_FALLBACK_STRICT_SOCIAL_SIGNALS
        or repair_kind in _OPENING_FALLBACK_STRICT_SOCIAL_SIGNALS
        or authorship in _OPENING_FALLBACK_STRICT_SOCIAL_SIGNALS
    )
    if explicit_strict_social:
        return OPENING_FALLBACK_OWNER_STRICT_SOCIAL

    explicit_retry = (
        final_source in _OPENING_FALLBACK_RETRY_SIGNALS
        or repair_kind in _OPENING_FALLBACK_RETRY_SIGNALS
        or authorship in _OPENING_FALLBACK_RETRY_SIGNALS
    )
    if explicit_retry:
        return OPENING_FALLBACK_OWNER_RETRY

    opening_signal = (
        _opening_owner_bool(opening_recovered_via_fallback)
        or "opening" in final_source
        or "opening" in repair_kind
        or family == "scene_opening"
    )
    if authorship in OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES and opening_signal:
        return OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED

    return OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS


def opening_fallback_owner_bucket_from_meta(meta: Mapping[str, Any] | None) -> str:
    """Return a normalized opening fallback owner bucket from FEM-shaped metadata."""
    if not isinstance(meta, Mapping) or not meta:
        return OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
    final_source = meta.get("final_emitted_source")
    recovered = meta.get("opening_recovered_via_fallback")
    authorship = meta.get("opening_fallback_authorship_source")
    repair_kind = meta.get("response_type_repair_kind")
    family = meta.get("fallback_family_used")
    if not isinstance(family, str):
        family = meta.get("fallback_family")
    temporal = meta.get("fallback_temporal_frame")
    return opening_fallback_owner_bucket_from_fields(
        final_emitted_source=final_source if isinstance(final_source, str) else None,
        opening_recovered_via_fallback=recovered if isinstance(recovered, bool) else None,
        opening_fallback_authorship_source=authorship if isinstance(authorship, str) else None,
        response_type_repair_kind=repair_kind if isinstance(repair_kind, str) else None,
        fallback_family=family if isinstance(family, str) else None,
        fallback_temporal_frame=temporal if isinstance(temporal, str) else None,
    )


def visibility_fallback_owner_bucket_from_fields(
    *,
    fallback_pool: str = "",
    fallback_kind: str = "",
    final_emitted_source: str = "",
) -> str:
    """Map visibility fallback pool/kind/source signals to one owner bucket.

    Read-side only: does not select fallback text or drive gate orchestration.
    """
    pool = str(fallback_pool or "").strip()
    kind = str(fallback_kind or "").strip()
    source = str(final_emitted_source or "").strip()
    if not (pool or kind or source):
        return VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE
    if pool == "scene_opening_deterministic" or kind == "opening_deterministic_fallback":
        return VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY
    if pool == "strict_social_visibility_minimal" or kind == "visibility_minimal_social_fallback":
        return VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
    return VISIBILITY_FALLBACK_OWNER_SEALED_GATE


def sealed_fallback_owner_bucket_from_fields(
    *,
    final_emitted_source: str | None = None,
    strict_social_route: bool = False,
) -> str:
    """Map sealed terminal replace signals to one owner bucket.

    Read-side only: matches ``stamp_sealed_fallback_realization_family`` bucket stamping.
    """
    src = str(final_emitted_source or "").strip()
    if strict_social_route and src == "minimal_social_emergency_fallback":
        return SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
    return SEALED_FALLBACK_OWNER_SEALED_GATE
