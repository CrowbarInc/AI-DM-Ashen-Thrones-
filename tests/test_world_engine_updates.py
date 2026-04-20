"""Tests for engine-driven world_state updates: resolution world_updates, flag-gated affordances, exit conditions."""
from __future__ import annotations

import json

import pytest

from game.affordances import get_available_affordances
from game.exploration import resolve_exploration_action
from game.world import apply_resolution_world_updates



pytestmark = pytest.mark.unit

def _scene(id: str = "test", exits=None, actions=None, interactables=None) -> dict:
    return {
        "scene": {
            "id": id,
            "location": "Test",
            "summary": "A test.",
            "mode": "exploration",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": exits or [],
            "enemies": [],
            "actions": actions or [],
            "interactables": interactables or [],
        }
    }


def _world(flags=None) -> dict:
    w = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    if flags:
        w["world_state"]["flags"] = dict(flags)
    return w


def test_apply_resolution_world_updates_set_flags():
    """Resolution world_updates set_flags applies to world."""
    world = _world()
    apply_resolution_world_updates(world, {"set_flags": {"met_well_dressed_woman": True}})
    assert world["world_state"]["flags"]["met_well_dressed_woman"] is True


def test_apply_resolution_world_updates_increment_counters():
    """Resolution world_updates increment_counters adds to counters."""
    world = _world()
    apply_resolution_world_updates(world, {"increment_counters": {"rumors_heard": 2}})
    assert world["world_state"]["counters"]["rumors_heard"] == 2
    apply_resolution_world_updates(world, {"increment_counters": {"rumors_heard": 1}})
    assert world["world_state"]["counters"]["rumors_heard"] == 3


def test_apply_resolution_world_updates_advance_clocks():
    """Resolution world_updates advance_clocks advances canonical clock value."""
    world = _world()
    apply_resolution_world_updates(world, {"advance_clocks": {"city_tension": 2}})
    assert world["world_state"]["clocks"]["city_tension"]["value"] == 2
    apply_resolution_world_updates(world, {"advance_clocks": {"city_tension": 1}})
    assert world["world_state"]["clocks"]["city_tension"]["value"] == 3


def test_apply_resolution_world_updates_combined():
    """Resolution can combine set_flags, increment_counters, advance_clocks."""
    world = _world()
    apply_resolution_world_updates(world, {
        "set_flags": {"patrol_route_known": True},
        "increment_counters": {"clues_found": 1},
        "advance_clocks": {"danger": 1},
    })
    assert world["world_state"]["flags"]["patrol_route_known"] is True
    assert world["world_state"]["counters"]["clues_found"] == 1
    assert world["world_state"]["clocks"]["danger"]["value"] == 1


def test_resolution_returns_world_updates_from_interactable():
    """Resolving discover_clue from interactable with world_updates_on_discover returns world_updates."""
    scene = _scene("room")
    scene["scene"]["discoverable_clues"] = [{"id": "patrol_clue", "text": "The patrol route is known."}]
    scene["scene"]["interactables"] = [
        {"id": "maps", "type": "investigate", "reveals_clue": "patrol_clue", "world_updates_on_discover": {"set_flags": {"patrol_route_known": True}}},
    ]
    session = {}
    world = _world()
    normalized = {"id": "investigate-maps", "label": "Investigate the maps", "type": "investigate", "prompt": "I investigate the maps"}
    resolution = resolve_exploration_action(scene, session, world, normalized)
    assert resolution["kind"] == "discover_clue"
    assert "world_updates" in resolution
    assert resolution["world_updates"]["set_flags"]["patrol_route_known"] is True


def test_resolution_returns_world_updates_from_exit():
    """Resolving scene_transition through exit with world_updates_on_transition returns world_updates."""
    scene = _scene("gate")
    scene["scene"]["exits"] = [
        {"label": "Follow the patrol", "target_scene_id": "old_milestone", "world_updates_on_transition": {"set_flags": {"patrol_route_known": True}}},
    ]
    session = {}
    world = _world()
    normalized = {"id": "go-follow", "label": "Go: Follow the patrol", "type": "scene_transition", "prompt": "I follow the patrol", "targetSceneId": "old_milestone"}
    resolution = resolve_exploration_action(
        scene, session, world, normalized,
        list_scene_ids=lambda: ["gate", "old_milestone"],
    )
    assert resolution["kind"] == "scene_transition"
    assert resolution["resolved_transition"] is True
    assert "world_updates" in resolution
    assert resolution["world_updates"]["set_flags"]["patrol_route_known"] is True


def test_affordances_react_to_flags():
    """Affordance with requires_flags appears when flag set, hidden when not."""
    scene = _scene("room")
    scene["scene"]["actions"] = [
        {"id": "travel_crossroads", "label": "Travel to the Crossroads", "type": "scene_transition", "targetSceneId": "crossroads", "prompt": "I go.", "conditions": {"requires_flags": ["patrol_route_known"]}},
    ]
    session = {"scene_runtime": {}}
    world_no_flag = _world()
    affs_no_flag = get_available_affordances(scene, session, world_no_flag)
    ids_no = [a["id"] for a in affs_no_flag]
    assert "travel_crossroads" not in ids_no

    world_with_flag = _world({"patrol_route_known": True})
    affs_with_flag = get_available_affordances(scene, session, world_with_flag)
    ids_with = [a["id"] for a in affs_with_flag]
    assert "travel_crossroads" in ids_with


def test_exit_conditions_gate_transition():
    """Exit with conditions is filtered from affordances when conditions not met."""
    scene = _scene("gate")
    scene["scene"]["exits"] = [
        {"label": "Enter Cinderwatch", "target_scene_id": "market"},
        {"label": "Follow the patrol", "target_scene_id": "crossroads", "conditions": {"requires_flags": ["patrol_route_known"]}},
    ]
    session = {"scene_runtime": {}}
    world = _world()

    affs = get_available_affordances(scene, session, world, list_scene_ids_fn=lambda: ["gate", "market", "crossroads"])
    labels = [a["label"] for a in affs]
    assert any("Enter Cinderwatch" in l for l in labels)
    assert not any("Follow the patrol" in l for l in labels)

    world["world_state"]["flags"]["patrol_route_known"] = True
    affs2 = get_available_affordances(scene, session, world, list_scene_ids_fn=lambda: ["gate", "market", "crossroads"])
    labels2 = [a["label"] for a in affs2]
    assert any("Follow the patrol" in l for l in labels2)


def test_excludes_flags_hides_affordance():
    """Affordance with excludes_flags is hidden when flag set."""
    scene = _scene("room")
    scene["scene"]["actions"] = [
        {"id": "talk_watcher", "label": "Confront the watcher", "type": "interact", "prompt": "I confront.", "conditions": {"excludes_flags": ["watcher_fled"]}},
    ]
    session = {"scene_runtime": {}}

    world_ok = _world()
    affs = get_available_affordances(scene, session, world_ok)
    assert any(a["id"] == "talk_watcher" for a in affs)

    world_flag = _world({"watcher_fled": True})
    affs2 = get_available_affordances(scene, session, world_flag)
    assert not any(a["id"] == "talk_watcher" for a in affs2)
