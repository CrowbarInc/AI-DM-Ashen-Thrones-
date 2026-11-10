"""Privileged HTTP reads fail closed; internal projections stay available offline."""
import copy
import json
import os
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import game.api as api
from game import storage as st
from game.api_ui_mode import resolve_requested_ui_mode, UiModePolicyError
from game.opening_presentation_renderer import plan_selecting_required
from tests.test_ui_mode_backend_integration import _seed_minimal_with_spoilers
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_20_response_confidentiality import confidential_world
from tests.test_pr_play_18_contract_alignment import _transport

SENTINEL = "PR_PLAY_21_PRIVILEGED_SENTINEL"


def _record(name, value):
    if os.environ.get("ASHEN_PR_PLAY_21_EVIDENCE") == "1":
        Path("artifacts/pr_play_21", name).write_text(json.dumps(value, indent=2), encoding="utf-8")


@pytest.fixture
def read_world(tmp_path, monkeypatch):
    original_connect = socket.socket.connect
    def no_network(sock, address):
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect(sock, address)  # Windows asyncio socketpair
        raise AssertionError("PR-PLAY-21 forbids external network")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    _seed_minimal_with_spoilers(tmp_path, monkeypatch)
    monkeypatch.setattr(st, "SNAPSHOTS_DIR", st.DATA_DIR / "snapshots")
    scene = st.load_active_scene()
    scene["scene"]["hidden_facts"] = [SENTINEL]
    scene["scene"]["visible_facts"] = ["Public test fact"]
    st._save_json(st.scene_path("test_scene"), scene)
    session = st.load_session()
    session["debug_traces"] = [{"detail": SENTINEL + "_DEBUG"}]
    st.save_session(session)
    st.append_log({"timestamp": "synthetic", "request": {"chat": "Public input"},
                   "gm_output": {"player_facing_text": "Public narration"},
                   "resolution": {"internal_state": SENTINEL + "_LOG"}})
    monkeypatch.setattr(api, "log_upstream_api_preflight_at_startup", lambda: None)
    with TestClient(api.app) as client:
        api.compose_state()  # Complete the existing derived character-name sync.
        yield client


def _authority():
    return copy.deepcopy([st.load_campaign(), st.load_world(), st.load_active_scene(),
                          st.load_character(), st.load_combat(), st.load_session(), st.load_log()])


def test_default_public_and_authority_preservation(read_world):
    before = _authority()
    state = read_world.get("/api/state")
    log = read_world.get("/api/log")
    assert state.status_code == log.status_code == 200
    assert set(state.json()) == {"ui_mode", "public_state"}
    assert state.json()["ui_mode"] == "player"
    assert state.json()["public_state"]["scene"]["scene"]["visible_facts"]
    assert log.json()["entries"][0]["gm_output"]["player_facing_text"] == "Public narration"
    assert log.json()["entries"][0]["player_input"] == "Public input"
    assert SENTINEL not in state.text + log.text
    assert _authority() == before
    assert SENTINEL in json.dumps(before)


@pytest.mark.parametrize("path", ["/api/state", "/api/log", "/api/debug_trace", "/api/snapshots"])
@pytest.mark.parametrize("mode", ["author", "debug"])
def test_privileged_http_denied_before_data_access(read_world, monkeypatch, path, mode):
    before = _authority()
    def forbidden():
        raise AssertionError("Privileged denial must precede state/log loading and projection")
    with monkeypatch.context() as patch:
        for name in ("compose_state", "load_log", "load_session", "list_snapshots"):
            patch.setattr(api, name, forbidden)
        response = read_world.get(path, params={"ui_mode": mode})
    assert response.status_code == 403
    assert response.json() == {"ok": False, "error": "privileged HTTP ui mode is not authorized"}
    assert SENTINEL not in response.text
    assert _authority() == before


