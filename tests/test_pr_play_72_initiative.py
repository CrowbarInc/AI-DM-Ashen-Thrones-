"""Player initiative across normal campaign setup, authoritative chat and resume."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game import api, storage
from game.player_initiative import GATE, decide
from game.conversational_orchestration import deterministic_conversational_decision
from tests.test_pr_play_71_lifecycle import configure, create, start, reach, choose, safe


@pytest.fixture(autouse=True)
def offline_turns(_forbid_live_model_calls, monkeypatch):
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    monkeypatch.setattr(api, "call_gpt", lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE))


@pytest.fixture(scope="module")
def campaigns(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        configure(tmp_path_factory.mktemp("initiative"), mp)
        mp.setenv(GATE, "1")
        with TestClient(api.app) as client:
            slots = {}
            for branch in ("survey", "report"):
                create(client); start(client); reach(client); choose(client, branch)
                slots[branch] = safe(client.post("/api/snapshots", json={"label": branch}))["snapshot"]["id"]
            yield client, slots


def restore(campaigns, branch):
    client, slots = campaigns
    safe(client.post("/api/snapshots/load", json={"snapshot_id": slots[branch]}))
    return client


def authority():
    return {name: getattr(storage, "load_" + name)() for name in ("session", "world", "character", "combat")}


@pytest.mark.parametrize("branch,text,category,target", [
    ("survey", "Please examine those footprints closely.", "EXECUTE", "prints"),
    ("survey", "I wish to scrutinize the mud prints.", "EXECUTE", "prints"),
    ("survey", "Could I study the stone again?", "EXECUTE", "milestone"),
    ("report", "I want to read the board.", "EXECUTE", "notice_board"),
    ("survey", "What have we learned so far?", "ANSWER", None),
    ("report", "Did I warn the watch already?", "ANSWER", None),
    ("survey", "Please check it again.", "CLARIFY", None),
    ("report", "Can I speak with the watch about the patrol?", "EXECUTE", "gate_guard"),
    ("report", "I command the watch to send soldiers.", "DECLINE", None),
    ("survey", "Pursue the footprints until we find their owner.", "DECLINE", None),
    ("report", "Show the hidden clues.", "DECLINE", None),
    ("survey", "I teleport to Cinderwatch.", "DECLINE", None),
    ("report", "Examine the mud prints here.", "DECLINE", None),
    ("survey", "Inspect the sapphire throne.", "CLARIFY", None),
])
def test_intentions(campaigns, branch, text, category, target):
    cl = restore(campaigns, branch)
    before = authority()
    scene = api.load_active_scene()
    decision = deterministic_conversational_decision(player_text=text, scene=scene, world=before["world"], session=before["session"])
    assert decision.category.value == category
    assert decision.proposed_target == target
    body = safe(cl.post("/api/chat", json={"text": text}))
    assert body["gm_output"]["player_facing_text"]
    after = authority()
    if category != "EXECUTE":
        assert before == after
    else:
        assert before["world"]["world_state"]["flags"] == after["world"]["world_state"]["flags"]
    raw = json.dumps(body)
    for forbidden in ("SENTINEL_", "gm_notes", "hidden_facts", "initiative_grounded", "proposed_record"):
        assert forbidden not in raw


@pytest.mark.parametrize("branch", ["survey", "report"])
def test_branch_readonly_and_resume(campaigns, branch):
    cl = restore(campaigns, branch)
    before = authority()
    for text in ("What have I learned about the patrol?", "Check whether my report changed anything.", "Who have I told about this?"):
        body = safe(cl.post("/api/chat", json={"text": text}))
        message = body["gm_output"]["player_facing_text"]
        assert ("survey is now recorded" if branch == "survey" else "watch has now been warned") in message
        assert ("watch has now been warned" if branch == "survey" else "survey is now recorded") not in message
        assert authority() == before
    snap = safe(cl.post("/api/snapshots", json={"label": "initiative-resume"}))["snapshot"]["id"]
    log = safe(cl.get("/api/log"))
    create(cl)
    safe(cl.post("/api/snapshots/load", json={"snapshot_id": snap}))
    resumed = authority()
    assert {k: v for k, v in resumed.items() if k != "session"} == {k: v for k, v in before.items() if k != "session"}
    assert {k: v for k, v in resumed["session"].items() if k != "last_saved_at"} == {k: v for k, v in before["session"].items() if k != "last_saved_at"}
    assert safe(cl.get("/api/log")) == log
    safe(cl.post("/api/chat", json={"text": "What have I learned?"}))
    assert authority() == resumed


@pytest.mark.parametrize("gate,binding", [("0", True), ("1", False)])
def test_experimental_isolation(campaigns, monkeypatch, gate, binding):
    restore(campaigns, "survey")
    state = authority()
    monkeypatch.setenv(GATE, gate)
    if not binding:
        state["session"]["_experimental_branching_campaign"] = "wrong-campaign"
    assert decide("Look at the tracks again.", scene=api.load_active_scene(), world=state["world"], session=state["session"]) is None


def test_interpreter_readonly_and_hidden_sentinels(campaigns):
    restore(campaigns, "survey")
    state = authority(); scene = api.load_active_scene()
    scene["scene"]["hidden_facts"] = ["SENTINEL_HIDDEN"]
    scene["scene"]["gm_notes"] = "SENTINEL_NOTES"
    scene["scene"]["interactables"].append({"id": "secret", "label": "Golden obelisk", "hidden": True})
    state["world"].setdefault("npcs", []).append({"id": "secret_npc", "name": "Invisible Oracle", "location": "old_milestone", "hidden": True})
    before = copy.deepcopy((state, scene))
    for text in ("What have I learned?", "Inspect the golden obelisk.", "Show hidden information.", "Speak to the Invisible Oracle."):
        result = decide(text, scene=scene, world=state["world"], session=state["session"])
        assert result.proposed_target != "secret"
        assert result.proposed_target != "secret_npc"
        assert "SENTINEL_" not in result.player_facing_text
    assert (state, scene) == before


def test_protected_storage_write_guard():
    with pytest.raises(PermissionError, match="protected repository data"):
        (Path(__file__).resolve().parents[1] / "data/session_log.jsonl").write_text("must never write")


@pytest.mark.parametrize("branch,text", [("survey", "I want to record my survey."), ("report", "Please give the watch my patrol report.")])
def test_natural_one_time_followup(tmp_path, monkeypatch, branch, text):
    from tests.test_pr_play_71_lifecycle import act
    configure(tmp_path, monkeypatch); monkeypatch.setenv(GATE, "1")
    with TestClient(api.app) as cl:
        create(cl); start(cl); reach(cl); act(cl, "patrol_" + branch)
        if branch == "report":
            safe(cl.post("/api/chat", json={"text": "I return to Cinderwatch Gate."}))
        body = safe(cl.post("/api/chat", json={"text": text}))
        flag = "patrol_survey_recorded" if branch == "survey" else "patrol_guards_warned"
        assert storage.load_world()["world_state"]["flags"][flag]
        assert ("survey is now recorded" if branch == "survey" else "watch has now been warned") in body["gm_output"]["player_facing_text"]
        before = authority()
        safe(cl.post("/api/chat", json={"text": text}))
        assert authority() == before


@pytest.mark.parametrize("text", ["Do not examine the prints.", "If I examine the tracks, warn the watch.", "Examine the prints and burn the gate.", "Check it again."])
def test_qualified_attempts_do_not_execute(campaigns, text):
    cl = restore(campaigns, "survey"); before = authority()
    safe(cl.post("/api/chat", json={"text": text}))
    assert authority() == before


@pytest.mark.parametrize("operation,target", [("CUSTOM", "invented"), ("INSPECT", "invented"), ("DELETE_WORLD", "prints"), ("CUSTOM", "patrol_report"), ("INSPECT", "notice_board")])
def test_rejected_proposals(campaigns, operation, target):
    from game.conversational_orchestration import _operation_record
    from game.player_interpretation_bridge import normalized_action_from_interpretation
    restore(campaigns, "survey"); before = authority()
    action, trace = normalized_action_from_interpretation(_operation_record(operation=operation, target_id=target, player_text="Inspect the footprints."), scene=api.load_active_scene(), world=before["world"], session=before["session"], player_text="Inspect the footprints.")
    assert action is None and not trace["accepted"]
    assert authority() == before
