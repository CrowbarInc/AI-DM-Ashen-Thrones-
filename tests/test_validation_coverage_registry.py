"""Objective #12 — registry schema integrity (governance artifact; no runtime hooks)."""

from __future__ import annotations

from dataclasses import replace

from tests.validation_coverage_registry import (
    REGISTRY,
    CoverageEntry,
    CoverageStatus,
    RequiredSurface,
    validate_entries,
    validate_registry,
)


def _base_active_unit_contract() -> CoverageEntry:
    return CoverageEntry(
        feature_id="registry_schema_probe",
        title="Schema probe",
        owner_domain="test_infra",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.UNIT_CONTRACT}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=("tests/test_validation_layer_contracts.py",),
        integration_smoke_modules=(),
        notes="",
        optional_smoke_overlap=(),
    )


def test_validation_coverage_registry_is_valid() -> None:
    errors = validate_registry()
    assert not errors, "registry validation errors:\n" + "\n".join(errors)


def test_seed_registry_covers_objective12_demo_surfaces() -> None:
    """Block D — committed seed must exercise each primary surface at least once (typed pointers)."""
    by_id = {e.feature_id: e for e in REGISTRY}
    for fid in (
        "validation_layer_contracts",
        "behavioral_gauntlet_validation",
        "playability_validation",
        "manual_gauntlet_lead_narration_smoke",
        "anti_railroading_transcript_regressions",
        "n1_longitudinal_scenario_spine_validation",
    ):
        assert fid in by_id, f"missing seeded feature_id {fid!r}"

    assert RequiredSurface.UNIT_CONTRACT in by_id["validation_layer_contracts"].required_surfaces
    assert RequiredSurface.BEHAVIORAL_GAUNTLET in by_id["behavioral_gauntlet_validation"].required_surfaces
    assert len(by_id["behavioral_gauntlet_validation"].behavioral_gauntlet_axes) == 4
    assert RequiredSurface.PLAYABILITY in by_id["playability_validation"].required_surfaces
    assert len(by_id["playability_validation"].playability_scenarios) == 4
    assert RequiredSurface.MANUAL_GAUNTLET in by_id["manual_gauntlet_lead_narration_smoke"].required_surfaces
    assert by_id["manual_gauntlet_lead_narration_smoke"].manual_gauntlets == ("g1",)
    assert RequiredSurface.TRANSCRIPT in by_id["anti_railroading_transcript_regressions"].required_surfaces
    assert by_id["anti_railroading_transcript_regressions"].transcript_modules == (
        "tests/test_anti_railroading_transcript_regressions.py",
    )
    assert RequiredSurface.INTEGRATION_SMOKE in by_id[
        "n1_longitudinal_scenario_spine_validation"
    ].required_surfaces
    assert "tools/run_n1_scenario_spine_validation.py" in by_id[
        "n1_longitudinal_scenario_spine_validation"
    ].integration_smoke_modules


def test_unit_contract_requires_typed_modules_not_notes() -> None:
    """Prose in ``notes`` must not satisfy ``unit_contract`` (Block B1)."""
    bad = replace(
        _base_active_unit_contract(),
        unit_contract_modules=(),
        notes="pytest lives at tests/test_validation_layer_contracts.py for bookkeeping only.",
    )
    errs = validate_entries((bad,))
    assert any("unit_contract_modules" in e and "unit_contract" in e for e in errs)


def test_integration_smoke_requires_integration_modules() -> None:
    entry = replace(
        _base_active_unit_contract(),
        feature_id="registry_integration_probe",
        required_surfaces=frozenset(
            {
                RequiredSurface.UNIT_CONTRACT,
                RequiredSurface.INTEGRATION_SMOKE,
            },
        ),
        integration_smoke_modules=(),
    )
    errs = validate_entries((entry,))
    assert any("integration_smoke_modules" in e for e in errs)


def test_active_rejects_unknown_manual_gauntlet_id() -> None:
    entry = replace(
        _base_active_unit_contract(),
        feature_id="registry_manual_probe",
        required_surfaces=frozenset(
            {RequiredSurface.UNIT_CONTRACT, RequiredSurface.MANUAL_GAUNTLET},
        ),
        manual_gauntlets=("g99",),
    )
    errs = validate_entries((entry,))
    assert any("manual_gauntlet" in e and "g99" in e for e in errs)


def test_active_rejects_unknown_playability_scenario_id() -> None:
    entry = replace(
        _base_active_unit_contract(),
        feature_id="registry_playability_probe",
        required_surfaces=frozenset({RequiredSurface.UNIT_CONTRACT, RequiredSurface.PLAYABILITY}),
        playability_scenarios=("test_playability_smoke_not_a_real_test",),
    )
    errs = validate_entries((entry,))
    assert any("playability_scenario" in e for e in errs)


def test_duplicate_pointers_rejected() -> None:
    path = "tests/test_validation_layer_contracts.py"
    entry = replace(
        _base_active_unit_contract(),
        feature_id="registry_dup_probe",
        unit_contract_modules=(path, path),
    )
    errs = validate_entries((entry,))
    assert any("duplicate pointer" in e for e in errs)


def test_validate_entries_accepts_custom_sequence() -> None:
    assert not validate_entries((_base_active_unit_contract(),))


def test_duplicate_feature_id_rejected() -> None:
    row = _base_active_unit_contract()
    dup = replace(row, title="Other title")
    errs = validate_entries((row, dup))
    assert any("duplicate feature_id" in e for e in errs)