@pytest.mark.parametrize("path", ["/api/campaign", "/api/scene", "/api/world"])
@pytest.mark.parametrize("selector", ["ui_mode", "uiMode"])
def test_supported_body_selectors_fail_closed_without_writes(read_world, path, selector):
    before = _authority()
    response = read_world.post(path, json={selector: "author"})
    assert response.status_code == 403 and SENTINEL not in response.text
    assert _authority() == before


@pytest.mark.parametrize("query,status", [
    ("ui_mode=%20author%20", 403), ("ui_mode=debug", 403),
    ("ui_mode=player&ui_mode=author", 403),
    ("ui_mode=author&ui_mode=player", 200), ("ui_mode=unknown", 400),
])
def test_selector_normalization_and_duplicate_queries(read_world, query, status):
    response = read_world.get("/api/state?" + query)
    assert response.status_code == status and SENTINEL not in response.text
    if status == 200:
        assert response.json()["ui_mode"] == "player"
        assert set(response.json()) == {"ui_mode", "public_state"}


def test_origin_and_loopback_do_not_grant_privilege(read_world):
    for origin in ("http://127.0.0.1:8000", "https://untrusted.example"):
        response = read_world.get("/api/state?ui_mode=author", headers={"Origin": origin})
        assert response.status_code == 403 and SENTINEL not in response.text
        assert response.headers["access-control-allow-origin"] == "*"


def test_internal_projection_access_is_preserved(read_world):
    before = _authority()
    state = api.compose_state()
    author = api._project_state_for_ui_mode(state, "author")
    debug = api._project_state_for_ui_mode(state, "debug")
    assert author["author_state"]["scene"]["scene"]["hidden_facts"] == [SENTINEL]
    assert {"detail": SENTINEL + "_DEBUG"} in debug["debug_state"]["debug_traces"]
    assert SENTINEL not in json.dumps(author["public_state"])
    assert _authority() == before


def test_missing_request_is_not_an_authorization_context():
    with pytest.raises(UiModePolicyError):
        resolve_requested_ui_mode(None, {"uiMode": "author"})


def test_offline_initialization_and_ordinary_action(confidential_world, monkeypatch):
    # Reuse PR-PLAY-20's guarded, temporary opening fixture and SDK transport.
    monkeypatch.setattr(st, "SNAPSHOTS_DIR", st.DATA_DIR / "snapshots")
    seen = []
    _transport(monkeypatch, seen, lambda kw: plan_selecting_required(kw["input"]))
    authority = copy.deepcopy(st.load_campaign())
    with TestClient(api.app) as client:
        started = client.post("/api/start_campaign")
        public = client.get("/api/state")
        denied = client.get("/api/state?ui_mode=author")
        action = client.post("/api/action", json={"action_type": "roll_initiative"})
    assert started.status_code == public.status_code == action.status_code == 200
    assert started.json()["ui"]["campaign_started"]
    assert started.json()["gm_output"]["player_facing_text"] == st.load_log()[0]["gm_output"]["player_facing_text"]
    assert started.json()["gm_output"]["player_facing_text"]
    assert action.json()["ok"] and st.load_combat()["in_combat"]
    assert denied.status_code == 403
    assert st.load_campaign() == authority
    for response in (started, public, denied, action):
        assert "PR_PLAY_20_HIDDEN_SENTINEL" not in response.text
    assert len(seen) == 1
    _record("initialization_and_action.json", {
        "start_status": started.status_code, "state_status": public.status_code,
        "privileged_status": denied.status_code, "action_status": action.status_code,
        "campaign_started": True, "opening_published": True, "initiative_started": True,
        "authoritative_campaign_unchanged": True, "mock_dispatches": len(seen), "live_provider_requests": 0,
        "start_response_text": started.text, "public_response_text": public.text,
        "denial_response_text": denied.text, "action_response_text": action.text,
        "public_response_keys": sorted(public.json()), "start_response_keys": sorted(started.json()),
        "action_response_keys": sorted(action.json())})
