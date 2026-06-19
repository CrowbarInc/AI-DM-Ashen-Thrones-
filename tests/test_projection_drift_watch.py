"""Deterministic tests for the BP4 finalized-FEM projection drift watch."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "projection_drift_watch.py"
SPEC = importlib.util.spec_from_file_location("projection_drift_watch_tool", TOOL)
assert SPEC and SPEC.loader
WATCH = importlib.util.module_from_spec(SPEC)
sys.modules["projection_drift_watch_tool"] = WATCH
SPEC.loader.exec_module(WATCH)


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _scan(tmp_path: Path, payload: object) -> dict:
    path = tmp_path / "data" / "transcript.json"
    _write(path, payload)
    return WATCH.scan_projection_drift_watch(roots=(tmp_path / "data",), repository_root=tmp_path)


def test_canonical_watch_registry_contains_only_bp3_shapes() -> None:
    assert set(WATCH.WATCH_SHAPES) == {
        "forced_retry_fallback",
        "nonsocial_fallback_minimal",
        "social_fallback_minimal",
        "provider_failure_without_trace",
    }
    assert all(set(item) == {"name", "bp3_classification", "expected_status", "rationale"} for item in WATCH.WATCH_SHAPES.values())


def test_no_watch_shapes_is_healthy(tmp_path: Path) -> None:
    report = _scan(
        tmp_path,
        {"turns": [{"turn_id": "clean", "meta": {"final_emission_meta": {"final_route": "accept_candidate"}}}]},
    )
    assert report["status"] == "healthy"
    assert report["alerts"] == []
    assert all(value == 0 for value in report["observed_count"].values())


def test_packaging_only_shape_outside_finalized_fem_is_ignored(tmp_path: Path) -> None:
    report = _scan(
        tmp_path,
        {
            "turns": [
                {
                    "turn_id": "packaging",
                    "gm_output": {"final_route": "forced_retry_fallback"},
                    "meta": {"final_emission_meta": {"final_route": "replaced"}},
                }
            ]
        },
    )
    assert report["status"] == "healthy"
    assert report["observed_count"]["forced_retry_fallback"] == 0


def test_finalized_watch_shape_already_projected_is_healthy(tmp_path: Path) -> None:
    report = _scan(
        tmp_path,
        {
            "turns": [
                {
                    "turn_id": "projected",
                    "meta": {
                        "final_emission_meta": {
                            "final_route": "forced_retry_fallback",
                            "fallback_provenance_trace": {"source": "fallback"},
                        }
                    },
                }
            ]
        },
    )
    assert report["observed_count"]["forced_retry_fallback"] == 1
    assert report["observed_with_projection"]["forced_retry_fallback"] == 1
    assert report["observed_without_projection"]["forced_retry_fallback"] == 0
    assert report["alerts"] == []


def test_finalized_unprojected_shape_generates_alert(tmp_path: Path) -> None:
    report = _scan(
        tmp_path,
        {
            "turns": [
                {
                    "turn_id": "gap-1",
                    "route_kind": "observe",
                    "meta": {
                        "final_emission_meta": {
                            "final_route": "nonsocial_fallback_minimal",
                            "final_emitted_source": "nonsocial_empty_repair_hard_line",
                        }
                    },
                }
            ]
        },
    )
    assert report["status"] == "alert"
    assert report["observed_count"]["nonsocial_fallback_minimal"] == 1
    assert report["observed_without_projection"]["nonsocial_fallback_minimal"] == 1
    assert report["new_projection_risk"]["nonsocial_fallback_minimal"]["status"] == "alert"
    assert report["alerts"] == [
        {
            "watch_shape": "nonsocial_fallback_minimal",
            "condition": "finalized_fem_watch_shape_without_fallback_selected_projection",
            "artifact": "data/transcript.json",
            "turn": "gap-1",
            "record_locator": "$.turns[0]",
            "fem_context_path": "$.meta.final_emission_meta",
            "route_kind": "observe",
            "final_route": "nonsocial_fallback_minimal",
            "final_emitted_source": "nonsocial_empty_repair_hard_line",
            "fallback_selected_projected": False,
        }
    ]


def test_provider_trace_suppresses_watch_shape(tmp_path: Path) -> None:
    report = _scan(
        tmp_path,
        {
            "_final_emission_meta": {
                "realization_fallback_family": "gpt_budget_or_provider_failure",
                "fallback_provenance_trace": {"source": "fallback"},
            }
        },
    )
    assert report["observed_count"]["provider_failure_without_trace"] == 0
    assert report["alerts"] == []


def test_deterministic_json_and_markdown_output(tmp_path: Path) -> None:
    report = _scan(tmp_path, {"_final_emission_meta": {"final_route": "social_fallback_minimal"}})
    first_json, first_md = WATCH.write_projection_drift_watch_reports(
        report,
        json_path=tmp_path / "first.json",
        markdown_path=tmp_path / "first.md",
    )
    second_json, second_md = WATCH.write_projection_drift_watch_reports(
        report,
        json_path=tmp_path / "second.json",
        markdown_path=tmp_path / "second.md",
    )
    assert first_json.read_bytes() == second_json.read_bytes()
    assert first_md.read_bytes() == second_md.read_bytes()
    markdown = first_md.read_text(encoding="utf-8")
    assert "# Projection Drift Watch Report" in markdown
    assert "## Alert Conditions" in markdown
    assert "social_fallback_minimal" in markdown
