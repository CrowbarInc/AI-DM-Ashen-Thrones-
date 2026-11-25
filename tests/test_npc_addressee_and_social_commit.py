"""Offline acceptance for ordinary NPC ownership and social receipts."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import api, social, storage
from game.ordinary_semantic_ownership import assess_addressee_grounding
from game.player_interpretation_bridge import normalized_action_from_interpretation
from tests.test_inspection_communication_admission import EXTENDED, captured, reason, replay, state, trace
from tests.test_repeat_statement_routing_ownership import CAPTAIN, assert_read_only, conversation, evaluate


@pytest.fixture
def social_calls(monkeypatch):
    calls = []
    resolve = social.resolve_social_action

    def observe(scene, session, world, action, **kwargs):
        receipt = resolve(scene, session, world, action, **kwargs)
        calls.append({"action": copy.deepcopy(action), "receipt": copy.deepcopy(receipt)})
        return receipt

    monkeypatch.setattr(social, "resolve_social_action", observe)
    return calls


@pytest.mark.parametrize("label,text,route", [
    ("scene-gm", "What can I see from here?", "visible_scene_context_answer"),
    ("scene-social", "I ask the captain what he can see.", "social"),
    ("prints-gm", "What do the footprints indicate?", "information"),
    ("prints-social", "Captain, what do the footprints indicate?", "social"),
    ("patrol-gm", "Where was the patrol last seen?", "information"),
    ("patrol-social", "I ask the captain where the patrol was last seen.", "social"),
    ("notice-gm", "What did I learn from the notice?", "information"),
    ("notice-social", "I tell the captain what I learned from the notice.", "social"),
    ("statement-gm", "What did the captain say?", "delivered_speaker_attribution"),
    ("statement-social", "I ask the captain another question.", "missing_social_question"),
    ("implicit-pronoun", "I ask whether he knows anything else.", "social"),
    ("address-pronoun", "I ask him whether he knows anything else.", "social"),
    ("direct-followup", "What else do you know about the patrol?", "social"),
    ("read-only-repeat", "Repeat what he told me.", "repeat_delivered_statement"),
    ("bare-repeat", "Can you repeat that?", "repeat_delivered_statement"),
])
def test_paired_http_boundaries(replay, social_calls, label, text, route):
    request, raw = captured(EXTENDED / "T10.json")
    setup = replay(label + "-setup", request, raw)
    assert setup["response"]["gm_output"]["player_facing_text"] == CAPTAIN
    social_calls.clear()
    row = replay(label, {"text": text}, duplicate=True)
    trace(label + "-resolver", social_calls)
    receipt = row["persisted_log_resolution"]
    if route == "social":
        assert len(social_calls) == 1 and social_calls[0]["action"]["target_id"] == "guard_captain"
        assert receipt["social"]["target_resolved"] is True
        assert receipt["success"] is True
        assert len(row["host"]["advance_world_tick"]) == 1
        assert row["after"]["session"]["turn_counter"] == row["before"]["session"]["turn_counter"] + 1
        assert row["before"]["character"] == row["after"]["character"]
        if label in {"scene-social", "prints-social", "notice-social"}:
            assert receipt["social"].get("topic_revealed") is None
            assert CAPTAIN not in row["response"]["gm_output"]["player_facing_text"]
            assert row["before"]["session"]["clue_knowledge"] == row["after"]["session"]["clue_knowledge"]
    else:
        assert not social_calls
        assert_read_only(row)
        if route == "information":
            assert reason(row) not in {"unresolved_addressee", "repeat_delivered_statement"}
            assert CAPTAIN not in row["response"]["gm_output"]["player_facing_text"]
        else:
            assert reason(row) == route
            if route in {"repeat_delivered_statement", "delivered_speaker_attribution"}:
                assert row["response"]["gm_output"]["player_facing_text"] == CAPTAIN


def test_handoff_from_genuinely_delivered_captain_speech(replay, social_calls):
    request, raw = captured(EXTENDED / "T10.json")
    setup = replay("handoff-captain-setup", request, raw)
    assert setup["response"]["gm_output"]["player_facing_text"] == CAPTAIN
    social_calls.clear()
    followup = replay("handoff-active-followup", {"text": "You mentioned the patrol. What have you heard?"})
    assert followup["persisted_log_resolution"]["success"] is True
    assert len(social_calls) == 1 and social_calls[0]["action"]["target_id"] == "guard_captain"
    assert len(followup["host"]["advance_world_tick"]) == 1
    assert followup["before"]["session"]["clue_knowledge"].keys() == followup["after"]["session"]["clue_knowledge"].keys()

    social_calls.clear()
    request, raw = captured(EXTENDED / "T11.json")
    notice = replay("handoff-notice-setup", request, raw, duplicate=True)
    assert "northwest mud track" in notice["response"]["gm_output"]["player_facing_text"]
    assert CAPTAIN not in notice["response"]["gm_output"]["player_facing_text"]
    recalled = replay("handoff-notice-recall", {"text": "What did that notice say about where the patrol was last seen?"})
    assert "northwest mud track" in recalled["response"]["gm_output"]["player_facing_text"]
    assert CAPTAIN not in recalled["response"]["gm_output"]["player_facing_text"]
    assert not social_calls
    assert_read_only(recalled)


def test_recall_her_last_statement(conversation):
    _, _, _, add = conversation
    add("officer")
    result = evaluate("ground-her-last-statement", conversation, "What was her last statement?")
    assert result["action"] == "answer" and result["npc_id"] == "officer"
    assert "notice is posted" in result["line"]


YARD = {"scene": {"id": "yard", "summary": "A damp courtyard."}}
CAPTAIN_ROW = {"id": "guard_captain", "name": "Guard Captain", "aliases": ["captain"], "location": "yard"}
RUNNER_ROW = {"id": "tavern_runner", "name": "Tavern Runner", "aliases": ["runner"], "location": "yard"}
OTHER_CAPTAIN = {"id": "river_captain", "name": "River Captain", "aliases": ["captain"], "location": "yard"}
ACTIVE = {"npc_id": "guard_captain", "scene_id": "yard", "campaign_id": "local", "status": "active"}


@pytest.mark.parametrize("label,text,roster,slot,proposed,target,eligibility", [
    ("present-t12", "Do those prints tell us which way the patrol went?",
     [CAPTAIN_ROW, RUNNER_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("printed-route", "What do the tracks tell me about the captain?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("conditional-print", "Could the prints tell the runner which way they went?",
     [RUNNER_ROW], None, "tavern_runner", None, "not_assessed"),
    ("object-reports", "What did the ledger tell us?",
     [CAPTAIN_ROW], ACTIVE, None, None, "not_assessed"),
    ("npc-is-subject", "What did the captain say?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("npc-location", "Where is the captain?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("no-direct-actor", "Where was the patrol last seen?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("word-overlap", "What do you think the footprints indicate?",
     [{**CAPTAIN_ROW, "description": "Studies footprints."}, RUNNER_ROW], ACTIVE, None, "guard_captain", "executable"),
    ("explicit-name", "I ask the Guard Captain about the patrol.",
     [CAPTAIN_ROW, OTHER_CAPTAIN], None, None, "guard_captain", "executable"),
    ("vocative", "Captain, where is the patrol?",
     [CAPTAIN_ROW, RUNNER_ROW], None, None, "guard_captain", "executable"),
    ("alias-conflict", "I ask the captain about the patrol.",
     [CAPTAIN_ROW, OTHER_CAPTAIN], None, "guard_captain", None, "requires_clarification"),
    ("canonical-overrides-proposal", "I tell the Guard Captain what I learned.",
     [CAPTAIN_ROW, RUNNER_ROW], None, "tavern_runner", "guard_captain", "executable"),
    ("unknown-alias", "I ask the friar about the patrol.",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("invented-surname", "I ask Captain Voss about the patrol.",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("unavailable", "I ask the captain about the patrol.",
     [{**CAPTAIN_ROW, "accessible": False}], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("hidden", "I ask the captain about the patrol.",
     [{**CAPTAIN_ROW, "hidden": True}], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("invisible", "I ask the captain about the patrol.",
     [{**CAPTAIN_ROW, "visible": False}], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("offscene", "I ask the captain about the patrol.",
     [{**CAPTAIN_ROW, "location": "gate"}], ACTIVE, "guard_captain", None, "requires_clarification"),
    ("no-roster", "I ask the captain about the patrol.",
     [], None, None, None, "requires_clarification"),
    ("ambiguous-third-person", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], None, None, None, "requires_clarification"),
    ("ambiguous-plural", "I ask them about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], ACTIVE, None, None, "requires_clarification"),
    ("pronoun-present", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], ACTIVE, "guard_captain", "guard_captain", "executable"),
    ("pronoun-proposal-conflict", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], ACTIVE, "tavern_runner", None, "requires_clarification"),
    ("pronoun-stale-scene", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], {**ACTIVE, "scene_id": "gate"}, None, None, "requires_clarification"),
    ("pronoun-stale-with-one-alternative", "I ask him about the patrol.",
     [RUNNER_ROW], {**ACTIVE, "scene_id": "gate"}, None, None, "requires_clarification"),
    ("pronoun-stale-campaign", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], {**ACTIVE, "campaign_id": "old"}, None, None, "requires_clarification"),
    ("pronoun-ended-conversation", "I ask him about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], {**ACTIVE, "status": "ended"}, None, None, "requires_clarification"),
    ("no-omitted-target", "I ask whether the captain knows about the patrol.",
     [CAPTAIN_ROW, RUNNER_ROW], None, "guard_captain", None, "requires_clarification"),
    ("scene-question-while-active", "What can I see from this location?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("scene-question-while-alone", "What can I see from this location?",
     [], None, None, None, "not_assessed"),
    ("earlier-evidence", "What did I learn from the notice?",
     [CAPTAIN_ROW, RUNNER_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("deictic-no-speech", "What does that mean for the patrol route?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("fragment-no-speech", "What about the patrol?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
    ("subject-pronoun", "Where did he go?",
     [CAPTAIN_ROW], ACTIVE, "guard_captain", None, "not_assessed"),
])
def test_grounding_boundaries(label, text, roster, slot, proposed, target, eligibility):
    world = {"npcs": copy.deepcopy(roster)}
    session = {"campaign_run_id": "local", "active_scene_id": "yard",
               "conversational_context": {"active_interlocutor": slot}}
    if slot:
        session["interaction_context"] = {
            "active_interaction_kind": "social", "active_interaction_target_id": slot["npc_id"],
        }
    before = copy.deepcopy({"session": session, "scene": YARD, "world": world})
    result = assess_addressee_grounding(text, scene=YARD, world=world, session=session, proposed_target_id=proposed)
    after = {"session": session, "scene": YARD, "world": world}
    trace("ground-" + label, {"before": before, "after": after, "text": text,
                              "proposal": proposed, "grounding": result})
    assert result["target_id"] == target
    assert result["operation_eligibility"] == eligibility
    assert before == after


@pytest.mark.parametrize("label,text,target,accepted", [
    ("footprint-proposal", "Do those prints tell us which way the patrol went?", "guard_captain", False),
    ("footprint-without-proposed-target", "Do those prints tell us which way the patrol went?", None, False),
    ("scene-proposal", "What can I see from this location?", "guard_captain", False),
    ("recall-proposal", "What did the captain say?", "guard_captain", False),
    ("knowledge-proposal", "What did I learn from the notice?", "guard_captain", False),
    ("active-proposal", "What about the patrol?", "guard_captain", False),
    ("unknown-target", "I ask the innkeeper about the patrol.", "guard_captain", False),
    ("no-audience", "I ask whether he knows about the patrol.", "guard_captain", False),
    ("wrong-proposed-id", "I ask the captain about the patrol.", "tavern_runner", True),
    ("true-address", "I ask the captain about the patrol.", "guard_captain", True),
    ("true-vocative", "Captain, where is the patrol?", "guard_captain", True),
])
def test_captured_ask_bridge_checks_original_address(label, text, target, accepted):
    _, raw = captured(EXTENDED / "T10.json")
    record = json.loads(raw)
    record["action_components"][0]["target_ref"] = target
    world = {"npcs": [CAPTAIN_ROW, RUNNER_ROW]}
    session = {"campaign_run_id": "local", "active_scene_id": "yard"}
    if label == "active-proposal":
        session["conversational_context"] = {"active_interlocutor": ACTIVE}
    before = copy.deepcopy({"session": session, "world": world, "scene": YARD})
    action, admission = normalized_action_from_interpretation(
        record, scene=YARD, world=world, session=session, player_text=text, known_scene_ids=lambda: ["yard"],
    )
    after = {"session": session, "world": world, "scene": YARD}
    trace("bridge-" + label, {"before": before, "after": after, "text": text, "record": record,
                              "proposal": target, "action": action, "admission": admission})
    assert admission["accepted"] is accepted
    if label.startswith("footprint-"):
        assert admission["reason"] == "ungrounded_provider_target"
    assert (action["target_id"] if action else None) == ("guard_captain" if accepted else None)
    assert before == after


@pytest.mark.parametrize("status,target_resolved,offscene", [
    (False, True, False),
    (None, True, False),
    (True, False, False),
    (True, True, True),
])
def test_failed_social_receipt_cannot_commit(replay, monkeypatch, status, target_resolved, offscene):
    resolve = social.resolve_social_action
    called = []

    def reject_after_resolver(*args, **kwargs):
        result = resolve(*args, **kwargs)
        assert result["social"]["topic_revealed"]["id"] == "patrol"
        result["success"] = status
        result["social"].update(target_resolved=target_resolved, offscene_target=offscene)
        called.append(copy.deepcopy(result))
        return result

    monkeypatch.setattr(social, "resolve_social_action", reject_after_resolver)
    request, raw = captured(EXTENDED / "T10.json")
    label = f"failed-receipt-{status}-{target_resolved}-{offscene}"
    row = replay(label, request, raw, duplicate=True)
    assert len(called) == 1
    assert row["persisted_log_resolution"]["metadata"]["rejected_social_receipt"]["success"] is status
    assert CAPTAIN not in row["response"]["gm_output"]["player_facing_text"]
    assert not row["host"].get("advance_world_tick")
    # This injected resolver did execute in the working state. The rejected
    # receipt must discard those writes, including the authored discoveries.
    row["host"].pop("offline_adapter")
    assert_read_only(row)


@pytest.mark.parametrize("action_type,condition", [
    ("social", "unknown"),
    ("exploration", "unknown"),
    ("social", "active-alternative"),
    ("social", "hidden"),
])
def test_structured_entry_rejects_missing_social_target(replay, social_calls, action_type, condition):
    target = "missing_npc"
    if condition == "active-alternative":
        request, raw = captured(EXTENDED / "T10.json")
        replay("structured-active-setup", request, raw)
    elif condition == "hidden":
        target = "guard_captain"
        world = storage.load_world()
        next(row for row in world["npcs"] if row["id"] == target)["hidden"] = True
        storage.save_world(world)
    social_calls.clear()
    before = state()
    with TestClient(api.app) as http:
        response = http.post("/api/action?ui_mode=player", json={
            "action_type": action_type,
            action_type + "_action": {"type": "question", "target_id": target, "prompt": "Ask about the patrol"},
        })
    after = state()
    row = response.json()
    trace(f"structured-{action_type}-{condition}", {
        "before": before, "after": after, "response": row, "resolver": social_calls,
    })
    assert response.status_code == 200 and not row["ok"]
    assert len(social_calls) == 1 and social_calls[0]["receipt"]["success"] is False
    assert CAPTAIN not in row["gm_output"]["player_facing_text"]
    assert before == after


def test_structured_social_accepts_selected_visible_captain(replay, social_calls):
    before = state()
    with TestClient(api.app) as http:
        response = http.post("/api/action?ui_mode=player", json={
            "action_type": "social",
            "intent": "I ask the guard captain what he knows about the missing patrol.",
            "social_action": {"type": "question", "target_id": "guard_captain"},
        })
    after = state()
    row = response.json()
    trace("structured-success", {"before": before, "after": after, "response": row, "resolver": social_calls})
    assert response.status_code == 200 and row["ok"]
    assert len(social_calls) == 1 and social_calls[0]["receipt"]["success"] is True
    assert row["gm_output"]["player_facing_text"] == CAPTAIN
    assert "lead_frontier_gate_old_milestone" in after["session"]["clue_knowledge"]
    assert before["character"] == after["character"]
