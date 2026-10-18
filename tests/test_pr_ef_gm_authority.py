"""PR-EF ownership, proposal integrity, persistence and production HTTP checks."""
from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app, chat
from game.conversational_orchestration import decision_from_interpretation_record, public_conversation_evidence
from game.live_chat_interpretation import production_interpretation_schema
from game.models import ChatRequest
from tests.test_pr_du_player_pipeline import _seed_pr_du_world, _fake_gm_for_resolution
from experiments.pr_dq.world import COURTYARD_ID, STREET_ID, GATE_ID, MARA_ID, LANTERN_ID


def raw_record(owner="GM", purpose="QUESTION", refs=(), components=()):
    return {
        "communication_mode": "IN_WORLD_ACTION" if owner in {"NPC", "CHARACTER"} else "OTHER",
        "interpretation_status": "INTERPRETED", "player_intent": {"summary": "Player communication"},
        "asserted_premises": [], "requested_outcomes": [],
        "action_components": [dict(order=i + 1, description=op, operation_class=op, target_ref=target) for i, (op, target) in enumerate(components)],
        "references": {"permitted_entity_ids": [target for _, target in components if target], "unresolved_references": []},
        "clarification_question": "", "correction": {"subject": "NONE", "note": ""},
        "communication": {"recipient": owner, "purpose": purpose, "subject": "current subject", "evidence_refs": list(refs)},
    }


