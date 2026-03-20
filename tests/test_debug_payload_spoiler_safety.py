"""Tests that debug endpoints and state payloads never expose spoiler content (hidden_facts, undiscovered clues)."""
import pytest

from game import storage
from game.api import app, compose_state
from game.defaults import default_scene, default_session, default_world, default_character, default_campaign, default_combat, default_conditions
from fastapi.testclient import TestClient


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


def _seed_minimal(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    scene = default_scene("test_scene")
    scene["scene"]["id"] = "test_scene"
    scene["scene"]["hidden_facts"] = ["secret_gm_only_fact", "another_spoiler"]
    scene["scene"]["discoverable_clues"] = ["undiscovered_clue_1"]
    scene["scene"]["visible_facts"] = ["visible_to_player"]
    storage._save_json(storage.scene_path("test_scene"), scene)
    session = default_session()
    session["active_scene_id"] = "test_scene"
    session["visited_scene_ids"] = ["test_scene"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _state_contains_spoiler(state: dict, scene_data: dict) -> bool:
    """Return True if state or debug payload contains any hidden_facts or undiscovered clue text."""
    def contains_in_obj(obj, path=""):
        if obj is None:
            return False
        if isinstance(obj, str):
            for h in (scene_data.get("scene", {}).get("hidden_facts") or []):
                if h and h in obj:
                    return True
            clues = scene_data.get("scene", {}).get("discoverable_clues") or []
            discovered = (scene_data.get("scene_runtime") or {}).get("test_scene") or {}
            discovered_texts = set(discovered.get("discovered_clues") or [])
            for c in clues:
                if c and c not in discovered_texts and c in obj:
                    return True
            return False
        if isinstance(obj, list):
            return any(contains_in_obj(x, path) for x in obj)
        if isinstance(obj, dict):
            if obj.get("hidden_facts"):
                return True
            return any(contains_in_obj(v, f"{path}.{k}") for k, v in obj.items())
        return False

    scene = state.get("scene") or {}
    scene_obj = scene.get("scene") or {}
    rt = state.get("session") or {}
    rt = rt.get("scene_runtime") or {}
    ctx = {"scene": scene_obj, "scene_runtime": rt}

    debug = state.get("debug") or {}
    traces = state.get("debug_traces") or []
    if contains_in_obj(debug, ctx) or contains_in_obj(traces, ctx):
        return True
    return False


def test_debug_and_traces_never_contain_hidden_facts(tmp_path, monkeypatch):
    """last_action_debug and debug_traces in compose_state never include hidden_facts or undiscovered clues."""
    _seed_minimal(tmp_path, monkeypatch)
    session = storage.load_session()
    session["last_action_debug"] = {
        "last_action_type": "chat",
        "player_input": "observe",
        "normalized_action": {"id": "obs", "type": "observe"},
        "resolution_kind": "observe",
        "target_scene": None,
        "resolver_result": {"kind": "observe"},
        "scene_transition": None,
    }
    session["debug_traces"] = [
        {
            "timestamp": "2025-01-01T12:00:00Z",
            "source": "chat",
            "action_type": "chat",
            "raw_input": "observe",
            "normalized_action": {"id": "obs"},
            "resolution": {"kind": "observe"},
            "scene_before": "test_scene",
            "scene_after": "test_scene",
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)

    state = compose_state()

    # Debug payload must not reference hidden_facts or undiscovered clue text
    debug = state.get("debug") or {}
    debug_str = str(debug)
    assert "secret_gm_only_fact" not in debug_str
    assert "another_spoiler" not in debug_str
    assert "undiscovered_clue_1" not in debug_str

    # Traces must not contain spoilers
    for t in state.get("debug_traces") or []:
        trace_str = str(t)
        assert "secret_gm_only_fact" not in trace_str
        assert "another_spoiler" not in trace_str


def test_debug_trace_endpoint_returns_safe_data(tmp_path, monkeypatch):
    """GET /api/debug_trace returns traces and they do not contain hidden_facts."""
    _seed_minimal(tmp_path, monkeypatch)
    session = storage.load_session()
    session["debug_traces"] = [
        {"source": "action", "resolution": {"kind": "observe"}, "raw_input": "look around"}
    ]
    storage._save_json(storage.SESSION_PATH, session)

    client = TestClient(app)
    r = client.get("/api/debug_trace")
    assert r.status_code == 200
    data = r.json()
    assert "traces" in data
    trace_str = str(data["traces"])
    assert "secret_gm_only_fact" not in trace_str


def test_state_includes_debug_when_present(tmp_path, monkeypatch):
    """GET /api/state includes debug and debug_traces when session has last_action_debug."""
    _seed_minimal(tmp_path, monkeypatch)
    session = storage.load_session()
    session["last_action_debug"] = {"player_input": "test", "resolution_kind": "observe"}
    session["debug_traces"] = [{"source": "action"}]
    storage._save_json(storage.SESSION_PATH, session)

    client = TestClient(app)
    r = client.get("/api/state")
    assert r.status_code == 200
    data = r.json()
    assert "debug" in data
    assert data["debug"]["player_input"] == "test"
    assert "debug_traces" in data
    assert len(data["debug_traces"]) >= 1
