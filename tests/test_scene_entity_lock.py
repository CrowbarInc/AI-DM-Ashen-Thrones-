from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from game import storage
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

pytestmark = [pytest.mark.integration, pytest.mark.regression]

# feature: social, continuity

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


def _seed_transition_world(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)

    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["exits"] = [{"label": "To Roadside", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("frontier_gate"), gate)

    roadside = default_scene("old_milestone")
    roadside["scene"]["id"] = "old_milestone"
    roadside["scene"]["exits"] = [{"label": "Back to Gate", "target_scene_id": "frontier_gate"}]
    storage._save_json(storage.scene_path("old_milestone"), roadside)

    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "runner"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "patrol", "text": "The patrol vanished east of town."}],
        },
        {
            "id": "tattered_man",
            "name": "Tattered Man",
            "location": "old_milestone",
            "topics": [{"id": "ambush", "text": "Bandits wait in the ditch line."}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_scene_transition_rebuilds_active_entities_and_invalidates_interlocutor(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)

    transition_action = {
        "id": "follow-tattered-man",
        "label": "Follow the tattered man",
        "type": "scene_transition",
        "prompt": "I follow the tattered man out to the roadside.",
        "targetSceneId": "old_milestone",
    }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: transition_action)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I follow the tattered man."})

    assert resp.status_code == 200
    data = resp.json()
    assert data["session"]["active_scene_id"] == "old_milestone"
    assert data["scene"]["scene"]["id"] == "old_milestone"
    assert data["session"]["interaction_context"]["active_interaction_target_id"] is None

    scene_state = data["session"].get("scene_state") or {}
    assert scene_state.get("active_scene_id") == "old_milestone"
    assert "tattered_man" in (scene_state.get("active_entities") or [])
    assert "runner" not in (scene_state.get("active_entities") or [])
    assert scene_state.get("current_interlocutor") is None


def test_departed_npc_direct_address_gets_offscene_narrator_response(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)
    session = storage.load_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("GPT should not be called for offscene target")
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Runner, what happened to the patrol?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    assert social.get("npc_id") == "runner"
    assert social.get("offscene_target") is True
    assert social.get("target_resolved") is False

    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    assert text
    assert "scene holds while voices shift around you" in text.lower()
    assert "no longer here to answer" not in text.lower()


def test_reintroduced_entity_can_speak_again_once_present(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)
    session = storage.load_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    storage._save_json(storage.SESSION_PATH, session)
    world = storage.load_world()
    for npc in world.get("npcs") or []:
        if isinstance(npc, dict) and npc.get("id") == "runner":
            npc["location"] = "old_milestone"
            npc["topics"] = [{"id": "return", "text": "Bandits are setting an ambush farther up road."}]
    storage._save_json(storage.WORLD_PATH, world)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Runner, what happened to the patrol?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    assert social.get("npc_id") == "runner"
    assert social.get("target_resolved") is True
    assert social.get("offscene_target") is not True
    assert "runner" in ((data.get("session") or {}).get("scene_state", {}).get("active_entities") or [])


def test_stale_interlocutor_does_not_override_active_scene_responder(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)
    session = storage.load_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "runner"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What happened here?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    assert social.get("npc_id") == "tattered_man"
    assert social.get("offscene_target") is not True
    assert data["session"]["interaction_context"]["active_interaction_target_id"] == "tattered_man"