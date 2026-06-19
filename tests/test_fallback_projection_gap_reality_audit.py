"""Audit-only tests for BP3 projection-gap artifact scanning."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fallback_projection_gap_reality_audit.py"
SPEC = importlib.util.spec_from_file_location("fallback_projection_gap_reality_audit_tool", TOOL)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules["fallback_projection_gap_reality_audit_tool"] = AUDIT
SPEC.loader.exec_module(AUDIT)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_finalized_fem_gap_is_confirmed_and_impacts_projection(tmp_path: Path) -> None:
    artifact = tmp_path / "data" / "transcript.json"
    _write_json(
        artifact,
        {
            "turns": [
                {
                    "turn_id": "turn-1",
                    "resolution": {"kind": "observe"},
                    "meta": {
                        "final_emission_meta": {
                            "final_route": "forced_retry_fallback",
                            "fallback_kind": "retry_escape_hatch",
                            "realization_fallback_family": "retry_terminal_fallback",
                        },
                        "runtime_lineage_events": [],
                    },
                }
            ]
        },
    )

    report = AUDIT.scan_projection_gap_reality(roots=(tmp_path / "data",), repository_root=tmp_path)
    metrics = report["frequency"]["forced_retry_fallback"]
    assert metrics == {
        "shape_occurrence_count": 1,
        "shape_turn_count": 1,
        "shape_artifact_count": 1,
        "finalized_fem_occurrence_count": 1,
        "packaging_only_occurrence_count": 0,
    }
    assert report["reachability"]["forced_retry_fallback"]["classification"] == "A. Confirmed active"
    assert report["projection_impact"]["additional_fallback_count_if_projected"] == 1
    assert report["projection_impact"]["estimated_adjusted_coverage"] == pytest.approx(16 / 19)


def test_outer_and_stage_retry_routes_are_packaging_only(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "session.json"
    _write_json(
        artifact,
        {
            "timestamp": "2026-06-01T00:00:00Z",
            "gm_output": {
                "final_route": "forced_retry_fallback",
                "metadata": {
                    "stage_diff_telemetry": {
                        "snapshots": [
                            {"stage": "retry_terminal_fallback_result", "final_route": "forced_retry_fallback"},
                            {"stage": "final_emission_gate_exit", "final_route": "replaced"},
                        ]
                    }
                },
                "internal_state": {
                    "emission_debug_lane": {
                        "_final_emission_meta": {
                            "final_route": "replaced",
                            "final_emitted_source": "global_scene_fallback",
                        }
                    }
                },
            },
        },
    )

    report = AUDIT.scan_projection_gap_reality(roots=(tmp_path / "artifacts",), repository_root=tmp_path)
    metrics = report["frequency"]["forced_retry_fallback"]
    assert metrics["shape_occurrence_count"] == 2
    assert metrics["shape_turn_count"] == 1
    assert metrics["finalized_fem_occurrence_count"] == 0
    assert metrics["packaging_only_occurrence_count"] == 2
    assert report["reachability"]["forced_retry_fallback"]["classification"] == "C. Packaging-only"
    assert report["projection_impact"]["current_projected_fallback_count"] == 1
    assert report["projection_impact"]["additional_fallback_count_if_projected"] == 0


def test_provider_family_with_trace_is_not_a_gap(tmp_path: Path) -> None:
    artifact = tmp_path / "data" / "session.json"
    _write_json(
        artifact,
        {
            "_final_emission_meta": {
                "realization_fallback_family": "gpt_budget_or_provider_failure",
                "fallback_provenance_trace": {"source": "fallback"},
            }
        },
    )

    report = AUDIT.scan_projection_gap_reality(roots=(artifact,), repository_root=tmp_path)
    metrics = report["frequency"]["gpt_budget_or_provider_failure_without_trace"]
    assert metrics["shape_occurrence_count"] == 0
    assert report["projection_impact"]["current_projected_fallback_count"] == 1


def test_jsonl_inventory_preserves_turn_and_artifact_counts(tmp_path: Path) -> None:
    artifact = tmp_path / "data" / "session_log.jsonl"
    rows = [
        {"timestamp": "one", "gm_output": {"final_route": "social_fallback_minimal"}},
        {"timestamp": "two", "gm_output": {"final_route": "social_fallback_minimal"}},
    ]
    artifact.parent.mkdir(parents=True)
    artifact.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = AUDIT.scan_projection_gap_reality(roots=(artifact,), repository_root=tmp_path)
    metrics = report["frequency"]["social_fallback_minimal"]
    assert metrics["shape_occurrence_count"] == 2
    assert metrics["shape_turn_count"] == 2
    assert metrics["shape_artifact_count"] == 1
    assert metrics["packaging_only_occurrence_count"] == 2


def test_empty_corpus_classifies_all_shapes_unreachable(tmp_path: Path) -> None:
    report = AUDIT.scan_projection_gap_reality(roots=(tmp_path,), repository_root=tmp_path)

    assert all(metrics["shape_occurrence_count"] == 0 for metrics in report["frequency"].values())
    assert all(
        value["classification"] == "D. Unreachable" for value in report["reachability"].values()
    )
    assert report["projection_impact"]["estimated_adjusted_coverage"] == pytest.approx(15 / 19)


def test_projection_audit_reports_are_scanned_but_not_counted_as_runtime_evidence(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "projection_coverage_report.json"
    _write_json(
        artifact,
        {"unprojected_shapes": [{"evidence_shape": {"final_route": "forced_retry_fallback"}}]},
    )

    report = AUDIT.scan_projection_gap_reality(roots=(tmp_path / "artifacts",), repository_root=tmp_path)
    assert report["frequency"]["forced_retry_fallback"]["shape_occurrence_count"] == 0
    assert report["scan_scope"]["audit_reference_artifacts_excluded_from_occurrences"] == [
        "artifacts/projection_coverage_report.json"
    ]


def test_report_writer_is_deterministic(tmp_path: Path) -> None:
    report = AUDIT.scan_projection_gap_reality(roots=(tmp_path,), repository_root=tmp_path)
    first = AUDIT.write_report(report, tmp_path / "one.json")
    second = AUDIT.write_report(report, tmp_path / "two.json")
    assert first.read_bytes() == second.read_bytes()
    assert first.read_text(encoding="utf-8").endswith("\n")
