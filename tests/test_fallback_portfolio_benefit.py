"""Tests for BP11 fallback portfolio engineering benefit analysis."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_portfolio_benefit as PORTFOLIO

pytestmark = pytest.mark.unit
AS_OF = "2026-06-19T00:00:00Z"


def _entry(
    remediation_id: str,
    *,
    status: str = "completed",
    outcome: str = "improved",
    reduction: float = 20,
    dimension: str = "fallback_kind",
    contributor: str = "sealed",
    observations: int = 5,
    sustained: bool = True,
) -> dict:
    return {
        "remediation_id": remediation_id,
        "contributor": contributor,
        "dimension": dimension,
        "opened_timestamp": "2026-05-01T00:00:00Z",
        "closed_timestamp": "2026-05-10T00:00:00Z" if status == "completed" else None,
        "status": status,
        "effectiveness_classification": outcome,
        "before_risk": 70,
        "completion_risk": 50 if status == "completed" else None,
        "current_risk": 70 - reduction,
        "absolute_risk_reduction": reduction,
        "sustained_improvement": sustained,
        "evidence": {"risk_snapshot_count": observations},
    }


def _report(*entries: dict) -> dict:
    return {"schema_version": 1, "remediations": list(entries)}


def test_empty_portfolio() -> None:
    report = PORTFOLIO.build_portfolio_benefit_report(_report(), as_of_timestamp=AS_OF)
    assert report["status"] == "empty_portfolio"
    assert report["portfolio_status"]["total_remediations"] == 0
    assert report["confidence"]["level"] == "low"


def test_mixed_outcomes() -> None:
    report = PORTFOLIO.build_portfolio_benefit_report(
        _report(
            _entry("resolved", outcome="resolved", reduction=50),
            _entry("improved", reduction=20, dimension="route_kind", contributor="social"),
            _entry("unchanged", outcome="unchanged", reduction=0, sustained=False),
            _entry("active", status="in_progress", outcome="unchanged", reduction=0, sustained=False),
            _entry("abandoned", status="abandoned", outcome="unchanged", reduction=0, sustained=False),
        ),
        as_of_timestamp=AS_OF,
    )
    assert report["portfolio_status"] == {
        "total_remediations": 5,
        "completed_remediations": 3,
        "active_remediations": 1,
        "abandoned_remediations": 1,
    }
    assert report["risk_reduction"]["cumulative_risk_reduction"] == 70
    assert report["risk_reduction"]["median_risk_reduction"] == 20
    assert report["engineering_yield"]["risk_points_removed"] == 70
    assert report["contributor_impact"]["routes"][0]["contributor"] == "social"


def test_regressions_reduce_net_benefit() -> None:
    report = PORTFOLIO.build_portfolio_benefit_report(
        _report(
            _entry("gain", reduction=20),
            _entry("loss", outcome="regressed", reduction=-10, sustained=False),
        ),
        as_of_timestamp=AS_OF,
    )
    assert report["risk_reduction"]["cumulative_risk_reduction"] == 10
    assert report["engineering_yield"]["risk_points_removed"] == 20
    assert report["engineering_yield"]["regression_rate"] == 0.5


@pytest.mark.parametrize(
    ("observations", "sustained", "expected"),
    [(1, False, "low"), (3, True, "medium"), (5, True, "high")],
)
def test_confidence_calculations(observations: int, sustained: bool, expected: str) -> None:
    report = PORTFOLIO.build_portfolio_benefit_report(
        _report(_entry("confidence", observations=observations, sustained=sustained)),
        as_of_timestamp=AS_OF,
    )
    assert report["confidence"]["level"] == expected


def test_deterministic_ordering() -> None:
    source = _report(
        _entry("zeta", reduction=20, contributor="zeta"),
        _entry("alpha", reduction=20, contributor="alpha"),
    )
    first = PORTFOLIO.build_portfolio_benefit_report(source, as_of_timestamp=AS_OF)
    second = PORTFOLIO.build_portfolio_benefit_report(deepcopy(source), as_of_timestamp=AS_OF)
    assert first == second
    assert [row["remediation_id"] for row in first["risk_reduction"]["largest_reductions"]] == ["alpha", "zeta"]
