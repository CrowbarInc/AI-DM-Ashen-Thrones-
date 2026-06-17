"""Protected golden replay assertion bridge diagnostics.

This file owns protected golden replay assertion bridge diagnostics.
Dashboard/classifier row semantics remain with failure dashboard/classifier
owner suites. Full replay orchestration remains with golden replay integration
suites.
"""

from __future__ import annotations

import pytest

from tests.helpers.failure_dashboard_report import (
    clear_recorded_protected_replay_failures,
    recorded_protected_replay_failure_rows,
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
    finally:
        clear_recorded_protected_replay_failures()
