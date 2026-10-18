"""PR-DY production chat uses the existing interpretation contract. No live provider calls."""

from __future__ import annotations

import json

import pytest

from experiments.pr_dq.world import LANTERN_ID, MARA_ID
from game import storage
from game.api import chat
from game.models import ChatRequest
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution, _seed_pr_du_world

pytestmark = pytest.mark.unit


def _payload(mode: str, status: str, operations: list[tuple[str, str | None]], *, question: str = "") -> dict:
    components = [
        {
            "order": index,
            "description": "described attempt",
            "target_ref": target,
            "operation_class": operation,
        }
        for index, (operation, target) in enumerate(operations, start=1)
    ]
    return {
        "communication_mode": mode,
        "interpretation_status": status,
        "player_intent": {"summary": "A described attempt."},
        "asserted_premises": [],
        "requested_outcomes": [],
        "action_components": components,
        "references": {
            "permitted_entity_ids": [target for _operation, target in operations if target],
            "unresolved_references": [],
        },
        "clarification_question": question,
        "correction": {"subject": "NONE", "note": ""},
    }


def _enable_live(monkeypatch):
    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    monkeypatch.delenv("ASHEN_DISABLE_PROVIDER_CALLS", raising=False)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")


def _install_interpretation(monkeypatch, payload: dict | str, calls: list):
    def _request(messages, *, estimated_input):
        calls.append({"messages": messages, "estimated_input": estimated_input})
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return {
            "ok": True,
            "sent": True,
            "text": text,
            "usage": {
                "purpose": "interpretation",
                "sent": True,
                "model": "gpt-4.1-mini",
                "input_tokens": 12,
                "output_tokens": 8,
                "total_tokens": 20,
            },
        }

    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", _request)


def test_pr_dy_live_inspect_reaches_resolver_without_parser_fallback(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    calls = []
    narration = []
    _install_interpretation(
        monkeypatch,
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", LANTERN_ID)]),
        calls,
    )
    def _narrate(messages, **_kwargs):
        narration.append(messages)
        return _fake_gm_for_resolution(messages)

    monkeypatch.setattr("game.api.call_gpt", _narrate)

    data = chat(ChatRequest(text="I take a closer look at the courtyard lantern.", ui_mode="player"))

    assert data["ok"] is True
    assert len(calls) == 1
    assert data["resolution"]["action_id"] == LANTERN_ID
    assert data["resolution"]["metadata"]["live_chat_interpretation"]["status"] == "accepted"
    assert storage.load_session()["turn_counter"] == 1
    assert narration


def test_pr_dy_rejected_interpretation_does_not_fall_through(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = storage.load_session()["turn_counter"]
    calls = []
    _install_interpretation(
        monkeypatch,
        _payload("IN_WORLD_ACTION", "UNSUPPORTED_REQUEST", [("HP_ASSIGNMENT", None)]),
        calls,
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="I take a closer look at the courtyard lantern.", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["metadata"]["authoritative_mutation"] is False
    assert data["resolution"]["metadata"]["resolver_invoked"] is False
    assert storage.load_session()["turn_counter"] == before
    assert len(calls) == 1


def test_pr_dy_malformed_interpretation_does_not_execute(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = storage.load_session()["turn_counter"]
    _install_interpretation(monkeypatch, "not-json", [])
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="I take a closer look at the courtyard lantern.", ui_mode="player"))

    assert data["resolution"]["metadata"]["processing_outcome"] == "malformed_interpretation"
    assert storage.load_session()["turn_counter"] == before


def test_pr_dy_auto_ooc_is_non_mutating(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before_session = storage.load_session()
    before_world = storage.load_world()
    _install_interpretation(
        monkeypatch,
        _payload("OUT_OF_CHARACTER_CORRECTION", "INTERPRETED", []),
        [],
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="Wait, how do the rules for searching work at this table?", ui_mode="player"))

    assert "out of character" in data["gm_output"]["player_facing_text"].lower()
    assert data["resolution"]["metadata"]["authoritative_mutation"] is False
    assert storage.load_session() == before_session
    assert storage.load_world() == before_world


def test_pr_dy_clarification_does_not_mutate(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = storage.load_session()["turn_counter"]
    _install_interpretation(
        monkeypatch,
        _payload(
            "CLARIFICATION",
            "CLARIFICATION_REQUIRED",
            [],
            question="Do you mean the lantern or the gate?",
        ),
        [],
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="Look at that.", ui_mode="player"))

    assert data["gm_output"]["player_facing_text"] == "Do you mean the lantern or the gate?"
    assert storage.load_session()["turn_counter"] == before


def test_pr_dy_explicit_ooc_does_not_call_interpretation(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = storage.load_session()["turn_counter"]

    def _request(*_args, **_kwargs):
        raise AssertionError("interpretation provider called")

    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", _request)
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="OOC: I am only asking how this table works.", ui_mode="player"))

    assert data["resolution"]["metadata"]["authoritative_mutation"] is False
    assert storage.load_session()["turn_counter"] == before


def test_pr_dy_explicit_ic_uses_validated_interpretation(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    calls = []
    _install_interpretation(
        monkeypatch,
        _payload("OUT_OF_CHARACTER_CORRECTION", "INTERPRETED", [("ASK", MARA_ID)]),
        calls,
    )
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    data = chat(ChatRequest(text="IC: I ask Sergeant Mara what lies beyond the gate.", ui_mode="player"))

    assert len(calls) == 1
    assert data["resolution"]["action_id"] == MARA_ID
    assert storage.load_session()["turn_counter"] == 1


def test_pr_dy_disabled_interpretation_does_not_call_provider(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")

    def _request(*_args, **_kwargs):
        raise AssertionError("interpretation provider called")

    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", _request)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    data = chat(ChatRequest(text="OOC: leave the scene alone.", ui_mode="player"))

    assert data["resolution"]["metadata"]["authoritative_mutation"] is False


def test_pr_dy_bridge_rejection_does_not_execute(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = storage.load_session()["turn_counter"]
    _install_interpretation(
        monkeypatch,
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("ASK", LANTERN_ID)]),
        [],
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="I ask the lantern a question.", ui_mode="player"))

    assert data["resolution"]["metadata"]["resolver_invoked"] is False
    assert storage.load_session()["turn_counter"] == before


def test_pr_dy_repeated_submission_commits_a_second_turn(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    _install_interpretation(
        monkeypatch,
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", LANTERN_ID)]),
        [],
    )
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
    text = "I take a closer look at the courtyard lantern."

    first = chat(ChatRequest(text=text, ui_mode="player"))
    second = chat(ChatRequest(text=text, ui_mode="player"))

    assert first["ok"] and second["ok"]
    assert storage.load_session()["turn_counter"] == 2
