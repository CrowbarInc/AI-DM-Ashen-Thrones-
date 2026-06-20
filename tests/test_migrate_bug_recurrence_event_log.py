"""Tests for bug recurrence event log lane migration (BQ3.7)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.helpers.replay_bug_recurrence import (
    DEFAULT_EVENT_SOURCE,
    PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    append_recurrence_events,
    build_recurrence_key,
    empty_recurrence_event_log,
    load_recurrence_event_log,
    write_recurrence_event_log,
)

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "migrate_bug_recurrence_event_log.py"
SPEC = importlib.util.spec_from_file_location("migrate_bug_recurrence_event_log_tool", TOOL)
assert SPEC and SPEC.loader
MIGRATE = importlib.util.module_from_spec(SPEC)
sys.modules["migrate_bug_recurrence_event_log_tool"] = MIGRATE
SPEC.loader.exec_module(MIGRATE)


def _classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "vocative_override_after_prior_continuity",
        "turn_index": 1,
        "category": "projection",
        "primary_owner": "projection",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "tests/helpers/golden_replay.py",
    }
    row.update(overrides)
    return row


def _build_unified_fixture_log() -> dict[str, object]:
    protected = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row()],
        event_metadata={
            "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
            "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
            "recorded_at": "2026-06-04T22:31:59Z",
        },
    )
    session = append_recurrence_events(
        protected,
        [
            _classification_row(
                scenario_id=None,
                field_path="route_kind",
                investigate_first="unknown",
                owner_drift_bucket="route_drift",
            )
        ],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )
    return session


def _migration_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "event_log": tmp_path / "bug_recurrence_event_log.json",
        "session_diagnostic": tmp_path / "bug_recurrence_session_diagnostic_event_log.json",
        "history_json": tmp_path / "bug_recurrence_history.json",
        "history_md": tmp_path / "bug_recurrence_history.md",
        "legacy": tmp_path / "bug_recurrence_event_log.legacy.json",
        "report": tmp_path / "BQ37_recurrence_history_migration.md",
    }


def test_migration_creates_byte_for_byte_legacy_archive(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    unified = _build_unified_fixture_log()
    write_recurrence_event_log(paths["event_log"], unified)
    original_bytes = paths["event_log"].read_bytes()

    MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    assert paths["legacy"].read_bytes() == original_bytes


def test_migration_split_counts_equal_original(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    unified = _build_unified_fixture_log()
    write_recurrence_event_log(paths["event_log"], unified)
    original_count = len(unified["events"])

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    protected_log = load_recurrence_event_log(paths["event_log"])
    diagnostic_log = load_recurrence_event_log(paths["session_diagnostic"])

    assert result["verification"]["no_events_lost"] is True
    assert len(protected_log["events"]) + len(diagnostic_log["events"]) == original_count
    assert result["summary"]["protected_event_count"] == 1
    assert result["summary"]["diagnostic_event_count"] == original_count - 1


def test_migration_is_idempotent(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())
    kwargs = {
        "event_log_path": paths["event_log"],
        "session_diagnostic_event_log_path": paths["session_diagnostic"],
        "history_json_path": paths["history_json"],
        "history_md_path": paths["history_md"],
        "legacy_archive_path": paths["legacy"],
        "report_path": paths["report"],
    }

    first = MIGRATE.migrate_bug_recurrence_event_log(**kwargs)
    protected_after_first = paths["event_log"].read_text(encoding="utf-8")
    diagnostic_after_first = paths["session_diagnostic"].read_text(encoding="utf-8")
    history_after_first = paths["history_json"].read_text(encoding="utf-8")
    legacy_bytes = paths["legacy"].read_bytes()

    second = MIGRATE.migrate_bug_recurrence_event_log(**kwargs)

    assert first["summary"] == second["summary"]
    assert paths["event_log"].read_text(encoding="utf-8") == protected_after_first
    assert paths["session_diagnostic"].read_text(encoding="utf-8") == diagnostic_after_first
    assert paths["history_json"].read_text(encoding="utf-8") == history_after_first
    assert paths["legacy"].read_bytes() == legacy_bytes


def test_protected_history_regenerated_from_protected_lane_only(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    history = json.loads(paths["history_json"].read_text(encoding="utf-8"))
    protected_metric = result["protected"]["regression_recurrence_rate"]

    assert history["total_rows"] == 1
    assert history["unique_recurrence_count"] == 1
    assert history["regression_recurrence_rate"]["numerator"] == protected_metric["numerator"] == 0
    assert history["regression_recurrence_rate"]["denominator"] == protected_metric["denominator"] == 1
    assert history["regression_recurrence_rate"]["rate"] == 0.0
    assert history["protected_replay_regression_recurrence_rate"]["population"] == "protected_replay_history"


def test_diagnostic_events_never_appear_in_protected_history(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    diagnostic_log = load_recurrence_event_log(paths["session_diagnostic"])
    history = json.loads(paths["history_json"].read_text(encoding="utf-8"))
    diagnostic_keys = {
        str(event.get("recurrence_key") or build_recurrence_key(event))
        for event in diagnostic_log["events"]
    }
    history_keys = {str(entry["recurrence_key"]) for entry in history["recurrences"]}

    assert diagnostic_keys
    assert history_keys
    assert diagnostic_keys.isdisjoint(history_keys)


def test_dry_run_does_not_write_artifacts(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())
    original_bytes = paths["event_log"].read_bytes()

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert paths["event_log"].read_bytes() == original_bytes
    assert not paths["legacy"].exists()
    assert not paths["history_json"].exists()
    assert not paths["report"].exists()
