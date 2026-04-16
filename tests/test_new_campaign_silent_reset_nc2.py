"""NC2: New Campaign must not imply a GM turn — empty transcript until explicit player input."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.storage as st
from game.api import app
from game.defaults import default_scene
from game.storage import append_log, load_log
from tests.test_turn_pipeline_shared import FAKE_GPT_RESPONSE

pytestmark = pytest.mark.integration


def _patch_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path
    monkeypatch.setattr(st, "BASE_DIR", base)
    monkeypatch.setattr(st, "DATA_DIR", base / "data")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "CAMPAIGN_PATH", st.DATA_DIR / "campaign.json")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "CONDITIONS_PATH", st.DATA_DIR / "conditions.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def test_new_campaign_response_and_log_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    append_log(
        {
            "timestamp": "2099-01-01T00:00:00Z",
            "gm_output": {"player_facing_text": "stale narration"},
        }
    )
    assert len(load_log()) == 1

    with TestClient(app) as client:
        nc = client.post("/api/new_campaign")
        assert nc.status_code == 200
        body = nc.json()
        assert body.get("status") == "ok"
        assert body.get("silent_reset_no_implicit_transcript") is True
        assert body.get("transcript_entry_count_after_reset") == 0

        lg = client.get("/api/log")
        assert lg.status_code == 200
        assert lg.json().get("entries") == []


def test_state_reload_after_new_campaign_does_not_persist_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read-only hydration must not append session_log rows (regression guard)."""
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    append_log({"timestamp": "t", "gm_output": {"player_facing_text": "x"}})
    assert load_log()

    def _forbidden_append_log(_entry: dict[str, Any]) -> None:
        raise AssertionError("append_log must not run during /api/state or /api/log hydration")

    monkeypatch.setattr(api_mod, "append_log", _forbidden_append_log)

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        for _ in range(3):
            st_r = client.get("/api/state")
            assert st_r.status_code == 200
            log_r = client.get("/api/log")
            assert log_r.status_code == 200
            assert log_r.json().get("entries") == []


def test_explicit_start_campaign_chat_still_produces_opening_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: dict(FAKE_GPT_RESPONSE))

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        chat = client.post("/api/chat", json={"text": "start the campaign"})
    assert chat.status_code == 200
    data = chat.json()
    assert data.get("ok") is True
    assert data.get("resolution", {}).get("kind") == "scene_opening"

    entries = load_log()
    assert len(entries) == 1
    assert entries[0].get("resolution", {}).get("kind") == "scene_opening"
