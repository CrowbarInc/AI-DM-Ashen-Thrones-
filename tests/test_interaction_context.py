"""Interaction context + authoritative social target (Block 2 promotion continuity)."""
from __future__ import annotations

from game.campaign_state import create_fresh_combat_state, create_fresh_session_document
from game.interaction_context import (
    clear_for_scene_change,
    inspect,
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    set_social_exchange_interruption_tracker,
    set_social_target,
    synchronize_scene_addressability,
)
from game.api import _apply_authoritative_scene_transition
from game.npc_promotion import promoted_npc_id_for_actor
from game.social import finalize_social_target_with_promotion
from game.storage import load_scene


import pytest

pytestmark = pytest.mark.integration

def _session_gate_with_roster(world: dict):
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update(
        {e: "active" for e in st["active_entities"]}
    )
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene


def test_finalize_uses_promoted_actor_map_when_world_actor_index_mismatches_scene():
    """Session map binds actor_id → npc_id even when promoted_npc_id_for_actor skips (origin_scene mismatch)."""
    canon = "canon_refugee_row"
    world: dict = {
        "npcs": [
            {
                "id": canon,
                "name": "Ragged stranger",
                "location": "frontier_gate",
                "disposition": "neutral",
                "promoted_from_actor_id": "refugee",
                "origin_scene_id": "other_scene",
                "origin_kind": "scene_actor",
                "topics": [],
            }
        ]
    }
    assert promoted_npc_id_for_actor(None, world, "frontier_gate", "refugee") is None
    session, scene = _session_gate_with_roster(world)
    session["scene_state"]["promoted_actor_npc_map"]["refugee"] = canon
    set_social_target(session, "refugee")

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="What do you mean by that?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth["npc_id"] == "refugee"
    assert auth["source"] == "continuity"

    out, binding, _hints = finalize_social_target_with_promotion(
        session,
        world,
        "frontier_gate",
        auth,
        action_type="question",
        turn_counter=3,
        scene_envelope=scene,
        raw_player_text="What do you mean by that?",
    )
    assert out["npc_id"] == canon
    assert binding["npc_id"] == canon
    assert binding["target_source"] == "promoted_actor"
    assert binding["promoted_this_turn"] is False
    assert len(world["npcs"]) == 1


def test_set_social_target_allow_lists_interaction_to_scene_interlocutor_binding():
    session = create_fresh_session_document()
    world = {
        "npcs": [
            {
                "id": "guard_captain",
                "name": "Captain",
                "location": "frontier_gate",
                "topics": [],
            }
        ]
    }
    scene = load_scene("frontier_gate")
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    set_social_target(session, "guard_captain")
    assert inspect(session).get("active_interaction_target_id") == "guard_captain"
    assert session["scene_state"]["current_interlocutor"] == "guard_captain"
    traces = session.get("debug_traces") or []
    assert traces
    last = traces[-1]
    assert last.get("kind") == "state_mutation"
    assert last.get("domain") == "interaction_state"
    assert last.get("owner_module") == "game.interaction_context"
    assert last.get("operation") == "set_social_target"


def test_clear_for_scene_change_clears_interaction_and_scene_interlocutor():
    session = create_fresh_session_document()
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    session["scene_state"]["current_interlocutor"] = "npc_x"
    session["interaction_context"]["active_interaction_target_id"] = "npc_x"
    session["interaction_context"]["interaction_mode"] = "social"

    clear_for_scene_change(session)
    ctx = inspect(session)
    assert ctx.get("active_interaction_target_id") is None
    assert ctx.get("interaction_mode") == "none"
    assert session["scene_state"].get("current_interlocutor") is None


def test_set_social_exchange_interruption_tracker_mirrors_to_scene_state_slot():
    session = create_fresh_session_document()
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    payload = {"count": 1, "last_sig": "abc"}
    set_social_exchange_interruption_tracker(session, payload)
    assert session["scene_state"].get("social_exchange_interruption_tracker") == payload
    assert session.get("social_exchange_interruption_tracker") == payload


def test_synchronize_scene_addressability_is_scene_owner_and_may_bind_interlocutor():
    session, scene = _session_gate_with_roster(
        {
            "npcs": [
                {
                    "id": "guard_captain",
                    "name": "Captain",
                    "location": "frontier_gate",
                    "topics": [],
                }
            ]
        }
    )
    world = {
        "npcs": [
            {
                "id": "guard_captain",
                "name": "Captain",
                "location": "frontier_gate",
                "topics": [],
            }
        ]
    }
    session["interaction_context"]["active_interaction_target_id"] = "guard_captain"
    meta = synchronize_scene_addressability(session, scene, world)
    assert isinstance(meta, dict)
    assert session["scene_state"]["current_interlocutor"] == "guard_captain"


def test_rebuild_active_scene_entities_emits_scene_state_mutation_trace():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    world = {
        "npcs": [
            {
                "id": "tavern_runner",
                "name": "Runner",
                "location": "frontier_gate",
                "topics": [],
            }
        ]
    }
    scene = load_scene("frontier_gate")
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    traces = session.get("debug_traces") or []
    assert traces
    last = traces[-1]
    assert last.get("kind") == "state_mutation"
    assert last.get("domain") == "scene_state"
    assert last.get("operation") == "rebuild_active_scene_entities"
    assert last.get("owner_module") == "game.interaction_context"


def test_apply_authoritative_scene_transition_runs_as_api_scene_state_orchestration(monkeypatch):
    session = create_fresh_session_document()
    session["interaction_context"]["active_interaction_target_id"] = "guard_captain"
    session["scene_state"]["current_interlocutor"] = "guard_captain"
    combat = create_fresh_combat_state()
    world: dict = {"npcs": []}
    scene_envelope = {"scene": {"id": "other", "visible_facts": [], "exits": [], "mode": "exploration"}}

    monkeypatch.setattr("game.api.activate_scene", lambda sid: None)
    monkeypatch.setattr("game.api.load_scene", lambda sid: dict(scene_envelope) | {"scene": {**scene_envelope["scene"], "id": sid}})
    monkeypatch.setattr("game.api.load_session", lambda: session)
    monkeypatch.setattr("game.api.load_combat", lambda: combat)

    out_scene, out_session, out_combat = _apply_authoritative_scene_transition(
        "other_scene",
        scene_envelope,
        session,
        combat,
        world,
    )
    assert out_scene["scene"]["id"] == "other_scene"
    assert out_session is session
    assert inspect(session).get("active_interaction_target_id") is None
    assert session["scene_state"].get("current_interlocutor") in (None, "")
