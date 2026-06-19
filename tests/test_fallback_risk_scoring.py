"""Tests for BP8 explainable structural fallback risk scoring."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_risk_scoring as RISK

pytestmark = pytest.mark.unit


def _snapshot(index: int, *, count: int = 1, rate: float = 0.10, name: str = "sealed") -> dict:
    return {
        "timestamp": f"2026-06-{index:02d}T00:00:00Z",
        "artifact_source": f"run-{index}.json",
        "eligible_turn_count": 100,
        "fallback_turn_count": int(rate * 100),
        "fallback_event_count": int(rate * 100),
        "fallback_trigger_rate": rate,
        "top_fallback_kinds": [{"name": name, "count": count}],
        "top_owner_buckets": [],
        "top_selection_owners": [],
        "top_content_owners": [],
        "top_diegetic_families": [],
        "top_realization_families": [],
        "route_rates": [],
    }


def _history(snapshots: list[dict]) -> dict:
    return {"schema_version": 1, "snapshots": snapshots}


def _kind(report: dict, name: str = "sealed") -> dict:
    return next(row for row in report["ranked_hotspots"]["fallback_kinds"] if row["name"] == name)


def test_no_history() -> None:
    report = RISK.analyze_fallback_risk(_history([]))
    assert report["status"] == "no_history"
    assert report["ranked_hotspots"]["all"] == []
    assert report["highest_risk_contributor"] is None


def test_low_risk() -> None:
    row = _kind(RISK.analyze_fallback_risk(_history([_snapshot(1)])))
    assert row["risk_score"] == 20.0
    assert row["risk_classification"] == "low"


def test_elevated_risk() -> None:
    snapshots = [_snapshot(index) for index in range(1, 5)]
    row = _kind(RISK.analyze_fallback_risk(_history(snapshots)))
    assert row["risk_score"] == 50.0
    assert row["risk_classification"] == "elevated"


def test_critical_risk() -> None:
    snapshots = [_snapshot(index) for index in range(1, 6)]
    snapshots.append(_snapshot(6, count=30, rate=0.40))
    row = _kind(RISK.analyze_fallback_risk(_history(snapshots)))
    assert row["risk_score"] >= 80.0
    assert row["risk_classification"] == "critical"
    assert row["anomaly_evidence"]["maximum_severity"] == "critical"
    assert row["trend_evidence"]["classification"] == "worsening"


def test_deterministic_ordering() -> None:
    snapshots = []
    for index in range(1, 4):
        snapshot = _snapshot(index, name="alpha")
        snapshot["top_fallback_kinds"].append({"name": "zeta", "count": 1})
        snapshots.append(snapshot)
    history = _history(snapshots)
    first = RISK.analyze_fallback_risk(history)
    second = RISK.analyze_fallback_risk(deepcopy(history))
    assert first == second
    assert [row["name"] for row in first["ranked_hotspots"]["fallback_kinds"]] == ["alpha", "zeta"]


def test_explainability_fields() -> None:
    row = _kind(RISK.analyze_fallback_risk(_history([_snapshot(1)])))
    assert set(row) >= {
        "contributing_factors",
        "incidence_evidence",
        "recurrence_evidence",
        "anomaly_evidence",
        "trend_evidence",
    }
    assert set(row["contributing_factors"]) == set(RISK.FACTOR_MAXIMUMS)
    assert sum(factor["points"] for factor in row["contributing_factors"].values()) == row["risk_score"]
