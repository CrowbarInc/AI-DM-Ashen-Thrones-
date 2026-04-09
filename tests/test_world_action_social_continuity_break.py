"""World-action turns must break active-interlocutor social continuity (Block #1)."""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    should_route_addressed_question_to_social,
)
from game.storage import load_scene

import pytest

pytestmark = pytest.mark.unit


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def _bind_guard_social(session: dict) -> None:
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "guard_captain"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"


def test_sprint_away_breaks_continuity_and_drops_social_route():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Galinor sprints down an alley away from the post."
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is False
    ic = session.get("interaction_context") or {}
    assert str(ic.get("interaction_mode") or "").strip().lower() == "activity"
    assert not str(ic.get("active_interaction_target_id") or "").strip()


def test_running_until_out_of_breath_where_end_up_not_active_interlocutor_followup():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = (
        "Galinor keeps running until he's out of breath. Where does he end up?"
    )
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is False
    assert ent.get("reason") != "active_interlocutor_followup"
    ok, meta = should_route_addressed_question_to_social(
        text,
        session=session,
        world=world,
        scene_envelope=scene,
    )
    assert ok is False
    assert meta.get("route_reason") != "active_interlocutor_followup"


def test_self_directed_gate_watch_after_dialogue_breaks_when_no_address():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "He keeps watching the gate for anything unusual."
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is False
    ic = session.get("interaction_context") or {}
    assert not str(ic.get("active_interaction_target_id") or "").strip()


def test_where_is_old_milestone_stays_social_with_active_guard():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Where is the old milestone?"
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is True
    assert ent.get("target_actor_id") == "guard_captain"
    assert ent.get("reason") == "active_interlocutor_followup"


def test_directed_rebuttal_to_you_stays_social():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "I told you I don't know anything."
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is True
    assert ent.get("target_actor_id") == "guard_captain"


def test_immediate_same_speaker_follow_up_question_stays_social():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Who sent them?"
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is True
    assert ent.get("reason") == "active_interlocutor_followup"
    assert ent.get("target_actor_id") == "guard_captain"


def test_where_did_the_patrol_end_up_stays_social_not_self_outcome_break():
    """'The patrol' is third-party; must not match self-outcome 'where does he end up' heuristic."""
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Where did the patrol end up?"
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is True
    assert ent.get("target_actor_id") == "guard_captain"


def test_guard_captain_vocative_where_road_lead_stays_social():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Guard Captain, where does this road lead?"
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert ent.get("should_route_social") is True
    assert ent.get("target_actor_id") == "guard_captain"
    assert ent.get("reason") != "active_interlocutor_followup"
