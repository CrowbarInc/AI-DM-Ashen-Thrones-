from __future__ import annotations

import ast
import json
from pathlib import Path

import tests.helpers.failure_dashboard_report as report_module
import tests.helpers.failure_dashboard_stability as stability_module
from tests.helpers.failure_dashboard_paths import (
    LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
)
from tests.helpers.failure_dashboard_session import (
    clear_recorded_long_session_stability_scorecards,
    record_long_session_stability_scorecard,
    recorded_long_session_stability_scorecards,
)
from tests.helpers.failure_dashboard_stability import (
    long_session_stability_scorecard_requested,
    render_long_session_stability_scorecard_markdown,
    write_long_session_stability_scorecard_artifacts,
    write_long_session_stability_scorecard_artifacts_if_requested,
)
from tests.helpers.golden_replay_api import build_long_session_stability_scorecard


def _route_drift_scorecard(scenario_id: str = "stability_probe") -> dict:
    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "social", "selected_speaker_id": "runner"},
        ],
    )


def test_compatibility_wrappers_reference_same_functions() -> None:
    assert report_module.render_long_session_stability_scorecard_markdown is render_long_session_stability_scorecard_markdown
    assert report_module.write_long_session_stability_scorecard_artifacts is write_long_session_stability_scorecard_artifacts
    assert (
        report_module.write_long_session_stability_scorecard_artifacts_if_requested
        is write_long_session_stability_scorecard_artifacts_if_requested
    )
    assert report_module.long_session_stability_scorecard_requested is long_session_stability_scorecard_requested


def test_stability_markdown_output_is_stable() -> None:
    scorecard = _route_drift_scorecard()
    markdown = render_long_session_stability_scorecard_markdown(
        scorecard,
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest stability module",
    )
    assert markdown.startswith("# Long-Session Stability Scorecard")
    assert "- Report only: `true`" in markdown
    assert "- Advisory only: `true`" in markdown
    assert "- Route changes: `1`" in markdown
    assert "## Stability Ownership" in markdown
    assert "`route_drift`" in markdown


def test_stability_json_output_is_stable(tmp_path: Path) -> None:
    scorecard = _route_drift_scorecard()
    json_path = tmp_path / LONG_SESSION_STABILITY_SCORECARD_JSON_PATH.name
    markdown_path = tmp_path / LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH.name

    write_long_session_stability_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest stability module",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_only"] is True
    assert payload["scenario_id"] == "stability_probe"
    assert payload["route_stability"]["route_change_count"] == 1
    assert "Long-Session Stability Scorecard" in markdown_path.read_text(encoding="utf-8")


def test_stability_artifact_filenames_unchanged() -> None:
    assert LONG_SESSION_STABILITY_SCORECARD_JSON_PATH.name == "long_session_stability_scorecard.json"
    assert LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH.name == "long_session_stability_scorecard.md"
    assert LONG_SESSION_STABILITY_SCORECARD_JSON_PATH.as_posix().endswith(
        "artifacts/golden_replay/long_session_stability_scorecard.json"
    )


def test_stability_scorecard_history_ordering_in_markdown() -> None:
    prior = _route_drift_scorecard("prior_run")
    current = _route_drift_scorecard("current_run")
    markdown = render_long_session_stability_scorecard_markdown(
        current,
        stability_scorecard_history=[prior, current],
        generated_at="2026-06-24T00:00:00Z",
    )
    assert "## Stability Trends" in markdown or "## Stability Trend" in markdown
    assert "current_run" in markdown


def test_session_collected_stability_data_flows_to_writer(tmp_path: Path) -> None:
    scorecard = _route_drift_scorecard("session_flow_probe")
    clear_recorded_long_session_stability_scorecards()
    try:
        record_long_session_stability_scorecard(scorecard)
        assert recorded_long_session_stability_scorecards() == [scorecard]

        json_path = tmp_path / "session_flow.json"
        markdown_path = tmp_path / "session_flow.md"
        write_long_session_stability_scorecard_artifacts(
            scorecard,
            json_path=json_path,
            markdown_path=markdown_path,
            generated_at="2026-06-24T00:00:00Z",
        )
        assert json.loads(json_path.read_text(encoding="utf-8"))["scenario_id"] == "session_flow_probe"
        assert "session_flow_probe" in markdown_path.read_text(encoding="utf-8")
    finally:
        clear_recorded_long_session_stability_scorecards()


def test_stability_writer_opt_in_gate(tmp_path: Path) -> None:
    scorecard = _route_drift_scorecard()
    json_path = tmp_path / "opt_in.json"
    markdown_path = tmp_path / "opt_in.md"

    written = write_long_session_stability_scorecard_artifacts_if_requested(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        env={},
    )
    assert written is None
    assert not json_path.exists()
    assert not markdown_path.exists()


def test_stability_module_delegates_to_replay_drift_reports() -> None:
    source_path = Path(stability_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.replay_drift_reports" in imported_modules
    assert "tests.helpers.failure_dashboard_report" not in imported_modules
    assert "tests.helpers.failure_dashboard_session" in imported_modules
    assert "tests.helpers.failure_dashboard_paths" in imported_modules

    source_text = source_path.read_text(encoding="utf-8")
    assert "def build_long_session_stability_history" not in source_text
    assert "build_long_session_stability_history(" in source_text


def test_report_hub_imports_stability_module() -> None:
    source_path = Path(report_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_stability" in imported_modules


def test_report_hub_delegates_stability_writer(tmp_path: Path) -> None:
    scorecard = _route_drift_scorecard("via_report_hub")
    json_path = tmp_path / "via_report_hub.json"
    markdown_path = tmp_path / "via_report_hub.md"

    report_module.write_long_session_stability_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-24T00:00:00Z",
        command_used="pytest report hub",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["scenario_id"] == "via_report_hub"
    assert "Long-Session Stability Scorecard" in markdown_path.read_text(encoding="utf-8")
