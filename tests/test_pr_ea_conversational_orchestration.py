from __future__ import annotations

import copy

import pytest

from experiments.pr_dq.world import GATE_ID, LANTERN_ID
from game import storage
from game.api import chat
from game.conversational_orchestration import (
    ConversationalDecisionCategory,
    decision_from_interpretation_record,
    deterministic_conversational_decision,
)
from game.models import ChatRequest
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution, _seed_pr_du_world
from tests.test_pr_dy_live_gameplay import _enable_live, _install_interpretation, _payload

pytestmark = pytest.mark.unit


def test_pr_ea_contract_distinguishes_incidental_context_from_primary_execute() -> None:
    record = _payload(
        "IN_WORLD_ACTION",
        "INTERPRETED",
        [("THANK", None), ("MOVE", GATE_ID)],
    )
    record["action_components"][0]["description"] = "Thank the guard."
    record["action_components"][1]["description"] = "Head through the gate."

    decision = decision_from_interpretation_record(record, player_text="I thank the guard and head through the gate.")

    assert decision.category == ConversationalDecisionCategory.EXECUTE
    assert decision.proposed_operation == "MOVE"
    assert decision.proposed_target == GATE_ID
    assert decision.incidental_context == ["Thank the guard."]
    assert decision.requires_authoritative_execution is True
    assert len((decision.proposed_record or {}).get("action_components") or []) == 1


def test_pr_ea_deterministic_incomplete_movement_clarifies_without_context() -> None:
    decision = deterministic_conversational_decision(player_text="I leave.")

    assert decision is not None
    assert decision.category == ConversationalDecisionCategory.CLARIFY
    assert decision.missing_information == ["destination"]
    assert decision.player_facing_text == "Where are you trying to go?"


def test_pr_ea_incomplete_movement_does_not_advance_turn_or_clock(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    before_session = copy.deepcopy(storage.load_session())
    before_world = copy.deepcopy(storage.load_world())

    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="I leave.", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["kind"] == "conversational_clarify"
    assert data["gm_output"]["player_facing_text"] == "Where are you trying to go?"
    after_session = storage.load_session()
    assert after_session["turn_counter"] == before_session["turn_counter"]
    assert after_session["clocks"] == before_session["clocks"]
    assert after_session["active_scene_id"] == before_session["active_scene_id"]
    assert after_session["conversational_context"]["pending_clarification"]["kind"] == "missing_destination"
    assert storage.load_world() == before_world
    assert len(storage.load_log()) == 1


def test_pr_ea_unmarked_ooc_help_question_is_nonmutating_without_provider(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    before_session = copy.deepcopy(storage.load_session())

    def _request(*_args, **_kwargs):
        raise AssertionError("interpretation provider called")

    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", _request)
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="How do I save the game?", ui_mode="player"))

    assert data["resolution"]["kind"] == "conversational_answer"
    assert (data["resolution"]["metadata"]["conversational_decision"] or {})["category"] == "ANSWER"
    assert data["resolution"]["metadata"]["provider_calls"]["interpretation_requests"] == 0
    assert storage.load_session() == before_session


def test_pr_ea_stored_incidental_plus_move_executes_existing_authoritative_resolver(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    payload = _payload(
        "IN_WORLD_ACTION",
        "INTERPRETED",
        [("THANK", None), ("MOVE", GATE_ID)],
    )
    payload["action_components"][0]["description"] = "Thank Sergeant Mara."
    payload["action_components"][1]["description"] = "Head through the gate."
    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_args: payload)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    data = chat(ChatRequest(text="I thank Sergeant Mara and head through the gate.", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["action_id"] == GATE_ID
    assert data["resolution"]["metadata"]["stored_interpretation"]["operation"] == "MOVE"
    assert storage.load_session()["turn_counter"] == 1


def test_pr_ea_live_missing_move_target_uses_focused_clarification(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    _enable_live(monkeypatch)
    before = copy.deepcopy(storage.load_session())
    _install_interpretation(
        monkeypatch,
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", None)]),
        [],
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="I head out.", ui_mode="player"))

    assert data["resolution"]["kind"] == "conversational_clarify"
    assert data["gm_output"]["player_facing_text"] == "Where are you trying to go?"
    after = storage.load_session()
    assert after["turn_counter"] == before["turn_counter"]
    assert after["clocks"] == before["clocks"]
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["conversational_context"]["pending_clarification"]["operation"] == "MOVE"
