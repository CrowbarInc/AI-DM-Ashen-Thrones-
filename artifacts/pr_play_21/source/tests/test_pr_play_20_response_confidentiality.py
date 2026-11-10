"""Player HTTP boundary regressions: real application, synthetic secrets, no sockets."""
import copy
import json
import os
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import game.api as api
from game import storage as st
from game.opening_presentation_renderer import plan_selecting_required
from game.state_channels import deep_project_public_payload, is_author_key, is_debug_key
from tests.test_pr_play_04_opening_integrity import opening_world, _snap
from tests.test_pr_play_18_contract_alignment import _transport

SENTINEL = "PR_PLAY_20_HIDDEN_SENTINEL"


def _record(name, value):
    if os.environ.get("ASHEN_PR_PLAY_20_EVIDENCE") == "1":
        # No real authored hidden/debug values enter external evidence.
        def sanitize(v, restricted=False):
            if isinstance(v, dict):
                return {k: sanitize(x, restricted or is_author_key(k) or is_debug_key(k)) for k, x in v.items()}
            if isinstance(v, list):
                return [sanitize(x, restricted) for x in v]
            if restricted and isinstance(v, str) and SENTINEL not in v:
                return "[REDACTED]"
            return v
        Path("artifacts/pr_play_20", name).write_text(json.dumps(sanitize(value), indent=2), encoding="utf-8")


@pytest.fixture
def confidential_world(opening_world, monkeypatch):
    original_connect = socket.socket.connect
    def no_network(sock, address):
        # Windows asyncio builds its internal socketpair over loopback.
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect(sock, address)
        raise AssertionError("PR-PLAY-20 forbids network connections")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    campaign = st.load_campaign()
    campaign["character_secret"] = {"public_hint": "A familiar mark", "hidden_truth": SENTINEL}
    campaign["internal_state"] = {"campaign_plan": SENTINEL + "_CAMPAIGN"}
    st._save_json(st.CAMPAIGN_PATH, campaign)
    world = st.load_world()
    world["internal_state"] = {"restricted_fact": SENTINEL + "_WORLD"}
    world["public_test_records"] = [{"name": "Public NPC", "hidden_agenda": SENTINEL + "_NPC"},
                                    {"title": "Public quest", "hidden_details": SENTINEL + "_QUEST"}]
    st.save_world(world)
    scene = st.load_active_scene()
    scene["scene"]["hidden_facts"] = [SENTINEL + "_SCENE"]
    st._save_json(st.scene_path(scene["scene"]["id"]), scene)
    monkeypatch.setattr(api, "log_upstream_api_preflight_at_startup", lambda: None)
    seen = []
    _transport(monkeypatch, seen, lambda kw: plan_selecting_required(kw["input"]))
    return seen


def test_successful_start_serialized_boundary(confidential_world):
    before = _snap()
    campaign_before = copy.deepcopy(st.load_campaign())
    world_before = copy.deepcopy(st.load_world())
    character_before = copy.deepcopy(st.load_character())
    combat_before = copy.deepcopy(st.load_combat())
    with TestClient(api.app) as client:
        response = client.post("/api/start_campaign?ui_mode=player")
        body = response.json()
        public = client.get("/api/state").json()["public_state"]
        repeated = client.post("/api/start_campaign")
    summary = {"mode": "player", "endpoint": "/api/start_campaign", "status": response.status_code,
               "sentinel_in_http": SENTINEL in response.text, "sentinel_in_public_state": SENTINEL in json.dumps(public),
               "sentinel_in_authority": st.load_campaign()["character_secret"]["hidden_truth"] == SENTINEL,
               "mock_dispatches": len(confidential_world), "live_provider_requests": 0,
               "before": before, "after": _snap(), "repeat_status": repeated.status_code}
    baseline = os.environ.get("ASHEN_PR_PLAY_20_BASELINE") == "1"
    _record("baseline_summary.json" if baseline else "offline_summary.json", summary)
    _record("baseline_response.json" if baseline else "repaired_response.json", body)
    _record("public_state.json", public)
    _record("rejected_repeat.json", repeated.json())
    assert response.status_code == 200
    assert len(confidential_world) == 1
    assert st.load_campaign() == campaign_before
    assert st.load_character() == character_before
    assert st.load_combat() == combat_before
    assert st.load_world()["internal_state"] == world_before["internal_state"]
    assert st.load_world()["public_test_records"] == world_before["public_test_records"]
    assert summary["sentinel_in_authority"]
    assert not summary["sentinel_in_public_state"]
    assert repeated.status_code == 409 and SENTINEL not in repeated.text
    assert body["gm_output"]["player_facing_text"] == st.load_log()[-1]["gm_output"]["player_facing_text"]
    assert body["gm_output"]["player_facing_text"]
    assert body["campaign"]["character_secret"]["public_hint"] == "A familiar mark"
    assert body["world"]["public_test_records"] == [{"name": "Public NPC"}, {"title": "Public quest"}]
    assert body["ui"]["campaign_started"] and not body["ui"]["campaign_can_start"]
    assert body["session"]["turn_counter"] == before["turn_counter"] + 1
    assert SENTINEL not in response.text
    assert body == deep_project_public_payload(body)


