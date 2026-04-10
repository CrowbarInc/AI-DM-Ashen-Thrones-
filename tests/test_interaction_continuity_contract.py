"""Unit tests for ``game.interaction_continuity`` contract builder and policy resolution."""
from __future__ import annotations

import pytest

from game.interaction_continuity import build_interaction_continuity_contract
from game.response_policy_contracts import resolve_interaction_continuity_contract

pytestmark = pytest.mark.unit

_SCENE_ID = "frontier_gate"


def _world_with_npc(npc_id: str, *, location: str = _SCENE_ID) -> dict:
    return {"npcs": [{"id": npc_id, "name": npc_id, "location": location}]}


def _scene_envelope(scene_id: str = _SCENE_ID) -> dict:
    return {"scene": {"id": scene_id, "active_entities": [], "exits": []}}


def test_strong_continuity_from_active_social_target():
    world = _world_with_npc("npc_bob")
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": "npc_bob",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": ["npc_bob"],
            "current_interlocutor": "npc_bob",
        },
    }
    env = _scene_envelope()
    env["scene"]["active_entities"] = ["npc_bob"]
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=env,
        world=world,
        response_type_contract=None,
    )
    assert c["enabled"] is True
    assert c["continuity_strength"] == "strong"
    assert c["anchored_interlocutor_id"] == "npc_bob"
    assert c["drop_interlocutor_requires_explicit_break"] is True
    assert c["debug"]["source_of_anchor"] == "active_interaction_target_id"
    assert "social_mode_active" in c["continuity_reasons"]
    assert "anchored_to_active_target" in c["continuity_reasons"]


def test_fallback_to_current_interlocutor_when_active_target_missing():
    world = _world_with_npc("npc_cara")
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": ["npc_cara"],
            "current_interlocutor": "npc_cara",
        },
    }
    env = _scene_envelope()
    env["scene"]["active_entities"] = ["npc_cara"]
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=env,
        world=world,
        response_type_contract=None,
    )
    assert c["continuity_strength"] == "strong"
    assert c["anchored_interlocutor_id"] == "npc_cara"
    assert c["debug"]["source_of_anchor"] == "current_interlocutor"
    assert "anchored_to_scene_interlocutor" in c["continuity_reasons"]


def test_invalid_off_scene_target_does_not_anchor_without_dialogue_rtc():
    world = _world_with_npc("npc_bob")
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": "npc_ghost",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": ["npc_bob"],
            "current_interlocutor": None,
        },
    }
    env = _scene_envelope()
    env["scene"]["active_entities"] = ["npc_bob"]
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=env,
        world=world,
        response_type_contract=None,
    )
    assert c["anchored_interlocutor_id"] == ""
    assert c["enabled"] is False
    assert c["continuity_strength"] == "none"
    assert "no_valid_continuity_anchor" in c["continuity_reasons"]


def test_invalid_target_soft_when_dialogue_response_type():
    world = _world_with_npc("npc_bob")
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": "npc_ghost",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": ["npc_bob"],
            "current_interlocutor": None,
        },
    }
    env = _scene_envelope()
    env["scene"]["active_entities"] = ["npc_bob"]
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=env,
        world=world,
        response_type_contract={"required_response_type": "dialogue"},
    )
    assert c["continuity_strength"] == "soft"
    assert c["enabled"] is True
    assert c["preserve_conversational_thread"] is True
    assert c["drop_interlocutor_requires_explicit_break"] is False
    assert "dialogue_response_type_without_hard_anchor" in c["continuity_reasons"]
    assert "no_valid_continuity_anchor" in c["continuity_reasons"]


def test_dialogue_without_hard_anchor_soft_continuity():
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
            "engagement_level": "none",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": [],
            "current_interlocutor": None,
        },
    }
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=_scene_envelope(),
        world={},
        response_type_contract={"required_response_type": "dialogue"},
    )
    assert c["continuity_strength"] == "soft"
    assert c["enabled"] is True
    assert c["preserve_conversational_thread"] is True
    assert c["drop_interlocutor_requires_explicit_break"] is False


def test_non_social_activity_no_continuity_contract():
    session = {
        "active_scene_id": _SCENE_ID,
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": "observe",
            "interaction_mode": "activity",
            "engagement_level": "focused",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        "scene_state": {
            "active_scene_id": _SCENE_ID,
            "active_entities": [],
            "current_interlocutor": None,
        },
    }
    c = build_interaction_continuity_contract(
        session,
        scene_id=_SCENE_ID,
        scene_envelope=_scene_envelope(),
        world={},
        response_type_contract={"required_response_type": "neutral_narration"},
    )
    assert c["continuity_strength"] == "none"
    assert c["enabled"] is False


def test_resolve_interaction_continuity_contract_from_response_policy():
    ic = build_interaction_continuity_contract(
        {
            "active_scene_id": _SCENE_ID,
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
                "engagement_level": "none",
                "conversation_privacy": None,
                "player_position_context": None,
            },
            "scene_state": {
                "active_scene_id": _SCENE_ID,
                "active_entities": [],
                "current_interlocutor": None,
            },
        },
        scene_id=_SCENE_ID,
        scene_envelope=_scene_envelope(),
        world={},
        response_type_contract=None,
    )
    gm = {"response_policy": {"interaction_continuity": ic}}
    resolved, src = resolve_interaction_continuity_contract(gm, resolution=None, session=None)
    assert src == "response_policy"
    assert resolved is not None
    assert resolved.get("continuity_strength") == ic["continuity_strength"]
