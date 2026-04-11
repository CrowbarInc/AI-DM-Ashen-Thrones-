"""Objective 18a: explicit inspect/manipulate turns escape active-interlocutor dialogue lock."""
from __future__ import annotations

import pytest

from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
)
from game.interaction_routing import choose_interaction_route, is_directed_dialogue

pytestmark = pytest.mark.unit


def _scene():
    return {"scene": {"id": "scene_investigate"}}


def _world():
    return {
        "npcs": [
            {"id": "tavern_runner", "name": "Tavern Runner", "location": "scene_investigate"},
            {"id": "gate_guard", "name": "Gate Guard", "location": "scene_investigate"},
        ]
    }


def _session_engaged_runner():
    return {
        "active_scene_id": "scene_investigate",
        "visited_scene_ids": ["scene_investigate"],
        "interaction_context": {
            "active_interaction_target_id": "tavern_runner",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
        },
    }


def test_inspect_object_tied_to_npc_not_social_route():
    """Engaged social scene + inspect object referencing NPC - not dialogue/social lock."""
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "Galinor inspects the tavern runner's stew."
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is False
    assert out.get("reason") == "explicit_non_social_action_escapes_social_lock"
    assert out.get("continuity_escape_prior_target_actor_id") == "tavern_runner"


def test_look_around_scene_not_pure_dialogue_route():
    """Look around / scan area — coarse route is not dialogue when socially engaged."""
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    assert (
        choose_interaction_route(
            "I glance around the tavern for exits.",
            scene=scene,
            session=session,
            world=world,
        )
        != "dialogue"
    )


def test_search_nearby_not_pure_dialogue_route():
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    assert (
        choose_interaction_route(
            "I search the nearby area for footprints.",
            scene=scene,
            session=session,
            world=world,
        )
        != "dialogue"
    )


def test_pick_up_open_move_action_lane():
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    assert (
        choose_interaction_route(
            "I open the side door and step past the runner.",
            scene=scene,
            session=session,
            world=world,
        )
        == "action"
    )


def test_direct_question_to_active_npc_stays_dialogue():
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    text = "What's in the stew today?"
    assert (
        resolve_directed_social_entry(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=None,
            raw_text=text,
        ).get("should_route_social")
        is True
    )
    assert (
        is_directed_dialogue(
            text,
            scene=scene,
            session=session,
            world=world,
            canonical_social_entry=resolve_directed_social_entry(
                session=session,
                scene=scene,
                world=world,
                segmented_turn=None,
                raw_text=text,
            ),
        )
        is True
    )
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"


def test_i_ask_blocks_escape_hybrid_order():
    """Speech-led line: ask before inspect — dialogue intent blocks escape."""
    session = _session_engaged_runner()
    scene = _scene()
    world = _world()
    text = "I ask the runner about the road, then I inspect the pot."
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is True
