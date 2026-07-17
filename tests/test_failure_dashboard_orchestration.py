from __future__ import annotations

import ast
from pathlib import Path

import tests.helpers.failure_dashboard_orchestration as orchestration_module
import tests.helpers.failure_dashboard_report as report_module
from tests.helpers.failure_dashboard_orchestration import (
    clear_requested_artifact_recordings,
    write_requested_dashboard_artifacts,
)


def test_compatibility_wrappers_reference_same_functions() -> None:
    assert report_module.write_requested_dashboard_artifacts is write_requested_dashboard_artifacts
    assert report_module.clear_requested_artifact_recordings is clear_requested_artifact_recordings


def test_orchestration_module_has_no_top_level_report_import() -> None:
    source_path = Path(orchestration_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    top_level_imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_report" not in top_level_imports
    assert "tests.helpers.failure_dashboard_drift" in top_level_imports
    assert "tests.helpers.failure_dashboard_stability" in top_level_imports
    assert "tests.helpers.failure_dashboard_session" in top_level_imports


def test_report_hub_imports_orchestration_module() -> None:
    source_path = Path(report_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_orchestration" in imported_modules


def test_clear_requested_artifact_recordings_respects_env_gates(monkeypatch) -> None:
    cleared: list[str] = []
    monkeypatch.setattr(
        orchestration_module,
        "clear_recorded_failure_dashboard_rows",
        lambda: cleared.append("dashboard"),
    )
    monkeypatch.setattr(
        orchestration_module,
        "clear_recorded_rerun_drift_scorecards",
        lambda: cleared.append("rerun"),
    )
    monkeypatch.setattr(
        orchestration_module,
        "clear_recorded_long_session_stability_scorecards",
        lambda: cleared.append("stability"),
    )
    monkeypatch.setattr(
        report_module,
        "failure_dashboard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        orchestration_module,
        "rerun_drift_scorecard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        orchestration_module,
        "long_session_stability_scorecard_requested",
        lambda env=None: True,
    )

    clear_requested_artifact_recordings(env={"ALL": "1"})

    assert cleared == ["dashboard", "rerun", "stability"]


def test_write_requested_dashboard_artifacts_ordering_on_failure(monkeypatch, tmp_path: Path) -> None:
    order: list[str] = []
    failure_path = tmp_path / "failure_report.md"

    monkeypatch.setattr(
        report_module,
        "write_protected_replay_failure_report_if_present",
        lambda **kwargs: (order.append("protected"), failure_path)[1],
    )
    monkeypatch.setattr(
        orchestration_module,
        "rerun_drift_scorecard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        orchestration_module,
        "write_rerun_drift_scorecard_artifacts",
        lambda *args, **kwargs: (order.append("rerun"), (tmp_path / "rerun.json", tmp_path / "rerun.md"))[1],
    )
    monkeypatch.setattr(
        report_module,
        "failure_dashboard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        report_module,
        "write_failure_dashboard_artifact",
        lambda *args, **kwargs: (order.append("dashboard"), tmp_path / "dashboard.md")[1],
    )

    written = write_requested_dashboard_artifacts(exitstatus=1, env={"ALL": "1"})

    assert order == ["protected", "dashboard"]
    assert written == [failure_path, tmp_path / "dashboard.md"]


def test_write_requested_dashboard_artifacts_ordering_on_success(monkeypatch, tmp_path: Path) -> None:
    order: list[str] = []

    monkeypatch.setattr(
        report_module,
        "write_protected_replay_failure_report_if_present",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        orchestration_module,
        "rerun_drift_scorecard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        orchestration_module,
        "write_rerun_drift_scorecard_artifacts",
        lambda *args, **kwargs: (order.append("rerun"), (tmp_path / "rerun.json", tmp_path / "rerun.md"))[1],
    )
    monkeypatch.setattr(
        orchestration_module,
        "long_session_stability_scorecard_requested",
        lambda env=None: True,
    )
    monkeypatch.setattr(
        orchestration_module,
        "write_long_session_stability_scorecard_artifacts",
        lambda *args, **kwargs: (order.append("stability"), (tmp_path / "stab.json", tmp_path / "stab.md"))[1],
    )
    monkeypatch.setattr(
        report_module,
        "failure_dashboard_requested",
        lambda env=None: False,
    )

    write_requested_dashboard_artifacts(exitstatus=0, env={"ALL": "1"})

    assert order == ["rerun", "stability"]


def test_write_requested_dashboard_artifacts_skips_success_only_branches_on_failure(monkeypatch, tmp_path: Path) -> None:
    rerun_called = False
    stability_called = False

    monkeypatch.setattr(
        report_module,
        "write_protected_replay_failure_report_if_present",
        lambda **kwargs: tmp_path / "failure_report.md",
    )
    monkeypatch.setattr(
        orchestration_module,
        "rerun_drift_scorecard_requested",
        lambda env=None: True,
    )

    def _rerun(*args, **kwargs):
        nonlocal rerun_called
        rerun_called = True
        return tmp_path / "rerun.json", tmp_path / "rerun.md"

    monkeypatch.setattr(orchestration_module, "write_rerun_drift_scorecard_artifacts", _rerun)
    monkeypatch.setattr(
        orchestration_module,
        "long_session_stability_scorecard_requested",
        lambda env=None: True,
    )

    def _stability(*args, **kwargs):
        nonlocal stability_called
        stability_called = True
        return tmp_path / "stab.json", tmp_path / "stab.md"

    monkeypatch.setattr(orchestration_module, "write_long_session_stability_scorecard_artifacts", _stability)
    monkeypatch.setattr(report_module, "failure_dashboard_requested", lambda env=None: False)

    write_requested_dashboard_artifacts(exitstatus=1, env={"ALL": "1"})

    assert rerun_called is False
    assert stability_called is False


def test_report_hub_delegates_orchestration_writer(monkeypatch, tmp_path: Path) -> None:
    dashboard_path = tmp_path / "via_report_hub.md"

    monkeypatch.setattr(
        report_module,
        "write_protected_replay_failure_report_if_present",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(orchestration_module, "rerun_drift_scorecard_requested", lambda env=None: False)
    monkeypatch.setattr(orchestration_module, "long_session_stability_scorecard_requested", lambda env=None: False)
    monkeypatch.setattr(report_module, "failure_dashboard_requested", lambda env=None: True)
    monkeypatch.setattr(
        report_module,
        "write_failure_dashboard_artifact",
        lambda *args, **kwargs: dashboard_path,
    )
    monkeypatch.setattr(orchestration_module, "recorded_failure_dashboard_rows", lambda: [{"scenario_id": "probe"}])

    written = report_module.write_requested_dashboard_artifacts(exitstatus=0, env={"ALL": "1"})

    assert written == [dashboard_path]
