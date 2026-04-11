"""Objective #21 block 3: stale interlocutor invalidation after visible speaker mismatch."""
from __future__ import annotations

import pytest

from game.defaults import default_scene, default_session, default_world
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.post_emission_speaker_adoption import (
    apply_post_emission_speaker_adoption,
    apply_stale_interlocutor_invalidation_after_emission,
)

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


def test_visible_guard_without_takeover_cue_clears_stale_runner_next_turn_not_runner_followup():
    """A. Guard grounded line without adoption takeover cue -> stale anchor cleared; no runner followup."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {"player_facing_text": 'Gate Guard says, "The gate closes at dusk."'}
    adopt = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    assert adopt.get("adopted") is False
    assert adopt.get("reason") == "no_takeover_or_player_directed_cue"

    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
        adoption_debug=adopt,
    )
    assert inv.get("cleared") is True
    assert inspect_interaction_context(session).get("active_interaction_target_id") in (None, "")
    assert (session.get("scene_state") or {}).get("current_interlocutor") in (None, "")

    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="Why close it so early?",
    )
    assert out.get("reason") != "active_interlocutor_followup"
    assert out.get("target_actor_id") != "tavern_runner"


def test_same_speaker_continuation_still_active_interlocutor_followup():
    """B. Same attributed speaker -> no stale clear; follow-up still binds active interlocutor."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {"player_facing_text": 'Tavern Runner leans in. "Same stew as yesterday; still hot."'}
    adopt = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
    )
    assert adopt.get("reason") == "already_current_interlocutor"

    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
        adoption_debug=adopt,
    )
    assert inv.get("cleared") is not True

    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="Is it still spiced the same way?",
    )
    assert out.get("reason") == "active_interlocutor_followup"
    assert out.get("target_actor_id") == "tavern_runner"


def test_ambiguous_multi_speaker_does_not_clear_stale_anchor():
    """C. Ambiguous multi-speaker output -> skip invalidation; runner continuity preserved."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {
        "player_facing_text": (
            'Gate Guard says, "Halt."\n'
            'Tavern Runner says, "Wait—the papers are in order."\n'
            '"Fine," the Gate Guard says, "move along."'
        )
    }
    adopt = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
    )
    assert adopt.get("reason") == "ambiguous_multi_speaker"

    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        gm,
        resolution=None,
        scene_changed=False,
        adoption_debug=adopt,
    )
    assert inv.get("cleared") is not True
    assert inspect_interaction_context(session).get("active_interaction_target_id") == "tavern_runner"


def test_adopted_speaker_is_authority_for_strict_social_continuity_fill():
    """D. After successful adoption, canonical interlocutor matches strict-social / retry consumers."""
    scene, world = _scene_world()
    session = _session_social("tavern_runner")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    gm = {"player_facing_text": 'Gate Guard says, "Halt—papers, now."'}
    adopt = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    assert adopt.get("adopted") is True

    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
        adoption_debug=adopt,
    )
    assert inv.get("reason") == "adoption_resolved_speaker"

    ic = inspect_interaction_context(session)
    aid = str(ic.get("active_interaction_target_id") or "").strip()
    assert canonical_interaction_target_npc_id(session, aid) == "gate_guard"
    assert (session.get("scene_state") or {}).get("current_interlocutor") == "gate_guard"
