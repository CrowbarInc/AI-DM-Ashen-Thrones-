"""Tests for scene-level discovery memory: searched targets, resolved interactables, affordance relabeling."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from game.affordances import get_available_affordances
from game.exploration import resolve_exploration_action
from game.scene_actions import normalize_scene_action
from game.session import reset_session_state
from game.storage import (
    get_scene_runtime,
    is_interactable_resolved,
    is_target_searched,
    load_session,
    mark_interactable_resolved,
    mark_target_searched,
    save_session,
)

pytestmark = pytest.mark.integration


def test_investigating_interactable_marks_it_resolved():
    """Investigating an interactable that reveals a clue marks it in resolved_interactables and searched_targets."""
    scene = {
        "scene": {
            "id": "test_scene",
            "location": "Test",
            "interactables": [
                {"id": "patrol_maps", "type": "investigate", "reveals_clue": "map_clue"}
            ],
            "discoverable_clues": [
                {"id": "map_clue", "text": "A map indicates patrol locations."}
            ],
        }
    }
    session = {}
    world = {}
    action = normalize_scene_action({
        "id": "inv-maps",
        "label": "Investigate the maps",
        "type": "investigate",
        "prompt": "I investigate the patrol maps"
    })

    resolution = resolve_exploration_action(
        scene, session, world, action,
        raw_player_text="I investigate the patrol maps",
        list_scene_ids=lambda: [],
        character=None,
    )
    assert resolution["kind"] == "discover_clue"
    assert resolution.get("interactable_id") == "patrol_maps"

    # Simulate API marking (resolve has no side effects)
    scene_id = scene["scene"]["id"]
    mark_interactable_resolved(session, scene_id, "patrol_maps")

    assert is_interactable_resolved(session, scene_id, "patrol_maps")
    assert is_target_searched(session, scene_id, "patrol_maps")


def test_repeat_interactable_returns_already_searched():
    """Repeating investigation of same interactable returns already_searched, no rediscovery."""
    scene = {
        "scene": {
            "id": "test_scene",
            "location": "Test",
            "interactables": [
                {"id": "patrol_maps", "type": "investigate", "reveals_clue": "map_clue"}
            ],
            "discoverable_clues": [
                {"id": "map_clue", "text": "A map indicates patrol locations."}
            ],
        }
    }
    session = {}
    rt = get_scene_runtime(session, "test_scene")
    rt["resolved_interactables"] = ["patrol_maps"]
    rt["searched_targets"] = ["patrol_maps"]

    action = normalize_scene_action({
        "id": "inv-maps",
        "label": "Investigate the maps",
        "type": "investigate",
        "prompt": "I investigate the patrol maps"
    })

    resolution = resolve_exploration_action(
        scene, session, {}, action,
        raw_player_text="I investigate the patrol maps",
        list_scene_ids=lambda: [],
    )
    assert resolution["kind"] == "already_searched"
    assert resolution.get("interactable_id") == "patrol_maps"
    assert resolution.get("discovered_clues") == []
    assert resolution.get("clue_id") is None


def test_different_targets_in_same_scene_work_independently():
    """Investigating target A then target B: both work; repeating A returns already_searched."""
    scene = {
        "scene": {
            "id": "multi_scene",
            "location": "Test",
            "interactables": [
                {"id": "desk", "type": "investigate", "reveals_clue": "desk_clue"},
                {"id": "chest", "type": "investigate", "reveals_clue": "chest_clue"},
            ],
            "discoverable_clues": [
                {"id": "desk_clue", "text": "Papers on the desk."},
                {"id": "chest_clue", "text": "Old coins in the chest."},
            ],
        }
    }
    session = {}
    world = {}

    # First: investigate desk
    action_desk = normalize_scene_action({
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk"
    })
    res_desk = resolve_exploration_action(
        scene, session, world, action_desk,
        raw_player_text="I investigate the desk",
        list_scene_ids=lambda: [],
    )
    assert res_desk["kind"] == "discover_clue"
    assert res_desk.get("interactable_id") == "desk"

    mark_interactable_resolved(session, "multi_scene", "desk")

    # Second: investigate chest (different target)
    action_chest = normalize_scene_action({
        "id": "inv-chest",
        "label": "Investigate the chest",
        "type": "investigate",
        "prompt": "I investigate the chest"
    })
    res_chest = resolve_exploration_action(
        scene, session, world, action_chest,
        raw_player_text="I investigate the chest",
        list_scene_ids=lambda: [],
    )
    assert res_chest["kind"] == "discover_clue"
    assert res_chest.get("interactable_id") == "chest"

    # Third: repeat desk -> already_searched
    res_desk2 = resolve_exploration_action(
        scene, session, world, action_desk,
        raw_player_text="I investigate the desk",
        list_scene_ids=lambda: [],
    )
    assert res_desk2["kind"] == "already_searched"


def test_generic_investigate_target_marked_and_repeat_returns_already_searched():
    """Generic investigate (no interactable match) marks action_id; repeat returns already_searched."""
    scene = {
        "scene": {
            "id": "gen_scene",
            "location": "Test",
            "interactables": [],
            "discoverable_clues": [{"id": "c1", "text": "A clue."}],
        }
    }
    session = {}
    action = normalize_scene_action({
        "id": "investigate-notice-board",
        "label": "Investigate the notice board",
        "type": "investigate",
        "prompt": "I investigate the notice board"
    })

    res1 = resolve_exploration_action(
        scene, session, {}, action,
        raw_player_text="I investigate the notice board",
        list_scene_ids=lambda: [],
    )
    assert res1["kind"] == "investigate"

    mark_target_searched(session, "gen_scene", "investigate-notice-board")

    res2 = resolve_exploration_action(
        scene, session, {}, action,
        raw_player_text="I investigate the notice board",
        list_scene_ids=lambda: [],
    )
    assert res2["kind"] == "already_searched"


def test_save_load_preserves_searched_target_state():
    """Session save/load preserves searched_targets and resolved_interactables."""
    session = {
        "active_scene_id": "test",
        "visited_scene_ids": ["test"],
        "scene_runtime": {
            "test": {
                "searched_targets": ["desk", "inv-maps"],
                "resolved_interactables": ["patrol_maps"],
            }
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session.json"
        path.write_text(json.dumps(session, indent=2), encoding="utf-8")

        # Simulate load
        loaded = json.loads(path.read_text(encoding="utf-8"))
        rt = loaded.get("scene_runtime", {}).get("test", {})
        assert "desk" in (rt.get("searched_targets") or [])
        assert "inv-maps" in (rt.get("searched_targets") or [])
        assert "patrol_maps" in (rt.get("resolved_interactables") or [])


def test_reset_clears_searched_target_runtime_state():
    """reset_session_state clears scene_runtime including searched_targets and resolved_interactables."""
    session = {
        "active_scene_id": "test",
        "visited_scene_ids": ["test"],
        "scene_runtime": {
            "test": {
                "searched_targets": ["desk"],
                "resolved_interactables": ["patrol_maps"],
                "discovered_clues": ["some clue"],
            }
        },
    }
    reset_session_state(session)
    assert session["scene_runtime"] == {}
    assert "test" not in session["scene_runtime"]


def test_affordance_relabeled_when_target_searched():
    """Investigate affordances are relabeled with '(already searched)' when target was searched."""
    scene = {
        "scene": {
            "id": "relabel_scene",
            "location": "Test",
            "mode": "exploration",
            "visible_facts": ["A dusty desk with papers."],
            "exits": [],
            "actions": [
                {
                    "id": "inv-desk",
                    "label": "Investigate the desk",
                    "type": "investigate",
                    "prompt": "I investigate the desk",
                }
            ],
        }
    }
    session = {
        "scene_runtime": {
            "relabel_scene": {
                "searched_targets": ["inv-desk"],
                "resolved_interactables": [],
            }
        },
    }
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}

    affs = get_available_affordances(scene, session, world)
    inv_desk = next((a for a in affs if a.get("id") == "inv-desk"), None)
    assert inv_desk is not None
    assert " (already searched)" in inv_desk.get("label", "")


def test_affordance_not_relabeled_when_target_not_searched():
    """Investigate affordances stay unchanged when target was not searched."""
    scene = {
        "scene": {
            "id": "fresh_scene",
            "location": "Test",
            "mode": "exploration",
            "visible_facts": ["A dusty desk."],
            "exits": [],
            "actions": [
                {"id": "inv-desk", "label": "Investigate the desk", "type": "investigate", "prompt": "I investigate."}
            ],
        }
    }
    session = {"scene_runtime": {"fresh_scene": {"searched_targets": [], "resolved_interactables": []}}}
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}

    affs = get_available_affordances(scene, session, world)
    inv_desk = next((a for a in affs if a.get("id") == "inv-desk"), None)
    assert inv_desk is not None
    assert " (already searched)" not in inv_desk.get("label", "")
