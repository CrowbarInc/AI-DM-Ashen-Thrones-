from __future__ import annotations

import ast
import json
from pathlib import Path

import tests.helpers.failure_dashboard_recurrence as recurrence_module
import tests.helpers.failure_dashboard_report as report_module
from tests.helpers.failure_dashboard_paths import (
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
)
from tests.helpers.failure_dashboard_recurrence import (
    protected_replay_recurrence_event_metadata,
    render_bug_recurrence_history_markdown,
    write_bug_recurrence_history_artifacts,
)


def _recurrence_classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "bug_recurrence_probe",
        "turn_index": 0,
        "category": "speaker",
        "primary_owner": "speaker",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "game/speaker_contract_enforcement.py",
    }
    row.update(overrides)
    return row


def test_compatibility_wrappers_reference_same_functions() -> None:
    import tests.helpers.failure_dashboard_report as report_module

    assert report_module.render_bug_recurrence_history_markdown is render_bug_recurrence_history_markdown
    assert report_module.write_bug_recurrence_history_artifacts is write_bug_recurrence_history_artifacts
    assert report_module.protected_replay_recurrence_event_metadata is protected_replay_recurrence_event_metadata


def test_recurrence_markdown_empty_history_is_stable() -> None:
    markdown = render_bug_recurrence_history_markdown({})
    assert markdown.startswith("# Bug-Class Recurrence History")
    assert "No recurrence history recorded." in markdown


def test_recurrence_writer_uses_expected_filenames(tmp_path: Path) -> None:
    json_path = tmp_path / BUG_RECURRENCE_HISTORY_JSON_PATH.name
    markdown_path = tmp_path / BUG_RECURRENCE_HISTORY_MARKDOWN_PATH.name
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    written_json, written_markdown = write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row()],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        command_used="pytest recurrence module",
        generated_at="2026-06-12T00:00:00Z",
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used="pytest recurrence module",
            generated_at="2026-06-12T00:00:00Z",
            artifact_source="artifacts/golden_replay/replay_failure_report.md",
        ),
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total_rows"] == 1
    assert "Bug-Class Recurrence History" in markdown_path.read_text(encoding="utf-8")


def test_report_hub_delegates_recurrence_writer(tmp_path: Path) -> None:
    import tests.helpers.failure_dashboard_report as report_module

    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    report_module.write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="via_report_hub")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        generated_at="2026-06-12T00:00:00Z",
        command_used="pytest report hub",
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used="pytest report hub",
            generated_at="2026-06-12T00:00:00Z",
            artifact_source="artifacts/golden_replay/replay_failure_report.md",
        ),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total_rows"] == 1
    assert "via_report_hub" in markdown_path.read_text(encoding="utf-8")


def test_recurrence_module_import_direction() -> None:
    source_path = Path(recurrence_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_report" not in imported_modules
    assert "tests.helpers.failure_dashboard_session" not in imported_modules
    assert "tests.helpers.failure_dashboard_paths" in imported_modules
    assert "tests.helpers.replay_bug_recurrence" in imported_modules


def test_report_hub_imports_recurrence_module() -> None:
    source_path = Path(report_module.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "tests.helpers.failure_dashboard_recurrence" in imported_modules
    assert "tests.helpers.replay_bug_recurrence" not in imported_modules
