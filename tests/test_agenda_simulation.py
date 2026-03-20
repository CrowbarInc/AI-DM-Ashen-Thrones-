"""Tests for deterministic agenda simulation layer in advance_world_tick."""
from __future__ import annotations

from game.world import (
    advance_world_tick,
    ensure_defaults,
    AGENDA_THRESHOLD_FLAG,
    AGENDA_THRESHOLD_OP_COMPLETE,
    PRESSURE_THRESHOLD_EVENT,
)


def _world(factions=None, npcs=None, projects=None, event_log=None):
    """Minimal world dict for testing."""
    w = {
        "factions": factions if factions is not None else [],
        "npcs": npcs if npcs is not None else [],
        "projects": projects if projects is not None else [],
        "event_log": event_log if event_log is not None else [],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ensure_defaults(w)
    return w


def test_faction_agenda_advances_over_ticks():
    """Faction agenda_progress increases deterministically each tick."""
    world = _world(factions=[
        {"id": "f1", "name": "Faction One", "pressure": 2, "agenda_progress": 0},
    ])
    result = advance_world_tick(world, {})
    assert world["factions"][0]["agenda_progress"] == 1

    advance_world_tick(world, {})
    assert world["factions"][0]["agenda_progress"] == 2

    advance_world_tick(world, {})
    assert world["factions"][0]["agenda_progress"] == 3


def test_pressure_threshold_fires_once_not_every_tick():
    """When pressure crosses PRESSURE_THRESHOLD_EVENT, event appended once; not on subsequent ticks."""
    world = _world(factions=[
        {"id": "f1", "name": "Faction One", "pressure": 2, "agenda_progress": 0},
    ])
    # Pressure 2 -> 3: crosses threshold (PRESSURE_THRESHOLD_EVENT=3)
    result = advance_world_tick(world, {})
    pressure_events = [e for e in result["events"] if e.get("type") == "faction_pressure"]
    assert len(pressure_events) == 1
    assert "pressure mounts" in pressure_events[0]["text"].lower()
    assert world["factions"][0]["pressure"] == 3

    # Pressure 3 -> 4: no new threshold cross. No new event.
    result = advance_world_tick(world, {})
    pressure_events = [e for e in result["events"] if e.get("type") == "faction_pressure"]
    assert len(pressure_events) == 0
    assert world["factions"][0]["pressure"] == 4

    # Another tick - still no new pressure event (already crossed 3)
    result = advance_world_tick(world, {})
    pressure_events = [e for e in result["events"] if e.get("type") == "faction_pressure"]
    assert len(pressure_events) == 0


def test_agenda_threshold_sets_flag_once():
    """When agenda_progress crosses AGENDA_THRESHOLD_FLAG, world flag set once."""
    world = _world(factions=[
        {"id": "f1", "name": "Faction One", "pressure": 0, "agenda_progress": 0},
    ])
    for _ in range(AGENDA_THRESHOLD_FLAG):
        advance_world_tick(world, {})
    assert world["world_state"]["flags"].get("faction_f1_agenda_advanced") is True
    assert world["factions"][0]["agenda_progress"] == AGENDA_THRESHOLD_FLAG

    # Next tick: flag already set, agenda continues
    advance_world_tick(world, {})
    assert world["world_state"]["flags"]["faction_f1_agenda_advanced"] is True
    assert world["factions"][0]["agenda_progress"] == AGENDA_THRESHOLD_FLAG + 1


def test_faction_operation_complete_fires_once():
    """When agenda_progress crosses AGENDA_THRESHOLD_OP_COMPLETE, event once."""
    world = _world(factions=[
        {"id": "f2", "name": "Faction Two", "pressure": 0, "agenda_progress": 0},
    ])
    for _ in range(AGENDA_THRESHOLD_OP_COMPLETE):
        result = advance_world_tick(world, {})
    op_events = [e for e in result["events"] if e.get("type") == "faction_operation_complete"]
    assert len(op_events) == 1
    assert "completes" in op_events[0]["text"].lower()

    # Further ticks: no duplicate operation_complete
    result = advance_world_tick(world, {})
    op_events = [e for e in result["events"] if e.get("type") == "faction_operation_complete"]
    assert len(op_events) == 0


def test_npc_moved_when_mobile_and_agenda_move_to():
    """NPC with availability=mobile and agenda_move_to_scene_id moves deterministically."""
    world = _world(npcs=[
        {
            "id": "runner",
            "name": "Runner",
            "location": "gate",
            "availability": "mobile",
            "agenda_move_to_scene_id": "market",
        },
    ])
    result = advance_world_tick(world, {})
    moved = [e for e in result["events"] if e.get("type") == "npc_moved"]
    assert len(moved) == 1
    assert moved[0]["npc_id"] == "runner"
    assert moved[0]["from_scene"] == "gate"
    assert moved[0]["to_scene"] == "market"
    assert world["npcs"][0]["location"] == "market"

    # Second tick: already at market, no move
    result = advance_world_tick(world, {})
    moved = [e for e in result["events"] if e.get("type") == "npc_moved"]
    assert len(moved) == 0


def test_npc_does_not_move_when_availability_not_mobile():
    """NPC with availability=available does not move even with agenda_move_to_scene_id."""
    world = _world(npcs=[
        {
            "id": "static",
            "name": "Static NPC",
            "location": "gate",
            "availability": "available",
            "agenda_move_to_scene_id": "market",
        },
    ])
    result = advance_world_tick(world, {})
    moved = [e for e in result["events"] if e.get("type") == "npc_moved"]
    assert len(moved) == 0
    assert world["npcs"][0]["location"] == "gate"


def test_project_progression_unchanged():
    """Project advancement behavior identical to pre-agenda code."""
    from game.projects import create_project
    world = _world()
    create_project(world, {"name": "Wall", "category": "infrastructure", "progress": 0, "target": 2})

    result = advance_world_tick(world, {})
    assert world["projects"][0]["progress"] == 1
    assert world["projects"][0]["status"] == "active"

    result = advance_world_tick(world, {})
    assert len([e for e in result["events"] if e.get("type") == "project_completed"]) == 1
    assert world["projects"][0]["progress"] == 2
    assert world["projects"][0]["status"] == "complete"

    result = advance_world_tick(world, {})
    assert len([e for e in result["events"] if e.get("type") == "project_completed"]) == 0


def test_return_shape_preserved():
    """advance_world_tick returns {events: [...], world: world}."""
    world = _world()
    result = advance_world_tick(world, {})
    assert "events" in result
    assert "world" in result
    assert isinstance(result["events"], list)
    assert result["world"] is world


def test_event_log_extended():
    """Generated events appended to world event_log."""
    world = _world(factions=[
        {"id": "f1", "name": "F1", "pressure": 2, "agenda_progress": 0},
    ])
    advance_world_tick(world, {})  # pressure 2 -> 3, crosses threshold
    assert len(world["event_log"]) >= 1
    assert any("pressure" in e.get("text", "").lower() for e in world["event_log"])
