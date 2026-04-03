"""Dialogue-lock → route/lane invariants without the full `/api/chat` stack.

Owns table-style contracts for `choose_interaction_route` / `is_directed_dialogue` under an
active social interlocutor. Full HTTP pipeline coverage stays in `test_turn_pipeline_shared.py`;
directed-address / vocative precedence stays in `test_directed_social_routing.py`.
"""
from __future__ import annotations

import pytest

from game.api import choose_interaction_route, is_directed_dialogue, is_world_action

pytestmark = pytest.mark.unit


# feature: routing
@pytest.mark.regression
def test_choose_interaction_route_dialogue_lock_pure_contract() -> None:
    """Pure routing table for dialogue lock (active runner, engaged social)."""
    scene = {"scene": {"id": "scene_investigate"}}
    world = {
        "npcs": [
            {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
            {"id": "captain_veyra", "name": "Captain Veyra", "location": "scene_investigate"},
        ]
    }
    session = {
        "interaction_context": {
            "active_interaction_target_id": "runner",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
        }
    }
    assert is_directed_dialogue(
        "Runner, do you know where I can find those figures?",
        scene=scene,
        session=session,
        world=world,
    )
    for text in (
        "Who attacked them?",
        "What are they planning?",
        "Who saw this happen?",
        "Tell me what you know.",
    ):
        assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"
    assert is_world_action("I search the crossroads for tracks.")
    assert (
        choose_interaction_route("I follow the runner.", scene=scene, session=session, world=world) == "action"
    )
    assert (
        choose_interaction_route("I grab him and demand answers.", scene=scene, session=session, world=world)
        == "action"
    )
    for text in (
        "Well? What should I do next?",
        "So what's the next step?",
        "Where does this lead?",
    ):
        assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"
    assert (
        choose_interaction_route(
            "OOC, what actions are available?",
            scene=scene,
            session=session,
            world=world,
        )
        != "dialogue"
    )
    assert (
        choose_interaction_route(
            "Mechanically, what can I roll here?",
            scene=scene,
            session=session,
            world=world,
        )
        != "dialogue"
    )
