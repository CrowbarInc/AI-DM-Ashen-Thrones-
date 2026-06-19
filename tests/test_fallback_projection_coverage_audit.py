"""Audit-only tests for BP2 fallback projection coverage."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fallback_projection_coverage_audit.py"
SPEC = importlib.util.spec_from_file_location("fallback_projection_coverage_audit_tool", TOOL)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules["fallback_projection_coverage_audit_tool"] = AUDIT
SPEC.loader.exec_module(AUDIT)


def test_projected_catalog_shapes_each_emit_one_fallback_selected_event() -> None:
    observed = {}
    for shape in AUDIT.PROJECTED_EVIDENCE_SHAPES:
        events = AUDIT._fallback_events(shape.fem)
        assert len(events) == 1, shape.shape_id
        observed[shape.shape_id] = events[0]["fallback_kind"]

    assert len(observed) == 15
    assert set(observed.values()) == {
        "sanitizer_strict_social",
        "sanitizer_empty_output",
        "opening_failed_closed",
        "scene_opening",
        "response_type_prepared_emission",
        "minimal_social_emergency_fallback",
        "strict_social_fallback",
        "visibility_or_scene_replacement",
        "upstream_fast_fallback",
        "sealed_social_interlocutor_fallback",
        "sealed_passive_scene_pressure_fallback",
        "sealed_npc_pursuit_neutral_fallback",
        "sealed_anti_reset_continuation_fallback",
        "sealed_global_scene_fallback",
        "sealed_unknown_replacement",
    }


def test_unprojected_catalog_shapes_emit_no_fallback_selected_event() -> None:
    assert {shape.shape_id for shape in AUDIT.UNPROJECTED_EVIDENCE_SHAPES} == {
        "forced_retry_terminal_route",
        "social_minimal_retry_route",
        "nonsocial_minimal_retry_route",
        "provider_failure_family_without_trace",
    }
    assert all(not AUDIT._fallback_events(shape.fem) for shape in AUDIT.UNPROJECTED_EVIDENCE_SHAPES)


def test_intentional_omissions_are_excluded_from_candidate_denominator() -> None:
    report = AUDIT.build_projection_coverage_report()

    assert len(report["intentional_omissions_excluded_from_denominator"]) == 8
    assert all(not AUDIT._fallback_events(shape.fem) for shape in AUDIT.INTENTIONAL_OMISSION_SHAPES)
    assert report["projection_candidate_count"] == len(AUDIT.PROJECTION_CANDIDATES)


def test_coverage_metrics_and_dimensions_are_deterministic() -> None:
    report = AUDIT.build_projection_coverage_report()

    assert report["projection_candidate_count"] == 19
    assert report["projected_fallback_count"] == 15
    assert report["unprojected_fallback_count"] == 4
    assert report["projection_coverage_rate"] == pytest.approx(15 / 19)
    assert report["coverage_by"]["fallback_kind"]["<unprojected>"] == {
        "projection_candidate_count": 4,
        "projected_fallback_count": 0,
        "unprojected_fallback_count": 4,
        "projection_coverage_rate": 0.0,
    }
    retry = report["coverage_by"]["realization_family"]["retry_terminal_fallback"]
    assert retry["projection_candidate_count"] == 4
    assert retry["projected_fallback_count"] == 1
    assert retry["unprojected_fallback_count"] == 3


def test_audit_does_not_mutate_catalog_fem() -> None:
    before = json.dumps([dict(shape.fem) for shape in AUDIT.PROJECTION_CANDIDATES], sort_keys=True)
    AUDIT.build_projection_coverage_report()
    after = json.dumps([dict(shape.fem) for shape in AUDIT.PROJECTION_CANDIDATES], sort_keys=True)
    assert after == before


def test_writer_is_sorted_deterministic_json(tmp_path: Path) -> None:
    report = AUDIT.build_projection_coverage_report()
    first = AUDIT.write_projection_coverage_report(report, tmp_path / "first.json")
    second = AUDIT.write_projection_coverage_report(report, tmp_path / "second.json")

    assert first.read_bytes() == second.read_bytes()
    assert first.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(first.read_text(encoding="utf-8")) == report


def test_cli_writes_report_without_runtime_execution(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "projection_coverage_report.json"
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["projection_candidate_count"] == 19
    assert payload["unprojected_fallback_count"] == 4
    assert "Projection coverage: 15/19 (78.95%)" in completed.stdout