def seed_scene(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    scene = storage.load_active_scene()
    scene["scene"]["summary"] = "A walled courtyard. A lit lantern hangs beside the gate. A side gate is barred from the other side. Sergeant Mara watches the road."
    scene["scene"]["visible_facts"] += ["The side gate is barred from the other side.", "Sergeant Mara looks concerned as she watches the road."]
    scene["scene"]["exits"][0]["aliases"] = ["gate", "courtyard gate"]
    scene["scene"]["interactables"][0]["reveals_clue"] = "lantern_mark"
    scene["scene"]["discoverable_clues"] = [{"id": "lantern_mark", "text": "A small maker's mark is stamped beneath the lantern."}]
    storage.save_scene(scene)
    session = storage.load_session()
    session["campaign_started"] = True
    storage.save_session(session)


TEN_TURNS = [
    "Could you describe our surroundings?",
    "What do I already know about that lantern?",
    "Does Sergeant Mara appear concerned?",
    "I ask Sergeant Mara where the street leads.",
    "Which road do you mean?",
    "GM, can you clarify what Mara just said?",
    "I inspect the courtyard lantern.",
    "Why did I find that mark?",
    "Actually, never mind the inspection; leave it alone.",
    "I walk through the courtyard gate.",
]


def scripted_interpretation(messages, **kwargs):
    """Test double for the existing wire call; never a production recognizer."""
    text = messages[1]["content"].splitlines()[0].removeprefix("Utterance: ")
    rows = {
        TEN_TURNS[0]: raw_record(purpose="DESCRIPTION", refs=["scene"]),
        TEN_TURNS[1]: raw_record(purpose="RECALL", refs=["visible:0"]),
        TEN_TURNS[2]: raw_record(refs=["visible:2"]),
        TEN_TURNS[3]: raw_record("NPC", components=[("ASK", MARA_ID)]),
        TEN_TURNS[4]: raw_record("NPC", "QUESTION", refs=[f"npc:{MARA_ID}:street"], components=[("ASK", MARA_ID)]),
        TEN_TURNS[5]: raw_record(purpose="EXPLANATION", refs=["reply:3"]),
        TEN_TURNS[6]: raw_record("CHARACTER", "ACTION", components=[("INSPECT", LANTERN_ID)]),
        TEN_TURNS[7]: raw_record(purpose="EXPLANATION", refs=["reply:3"]),
    }
    return {"ok": True, "sent": False, "text": json.dumps(rows[text])}


def run_ten_turns(*, live=False):
    client = TestClient(app)
    rows = []
    for number, text in enumerate(TEN_TURNS, 1):
        before_session, before_world = copy.deepcopy(storage.load_session()), copy.deepcopy(storage.load_world())
        response = client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"})
        data = response.json()
        after = storage.load_session()
        # Every request reloads from disk; the sixth turn explicitly round-trips the save.
        if number == 6:
            storage.save_session(copy.deepcopy(after))
            assert storage.load_session().get("conversational_context") == after.get("conversational_context")
        resolution = data.get("resolution") or {}
        row = {"turn": number, "player": text, "http_status": response.status_code,
               "response": data.get("gm_output", {}).get("player_facing_text"), "resolution": resolution,
               "world_changed": before_world != storage.load_world(),
               "changed_session_keys": sorted(key for key in set(before_session) | set(after) if before_session.get(key) != after.get(key)),
               "before_turn": before_session.get("turn_counter"), "after_turn": after.get("turn_counter"),
               "scene": after.get("active_scene_id"), "provider_mode": "live" if live else "scripted wire / narration double"}
        rows.append(row)
    return rows


def test_production_ten_turn_sequence(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "0")
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation", scripted_interpretation)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
    rows = run_ten_turns()
    assert len(storage.load_log()) == 10
    for i in (0, 1, 2, 5, 7, 8):
        row = rows[i]
        assert row["http_status"] == 200
        assert row["before_turn"] == row["after_turn"]
        assert not row["world_changed"]
        assert "who are you asking" not in row["response"].lower()
        assert "should i start" not in row["response"].lower()
    for i in (3, 4):
        assert rows[i]["resolution"]["social"]["npc_id"] == MARA_ID
    assert rows[4]["resolution"]["social"]["recalled_topic"] is True
    assert "north road" in rows[4]["response"].lower()
    assert rows[6]["resolution"]["action_id"] == LANTERN_ID
    assert rows[9]["scene"] == STREET_ID
    assert rows[9]["after_turn"] == rows[9]["before_turn"] + 1
    assert rows[2]["response"].startswith("Sergeant Mara looks concerned")


def test_schema_owns_communication_without_execution_fields():
    schema = production_interpretation_schema()
    assert "communication" in schema["required"]
    assert "GM" in schema["properties"]["communication"]["properties"]["recipient"]["enum"]
    assert "authorized" not in json.dumps(schema)


@pytest.mark.parametrize("operation", ["SOCIAL_SIGNAL", "INVENTORY_GRANT", "ATTACK", "TIME_CONTROL"])
def test_unsupported_singletons_never_offer_confirmation(operation):
    record = raw_record("CHARACTER", "ACTION", components=[(operation, None)])
    record.pop("communication")
    result = decision_from_interpretation_record(record, player_text="Attempt something")
    assert result.category.value == "DECLINE"
    assert "?" not in result.player_facing_text
    assert result.context_update["conversational_context"]["pending_clarification"] is None


def test_unknown_and_mixed_communication_cannot_execute():
    for owner in ("GM", "MIXED", "SESSION"):
        record = raw_record(owner, components=[("MOVE", GATE_ID)])
        result = decision_from_interpretation_record(record, player_text="Can I go? If safe, go.")
        assert not result.requires_authoritative_execution
        assert result.proposed_record is None
        assert "established" in result.player_facing_text or "ruling" in result.player_facing_text


def test_public_evidence_excludes_undiscovered_clues_and_npc_topics(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    evidence = json.dumps(public_conversation_evidence(storage.load_active_scene(), []))
    assert "maker's mark" not in evidence
    assert "north road" not in evidence


def test_bad_compound_target_is_not_offered(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    record = raw_record("CHARACTER", "ACTION", components=[("ASK", GATE_ID), ("MOVE", GATE_ID)])
    record.pop("communication")
    result = decision_from_interpretation_record(record, scene=storage.load_active_scene(), world=storage.load_world())
    assert "?" not in result.player_facing_text
    assert not result.requires_authoritative_execution


def test_withdrawal_after_reload_cannot_execute_pending(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    chat(ChatRequest(text="I leave."))
    before = storage.load_session()
    world = storage.load_world()
    result = chat(ChatRequest(text="No."))
    after = storage.load_session()
    assert result["resolution"]["metadata"]["resolver_invoked"] is False
    assert after["conversational_context"]["pending_clarification"] is None
    assert after["turn_counter"] == before["turn_counter"]
    assert storage.load_world() == world


def test_unsupported_first_step_cannot_be_reordered_into_confirmation(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    record = raw_record("CHARACTER", "ACTION", components=[("USE_VISIBLE_OBJECT", LANTERN_ID), ("MOVE", GATE_ID)])
    record.pop("communication")
    result = decision_from_interpretation_record(record, scene=storage.load_active_scene(), world=storage.load_world())
    assert "?" not in result.player_facing_text
    assert result.secondary_intentions[0]["operation"] == "USE_VISIBLE_OBJECT"
    assert result.secondary_intentions[1]["operation"] == "MOVE"


def test_gm_question_cannot_swallow_conditional_action():
    record = raw_record("GM", "QUESTION", components=[("ASK", None), ("MOVE", GATE_ID)])
    result = decision_from_interpretation_record(record, player_text="Is it safe? If so, I leave.")
    assert result.communication_owner == "MIXED"
    assert result.category.value == "CLARIFY"
    assert len(result.secondary_intentions) == 2
    assert not result.requires_authoritative_execution


def test_conditional_turn_keeps_action_before_movement_question_shortcut(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    before = storage.load_session()
    result = chat(ChatRequest(text="Would leaving be prudent? Provided it is, we will depart."))
    decision = result["resolution"]["metadata"]["conversational_decision"]
    assert decision["communication_owner"] == "MIXED"
    assert decision["secondary_intentions"]
    assert storage.load_session()["turn_counter"] == before["turn_counter"]


def test_gm_why_after_refusal_keeps_reason_and_does_not_ask_for_npc(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    chat(ChatRequest(text="I teleport to the moon."))
    before = storage.load_session()
    world = storage.load_world()
    reply = chat(ChatRequest(text="Why not?"))
    assert "who are you asking" not in reply["gm_output"]["player_facing_text"].lower()
    assert reply["resolution"]["metadata"]["conversational_decision"]["communication_owner"] == "GM"
    assert storage.load_session()["turn_counter"] == before["turn_counter"]
    assert storage.load_world() == world


def test_new_explicit_action_supersedes_old_pending_intention(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    chat(ChatRequest(text="I leave."))
    assert storage.load_session()["conversational_context"]["pending_clarification"]
    record = raw_record("CHARACTER", "ACTION", components=[("INSPECT", LANTERN_ID)])
    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *args: record)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
    data = chat(ChatRequest(text="I inspect the courtyard lantern."))
    assert data["resolution"]["action_id"] == LANTERN_ID
    assert storage.load_session()["conversational_context"]["pending_clarification"] is None
