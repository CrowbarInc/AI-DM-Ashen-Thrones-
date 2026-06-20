"""Tests for bug recurrence history backfill from protected failure reports."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "backfill_bug_recurrence_history.py"
SPEC = importlib.util.spec_from_file_location("backfill_bug_recurrence_history_tool", TOOL)
assert SPEC and SPEC.loader
BACKFILL = importlib.util.module_from_spec(SPEC)
sys.modules["backfill_bug_recurrence_history_tool"] = BACKFILL
SPEC.loader.exec_module(BACKFILL)


MINIMAL_FAILURE_REPORT = """\
# Protected Replay Failure Report

## Run Summary

- Status: `failed`
- Command: `python -m pytest tests/test_golden_replay.py -q`
- Generated at: `2026-06-04T22:31:59Z`

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| vocative_probe | tests/test_golden_replay.py::test_probe | 1 | selected_speaker_id: exact value mismatch | structural_drift | guard | guard_captain | projection | medium | projection | none | tests/helpers/golden_replay.py |
"""


def test_parse_failure_report_classification_rows_minimal_table() -> None:
    rows = BACKFILL.parse_failure_report_classification_rows(MINIMAL_FAILURE_REPORT)

    assert len(rows) == 1
    row = rows[0]
    assert row["scenario_id"] == "vocative_probe"
    assert row["turn_index"] == 1
    assert row["category"] == "projection"
    assert row["field_path"] == "selected_speaker_id"
    assert row["investigate_first"] == "tests/helpers/golden_replay.py"
    assert row["test_node_id"] == "tests/test_golden_replay.py::test_probe"
    assert row["owner_drift_bucket"] == "speaker_drift"


def test_backfill_appends_into_empty_event_log(tmp_path: Path) -> None:
    report_path = tmp_path / "replay_failure_report.md"
    report_path.write_text(MINIMAL_FAILURE_REPORT, encoding="utf-8")

    result = BACKFILL.backfill_bug_recurrence_history(
        failure_report_path=report_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        history_json_path=tmp_path / "bug_recurrence_history.json",
        history_md_path=tmp_path / "bug_recurrence_history.md",
    )

    assert result["parsed_row_count"] == 1
    assert result["append_count"] == 1
    assert result["skipped_duplicate_count"] == 0

    event_log = json.loads((tmp_path / "bug_recurrence_event_log.json").read_text(encoding="utf-8"))
    history = json.loads((tmp_path / "bug_recurrence_history.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "bug_recurrence_history.md").read_text(encoding="utf-8")

    assert len(event_log["events"]) == 1
    event = event_log["events"][0]
    assert event["event_source"] == "protected_replay_failure"
    assert event["artifact_source"].endswith("replay_failure_report.md")
    assert event["recorded_at"] == "2026-06-04T22:31:59Z"
    assert event["command"] == "python -m pytest tests/test_golden_replay.py -q"
    assert history["total_rows"] == 1
    assert history["unique_recurrence_count"] == 1
    assert history["summary"][0]["status"] == "watch"
    assert "No recurrence history recorded." not in markdown


def test_backfill_is_idempotent(tmp_path: Path) -> None:
    report_path = tmp_path / "replay_failure_report.md"
    report_path.write_text(MINIMAL_FAILURE_REPORT, encoding="utf-8")
    kwargs = {
        "failure_report_path": report_path,
        "event_log_path": tmp_path / "bug_recurrence_event_log.json",
        "history_json_path": tmp_path / "bug_recurrence_history.json",
        "history_md_path": tmp_path / "bug_recurrence_history.md",
    }

    first = BACKFILL.backfill_bug_recurrence_history(**kwargs)
    second = BACKFILL.backfill_bug_recurrence_history(**kwargs)

    assert first["append_count"] == 1
    assert second["append_count"] == 0
    assert second["skipped_duplicate_count"] == 1
    assert len(json.loads((tmp_path / "bug_recurrence_event_log.json").read_text(encoding="utf-8"))["events"]) == 1


def test_backfill_without_failure_table_appends_nothing(tmp_path: Path) -> None:
    report_path = tmp_path / "empty_report.md"
    report_path.write_text("# Protected Replay Failure Report\n\nNo table here.\n", encoding="utf-8")

    result = BACKFILL.backfill_bug_recurrence_history(
        failure_report_path=report_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        history_json_path=tmp_path / "bug_recurrence_history.json",
        history_md_path=tmp_path / "bug_recurrence_history.md",
    )

    assert result["parsed_row_count"] == 0
    assert result["append_count"] == 0
    assert not (tmp_path / "bug_recurrence_event_log.json").exists()


def test_backfill_skips_row_missing_required_fields_with_warning() -> None:
    report = MINIMAL_FAILURE_REPORT.replace("Investigate First |", "Investigate First | Owner Drift Bucket |").replace(
        "tests/helpers/golden_replay.py |",
        "none | speaker_drift |",
    )
    warnings: list[str] = []
    rows = BACKFILL.parse_failure_report_classification_rows(report, warnings=warnings)

    assert rows == []
    assert warnings


def test_backfill_dry_run_reports_append_plan(tmp_path: Path) -> None:
    report_path = tmp_path / "replay_failure_report.md"
    report_path.write_text(MINIMAL_FAILURE_REPORT, encoding="utf-8")

    result = BACKFILL.backfill_bug_recurrence_history(
        failure_report_path=report_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        history_json_path=tmp_path / "bug_recurrence_history.json",
        history_md_path=tmp_path / "bug_recurrence_history.md",
        dry_run=True,
    )

    assert result["append_count"] == 1
    assert not (tmp_path / "bug_recurrence_event_log.json").exists()


def test_backfill_check_passes_after_successful_backfill(tmp_path: Path) -> None:
    report_path = tmp_path / "replay_failure_report.md"
    report_path.write_text(MINIMAL_FAILURE_REPORT, encoding="utf-8")
    kwargs = {
        "failure_report_path": report_path,
        "event_log_path": tmp_path / "bug_recurrence_event_log.json",
        "history_json_path": tmp_path / "bug_recurrence_history.json",
        "history_md_path": tmp_path / "bug_recurrence_history.md",
    }
    BACKFILL.backfill_bug_recurrence_history(**kwargs)
    result = BACKFILL.backfill_bug_recurrence_history(**kwargs, check=True)

    assert result["check_passed"] is True
