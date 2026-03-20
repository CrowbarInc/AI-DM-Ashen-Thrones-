"""Tests for FastAPI lifespan startup and UTC timestamp handling."""
from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.utils import utc_iso_now


def test_utc_iso_now_returns_valid_iso_format():
    """utc_iso_now() returns parseable ISO timestamp ending with Z."""
    ts = utc_iso_now()
    assert isinstance(ts, str)
    assert ts.endswith("Z")
    # Match ISO 8601: 2025-03-16T12:34:56.789012Z or 2025-03-16T12:34:56+00:00
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts)
    # Should be parseable (Z is recognized by fromisoformat in Python 3.11+, or we can replace)
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.tzinfo.utcoffset(None) == timezone.utc.utcoffset(None)


def test_utc_iso_now_preserves_existing_format():
    """Timestamp format is compatible with existing persisted format (ISO + Z suffix)."""
    ts = utc_iso_now()
    # Same shape as previous datetime.utcnow().isoformat() + 'Z'
    assert "." in ts or "Z" in ts
    assert ts[-1] == "Z"


def test_lifespan_startup_initializes_app(tmp_path, monkeypatch):
    """FastAPI app starts with lifespan; /api/state succeeds after startup (data files exist)."""
    import game.storage as st
    from game.defaults import default_scene
    import json

    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "SCENES_DIR", tmp_path / "data" / "scenes")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "CAMPAIGN_PATH", st.DATA_DIR / "campaign.json")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "CONDITIONS_PATH", st.DATA_DIR / "conditions.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    # Seed scenes required by ensure_data_files_exist (frontier_gate references market_quarter, old_milestone)
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        path = st.SCENES_DIR / f"{sid}.json"
        if not path.exists():
            path.write_text(json.dumps(default_scene(sid), indent=2), encoding="utf-8")

    with TestClient(app) as client:
        # Lifespan runs on context enter; ensure_data_files_exist creates default files
        resp = client.get("/api/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "campaign" in data
    assert "session" in data
    assert "character" in data


def test_save_session_sets_last_saved_at(tmp_path, monkeypatch):
    """save_session sets last_saved_at with valid UTC timestamp."""
    import game.storage as st

    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "CAMPAIGN_PATH", st.DATA_DIR / "campaign.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "CONDITIONS_PATH", st.DATA_DIR / "conditions.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)

    session = st.load_session()
    st.save_session(session)
    loaded = st.load_session()
    assert "last_saved_at" in loaded
    ts = loaded["last_saved_at"]
    assert isinstance(ts, str)
    assert ts.endswith("Z")
    # Parseable
    datetime.fromisoformat(ts.replace("Z", "+00:00"))
