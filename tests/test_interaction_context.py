"""Interaction context + authoritative social target (Block 2 promotion continuity)."""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.interaction_context import rebuild_active_scene_entities, resolve_authoritative_social_target, set_social_target
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
