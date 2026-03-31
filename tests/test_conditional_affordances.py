"""Tests for conditional affordance filtering: requires_flags, requires_clues, excludes_flags, consumed_action_ids."""
from __future__ import annotations

import pytest

from game.affordances import get_available_affordances, generate_scene_affordances
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime, mark_action_consumed


def _scene_with_actions(actions: list) -> dict:
    """Build a scene envelope with custom actions."""
    return {
        "scene": {
            "id": "test_scene",
            "location": "Test",
            "summary": "A test scene.",
            "mode": "exploration",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
            "actions": actions,
        }
    }


def _world(flags: dict | None = None) -> dict:
    """Build world with optional flags."""
    w = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    if flags:
        w["world_state"]["flags"] = dict(flags)
    return w


def test_no_condition_affordances_still_appear():
    """Affordances without conditions must appear unchanged."""
    scene = _scene_with_actions([
        {"id": "simple_action", "label": "Do something", "type": "custom", "prompt": "I do something."},
    ])
    session = {"scene_runtime": {}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "simple_action" in ids
    assert "observe_the_area" in ids  # generated baseline


def test_requires_flags_filters_out_when_missing():
    """requires_flags: affordance hidden when any required flag is not set."""
    scene = _scene_with_actions([
        {
            "id": "needs_flag",
            "label": "Confront the watcher",
            "type": "interact",
            "prompt": "I confront them.",
            "conditions": {"requires_flags": ["met_well_dressed_woman"]},
        },
    ])
    session = {"scene_runtime": {}}
    world = _world()  # no flags
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "needs_flag" not in ids


def test_requires_flags_shows_when_all_set():
    """requires_flags: affordance shown when all required flags are truthy."""
    scene = _scene_with_actions([
        {
            "id": "needs_flag",
            "label": "Confront the watcher",
            "type": "interact",
            "prompt": "I confront them.",
            "conditions": {"requires_flags": ["met_well_dressed_woman"]},
        },
    ])
    session = {"scene_runtime": {}}
    world = _world({"met_well_dressed_woman": True})
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "needs_flag" in ids


def test_requires_clues_filters_out_when_missing():
    """requires_clues: affordance hidden when any required clue not discovered."""
    scene = _scene_with_actions([
        {
            "id": "needs_clue",
            "label": "Travel to the Crossroads",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "prompt": "I go to the crossroads.",
            "conditions": {"requires_clues": ["patrol_route_learned"]},
        },
    ])
    session = {"scene_runtime": {"test_scene": {"discovered_clues": [], "discovered_clue_ids": []}}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "needs_clue" not in ids


def test_requires_clues_shows_when_all_discovered():
    """requires_clues: affordance shown when all required clues are discovered (by id or text)."""
    scene = _scene_with_actions([
        {
            "id": "needs_clue",
            "label": "Travel to the Crossroads",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "prompt": "I go to the crossroads.",
            "conditions": {"requires_clues": ["patrol_route_learned"]},
        },
    ])
    session = {
        "scene_runtime": {
            "test_scene": {"discovered_clues": [], "discovered_clue_ids": ["patrol_route_learned"]},
        },
    }
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "needs_clue" in ids


def test_requires_clues_matches_text():
    """requires_clues: can match by discovered_clues text as well as id."""
    scene = _scene_with_actions([
        {
            "id": "needs_clue_text",
            "label": "Follow the lead",
            "type": "custom",
            "prompt": "I follow.",
            "conditions": {"requires_clues": ["A map indicates the locations of recent disturbances."]},
        },
    ])
    session = {
        "scene_runtime": {
            "test_scene": {
                "discovered_clues": ["A map indicates the locations of recent disturbances."],
                "discovered_clue_ids": [],
            },
        },
    }
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "needs_clue_text" in ids


def test_excludes_flags_hides_when_any_set():
    """excludes_flags: affordance hidden when any excluded flag is truthy."""
    scene = _scene_with_actions([
        {
            "id": "no_watcher_fled",
            "label": "Confront the watcher",
            "type": "interact",
            "prompt": "I confront them.",
            "conditions": {"excludes_flags": ["watcher_fled"]},
        },
    ])
    session = {"scene_runtime": {}}
    world = _world({"watcher_fled": True})
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "no_watcher_fled" not in ids


def test_excludes_flags_shows_when_none_set():
    """excludes_flags: affordance shown when no excluded flag is set."""
    scene = _scene_with_actions([
        {
            "id": "no_watcher_fled",
            "label": "Confront the watcher",
            "type": "interact",
            "prompt": "I confront them.",
            "conditions": {"excludes_flags": ["watcher_fled"]},
        },
    ])
    session = {"scene_runtime": {}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "no_watcher_fled" in ids


def test_excludes_clues_hides_when_discovered():
    """excludes_clues: affordance hidden when any excluded clue is discovered."""
    scene = _scene_with_actions([
        {
            "id": "scan-for-details",
            "label": "Scan for details",
            "type": "observe",
            "prompt": "I scan.",
            "conditions": {"excludes_clues": ["patrol_route_learned"]},
        },
    ])
    session = {
        "scene_runtime": {
            "test_scene": {"discovered_clues": [], "discovered_clue_ids": ["patrol_route_learned"]},
        },
    }
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "scan-for-details" not in ids


def test_excludes_clues_shows_when_not_discovered():
    """excludes_clues: affordance shown when no excluded clue is discovered."""
    scene = _scene_with_actions([
        {
            "id": "scan-for-details",
            "label": "Scan for details",
            "type": "observe",
            "prompt": "I scan.",
            "conditions": {"excludes_clues": ["patrol_route_learned"]},
        },
    ])
    session = {"scene_runtime": {"test_scene": {"discovered_clues": [], "discovered_clue_ids": []}}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "scan-for-details" in ids


def test_consumed_action_ids_hide_actions():
    """Actions in consumed_action_ids are filtered out."""
    scene = _scene_with_actions([
        {"id": "one_time_action", "label": "Use the device", "type": "custom", "prompt": "I use it."},
    ])
    session = {"scene_runtime": {"test_scene": {"consumed_action_ids": ["one_time_action"]}}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "one_time_action" not in ids


def test_global_clue_discovery():
    """requires_clues matches clues discovered in other scenes (global aggregation)."""
    scene = _scene_with_actions([
        {
            "id": "global_clue_action",
            "label": "Act on clue",
            "type": "custom",
            "prompt": "I act.",
            "conditions": {"requires_clues": ["clue_from_other_scene"]},
        },
    ])
    session = {
        "scene_runtime": {
            "other_scene": {"discovered_clues": [], "discovered_clue_ids": ["clue_from_other_scene"]},
            "test_scene": {"discovered_clues": [], "discovered_clue_ids": []},
        },
    }
    world = _world()
    affs = get_available_affordances(scene, session, world)
    ids = [a["id"] for a in affs]
    assert "global_clue_action" in ids


def test_normalize_preserves_conditions():
    """normalize_scene_action preserves conditions dict."""
    raw = {
        "id": "test",
        "label": "Test",
        "type": "interact",
        "conditions": {
            "requires_flags": ["a", "b"],
            "requires_clues": ["c"],
            "excludes_flags": ["d"],
        },
    }
    out = normalize_scene_action(raw)
    assert "conditions" in out
    assert out["conditions"]["requires_flags"] == ["a", "b"]
    assert out["conditions"]["requires_clues"] == ["c"]
    assert out["conditions"]["excludes_flags"] == ["d"]


def test_normalize_preserves_follow_lead_commitment_metadata():
    """normalize_scene_action passes through follow-lead commitment metadata unchanged."""
    raw = {
        "id": "follow-lead-bootprints-toward-the-river",
        "label": "Follow lead: Bootprints toward the river.",
        "type": "scene_transition",
        "targetSceneId": "market_quarter",
        "prompt": "I follow the lead to market_quarter.",
        "metadata": {
            "authoritative_lead_id": "tracks_reg",
            "clue_id": "tracks",
            "commitment_source": "follow_lead_affordance",
            "commitment_strength": 1,
            "target_scene_id": "market_quarter",
            "lead_text": "Bootprints toward the river.",
        },
    }
    out = normalize_scene_action(raw)
    m = out.get("metadata") or {}
    assert m.get("authoritative_lead_id") == "tracks_reg"
    assert m.get("clue_id") == "tracks"
    assert m.get("commitment_source") == "follow_lead_affordance"
    assert m.get("commitment_strength") == 1
    assert m.get("target_scene_id") == "market_quarter"
    assert "Bootprints" in (m.get("lead_text") or "")


def test_backward_compat_scenes_without_conditions():
    """Scenes without any conditions in actions work unchanged."""
    scene = _scene_with_actions([
        {"id": "legacy", "label": "Legacy action", "prompt": "I do it."},
    ])
    session = {"scene_runtime": {}}
    world = _world()
    affs = get_available_affordances(scene, session, world)
    assert any(a["id"] == "legacy" for a in affs)
