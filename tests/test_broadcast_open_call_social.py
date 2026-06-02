"""Broadcast / open-call crowd social — downstream smoke (Cycle AL5).

Proves routing and outcome wiring for broadcast open-call lines through
``resolve_directed_social_entry``, ``is_broadcast_social_open_call``, and open-call
exemption from strict question-resolution / unresolved retry pressure.

Legality owners (do not restate here):
- ``tests/test_social_exchange_emission.py`` — strict-social / question-resolution tables
- ``tests/test_dialogue_routing_lock.py`` — dialogue route classification table
- ``tests/test_broad_address_social_bid.py`` — broad-address bid detection and recovery
"""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.gm import question_resolution_rule_check
from game.gm_retry import detect_retry_failures
from game.interaction_context import (
    canonical_scene_addressable_roster,
    is_broadcast_social_open_call,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
)
from game.storage import load_scene
from tests.helpers.emission_smoke_assertions import (
    assert_broadcast_open_call_rejected_smoke,
    assert_open_call_crowd_reaction_wiring_smoke,
    assert_open_call_no_unresolved_retry_smoke,
    assert_open_social_solicitation_route,
)

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


def _open_call_resolution() -> dict:
    return {
        "kind": "question",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "npc_reply_expected": False,
            "reply_kind": "reaction",
            "target_resolved": False,
        },
    }


def test_who_wants_routes_open_social_with_broadcast_flag():
    session, scene, world = _gate_session_scene()
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text='Galinor bellows: "WHO WANTS TO SPEAK WITH CINDERWATCH\'S NEWEST HERO?!?"',
    )
    assert_open_social_solicitation_route(ent, phrase="who_wants")


def test_broadcast_detector_rejects_local_observation():
    session, scene, world = _gate_session_scene()
    roster = canonical_scene_addressable_roster(world, "frontier_gate", scene_envelope=scene, session=session)
    d = is_broadcast_social_open_call(
        "What do I see?",
        roster=list(roster),
        session=session,
        scene_envelope=scene,
        world=world,
    )
    assert_broadcast_open_call_rejected_smoke(d, reason="local_scene_observation_query")


def test_broadcast_detector_rejects_named_vocative():
    session, scene, world = _gate_session_scene()
    roster = canonical_scene_addressable_roster(world, "frontier_gate", scene_envelope=scene, session=session)
    d = is_broadcast_social_open_call(
        "Guard Captain, answer me.",
        roster=list(roster),
        session=session,
        scene_envelope=scene,
        world=world,
    )
    assert_broadcast_open_call_rejected_smoke(d)


def test_question_resolution_exempt_for_open_call_crowd_reaction():
    chk = question_resolution_rule_check(
        player_text="Who wants to speak with me?",
        gm_reply_text="The line rustles; eyes flick toward you, measuring.",
        resolution=_open_call_resolution(),
    )
    assert_open_call_crowd_reaction_wiring_smoke(chk)


def test_detect_retry_failures_skips_unresolved_question_for_open_call():
    session, scene, world = _gate_session_scene()
    gm_reply = {
        "player_facing_text": "The crowd holds its breath—then the murmur returns, low and uneasy.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    failures = detect_retry_failures(
        player_text="Which of you saw what happened?",
        gm_reply=gm_reply,
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=_open_call_resolution(),
    )
    assert_open_call_no_unresolved_retry_smoke(failures)
