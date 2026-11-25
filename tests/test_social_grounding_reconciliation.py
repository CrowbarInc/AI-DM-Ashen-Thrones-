"""Offline acceptance for conversation provenance and consequence boundaries."""
import copy

import pytest

from experiments.pr_dq.world import MARA_ANSWER, MARA_ID
from game import api, social, storage
from game.conversational_continuity import delivered_exchanges
from game.models import ChatRequest
from game.provider_budget import snapshot as provider_snapshot
from tests.test_inspection_communication_admission import gameplay_session, reason, replay, state, trace, turn_delta
from tests.test_npc_addressee_and_social_commit import social_calls
from tests.test_pr_du_player_pipeline import _seed_pr_du_world
from tests.test_pr_eb_conversational_continuity import _activate_mara
from tests.test_pr_play_post_npc_handoff import (
    CAPTAIN_FOLLOWUP, CAPTAIN_OPENING, _env, _say, client,
)
from tests.test_repeat_statement_routing_ownership import CAPTAIN, assert_read_only

MARA_OPENING = "Sergeant Mara, is the road on the other side of this gate?"
PATROL_CLUE = "social_frontier_gate_guard_captain_patrol"
PATROL_LEAD = "lead_frontier_gate_old_milestone"


def visible(row):
    return row["response"]["gm_output"]["player_facing_text"]


def clock_delta(row):
    before, after = (row[key]["session"]["clocks"] for key in ("before", "after"))
    return after["time_pressure"] - before["time_pressure"]


def assert_social(row, calls, target, *, discover=False):
    assert len(calls) == 1
    assert calls[0]["action"]["target_id"] == target
    assert calls[0]["receipt"]["success"] is True
    receipt = row["persisted_log_resolution"]
    assert receipt["success"] is True
    assert receipt["social"]["target_resolved"] is True
    assert receipt["social"]["npc_id"] == target
    assert len(row["host"]["advance_world_tick"]) == turn_delta(row) == clock_delta(row) == 1
    prior, current = (row[key]["session"] for key in ("before", "after"))
    for field in ("active_scene_id", "visited_scene_ids", "flags"):
        assert prior[field] == current[field]
    for field in ("character", "campaign", "combat", "conditions"):
        assert row["before"][field] == row["after"][field]
    assert row["before"]["world"].get("inventory") == row["after"]["world"].get("inventory")
    assert row["before"]["world"]["world_state"] == row["after"]["world"]["world_state"]
    before_scene, after_scene = (copy.deepcopy(row[key]["active_scene"]) for key in ("before", "after"))
    if discover:
        assert after_scene["scene"].pop("discovered_clues") == [
            "A patrol went missing near the old milestone.", "Investigate the old milestone",
        ]
        assert before_scene["scene"].pop("discovered_clues") == []
    assert before_scene == after_scene
    assert set(current["clue_knowledge"]) - set(prior["clue_knowledge"]) == ({PATROL_CLUE, PATROL_LEAD} if discover else set())
    if not discover:
        assert prior["clue_knowledge"] == current["clue_knowledge"]
        for field in ("pending_leads", "social_lead_event_ids"):
            assert prior.get(field) == current.get(field)
        prior_leads = copy.deepcopy(prior.get("lead_registry", {}))
        current_leads = copy.deepcopy(current.get("lead_registry", {}))
        # A repeat of the same authored topic may refresh the existing lead.
        for field in ("last_touched_turn", "last_updated_turn"):
            old = prior_leads.get(PATROL_LEAD, {}).pop(field, None)
            new = current_leads.get(PATROL_LEAD, {}).pop(field, None)
            assert new in {old, current["turn_counter"]}
        assert prior_leads == current_leads


def open_captain(replay, calls, label):
    result = replay(label + "-opening", {"text": CAPTAIN_OPENING})
    assert_social(result, calls, "guard_captain", discover=True)
    assert visible(result) == CAPTAIN
    delivered = delivered_exchanges(result["after"]["session"])[-1]
    assert delivered["speaker_id"] == "guard_captain"
    assert delivered["delivered_text"] == CAPTAIN
    calls.clear()
    return result


