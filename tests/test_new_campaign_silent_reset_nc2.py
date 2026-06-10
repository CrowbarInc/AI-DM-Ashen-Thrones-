"""NC2: New Campaign must not imply a GM turn — empty transcript until explicit player input."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
from game.api import app
from game.storage import append_log, load_log
from tests.helpers.turn_pipeline_http_fixtures import FAKE_GPT_RESPONSE, _seed_campaign_start_storage

pytestmark = pytest.mark.integration


def test_new_campaign_response_and_log_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_campaign_start_storage(tmp_path, monkeypatch)
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
    _seed_campaign_start_storage(tmp_path, monkeypatch)
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
    _seed_campaign_start_storage(tmp_path, monkeypatch)
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
