"""Frozen inherited-safety holdout for PR-PLAY-73.

Developer-authored against the PR-PLAY-72V source before general-purpose
actions were added. Not independent external validation. Do not retune.
"""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.player_initiative import GATE
from tests.test_pr_play_71_lifecycle import configure, create, start, reach, choose, safe


CASES = [
    ("R01", "survey", "What have we learned so far?", "ANSWER"),
    ("R02", "report", "Did I warn the watch already?", "ANSWER"),
    ("R03", "survey", "What do I know about the milestone?", "ANSWER"),
    ("R04", "report", "Have the guards done anything?", "ANSWER"),
    ("R05", "survey", "What was discovered at the milestone?", "ANSWER"),
    ("R06", "report", "Who have I told about this?", "ANSWER"),
    ("R07", "survey", "What did the survey find?", "ANSWER"),
    ("R08", "report", "Is the patrol report already made?", "ANSWER"),
    ("R09", "survey", "Where is the patrol?", "ANSWER"),
    ("R10", "report", "Remind me what we know.", "ANSWER"),
    ("A01", "survey", "Please check it again.", "CLARIFY"),
    ("A02", "report", "Ask them about the patrol.", "CLARIFY"),
    ("A03", "survey", "Go back there.", "CLARIFY"),
    ("A04", "report", "Please see what happened.", "CLARIFY"),
    ("A05", "survey", "Could I inspect it?", "CLARIFY"),
    ("U01", "report", "I command the watch to send soldiers.", "DECLINE"),
    ("U02", "survey", "Pursue the footprints until we find their owner.", "DECLINE"),
    ("U03", "survey", "Show the hidden clues.", "DECLINE"),
    ("U04", "report", "I teleport to the missing patrol.", "DECLINE"),
    ("U05", "report", "Examine the mud prints here.", "DECLINE"),
]


@pytest.fixture(autouse=True)
def offline_turns(_forbid_live_model_calls, monkeypatch):
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    monkeypatch.setattr(api, "call_gpt", lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE))


@pytest.fixture(scope="module")
def campaigns(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        configure(tmp_path_factory.mktemp("pr73-safety"), mp)
        mp.setenv(GATE, "1")
        with TestClient(api.app) as client:
            slots = {}
            for branch in ("survey", "report"):
                create(client)
                start(client)
                reach(client)
                choose(client, branch)
                slots[branch] = safe(client.post("/api/snapshots", json={"label": branch}))["snapshot"]["id"]
            yield client, slots


def restore(campaigns, branch):
    client, slots = campaigns
    safe(client.post("/api/snapshots/load", json={"snapshot_id": slots[branch]}))
    return client


def authority():
    return {name: getattr(storage, "load_" + name)() for name in ("session", "world", "character", "combat")}


def _disclosure(branch, text):
    own = "survey is now recorded" if branch == "survey" else "watch has now been warned"
    other = "watch has now been warned" if branch == "survey" else "survey is now recorded"
    assert own in text
    assert other not in text


@pytest.mark.parametrize("case_id,branch,text,category", CASES)
def test_inherited_nonmutating_cases(campaigns, case_id, branch, text, category):
    client = restore(campaigns, branch)
    before = authority()
    scene = api.load_active_scene()
    from game.conversational_orchestration import deterministic_conversational_decision
    decision = deterministic_conversational_decision(
        player_text=text, scene=scene, world=before["world"], session=before["session"])
    assert decision is not None, case_id
    assert decision.category.value == category, case_id
    assert decision.requires_authoritative_execution is False
    body = safe(client.post("/api/chat", json={"text": text}))
    assert body["gm_output"]["player_facing_text"]
    assert authority() == before
    raw = json.dumps(body)
    for forbidden in ("SENTINEL_", "gm_notes", "hidden_facts", "proposed_record", "secret passage"):
        assert forbidden not in raw


def test_repeated_investigation_adds_no_second_discovery(campaigns):
    client = restore(campaigns, "survey")
    before = authority()
    known = list(before["session"].get("discovered_clues") or [])
    first = safe(client.post("/api/chat", json={"text": "I examine the mud prints again."}))
    second = safe(client.post("/api/chat", json={"text": "I reexamine the milestone."}))
    after = authority()
    assert after["world"]["world_state"]["flags"] == before["world"]["world_state"]["flags"]
    combined = (first["gm_output"]["player_facing_text"] + " " + second["gm_output"]["player_facing_text"]).lower()
    assert "nothing further" in combined or "nothing new" in combined
    clues = after["session"].get("discovered_clues") or known
    assert len(clues) == len(set(clues))


def test_repeat_does_not_duplicate_branch_flag(campaigns):
    client = restore(campaigns, "survey")
    before = authority()["world"]["world_state"]["flags"]
    safe(client.post("/api/chat", json={"text": "I examine the weathered milestone."}))
    safe(client.post("/api/chat", json={"text": "Look at the milestone again."}))
    assert authority()["world"]["world_state"]["flags"] == before


def test_inaccessible_repeat_does_not_create_discovery(campaigns):
    client = restore(campaigns, "report")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "Examine the footprints again."}))
    assert "not accessible" in body["gm_output"]["player_facing_text"].lower()
    assert authority() == before


