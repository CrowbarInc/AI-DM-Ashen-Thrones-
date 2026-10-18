"""PR-CK: ordinary gameplay must not default to the social resolver.

These checks stay on the existing resolution contract and ordinary selector.
They do not add a second classifier.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.discourse_state import DISCOURSE_FOCUS_KEY, SLOT_INTERLOCUTOR
from game.ordinary_semantic_ownership import select_ordinary_resolver, stage_permitted
from game.resolution_contract import construct_resolution_contract
from tests.helpers.turn_pipeline_http_fixtures import FAKE_GPT_RESPONSE, _seed_shared_world


def _route(text: str, session: dict | None = None) -> dict:
    contract = construct_resolution_contract(player_text=text, session=session, scene_id="scene_investigate")
    payload = contract.as_dict()
    resolver, family = select_ordinary_resolver(payload)
    return {
        "operation": payload.get("operation"),
        "subject": (payload.get("construction") or {}).get("resolution_subject"),
        "resolver": resolver,
        "family": family,
        "interlocutor": payload.get("interlocutor_id") or None,
        "exploration": stage_permitted(resolver, "exploration", payload),
        "passive_wait": stage_permitted(resolver, "passive_wait", payload),
        "social": stage_permitted(resolver, "social", payload),
    }


def _focus(npc_id: str = "baker") -> dict:
    return {
        DISCOURSE_FOCUS_KEY: {
            "version": 1,
            "scene_id": "scene_investigate",
            SLOT_INTERLOCUTOR: {"id": npc_id, "label": "the baker", "scene_id": "scene_investigate"},
        }
    }


EXPLORATION = (
    "I investigate the desk.",
    "I search the desk.",
    "I examine the desk.",
    "I look through the papers.",
    "I inspect the contents of the drawer.",
)

PASSIVE = (
    "I wait.",
    "I wait for a while.",
    "I remain silent and observe.",
    "I stay here and watch.",
)

NARRATION = (
    "Describe the gate.",
    "Where are we?",
    "hello there",
    "The rain is cold.",
)

SOCIAL = (
    "I ask the baker which loaf he recommends.",
    "I turn to the guard and ask who passed through.",
    "I ask the merchant whether the shop is open.",
    "What happened to the patrol?",
    "What have you heard?",
    "Where are you?",
    "I talk to the tavern runner.",
    "Tell me plainly.",
    "I persuade the gate guard to let me pass.",
)


@pytest.mark.parametrize("text", EXPLORATION)
def test_exploration_language_selects_exploration(text: str) -> None:
    route = _route(text)
    assert route["resolver"] == "exploration"
    assert route["exploration"] is True
    assert route["social"] is False
    assert route["interlocutor"] is None
    assert route["operation"] in {"inspect", "perceive"}


@pytest.mark.parametrize("text", PASSIVE)
def test_passive_language_does_not_select_social(text: str) -> None:
    route = _route(text)
    assert route["resolver"] != "social"
    assert route["social"] is False
    assert route["passive_wait"] is True
    assert route["interlocutor"] is None


@pytest.mark.parametrize("text", NARRATION)
def test_narration_and_unmatched_text_do_not_invent_a_social_addressee(text: str) -> None:
    route = _route(text)
    assert route["resolver"] != "social"
    assert route["subject"] != "social"
    assert route["interlocutor"] is None
    assert route["social"] is False


def test_scene_focus_alone_does_not_make_a_wait_social() -> None:
    route = _route("I wait.", _focus())
    assert route["resolver"] != "social"
    assert route["interlocutor"] is None


@pytest.mark.parametrize("text", SOCIAL)
def test_addressed_and_informational_questions_stay_social(text: str) -> None:
    route = _route(text)
    assert route["resolver"] == "social"
    assert route["operation"] == "ask"
    assert route["subject"] == "social"


def test_followup_with_an_active_interlocutor_keeps_that_addressee() -> None:
    route = _route("Who attacked them?", _focus("gate_guard"))
    assert route["resolver"] == "social"
    assert route["subject"] == "social"
    assert route["interlocutor"] == "gate_guard"


def test_place_and_world_action_keep_their_resolvers() -> None:
    place = _route("Where is the harbor?")
    assert place["resolver"] == "adjudication"
    assert place["subject"] == "place_location"
    door = _route("I open the door.")
    assert door["resolver"] == "world_action"
    assert door["operation"] == "act"


def test_compound_search_and_ask_stays_unresolved() -> None:
    route = _route("I search the yard and inquire who keeps the key.")
    assert route["operation"] == "unresolved"
    assert route["resolver"] != "exploration"
    assert route["resolver"] != "social"


def test_quoted_social_with_subordinate_investigation_stays_social() -> None:
    route = _route('I nod. "Thank you," I say, before investigating further.')
    assert route["resolver"] == "social"
    assert route["operation"] == "ask"


def test_chat_search_can_discover_the_authored_desk_clue(tmp_path, monkeypatch) -> None:
    _seed_shared_world(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *_args, **_kwargs: FAKE_GPT_RESPONSE)
    client = TestClient(app)
    response = client.post("/api/chat", json={"text": "I search the desk."})
    assert response.status_code == 200
    body = response.json()
    assert body["resolution"]["kind"] == "discover_clue"
    runtime = body["session"]["scene_runtime"]["scene_investigate"]
    assert "A map indicates patrol locations." in (runtime.get("discovered_clues") or [])


def test_chat_investigation_of_an_unclued_object_discovers_nothing(tmp_path, monkeypatch) -> None:
    _seed_shared_world(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *_args, **_kwargs: FAKE_GPT_RESPONSE)
    client = TestClient(app)
    response = client.post("/api/chat", json={"text": "I investigate the iron latch."})
    assert response.status_code == 200
    body = response.json()
    runtime = body["session"]["scene_runtime"]["scene_investigate"]
    assert "A map indicates patrol locations." not in (runtime.get("discovered_clues") or [])
    assert body["resolution"].get("kind") != "discover_clue"


def test_action_and_chat_observation_are_not_social(tmp_path, monkeypatch) -> None:
    _seed_shared_world(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *_args, **_kwargs: FAKE_GPT_RESPONSE)
    client = TestClient(app)
    chat = client.post("/api/chat", json={"text": "Describe the gate."})
    assert chat.status_code == 200
    chat_body = chat.json()
    metadata = (chat_body.get("resolution") or {}).get("metadata") or {}
    contract = metadata.get("resolution_contract") or {}
    assert metadata.get("selected_resolver") != "social"
    assert contract.get("operation") != "ask"
    assert not contract.get("interlocutor_id")
