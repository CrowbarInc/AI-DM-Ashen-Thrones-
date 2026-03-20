"""Targeted tests for activate_scene_id validation and GET-time session persistence."""
import json

from game import storage
from game.api import compose_state, app
from game.clocks import get_or_init_clocks, DEFAULT_CLOCKS
from game.defaults import default_scene, default_session, default_world, default_character, default_campaign, default_combat, default_conditions
from fastapi.testclient import TestClient


def _patch_storage_to_tmp(tmp_path, monkeypatch):
    """Point storage to tmp_path and create dirs; call once per test that needs isolated storage."""
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


def _minimal_gm(activate_scene_id=None):
    return {
        "player_facing_text": "Something happens.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": activate_scene_id,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


# ---- activate_scene_id validation ----


def test_invalid_activate_scene_id_ignored_safely(tmp_path, monkeypatch):
    """Invalid activate_scene_id in GM output is ignored: no activation, no default scene created."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    # One known scene only
    scene_a = default_scene("scene_a")
    scene_a["scene"]["id"] = "scene_a"
    storage._save_json(storage.scene_path("scene_a"), scene_a)
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

    # Mock call_gpt so chat applies our gm with invalid activate_scene_id
    def fake_call_gpt(messages):
        return _minimal_gm(activate_scene_id="nonexistent_scene")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "Hello."})
    assert r.status_code == 200

    session_after = storage.load_session()
    assert session_after["active_scene_id"] == "scene_a"
    ids = storage.list_scene_ids()
    assert "nonexistent_scene" not in ids
    assert "scene_a" in ids


def test_valid_activate_scene_id_is_advisory_only_in_chat(tmp_path, monkeypatch):
    """Valid activate_scene_id in GM output is advisory-only and does not activate scene during chat."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    scene_a = default_scene("scene_a")
    scene_a["scene"]["id"] = "scene_a"
    scene_a["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), scene_a)
    scene_b = default_scene("scene_b")
    scene_b["scene"]["id"] = "scene_b"
    storage._save_json(storage.scene_path("scene_b"), scene_b)
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

    def fake_call_gpt(messages):
        return _minimal_gm(activate_scene_id="scene_b")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "Hello there."})
    assert r.status_code == 200

    data = r.json()
    assert data.get("ok") is True
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_b"
    session_after = storage.load_session()
    assert session_after["active_scene_id"] == "scene_a"
    scene = storage.load_active_scene()
    assert scene["scene"]["id"] == "scene_a"


def test_post_scene_activate_rejects_unknown_id(tmp_path, monkeypatch):
    """POST /api/scene/activate returns error and does not create scene for unknown ID."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("only_scene"), default_scene("only_scene"))
    session = default_session()
    session["active_scene_id"] = "only_scene"
    session["visited_scene_ids"] = ["only_scene"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())

    client = TestClient(app)
    r = client.post("/api/scene/activate", json={"scene_id": "unknown_id"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is False
    assert "error" in data
    assert "unknown" in data["error"].lower() or "invalid" in data["error"].lower()

    session_after = storage.load_session()
    assert session_after["active_scene_id"] == "only_scene"
    assert "unknown_id" not in storage.list_scene_ids()


def test_post_scene_activate_clears_interaction_context(tmp_path, monkeypatch):
    """Activating a new scene clears active interaction context to prevent stale social targets."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    scene_a = default_scene("scene_a")
    scene_a["scene"]["id"] = "scene_a"
    scene_b = default_scene("scene_b")
    scene_b["scene"]["id"] = "scene_b"
    storage._save_json(storage.scene_path("scene_a"), scene_a)
    storage._save_json(storage.scene_path("scene_b"), scene_b)

    session = default_session()
    session["active_scene_id"] = "scene_a"
    session["visited_scene_ids"] = ["scene_a"]
    session["interaction_context"] = {
        "active_interaction_target_id": "guard_captain",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": "lowered_voice",
        "player_position_context": "seated_with_target",
    }
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())

    client = TestClient(app)
    r = client.post("/api/scene/activate", json={"scene_id": "scene_b"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True

    session_after = storage.load_session()
    assert session_after["active_scene_id"] == "scene_b"
    ctx = session_after.get("interaction_context") or {}
    assert ctx.get("active_interaction_target_id") is None
    assert ctx.get("active_interaction_kind") is None
    assert ctx.get("interaction_mode") == "none"
    assert ctx.get("engagement_level") == "none"
    assert ctx.get("conversation_privacy") is None
    assert ctx.get("player_position_context") is None


# ---- GET-time session persistence ----


def test_get_time_session_initialization_persists_when_mutation_occurs(tmp_path, monkeypatch):
    """When GET /api/state (compose_state) initializes clocks on session, the mutation is persisted."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    if "clocks" in session:
        del session["clocks"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())

    compose_state()

    session_reloaded = json.loads(storage.SESSION_PATH.read_text(encoding="utf-8"))
    assert "clocks" in session_reloaded
    for key in DEFAULT_CLOCKS:
        assert key in session_reloaded["clocks"]


def test_no_unnecessary_persistence_when_session_already_has_clocks(tmp_path, monkeypatch):
    """When session already has clocks, compose_state does not call save_session (no unnecessary write)."""
    _patch_storage_to_tmp(tmp_path, monkeypatch)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["character_name"] = "Galinor"  # match default character so sync doesn't trigger save
    get_or_init_clocks(session)
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())

    save_calls = []

    def record_save(data):
        save_calls.append(data)

    with monkeypatch.context() as m:
        m.setattr("game.api.save_session", record_save)
        compose_state()

    assert len(save_calls) == 0
