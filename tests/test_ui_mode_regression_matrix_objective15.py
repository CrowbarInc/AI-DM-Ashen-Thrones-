"""Objective #15 hardening: ui_mode separation regression matrix.

This suite is intentionally table-driven and focused on preventing cross-mode contamination:
- exact `/api/state` envelope keys per ui_mode
- endpoint lockouts (author/debug/runtime)
- deep projection strips nested author/debug keys from public_state
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

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


def _seed_minimal_world(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)

    scene = default_scene("test_scene")
    scene["scene"]["id"] = "test_scene"
    scene["scene"]["visible_facts"] = ["a public fact"]
    scene["scene"]["hidden_facts"] = ["author-only spoiler: hidden_facts must not leak"]
    # Intentionally embed debug-shaped keys into scene payload to verify deep projection.
    scene["scene"]["debug"] = {"should_not": "appear"}
    scene["scene"]["debug_traces"] = [{"x": 1}]
    storage._save_json(storage.scene_path("test_scene"), scene)

    session = default_session()
    session["active_scene_id"] = "test_scene"
    session["visited_scene_ids"] = ["test_scene"]
    # Intentionally add debug-shaped keys into session to verify deep projection.
    session["debug_traces"] = [{"trace_id": "t1"}]
    session["last_action_debug"] = {"player_input": "noop", "_final_emission_meta": {"x": 1}}
    storage._save_json(storage.SESSION_PATH, session)

    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _stringify(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True)
    except Exception:
        return str(obj)


def _assert_no_substrings(obj: Any, forbidden: Iterable[str]) -> None:
    blob = _stringify(obj)
    for s in forbidden:
        assert s not in blob


def _assert_no_forbidden_keys(obj: Any, forbidden_keys: set[str]) -> None:
    def walk(v: Any) -> None:
        if v is None:
            return
        if isinstance(v, list):
            for x in v:
                walk(x)
            return
        if isinstance(v, dict):
            for k, vv in v.items():
                if isinstance(k, str) and k in forbidden_keys:
                    raise AssertionError(f"forbidden key leaked into public_state: {k!r}")
                walk(vv)

    walk(obj)


def test_state_envelope_keys_exact_per_mode(tmp_path, monkeypatch) -> None:
    _seed_minimal_world(tmp_path, monkeypatch)
    client = TestClient(app)

    # player: exact shipped keys
    r_p = client.get("/api/state?ui_mode=player")
    assert r_p.status_code == 200
    p = r_p.json()
    assert set(p.keys()) == {"ui_mode", "public_state"}
    assert p["ui_mode"] == "player"

    # author: exact shipped keys
    r_a = client.get("/api/state?ui_mode=author")
    assert r_a.status_code == 200
    a = r_a.json()
    assert set(a.keys()) == {"ui_mode", "public_state", "author_state"}
    assert a["ui_mode"] == "author"

    # debug: exact shipped keys
    r_d = client.get("/api/state?ui_mode=debug")
    assert r_d.status_code == 200
    d = r_d.json()
    assert set(d.keys()) == {"ui_mode", "public_state", "debug_state"}
    assert d["ui_mode"] == "debug"


def test_unknown_ui_mode_fails_closed(tmp_path, monkeypatch) -> None:
    _seed_minimal_world(tmp_path, monkeypatch)
    client = TestClient(app)

    r = client.get("/api/state?ui_mode=not_a_real_mode")
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False
    assert "unknown ui mode" in (body.get("error") or "").lower()


def test_public_state_deep_projection_strips_nested_author_and_debug_leakage(tmp_path, monkeypatch) -> None:
    _seed_minimal_world(tmp_path, monkeypatch)
    client = TestClient(app)

    public = client.get("/api/state?ui_mode=player").json()["public_state"]

    # Key-shaped deep stripping: forbidden author/debug *keys* must not appear anywhere in public_state.
    _assert_no_forbidden_keys(
        public,
        forbidden_keys={"hidden_facts", "debug", "debug_traces", "_final_emission_meta"},
    )
    # Content-shaped stripping: seeded spoiler/debug values must not appear either.
    _assert_no_substrings(public, forbidden=("author-only spoiler", "should_not"))


@dataclass(frozen=True, slots=True)
class _EndpointCase:
    name: str
    method: str
    path: str
    ui_mode: str
    json_body: dict[str, Any] | None
    expected_status: int


def _request(client: TestClient, case: _EndpointCase):
    url = f"{case.path}?ui_mode={case.ui_mode}"
    if case.method == "GET":
        return client.get(url)
    if case.method == "POST":
        return client.post(url, json=case.json_body or {})
    raise AssertionError(f"unsupported method: {case.method}")


@pytest.mark.parametrize(
    "case",
    [
        # --- player mode forbids author endpoints ---
        _EndpointCase("player forbids POST /api/campaign", "POST", "/api/campaign", "player", {"title": "x"}, 403),
        _EndpointCase("player forbids POST /api/scene", "POST", "/api/scene", "player", {"scene": {"id": "x"}}, 403),
        _EndpointCase("player forbids POST /api/world", "POST", "/api/world", "player", {"world": {}}, 403),
        # --- player mode forbids debug endpoints ---
        _EndpointCase("player forbids GET /api/debug_trace", "GET", "/api/debug_trace", "player", None, 403),
        # --- author mode forbids debug endpoints and runtime action endpoints ---
        _EndpointCase("author forbids GET /api/debug_trace", "GET", "/api/debug_trace", "author", None, 403),
        _EndpointCase("author forbids POST /api/action", "POST", "/api/action", "author", {"action_type": "freeform", "intent": "x"}, 403),
        _EndpointCase("author forbids POST /api/chat", "POST", "/api/chat", "author", {"text": "hello"}, 403),
        # --- debug mode forbids author endpoints and runtime action endpoints ---
        _EndpointCase("debug forbids POST /api/campaign", "POST", "/api/campaign", "debug", {"title": "x"}, 403),
        _EndpointCase("debug forbids POST /api/scene", "POST", "/api/scene", "debug", {"scene": {"id": "x"}}, 403),
        _EndpointCase("debug forbids POST /api/world", "POST", "/api/world", "debug", {"world": {}}, 403),
        _EndpointCase("debug forbids POST /api/action", "POST", "/api/action", "debug", {"action_type": "freeform", "intent": "x"}, 403),
        _EndpointCase("debug forbids POST /api/chat", "POST", "/api/chat", "debug", {"text": "hello"}, 403),
        # --- allowed seams (sanity checks) ---
        _EndpointCase("author allows POST /api/scene", "POST", "/api/scene", "author", {"scene": {"id": "test_scene"}}, 200),
        _EndpointCase("debug allows GET /api/debug_trace", "GET", "/api/debug_trace", "debug", None, 200),
        _EndpointCase("player allows GET /api/log", "GET", "/api/log", "player", None, 200),
    ],
    ids=lambda c: c.name,
)
def test_endpoint_lockout_matrix(tmp_path, monkeypatch, case: _EndpointCase) -> None:
    _seed_minimal_world(tmp_path, monkeypatch)
    client = TestClient(app)

    r = _request(client, case)
    assert r.status_code == case.expected_status
    if r.status_code in (400, 403):
        body = r.json()
        assert body.get("ok") is False
        assert isinstance(body.get("error"), str) and body["error"]

