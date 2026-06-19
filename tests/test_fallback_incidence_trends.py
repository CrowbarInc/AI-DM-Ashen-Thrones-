"""Tests for BP5 append-only fallback incidence trend reporting."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fallback_incidence_trends.py"
SPEC = importlib.util.spec_from_file_location("fallback_incidence_trends_tool", TOOL)
assert SPEC and SPEC.loader
TRENDS = importlib.util.module_from_spec(SPEC)
sys.modules["fallback_incidence_trends_tool"] = TRENDS
SPEC.loader.exec_module(TRENDS)


def _report(*, rate: float, turns: int, events: int, kind_counts: dict[str, int] | None = None) -> dict:
    eligible = 100
    return {
        "eligible_turn_count": eligible,
        "fallback_turn_count": turns,
        "fallback_event_count": events,
        "fallback_trigger_rate": rate,
        "route_turn_count": {"social": 40, "action": 60},
        "route_fallback_turn_count": {"social": turns, "action": 0},
        "route_fallback_trigger_rate": {"social": turns / 40, "action": 0.0},
        "frequency": {
            "fallback_kind": kind_counts or {},
            "fallback_owner_bucket": {"sealed-gate": events} if events else {},
            "fallback_selection_owner": {"game.final_emission_gate": events} if events else {},
            "fallback_content_owner": {"game.final_emission_sealed_fallback": events} if events else {},
        },
    }


def _snapshot(index: int, *, rate: float, turns: int, events: int, kinds: dict[str, int] | None = None) -> dict:
    return TRENDS.snapshot_from_incidence_report(
        _report(rate=rate, turns=turns, events=events, kind_counts=kinds),
        timestamp=f"2026-06-{index:02d}T00:00:00Z",
        artifact_source=f"run-{index}.json",
    )


def test_first_snapshot_is_appended_and_has_insufficient_history(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    snapshot = _snapshot(1, rate=0.10, turns=10, events=12, kinds={"zeta": 2, "alpha": 2})
    history = TRENDS.append_snapshot_to_history(history_path, snapshot)
    analysis = TRENDS.analyze_fallback_incidence_history(history)

    assert history["snapshots"] == [snapshot]
    assert analysis["classification"] == "insufficient_history"
    assert analysis["change_since_previous"] is None
    assert history_path.is_file()


def test_multiple_snapshots_compute_previous_and_rolling_deltas() -> None:
    history = TRENDS.empty_history()
    for snapshot in (
        _snapshot(1, rate=0.10, turns=10, events=12),
        _snapshot(2, rate=0.20, turns=20, events=24),
        _snapshot(3, rate=0.15, turns=15, events=18),
    ):
        history = TRENDS.append_snapshot(history, snapshot)

    analysis = TRENDS.analyze_fallback_incidence_history(history)
    assert analysis["change_since_previous"] == {
        "delta_fallback_trigger_rate": pytest.approx(-0.05),
        "delta_fallback_event_count": -6,
        "delta_fallback_turn_count": -5,
    }
    assert analysis["rolling_history"]["prior_snapshot_count"] == 2
    assert analysis["rolling_history"]["average_fallback_trigger_rate"] == pytest.approx(0.15)
    assert analysis["rolling_history"]["delta_fallback_event_count"] == 0


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (0.10, 0.13, "worsening"),
        (0.13, 0.10, "improving"),
        (0.10, 0.109, "stable"),
    ],
)
def test_trigger_rate_classifications(previous: float, current: float, expected: str) -> None:
    history = {
        "schema_version": 1,
        "snapshots": [
            _snapshot(1, rate=previous, turns=10, events=10),
            _snapshot(2, rate=current, turns=11, events=11),
        ],
    }
    assert TRENDS.analyze_fallback_incidence_history(history)["classification"] == expected


def test_hotspots_and_routes_have_deterministic_ordering() -> None:
    first = _snapshot(1, rate=0.05, turns=5, events=5, kinds={"beta": 2, "alpha": 2})
    second = _snapshot(2, rate=0.10, turns=10, events=10, kinds={"beta": 3, "alpha": 3, "gamma": 4})
    analysis = TRENDS.analyze_fallback_incidence_history(
        {"schema_version": 1, "snapshots": [first, second]}
    )

    assert [row["name"] for row in second["top_fallback_kinds"]] == ["gamma", "alpha", "beta"]
    assert [row["name"] for row in analysis["hotspots"]["fallback_kinds"]] == ["gamma", "alpha", "beta"]
    assert [row["route_kind"] for row in analysis["route_trends"]] == ["action", "social"]


def test_append_only_persistence_preserves_existing_snapshot_bytes_semantically(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    first = _snapshot(1, rate=0.05, turns=5, events=6)
    second = _snapshot(2, rate=0.06, turns=6, events=7)
    TRENDS.append_snapshot_to_history(path, first)
    before = json.loads(path.read_text(encoding="utf-8"))["snapshots"]
    updated = TRENDS.append_snapshot_to_history(path, second)

    assert updated["snapshots"][:-1] == before
    assert updated["snapshots"][-1] == second


def test_empty_history_markdown_is_deterministic() -> None:
    analysis = TRENDS.analyze_fallback_incidence_history(TRENDS.empty_history())
    first = TRENDS.render_fallback_incidence_trends_markdown(analysis)
    second = TRENDS.render_fallback_incidence_trends_markdown(analysis)
    assert first == second
    assert "`insufficient_history`" in first
    assert "No fallback incidence snapshots have been recorded." in first
