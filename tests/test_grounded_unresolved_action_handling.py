"""Admission through real HTTP: authority, publication, retry and disclosure."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.conversational_orchestration import deterministic_conversational_decision
from game.physical_adjudication import disabled_action_disposition
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import CANARIES, seed_gate


@pytest.fixture(autouse=True)
def isolated_request_lane():
    from game.integrated_play import _LANES
    _LANES.clear()
    yield
    _LANES.clear()


def gameplay():
    session = storage.load_session()
    return copy.deepcopy({
        "character": storage.load_character(), "world": storage.load_world(),
        "scene": storage.load_active_scene(), "combat": storage.load_combat(),
        "turn": session.get("turn_counter"), "clocks": session.get("clocks"),
        "scene_state": session.get("scene_state"),
        "publication": session.get("last_publication"),
    })


@pytest.mark.parametrize("text,terms", [
    ("I move the rain barrel out of the way.", ("rain barrel", "target")),
    ("I climb over the notice board.", ("notice board", "authorize")),
    ("I open the gate.", ("gate", "target")),
    ("I back away from the notice board.", ("notice board", "authorize")),
    ("We move back from the bronze beacon.", ("bronze beacon", "target")),
])
def test_unadmitted_request_has_context_without_gameplay_effects(tmp_path, monkeypatch, text, terms):
    seed_gate(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    before = gameplay()
    providers = len(snapshot()["records"])
    with TestClient(app) as client:
        first = client.post('/api/chat?ui_mode=player', json={"text": text, "client_request_id": "nonexecution"})
        second = client.post('/api/chat?ui_mode=player', json={"text": text, "client_request_id": "nonexecution"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    visible = first.json()["gm_output"]["player_facing_text"]
    assert all(term in visible.casefold() for term in terms)
    assert "Nothing was carried out" in visible
    assert all(canary not in visible for canary in CANARIES)
    assert gameplay() == before
    assert len(snapshot()["records"]) == providers


def test_ambiguous_alias_outside_gate_requires_one_question(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    scene = storage.load_active_scene()
    scene["scene"].update(id="workshop", location="Workshop", interactables=[
        {"id": "red_crate", "label": "Red crate", "aliases": ["crate"]},
        {"id": "blue_crate", "label": "Blue crate", "aliases": ["crate"]},
        {"id": "hidden_crate", "label": "CANARY_SECRET_CRATE", "aliases": ["crate"], "hidden": True},
    ])
    session = storage.load_session()
    session["active_scene_id"] = "workshop"
    storage.save_session(session)
    # Use the existing loader contract to supply a separately authored scene.
    monkeypatch.setattr("game.api.load_active_scene", lambda: copy.deepcopy(scene))
    monkeypatch.setattr(storage, "load_active_scene", lambda: copy.deepcopy(scene))
    before = gameplay()
    with TestClient(app) as client:
        body = client.post('/api/chat?ui_mode=player', json={"text": "I push the crate."}).json()
    text = body["gm_output"]["player_facing_text"]
    assert text.count("?") == 1
    assert "Red crate" in text and "Blue crate" in text
    assert "CANARY_SECRET_CRATE" not in text
    assert gameplay() == before


def test_routes_use_public_current_authority_only():
    scene = {"scene": {"id": "workshop", "exits": [
        {"id": "quay", "label": "Brass Quay"},
        {"id": "secret", "label": "CANARY_SECRET_EXIT", "hidden": True},
    ]}}
    decision = deterministic_conversational_decision(
        player_text="Which exits are available?", scene=scene, session={}, world={},
    )
    assert decision.disposition == "GROUNDED_INFORMATION"
    assert "Brass Quay" in decision.player_facing_text
    assert "CANARY" not in decision.player_facing_text
    assert not decision.requires_authoritative_execution


def test_enabled_physics_keeps_its_owner(monkeypatch):
    from tests.test_pr_play_76_physical import enable, stage
    enable(monkeypatch)
    session = stage()[0]
    assert disabled_action_disposition("I push the crate.", session, {"scene": {"id": "yard"}}) is None
