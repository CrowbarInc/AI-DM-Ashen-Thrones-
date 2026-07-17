from __future__ import annotations

import ast
from pathlib import Path

import pytest

import tests.helpers.failure_dashboard_paths as paths_module
import tests.helpers.failure_dashboard_report as report_module
import tests.helpers.replay_bug_recurrence as recurrence_module


CANONICAL_PATH_CONSTANTS: tuple[str, ...] = (
    "FAILURE_DASHBOARD_LATEST_PATH",
    "PROTECTED_REPLAY_FAILURE_REPORT_PATH",
    "RERUN_DRIFT_SCORECARD_JSON_PATH",
    "RERUN_DRIFT_SCORECARD_MARKDOWN_PATH",
    "LONG_SESSION_STABILITY_SCORECARD_JSON_PATH",
    "LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH",
    "OWNER_DRIFT_LONGITUDINAL_JSON_PATH",
    "OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH",
    "OWNER_DRIFT_HOTSPOTS_JSON_PATH",
    "OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH",
    "OWNER_DRIFT_TRENDS_JSON_PATH",
    "OWNER_DRIFT_TRENDS_MARKDOWN_PATH",
    "OWNER_DRIFT_RISK_JSON_PATH",
    "OWNER_DRIFT_RISK_MARKDOWN_PATH",
    "BUG_RECURRENCE_HISTORY_JSON_PATH",
    "BUG_RECURRENCE_HISTORY_MARKDOWN_PATH",
    "BUG_RECURRENCE_EVENT_LOG_JSON_PATH",
    "BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH",
    "BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH",
    "BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH",
    "RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH",
)

CANONICAL_ENV_CONSTANTS: tuple[str, ...] = (
    "FAILURE_DASHBOARD_ENV_VAR",
    "RERUN_DRIFT_SCORECARD_ENV_VAR",
    "LONG_SESSION_STABILITY_SCORECARD_ENV_VAR",
)


@pytest.mark.parametrize("name", CANONICAL_PATH_CONSTANTS)
def test_path_module_exposes_canonical_artifact_paths(name: str) -> None:
    value = getattr(paths_module, name)
    assert isinstance(value, Path)
    assert str(value).replace("\\", "/")


@pytest.mark.parametrize("name", CANONICAL_PATH_CONSTANTS)
def test_failure_dashboard_report_reexports_path_aliases(name: str) -> None:
    assert getattr(report_module, name) is getattr(paths_module, name)


@pytest.mark.parametrize("name", CANONICAL_ENV_CONSTANTS)
def test_failure_dashboard_report_reexports_env_gate_aliases(name: str) -> None:
    assert getattr(report_module, name) is getattr(paths_module, name)


def test_canonical_golden_replay_artifact_directories_unchanged() -> None:
    golden_replay_paths = [
        getattr(paths_module, name)
        for name in CANONICAL_PATH_CONSTANTS
        if getattr(paths_module, name).as_posix().startswith("artifacts/golden_replay/")
    ]
    assert golden_replay_paths
    for path in golden_replay_paths:
        assert path.parent.as_posix() == "artifacts/golden_replay"


def test_failure_dashboard_latest_directory_unchanged() -> None:
    assert paths_module.FAILURE_DASHBOARD_LATEST_PATH.as_posix() == "audits/failure_dashboard_latest.md"


def test_bug_recurrence_path_helpers_for_canonical_history_json() -> None:
    history = paths_module.BUG_RECURRENCE_HISTORY_JSON_PATH
    assert paths_module.bug_recurrence_event_log_path(history) == paths_module.BUG_RECURRENCE_EVENT_LOG_JSON_PATH
    assert (
        paths_module.bug_recurrence_session_diagnostic_event_log_path(history)
        == paths_module.BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH
    )
    assert (
        paths_module.bug_recurrence_session_event_log_path(history)
        == paths_module.BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH
    )
    assert (
        paths_module.bug_recurrence_synthetic_test_artifact_event_log_path(history)
        == paths_module.BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH
    )
    assert (
        paths_module.bug_recurrence_trajectory_history_path(history)
        == paths_module.RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
    )


def test_bug_recurrence_path_helpers_for_custom_history_json(tmp_path: Path) -> None:
    custom_history = tmp_path / "custom_recurrence_history.json"
    assert paths_module.bug_recurrence_event_log_path(custom_history) == tmp_path / "custom_recurrence_history_event_log.json"
    assert (
        paths_module.bug_recurrence_session_diagnostic_event_log_path(custom_history)
        == tmp_path / "custom_recurrence_history_session_diagnostic_event_log.json"
    )
    assert (
        paths_module.bug_recurrence_session_event_log_path(custom_history)
        == tmp_path / "custom_recurrence_history_session_event_log.json"
    )
    assert (
        paths_module.bug_recurrence_synthetic_test_artifact_event_log_path(custom_history)
        == tmp_path / "custom_recurrence_history_synthetic_test_artifact_event_log.json"
    )
    assert paths_module.bug_recurrence_trajectory_history_path(custom_history) == tmp_path / "recurrence_trajectory_history.json"


def test_replay_bug_recurrence_does_not_import_failure_dashboard_report_for_paths() -> None:
    source_path = Path(recurrence_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_report" not in imported_modules


def test_writer_default_paths_match_canonical_locations(tmp_path: Path) -> None:
    from tests.helpers.failure_dashboard_report import (
        write_owner_drift_hotspot_artifacts,
        write_rerun_drift_scorecard_artifacts,
    )

    scorecard_json = tmp_path / "rerun_drift_scorecard.json"
    scorecard_md = tmp_path / "rerun_drift_scorecard.md"
    write_rerun_drift_scorecard_artifacts(
        {"comparison_available": False, "reason": "test"},
        json_path=scorecard_json,
        markdown_path=scorecard_md,
        longitudinal_json_path=tmp_path / "owner_drift_longitudinal.json",
        longitudinal_markdown_path=tmp_path / "owner_drift_longitudinal.md",
    )
    assert scorecard_json.is_file()
    assert scorecard_md.is_file()

    hotspot_json = tmp_path / "owner_drift_hotspots.json"
    hotspot_md = tmp_path / "owner_drift_hotspots.md"
    write_owner_drift_hotspot_artifacts(
        [],
        json_path=hotspot_json,
        markdown_path=hotspot_md,
    )
    assert hotspot_json.is_file()
    assert hotspot_md.is_file()

    assert paths_module.RERUN_DRIFT_SCORECARD_JSON_PATH.as_posix().endswith("rerun_drift_scorecard.json")
    assert paths_module.OWNER_DRIFT_HOTSPOTS_JSON_PATH.as_posix().endswith("owner_drift_hotspots.json")
