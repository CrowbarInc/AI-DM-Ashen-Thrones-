"""Production request and host counterfactuals; no live-model adequacy claim."""
import copy
import json
from pathlib import Path

import pytest

from game import live_chat_interpretation as live
from game.conversational_orchestration import decision_from_interpretation_record, public_conversation_evidence
from tests.test_atgb_r1_04_readiness import record

ROOT = Path(__file__).resolve().parents[1]


def corrected(refs=(), subject="people"):
    result = record("CORRECTION")
    result["communication"]["subject"] = subject
    result["communication"]["evidence_refs"] = list(refs)
    result["correction"] = {"subject": "REFERENT", "note": "Resolved conversational subject"}
    return result


def interpret(monkeypatch, payload, *, text="I meant the people, not the weather.", scene=None, log=None, session=None, world=None):
    captured = {}
    monkeypatch.setattr(live, "production_live_interpretation_enabled", lambda: True)
    def wire(messages, **kwargs):
        captured.update(messages=copy.deepcopy(messages), schema=live.production_interpretation_schema())
        return {"ok": True, "sent": False, "text": json.dumps(payload)}
    monkeypatch.setattr(live, "request_interpretation", wire)
    result = live.interpret_production_turn(player_text=text, mode="AUTO", scene=scene, world=world, log=log, session=session)
    return result, captured


@pytest.mark.parametrize("clause", [
    "Ordinary conversational correction", "does not itself revise a gameplay action",
    "player clarifying their own meaning", "AI-DM requesting clarification",
    "continue the corrected conversation", "Recover the underlying question",
    "Select relevant authorized PUBLIC evidence_refs", "meaningful ambiguity remains",
    "Restricted or unestablished information", "actual eligible pending intention",
    "no world facts may use empty evidence_refs", "OTHER for resolved GM conversation",
])
def test_actual_request_contract(monkeypatch, clause):
    _, captured = interpret(monkeypatch, corrected())
    contract = json.dumps(captured)
    assert clause in contract
    assert "CORRECTION revises unexecuted intent" not in contract
    assert "CLARIFICATION=the utterance is unclear" not in contract


@pytest.mark.parametrize("text,fact", [
    ("I meant the people, not the weather.", "Two astronomers stand by the telescope."),
    ("No, I was asking about the violinist.", "The violinist wears a blue coat."),
    ("I meant her coat's color, not its fabric.", "Her coat is blue."),
])
def test_supported_corrections(monkeypatch, text, fact):
    scene = {"scene": {"id": "observatory", "visible_facts": [fact]}}
    result, _ = interpret(monkeypatch, corrected(["visible:0"]), text=text, scene=scene)
    decision = decision_from_interpretation_record(result["record"], player_text=text, scene=scene)
    assert decision.player_facing_text == "Understood. " + fact
    assert decision.category.value == "ANSWER"
    assert not decision.requires_authoritative_execution
    assert decision.context_update is None


def test_insufficient_and_restricted_evidence(monkeypatch):
    scene = {"scene": {"id": "observatory", "discoverable_clues": [{"text": "Private identity: the assassin."}]}}
    assert "assassin" not in json.dumps(public_conversation_evidence(scene, []))
    result, captured = interpret(monkeypatch, corrected(), scene=scene)
    assert "assassin" not in json.dumps(captured)
    decision = decision_from_interpretation_record(result["record"], player_text="I meant their identities.", scene=scene)
    assert decision.player_facing_text == "That has not been established in the information available to you."
    rejected, _ = interpret(monkeypatch, corrected(["private:identity"]), scene=scene)
    assert rejected["reason"] == "malformed_communication"


@pytest.mark.parametrize("change", ["unresolved", "status", "purpose", "subject", "components"])
def test_acknowledgment_requires_resolved_conversational_correction(change):
    payload = corrected(["visible:0"])
    payload["public_evidence"] = {"visible:0": "The violinist wears blue."}
    if change == "unresolved":
        payload["communication"]["recipient"] = "AMBIGUOUS"
        payload["references"]["unresolved_references"] = ["that person"]
        payload["clarification_question"] = "Which person do you mean?"
    elif change == "status":
        payload["interpretation_status"] = "CLARIFICATION_REQUIRED"
        payload["clarification_question"] = "Which person do you mean?"
    elif change == "purpose":
        payload["communication"]["purpose"] = "DESCRIPTION"
    elif change == "subject":
        payload["correction"]["subject"] = "NONE"
    else:
        payload["action_components"] = [{"order": 1, "operation_class": "ASK", "target_ref": None, "description": "ask"}]
    decision = decision_from_interpretation_record(payload, player_text="No, that person.")
    assert not decision.player_facing_text.startswith("Understood.")
    assert not decision.requires_authoritative_execution
    if change in {"unresolved", "status"}:
        assert decision.category.value == "CLARIFY"