@pytest.mark.parametrize("label,text,expected", [
    ("natural-followup", CAPTAIN_FOLLOWUP, "guard_captain"),
    ("same-topic", "What else do you know about the missing patrol?", "guard_captain"),
    ("new-directed-request", "I tell the captain what I learned from the notice.", "guard_captain"),
    ("explicit-handoff", "I ask the Tavern Runner about the missing patrol.", "tavern_runner"),
    ("gm-world-fact", "Where was the patrol last seen?", None),
    ("gm-current-scene", "What can I see from here?", None),
])
def test_conversation_routes(replay, social_calls, label, text, expected):
    open_captain(replay, social_calls, label)
    row = replay(label, {"text": text})
    if expected:
        assert_social(row, social_calls, expected)
        if label == "natural-followup":
            assert visible(row) == CAPTAIN
    else:
        assert not social_calls
        assert_read_only(row)
        assert reason(row) not in {"unresolved_addressee", "repeat_delivered_statement"}
        assert visible(row) != CAPTAIN


@pytest.mark.parametrize("label,text,expected_reason", [
    ("explicit-recall", "What did the captain say?", "delivered_speaker_attribution"),
    ("speaker-pronoun-recall", "Repeat what he told me.", "repeat_delivered_statement"),
    ("deictic-recall", "Can you repeat that?", "repeat_delivered_statement"),
    ("t12-world-fact", "Do those prints tell us which way the patrol went?", None),
])
def test_statement_ownership(replay, social_calls, label, text, expected_reason):
    open_captain(replay, social_calls, label)
    row = replay(label, {"text": text})
    assert_read_only(row)
    assert not social_calls
    if expected_reason:
        assert reason(row) == expected_reason
        assert visible(row) == CAPTAIN
    else:
        assert reason(row) not in {"repeat_delivered_statement", "delivered_speaker_attribution", "unresolved_addressee"}
        assert visible(row) != CAPTAIN


@pytest.mark.parametrize("label,text", [
    ("pronoun-with-two-present", "I ask him about the patrol."),
    ("plural-referent", "I ask them about the patrol."),
    ("unaddressed-speech", "I ask whether he knows anything else."),
    ("unsupported-alias", "I ask Gate Guard about the patrol."),
    ("unknown-name", "I ask Captain Voss about the patrol."),
    ("absent-role", "I ask the innkeeper about the patrol."),
])
def test_unresolved_addressee(replay, social_calls, label, text):
    row = replay(label, {"text": text})
    assert_read_only(row)
    assert not social_calls
    assert visible(row) != CAPTAIN
    assert reason(row) == "unresolved_addressee"
    assert all(row["ownership"] != "npc" for row in delivered_exchanges(row["after"]["session"]))


@pytest.mark.parametrize("label", ["ambiguous-captain", "offscene", "unrelated-exchange", "speakerless"])
def test_grounding_with_confounders(replay, social_calls, label):
    if label == "ambiguous-captain":
        world = storage.load_world()
        world["npcs"].append({
            "id": "river_captain", "name": "River Captain", "aliases": ["captain"], "location": "frontier_gate",
        })
        storage._save_json(storage.WORLD_PATH, world)
        text = "I ask the captain about the patrol."
    elif label == "offscene":
        open_captain(replay, social_calls, label)
        world = storage.load_world()
        captain = next(row for row in world["npcs"] if row["id"] == "guard_captain")
        captain["location"] = "old_milestone"
        storage._save_json(storage.WORLD_PATH, world)
        text = "I ask him about the patrol."
    elif label == "unrelated-exchange":
        open_captain(replay, social_calls, label)
        text = "Which innkeeper?"
    else:
        setup = replay(label + "-opening", {"text": "What can I see from here?"})
        assert_read_only(setup)
        assert all(row["ownership"] != "npc" for row in delivered_exchanges(setup["after"]["session"]))
        text = "Could you repeat that?"

    row = replay(label, {"text": text})
    assert_read_only(row)
    assert not social_calls
    assert visible(row) != CAPTAIN
    assert delivered_exchanges(row["after"]["session"])[-1]["ownership"] != "npc"
    if label == "ambiguous-captain":
        assert reason(row) == "ordinary_contract_nonexecution"
        assert "captain" in visible(row).casefold()
    elif label == "offscene":
        assert reason(row) == "unresolved_addressee"


def test_legacy_publication_cannot_supply_addressee(client, social_calls):
    before = state()
    assert before["session"]["last_publication"]["visible"].startswith("Gate Guard says")
    assert not delivered_exchanges(before["session"])
    result = _say(client, CAPTAIN_FOLLOWUP)
    after = state()
    log = storage.load_log()[-1]["resolution"]
    trace("seeded-publication", {"before": before, "after": after, "response": result, "resolution": log})
    assert not social_calls
    assert_direct_read_only(before, after)
    assert log["metadata"]["conversational_decision"]["reason"] == "information_unresolved"
    assert "Guard Captain" not in result["visible"] and "Gate Guard" not in result["visible"]


