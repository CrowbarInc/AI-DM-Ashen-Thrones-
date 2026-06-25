from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import tests.helpers.replay_bug_recurrence as facade
import tests.helpers.replay_bug_recurrence_events as events_module
import tests.helpers.replay_bug_recurrence_history as history_module
import tests.helpers.replay_bug_recurrence_serialization as serialization_module
import tests.helpers.replay_bug_recurrence_statistics as statistics_module

pytestmark = pytest.mark.unit


def _classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "decomposition_probe",
        "turn_index": 0,
        "category": "speaker",
        "primary_owner": "speaker",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "game/speaker_contract_enforcement.py",
    }
    row.update(overrides)
    return row


def test_facade_reexports_focused_module_symbols() -> None:
    assert facade.build_recurrence_key is events_module.build_recurrence_key
    assert facade.aggregate_recurrence_history is events_module.aggregate_recurrence_history
    assert facade.build_recurrence_timeline is history_module.build_recurrence_timeline
    assert facade.build_recurrence_maturity_assessment is statistics_module.build_recurrence_maturity_assessment
    assert (
        facade.render_recurrence_outcome_validation_report_markdown
        is serialization_module.render_recurrence_outcome_validation_report_markdown
    )


def test_import_direction_avoids_dashboard_cycles() -> None:
    focused_modules = (
        events_module,
        history_module,
        statistics_module,
        serialization_module,
    )
    forbidden = {
        "tests.helpers.failure_dashboard_report",
        "tests.helpers.failure_dashboard_recurrence",
        "tests.helpers.failure_dashboard_session",
    }
    for module in focused_modules:
        source_path = Path(module.__file__).resolve()
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert imported.isdisjoint(forbidden)


def test_recurrence_key_and_history_calculations_unchanged() -> None:
    row = _classification_row()
    assert facade.build_recurrence_key(row) == events_module.build_recurrence_key(row)

    history = facade.aggregate_recurrence_history(facade.recurrence_rows([row, row]))
    assert history["total_rows"] == 2
    assert history["unique_recurrence_count"] == 1
    assert history["recurrences"][0]["occurrence_count"] == 2
    assert history["regression_recurrence_rate"]["rate"] == 1.0


def test_trajectory_history_roundtrip_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "recurrence_trajectory_history.json"
    snapshot = {
        "snapshot_index": 1,
        "timestamp": "2026-06-21T12:00:00Z",
        "artifact_source": "artifacts/golden_replay/bug_recurrence_history.json",
        "protected_observation_count": 3,
        "unique_recurrence_keys": 1,
        "regression_recurrence_rate": 0.0,
        "governance_health_score": 50.0,
        "lifecycle_health_score": 40.0,
        "portfolio_risk_score": 30.0,
        "operational_readiness_score": 60.0,
        "effectiveness_score": 0.5,
        "maturity_score": 55.0,
        "stability_score": 70.0,
        "program_effectiveness_score": 45.0,
    }
    history = facade.append_recurrence_trajectory_history(
        facade.empty_recurrence_trajectory_history(),
        snapshot,
    )
    facade.write_recurrence_trajectory_history(history, path)
    loaded = facade.load_recurrence_trajectory_history(path)
    assert loaded == history
    assert facade.summarize_recurrence_trajectory(loaded)["baseline_only"] is True


def test_event_log_serialization_envelope_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "bug_recurrence_event_log.json"
    payload = facade.append_recurrence_events(
        facade.empty_recurrence_event_log(),
        [_classification_row()],
        event_metadata={"event_source": facade.DEFAULT_EVENT_SOURCE},
    )
    facade.write_recurrence_event_log(path, payload)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == facade.RECURRENCE_SCHEMA_VERSION
    assert loaded["report_only"] is True
    assert len(loaded["events"]) == 1
    assert loaded["events"][0]["recurrence_key"] == facade.build_recurrence_key(_classification_row())
