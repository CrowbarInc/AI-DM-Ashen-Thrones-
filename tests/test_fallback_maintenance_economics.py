"""Tests for BP13 fallback maintenance-economics integration."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_maintenance_economics as ECONOMICS

pytestmark = pytest.mark.unit


def _build(**overrides) -> dict:
    inputs = {
        "trends": {},
        "anomalies": {},
        "recurrence": {},
        "risk": {},
        "queue": {},
        "effectiveness": {},
        "portfolio": {},
        "roi": {},
    }
    inputs.update(overrides)
    return ECONOMICS.build_fallback_maintenance_economics(**inputs)


def _risk_row(name: str, score: float, group: str = "fallback_kinds") -> tuple[str, dict]:
    return group, {
        "dimension": "fallback_kind" if group == "fallback_kinds" else "owner_bucket",
        "name": name,
        "risk_score": score,
        "risk_classification": "high",
        "recurrence_evidence": {"classification": "persistent"},
        "anomaly_evidence": {"participation_count": 1},
    }


def _risk_report(*specs: tuple[str, dict]) -> dict:
    groups = {"all": [row for _, row in specs], "fallback_kinds": [], "owners": [], "routes": [], "families": []}
    for group, row in specs:
        groups[group].append(row)
    return {"status": "ok", "ranked_hotspots": groups}


def test_empty_history() -> None:
    report = _build()
    assert report["status"] == "insufficient_data"
    assert report["maintenance_burden"]["score"] == 0
    assert report["maintenance_burden"]["classification"] == "negligible"
    assert report["confidence"]["level"] == "low"


def test_low_confidence_portfolio() -> None:
    spec = _risk_row("sealed", 20)
    report = _build(
        risk=_risk_report(spec),
        recurrence={"snapshot_count": 1, "entities": {}},
        portfolio={"portfolio_status": {"total_remediations": 1}},
        roi={"confidence": {"effort_data_coverage": 0.0}},
    )
    assert report["confidence"]["level"] == "low"
    assert report["maintenance_burden"]["classification"] == "negligible"


def test_populated_portfolio() -> None:
    spec = _risk_row("sealed", 80)
    report = _build(
        trends={"classification": "worsening"},
        anomalies={"status": "anomalies_detected", "severity": "warning", "anomalies": [{"name": "sealed"}]},
        recurrence={
            "snapshot_count": 12,
            "entities": {"fallback_kind": [{"name": "sealed", "classification": "dominant"}]},
        },
        risk=_risk_report(spec),
        queue={"queue": [{"dimension": "fallback_kind", "contributor": "sealed", "risk_score": 80, "priority": "urgent"}]},
        effectiveness={"status": "ok"},
        portfolio={
            "status": "ok",
            "portfolio_status": {"total_remediations": 6},
            "risk_reduction": {"cumulative_risk_reduction": 40},
        },
        roi={
            "status": "ok",
            "confidence": {"effort_data_coverage": 0.9},
            "portfolio_roi": {"risk_points_removed_per_hour": 2.0, "remediation_efficiency": "high"},
            "capacity_analysis": {"total_hours_invested": 20},
        },
    )
    assert report["confidence"]["level"] == "high"
    assert report["cost_benefit"]["risk_removed_per_engineering_hour"] == 2.0
    assert report["cost_benefit"]["unresolved_risk_per_engineering_hour"] == 4.0
    assert report["risk_analysis"]["backlog_risk"] == 80
    assert report["maintenance_burden"]["score"] > 0


def test_hotspot_ranking() -> None:
    alpha = _risk_row("alpha", 40)
    zeta = _risk_row("zeta", 70)
    report = _build(risk=_risk_report(alpha, zeta))
    assert [row["contributor"] for row in report["structural_hotspots"]["fallback_kinds"]] == ["zeta", "alpha"]


def test_deterministic_ordering() -> None:
    risk = _risk_report(_risk_row("zeta", 50), _risk_row("alpha", 50))
    first = _build(risk=risk)
    second = _build(risk=deepcopy(risk))
    assert first == second
    assert [row["contributor"] for row in first["structural_hotspots"]["fallback_kinds"]] == ["alpha", "zeta"]
    summary = ECONOMICS.build_scorecard_summary(first)
    assert set(summary) >= {"maintenance_burden", "unresolved_risk", "roi", "recurring_hotspots", "confidence"}
