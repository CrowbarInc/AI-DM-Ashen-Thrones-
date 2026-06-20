"""Tests for protected replay recurrence trajectory history (BQ-C2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.failure_dashboard_report import (
    render_bug_recurrence_history_markdown,
)
from tests.helpers.replay_bug_recurrence import (
    RECURRENCE_TRAJECTORY_BASELINE_MESSAGE,
    append_recurrence_trajectory_history,
    build_recurrence_trajectory_snapshot,
    empty_recurrence_trajectory_history,
    load_recurrence_trajectory_history,
    summarize_recurrence_trajectory,
    write_recurrence_trajectory_history,
)

pytestmark = pytest.mark.unit


def _sample_snapshot(*, index: int = 1, portfolio_risk: float = 44.1) -> dict:
    return {
        "snapshot_index": index,
        "timestamp": f"2026-06-2{index}T12:00:00Z",
        "artifact_source": "artifacts/golden_replay/bug_recurrence_history.json",
        "protected_observation_count": 11,
        "unique_recurrence_keys": 4,
        "regression_recurrence_rate": 0.25,
        "governance_health_score": 55.2,
        "lifecycle_health_score": 45.0,
        "portfolio_risk_score": portfolio_risk,
        "operational_readiness_score": 76.4,
        "effectiveness_score": 0.82,
        "maturity_score": 73.0,
        "stability_score": 75.0,
        "program_effectiveness_score": 41.3,
    }


def test_first_snapshot_creation_establishes_baseline_only_summary() -> None:
    history = append_recurrence_trajectory_history(
        empty_recurrence_trajectory_history(),
        _sample_snapshot(index=1),
    )
    summary = summarize_recurrence_trajectory(history)

    assert len(history["snapshots"]) == 1
    assert history["snapshots"][0]["snapshot_index"] == 1
    assert summary["trajectory_available"] is False
    assert summary["baseline_only"] is True
    assert summary["portfolio_risk_change"] == 0.0
    assert summary["message"] == RECURRENCE_TRAJECTORY_BASELINE_MESSAGE


def test_append_recurrence_trajectory_history_is_idempotent_for_duplicate_snapshot() -> None:
    first = append_recurrence_trajectory_history(
        empty_recurrence_trajectory_history(),
        _sample_snapshot(index=1),
    )
    second = append_recurrence_trajectory_history(first, _sample_snapshot(index=1))

    assert len(first["snapshots"]) == 1
    assert len(second["snapshots"]) == 1


def test_temporal_capture_appends_second_snapshot_with_same_metrics() -> None:
    history = append_recurrence_trajectory_history(
        empty_recurrence_trajectory_history(),
        _sample_snapshot(index=1),
    )
    follow_up = dict(_sample_snapshot(index=1))
    follow_up["timestamp"] = "2026-06-20T20:00:00Z"
    history = append_recurrence_trajectory_history(
        history,
        follow_up,
        temporal_capture=True,
    )

    assert len(history["snapshots"]) == 2
    assert history["snapshots"][1]["snapshot_index"] == 2
    assert history["snapshots"][1]["timestamp"] == "2026-06-20T20:00:00Z"


def test_second_snapshot_activates_trajectory_and_change_metrics() -> None:
    history = append_recurrence_trajectory_history(
        empty_recurrence_trajectory_history(),
        _sample_snapshot(index=1, portfolio_risk=44.1),
    )
    history = append_recurrence_trajectory_history(
        history,
        _sample_snapshot(index=2, portfolio_risk=52.0),
    )
    summary = summarize_recurrence_trajectory(history)

    assert len(history["snapshots"]) == 2
    assert summary["trajectory_available"] is True
    assert summary["portfolio_risk_change"] == pytest.approx(7.9)
    assert summary["portfolio_trajectory"]["direction"] == "regressing"
    assert summary["governance_trajectory"]["absolute_change"] == 0.0


def test_build_recurrence_trajectory_snapshot_serializes_core_fields() -> None:
    snapshot = build_recurrence_trajectory_snapshot(
        timestamp="2026-06-20T12:00:00Z",
        artifact_source="artifacts/golden_replay/bug_recurrence_history.json",
        recurrence_history={"unique_recurrence_count": 4, "total_rows": 11},
        recurrence_portfolio_summary={"total_observations": 11, "portfolio_risk_score": 44.1},
        recurrence_forecast_summary={"stability_score": 75.0},
        recurrence_governance_summary={"governance_health_score": 55.2},
        recurrence_lifecycle_summary={"lifecycle_health_score": 45.0},
        recurrence_program_effectiveness_summary={
            "effectiveness_confidence": 0.82,
            "program_effectiveness_score": 41.3,
        },
        recurrence_maturity_summary={
            "operational_readiness_score": 76.4,
            "overall_maturity_score": 73.0,
        },
    )

    assert snapshot["protected_observation_count"] == 11
    assert snapshot["unique_recurrence_keys"] == 4
    assert snapshot["portfolio_risk_score"] == 44.1
    assert snapshot["effectiveness_score"] == 0.82


def test_trajectory_history_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "recurrence_trajectory_history.json"
    history = append_recurrence_trajectory_history(
        empty_recurrence_trajectory_history(),
        _sample_snapshot(index=1),
    )
    write_recurrence_trajectory_history(history, path)
    loaded = load_recurrence_trajectory_history(path)

    assert loaded["schema_version"] == 1
    assert len(loaded["snapshots"]) == 1
    assert loaded["snapshots"][0]["unique_recurrence_keys"] == 4


def test_trajectory_markdown_renders_baseline_message() -> None:
    summary = summarize_recurrence_trajectory(
        append_recurrence_trajectory_history(
            empty_recurrence_trajectory_history(),
            _sample_snapshot(index=1),
        )
    )
    markdown = render_bug_recurrence_history_markdown(
        {
            "summary": [],
            "recurrence_trajectory_history": append_recurrence_trajectory_history(
                empty_recurrence_trajectory_history(),
                _sample_snapshot(index=1),
            ),
            "recurrence_trajectory_summary": summary,
        }
    )

    assert "## Recurrence Trajectory" in markdown
    assert RECURRENCE_TRAJECTORY_BASELINE_MESSAGE in markdown
    assert "Trajectory available: `false`" in markdown
