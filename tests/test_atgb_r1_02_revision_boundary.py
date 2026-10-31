"""ATGB-R1-02: deterministic revision-entry contract; no live providers."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game import conversational_orchestration as orchestration, storage
from game.api import chat
from game.models import ChatRequest
from tests.test_pr_ef_gm_authority import raw_record, seed_scene

pytestmark = pytest.mark.regression
ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = [
    "I meant the people, not the weather.",
    "No, I meant the people.",
    "I was asking about the people, not the weather.",
    "That's not what I meant.",
    "I meant the person standing beside the door.",
    "I mean the people, not the weather.",
    "The people, not the weather.",
    "I meant the musicians, not the merchants.",
]
AMBIGUOUS = ["No, the other one.", "I meant the other one.", "Change that.", "Actually, do the other thing."]


def pending(operation="MOVE", scene_id="observatory", status="pending"):
    return {"operation": operation, "scene_id": scene_id, "status": status,
            "target_id": "western_arch", "clarification": "Which doorway do you mean?"}


@pytest.mark.parametrize("text", CORRECTIONS + AMBIGUOUS)
@pytest.mark.parametrize("purpose", ["DESCRIPTION", "CORRECTION"])
@pytest.mark.parametrize("state", ["empty", "pending", "executed"])
def test_correction_language_alone_is_not_action_control(text, purpose, state, monkeypatch):
    ctx = {"last_gm_exchange": {"player_text": "Who is here?", "response_text": "Two astronomers stand by the telescope."}}
    if state != "empty":
        ctx["pending_intention" if state == "pending" else "last_executed_intention"] = pending(status=state)
    session = {"conversational_context": ctx}
    scene = {"scene": {"id": "observatory"}}
    before = copy.deepcopy((session, scene))
    record = raw_record(purpose=purpose)
    decision = orchestration.decision_from_interpretation_record(record, player_text=text, session=session, scene=scene)
    assert decision.reason == "communication_before_execution"
    assert decision.context_update is None
    assert not decision.requires_authoritative_execution
    assert decision.proposed_record is None
    assert (session, scene) == before
    assert "unexecuted intention" not in decision.player_facing_text


@pytest.mark.parametrize("text,operation", [
    ("Change my pending move to the eastern doorway.", "MOVE"),
    ("Change my pending attack to the guard.", "ATTACK"),
    ("I meant to move east instead of west.", "MOVE"),
    ("I meant to move east.", "MOVE"),
    ("I meant to attack the guard.", "ATTACK"),
    ("Instead, make that a question about the lamp.", "ASK"),
])
@pytest.mark.parametrize("state,expected", [
    ("pending", "pending_intention_revised"),
    ("clarification", "pending_intention_revised"),
    ("wrong_scene", "no_pending_intention"),
    ("executed", "executed_intention_not_reversible"),
])
def test_mechanical_revision_keeps_existing_validation(text, operation, state, expected):
    intention = pending(operation, scene_id="elsewhere" if state == "wrong_scene" else "observatory")
    key = "pending_clarification" if state == "clarification" else "pending_intention"
    if state == "executed":
        key = "last_executed_intention"
        intention["status"] = "executed"
    session = {"conversational_context": {key: intention}}
    before = copy.deepcopy(session)
    decision = orchestration.decision_from_interpretation_record(
        raw_record(purpose="CORRECTION", components=[(operation, "eastern_arch")]),
        player_text=text, session=session, scene={"scene": {"id": "observatory"}},
    )
    assert decision.reason == expected
    assert decision.execution_policy == "answer_only"
    assert not decision.requires_authoritative_execution
    assert decision.proposed_record is None
    assert session == before
    if expected == "pending_intention_revised":
        assert decision.context_update["conversational_context"]["pending_intention"]["revised_text"] == text
    else:
        assert decision.context_update is None


@pytest.mark.parametrize("text", ["Change my pending move to the eastern doorway.",
                                  "Change my pending attack to the guard.",
                                  "Instead, make that a question about the lamp."])
def test_explicit_revision_without_intention_cannot_fabricate_one(text):
    decision = orchestration.decision_from_interpretation_record(raw_record(purpose="CORRECTION"), player_text=text)
    assert decision.reason == "no_pending_intention"
    assert decision.context_update is None
    assert not decision.requires_authoritative_execution


@pytest.mark.parametrize("purpose", ["DESCRIPTION", "CORRECTION"])
def test_s08_2_preserved_context_reaches_ordinary_response(purpose):
    capture = json.loads((ROOT / "artifacts/atgb/atgb_03c/S08/result.json").read_text(encoding="utf-8"))
    first, second = capture["turns"][:2]
    session = {"active_scene_id": "frontier_gate", "conversational_context": {
        "last_gm_exchange": {"player_text": first["player_input"], "response_text": first["response_text"]}}}
    before = copy.deepcopy(session)
    decision = orchestration.decision_from_interpretation_record(
        raw_record(purpose=purpose), player_text=second["player_input"], session=session,
        scene={"scene": {"id": "frontier_gate"}},
    )
    assert decision.reason == "communication_before_execution"
    assert decision.player_facing_text == "That has not been established in the information available to you."
    assert decision.context_update is None
    assert session == before


def test_correction_preserves_selected_public_evidence():
    record = raw_record(purpose="CORRECTION", refs=["visible:people"])
    record["public_evidence"] = {"visible:people": "Two astronomers stand by the telescope."}
    decision = orchestration.decision_from_interpretation_record(record, player_text="I meant the people.")
    assert decision.player_facing_text == record["public_evidence"]["visible:people"]
    assert decision.reason == "communication_before_execution"


@pytest.mark.parametrize("text", [CORRECTIONS[0], "Change my pending attack to the guard.", "Change that."])
def test_api_nonmutating_correction_with_no_providers(tmp_path, monkeypatch, text):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_: raw_record(purpose="CORRECTION"))
    monkeypatch.setattr("game.api.call_gpt", lambda *a, **k: pytest.fail("narration invoked"))
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", lambda *a, **k: pytest.fail("interpretation invoked"))
    before = copy.deepcopy((storage.load_world(), storage.load_session(), storage.load_active_scene(), storage.load_character()))
    response = chat(ChatRequest(text=text, ui_mode="player"))
    assert response["ok"] is True
    assert not response["resolution"].get("social")
    assert (storage.load_world(), storage.load_active_scene(), storage.load_character()) == (before[0], before[2], before[3])
    # Delivered conversational memory and save timestamps are allowed to change;
    # gameplay state and pending/executed intention records are not.
    after_session = storage.load_session()
    assert {k: v for k, v in after_session.items() if k not in {"conversational_context", "last_saved_at"}} == {
        k: v for k, v in before[1].items() if k not in {"conversational_context", "last_saved_at"}}
    for key in ("pending_intention", "pending_clarification", "last_executed_intention"):
        assert (after_session.get("conversational_context") or {}).get(key) == (before[1].get("conversational_context") or {}).get(key)
    assert "maker's mark" not in response["gm_output"]["player_facing_text"]
