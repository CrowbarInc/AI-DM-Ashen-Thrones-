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

CO14 assertion helpers (``assert_opening_fallback_authorship``, ``assert_opening_fallback_fail_closed``,
``assert_opening_fallback_family_temporal``, ``assert_opening_fallback_upstream_prepared``) absorb repeated
opening metadata locks from ``tests/test_final_emission_opening_fallback.py`` without hiding scenario boundaries.

CO15 visibility helpers (``assert_visibility_replacement_metadata``, ``assert_visibility_pass_metadata``,
``assert_visibility_checked_entities``, ``assert_visibility_checked_facts``) absorb repeated visibility
legality/projection locks from ``tests/test_final_emission_visibility.py`` without collapsing first-mention,
referential-clarity, or scenario-specific diagnostic boundaries.

CO16 referential-clarity helpers (``assert_referential_clarity_pass_metadata``,
``assert_referential_clarity_replacement_metadata``, ``assert_referential_clarity_default_metadata``,
``assert_referential_clarity_skipped_metadata``) absorb repeated referential legality/projection locks from
``tests/test_final_emission_visibility.py`` separately from visibility fallback and opening authorship helpers.

CO17 first-mention helpers (``assert_first_mention_pass_metadata``, ``assert_first_mention_replacement_metadata``,
``assert_first_mention_default_metadata``, ``assert_first_mention_skipped_metadata``) absorb repeated first-mention
legality/projection locks from ``tests/test_final_emission_visibility.py`` separately from visibility, referential,
and opening fallback helpers.

CO18 fallback-behavior validator helpers (``assert_fallback_validator_pass``, ``assert_fallback_validator_failure``)
absorb repeated ``validate_fallback_behavior`` predicate locks from ``tests/test_fallback_behavior_validator.py``
separately from gate integration, FEM ownership, and opening/visibility/referential/first-mention helpers.

Import opening helpers from this module directly (AS1 retired ``final_emission_gate_fixtures`` shim).
"""
from __future__ import annotations

from collections.abc import Mapping as AbcMapping, Sequence
from typing import Any, Mapping

from game.attribution_read_views import (
    OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    opening_fallback_owner_bucket_from_fields,
    opening_fallback_owner_bucket_from_meta,
)
from tests.helpers.response_type_smoke import response_type_contract

from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

# Cycle AP1 / CK Block 1–5: retired gate-local composer authorship — legacy/test inject only.
# Production ``game/`` never writes these tokens; canonical paths use
# ``OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED`` from upstream packaging.
# Import compat-local authorship only via ``legacy_compatibility_local_*`` helpers below.
# The shorter ``compatibility_local`` token was retired from read mapping (see
# ``OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP`` in ownership schema).
OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL = "compatibility_local_opening_deterministic"
assert OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL in OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES


def legacy_compatibility_local_opening_authorship_source() -> str:
    """Read-only accessor for the retired compat-local authorship token (sole raw-token boundary)."""
    return OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL

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


def assert_opening_fallback_authorship(
    meta: Mapping[str, Any] | None,
    expected: str | None,
    *,
    forbid_compat_local: bool = True,
) -> None:
    """Assert ``opening_fallback_authorship_source`` and optional compat-local prohibition."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("opening_fallback_authorship_source") == expected
    if forbid_compat_local:
        assert fem.get("opening_fallback_authorship_source") != legacy_compatibility_local_opening_authorship_source()


def assert_opening_fallback_family_temporal(
    meta: Mapping[str, Any] | None,
    *,
    family: str = OPENING_FALLBACK_FAMILY,
    temporal_frame: str = "first_impression",
) -> None:
    """Assert opening fallback family and temporal frame stamps on composition/FEM meta."""
    assert_final_emission_meta_contains(
        meta,
        fallback_family_used=family,
        fallback_temporal_frame=temporal_frame,
    )


