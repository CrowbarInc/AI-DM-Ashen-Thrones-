"""NPC promotion schema, world helpers, and promotion API (Blocks 1–2)."""
from __future__ import annotations

import copy

from game.campaign_state import create_fresh_session_document
from game.defaults import default_world
from game.interaction_context import inspect, maybe_promote_active_social_target, set_social_target, should_promote_scene_actor
from game.npc_promotion import deterministic_promoted_npc_id, disposition_to_stance, promote_scene_actor_to_npc
from game.social import finalize_social_target_with_promotion
from game.world import (
    ensure_npc_social_fields,
    get_world_npc_by_id,
    normalize_promoted_npc_record,
    promoted_npc_id_for_actor,
    upsert_world_npc,
)


def test_default_world_loads_and_normalizes_on_ensure():
    w = default_world()
    npc = w["npcs"][0]
    ensure_npc_social_fields(npc)
    assert npc["stance_toward_player"] == "neutral"
    assert npc["origin_kind"] == "npc"
    assert isinstance(npc["knowledge_scope"], list)
    assert npc["information_reliability"] == "partial"
    assert npc["tags"] == []


def test_disposition_maps_to_stance():
    assert disposition_to_stance("friendly") == "favorable"
    assert disposition_to_stance("neutral") == "neutral"
    assert disposition_to_stance("hostile") == "hostile"
    assert disposition_to_stance("wary") == "wary"
    assert disposition_to_stance("odd") == "wary"


def test_tavern_runner_friendly_stance():
    w = default_world()
    runner = next(n for n in w["npcs"] if n["id"] == "tavern_runner")
    ensure_npc_social_fields(runner)
    assert runner["disposition"] == "friendly"
    assert runner["stance_toward_player"] == "favorable"


def test_deterministic_promoted_npc_id_prefers_source_actor_id():
    assert (
        deterministic_promoted_npc_id("frontier_gate", "Ignored", source_actor_id="emergent_watcher")
        == "emergent_watcher"
    )
    assert (
        deterministic_promoted_npc_id("frontier_gate", "Ragged stranger", source_actor_id=None)
        == "frontier_gate__ragged_stranger"
    )


def test_promoted_npc_id_for_actor_native_and_promoted():
    w = default_world()
    assert promoted_npc_id_for_actor(None, w, "frontier_gate", "guard_captain") == "guard_captain"
    w2 = copy.deepcopy(w)
    upsert_world_npc(
        w2,
        {
            "id": "frontier_gate__ragged_stranger",
            "name": "Ragged stranger",
            "location": "frontier_gate",
            "role": "refugee",
            "affiliation": "",
            "availability": "available",
            "current_agenda": "",
            "disposition": "neutral",
            "origin_kind": "scene_actor",
            "origin_scene_id": "frontier_gate",
            "promoted_from_actor_id": "refugee",
            "topics": [],
        },
    )
    assert promoted_npc_id_for_actor(None, w2, "frontier_gate", "refugee") == "frontier_gate__ragged_stranger"


def test_promoted_npc_id_scene_mismatch_ignored():
    w: dict = {"npcs": [
        {
            "id": "a",
            "name": "A",
            "location": "s1",
            "promoted_from_actor_id": "x",
            "origin_scene_id": "s1",
        }
    ]}
    ensure_npc_social_fields(w["npcs"][0])
    assert promoted_npc_id_for_actor(None, w, "s2", "x") is None
    assert promoted_npc_id_for_actor(None, w, "s1", "x") == "a"


def test_upsert_world_npc_idempotent():
    w = {"npcs": []}
    rec = {
        "id": "frontier_gate__vendor",
        "name": "Stall vendor",
        "location": "frontier_gate",
        "role": "merchant",
        "affiliation": "",
        "availability": "available",
        "current_agenda": "",
        "disposition": "neutral",
        "origin_kind": "crowd_actor",
        "origin_scene_id": "frontier_gate",
        "promoted_from_actor_id": "crowd_vendor",
        "topics": [{"id": "wares", "text": "Cheap rope."}],
    }
    a = upsert_world_npc(w, rec)
    b = upsert_world_npc(w, rec)
    assert a == b
    assert len(w["npcs"]) == 1


