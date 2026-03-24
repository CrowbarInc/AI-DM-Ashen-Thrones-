"""Interaction target establishment for freeform NPC dialogue (engine-owned)."""

from game.defaults import default_session, default_world
from game.interaction_context import (
    establish_dialogue_interaction_from_input,
    find_addressed_npc_id_for_turn,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.prompt_context import derive_narration_obligations
from game.social_exchange_emission import resolve_strict_social_npc_target_id
from game.storage import get_interaction_context


def _scene(gate_id: str = "gate") -> dict:
    return {"scene": {"id": gate_id}, "scene_state": {"active_entities": []}}


def test_you_there_sets_active_target_single_npc():
    world = default_world()
    world["npcs"] = [
        {"id": "rian", "name": "Rian", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    scene = _scene()
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)

    establish_dialogue_interaction_from_input(
        session,
        world,
        scene,
        "You there, what's your name?",
    )
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "rian"
    assert ctx["interaction_mode"] == "social"


def test_vocative_name_maintains_follow_up_who_question():
    world = default_world()
    world["npcs"] = [
        {"id": "rian", "name": "Rian", "location": "gate", "topics": []},
        {"id": "other", "name": "Other", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    scene = _scene()
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)

    establish_dialogue_interaction_from_input(session, world, scene, "Rian?")
    assert get_interaction_context(session)["active_interaction_target_id"] == "rian"

    tid = find_addressed_npc_id_for_turn(
        "Who attacked them?",
        session,
        world,
        scene,
    )
    assert tid == "rian"


def test_strict_social_resolution_prefers_active_over_substring():
    world = default_world()
    world["npcs"] = [
        {"id": "tavern_runner", "name": "Runner", "location": "gate", "topics": []},
        {"id": "guard_captain", "name": "Guard Captain", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_entities"] = ["tavern_runner", "guard_captain"]
    scene = _scene()
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)
    set_social_target(session, "tavern_runner")

    target_id, basis = resolve_strict_social_npc_target_id(
        session,
        world,
        "gate",
        "I press the guard about the patrol route.",
    )
    assert target_id == "tavern_runner"
    assert basis == "active"


def test_wait_idle_while_engaged_expects_npc_reply():
    session_view = {
        "turn_counter": 5,
        "visited_scene_count": 2,
        "active_interaction_target_id": "rian",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
    }
    obligations = derive_narration_obligations(
        session_view,
        resolution={"kind": "observe", "action_id": "wait"},
        intent={"labels": ["passive_pause", "observation"]},
        recent_log_for_prompt=[],
        scene_runtime={},
    )
    assert obligations["active_npc_reply_expected"] is True
