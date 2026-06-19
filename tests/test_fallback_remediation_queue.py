"""Tests for BP9 advisory fallback remediation prioritization."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_remediation_queue as QUEUE

pytestmark = pytest.mark.unit


def _risk_row(
    name: str,
    *,
    score: float,
    recurrence: str = "persistent",
    appearances: int = 4,
    anomaly_count: int = 1,
) -> dict:
    return {
        "dimension": "fallback_kind",
        "name": name,
        "risk_score": score,
        "risk_classification": "high",
        "recurrence_evidence": {
            "classification": recurrence,
            "snapshot_appearances": appearances,
        },
        "anomaly_evidence": {"participation_count": anomaly_count},
        "trend_evidence": {"classification": "stable"},
    }


def _risk_report(*rows: dict) -> dict:
    return {"schema_version": 1, "ranked_hotspots": {"all": list(rows)}}


def _history_entry(name: str, *, score: float, priority: str) -> dict:
    return {
        "timestamp": "2026-06-01T00:00:00Z",
        "contributor": name,
        "dimension": "fallback_kind",
        "score": score,
        "risk_classification": "high",
        "priority": priority,
        "recurrence": "persistent",
        "snapshot_appearances": 3,
        "anomaly_count": 1,
    }


def _history(*entries: dict) -> dict:
    return {
        "schema_version": 1,
        "snapshots": [{"timestamp": "2026-06-01T00:00:00Z", "contributors": list(entries)}],
    }


def test_empty_history() -> None:
    report = QUEUE.build_remediation_queue(_risk_report(), QUEUE.empty_risk_history())
    assert report["status"] == "empty"
    assert report["queue"] == []


def test_promotion() -> None:
    history = _history(_history_entry("sealed", score=60, priority="schedule"))
    report = QUEUE.build_remediation_queue(_risk_report(_risk_row("sealed", score=70)), history)
    item = report["queue"][0]
    assert item["priority"] == "prioritize"
    assert item["transition"] == "promotion"
    assert item["promotion_signals"]
    assert report["promotions"] == [item]


def test_demotion() -> None:
    history = _history(_history_entry("sealed", score=85, priority="urgent"))
    report = QUEUE.build_remediation_queue(_risk_report(_risk_row("sealed", score=50)), history)
    item = report["queue"][0]
    assert item["priority"] == "schedule"
    assert item["transition"] == "demotion"
    assert item["demotion_signals"]
    assert report["demotions"] == [item]


def test_stable_queue_item() -> None:
    history = _history(_history_entry("sealed", score=48, priority="schedule"))
    report = QUEUE.build_remediation_queue(_risk_report(_risk_row("sealed", score=50)), history)
    item = report["queue"][0]
    assert item["priority"] == "schedule"
    assert item["transition"] == "stable"
    assert item["rolling_score_trend"] == "stable"
    assert report["stable_entries"] == [item]


def test_deterministic_ordering() -> None:
    history = _history(
        _history_entry("zeta", score=50, priority="schedule"),
        _history_entry("alpha", score=50, priority="schedule"),
    )
    risk = _risk_report(_risk_row("zeta", score=50), _risk_row("alpha", score=50))
    first = QUEUE.build_remediation_queue(risk, history)
    second = QUEUE.build_remediation_queue(deepcopy(risk), deepcopy(history))
    assert first == second
    assert [item["contributor"] for item in first["queue"]] == ["alpha", "zeta"]
