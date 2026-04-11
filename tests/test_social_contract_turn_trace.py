"""Regression: ``turn_trace.social_contract_trace`` mirrors canonical contract + post-emission debug."""
from __future__ import annotations

import pytest

from game.api_turn_support import build_social_contract_turn_trace
from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, resolve_directed_social_entry

pytestmark = pytest.mark.unit


def _scene_world():
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


def _session_runner_topic_pressure(*, last_answer: str) -> dict:
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


def test_trace_followup_recovery_matches_directed_social_contract():
    """Local-observation follow-up recovered to social — trace fields match ``social_turn_contract``."""
    scene, world = _scene_world()
    session = _session_runner_topic_pressure(last_answer="Old crossroads—that way.")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    text = "Okay? What's going on at the old crossroads?"
    entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    stc = entry.get("social_turn_contract") or {}
    tt = build_social_contract_turn_trace(
        resolution={"metadata": {"social_turn_contract": dict(stc)}},
        normalized_action=None,
        directed_social_entry=None,
        route_selected="dialogue",
        session=session,
    )
    assert tt["routing_reason_code"] == stc.get("routing_reason_code")
    assert tt["social_followup_recovery"] == "fired"
    assert tt["continuity_status"] == "preserved"
    assert tt["reply_owner_actor_id"] == "tavern_runner"
    assert tt["fallback_anchor_source"] == "active_interlocutor"
    assert tt["final_reply_owner"] == "tavern_runner"


def test_trace_explicit_takeover_adoption_overlays_interlocutor_status():
    """Emitted takeover adoption — overlay matches adoption debug, final owner from session."""
    scene, world = _scene_world()
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    session["scene_state"] = {"current_interlocutor": "tavern_runner"}
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)

    stc = {
        "routing_reason_code": "active_interlocutor_followup",
        "social_followup_recovery": "not_applicable",
        "reply_owner_actor_id": "tavern_runner",
        "interlocutor_status": "retained",
        "continuity_status": "preserved",
        "fallback_anchor_source": "active_interlocutor",
    }
    adoption = {
        "adopted": True,
        "reason": "emitted_authoritative_takeover",
        "interlocutor_status": "adopted",
        "fallback_anchor_source": "visible_speaker",
        "npc_id": "gate_guard",
    }
    session["interaction_context"]["active_interaction_target_id"] = "gate_guard"
    session["scene_state"]["current_interlocutor"] = "gate_guard"

    tt = build_social_contract_turn_trace(
        resolution={"metadata": {"social_turn_contract": dict(stc)}},
        normalized_action=None,
        directed_social_entry=None,
        route_selected="dialogue",
        session=session,
        adoption_debug=adoption,
        stale_invalidation_debug=None,
    )
    assert tt["interlocutor_status"] == "adopted"
    assert tt["fallback_anchor_source"] == "visible_speaker"
    assert tt["visible_grounded_speaker"] == "gate_guard"
    assert tt["final_reply_owner"] == "gate_guard"
    assert tt["routing_reason_code"] == "active_interlocutor_followup"


def test_trace_stale_invalidation_overlays_from_stale_debug():
    """Stale interlocutor cleared — trace matches stale invalidation debug (canonical copy)."""
    stc = {
        "routing_reason_code": "active_interlocutor_followup",
        "social_followup_recovery": "not_applicable",
        "reply_owner_actor_id": "tavern_runner",
        "interlocutor_status": "retained",
        "continuity_status": "preserved",
        "fallback_anchor_source": "active_interlocutor",
    }
    session = default_session()
    session["interaction_context"] = {"active_interaction_target_id": None}
    stale = {
        "cleared": True,
        "reason": "visible_speaker_contradicts_stored_interlocutor",
        "interlocutor_status": "invalidated",
        "fallback_anchor_source": "visible_speaker",
        "visible_grounded_speaker_id": "gate_guard",
    }
    tt = build_social_contract_turn_trace(
        resolution={"metadata": {"social_turn_contract": dict(stc)}},
        normalized_action=None,
        directed_social_entry=None,
        route_selected="dialogue",
        session=session,
        adoption_debug={"adopted": False, "reason": "no_takeover_or_player_directed_cue"},
        stale_invalidation_debug=stale,
    )
    assert tt["interlocutor_status"] == "invalidated"
    assert tt["fallback_anchor_source"] == "visible_speaker"
    assert tt["visible_grounded_speaker"] == "gate_guard"


def test_trace_ambiguity_no_false_visible_speaker():
    """Anonymous crowd / unresolved visible speaker — no ``visible_grounded_speaker`` id in trace."""
    session = default_session()
    session["interaction_context"] = {"active_interaction_target_id": "tavern_runner"}
    stc = {
        "routing_reason_code": "visible_speaker",
        "reply_owner_actor_id": "tavern_runner",
        "interlocutor_status": "adopted",
        "continuity_status": "redirected",
        "fallback_anchor_source": "visible_speaker",
        "social_followup_recovery": "not_applicable",
    }
    adoption = {
        "adopted": False,
        "reason": "generic_or_anonymous_speaker",
        "interlocutor_status": "none",
    }
    tt = build_social_contract_turn_trace(
        resolution={"metadata": {"social_turn_contract": dict(stc)}},
        normalized_action=None,
        directed_social_entry=None,
        route_selected="dialogue",
        session=session,
        adoption_debug=adoption,
    )
    assert tt["visible_grounded_speaker"] is None
    assert tt["final_reply_owner"] == "tavern_runner"


def test_coalesce_prefers_resolution_metadata_over_directed_entry():
    """Resolution metadata wins over ``directed_social_entry`` for contract coalescing."""
    stc_a = {
        "routing_reason_code": "from_resolution",
        "social_followup_recovery": "not_applicable",
        "reply_owner_actor_id": "npc_a",
        "interlocutor_status": "retained",
        "continuity_status": "preserved",
        "fallback_anchor_source": "active_interlocutor",
    }
    stc_b = {
        "routing_reason_code": "from_entry",
        "social_followup_recovery": "skipped",
        "reply_owner_actor_id": "npc_b",
        "interlocutor_status": "none",
        "continuity_status": "broken",
        "fallback_anchor_source": "none",
    }
    tt = build_social_contract_turn_trace(
        resolution={"metadata": {"social_turn_contract": dict(stc_a)}},
        normalized_action=None,
        directed_social_entry={"social_turn_contract": dict(stc_b)},
        route_selected="undecided",
        session=default_session(),
    )
    assert tt["routing_reason_code"] == "from_resolution"