@pytest.mark.parametrize("endpoint,payload", [("/api/action", {"action_type": "roll_initiative"}),
                                             ("/api/chat", {"text": "OOC: help"})])
def test_ordinary_success_and_rejection(confidential_world, endpoint, payload):
    with TestClient(api.app) as client:
        success = client.post(endpoint, json=payload)
        rejection = client.post("/api/action", json={"action_type": "unsupported"})
    _record("ordinary_" + endpoint.rsplit("/", 1)[-1] + ".json", success.json())
    assert success.status_code == 200 and success.json()["ok"]
    assert SENTINEL not in success.text
    assert success.json() == deep_project_public_payload(success.json())
    assert rejection.json()["ok"] is False and SENTINEL not in rejection.text
    assert st.load_campaign()["character_secret"]["hidden_truth"] == SENTINEL


def test_failed_opening_and_mode_policy(confidential_world, monkeypatch):
    _transport(monkeypatch, [], lambda kw: json.dumps({"selected_entries": []}))
    with TestClient(api.app) as client:
        bad = client.post("/api/start_campaign")
        state = client.get("/api/state")
        for mode in ("debug", "author"):
            denied = client.post("/api/start_campaign?ui_mode=" + mode)
            assert denied.status_code == 403 and SENTINEL not in denied.text
        assert client.get("/api/state?ui_mode=debug").status_code == 403
        assert client.get("/api/state?ui_mode=author").status_code == 403
        # PR-PLAY-21 closes unauthenticated HTTP reads; the internal projection
        # remains available to local author/developer code.
        debug = api._project_state_for_ui_mode(api.compose_state(), "debug")
        author = api._project_state_for_ui_mode(api.compose_state(), "author")
    _record("failed_opening.json", bad.json())
    assert bad.status_code == 422 and SENTINEL not in bad.text
    assert not st.load_session()["campaign_started"] and not st.load_log()
    assert SENTINEL not in state.text and SENTINEL not in json.dumps(debug)
    assert "debug_state" in debug and "author_state" in author
    assert author["author_state"]["campaign"]["character_secret"]["hidden_truth"] == SENTINEL


def test_rejected_turn_with_composed_state(confidential_world, monkeypatch):
    # The two combat-rejection branches return this internal representation.
    # Isolate admission from routing so the HTTP projection cannot be bypassed
    # by an early raw-state return, even without the shared success helper.
    monkeypatch.setattr(api, "chat", lambda *a, **kw: {"ok": False, "error": "You cannot act right now.",
                                                      **api.compose_state()})
    with TestClient(api.app) as client:
        response = client.post("/api/chat", json={"text": "I attack."})
    _record("rejected_composed_turn.json", response.json())
    assert response.status_code == 200 and not response.json()["ok"]
    assert response.json()["error"] == "You cannot act right now."
    assert response.json()["campaign"]["character_secret"]["public_hint"] == "A familiar mark"
    assert SENTINEL not in response.text
