"""Thin checks for ``tools/validation_coverage_audit.py`` (deterministic, no game imports)."""

from __future__ import annotations

from dataclasses import replace
from io import StringIO

from tests.validation_coverage_registry import (
    CoverageEntry,
    CoverageStatus,
    RequiredSurface,
)
from tools.validation_coverage_audit import run


def _active_unit(feature_id: str = "audit_unit_a") -> CoverageEntry:
    path = "tests/test_validation_layer_contracts.py"
    return CoverageEntry(
        feature_id=feature_id,
        title="Audit probe A",
        owner_domain="test_infra",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.UNIT_CONTRACT}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=(path,),
        integration_smoke_modules=(),
        notes="",
        optional_smoke_overlap=(),
    )


def _active_unit_plus_transcript(feature_id: str = "audit_unit_b") -> CoverageEntry:
    path = "tests/test_validation_layer_contracts.py"
    return CoverageEntry(
        feature_id=feature_id,
        title="Audit probe B",
        owner_domain="test_infra",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.UNIT_CONTRACT, RequiredSurface.TRANSCRIPT}),
        transcript_modules=(path,),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=(path,),
        integration_smoke_modules=(),
        notes="",
        optional_smoke_overlap=(),
    )


def test_strict_ok_registry_exits_zero() -> None:
    out, err = StringIO(), StringIO()
    code = run(["--strict"], registry_override=(_active_unit(),), stdout=out, stderr=err)
    assert code == 0
    assert "Registry validation: OK" in out.getvalue()


def test_strict_invalid_entries_exits_nonzero() -> None:
    row = _active_unit()
    dup = replace(row, title="Different title same id")
    out, err = StringIO(), StringIO()
    code = run(["--strict"], registry_override=(row, dup), stdout=out, stderr=err)
    assert code == 2
    assert "duplicate feature_id" in out.getvalue()


def test_feature_filter_prints_feature_block() -> None:
    row = _active_unit(feature_id="audit_feature_x")
    out, err = StringIO(), StringIO()
    code = run(["--feature", "audit_feature_x"], registry_override=(row,), stdout=out, stderr=err)
    assert code == 0
    blob = out.getvalue()
    assert "feature_id: audit_feature_x" in blob
    assert "Audit probe A" in blob
    assert "Likely commands" in blob
    assert "pytest tests/test_validation_layer_contracts.py" in blob


def test_surface_filter_lists_declaring_rows() -> None:
    a = _active_unit(feature_id="surface_a")
    b = _active_unit_plus_transcript(feature_id="surface_b")
    out, err = StringIO(), StringIO()
    code = run(["--surface", "transcript"], registry_override=(a, b), stdout=out, stderr=err)
    assert code == 0
    blob = out.getvalue()
    assert "surface_b" in blob
    assert "surface_a" not in blob


def test_missing_surface_filter_lists_only_gaps() -> None:
    a = _active_unit(feature_id="no_transcript_decl")
    b = _active_unit_plus_transcript(feature_id="has_transcript_decl")
    out, err = StringIO(), StringIO()
    code = run(["--missing", "transcript"], registry_override=(a, b), stdout=out, stderr=err)
    assert code == 0
    lines = [ln.strip() for ln in out.getvalue().splitlines() if ln.strip() and not ln.startswith("=")]
    assert "no_transcript_decl" in lines
    assert "has_transcript_decl" not in lines
