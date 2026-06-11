"""Canonical test-only opening fallback evidence fixtures.

These builders centralize repeated FEM-shaped and replay-observed setup only.
They intentionally emit **minimal** route/owner slices (``final_emitted_source``,
authorship, repair kind, family) — not the full
:data:`game.final_emission_meta.OPENING_FALLBACK_RESULT_META_FIELDS` shape produced at
write time by ``build_opening_fallback_result_meta``. Tests that need every result-meta
key should assert against payload/FEM fixtures or import
``OPENING_FALLBACK_RESULT_META_FIELDS`` from ``game.final_emission_meta``.

Helper boundary (Cycle AS1):
- Downstream HTTP smoke / response-type scaffolds: ``emission_smoke_assertions.py``
- Strict-social harness: ``strict_social_harness.py``
- Opening attach-then gate harness (private seams): ``opening_fallback_gate_harness.py``
- Classifier/dashboard inline observed rows may wrap these builders; duplication there
  is intentional diagnostic projection, not runtime gate ownership.

Import opening helpers from this module directly (AS1 retired ``final_emission_gate_fixtures`` shim).
"""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_meta import (
    OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    OPENING_FALLBACK_RESULT_META_FIELDS,
    opening_fallback_owner_bucket_from_fields,
    opening_fallback_owner_bucket_from_meta,
)
from tests.helpers.emission_smoke_assertions import response_type_contract

# Re-export for tests that lock composition_meta against opening_fallback_meta (AJ2/AJ4).
OPENING_FALLBACK_RESULT_META_FIELD_NAMES = OPENING_FALLBACK_RESULT_META_FIELDS
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

# Cycle AP1: retired gate-local composer authorship — test inject vocabulary only.
# Production ``game/`` never writes these tokens; canonical paths use
# ``OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED`` from upstream packaging.
OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL = "compatibility_local_opening_deterministic"
assert OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL in OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES

OPENING_FALLBACK_FAMILY = "scene_opening"
OPENING_SUCCESS_SOURCE = "opening_deterministic_fallback"
OPENING_FAILED_CLOSED_SOURCE = "opening_fallback_failed_closed"
OPENING_SUCCESS_REPAIR_KIND = "opening_deterministic_fallback"
OPENING_FAILED_CLOSED_REPAIR_KIND = "opening_deterministic_fallback_failed_closed"

EXPECTED_FRONTIER_GATE_OPENING_FALLBACK = (
    "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. "
    "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. "
    "A notice board lists new taxes, curfews, and a posted warning about a missing patrol. "
    "You can start with Read the notice board or Approach the guards."
)


def opening_validation_context() -> dict:
    facts = [
        "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
        "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.",
        "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
    ]
    return {
        "location_anchors": ["Cinderwatch Gate District"],
        "visible_facts": facts,
        "actionable_labels": ["Read the notice board", "Approach the guards"],
    }


def opening_gm_output() -> dict:
    facts = opening_validation_context()["visible_facts"]
    return {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": list(facts),
        "metadata": {
            "emission_debug": {
                "opening_curated_facts_present": True,
                "opening_curated_facts_count": len(facts),
                "opening_curated_facts_source": "realization",
            }
        },
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "opening_curated_facts": list(facts),
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Cinderwatch Gate District"]},
                "scene_anchors": {"location_anchors": ["Cinderwatch Gate District"]},
                "active_pressures": {},
            },
            "opening_scene_realization": {"contract": {"narration_basis_visible_facts": facts}},
            "narration_visibility": {"visible_facts": facts},
            "scene": {
                "public": {
                    "id": "frontier_gate",
                    "location": "Cinderwatch Gate District",
                    "visible_facts": facts,
                    "actions": [{"label": "Read the notice board"}, {"label": "Approach the guards"}],
                }
            },
        },
    }


def assert_final_emission_meta_contains(
    meta: Mapping[str, Any] | None,
    **expected: Any,
) -> dict[str, Any]:
    """Assert exact key matches on FEM/debug metadata already extracted from gate output."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    for key, value in expected.items():
        assert fem.get(key) == value, f"{key}: expected {value!r}, got {fem.get(key)!r}"
    return fem


def assert_fallback_owner_bucket(
    expected: str,
    *,
    meta: Mapping[str, Any] | None = None,
    from_fields: Mapping[str, Any] | None = None,
) -> None:
    """Assert opening fallback owner bucket via meta read or explicit field projection."""
    if from_fields is not None:
        got = opening_fallback_owner_bucket_from_fields(**dict(from_fields))
    else:
        got = opening_fallback_owner_bucket_from_meta(meta)
    assert got == expected


def assert_opening_fallback_source(
    meta: Mapping[str, Any] | None,
    *,
    final_emitted_source: str,
    authorship_source: str | None = None,
    owner_bucket: str | None = None,
    forbid_compat_local_authorship: bool = False,
) -> None:
    """Assert canonical opening fallback source/authorship/owner-bucket projection locks."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("final_emitted_source") == final_emitted_source
    if authorship_source is not None:
        assert fem.get("opening_fallback_authorship_source") == authorship_source
    if forbid_compat_local_authorship:
        assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    if owner_bucket is not None:
        assert_fallback_owner_bucket(owner_bucket, meta=fem)


def assert_sealed_fallback_owner_bucket(meta: Mapping[str, Any] | None, expected: str) -> None:
    """Assert sealed fallback owner-bucket stamp on FEM/debug metadata."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("sealed_fallback_owner_bucket") == expected


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


def opening_dual_family_fem_meta(*, realization_family: str, **overrides: Any) -> dict[str, Any]:
    """Return FEM slice with both diegetic ``fallback_family_used`` and provenance family."""
    from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD

    evidence = successful_opening_fem_meta()
    evidence[REALIZATION_FALLBACK_FAMILY_FIELD] = realization_family
    evidence.update(overrides)
    return evidence


def opening_upstream_composition_meta_slice(**overrides: Any) -> dict[str, Any]:
    """Return upstream-prepared opening composition-meta slice used by adapter/payload tests."""
    evidence: dict[str, Any] = {
        "fallback_family_used": OPENING_FALLBACK_FAMILY,
        "fallback_temporal_frame": "first_impression",
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    }
    evidence.update(overrides)
    return evidence
