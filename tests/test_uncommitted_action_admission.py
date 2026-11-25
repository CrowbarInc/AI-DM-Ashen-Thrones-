"""Negated and conditional player acts must not reach execution.

The coverage record already calls these non-execution. Admission has to
withhold them before dialogue, a social check, or a turn advance.
"""
import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate


def _quiet():
    session = storage.load_session()
    return {
        "turn": session.get("turn_counter"),
        "scene": session.get("active_scene_id"),
        "clocks": copy.deepcopy(session.get("clocks")),
        "runtime": copy.deepcopy(session.get("npc_runtime")),
        "receipts": copy.deepcopy(session.get("mechanical_action_receipts")),
        "inventory": copy.deepcopy(storage.load_character().get("inventory")),
    }


def _chat(client, text, request_id):
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": text, "client_request_id": request_id},
    )
    body = response.json()
    visible = (body.get("gm_output") or {}).get("player_facing_text") or ""
    return response.status_code, visible


@pytest.fixture()
def gate(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    for key in (
        "ASHEN_DISABLE_PROVIDER_CALLS",
        "ASHEN_DISABLE_LIVE_INTERPRETATION",
        "ASHEN_DISABLE_EXPRESSION_GENERATION",
        "ASHEN_DISABLE_PROVIDER_RETRIES",
        "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT",
    ):
        monkeypatch.setenv(key, "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    before = _quiet()
    providers = len(snapshot()["records"])
    with TestClient(app) as client:
        yield client, before, providers
    _LANES.clear()


def test_negated_persuade_does_not_speak_or_commit(gate):
    client, before, providers = gate
    code, visible = _chat(client, "I do not persuade the guard captain.", "negated-persuade")
    after = _quiet()
    assert code == 200
    assert "Nothing has been attempted" in visible
    assert "d20=" not in visible
    assert "will not carry out" not in visible.casefold()
    assert "Provider calls are disabled" not in visible
    assert after["turn"] == before["turn"]
    assert after["scene"] == before["scene"]
    assert after["clocks"] == before["clocks"]
    assert after["runtime"] == before["runtime"]
    assert after["receipts"] == before["receipts"]
    assert after["inventory"] == before["inventory"]
    assert len(snapshot()["records"]) == providers


def test_conditional_persuade_does_not_advance(gate):
    client, before, providers = gate
    code, visible = _chat(
        client,
        "If he is listening, I try to persuade the guard captain.",
        "conditional-persuade",
    )
    after = _quiet()
    assert code == 200
    assert "Nothing has been attempted" in visible
    assert "only conditional" in visible
    assert "d20=" not in visible
    assert "Provider calls are disabled" not in visible
    assert after["turn"] == before["turn"]
    assert after["clocks"] == before["clocks"]
    assert after["runtime"] == before["runtime"]
    assert after["receipts"] == before["receipts"]
    assert len(snapshot()["records"]) == providers


def test_try_not_to_persuade_is_not_a_physical_attempt(gate):
    client, before, providers = gate
    code, visible = _chat(client, "I try not to persuade the guard captain.", "try-not")
    after = _quiet()
    assert code == 200
    assert visible == "You do not do that. Nothing has been attempted."
    assert "accessible target" not in visible
    assert after["turn"] == before["turn"]
    assert after["runtime"] == before["runtime"]
    assert len(snapshot()["records"]) == providers


def test_negated_social_then_real_check_still_commits(gate):
    client, before, _providers = gate
    code, visible = _chat(client, "I don't try to persuade the tavern runner.", "negated-runner")
    assert code == 200
    assert "Nothing has been attempted" in visible
    assert "d20=" not in visible
    assert _quiet()["turn"] == before["turn"]
    code, visible = _chat(client, "I try to persuade the guard captain.", "real-check")
    assert code == 200
    assert "vs DC" in visible
    assert _quiet()["receipts"]


def test_later_affirmative_travel_is_not_withheld_by_an_earlier_negation(gate):
    client, before, _providers = gate
    code, visible = _chat(client, "I don't wait; I enter Cinderwatch.", "negated-wait-enter")
    assert code == 200
    assert storage.load_session()["active_scene_id"] == "market_quarter"
    assert "Nothing has been attempted" not in visible
    assert storage.load_session()["turn_counter"] == before["turn"] + 1


def test_travel_negation_keeps_its_existing_message(gate):
    client, before, _providers = gate
    code, visible = _chat(client, "I won't enter Cinderwatch.", "stay")
    assert code == 200
    assert visible == "You stay where you are. Nothing has been attempted."
    assert storage.load_session()["active_scene_id"] == before["scene"]
    assert storage.load_session()["turn_counter"] == before["turn"]
