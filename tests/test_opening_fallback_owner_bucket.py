"""Owner tests for opening fallback owner-bucket read mapping.

Opening fallback ownership is intentionally split:
- ``game.opening_deterministic_fallback`` owns curated-facts-to-text composition.
- ``game.upstream_response_repairs`` owns canonical upstream-prepared payload packaging.
- ``game.final_emission_gate`` owns selection, fail-closed behavior, orchestration, and final route/output wiring.
- ``game.final_emission_meta`` owns owner-bucket mapping and projection metadata.

This file owns only the read-side owner-bucket mapping via
``opening_fallback_owner_bucket_from_meta``. Full opening telemetry keys are
registered in ``OPENING_FALLBACK_PROJECTION_FIELDS``; minimal FEM/replay slices
use ``tests.helpers.opening_fallback_evidence`` — intentional cross-layer locks,
not duplicate write-time metadata composition.
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
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
    final_emission_meta_read_side_surface,
    opening_fallback_owner_bucket_from_fields,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FAILED_CLOSED_REPAIR_KIND,
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    assert_fallback_owner_bucket,
    fail_closed_opening_observed_fields,
    successful_opening_observed_fields,
)
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

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


def test_opening_fallback_owner_bucket_registry_matches_read_side_surface() -> None:
    registries = final_emission_meta_read_side_surface()["fallback_owner_bucket_registries"]
    opening_registry = registries["opening"]
    assert opening_registry["OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert opening_registry["OPENING_FALLBACK_OWNER_SEALED_GATE"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    assert set(opening_registry.values()) == set(OPENING_FALLBACK_OWNER_BUCKETS)


def test_canonical_upstream_prepared_authorship_source_maps_to_upstream_prepared() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        meta=successful_opening_observed_fields(),
    )


def test_fail_closed_repair_kind_maps_to_sealed_gate() -> None:
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_SEALED_GATE,
        meta=fail_closed_opening_observed_fields(
            opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        ),
    )


def test_injected_legacy_compatibility_local_authorship_maps_to_unknown_ambiguous() -> None:
    """Injected legacy token maps to unknown-ambiguous; production never emits it."""
    assert OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL != OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert_fallback_owner_bucket(
        OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        meta=successful_opening_observed_fields(
            opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
        ),
    )


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
        meta=successful_opening_observed_fields(
            response_type_repair_kind=OPENING_FAILED_CLOSED_REPAIR_KIND,
        ),
    )


def test_visibility_fallback_owner_bucket_from_fields_cases() -> None:
    """Visibility bucket mapping is owned by ``final_emission_meta`` (Cycle BK1/BK2)."""
    from game.final_emission_meta import visibility_fallback_owner_bucket_from_fields

    cases = (
        ({"fallback_pool": "scene_opening_deterministic", "fallback_kind": "", "final_emitted_source": ""}, VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY),
        ({"fallback_pool": "", "fallback_kind": "opening_deterministic_fallback", "final_emitted_source": ""}, VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY),
        (
            {"fallback_pool": "strict_social_visibility_minimal", "fallback_kind": "", "final_emitted_source": ""},
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        ),
        ({"fallback_pool": "", "fallback_kind": "visibility_minimal_social_fallback", "final_emitted_source": ""}, VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY),
        ({"fallback_pool": "global", "fallback_kind": "global_scene_fallback", "final_emitted_source": "x"}, VISIBILITY_FALLBACK_OWNER_SEALED_GATE),
        ({"fallback_pool": "", "fallback_kind": "", "final_emitted_source": ""}, VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE),
    )
    for kwargs, expected in cases:
        assert visibility_fallback_owner_bucket_from_fields(**kwargs) == expected


def test_sealed_fallback_owner_bucket_from_fields_cases() -> None:
    """Sealed bucket mapping is owned by ``final_emission_meta`` (Cycle BK1/BK2)."""
    from game.final_emission_meta import (
        SEALED_FALLBACK_OWNER_SEALED_GATE,
        SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
        sealed_fallback_owner_bucket_from_fields,
    )

    assert (
        sealed_fallback_owner_bucket_from_fields(
            final_emitted_source="acceptance_quality_global_scene_fallback",
            strict_social_route=False,
        )
        == SEALED_FALLBACK_OWNER_SEALED_GATE
    )
    assert (
        sealed_fallback_owner_bucket_from_fields(
            final_emitted_source="minimal_social_emergency_fallback",
            strict_social_route=True,
        )
        == SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
    )


def test_fallback_owner_bucket_registries_cover_all_three_families() -> None:
    registries = final_emission_meta_read_side_surface()["fallback_owner_bucket_registries"]
    assert set(registries) == {"opening", "sealed", "visibility"}
