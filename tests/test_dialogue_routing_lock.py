from __future__ import annotations

from game.api import choose_interaction_route, is_directed_dialogue, is_world_action


def _scene():
    return {"scene": {"id": "scene_gate"}}


def _world():
    return {
        "npcs": [
            {"id": "runner", "name": "Tavern Runner", "location": "scene_gate"},
            {"id": "captain_veyra", "name": "Captain Veyra", "location": "scene_gate"},
        ]
    }


def _session(active_target: str | None = None):
    session = {"interaction_context": {}}
    if active_target:
        session["interaction_context"]["active_interaction_target_id"] = active_target
        session["interaction_context"]["active_interaction_kind"] = "social"
        session["interaction_context"]["interaction_mode"] = "social"
        session["interaction_context"]["engagement_level"] = "engaged"
    return session


def test_dialogue_lock_detects_npc_directed_information_questions():
    scene = _scene()
    world = _world()
    session = _session("runner")

    assert is_directed_dialogue(
        "Runner, do you know where I can find those figures?",
        scene=scene,
        session=session,
        world=world,
    )
    assert choose_interaction_route(
        "Who attacked them?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"
    assert choose_interaction_route(
        "What are they planning?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"


def test_dialogue_lock_ignores_vague_or_unknown_answerability():
    scene = _scene()
    world = _world()
    session = _session("runner")

    assert choose_interaction_route(
        "Who saw this happen?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"
    assert choose_interaction_route(
        "Tell me what you know.",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"


def test_world_action_detection_remains_active_for_forceful_actions():
    assert is_world_action("I search the crossroads for tracks.")
    assert choose_interaction_route(
        "I follow the runner.",
        scene=_scene(),
        session=_session("runner"),
        world=_world(),
    ) == "action"
    assert choose_interaction_route(
        "I grab him and demand answers.",
        scene=_scene(),
        session=_session("runner"),
        world=_world(),
    ) == "action"


def test_active_npc_ambiguous_followups_prefer_dialogue_route():
    scene = _scene()
    world = _world()
    session = _session("runner")

    assert choose_interaction_route(
        "Well? What should I do next?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"
    assert choose_interaction_route(
        "So what's the next step?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"
    assert choose_interaction_route(
        "Where does this lead?",
        scene=scene,
        session=session,
        world=world,
    ) == "dialogue"


def test_explicit_mechanical_or_ooc_markers_do_not_force_dialogue():
    scene = _scene()
    world = _world()
    session = _session("runner")

    assert choose_interaction_route(
        "OOC, what actions are available?",
        scene=scene,
        session=session,
        world=world,
    ) != "dialogue"
    assert choose_interaction_route(
        "Mechanically, what can I roll here?",
        scene=scene,
        session=session,
        world=world,
    ) != "dialogue"
