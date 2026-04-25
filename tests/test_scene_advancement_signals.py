"""Focused tests for explicit scene-advancement signaling."""
from __future__ import annotations

import json

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
    gate["scene"]["exits"] = [
        {"label": "Go to the Crossroads", "target_scene_id": "crossroads"},
        {"label": "Enter Cinderwatch", "target_scene_id": "market_quarter"},
    ]
    crossroads = default_scene("crossroads")
    crossroads["scene"]["id"] = "crossroads"
    crossroads["scene"]["location"] = "The Crossroads"
    crossroads["scene"]["summary"] = "A wind-bent milestone marks the road split."
    crossroads["scene"]["exits"] = [{"label": "Back to the gate", "target_scene_id": "frontier_gate"}]

    storage._save_json(storage.scene_path("frontier_gate"), gate)
    storage._save_json(storage.scene_path("crossroads"), crossroads)
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))

    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["interaction_context"]["active_interaction_target_id"] = "tavern_runner"
    session["interaction_context"]["active_interaction_kind"] = "social"
    session["interaction_context"]["interaction_mode"] = "social"
    session["interaction_context"]["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_campaign_start_turn_provides_opening_scene_context(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)
    captured_payloads: list[dict] = []

    def _capture(messages):
        for msg in messages:
            if msg.get("role") != "user":
                continue
            try:
                payload = json.loads(msg.get("content") or "{}")
            except Exception:
                continue
            captured_payloads.append(payload)
        return {
            "player_facing_text": "Rain lashes the gate district as the campaign begins.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _capture)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Begin the campaign."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "scene_opening"
    assert (resolution.get("state_changes") or {}).get("opening_scene_turn") is True
    assert (resolution.get("state_changes") or {}).get("new_scene_context_available") is True
    assert captured_payloads
    obligations = captured_payloads[-1].get("narration_obligations") or {}
    assert obligations.get("is_opening_scene") is True
    advancement = captured_payloads[-1].get("scene_advancement") or {}
    assert advancement.get("new_scene_context_available") is True


def test_known_destination_transition_sets_arrival_signals(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: {
                "player_facing_text": "At the crossroads, the roads split under a low sky.",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            },
        )
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "Go to the crossroads.",
                "exploration_action": {
                    "id": "go-crossroads",
                    "label": "Go to the crossroads",
                    "type": "scene_transition",
                    "targetSceneId": "crossroads",
                    "prompt": "Go to the crossroads.",
                },
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "crossroads"
    resolution = data.get("resolution") or {}
    state_changes = resolution.get("state_changes") or {}
    assert resolution.get("resolved_transition") is True
    assert state_changes.get("scene_transition_occurred") is True
    assert state_changes.get("arrived_at_scene") is True
    assert state_changes.get("new_scene_context_available") is True


def test_leave_interaction_and_travel_yields_scene_ready_state(tmp_path, monkeypatch):
    _seed_transition_world(tmp_path, monkeypatch)
    captured_payloads: list[dict] = []

    def _capture(messages):
        for msg in messages:
            if msg.get("role") != "user":
                continue
            try:
                payload = json.loads(msg.get("content") or "{}")
            except Exception:
                continue
            captured_payloads.append(payload)
        return {
            "player_facing_text": "You leave the conversation and reach the crossroads.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _capture)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I leave the conversation and head to the crossroads."})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    state_changes = resolution.get("state_changes") or {}
    assert resolution.get("resolved_transition") is True
    assert state_changes.get("new_scene_context_available") is True
    assert data.get("session", {}).get("active_scene_id") == "crossroads"
    interaction_ctx = data.get("session", {}).get("interaction_context") or {}
    assert interaction_ctx.get("interaction_mode") == "none"
    assert captured_payloads
    # Prompt context should already be using destination scene state.
    assert (captured_payloads[-1].get("scene") or {}).get("public", {}).get("id") == "crossroads"
