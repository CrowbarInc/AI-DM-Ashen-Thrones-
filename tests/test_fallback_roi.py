"""Tests for BP12 fallback engineering effort and ROI attribution."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_roi as ROI

pytestmark = pytest.mark.unit


def _entry(remediation_id: str, *, reduction: float = 20, status: str = "completed", observations: int = 5) -> dict:
    return {
        "remediation_id": remediation_id,
        "contributor": remediation_id,
        "dimension": "fallback_kind",
        "status": status,
        "effectiveness_classification": "improved",
        "absolute_risk_reduction": reduction,
        "evidence": {"risk_snapshot_count": observations},
    }


def _effectiveness(*entries: dict) -> dict:
    return {"schema_version": 1, "remediations": list(entries)}


def _effort(remediation_id: str, **fields) -> dict:
    return {"remediation_id": remediation_id, **fields}


def _registry(*rows: dict) -> dict:
    return {"schema_version": 1, "remediations": list(rows)}


def test_no_effort_data() -> None:
    report = ROI.build_fallback_roi_report(_effectiveness(_entry("one")), _registry())
    assert report["status"] == "no_effort_data"
    assert report["portfolio_roi"]["risk_points_removed_per_hour"] is None
    assert report["confidence"]["level"] == "low"


def test_partial_effort_data() -> None:
    report = ROI.build_fallback_roi_report(
        _effectiveness(_entry("one"), _entry("two")),
        _registry(_effort("one", actual_hours=10, owner="team-a")),
    )
    assert report["portfolio_roi"]["effort_tracked_count"] == 1
    assert report["confidence"]["effort_data_coverage"] == 0.5
    assert report["capacity_analysis"]["total_hours_invested"] == 10


def test_roi_calculations() -> None:
    report = ROI.build_fallback_roi_report(
        _effectiveness(_entry("one", reduction=20)),
        _registry(_effort("one", actual_hours=10, engineer_count=2, owner="team-a", remediation_type="gate")),
    )
    row = report["remediation_efficiency"][0]
    assert row["risk_points_removed_per_hour"] == 2
    assert row["hours_per_risk_point"] == 0.5
    assert row["remediation_efficiency"] == "high"
    assert report["forecasts"]["expected_risk_reduction_per_engineer_month"] == 320


def test_owner_comparisons() -> None:
    report = ROI.build_fallback_roi_report(
        _effectiveness(_entry("fast", reduction=20), _entry("slow", reduction=10)),
        _registry(
            _effort("fast", actual_hours=5, owner="fast-team"),
            _effort("slow", actual_hours=20, owner="slow-team"),
        ),
    )
    analysis = report["owner_analysis"]
    assert analysis["highest_efficiency_owners"][0]["owner"] == "fast-team"
    assert analysis["lowest_efficiency_owners"][0]["owner"] == "slow-team"
    assert analysis["highest_effort_consumers"][0]["owner"] == "slow-team"
    assert analysis["largest_risk_reducers"][0]["owner"] == "fast-team"


def test_estimate_variance() -> None:
    report = ROI.build_fallback_roi_report(
        _effectiveness(_entry("over"), _entry("under")),
        _registry(
            _effort("over", estimated_hours=8, actual_hours=10),
            _effort("under", estimated_hours=12, actual_hours=9),
        ),
    )
    accuracy = report["estimate_accuracy"]
    assert accuracy["average_estimate_variance_hours"] == -0.5
    assert accuracy["overrun_rate"] == 0.5
    assert accuracy["underrun_rate"] == 0.5


def test_deterministic_ordering() -> None:
    effectiveness = _effectiveness(_entry("zeta"), _entry("alpha"))
    registry = _registry(
        _effort("zeta", actual_hours=10, owner="same"),
        _effort("alpha", actual_hours=10, owner="same"),
    )
    first = ROI.build_fallback_roi_report(effectiveness, registry)
    second = ROI.build_fallback_roi_report(deepcopy(effectiveness), deepcopy(registry))
    assert first == second
    assert [row["remediation_id"] for row in first["remediation_efficiency"]] == ["alpha", "zeta"]