def assert_opening_fallback_fail_closed(
    meta: Mapping[str, Any] | None,
    *,
    repair_kind: str = OPENING_FAILED_CLOSED_REPAIR_KIND,
    owner_bucket: str = OPENING_FALLBACK_OWNER_SEALED_GATE,
    include_family_temporal: bool = False,
    assert_owner_via_projection: bool = False,
    **extra: Any,
) -> None:
    """Assert sealed fail-closed opening metadata stamps."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("opening_fallback_failed_closed") is True
    assert_opening_fallback_authorship(fem, None)
    if include_family_temporal:
        assert_opening_fallback_family_temporal(fem)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    if assert_owner_via_projection:
        assert_fallback_owner_bucket(
            owner_bucket,
            from_fields=opening_owner_bucket_projection_fields(fem, repair_kind=repair_kind),
        )
    else:
        assert_fallback_owner_bucket(owner_bucket, meta=fem)


def assert_opening_fallback_upstream_prepared(
    meta: Mapping[str, Any] | None,
    *,
    final_emitted_source: str | None = OPENING_SUCCESS_SOURCE,
    owner_bucket: str = OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    forbid_compat_local: bool = True,
    **extra: Any,
) -> None:
    """Assert successful upstream-prepared opening authorship, owner bucket, and optional source."""
    if final_emitted_source is not None:
        assert_opening_fallback_source(
            meta,
            final_emitted_source=final_emitted_source,
            authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            owner_bucket=owner_bucket,
            forbid_compat_local_authorship=forbid_compat_local,
        )
    else:
        assert_opening_fallback_authorship(
            meta,
            OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            forbid_compat_local=forbid_compat_local,
        )
        assert_fallback_owner_bucket(owner_bucket, meta=meta)
    if extra:
        assert_final_emission_meta_contains(meta, **extra)


def assert_sealed_fallback_owner_bucket(meta: Mapping[str, Any] | None, expected: str) -> None:
    """Assert sealed fallback owner-bucket stamp on FEM/debug metadata."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("sealed_fallback_owner_bucket") == expected


