"""Protected golden replay assertion bridge diagnostics.

This file owns protected golden replay assertion bridge diagnostics.
Dashboard/classifier row semantics remain with failure dashboard/classifier
owner suites. Full replay orchestration remains with golden replay integration
suites.
"""

from __future__ import annotations

import json

import pytest

from tests.helpers.failure_dashboard_report import (
    clear_recorded_protected_replay_failures,
    protected_replay_recurrence_event_metadata,
    recorded_protected_replay_failure_rows,
    write_owner_drift_risk_artifacts,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.golden_replay import assert_protected_golden_turn_observation
from tests.helpers.replay_observed_row_fixtures import protected_speaker_failure_turn


def test_protected_golden_assertion_failure_records_canonical_report(tmp_path):
    turn = protected_speaker_failure_turn()
    report_path = tmp_path / "replay_failure_report.md"
    clear_recorded_protected_replay_failures()
    try:
        assert write_protected_replay_failure_report_if_present(path=report_path) is None
        with pytest.raises(AssertionError) as exc:
            assert_protected_golden_turn_observation(
                turn,
                {"equals": {"selected_speaker_id": "runner"}},
                scenario_id="synthetic_protected_bridge",
                debug_context="synthetic reporting bridge context",
            )
        assert "golden replay expectation failed: exact value mismatch" in str(exc.value)

        rows = recorded_protected_replay_failure_rows()
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == "synthetic_protected_bridge"
        assert rows[0]["field_path"] == "selected_speaker_id"

        write_owner_drift_risk_artifacts(
            rows,
            json_path=tmp_path / "owner_drift_risk.json",
            markdown_path=tmp_path / "owner_drift_risk.md",
            command_used="pytest protected bridge",
            generated_at="2026-06-12T00:00:00Z",
            recurrence_event_metadata=protected_replay_recurrence_event_metadata(
                command_used="pytest protected bridge",
                generated_at="2026-06-12T00:00:00Z",
                artifact_source=report_path,
            ),
        )
        event = json.loads((tmp_path / "bug_recurrence_event_log.json").read_text(encoding="utf-8"))["events"][0]
        assert event["event_source"] == "protected_replay_failure"
        assert event["command"] == "pytest protected bridge"
        assert event["recorded_at"] == "2026-06-12T00:00:00Z"
        assert rows[0]["test_node_id"]
        assert event["test_node_id"] == rows[0]["test_node_id"]
        assert "test_protected_golden_assertion_failure_records_canonical_report" in event["test_node_id"]
    finally:
        clear_recorded_protected_replay_failures()
