"""Authoritative emitted-speaker adoption into interaction state (Objective #21 block 2)."""
from __future__ import annotations

import pytest

from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities
from game.post_emission_speaker_adoption import apply_post_emission_speaker_adoption

pytestmark = pytest.mark.unit


def _scene_world():
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    world = default_world()
    world["npcs"] = [
        {"id": "tavern_runner", "name": "Tavern Runner", "location": "scene_investigate", "topics": []},
        {"id": "gate_guard", "name": "Gate Guard", "location": "scene_investigate", "topics": []},
    ]
    return scene, world


def _session_social(target_id: str) -> dict:
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    session["interaction_context"] = {
        "active_interaction_target_id": target_id,
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    return session


def test_guard_takeover_with_explicit_speech_adopts_guard():
    """A. Grounded guard takeover with explicit speech -> guard becomes current interlocutor."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {
        "player_facing_text": 'Gate Guard says, "Halt—papers, now."',
    }
    out = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    assert out.get("adopted") is True
    assert out.get("interlocutor_status") == "adopted"
    assert out.get("fallback_anchor_source") == "visible_speaker"
    assert out.get("npc_id") == "gate_guard"
    assert session["interaction_context"]["active_interaction_target_id"] == "gate_guard"
    assert (session.get("scene_state") or {}).get("current_interlocutor") == "gate_guard"


def test_anonymous_crowd_voice_does_not_steal_interlocutor():
    """B. Anonymous / generic crowd speaker must not become interlocutor."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {
        "player_facing_text": 'Someone in the crowd shouts, "Fire!" and panic ripples.',
    }
    out = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
    )
    assert out.get("interlocutor_status") == "none"
    assert session["interaction_context"]["active_interaction_target_id"] == "tavern_runner"


def test_mention_of_other_npc_does_not_switch_interlocutor():
    """C. Primary attributed speaker remains the interlocutor when another NPC is only mentioned."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {
        "player_facing_text": (
            'Tavern Runner jerks a thumb toward the gate. "Ask the gate guard—he runs the chalk line."'
        ),
    }
    apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
    )
    assert session["interaction_context"]["active_interaction_target_id"] == "tavern_runner"


def test_same_speaker_reply_keeps_interlocutor():
    """D. Normal continuation from the same attributed speaker does not thrash state."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {
        "player_facing_text": 'Tavern Runner leans in. "Same stew as yesterday; still hot."',
    }
    out = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
    )
    assert out.get("adopted") is False
    assert out.get("reason") == "already_current_interlocutor"
    assert out.get("interlocutor_status") == "retained"
    assert out.get("fallback_anchor_source") == "active_interlocutor"
    assert session["interaction_context"]["active_interaction_target_id"] == "tavern_runner"
