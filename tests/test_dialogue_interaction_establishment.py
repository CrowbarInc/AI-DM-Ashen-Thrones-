"""Interaction target establishment for freeform NPC dialogue (engine-owned)."""

from game.defaults import default_session, default_world
from game.interaction_context import (
    establish_dialogue_interaction_from_input,
    find_addressed_npc_id_for_turn,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.prompt_context import derive_narration_obligations
from game.social_exchange_emission import (
    player_line_triggers_strict_social_emission,
    reconcile_strict_social_resolution_speaker,
    resolve_strict_social_npc_target_id,
)
from game.storage import get_interaction_context


def _scene(gate_id: str = "gate") -> dict:
    return {"scene": {"id": gate_id}, "scene_state": {"active_entities": []}}


def test_empty_world_npcs_frontier_gate_binds_guard_aligns_strict_social():
    """When ``world['npcs']`` is empty, roster falls back like strict-social emission."""
    world: dict = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {
        "scene": {"id": "frontier_gate"},
        "scene_state": {"active_entities": []},
    }
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    line = "Captain, what happened to the missing patrol?"
    est = establish_dialogue_interaction_from_input(session, world, scene, line)
    assert est["established"] is True
    assert est["target_id"] == "guard_captain"
    assert get_interaction_context(session)["active_interaction_target_id"] == "guard_captain"
    assert player_line_triggers_strict_social_emission(line, session, world, "frontier_gate") is True


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


def test_comma_vocative_overrides_prior_active_interlocutor_for_binding_and_emission():
    """Explicit ``Runner, …`` must switch active_interaction_target_id and strict-social speaker."""
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
    set_social_target(session, "guard_captain")

    line = "Runner, what do you know about the patrol?"
    est = establish_dialogue_interaction_from_input(session, world, scene, line)
    assert est["established"] is True
    assert est["target_id"] == "tavern_runner"
    assert get_interaction_context(session)["active_interaction_target_id"] == "tavern_runner"

    tid, basis = resolve_strict_social_npc_target_id(session, world, "gate", line)
    assert tid == "tavern_runner"
    assert basis == "vocative"

    res = {
        "kind": "question",
        "prompt": line,
        "social": {
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "social_intent_class": "social_exchange",
        },
    }
    out = reconcile_strict_social_resolution_speaker(res, session, world, "gate")
    assert out["social"]["npc_id"] == "tavern_runner"


def test_generic_you_stranger_overrides_active_guard_for_binding_and_strict_social():
    """``you, stranger`` must rebind off the prior interlocutor (not pronoun ``you`` continuity)."""
    world = default_world()
    world["npcs"] = [
        {"id": "gate_guard", "name": "Gate Guard", "location": "gate", "role": "guard", "topics": []},
        {"id": "ragged_stranger", "name": "Ragged Stranger", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_entities"] = ["gate_guard", "ragged_stranger"]
    scene = {
        "scene": {"id": "gate"},
        "scene_state": {"active_entities": ["gate_guard", "ragged_stranger"]},
    }
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)
    set_social_target(session, "gate_guard")

    line = "You, stranger, have you heard any good rumors of late?"
    est = establish_dialogue_interaction_from_input(session, world, scene, line)
    assert est["established"] is True
    assert est["target_id"] == "ragged_stranger"
    assert get_interaction_context(session)["active_interaction_target_id"] == "ragged_stranger"

    tid, basis = resolve_strict_social_npc_target_id(session, world, "gate", line)
    assert tid == "ragged_stranger"
    assert basis == "generic_address"

    res = {
        "kind": "question",
        "prompt": line,
        "social": {
            "npc_id": "gate_guard",
            "npc_name": "Gate Guard",
            "social_intent_class": "social_exchange",
        },
    }
    out = reconcile_strict_social_resolution_speaker(res, session, world, "gate")
    assert out["social"]["npc_id"] == "ragged_stranger"


def test_generic_to_the_guard_redirects_from_prior_stranger_target():
    world = default_world()
    world["npcs"] = [
        {"id": "gate_guard", "name": "Gate Guard", "location": "gate", "role": "guard", "topics": []},
        {"id": "ragged_stranger", "name": "Ragged Stranger", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_entities"] = ["gate_guard", "ragged_stranger"]
    scene = {
        "scene": {"id": "gate"},
        "scene_state": {"active_entities": ["gate_guard", "ragged_stranger"]},
    }
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)
    set_social_target(session, "ragged_stranger")

    line = "I look back at him, then to the guard — any word on the patrol?"
    est = establish_dialogue_interaction_from_input(session, world, scene, line)
    assert est["established"] is True
    assert est["target_id"] == "gate_guard"


def test_generic_refugee_redirect_overrides_active_guard():
    world = default_world()
    world["npcs"] = [
        {"id": "gate_guard", "name": "Gate Guard", "location": "gate", "role": "guard", "topics": []},
        {"id": "tired_refugee", "name": "Tired Refugee", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_entities"] = ["gate_guard", "tired_refugee"]
    scene = {
        "scene": {"id": "gate"},
        "scene_state": {"active_entities": ["gate_guard", "tired_refugee"]},
    }
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)
    set_social_target(session, "gate_guard")

    line = "You, refugee, is the gate still letting carts through?"
    est = establish_dialogue_interaction_from_input(session, world, scene, line)
    assert est["established"] is True
    assert est["target_id"] == "tired_refugee"


def test_no_explicit_generic_pronoun_you_keeps_active_interlocutor():
    world = default_world()
    world["npcs"] = [
        {"id": "gate_guard", "name": "Gate Guard", "location": "gate", "role": "guard", "topics": []},
        {"id": "ragged_stranger", "name": "Ragged Stranger", "location": "gate", "topics": []},
    ]
    session = default_session()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_entities"] = ["gate_guard", "ragged_stranger"]
    scene = {
        "scene": {"id": "gate"},
        "scene_state": {"active_entities": ["gate_guard", "ragged_stranger"]},
    }
    rebuild_active_scene_entities(session, world, "gate", scene_envelope=scene)
    set_social_target(session, "gate_guard")

    tid = find_addressed_npc_id_for_turn(
        "What about you — still holding the line?",
        session,
        world,
        scene,
    )
    assert tid == "gate_guard"


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