def test_get_world_npc_by_id_normalizes():
    w = {
        "npcs": [
            {"id": "z", "name": "Zed", "location": "here", "disposition": "hostile"},
        ]
    }
    n = get_world_npc_by_id(w, "z")
    assert n is not None
    assert n["stance_toward_player"] == "hostile"


def test_normalize_promoted_npc_record_is_copy():
    src = {"id": "k", "name": "K", "location": "x", "disposition": "friendly"}
    out = normalize_promoted_npc_record(src)
    assert out is not src
    assert out["stance_toward_player"] == "favorable"
    assert "stance_toward_player" not in src


def _gate_session():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    return session


def test_promote_scene_actor_creates_world_npc():
    session = _gate_session()
    world: dict = {"npcs": []}
    r = promote_scene_actor_to_npc(session, world, "frontier_gate", "threadbare_watcher", reason="test")
    assert r["ok"] is True
    assert r["npc_id"] == "threadbare_watcher"
    assert r["already_promoted"] is False
    assert len(world["npcs"]) == 1
    npc = world["npcs"][0]
    assert npc["id"] == "threadbare_watcher"
    assert npc["promoted_from_actor_id"] == "threadbare_watcher"
    assert npc["origin_scene_id"] == "frontier_gate"
    assert npc["origin_kind"] == "scene_actor"
    assert npc["information_reliability"] == "partial"
    assert "scene:frontier_gate" in npc["knowledge_scope"]
    assert session["scene_state"]["promoted_actor_npc_map"]["threadbare_watcher"] == "threadbare_watcher"


def test_promote_same_actor_twice_no_duplicate_npc():
    session = _gate_session()
    world: dict = {"npcs": []}
    a = promote_scene_actor_to_npc(session, world, "frontier_gate", "threadbare_watcher")
    b = promote_scene_actor_to_npc(session, world, "frontier_gate", "threadbare_watcher")
    assert a["ok"] and b["ok"]
    assert len(world["npcs"]) == 1
    assert b["already_promoted"] is True


def test_promote_updates_interlocutor_when_npc_id_differs():
    session = _gate_session()
    world: dict = {"npcs": []}
    upsert_world_npc(
        world,
        {
            "id": "frontier_gate__ragged_stranger",
            "name": "Ragged stranger",
            "location": "frontier_gate",
            "role": "refugee",
            "affiliation": "",
            "availability": "available",
            "current_agenda": "",
            "disposition": "neutral",
            "origin_kind": "scene_actor",
            "origin_scene_id": "frontier_gate",
            "promoted_from_actor_id": "refugee",
            "topics": [],
        },
    )
    set_social_target(session, "refugee")
    session["scene_state"]["active_entities"] = ["refugee", "guard_captain"]
    session["scene_state"]["entity_presence"] = {"refugee": "active", "guard_captain": "active"}
    r = promote_scene_actor_to_npc(session, world, "frontier_gate", "refugee")
    assert r["ok"] and r["npc_id"] == "frontier_gate__ragged_stranger"
    assert inspect(session)["active_interaction_target_id"] == "frontier_gate__ragged_stranger"
    assert session["scene_state"]["current_interlocutor"] == "frontier_gate__ragged_stranger"
    assert "frontier_gate__ragged_stranger" in session["scene_state"]["active_entities"]
    assert "refugee" not in session["scene_state"]["active_entities"]


def test_promote_actor_not_found():
    session = _gate_session()
    world: dict = {"npcs": []}
    r = promote_scene_actor_to_npc(session, world, "frontier_gate", "no_such_actor_xyz")
    assert r["ok"] is False
    assert r["error"] == "actor_not_found"


def test_promote_kind_npc_without_world_row_rejected():
    session = _gate_session()
    world: dict = {"npcs": []}
    r = promote_scene_actor_to_npc(session, world, "frontier_gate", "guard_captain")
    assert r["ok"] is False
    assert r["error"] == "not_promotable"