def assert_direct_read_only(before, after):
    assert gameplay_session(before["session"]) == gameplay_session(after["session"])
    for key in before.keys() - {"session"}:
        assert before[key] == after[key], key


@pytest.mark.parametrize("label,text", [
    ("mara-pronoun", "I ask her about the north road."),
    ("mara-recall", "What was the last thing she said?"),
    ("mara-fragment-after-speech", "Which captain?"),
    ("mara-fragment-with-focus", "Which captain?"),
])
def test_mara_context(tmp_path, monkeypatch, social_calls, label, text):
    _seed_pr_du_world(tmp_path, monkeypatch)
    _env(monkeypatch)
    if label == "mara-fragment-with-focus":
        _activate_mara()
        original = None
    else:
        opening = api.chat(ChatRequest(text=MARA_OPENING))
        original = opening["gm_output"]["player_facing_text"]
        assert MARA_ANSWER.casefold() in original.casefold()
        assert len(social_calls) == 1 and social_calls[0]["receipt"]["success"] is True
        assert delivered_exchanges(storage.load_session())[-1]["speaker_id"] == MARA_ID
    social_calls.clear()
    before = state()
    ticks = []
    tick = api.advance_world_tick

    def observe_tick(*args, **kwargs):
        result = tick(*args, **kwargs)
        ticks.append(result)
        return result

    monkeypatch.setattr(api, "advance_world_tick", observe_tick)
    budget_before = len(provider_snapshot()["records"])
    reply = api.chat(ChatRequest(text=text))
    after = state()
    provider_records = len(provider_snapshot()["records"]) - budget_before
    trace(label, {"before": before, "after": after, "opening": original, "response": reply,
                  "social_calls": social_calls, "world_ticks": ticks, "provider_records": provider_records})
    assert provider_records == 0
    if label == "mara-pronoun":
        assert len(social_calls) == 1 and social_calls[0]["action"]["target_id"] == MARA_ID
        assert reply["resolution"]["success"] is True
        assert after["session"]["turn_counter"] == before["session"]["turn_counter"] + 1
        assert after["session"]["clue_knowledge"] == before["session"]["clue_knowledge"]
        assert after["character"] == before["character"]
        assert clock_delta({"before": before, "after": after}) == len(ticks) == 1
        assert after["session"]["flags"] == before["session"]["flags"]
        assert after["world"]["world_state"] == before["world"]["world_state"]
    else:
        assert not social_calls and not ticks
        assert_direct_read_only(before, after)
        if label == "mara-recall":
            assert reply["gm_output"]["player_facing_text"] == "From what has already been established: " + original
        else:
            assert "Sergeant Mara" not in reply["gm_output"]["player_facing_text"]


@pytest.mark.parametrize("label,fields", [
    ("unsuccessful", {"success": False}),
    ("indeterminate", {"success": None}),
    ("unresolved", {"target_resolved": False}),
    ("offscene", {"offscene_target": True}),
])
def test_rejected_exchange_discards_staged_consequences(replay, monkeypatch, label, fields):
    resolve = social.resolve_social_action
    seen = []

    def reject(*args, **kwargs):
        receipt = resolve(*args, **kwargs)
        assert receipt["success"] is True
        assert receipt["social"]["topic_revealed"]["id"] == "patrol"
        receipt.update({key: value for key, value in fields.items() if key == "success"})
        receipt["social"].update({key: value for key, value in fields.items() if key != "success"})
        seen.append(copy.deepcopy(receipt))
        return receipt

    monkeypatch.setattr(social, "resolve_social_action", reject)
    row = replay("rejected-" + label, {"text": CAPTAIN_OPENING}, duplicate=True)
    assert len(seen) == 1
    trace("rejected-" + label + "-receipt", seen[0])
    assert "rejected_social_receipt" in row["persisted_log_resolution"]["metadata"]
    assert visible(row) != CAPTAIN
    assert_read_only(row)


@pytest.mark.parametrize("label,text,setup,successful", [
    ("initial-discovery", CAPTAIN_OPENING, False, True),
    ("contextual-ask", CAPTAIN_FOLLOWUP, True, True),
    ("statement-recall", "Could you repeat that?", True, False),
    ("unresolved-ask", "I ask him about the patrol.", False, False),
])
def test_duplicate_preserves_first_result(replay, social_calls, label, text, setup, successful):
    if setup:
        open_captain(replay, social_calls, "duplicate-" + label)
    row = replay("duplicate-" + label, {"text": text}, duplicate=True)
    if successful:
        assert_social(row, social_calls, "guard_captain", discover=not setup)
    else:
        assert not social_calls
        assert_read_only(row)
    assert row["provider_records"] == 0
