"""Tests for BP7 fallback recurrence and persistence analysis."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tools import fallback_recurrence as RECURRENCE

pytestmark = pytest.mark.unit


def _snapshot(index: int, entities: dict[str, dict[str, int]]) -> dict:
    def rows(dimension: str) -> list[dict]:
        return [{"name": name, "count": count} for name, count in entities.get(dimension, {}).items()]

    routes = [
        {
            "route_kind": name,
            "eligible_turn_count": 10,
            "fallback_turn_count": count,
            "fallback_trigger_rate": count / 10,
        }
        for name, count in entities.get("route_kind", {}).items()
    ]
    return {
        "timestamp": f"2026-06-{index:02d}T00:00:00Z",
        "artifact_source": f"run-{index}.json",
        "eligible_turn_count": 100,
        "fallback_turn_count": 10,
        "fallback_event_count": 10,
        "fallback_trigger_rate": 0.10,
        "top_fallback_kinds": rows("fallback_kind"),
        "top_owner_buckets": rows("owner_bucket"),
        "top_selection_owners": rows("selection_owner"),
        "top_content_owners": rows("content_owner"),
        "top_diegetic_families": rows("diegetic_family"),
        "top_realization_families": rows("realization_family"),
        "route_rates": routes,
    }


def _analyze(entity_snapshots: list[dict[str, dict[str, int]]]) -> dict:
    return RECURRENCE.analyze_fallback_recurrence(
        {
            "schema_version": 1,
            "snapshots": [_snapshot(index, entities) for index, entities in enumerate(entity_snapshots, 1)],
        }
    )


def _entity(report: dict, dimension: str, name: str) -> dict:
    return next(row for row in report["entities"][dimension] if row["name"] == name)


def test_single_snapshot_entity_is_transient() -> None:
    report = _analyze([{"fallback_kind": {"sealed": 2}}])
    row = _entity(report, "fallback_kind", "sealed")
    assert row["classification"] == "transient"
    assert row["snapshot_appearances"] == 1
    assert row["consecutive_appearances"] == 1
    assert row["appearance_percentage"] == 1.0


def test_recurring_entity() -> None:
    report = _analyze(
        [
            {"route_kind": {"social": 1}},
            {},
            {"route_kind": {"social": 2}},
            {},
            {},
        ]
    )
    row = _entity(report, "route_kind", "social")
    assert row["classification"] == "recurring"
    assert row["consecutive_appearances"] == 1
    assert row["cumulative_incidence_contribution"] == 3


def test_persistent_entity() -> None:
    report = _analyze(
        [
            {"owner_bucket": {"gate": 1}},
            {"owner_bucket": {"gate": 2}},
            {},
            {},
        ]
    )
    row = _entity(report, "owner_bucket", "gate")
    assert row["classification"] == "persistent"
    assert row["appearance_percentage"] == 0.5
    assert row["consecutive_appearances"] == 2


def test_dominant_entity() -> None:
    report = _analyze(
        [
            {"diegetic_family": {"warded": 1}},
            {"diegetic_family": {"warded": 1}},
            {},
            {"diegetic_family": {"warded": 2}},
        ]
    )
    row = _entity(report, "diegetic_family", "warded")
    assert row["classification"] == "dominant"
    assert row in report["dominant_contributors"]


def test_deterministic_ordering() -> None:
    source = [
        {"fallback_kind": {"zeta": 2, "alpha": 2}},
        {"fallback_kind": {"alpha": 3, "zeta": 3}},
        {},
    ]
    first = _analyze(source)
    second = _analyze(deepcopy(source))
    assert first == second
    assert [row["name"] for row in first["entities"]["fallback_kind"]] == ["alpha", "zeta"]


def test_anomaly_integrates_with_transient_hotspot() -> None:
    source = [{}, {}, {}, {}, {}, {"fallback_kind": {"new_kind": 10}}]
    report = _analyze(source)
    assert "anomaly + transient hotspot: fallback_kind/new_kind" in report["integrated_signals"]
