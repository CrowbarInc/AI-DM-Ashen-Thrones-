"""Tests for BP10 fallback remediation effectiveness tracking."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_remediation_effectiveness as EFFECTIVENESS

pytestmark = pytest.mark.unit


def _registry(*records: dict) -> dict:
    return {"schema_version": 1, "remediations": list(records)}


def _record(remediation_id: str = "rem-1") -> dict:
    return {
        "remediation_id": remediation_id,
        "contributor": "sealed",
        "dimension": "fallback_kind",
        "opened_timestamp": "2026-06-01T00:00:00Z",
        "closed_timestamp": "2026-06-02T00:00:00Z",
        "status": "completed",
    }


def _snapshot(day: int, score: float, recurrence: str = "persistent", anomalies: int = 1) -> dict:
    return {
        "timestamp": f"2026-06-{day:02d}T00:00:00Z",
        "contributors": [
            {
                "timestamp": f"2026-06-{day:02d}T00:00:00Z",
                "contributor": "sealed",
                "dimension": "fallback_kind",
                "score": score,
                "risk_classification": "high",
                "priority": "schedule",
                "recurrence": recurrence,
                "snapshot_appearances": day,
                "anomaly_count": anomalies,
            }
        ],
    }


def _history(*snapshots: dict) -> dict:
    return {"schema_version": 1, "snapshots": list(snapshots)}


def test_no_remediations() -> None:
    report = EFFECTIVENESS.build_remediation_effectiveness_report(
        EFFECTIVENESS.empty_registry(), _history(), {}
    )
    assert report["status"] == "no_remediations"
    assert report["remediations"] == []


def test_successful_improvement() -> None:
    history = _history(
        _snapshot(1, 80),
        _snapshot(2, 40, "transient", 0),
        _snapshot(3, 35, "transient", 0),
        _snapshot(4, 30, "transient", 0),
    )
    report = EFFECTIVENESS.build_remediation_effectiveness_report(_registry(_record()), history, {})
    row = report["remediations"][0]
    assert row["effectiveness_classification"] == "improved"
    assert row["absolute_risk_reduction"] == 50
    assert row["percentage_risk_reduction"] == pytest.approx(0.625)
    assert row["time_to_improvement_hours"] == 24
    assert row["sustained_improvement"] is True


def test_no_change() -> None:
    history = _history(_snapshot(1, 50), _snapshot(2, 48), _snapshot(3, 49))
    report = EFFECTIVENESS.build_remediation_effectiveness_report(_registry(_record()), history, {})
    row = report["remediations"][0]
    assert row["effectiveness_classification"] == "unchanged"
    assert row["delta_risk"] == -1


def test_regression() -> None:
    history = _history(
        _snapshot(1, 80),
        _snapshot(2, 40, "transient", 0),
        _snapshot(3, 75, "persistent", 1),
    )
    report = EFFECTIVENESS.build_remediation_effectiveness_report(_registry(_record()), history, {})
    row = report["remediations"][0]
    assert row["effectiveness_classification"] == "regressed"
    assert row["regression_evidence"]["risk_returned_after_closure"] is True
    assert row["regression_evidence"]["recurrence_returned_after_closure"] is True
    assert row["regression_evidence"]["anomaly_returned_after_closure"] is True


def test_deterministic_ordering() -> None:
    first_record = _record("rem-z")
    second_record = _record("rem-a")
    registry = _registry(first_record, second_record)
    history = _history(_snapshot(1, 50), _snapshot(2, 40))
    first = EFFECTIVENESS.build_remediation_effectiveness_report(registry, history, {})
    second = EFFECTIVENESS.build_remediation_effectiveness_report(deepcopy(registry), deepcopy(history), {})
    assert first == second
    assert [row["remediation_id"] for row in first["remediations"]] == ["rem-a", "rem-z"]