def assert_visibility_replacement_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    checked_entities: Sequence[AbcMapping[str, Any]] | None = None,
    checked_facts: Sequence[AbcMapping[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Assert visibility legality failure with replacement applied (owner legality, not smoke-only)."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("visibility_validation_passed") is False
    assert fem.get("visibility_replacement_applied") is True
    if violation_kinds is not None:
        assert fem.get("visibility_violation_kinds") == list(violation_kinds)
    if checked_entities is not None:
        assert_visibility_checked_entities(fem, checked_entities)
    if checked_facts is not None:
        assert_visibility_checked_facts(fem, checked_facts)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_visibility_pass_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    checked_entities: Sequence[AbcMapping[str, Any]] | None = None,
    checked_facts: Sequence[AbcMapping[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Assert visibility legality pass without replacement."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("visibility_validation_passed") is True
    assert fem.get("visibility_replacement_applied") is False
    expected_kinds = [] if violation_kinds is None else list(violation_kinds)
    assert fem.get("visibility_violation_kinds") == expected_kinds
    if checked_entities is not None:
        assert_visibility_checked_entities(fem, checked_entities)
    if checked_facts is not None:
        assert_visibility_checked_facts(fem, checked_facts)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_visibility_checked_entities(
    meta: Mapping[str, Any] | None,
    expected: Sequence[AbcMapping[str, Any]],
) -> None:
    """Assert visibility entity match list on FEM/debug metadata."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("visibility_checked_entities") == [dict(item) for item in expected]


def assert_visibility_checked_facts(
    meta: Mapping[str, Any] | None,
    expected: Sequence[AbcMapping[str, Any]],
) -> None:
    """Assert visibility fact match list on FEM/debug metadata."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("visibility_checked_facts") == [dict(item) for item in expected]


def assert_visibility_projection_smoke(meta: Mapping[str, Any] | None) -> None:
    """Projection smoke: core visibility metadata keys are present for wiring diagnosis."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    for key in (
        "visibility_validation_passed",
        "visibility_replacement_applied",
        "visibility_violation_kinds",
    ):
        assert key in fem, f"expected visibility projection key {key!r} on final emission meta"


_REFERENTIAL_CLARITY_DEFAULT_META_KEYS: tuple[str, ...] = (
    "referential_clarity_validation_passed",
    "referential_clarity_replacement_applied",
    "referential_clarity_violation_kinds",
    "referential_clarity_checked_entities",
    "referential_clarity_violation_sample",
    "referential_clarity_local_substitution_attempted",
    "referential_clarity_local_substitution_applied",
    "referential_clarity_local_substitution_token",
    "referential_clarity_local_substitution_replacement",
    "referential_clarity_fallback_avoided",
    "referential_clarity_fallback_after_failed_local_repair",
)


def assert_referential_clarity_default_metadata(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """Projection smoke: pins emitted referential-clarity metadata shape, not the legality matrix."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    for key in _REFERENTIAL_CLARITY_DEFAULT_META_KEYS:
        assert key in fem, f"expected referential clarity projection key {key!r} on final emission meta"
    return fem


def assert_referential_clarity_pass_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    include_default_shape: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Assert referential-clarity legality pass without replacement."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    if include_default_shape:
        assert_referential_clarity_default_metadata(fem)
    assert fem.get("referential_clarity_validation_passed") is True
    assert fem.get("referential_clarity_replacement_applied") is False
    if violation_kinds is not None:
        assert fem.get("referential_clarity_violation_kinds") == list(violation_kinds)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_referential_clarity_replacement_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    violation_kind: str | None = None,
    violation_kinds_any: Sequence[str] | None = None,
    include_default_shape: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Assert referential-clarity legality failure with replacement applied."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    if include_default_shape:
        assert_referential_clarity_default_metadata(fem)
    assert fem.get("referential_clarity_validation_passed") is False
    assert fem.get("referential_clarity_replacement_applied") is True
    kinds = fem.get("referential_clarity_violation_kinds")
    if violation_kinds is not None:
        assert kinds == list(violation_kinds)
    if violation_kind is not None:
        assert violation_kind in kinds
    if violation_kinds_any is not None:
        assert any(kind in kinds for kind in violation_kinds_any)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_referential_clarity_skipped_metadata(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """Assert referential clarity was skipped (e.g. visibility failure ran first)."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("referential_clarity_validation_passed") is None
    assert fem.get("referential_clarity_replacement_applied") is False
    assert fem.get("referential_clarity_violation_kinds") == []
    assert fem.get("referential_clarity_checked_entities") == []
    assert fem.get("referential_clarity_violation_sample") == []
    return fem


_FIRST_MENTION_DEFAULT_META_KEYS: tuple[str, ...] = (
    "first_mention_validation_passed",
    "first_mention_replacement_applied",
    "first_mention_violation_kinds",
    "first_mention_checked_entities",
    "first_mention_leading_pronoun_detected",
    "first_mention_first_explicit_entity_offset",
    "first_mention_fallback_strategy",
    "first_mention_fallback_candidate_source",
    "opening_scene_first_mention_preference_used",
)


def assert_first_mention_default_metadata(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """Projection smoke: keep first-mention metadata presence diagnosable without owning legality matrix."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    for key in _FIRST_MENTION_DEFAULT_META_KEYS:
        assert key in fem, f"expected first-mention projection key {key!r} on final emission meta"
    return fem


def assert_first_mention_pass_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    include_default_shape: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Assert first-mention legality pass without replacement."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    if include_default_shape:
        assert_first_mention_default_metadata(fem)
    assert fem.get("first_mention_validation_passed") is True
    assert fem.get("first_mention_replacement_applied") is False
    if violation_kinds is not None:
        assert fem.get("first_mention_violation_kinds") == list(violation_kinds)
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_first_mention_replacement_metadata(
    meta: Mapping[str, Any] | None,
    *,
    violation_kinds: Sequence[str] | None = None,
    violation_kind: str | None = None,
    include_default_shape: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Assert first-mention legality failure with replacement applied."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    if include_default_shape:
        assert_first_mention_default_metadata(fem)
    assert fem.get("first_mention_validation_passed") is False
    assert fem.get("first_mention_replacement_applied") is True
    kinds = fem.get("first_mention_violation_kinds")
    if violation_kinds is not None:
        assert kinds == list(violation_kinds)
    if violation_kind is not None:
        assert violation_kind in kinds
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_first_mention_skipped_metadata(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """Assert first-mention validation was skipped (e.g. visibility failure ran first)."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("first_mention_validation_passed") is None
    assert fem.get("first_mention_replacement_applied") is False
    assert fem.get("first_mention_violation_kinds") == []
    assert fem.get("first_mention_checked_entities") == []
    assert fem.get("first_mention_leading_pronoun_detected") is False
    assert fem.get("first_mention_first_explicit_entity_offset") is None
    assert fem.get("first_mention_fallback_strategy") is None
    assert fem.get("first_mention_fallback_candidate_source") is None
    assert fem.get("opening_scene_first_mention_preference_used") is False
    return fem


def assert_fallback_validator_pass(
    out: Mapping[str, Any] | None,
    *,
    checked: bool | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Assert ``validate_fallback_behavior`` pass/skip-clean result (validator owner, not gate integration)."""
    result = dict(out) if isinstance(out, Mapping) else {}
    assert result.get("passed") is True
    if checked is not None:
        assert result.get("checked") is checked, (
            f"checked: expected {checked!r}, got {result.get('checked')!r}"
        )
    if extra:
        assert_final_emission_meta_contains(result, **extra)
    return result


def assert_fallback_validator_failure(
    out: Mapping[str, Any] | None,
    *,
    failure_reason: str | None = None,
    failure_reasons: Sequence[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Assert ``validate_fallback_behavior`` failure with optional reason membership or exact reasons list."""
    result = dict(out) if isinstance(out, Mapping) else {}
    assert result.get("passed") is False
    reasons = list(result.get("failure_reasons") or [])
    if failure_reason is not None:
        assert failure_reason in reasons, (
            f"failure_reasons: expected {failure_reason!r} in {reasons!r}"
        )
    if failure_reasons is not None:
        assert reasons == list(failure_reasons), (
            f"failure_reasons: expected {list(failure_reasons)!r}, got {reasons!r}"
        )
    if extra:
        assert_final_emission_meta_contains(result, **extra)
    return result


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


def legacy_compatibility_local_opening_authorship_meta(**overrides: Any) -> dict[str, Any]:
    """Return meta slice with retired compatibility-local authorship (legacy/test/replay inject only)."""
    meta: dict[str, Any] = {
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    }
    meta.update(overrides)
    return meta


def build_legacy_compatibility_local_opening_fallback_evidence(**overrides: Any) -> dict[str, Any]:
    """Return replay/classifier-shaped successful opening evidence with legacy compat-local authorship."""
    return successful_opening_observed_fields(
        opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
        **overrides,
    )


def opening_owner_bucket_projection_fields(
    meta: Mapping[str, Any],
    *,
    repair_kind: str,
) -> dict[str, Any]:
    """Return field bundle for ``opening_fallback_owner_bucket_from_fields`` projection locks."""
    return {
        "final_emitted_source": OPENING_SUCCESS_SOURCE,
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": meta.get("opening_fallback_authorship_source"),
        "response_type_repair_kind": repair_kind,
        "fallback_family": meta.get("fallback_family_used"),
        "fallback_temporal_frame": meta.get("fallback_temporal_frame"),
    }