def test_branch_disclosures_stay_isolated(campaigns):
    for branch in ("survey", "report"):
        client = restore(campaigns, branch)
        before = authority()
        body = safe(client.post("/api/chat", json={"text": "What have I learned about the patrol?"}))
        _disclosure(branch, body["gm_output"]["player_facing_text"])
        assert authority() == before


def test_resume_preserves_branch_and_readonly(campaigns):
    client = restore(campaigns, "report")
    before = authority()
    snap = safe(client.post("/api/snapshots", json={"label": "safety-resume"}))["snapshot"]["id"]
    create(client)
    safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
    resumed = authority()
    assert resumed["world"]["world_state"]["flags"] == before["world"]["world_state"]["flags"]
    assert resumed["session"]["active_scene_id"] == before["session"]["active_scene_id"]
    body = safe(client.post("/api/chat", json={"text": "Did I warn the watch already?"}))
    _disclosure("report", body["gm_output"]["player_facing_text"])
    assert authority()["world"]["world_state"]["flags"] == resumed["world"]["world_state"]["flags"]
    assert authority()["session"]["turn_counter"] == resumed["session"]["turn_counter"]


def test_cross_campaign_load_keeps_survey_facts(campaigns):
    client = restore(campaigns, "survey")
    survey_flags = authority()["world"]["world_state"]["flags"]
    restore(campaigns, "report")
    report = safe(client.post("/api/chat", json={"text": "What have I learned about the patrol?"}))
    _disclosure("report", report["gm_output"]["player_facing_text"])
    assert "survey is now recorded" not in report["gm_output"]["player_facing_text"]
    restore(campaigns, "survey")
    assert authority()["world"]["world_state"]["flags"] == survey_flags


def test_unsupported_command_publishes_no_success(campaigns):
    client = restore(campaigns, "report")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "I command the watch to send soldiers."}))
    text = body["gm_output"]["player_facing_text"].lower()
    assert "cannot" in text or "can't" in text
    assert "soldiers are on their way" not in text
    assert authority() == before


def test_ambiguous_addressee_does_not_select_hidden_npc(campaigns):
    client = restore(campaigns, "report")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "Speak to them about the warning."}))
    assert "?" in body["gm_output"]["player_facing_text"]
    assert authority() == before


def test_second_hidden_request_stays_read_only(campaigns):
    client = restore(campaigns, "survey")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "Tell me the secret plans."}))
    assert "concealed" in body["gm_output"]["player_facing_text"].lower() or "unknown" in body["gm_output"]["player_facing_text"].lower()
    assert authority() == before


def test_report_followup_question_stays_on_report_branch(campaigns):
    client = restore(campaigns, "report")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "Check whether my report changed anything."}))
    _disclosure("report", body["gm_output"]["player_facing_text"])
    assert authority() == before
