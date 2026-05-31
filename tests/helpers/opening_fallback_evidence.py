"""Canonical test-only opening fallback evidence fixtures.

These builders centralize repeated FEM-shaped and replay-observed setup only.
Consumer tests remain responsible for asserting their own projection,
classification, reporting, or lineage contracts.
"""
from __future__ import annotations

from typing import Any

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

# Legacy compatibility-local authorship token — test/read-side only; never emitted on canonical paths.
OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL = "compatibility_local_opening_deterministic"

OPENING_FALLBACK_FAMILY = "scene_opening"
OPENING_SUCCESS_SOURCE = "opening_deterministic_fallback"
OPENING_FAILED_CLOSED_SOURCE = "opening_fallback_failed_closed"
OPENING_SUCCESS_REPAIR_KIND = "opening_deterministic_fallback"
OPENING_FAILED_CLOSED_REPAIR_KIND = "opening_deterministic_fallback_failed_closed"


def successful_opening_fem_meta(**overrides: Any) -> dict[str, Any]:
    """Return canonical FEM-shaped evidence for successful opening recovery."""
    evidence: dict[str, Any] = {
        "final_emitted_source": OPENING_SUCCESS_SOURCE,
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        "fallback_family_used": OPENING_FALLBACK_FAMILY,
    }
    evidence.update(overrides)
    return evidence


def fail_closed_opening_fem_meta(**overrides: Any) -> dict[str, Any]:
    """Return canonical FEM-shaped evidence for sealed opening failure."""
    evidence: dict[str, Any] = {
        "final_emitted_source": OPENING_FAILED_CLOSED_SOURCE,
        "response_type_repair_kind": OPENING_FAILED_CLOSED_REPAIR_KIND,
    }
    evidence.update(overrides)
    return evidence


def successful_opening_observed_fields(*, include_owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return replay/classifier-shaped successful opening evidence fields."""
    evidence: dict[str, Any] = {
        "final_emitted_source": OPENING_SUCCESS_SOURCE,
        "response_type_repair_kind": OPENING_SUCCESS_REPAIR_KIND,
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        "fallback_family": OPENING_FALLBACK_FAMILY,
        "fallback_temporal_frame": "first_impression",
    }
    if include_owner_bucket:
        evidence["opening_fallback_owner_bucket"] = OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    evidence.update(overrides)
    return evidence


def fail_closed_opening_observed_fields(*, include_owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return replay/classifier-shaped sealed opening failure evidence fields."""
    evidence: dict[str, Any] = {
        "final_emitted_source": OPENING_FAILED_CLOSED_SOURCE,
        "response_type_repair_kind": OPENING_FAILED_CLOSED_REPAIR_KIND,
        "opening_recovered_via_fallback": True,
        "fallback_family": OPENING_FALLBACK_FAMILY,
    }
    if include_owner_bucket:
        evidence["opening_fallback_owner_bucket"] = OPENING_FALLBACK_OWNER_SEALED_GATE
    evidence.update(overrides)
    return evidence
