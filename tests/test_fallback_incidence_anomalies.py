"""Tests for BP6 advisory fallback-incidence anomaly detection."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_incidence_anomalies as ANOMALIES

pytestmark = pytest.mark.unit


def _snapshot(index: int, *, rate: float = 0.10, turns: int = 10, events: int = 10) -> dict:
    return {
        "timestamp": f"2026-06-{index:02d}T00:00:00Z",
        "artifact_source": f"run-{index}.json",
        "eligible_turn_count": 100,
        "fallback_turn_count": turns,
        "fallback_event_count": events,
        "fallback_trigger_rate": rate,
        "top_fallback_kinds": [{"name": "sealed", "count": events}],
        "top_owner_buckets": [{"name": "gate", "count": events}],
        "top_selection_owners": [{"name": "selector", "count": events}],
        "top_content_owners": [{"name": "writer", "count": events}],
        "route_rates": [
            {
                "route_kind": "action",
                "eligible_turn_count": 50,
                "fallback_turn_count": turns,
                "fallback_trigger_rate": rate,
            }
        ],
    }


def _history(current: dict | None = None) -> dict:
    snapshots = [_snapshot(index) for index in range(1, 6)]
    snapshots.append(current or _snapshot(6))
    return {"schema_version": 1, "snapshots": snapshots}


def test_insufficient_history_suppresses_anomalies() -> None:
    report = ANOMALIES.analyze_fallback_incidence_anomalies(
        {"schema_version": 1, "snapshots": [_snapshot(index) for index in range(1, 5)]}
    )
    assert report["status"] == "insufficient_history"
    assert report["anomalies"] == []
    assert report["baseline"] == {}


def test_no_anomaly() -> None:
    report = ANOMALIES.analyze_fallback_incidence_anomalies(_history())
    assert report["status"] == "no_anomalies"
    assert report["severity"] == "none"
    assert report["stability"] == "stable + no anomalies"


@pytest.mark.parametrize(("rate", "direction"), [(0.30, "above"), (0.0, "below")])
def test_trigger_rate_spike_and_drop(rate: float, direction: str) -> None:
    report = ANOMALIES.analyze_fallback_incidence_anomalies(_history(_snapshot(6, rate=rate)))
    matches = [row for row in report["anomalies"] if row["category"] == "trigger_rate"]
    assert len(matches) == 1
    assert matches[0]["direction"] == direction


def test_owner_spike() -> None:
    current = _snapshot(6, events=30)
    current["top_owner_buckets"] = [{"name": "gate", "count": 30}]
    report = ANOMALIES.analyze_fallback_incidence_anomalies(_history(current))
    assert any(
        row["category"] == "owner_bucket" and row["name"] == "gate" and row["direction"] == "above"
        for row in report["anomalies"]
    )


def test_route_spike() -> None:
    current = _snapshot(6)
    current["route_rates"][0]["fallback_trigger_rate"] = 0.50
    report = ANOMALIES.analyze_fallback_incidence_anomalies(_history(current))
    assert any(row["category"] == "route" and row["name"] == "action" for row in report["anomalies"])


def test_deterministic_ordering() -> None:
    current = _snapshot(6, rate=0.40, turns=40, events=40)
    current["top_owner_buckets"] = [{"name": "zeta", "count": 20}, {"name": "alpha", "count": 20}]
    history = _history(current)
    first = ANOMALIES.analyze_fallback_incidence_anomalies(history)
    second = ANOMALIES.analyze_fallback_incidence_anomalies(deepcopy(history))
    assert first == second
    assert first["anomalies"] == sorted(
        first["anomalies"],
        key=lambda row: (
            ANOMALIES.SEVERITY_ORDER[row["severity"]],
            row["category"],
            row["metric"],
            row.get("name") or "",
            row["direction"],
        ),
    )
