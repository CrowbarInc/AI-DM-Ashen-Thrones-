"""Objective #21 — recover NPC topic follow-ups misclassified as local observation."""
from __future__ import annotations

import pytest

from game.defaults import default_scene, default_session, default_world
from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
)
from game.intent_parser import parse_freeform_to_action

pytestmark = pytest.mark.unit


def _base_scene_world():
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
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
    return scene, world


def _session_with_runner_topic_pressure(*, last_answer: str) -> dict:
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    session["scene_runtime"] = {
        "scene_investigate": {
            "topic_pressure_last_topic_key": "crossroads_incident",
            "topic_pressure_current": {
                "speaker_key": "tavern_runner",
                "topic_key": "crossroads_incident",
            },
            "topic_pressure": {
                "crossroads_incident": {
                    "last_answer": last_answer,
                    "last_turn": 3,
                }
            },
        }
    }
    return session


def test_runner_clue_followup_routes_social_not_observe():
    """A. NPC clue 'Old crossroads—that way.' -> 'What's going on at the old crossroads?' stays social."""
    scene, world = _base_scene_world()
    session = _session_with_runner_topic_pressure(last_answer="Old crossroads—that way.")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "Okay? What's going on at the old crossroads?"
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is True
    assert out.get("target_actor_id") == "tavern_runner"
    stc = out.get("social_turn_contract") or {}
    assert stc.get("social_followup_recovery") == "fired"
    assert stc.get("continuity_status") == "preserved"
    assert stc.get("interlocutor_status") == "retained"
    assert stc.get("fallback_anchor_source") == "active_interlocutor"
    act = parse_freeform_to_action(
        text,
        scene,
        session=session,
        world=world,
    )
    assert act is None or act.get("type") != "observe"


def test_same_wording_without_context_stays_observation_exploration():
    """B. No active NPC / no surfaced answer — still observe when shaped like local observation."""
    scene, world = _base_scene_world()
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "What's going on at the old crossroads?"
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is False
    assert out.get("reason") == "local_scene_observation_query"
    stc = out.get("social_turn_contract") or {}
    assert stc.get("social_followup_recovery") == "skipped"
    assert stc.get("continuity_status") == "broken"
    act = parse_freeform_to_action(text, scene, session=session, world=world)
    assert act is not None
    assert act.get("type") == "observe"


def test_perception_question_at_anchor_not_forcibly_social():
    """C. Genuine perception at a place name does not use going-on recovery."""
    scene, world = _base_scene_world()
    session = _session_with_runner_topic_pressure(last_answer="Old crossroads—that way.")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "What do I see near the old crossroads marker?"
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is False
    assert out.get("reason") == "local_scene_observation_query"
    stc = out.get("social_turn_contract") or {}
    assert stc.get("social_followup_recovery") == "skipped"
    assert stc.get("continuity_status") == "broken"


def test_direct_question_to_active_npc_control():
    """D. Direct information question to engaged NPC still routes social (baseline)."""
    scene, world = _base_scene_world()
    session = _session_with_runner_topic_pressure(last_answer="Stew's plain today.")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "What's in the stew today?"
    out = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert out.get("should_route_social") is True
    assert out.get("target_actor_id") == "tavern_runner"
    stc = out.get("social_turn_contract") or {}
    assert stc.get("social_followup_recovery") == "not_applicable"
    assert stc.get("continuity_status") == "preserved"
    assert stc.get("interlocutor_status") == "retained"
    assert stc.get("fallback_anchor_source") == "active_interlocutor"
