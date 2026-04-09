"""Observation-style scene questions must not route as social dialogue without an addressee."""
from __future__ import annotations

import pytest

from game.api import choose_interaction_route, is_directed_dialogue
from game.defaults import default_scene, default_session, default_world
from game.interaction_context import _looks_like_local_observation_question, resolve_directed_social_entry
from game.intent_parser import parse_freeform_to_action
from game.response_type_gating import derive_response_type_contract

pytestmark = pytest.mark.unit


def _scene_world_session(*, with_npcs: bool = True):
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    world = default_world()
    if with_npcs:
        world["npcs"] = [
            {
                "id": "runner",
                "name": "Tavern Runner",
                "location": "scene_investigate",
                "topics": [],
            },
            {
                "id": "gate_guard",
                "name": "Gate Guard",
                "location": "scene_investigate",
                "topics": [],
            },
        ]
    else:
        world["npcs"] = []
    return scene, session, world


def test_looks_like_local_observation_positive_examples() -> None:
    assert _looks_like_local_observation_question("What does he see?")
    assert _looks_like_local_observation_question("What do I see?")
    assert _looks_like_local_observation_question("What stands out?")
    assert _looks_like_local_observation_question("What is happening here?")
    assert _looks_like_local_observation_question(
        "Galinor watches the city. What does he notice?"
    )
    assert _looks_like_local_observation_question(
        "From the entryway, what can he make out?"
    )
    assert _looks_like_local_observation_question("What do I see from here?")


def test_looks_like_local_observation_negative_examples() -> None:
    assert not _looks_like_local_observation_question("What does the guard see?")
    assert not _looks_like_local_observation_question("What does the town crier know?")
    assert not _looks_like_local_observation_question(
        "Who here wants to speak with me?"
    )
    assert not _looks_like_local_observation_question(
        "What do people know about the missing patrol?"
    )
    assert not _looks_like_local_observation_question(
        "What happened at the old milestone?"
    )
    assert not _looks_like_local_observation_question(
        "Who wants to speak with Cinderwatch's newest hero?"
    )


def test_resolve_directed_social_entry_local_observation_returns_early() -> None:
    scene, session, world = _scene_world_session()
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="What does he see?",
    )
    assert out["should_route_social"] is False
    assert out["reason"] == "local_scene_observation_query"


def test_resolve_directed_social_entry_named_npc_perception_still_social_when_resolved() -> None:
    """Named addressee + perception verb stays social when the engine resolves the target."""
    scene, session, world = _scene_world_session()
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="What does Tavern Runner see?",
    )
    assert out["should_route_social"] is True
    assert out.get("target_actor_id") == "runner"


def test_is_directed_dialogue_not_for_bare_observation_with_npcs_present() -> None:
    scene, session, world = _scene_world_session()
    ce = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="What does he see?",
    )
    assert is_directed_dialogue(
        "What does he see?",
        scene=scene,
        session=session,
        world=world,
        canonical_social_entry=ce,
    ) is False


def test_choose_interaction_route_not_dialogue_for_local_observation() -> None:
    scene, session, world = _scene_world_session()
    ce = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="What does he see?",
    )
    assert (
        choose_interaction_route(
            "What does he see?",
            scene=scene,
            session=session,
            world=world,
            canonical_social_entry=ce,
        )
        != "dialogue"
    )


def test_parse_freeform_to_action_observe_lane_for_local_observation() -> None:
    scene, session, world = _scene_world_session()
    act = parse_freeform_to_action(
        "Galinor scans the crowd. What stands out?",
        scene,
        session=session,
        world=world,
    )
    assert act is not None
    assert act.get("type") == "observe"
    assert (act.get("metadata") or {}).get("parser_lane") == "local_observation_question"


def test_response_contract_observe_is_not_social_question_guard() -> None:
    contract = derive_response_type_contract(
        segmented_turn=None,
        normalized_action={"type": "observe", "prompt": "What do I see from here?"},
        resolution={"kind": "observe", "prompt": "What do I see from here?"},
        interaction_context={"interaction_mode": "none"},
        route_choice="action",
        directed_social_entry=None,
        raw_player_text="What do I see from here?",
    ).to_dict()
    assert contract["source_route"] == "exploration"
    assert "social_question_guard" not in contract["debug_reasons"]
