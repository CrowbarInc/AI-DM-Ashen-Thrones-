"""Tests for automatic affordance generation from scene objects and interactables."""
from __future__ import annotations

import pytest

from game.affordances import (
    ALREADY_SEARCHED_SUFFIX,
    generate_scene_affordances,
    get_available_affordances,
)
from game.scene_actions import normalize_scene_action



pytestmark = pytest.mark.integration

def _scene(overrides: dict | None = None) -> dict:
    """Build a scene envelope with optional overrides."""
    base = {
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
            "actions": [],
        }
    }
    if overrides:
        scene = base["scene"]
        for k, v in overrides.items():
            scene[k] = v
    return base


def _session(scene_id: str = "test_scene", **runtime_overrides) -> dict:
    """Build session with optional scene_runtime overrides."""
    rt = {
        "searched_targets": [],
        "resolved_interactables": [],
        "discovered_clues": [],
        "discovered_clue_ids": [],
    }
    rt.update(runtime_overrides)
    return {
        "scene_runtime": {scene_id: rt},
        "active_scene_id": scene_id,
    }


def _world() -> dict:
    return {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}


def test_objects_generate_investigation_affordances():
    """Scene.objects with type investigate generate investigation affordances."""
    scene = _scene({
        "objects": [
            {"id": "dusty_chest", "label": "Dusty chest", "type": "investigate"},
            {"id": "old_table", "type": "investigate"},  # label from id
        ],
    })
    session = _session()
    world = _world()

    affs = generate_scene_affordances(scene, "exploration", session)

    chest = next((a for a in affs if a.get("id") == "dusty_chest"), None)
    assert chest is not None
    assert chest.get("type") == "investigate"
    assert "Examine" in (chest.get("label") or "")
    assert "chest" in (chest.get("label") or "").lower()
    assert "prompt" in chest
    assert chest.get("targetEntityId") == "dusty_chest"

    table = next((a for a in affs if a.get("id") == "old_table"), None)
    assert table is not None
    assert table.get("type") == "investigate"
    assert "Examine" in (table.get("label") or "")


def test_interactables_generate_investigate_observe_interact():
    """Interactables generate affordances based on their type."""
    scene = _scene({
        "interactables": [
            {"id": "patrol_maps", "type": "investigate", "reveals_clue": "patrol_route"},
            {"id": "well_dressed_woman", "type": "interact", "label": "Well-dressed woman"},
            {"id": "shadowy_corner", "type": "observe"},
        ],
    })
    session = _session()
    world = _world()

    affs = generate_scene_affordances(scene, "exploration", session)

    maps_aff = next((a for a in affs if a.get("id") == "patrol_maps"), None)
    assert maps_aff is not None
    assert maps_aff.get("type") == "investigate"
    assert "Examine" in (maps_aff.get("label") or "")

    woman_aff = next((a for a in affs if a.get("id") == "well_dressed_woman"), None)
    assert woman_aff is not None
    assert woman_aff.get("type") == "interact"
    assert any((woman_aff.get("label") or "").startswith(v) for v in ("Talk to", "Approach"))
    assert "woman" in (woman_aff.get("label") or "").lower()

    corner_aff = next((a for a in affs if a.get("id") == "shadowy_corner"), None)
    assert corner_aff is not None
    assert corner_aff.get("type") == "observe"
    assert "Inspect" in (corner_aff.get("label") or "")


def test_manual_affordances_override_generated():
    """Manual scene.actions override auto-generated affordances with the same id."""
    scene = _scene({
        "interactables": [
            {"id": "patrol_maps", "type": "investigate", "reveals_clue": "patrol_route"},
        ],
        "actions": [
            {
                "id": "patrol_maps",
                "label": "Examine the patrol maps carefully",
                "type": "investigate",
                "prompt": "I examine the maps in detail.",
                "conditions": {"requires_flags": ["has_magnifying_glass"]},
            },
        ],
    })
    session = _session()
    world_with_flag = {"world_state": {"flags": {"has_magnifying_glass": True}, "counters": {}, "clocks": {}}}
    world_no_flag = _world()

    affs = get_available_affordances(scene, session, world_with_flag)
    maps_aff = next((a for a in affs if a.get("id") == "patrol_maps"), None)
    assert maps_aff is not None
    # Manual override: custom label and conditions
    assert maps_aff.get("label") == "Examine the patrol maps carefully"
    assert maps_aff.get("conditions", {}).get("requires_flags") == ["has_magnifying_glass"]

    # Should be filtered out when flag not set
    affs_no_flag = get_available_affordances(scene, session, world_no_flag)
    ids = [a.get("id") for a in affs_no_flag]
    assert "patrol_maps" not in ids  # condition fails


def test_manual_override_without_conditions_still_appears():
    """Manual override without conditions still appears (smoke test for override)."""
    scene = _scene({
        "interactables": [{"id": "foo", "type": "investigate"}],
        "actions": [
            {"id": "foo", "label": "Custom investigate foo", "type": "investigate", "prompt": "I check foo."},
        ],
    })
    session = _session()
    world = _world()

    affs = get_available_affordances(scene, session, world)
    foo_aff = next((a for a in affs if a.get("id") == "foo"), None)
    assert foo_aff is not None
    assert foo_aff.get("label") == "Custom investigate foo"


def test_searched_targets_relabel_investigation_affordances():
    """Investigate affordances are relabeled with '(already searched)' when target was searched."""
    scene = _scene({
        "interactables": [{"id": "desk", "type": "investigate", "label": "Desk"}],
    })
    session = _session("test_scene", searched_targets=["desk"])
    world = _world()

    affs = get_available_affordances(scene, session, world)
    desk_aff = next((a for a in affs if a.get("id") == "desk"), None)
    assert desk_aff is not None
    assert ALREADY_SEARCHED_SUFFIX in (desk_aff.get("label") or "")


