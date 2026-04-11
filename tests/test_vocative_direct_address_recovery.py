"""Directed vocative recovery when continuity is absent (embedded ``tell me X,`` / ``X, who`` cues)."""

from __future__ import annotations

import copy

import pytest

from game.defaults import default_session
from game.interaction_context import rebuild_active_scene_entities, resolve_authoritative_social_target
from game.storage import load_scene

pytestmark = [pytest.mark.integration, pytest.mark.regression]


@pytest.fixture
def frontier_gate_cleared_interaction():
    """frontier_gate scene; empty world.npcs; active entities match gate roster; no dialogue continuity."""
    world: dict = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {}
    scene = load_scene("frontier_gate")
    st = session["scene_state"]
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = [
        "guard_captain",
        "tavern_runner",
        "refugee",
        "threadbare_watcher",
    ]
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, world, scene


def test_tell_me_runner_recovers_tavern_runner_without_continuity(frontier_gate_cleared_interaction):
    session, world, scene = frontier_gate_cleared_interaction
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text='Tell me runner, who runs the watch?',
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is True, auth
    assert auth.get("npc_id") == "tavern_runner", auth
    assert auth.get("source") == "vocative", auth
    assert "embedded" in str(auth.get("reason") or "").lower(), auth


def test_runner_comma_wh_question_recovers_without_continuity(frontier_gate_cleared_interaction):
    session, world, scene = frontier_gate_cleared_interaction
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Runner, what's special about that place?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is True, auth
    assert auth.get("npc_id") == "tavern_runner", auth


def test_guard_comma_wh_binds_unique_guard_without_continuity(frontier_gate_cleared_interaction):
    session, world, scene = frontier_gate_cleared_interaction
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Guard, who posted that notice?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is True, auth
    assert auth.get("npc_id") == "guard_captain", auth


def test_ambiguous_runner_role_does_not_bind(frontier_gate_cleared_interaction):
    session, world, scene = frontier_gate_cleared_interaction
    base = scene
    sc = copy.deepcopy(base.get("scene")) if isinstance(base.get("scene"), dict) else {}
    addr = sc.get("addressables")
    if not isinstance(addr, list):
        addr = []
    dup = {
        "id": "second_runner",
        "name": "Another Runner",
        "scene_id": "frontier_gate",
        "kind": "scene_actor",
        "addressable": True,
        "address_priority": 1,
        "address_roles": ["runner", "informant"],
        "aliases": [],
    }
    sc["addressables"] = list(addr) + [dup]
    scene2 = {"scene": sc, "scene_state": base.get("scene_state") or {}}
    st = session.get("scene_state")
    if isinstance(st, dict):
        ae = list(st.get("active_entities") or [])
        if "second_runner" not in ae:
            ae.append("second_runner")
        st = dict(st)
        st["active_entities"] = ae
        st["entity_presence"] = dict(st.get("entity_presence") or {})
        st["entity_presence"]["second_runner"] = "active"
        session["scene_state"] = st
        scene2["scene_state"] = st
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene2)

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Tell me runner, who runs the watch?",
        scene_envelope=scene2,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is False, auth
    assert auth.get("npc_id") in (None, ""), auth


def test_non_addressed_question_does_not_invent_target(frontier_gate_cleared_interaction):
    session, world, scene = frontier_gate_cleared_interaction
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Who runs the watch?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is False, auth
    assert auth.get("source") == "none", auth
