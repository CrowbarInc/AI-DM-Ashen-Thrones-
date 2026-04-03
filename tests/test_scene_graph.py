"""Tests for scene graph enforcement: valid/invalid transitions, affordance filtering, lint."""
from game import storage
from game.api import app
from game.exploration import resolve_exploration_action
from game.scene_graph import build_scene_graph, is_transition_valid, get_reachable_from
from game.scene_actions import normalize_scene_action
from game.defaults import default_scene, default_session, default_world, default_character, default_campaign, default_combat, default_conditions
from game.affordances import get_available_affordances
from game.scene_lint import validate_scene
from fastapi.testclient import TestClient


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


def _seed_three_scenes(tmp_path, monkeypatch):
    """Scene A exits to B. Scene B exits to A and C. Scene C has no exits to A."""
    _patch_storage(tmp_path, monkeypatch)
    # A -> B
    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)
    # B -> A, C
    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    sb["scene"]["exits"] = [
        {"label": "To A", "target_scene_id": "scene_a"},
        {"label": "To C", "target_scene_id": "scene_c"},
    ]
    storage._save_json(storage.scene_path("scene_b"), sb)
    # C -> B only (no direct path A->C)
    sc = default_scene("scene_c")
    sc["scene"]["id"] = "scene_c"
    sc["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_c"), sc)

    session = default_session()
    session["active_scene_id"] = "scene_a"
    session["visited_scene_ids"] = ["scene_a", "scene_b", "scene_c"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_valid_transition_to_connected_scene_succeeds(tmp_path, monkeypatch):
    """Transition from A to B (connected via exit) resolves and activates."""
    _seed_three_scenes(tmp_path, monkeypatch)

    def fake_gpt(m):
        return {"player_facing_text": "You arrive.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "exploration_action": {
                    "id": "go-b",
                    "label": "Go: To B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to B.",
                },
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["session"]["active_scene_id"] == "scene_b"
    assert data["scene"]["scene"]["id"] == "scene_b"
    assert data.get("resolution", {}).get("resolved_transition") is True


def test_invalid_transition_to_unconnected_scene_fails(tmp_path, monkeypatch):
    """Transition from A to C (no direct exit A->C) is rejected; player stays in A."""
    _seed_three_scenes(tmp_path, monkeypatch)

    def fake_gpt(m):
        return {"player_facing_text": "You cannot reach that place from here.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "exploration_action": {
                    "id": "go-c",
                    "label": "Go: To C",
                    "type": "scene_transition",
                    "targetSceneId": "scene_c",
                    "prompt": "I go to C.",
                },
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    # Scene did NOT change
    assert data["session"]["active_scene_id"] == "scene_a"
    assert data["scene"]["scene"]["id"] == "scene_a"
    assert data.get("resolution", {}).get("resolved_transition") is False
    # Hint should indicate blocked path
    hint = data.get("resolution", {}).get("hint", "")
    assert "not reachable" in hint or "blocked" in hint.lower() or "path" in hint.lower()


def test_freeform_travel_intent_respects_graph(tmp_path, monkeypatch):
    """Free text 'go to B' from scene A matches exit 'To B' and transitions (graph allows A->B)."""
    _seed_three_scenes(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: {"player_facing_text": "You arrive at B.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""})
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "go to B"})
    assert r.status_code == 200
    data = r.json()
    assert data["session"]["active_scene_id"] == "scene_b"
    assert data.get("resolution", {}).get("resolved_transition") is True


def test_scene_lint_catches_invalid_exit_targets():
    """Scene lint reports error when exit points to missing scene."""
    known = {"scene_a", "scene_b"}
    scene = {
        "scene": {
            "id": "scene_a",
            "exits": [
                {"label": "To B", "target_scene_id": "scene_b"},
                {"label": "To missing", "target_scene_id": "nonexistent"},
            ],
        }
    }
    result = validate_scene(scene, known)
    assert "errors" in result
    assert any("nonexistent" in e for e in result["errors"])
    assert any("scene_a" in e or "exit" in e.lower() for e in result["errors"])


def test_build_scene_graph_derives_from_exits(tmp_path, monkeypatch):
    """Graph is correctly built from scene exits."""
    _seed_three_scenes(tmp_path, monkeypatch)
    graph = build_scene_graph(storage.list_scene_ids, storage.load_scene)
    assert "scene_a" in graph
    assert "scene_b" in graph
    assert "scene_c" in graph
    assert graph["scene_a"] == {"scene_b"}
    assert "scene_a" in graph["scene_b"]
    assert "scene_c" in graph["scene_b"]
    assert graph["scene_c"] == {"scene_b"}


def test_affordances_filter_invalid_transitions(tmp_path, monkeypatch):
    """Scene_transition affordances to unreachable scenes are filtered out."""
    _seed_three_scenes(tmp_path, monkeypatch)
    graph = build_scene_graph(storage.list_scene_ids, storage.load_scene)
    scene = storage.load_active_scene()
    session = storage.load_session()
    world = storage.load_world()
    known = set(storage.list_scene_ids())
    # From scene_a, reachable = {scene_b}. Not scene_c.
    affs = get_available_affordances(
        scene, session, world,
        list_scene_ids_fn=storage.list_scene_ids,
        scene_graph=graph,
    )
    transition_affs = [a for a in affs if (a.get("type") or "").strip().lower() == "scene_transition"]
    targets = [a.get("targetSceneId") or a.get("target_scene_id") for a in transition_affs]
    assert "scene_b" in targets
    assert "scene_c" not in targets