def test_visible_facts_generate_single_non_redundant_default():
    """Visible facts should not generate both Observe and Investigate variants by default."""
    scene = _scene({
        "visible_facts": ["A dusty desk with papers."],
    })
    session = _session()
    world = _world()

    affs = generate_scene_affordances(scene, "exploration", session)

    fact_actions = [a for a in affs if "dusty desk with papers" in (a.get("prompt") or "").lower()]
    assert len(fact_actions) == 1
    assert fact_actions[0].get("type") == "investigate"
    assert (fact_actions[0].get("label") or "").startswith("Examine")


def test_affordances_serialize_correctly_for_frontend():
    """Generated affordances have the structured format expected by the UI."""
    scene = _scene({
        "objects": [{"id": "test_obj", "label": "Test object", "type": "investigate"}],
    })
    session = _session()
    world = _world()

    affs = get_available_affordances(scene, session, world)
    obj_aff = next((a for a in affs if a.get("id") == "test_obj"), None)
    assert obj_aff is not None

    # Required keys for engine / frontend
    required = {"id", "label", "type", "prompt", "targetSceneId", "targetEntityId", "targetLocationId"}
    for k in required:
        assert k in obj_aff, f"Missing key: {k}"
    assert obj_aff.get("id")
    assert obj_aff.get("label")
    assert obj_aff.get("type") in ("observe", "investigate", "interact", "scene_transition", "travel", "custom")
    assert obj_aff.get("prompt")

    # Normalize should not alter structure
    norm = normalize_scene_action(obj_aff)
    assert norm.get("id") == obj_aff.get("id")
    assert norm.get("label") == obj_aff.get("label")
    assert norm.get("type") == obj_aff.get("type")


def test_no_duplicate_ids_when_manual_and_generated_collide():
    """When manual and generated share an id, only one appears (manual wins)."""
    scene = _scene({
        "interactables": [{"id": "unique_id", "type": "investigate"}],
        "actions": [{"id": "unique_id", "label": "Manual action", "type": "investigate", "prompt": "Manual."}],
    })
    session = _session()
    world = _world()

    affs = get_available_affordances(scene, session, world)
    matches = [a for a in affs if a.get("id") == "unique_id"]
    assert len(matches) == 1
    assert matches[0].get("label") == "Manual action"


def test_duplicate_npc_talk_affordances_are_removed():
    """Auto-generated NPC question/talk affordances should appear only once per NPC."""
    scene = _scene()
    session = _session()
    world = {
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
        "npcs": [{"id": "lirael", "name": "Lirael", "location": "test_scene"}],
    }
    affs = get_available_affordances(scene, session, world)
    social = [a for a in affs if a.get("targetEntityId") == "lirael" and a.get("type") in ("question", "interact")]
    assert len(social) == 1
    assert social[0].get("label") == "Talk to Lirael"


def test_generated_labels_are_short_and_verb_first():
    """Generated defaults should use short player-intent labels."""
    scene = _scene({
        "visible_facts": [
            "A weathered notice board covered in old proclamations.",
            "A knot of whispering men linger near the stairs.",
        ],
        "exits": [{"label": "Cinderwatch Gate District", "target_scene_id": "cinderwatch_gate"}],
    })
    session = _session()
    world = _world()
    affs = get_available_affordances(scene, session, world, list_scene_ids_fn=lambda: ["test_scene", "cinderwatch_gate"])
    labels = [str(a.get("label") or "") for a in affs]
    verb_prefixes = ("Talk to", "Approach", "Examine", "Inspect", "Leave for", "Go to", "Observe")
    assert labels
    assert all(label.startswith(verb_prefixes) for label in labels)
    assert all(len(label) <= 60 for label in labels)


def test_affordances_capped_to_five():
    """Final affordance list should be pruned to at most five choices."""
    scene = _scene({
        "visible_facts": [f"Detail {i}" for i in range(8)],
        "objects": [{"id": f"obj_{i}", "type": "investigate"} for i in range(6)],
        "exits": [{"label": f"Exit {i}", "target_scene_id": f"scene_{i}"} for i in range(4)],
    })
    session = _session()
    world = _world()
    affs = get_available_affordances(
        scene,
        session,
        world,
        list_scene_ids_fn=lambda: ["test_scene"] + [f"scene_{i}" for i in range(4)],
    )
    assert len(affs) <= 5


def test_explicit_scene_authored_actions_preserved_unless_true_duplicate():
    """Scene-authored actions should survive pruning and dedupe unless they are obvious duplicates."""
    scene = _scene({
        "actions": [
            {"id": "talk_lirael_custom", "label": "Talk to Lirael", "type": "question", "prompt": "I talk to Lirael.", "targetEntityId": "lirael"},
            {"id": "inspect_board_custom", "label": "Examine the notice board", "type": "investigate", "prompt": "I examine the notice board."},
        ],
    })
    session = _session()
    world = {
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
        "npcs": [{"id": "lirael", "name": "Lirael", "location": "test_scene"}],
    }
    affs = get_available_affordances(scene, session, world)
    ids = [a.get("id") for a in affs]
    assert "talk_lirael_custom" in ids
    assert "inspect_board_custom" in ids
    # Auto-generated duplicate for Lirael should be suppressed by dedupe.
    assert len([a for a in affs if (a.get("targetEntityId") or "") == "lirael"]) == 1
