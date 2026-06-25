from __future__ import annotations

import ast
import json
from pathlib import Path

import tests.helpers.failure_dashboard_drift as drift_module
import tests.helpers.failure_dashboard_report as report_module
from tests.helpers.failure_dashboard_drift import (
    render_rerun_drift_scorecard_markdown,
    write_owner_drift_hotspot_artifacts,
    write_owner_drift_longitudinal_artifacts,
    write_owner_drift_risk_artifacts,
    write_owner_drift_trend_artifacts,
    write_rerun_drift_scorecard_artifacts,
)
from tests.helpers.failure_dashboard_paths import (
    OWNER_DRIFT_HOTSPOTS_JSON_PATH,
    OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    OWNER_DRIFT_RISK_JSON_PATH,
    OWNER_DRIFT_TRENDS_JSON_PATH,
    RERUN_DRIFT_SCORECARD_JSON_PATH,
)
from tests.helpers.golden_replay_api import compare_golden_replay_reruns
from tests.helpers.replay_observed_row_fixtures import synthetic_rerun_turn


def _synthetic_rerun_scorecard() -> dict:
    return compare_golden_replay_reruns(
        [synthetic_rerun_turn(final_text="The runner answers.")],
        [
            synthetic_rerun_turn(
                selected_speaker_id="guard",
                route_kind="action",
                final_text="The guard answers.",
            )
        ],
    )


def test_compatibility_wrappers_reference_same_functions() -> None:
    assert report_module.render_rerun_drift_scorecard_markdown is render_rerun_drift_scorecard_markdown
    assert report_module.write_rerun_drift_scorecard_artifacts is write_rerun_drift_scorecard_artifacts
    assert report_module.write_owner_drift_hotspot_artifacts is write_owner_drift_hotspot_artifacts
    assert report_module.write_owner_drift_longitudinal_artifacts is write_owner_drift_longitudinal_artifacts
    assert report_module.write_owner_drift_trend_artifacts is write_owner_drift_trend_artifacts
    assert report_module.write_owner_drift_risk_artifacts is write_owner_drift_risk_artifacts


def test_drift_markdown_output_is_stable() -> None:
    scorecard = _synthetic_rerun_scorecard()
    markdown = render_rerun_drift_scorecard_markdown(
        scorecard,
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest drift module",
    )
    assert markdown.startswith("# Golden Rerun Drift Scorecard")
    assert "## Owner Drift Summary" in markdown
    assert "| `speaker_drift` | `1` |" in markdown
    assert "## Compact Per-Turn Drift Rows" in markdown


def test_drift_json_output_is_stable(tmp_path: Path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / RERUN_DRIFT_SCORECARD_JSON_PATH.name
    markdown_path = tmp_path / "rerun_drift_scorecard.md"

    write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        longitudinal_json_path=tmp_path / OWNER_DRIFT_LONGITUDINAL_JSON_PATH.name,
        longitudinal_markdown_path=tmp_path / "owner_drift_longitudinal.md",
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest drift module",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_only"] is True
    assert payload["total_turns_compared"] == 1
    assert isinstance(payload.get("owner_drift_classifications"), list)


def test_drift_artifact_filenames_unchanged() -> None:
    assert RERUN_DRIFT_SCORECARD_JSON_PATH.name == "rerun_drift_scorecard.json"
    assert OWNER_DRIFT_LONGITUDINAL_JSON_PATH.name == "owner_drift_longitudinal.json"
    assert OWNER_DRIFT_HOTSPOTS_JSON_PATH.name == "owner_drift_hotspots.json"
    assert OWNER_DRIFT_TRENDS_JSON_PATH.name == "owner_drift_trends.json"
    assert OWNER_DRIFT_RISK_JSON_PATH.name == "owner_drift_risk.json"


def test_rerun_drift_cascade_write_order(monkeypatch) -> None:
    order: list[str] = []
    scorecard = _synthetic_rerun_scorecard()

    def _track(name: str, return_value: object = None):
        def _wrapped(*_args, **_kwargs):
            order.append(name)
            return return_value

        return _wrapped

    monkeypatch.setattr(
        drift_module,
        "append_owner_drift_longitudinal_markdown",
        _track("append_longitudinal"),
    )
    monkeypatch.setattr(
        drift_module,
        "write_owner_drift_longitudinal_artifacts",
        _track("longitudinal", (Path("long.json"), Path("long.md"))),
    )
    monkeypatch.setattr(
        drift_module,
        "write_owner_drift_hotspot_artifacts",
        _track("hotspots", (Path("hot.json"), Path("hot.md"))),
    )
    monkeypatch.setattr(
        drift_module,
        "write_owner_drift_trend_artifacts",
        _track("trends", (Path("trend.json"), Path("trend.md"))),
    )
    monkeypatch.setattr(
        drift_module,
        "write_owner_drift_risk_artifacts",
        _track("risk", (Path("risk.json"), Path("risk.md"))),
    )

    write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=Path("scorecard.json"),
        markdown_path=Path("scorecard.md"),
        generated_at="2026-06-24T00:00:00Z",
    )

    assert order == [
        "append_longitudinal",
        "longitudinal",
        "hotspots",
        "trends",
        "risk",
    ]


def test_drift_module_delegates_to_replay_drift_reports() -> None:
    source_path = Path(drift_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.replay_drift_reports" in imported_modules
    assert "tests.helpers.failure_dashboard_report" not in imported_modules

    source_text = source_path.read_text(encoding="utf-8")
    assert "def aggregate_owner_drift_history" not in source_text
    assert "def build_hotspot_rankings" not in source_text
    assert "def build_risk_payload" not in source_text
    assert "aggregate_owner_drift_history(" in source_text
    assert "build_hotspot_rankings(" in source_text


def test_report_hub_imports_drift_module() -> None:
    source_path = Path(report_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_drift" in imported_modules


def test_report_hub_delegates_drift_writer(tmp_path: Path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / "via_report_hub.json"
    markdown_path = tmp_path / "via_report_hub.md"

    report_module.write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        longitudinal_json_path=tmp_path / "longitudinal.json",
        longitudinal_markdown_path=tmp_path / "longitudinal.md",
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest report hub",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total_turns_compared"] == 1
    assert "Golden Rerun Drift Scorecard" in markdown_path.read_text(encoding="utf-8")


def test_longitudinal_writer_uses_expected_filenames(tmp_path: Path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / OWNER_DRIFT_LONGITUDINAL_JSON_PATH.name
    markdown_path = tmp_path / "owner_drift_longitudinal.md"

    written_json, written_markdown = write_owner_drift_longitudinal_artifacts(
        [scorecard],
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["advisory_only"] is True
    assert "Owner Drift Longitudinal Report" in markdown_path.read_text(encoding="utf-8")
