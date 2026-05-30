"""Owner tests for opening fallback owner-bucket read mapping.

Opening fallback ownership is intentionally split:
- ``game.opening_deterministic_fallback`` owns curated-facts-to-text composition.
- ``game.upstream_response_repairs`` owns canonical upstream-prepared payload packaging.
- ``game.final_emission_gate`` owns selection, compatibility-local/fail-closed behavior, orchestration, and final route/output wiring.
- ``game.final_emission_meta`` owns owner-bucket mapping and projection metadata.

This file owns only the read-side owner-bucket mapping. Repeated projection fields
in replay/dashboard/classifier tests are intentional cross-layer contract locks,
not duplicate prose or gate orchestration ownership.
"""

from __future__ import annotations

import pytest

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_RETRY,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_STRICT_SOCIAL,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    OPENING_FALLBACK_OWNER_BUCKETS,
    opening_fallback_owner_bucket_from_fields,
)
from tests.helpers.final_emission_gate_fixtures import assert_fallback_owner_bucket
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
)

pytestmark = pytest.mark.unit


def test_owner_bucket_constants_are_the_allowed_values() -> None:
    assert OPENING_FALLBACK_OWNER_BUCKETS == frozenset(
        {
            "upstream-prepared",
            "sealed-gate",
            "retry",
            "strict-social",
            "unknown-ambiguous",
        }
    )


def test_canonical_upstream_prepared_authorship_source_maps_to_upstream_prepared() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        meta={
            "opening_recovered_via_fallback": True,
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            "final_emitted_source": "opening_deterministic_fallback",
            "response_type_repair_kind": "opening_deterministic_fallback",
        },
    )


def test_fail_closed_repair_kind_maps_to_sealed_gate() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_SEALED_GATE,
        meta={
            "response_type_repair_kind": "opening_deterministic_fallback_failed_closed",
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        },
    )


def test_legacy_compatibility_local_authorship_source_maps_to_unknown_ambiguous() -> None:
    """Legacy compatibility-local opening authorship is observed, not canonicalized."""
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        meta={
            "opening_recovered_via_fallback": True,
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            "final_emitted_source": "opening_deterministic_fallback",
        },
    )
    assert OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL != OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED


def test_missing_metadata_maps_to_unknown_ambiguous() -> None:
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS, meta=None)


def test_empty_metadata_maps_to_unknown_ambiguous() -> None:
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS, meta={})


def test_non_opening_fallback_family_maps_to_unknown_ambiguous() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        meta={
            "fallback_family_used": "observation",
            "fallback_temporal_frame": "continuation",
            "final_emitted_source": "global_scene_fallback",
        },
    )


def test_strict_social_signal_maps_to_strict_social_only_when_explicit() -> None:
    assert (
        opening_fallback_owner_bucket_from_fields(
            opening_recovered_via_fallback=True,
            fallback_family="scene_opening",
        )
        == OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
    )
    assert (
        opening_fallback_owner_bucket_from_fields(
            opening_recovered_via_fallback=True,
            response_type_repair_kind="strict_social_dialogue_repair",
        )
        == OPENING_FALLBACK_OWNER_STRICT_SOCIAL
    )


def test_retry_signal_maps_to_retry_only_when_explicit() -> None:
    assert (
        opening_fallback_owner_bucket_from_fields(
            opening_recovered_via_fallback=True,
            response_type_repair_kind="opening_deterministic_fallback",
        )
        == OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
    )
    assert (
        opening_fallback_owner_bucket_from_fields(
            opening_recovered_via_fallback=True,
            final_emitted_source="forced_retry_fallback",
        )
        == OPENING_FALLBACK_OWNER_RETRY
    )


def test_conflicting_upstream_prepared_and_fail_closed_signals_choose_sealed_gate() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_SEALED_GATE,
        meta={
            "opening_recovered_via_fallback": True,
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            "response_type_repair_kind": "opening_deterministic_fallback_failed_closed",
            "final_emitted_source": "opening_deterministic_fallback",
        },
    )
