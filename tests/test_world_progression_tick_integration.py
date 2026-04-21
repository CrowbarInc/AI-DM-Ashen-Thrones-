"""Integration: world tick and update paths use ``game.world_progression`` for supported kinds."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from game import world_progression as wp
from game.world import (
    advance_world_tick,
    apply_resolution_world_updates,
    apply_world_updates,
    ensure_defaults,
)

pytestmark = pytest.mark.unit


def _minimal_world(**kwargs):
    w = {
        "factions": kwargs.get("factions", []),
        "npcs": kwargs.get("npcs", []),
        "projects": kwargs.get("projects", []),
        "event_log": kwargs.get("event_log", []),
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ensure_defaults(w)
    return w


def test_advance_world_tick_projects_and_factions_via_backbone():
    world = _minimal_world(
        projects=[
            {
                "id": "p1",
                "name": "Test",
                "category": "research",
                "status": "active",
                "progress": 0,
                "target": 3,
                "tags": [],
                "notes": "",
                "metadata": {},
            }
        ],
        factions=[{"id": "guild", "name": "Guild", "pressure": 0, "agenda_progress": 0}],
    )
    calls: list[str] = []
    orig = wp.advance_progression_node

    def _spy(w, node_id, amount=1, **kw):
        calls.append(str(node_id))
        return orig(w, node_id, amount, **kw)

    with patch.object(wp, "advance_progression_node", side_effect=_spy):
        advance_world_tick(world, {})

    assert "project:p1" in calls
    assert "faction_pressure:guild" in calls
    assert "faction_agenda:guild" in calls
    assert world["projects"][0]["progress"] == 1
    assert world["factions"][0]["pressure"] == 1
    assert world["factions"][0]["agenda_progress"] == 1


def test_advance_world_tick_threshold_events_once_and_no_duplicate_world_progression_in_log():
    world = _minimal_world(
        factions=[{"id": "f1", "name": "F1", "pressure": 2, "agenda_progress": 2}],
    )
    out = advance_world_tick(world, {})
    assert out["events"]
    pressure_hits = [e for e in out["events"] if e.get("type") == "faction_pressure"]
    assert len(pressure_hits) == 1
    assert world["world_state"]["flags"].get("faction_f1_agenda_advanced") is True
    wp_types = [e for e in world["event_log"] if e.get("type") == "world_progression"]
    assert wp_types == []


def test_duplicate_faction_uid_rows_still_advance_independently():
    """When progression uids collide, tick uses per-row advances (backbone cannot disambiguate)."""
    world = _minimal_world(
        factions=[
            {"pressure": 0, "agenda_progress": 0},
            {"pressure": 0, "agenda_progress": 0},
        ],
    )
    advance_world_tick(world, {})
    assert world["factions"][0]["pressure"] == 1
    assert world["factions"][1]["pressure"] == 1


def test_apply_resolution_routes_flags_and_clocks_through_delta():
    world = _minimal_world()
    with patch.object(wp, "apply_progression_delta", wraps=wp.apply_progression_delta) as spy:
        apply_resolution_world_updates(
            world,
            {
                "set_flags": {"probe": True},
                "advance_clocks": {"city": 2},
            },
        )
    assert spy.call_count == 2
    assert world["world_state"]["flags"].get("probe") is True
    assert world["world_state"]["clocks"]["city"]["value"] == 2


def test_apply_world_updates_flags_use_progression_delta():
    world = _minimal_world()
    with patch.object(wp, "apply_progression_delta", wraps=wp.apply_progression_delta) as spy:
        apply_world_updates(world, {"world_state": {"flags": {"gm": True}}})
    assert spy.called
    assert world["world_state"]["flags"].get("gm") is True


def test_malformed_project_row_skipped_without_error():
    world = _minimal_world(projects=["not-a-dict", None])
    advance_world_tick(world, {})
    assert world["projects"][0] == "not-a-dict"
