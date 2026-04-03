"""Scene-transition authority tests.

Engine/resolution path is authoritative for scene activation in a turn.
GPT transition fields are advisory-only.
"""
from __future__ import annotations

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

import pytest

pytestmark = pytest.mark.integration

# feature: routing, emission


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


def _seed_three_scenes(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)

    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    storage._save_json(storage.scene_path("scene_b"), sb)

    sc = default_scene("scene_c")
    sc["scene"]["id"] = "scene_c"
    storage._save_json(storage.scene_path("scene_c"), sc)

    session = default_session()
    session["active_scene_id"] = "scene_a"
    session["visited_scene_ids"] = ["scene_a"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _gm_with_transition_proposal(target: str) -> dict:
    return {
        "player_facing_text": "Narration.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": target,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def test_resolver_scene_transition_remains_authoritative(tmp_path, monkeypatch):
    """Resolver transition applies; conflicting GPT proposal stays advisory."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "Go to B",
                "exploration_action": {
                    "id": "go-b",
                    "label": "Go to B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to B.",
                },
            },
        )

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("resolution", {}).get("resolved_transition") is True
    assert data.get("resolution", {}).get("target_scene_id") == "scene_b"
    assert data.get("session", {}).get("active_scene_id") == "scene_b"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_b"
    # Proposal remains present but non-authoritative.
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_c"
    assert "scene_c" not in (data.get("session", {}).get("visited_scene_ids") or [])


def test_gpt_transition_proposal_does_not_apply_without_resolver_transition(tmp_path, monkeypatch):
    """Chat turn with only GPT transition proposal does not activate scene."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_b"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "hello there"})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_b"
    assert data.get("session", {}).get("active_scene_id") == "scene_a"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_a"


def test_no_double_scene_switch_when_resolver_transition_and_gpt_proposal_both_present(tmp_path, monkeypatch):
    """Only one activation call occurs in a turn when both sources exist."""
    _seed_three_scenes(tmp_path, monkeypatch)
    activate_calls: list[str] = []

    def wrapped_activate(scene_id: str):
        activate_calls.append(scene_id)
        return storage.activate_scene(scene_id)

    with monkeypatch.context() as m:
        m.setattr("game.api.activate_scene", wrapped_activate)
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "exploration_action": {
                    "id": "go-b",
                    "label": "Go to B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to B.",
                },
            },
        )

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "scene_b"
    assert activate_calls == ["scene_b"]
