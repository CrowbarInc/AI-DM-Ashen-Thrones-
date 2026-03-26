"""Routing precedence: addressed NPC questions before adjudication/feasibility."""
from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.adjudication import classify_adjudication_query, resolve_adjudication_query
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.interaction_context import rebuild_active_scene_entities, should_route_addressed_question_to_social
from game.intent_parser import segment_mixed_player_turn

FAKE_GPT_RESPONSE = {
    "player_facing_text": "[Narration]",
    "tags": [],
    "scene_update": None,
    "activate_scene_id": None,
    "new_scene_draft": None,
    "world_updates": None,
    "suggested_action": None,
    "debug_notes": "",
}


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _seed_scene_with_runner(tmp_path, monkeypatch, *, clear_interaction: bool = False):
    _patch_storage(tmp_path, monkeypatch)
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    storage._save_json(storage.scene_path("scene_investigate"), scene)
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    if clear_interaction:
        session["interaction_context"] = {}
    storage._save_json(storage.SESSION_PATH, session)
    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "East road.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_segment_mixed_does_not_strip_can_you_npc_question_as_adjudication_clause():
    line = "You there, runner. Can you tell me what happened to the missing patrol?"
    seg = segment_mixed_player_turn(line)
    assert seg.get("adjudication_question_text") is None
    assert "runner" in (seg.get("declared_action_text") or "").lower()
    assert "can you tell" in (seg.get("declared_action_text") or "").lower()


def test_classify_adjudication_skips_can_you_when_runner_addressable(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=True)
    scene = storage.load_scene("scene_investigate")
    session = storage.load_session()
    world = storage.load_world()
    q = "Can you tell me what happened to the missing patrol?"
    cat = classify_adjudication_query(
        q,
        has_active_interaction=False,
        session=session,
        world=world,
        scene=scene,
    )
    assert cat is None


def test_classify_adjudication_can_i_reach_roof_stays_feasibility(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=True)
    scene = storage.load_scene("scene_investigate")
    session = storage.load_session()
    world = storage.load_world()
    q = "Can I reach the roof from here?"
    cat = classify_adjudication_query(
        q,
        has_active_interaction=False,
        session=session,
        world=world,
        scene=scene,
    )
    assert cat == "action_feasibility_query"


def test_should_route_addressed_question_active_followup(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=False)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    world = storage.load_world()
    scene = storage.load_scene("scene_investigate")
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    storage._save_json(storage.SESSION_PATH, session)
    session = storage.load_session()
    ok, meta = should_route_addressed_question_to_social(
        "Who's behind this plot?",
        session=session,
        world=world,
        scene_envelope=scene,
    )
    assert ok is True
    assert meta.get("route_reason") == "active_interlocutor_followup"
    assert meta.get("addressed_actor_id") == "runner"


def test_resolve_adjudication_none_for_directed_runner_question(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=True)
    scene = storage.load_scene("scene_investigate")
    session = storage.load_session()
    world = storage.load_world()
    character = storage.load_character()
    out = resolve_adjudication_query(
        "You there, runner. Can you tell me what happened to the missing patrol?",
        scene=scene,
        session=session,
        world=world,
        character=character,
        has_active_interaction=False,
    )
    assert out is None


def test_chat_hailing_runner_with_can_you_question_routes_social(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=True)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "You there, runner. Can you tell me what happened to the missing patrol?"},
        )
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    assert resolution.get("kind") != "adjudication_query"


def test_chat_runner_binding_followup_can_you_stays_social(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=False)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "I just want to know who attacked them. Can you tell me?"},
        )
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    assert resolution.get("kind") != "adjudication_query"


def test_chat_quoted_role_address_question_routes_social(tmp_path, monkeypatch):
    _seed_scene_with_runner(tmp_path, monkeypatch, clear_interaction=True)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": '"Runner, what happened to the missing patrol?"'},
        )
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
