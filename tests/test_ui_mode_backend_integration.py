"""Objective #15 Block B — backend integration tests for canonical ui_mode_policy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game import storage
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)


pytestmark = pytest.mark.integration


def _patch_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    # Satisfy startup validation for default bootstrap scenes.
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        (storage.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2),
            encoding="utf-8",
        )


def _seed_minimal_with_spoilers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_storage(tmp_path, monkeypatch)

    scene = default_scene("test_scene")
    scene["scene"]["id"] = "test_scene"
    scene["scene"]["hidden_facts"] = ["secret_gm_only_fact"]
    storage._save_json(storage.scene_path("test_scene"), scene)

    session = default_session()
    session["active_scene_id"] = "test_scene"
    session["visited_scene_ids"] = ["test_scene"]
    session["last_action_debug"] = {"player_input": "dbg", "resolution_kind": "observe"}
    session["debug_traces"] = [{"source": "action", "_final_emission_meta": {"x": 1}}]
    storage._save_json(storage.SESSION_PATH, session)

    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_api_state_projection_player_author_debug_and_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_minimal_with_spoilers(tmp_path, monkeypatch)

    with TestClient(app) as client:
        r0 = client.get("/api/state")
        assert r0.status_code == 200
        d0 = r0.json()
        assert d0.get("ui_mode") == "player"
        assert "public_state" in d0
        assert "author_state" not in d0
        assert "debug_state" not in d0

        r1 = client.get("/api/state?ui_mode=author")
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ui_mode") == "author"
        assert "public_state" in d1
        assert "author_state" in d1
        assert "debug_state" not in d1

        r2 = client.get("/api/state?ui_mode=debug")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("ui_mode") == "debug"
        assert "public_state" in d2
        assert "debug_state" in d2
        assert "author_state" not in d2

        bad = client.get("/api/state?ui_mode=totally_not_a_mode")
        assert bad.status_code == 400


def test_state_leakage_guards_by_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_minimal_with_spoilers(tmp_path, monkeypatch)

    with TestClient(app) as client:
        player = client.get("/api/state").json()
        public_state = player["public_state"]
        public_blob = json.dumps(public_state, sort_keys=True)
        # Player/public must not contain author spoilers or debug lanes.
        assert "secret_gm_only_fact" not in public_blob
        assert "debug_traces" not in public_blob
        assert "_final_emission_meta" not in public_blob
        assert "hidden_facts" not in (public_state.get("scene") or {}).get("scene", {})

        author = client.get("/api/state?ui_mode=author").json()
        author_blob = json.dumps(author.get("author_state") or {}, sort_keys=True)
        assert "hidden_facts" in author_blob
        assert "debug_traces" not in author_blob
        assert "_final_emission_meta" not in author_blob

        debug = client.get("/api/state?ui_mode=debug").json()
        debug_blob = json.dumps(debug.get("debug_state") or {}, sort_keys=True)
        assert "debug_traces" in debug_blob
        assert "_final_emission_meta" in debug_blob
        assert "hidden_facts" not in debug_blob


def test_endpoint_guards_author_debug_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_minimal_with_spoilers(tmp_path, monkeypatch)

    with TestClient(app) as client:
        # Author write endpoints: author only
        r_player = client.post("/api/campaign", json={"title": "t", "ui_mode": "player"})
        assert r_player.status_code == 403
        r_debug = client.post("/api/campaign", json={"title": "t", "ui_mode": "debug"})
        assert r_debug.status_code == 403

        # Debug read endpoints: debug only
        assert client.get("/api/debug_trace").status_code == 403
        assert client.get("/api/debug_trace?ui_mode=author").status_code == 403
        assert client.get("/api/debug_trace?ui_mode=debug").status_code == 200

        # Runtime action endpoints: player only
        assert client.post("/api/chat", json={"text": "hello", "ui_mode": "author"}).status_code == 403
        assert client.post("/api/chat", json={"text": "hello", "ui_mode": "debug"}).status_code == 403
        assert client.post("/api/action", json={"action_type": "exploration", "ui_mode": "author"}).status_code == 403
        assert client.post("/api/action", json={"action_type": "exploration", "ui_mode": "debug"}).status_code == 403


def test_public_log_exposes_player_input_as_public_transcript_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_minimal_with_spoilers(tmp_path, monkeypatch)
    storage.append_log(
        {
            "timestamp": "2026-04-26T12:00:00Z",
            "request": {"chat": "I ask the guard about the missing patrol."},
            "resolution": {
                "prompt": "I ask the guard about the missing patrol.",
                "metadata": {
                    "player_input": "I ask the guard about the missing patrol.",
                    "emission_debug": {"should_not": "ship"},
                },
            },
            "gm_output": {
                "player_facing_text": "The guard glances toward the rain-dark road.",
                "metadata": {"emission_debug": {"should_not": "ship"}},
                "_final_emission_meta": {"should_not": "ship"},
            },
            "log_meta": {"player_input": "I ask the guard about the missing patrol."},
        }
    )

    with TestClient(app) as client:
        r = client.get("/api/log")
        assert r.status_code == 200
        entry = r.json()["entries"][0]

    assert entry["player_input"] == "I ask the guard about the missing patrol."
    assert entry["gm_output"] == {
        "player_facing_text": "The guard glances toward the rain-dark road."
    }
    assert "log_meta" not in entry
    assert "resolution" not in entry
    assert "emission_debug" not in json.dumps(entry)
    assert "_final_emission_meta" not in json.dumps(entry)