def test_should_promote_and_maybe_promote_active_target():
    session = _gate_session()
    world: dict = {"npcs": []}
    assert should_promote_scene_actor(session, world, "frontier_gate", "threadbare_watcher")
    set_social_target(session, "threadbare_watcher")
    out = maybe_promote_active_social_target(session, world, "frontier_gate", reason="hook")
    assert out is not None and out["ok"] is True
    assert len(world["npcs"]) == 1


def test_world_reexports_promote_scene_actor_to_npc():
    from game.world import promote_scene_actor_to_npc as w_promo

    assert w_promo is promote_scene_actor_to_npc


def test_finalize_social_target_binds_promoted_actor_npc_map_without_new_npc_row():
    session = _gate_session()
    world: dict = {"npcs": []}
    promote_scene_actor_to_npc(session, world, "frontier_gate", "refugee")
    assert len(world["npcs"]) == 1
    npc_id = world["npcs"][0]["id"]
    session["scene_state"]["promoted_actor_npc_map"]["refugee"] = npc_id
    auth = {
        "npc_id": "refugee",
        "npc_name": "Refugee",
        "target_resolved": True,
        "offscene_target": False,
        "source": "continuity",
        "reason": "test",
    }
    out, binding, _ = finalize_social_target_with_promotion(
        session,
        world,
        "frontier_gate",
        auth,
        action_type="question",
        turn_counter=3,
        scene_envelope=None,
        raw_player_text="What did you see?",
    )
    assert out["npc_id"] == npc_id
    assert binding["target_source"] == "promoted_actor"
    assert binding["promoted_this_turn"] is False
    # When canonical id equals actor id, origin_actor_id stays None (map is still authoritative).
    assert binding.get("origin_actor_id") in (None, "refugee")
    assert len(world["npcs"]) == 1


def test_finalize_social_target_auto_promotes_on_stable_address():
    session = _gate_session()
    world: dict = {"npcs": []}
    auth = {
        "npc_id": "threadbare_watcher",
        "npc_name": "Watcher",
        "target_resolved": True,
        "offscene_target": False,
        "source": "vocative",
        "reason": "test",
    }
    out, binding, hints = finalize_social_target_with_promotion(
        session,
        world,
        "frontier_gate",
        auth,
        action_type="question",
        turn_counter=0,
        scene_envelope=None,
        raw_player_text="Threadbare watcher, what do you know?",
    )
    assert binding.get("promoted_this_turn") is True
    assert binding["npc_id"] == out["npc_id"]
    assert hints.get("guardedness") in ("low", "medium", "high")
    assert len(world["npcs"]) == 1


def test_meaningful_social_exchanges_idempotent_single_npc_via_finalize():
    """Repeated stable-address finalize paths do not grow world.npcs (repromotion is upsert-only)."""
    session = _gate_session()
    world: dict = {"npcs": []}
    auth = {
        "npc_id": "threadbare_watcher",
        "npc_name": "Watcher",
        "target_resolved": True,
        "offscene_target": False,
        "source": "vocative",
        "reason": "test",
    }
    raw = "Threadbare watcher, what now?"
    for turn in range(3):
        _, binding, _ = finalize_social_target_with_promotion(
            session,
            world,
            "frontier_gate",
            auth,
            action_type="question",
            turn_counter=turn,
            scene_envelope=None,
            raw_player_text=raw,
        )
        assert binding.get("npc_id") == "threadbare_watcher"
        assert binding.get("promoted_this_turn") is (turn == 0)
    assert len(world["npcs"]) == 1


def test_finalize_social_target_skips_promote_on_first_roster_fallback():
    session = _gate_session()
    world: dict = {"npcs": []}
    auth = {
        "npc_id": "threadbare_watcher",
        "target_resolved": True,
        "offscene_target": False,
        "source": "first_roster",
        "reason": "fallback",
    }
    _, binding, _ = finalize_social_target_with_promotion(
        session,
        world,
        "frontier_gate",
        auth,
        action_type="question",
        turn_counter=0,
        scene_envelope=None,
        raw_player_text="So… anything new?",
    )
    assert binding == {}
    assert len(world["npcs"]) == 0