def test_no_fact_acknowledgment_needs_no_evidence(monkeypatch):
    result, _ = interpret(monkeypatch, record("WITHDRAWAL"), text="Never mind.")
    assert result["record"]["public_evidence"] == {}
    decision = decision_from_interpretation_record(result["record"], player_text="Never mind.")
    assert decision.category.value == "ANSWER"
    assert not decision.requires_authoritative_execution


@pytest.mark.parametrize("case", ["supported", "insufficient", "restricted", "ambiguous"])
def test_direct_chat_delivery_and_state_integrity(tmp_path, monkeypatch, case):
    from game import storage
    from game.api import chat
    from game.models import ChatRequest
    from tests.test_pr_ef_gm_authority import seed_scene

    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setattr(live, "production_live_interpretation_enabled", lambda: True)
    payload = corrected(["visible:1"] if case == "supported" else [])
    if case == "restricted":
        payload["communication"]["evidence_refs"] = ["private:mark"]
    if case == "ambiguous":
        payload.update(communication_mode="CLARIFICATION", interpretation_status="CLARIFICATION_REQUIRED",
                       clarification_question="Which person do you mean?")
        payload["communication"].update(recipient="AMBIGUOUS", purpose="CLARIFICATION")
        payload["references"]["unresolved_references"] = ["that person"]
    monkeypatch.setattr(live, "request_interpretation", lambda *a, **k: {"ok": True, "sent": False, "text": json.dumps(payload)})
    monkeypatch.setattr("game.api.call_gpt", lambda *a, **k: pytest.fail("generation invoked"))
    def snapshot():
        return copy.deepcopy([storage.load_world(), storage.load_active_scene(), storage.load_character(), storage.load_combat(), storage.load_session()])
    before = snapshot()
    response = chat(ChatRequest(text="I meant the person beside the gate.", ui_mode="player"))
    after = snapshot()
    output = response["gm_output"]["player_facing_text"]
    assert response["ok"]
    assert "maker's mark" not in output
    assert before[:4] == after[:4]
    for key in set(before[4]) | set(after[4]):
        if key not in {"conversational_context", "last_saved_at"}:
            assert before[4].get(key) == after[4].get(key)
    for key in ("pending_intention", "pending_clarification", "last_executed_intention"):
        assert (before[4].get("conversational_context") or {}).get(key) == (after[4].get("conversational_context") or {}).get(key)
    if case == "supported":
        assert output == "Understood. " + before[1]["scene"]["visible_facts"][1]
    elif case == "insufficient":
        assert output == "That has not been established in the information available to you."
    elif case == "ambiguous":
        assert output == "Which person do you mean?"
    else:
        assert not output.startswith("Understood.")


@pytest.mark.parametrize("campaign,trial,trace_name", [
    ("atgb_r1_05", "L1", "traces.json"), ("atgb_r1_05", "L2", "traces.json"),
    ("atgb_r1_03", "L3", "trace.json"),
])
def test_saved_failure_replay(monkeypatch, campaign, trial, trace_name):
    path = ROOT / "artifacts/atgb" / campaign / trial
    before = json.loads((path / "before.json").read_text())
    unchanged = copy.deepcopy(before)
    trace = json.loads((path / trace_name).read_text())
    original = next(row["return"] for row in trace if row["function"] == "request_interpretation")
    historical = json.loads(original["text"])
    text = json.loads((path / "setup.json").read_text())["player_input"]
    kwargs = {key: before[key] for key in ("scene", "world", "session", "log")}
    old, captured = interpret(monkeypatch, historical, text=text, **kwargs)
    old_decision = decision_from_interpretation_record(old["record"], player_text=text, **{k: before[k] for k in ("scene", "world", "session")})
    assert old_decision.category.value == "CLARIFY"
    counterfactual = copy.deepcopy(historical)
    counterfactual.update(communication_mode="OTHER", interpretation_status="INTERPRETED", action_components=[], clarification_question="", correction={"subject": "REFERENT", "note": "Resolved conversational subject"})
    counterfactual["communication"].update(recipient="GM", purpose="CORRECTION", evidence_refs=["visible:1", "visible:2", "visible:3"])
    new, captured = interpret(monkeypatch, counterfactual, text=text, **kwargs)
    decision = decision_from_interpretation_record(new["record"], player_text=text, **{k: before[k] for k in ("scene", "world", "session")})
    assert decision.category.value == "ANSWER"
    assert decision.player_facing_text == "Understood. " + " ".join(new["record"]["public_evidence"].values())
    assert decision.context_update is None
    assert not decision.requires_authoritative_execution
    assert before == unchanged
    assert "Recover the underlying question" in captured["messages"][0]["content"]
