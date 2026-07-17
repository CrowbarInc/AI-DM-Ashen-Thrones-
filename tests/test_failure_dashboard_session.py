from __future__ import annotations

import ast
from pathlib import Path

import pytest

import tests.helpers.failure_dashboard_paths as paths_module
import tests.helpers.failure_dashboard_report as report_module
import tests.helpers.failure_dashboard_session as session_module
from tests.helpers.failure_dashboard_report import (
    clear_recorded_failure_dashboard_rows,
    clear_recorded_protected_replay_failures,
    clear_recorded_rerun_drift_scorecards,
    record_failure_dashboard_rows,
    record_protected_replay_assertion_failure,
    record_rerun_drift_scorecard,
    record_runtime_lineage_events,
    recorded_failure_dashboard_rows,
    recorded_protected_replay_failure_rows,
    recorded_rerun_drift_scorecards,
    recorded_runtime_lineage_events,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.replay_observed_row_fixtures import protected_speaker_failure_turn
from game.runtime_lineage_telemetry import make_runtime_lineage_event


@pytest.fixture(autouse=True)
def _clear_session_buffers() -> None:
    session_module.clear_all_session_buffers()
    yield
    session_module.clear_all_session_buffers()


def test_record_failure_dashboard_rows_preserves_order() -> None:
    record_failure_dashboard_rows([{"scenario_id": "a", "turn_index": 1}, {"scenario_id": "b", "turn_index": 2}])
    assert [row["scenario_id"] for row in recorded_failure_dashboard_rows()] == ["a", "b"]


def test_record_runtime_lineage_events_preserves_order() -> None:
    first = make_runtime_lineage_event(event_kind="gate_outcome", stage="gate", gate_path="first")
    second = make_runtime_lineage_event(event_kind="gate_outcome", stage="gate", gate_path="second")
    record_runtime_lineage_events([first, second])
    assert [event["gate_path"] for event in recorded_runtime_lineage_events()] == ["first", "second"]


def test_record_rerun_drift_scorecard_preserves_order() -> None:
    record_rerun_drift_scorecard({"comparison_available": True, "id": 1})
    record_rerun_drift_scorecard({"comparison_available": True, "id": 2})
    assert [item["id"] for item in recorded_rerun_drift_scorecards()] == [1, 2]


def test_clear_failure_dashboard_rows_clears_only_dashboard_buffers() -> None:
    record_failure_dashboard_rows([{"scenario_id": "dash"}])
    record_runtime_lineage_events([{"event": "lineage"}])
    record_rerun_drift_scorecard({"comparison_available": False})

    clear_recorded_failure_dashboard_rows()

    assert recorded_failure_dashboard_rows() == []
    assert recorded_runtime_lineage_events() == []
    assert recorded_rerun_drift_scorecards() == [{"comparison_available": False}]


def test_clear_protected_replay_failures_clears_only_protected_buffers() -> None:
    record_failure_dashboard_rows([{"scenario_id": "dash"}])
    record_protected_replay_assertion_failure(
        scenario_id="s",
        test_node_id="tests/test_x.py::test_y",
        observed_turn=protected_speaker_failure_turn(),
        field_path="selected_speaker_id",
        expected="runner",
        actual="other",
        reason="mismatch",
        drift_bucket="exact_drift",
    )

    clear_recorded_protected_replay_failures()

    assert recorded_protected_replay_failure_rows() == []
    assert recorded_failure_dashboard_rows() == [{"scenario_id": "dash"}]


def test_compatibility_wrappers_share_session_buffers() -> None:
    record_failure_dashboard_rows([{"scenario_id": "via-report"}])
    assert recorded_failure_dashboard_rows() == session_module.recorded_failure_dashboard_rows()


def test_report_writer_consumes_session_records(tmp_path: Path) -> None:
    record_protected_replay_assertion_failure(
        scenario_id="writer_bridge",
        test_node_id="tests/test_failure_dashboard_session.py::test_report_writer_consumes_session_records",
        observed_turn=protected_speaker_failure_turn(),
        field_path="selected_speaker_id",
        expected="runner",
        actual="other",
        reason="mismatch",
        drift_bucket="exact_drift",
    )

    report_path = tmp_path / "replay_failure_report.md"
    written = write_protected_replay_failure_report_if_present(path=report_path)

    assert written == report_path
    assert report_path.is_file()
    assert "writer_bridge" in report_path.read_text(encoding="utf-8")


def test_path_constants_unchanged_by_session_module() -> None:
    assert paths_module.PROTECTED_REPLAY_FAILURE_REPORT_PATH == report_module.PROTECTED_REPLAY_FAILURE_REPORT_PATH


def test_session_module_import_direction() -> None:
    source_path = Path(session_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_report" not in imported_modules
    assert "tests.helpers.replay_drift_reports" not in imported_modules
    assert "tests.helpers.replay_bug_recurrence" not in imported_modules


def test_failure_dashboard_report_imports_session_module() -> None:
    source_path = Path(report_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_session" in imported_modules
