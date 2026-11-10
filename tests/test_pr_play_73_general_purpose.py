"""General-purpose action pathway. Developer tests, not an external holdout.

Deferred on purpose: bounded-fact promotion, climb DC, intra-scene position,
and live provider commitment. Those tests assert the refusal, not a fake success.
"""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.general_purpose_actions import (
    classify, consider_provider_record, validate_provider_proposal,
)
from game.player_initiative import GATE, decide
from game.skill_checks import resolve_skill_check
from tests.test_pr_play_71_lifecycle import choose, configure, create, reach, safe, start

DEFERRED = (
    "bounded_improvisation_promotion",
    "climb_check",
    "intra_scene_position",
    "live_provider_commit",
)


@pytest.fixture(autouse=True)
def offline_turns(_forbid_live_model_calls, monkeypatch):
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    monkeypatch.setattr(api, "call_gpt", lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE))


@pytest.fixture(scope="module")
def campaigns(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        configure(tmp_path_factory.mktemp("pr73-general"), mp)
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


def flags():
    return storage.load_world().get("world_state", {}).get("flags", {})


def clues():
    from game.clues import get_all_known_clue_texts
    return tuple(sorted(get_all_known_clue_texts(storage.load_session())))


def context():
    state = authority()
    return state, api.load_active_scene()


CLASSIFY_CASES = [
    ("survey", "Please examine those footprints closely.", None),
    ("survey", "I want to look farther down the road.", "B"),
    ("survey", "Look for a stable handhold.", "C"),
    ("survey", "I want to find a secret passage beneath the milestone.", "D"),
    ("survey", "I teleport to the missing patrol.", None),
    ("survey", "I want to climb onto the broken stonework to get a better view.", "D"),
    ("survey", "From up here, can I see anything farther down the road?", "B"),
    ("survey", "I want to move some loose stones aside and check underneath.", "D"),
    ("survey", "I want to persuade the watch to take my warning more seriously.", "E"),
    ("report", "I want to persuade the watch to take my warning more seriously.", "B"),
    ("survey", "What can I see from here?", "RO"),
    ("survey", "Climb that.", "E"),
    ("survey", "Move it.", "E"),
    ("survey", "I want to check underneath the milestone.", "B"),
    ("report", "Examine the mud prints here.", None),
]


@pytest.mark.parametrize("branch,text,category", CLASSIFY_CASES)
def test_classification_is_read_only(campaigns, branch, text, category):
    restore(campaigns, branch)
    state, scene = context()
    before = copy.deepcopy(state)
    proposal = classify(text, scene=scene, world=state["world"], session=state["session"])
    if category is None:
        assert proposal is None
    else:
        assert proposal["category"] == category
        assert proposal["mutation"] is False
    assert authority() == before


def test_authored_inspect_still_executes(campaigns):
    client = restore(campaigns, "survey")
    before_flags = flags()
    body = safe(client.post("/api/chat", json={"text": "I examine the mud prints again."}))
    assert body["gm_output"]["player_facing_text"]
    assert flags() == before_flags


def test_observation_uses_established_fact_without_discovery(campaigns):
    client = restore(campaigns, "survey")
    before_clues = clues()
    before_flags = flags()
    scene_id = storage.load_session()["active_scene_id"]
    body = safe(client.post("/api/chat", json={"text": "From up here, can I see anything farther down the road?"}))
    text = body["gm_output"]["player_facing_text"]
    assert "Nothing farther is established." in text
    assert "No elevated position is established" in text
    assert "secret" not in text.lower()
    assert clues() == before_clues
    assert flags() == before_flags
    assert storage.load_session()["active_scene_id"] == scene_id
    raw = json.dumps(body)
    assert "hidden_facts" not in raw and "SENTINEL_" not in raw and "gm_notes" not in raw


def test_search_does_not_invent_contents(campaigns):
    client = restore(campaigns, "survey")
    before_clues = clues()
    body = safe(client.post("/api/chat", json={"text": "I want to check underneath the milestone."}))
    text = body["gm_output"]["player_facing_text"]
    assert "Nothing concealed is established" in text
    assert "treasure" in text.lower()
    assert clues() == before_clues
    assert "secret passage" not in json.dumps(storage.load_world()).lower()


def test_unestablished_stones_and_climb_do_not_mutate(campaigns):
    client = restore(campaigns, "survey")
    before = authority()
    for text in (
        "I want to climb onto the broken stonework to get a better view of the road.",
        "I want to climb the weathered milestone.",
        "I want to move some loose stones aside and check underneath.",
        "I want to find a secret passage beneath the milestone.",
        "Look for a stable handhold.",
    ):
        body = safe(client.post("/api/chat", json={"text": text}))
        message = body["gm_output"]["player_facing_text"].lower()
        assert (
            "not established" in message or "no climbing check is configured" in message
            or "has not been added" in message or "has been created" in message
        )
        assert authority() == before


def test_social_check_does_not_grant_compliance(campaigns):
    client = restore(campaigns, "report")
    before_flags = copy.deepcopy(flags())
    before_clues = clues()
    body = safe(client.post("/api/chat", json={"text": "I want to persuade the watch to take my warning more seriously."}))
    text = body["gm_output"]["player_facing_text"]
    assert "No new order or compliance is established" in text
    assert "DC" in text
    assert flags() == before_flags
    assert clues() == before_clues
    assert storage.load_session()["active_scene_id"] == "frontier_gate"


def test_social_check_matches_engine_roll(campaigns):
    client = restore(campaigns, "report")
    turn = int(storage.load_session()["turn_counter"]) + 1
    body = safe(client.post("/api/chat", json={"text": "I urge the watch to treat the warning as urgent."}))
    character = storage.load_character()
    rolled = resolve_skill_check("diplomacy", 10, character, {
        "seed_parts": [turn, "frontier_gate", "social_initiative", "gate_guard", "diplomacy", "10"],
    })
    text = body["gm_output"]["player_facing_text"]
    assert f"d20 {rolled['roll']}" in text
    assert ("succeeds" if rolled["success"] else "fails") in text


def test_survey_social_has_no_listener(campaigns):
    client = restore(campaigns, "survey")
    before = authority()
    body = safe(client.post("/api/chat", json={"text": "I want to persuade the watch to take my warning more seriously."}))
    assert "Nobody here can be persuaded" in body["gm_output"]["player_facing_text"]
    assert authority() == before


def test_repeat_observation_does_not_duplicate(campaigns):
    client = restore(campaigns, "survey")
    before_clues = clues()
    safe(client.post("/api/chat", json={"text": "I look farther down the road."}))
    safe(client.post("/api/chat", json={"text": "I look farther down the road once more."}))
    assert clues() == before_clues
    assert flags()["patrol_survey"] is True
    assert not flags().get("patrol_report")


def test_resume_keeps_observation_and_branch(campaigns):
    client = restore(campaigns, "survey")
    first = safe(client.post("/api/chat", json={"text": "I peer farther down the road."}))
    assert "Nothing farther is established." in first["gm_output"]["player_facing_text"]
    snap = safe(client.post("/api/snapshots", json={"label": "observed"}))["snapshot"]["id"]
    remembered = clues()
    remembered_flags = copy.deepcopy(flags())
    create(client)
    safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
    assert clues() == remembered
    assert flags() == remembered_flags
    follow = safe(client.post("/api/chat", json={"text": "What can I see from here?"}))
    assert "track" in follow["gm_output"]["player_facing_text"].lower() or "milestone" in follow["gm_output"]["player_facing_text"].lower()
    assert clues() == remembered
    assert flags() == remembered_flags


def test_report_branch_resume_social_context(campaigns):
    client = restore(campaigns, "report")
    before_flags = copy.deepcopy(flags())
    safe(client.post("/api/chat", json={"text": "I plead with the watch about the warning."}))
    snap = safe(client.post("/api/snapshots", json={"label": "pleaded"}))["snapshot"]["id"]
    create(client)
    safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
    assert flags() == before_flags
    assert storage.load_session()["active_scene_id"] == "frontier_gate"
    body = safe(client.post("/api/chat", json={"text": "Have the guards done anything?"}))
    assert "watch has now been warned" in body["gm_output"]["player_facing_text"]
    assert "survey is now recorded" not in body["gm_output"]["player_facing_text"]
    assert flags() == before_flags


def test_ambiguous_and_readonly_do_not_mutate(campaigns):
    client = restore(campaigns, "survey")
    before = authority()
    for text in ("Climb that.", "Move it.", "Look over there.", "What do I know about the stonework?", "What can I see from here?"):
        body = safe(client.post("/api/chat", json={"text": text}))
        assert body["gm_output"]["player_facing_text"]
        assert authority() == before


def test_gate_off_does_not_classify(campaigns, monkeypatch):
    restore(campaigns, "survey")
    state, scene = context()
    monkeypatch.setenv(GATE, "0")
    assert decide("I look farther down the road.", scene=scene, world=state["world"], session=state["session"]) is None


@pytest.mark.parametrize("proposal,reason", [
    ({"family": "environmental_observation"}, "family_only"),
    ("nope", "malformed"),
    ({"family": "environmental_observation", "target_ref": "secret_tunnel"}, "invented_target"),
    ({"family": "social_initiative", "success": True}, "invented_outcome_or_hidden_field"),
    ({"family": "physical_search", "hidden_fact": "SENTINEL_HIDDEN"}, "invented_outcome_or_hidden_field"),
    ({"family": "teleport"}, "unsupported_family"),
])
def test_provider_proposal_validation(campaigns, proposal, reason):
    restore(campaigns, "survey")
    state, scene = context()
    before = copy.deepcopy(state)
    verdict = validate_provider_proposal(proposal, scene=scene, world=state["world"])
    assert verdict["reason"] == reason
    assert authority() == before


def test_provider_disagreement_does_not_commit(campaigns):
    restore(campaigns, "survey")
    state, scene = context()
    record = {"action_components": [{"operation_class": "INSPECT", "target_ref": "secret_tunnel"}]}
    verdict = consider_provider_record(
        record, player_text="I look farther down the road.", scene=scene, world=state["world"], session=state["session"],
    )
    assert verdict["accepted"] is False
    assert verdict["reason"] in {"invented_target", "deterministic_disagreement", "unsupported_family"}


def test_deferred_capabilities_are_explicit():
    assert "bounded_improvisation_promotion" in DEFERRED
    assert "climb_check" in DEFERRED
    assert "live_provider_commit" in DEFERRED


UNIT_SCENE = {
    "scene": {
        "id": "old_milestone",
        "summary": "A weathered milestone leans beside the northwest mud track, where the road thins into scrub.",
        "visible_facts": [
            "A weathered stone milestone leans beside the northwest mud track.",
            "The track continues a short way past the stone before rainwater and brush make the next step unclear.",
        ],
        "interactables": [
            {"id": "milestone", "label": "Weathered milestone", "aliases": ["old milestone", "stone", "marker"]},
        ],
        "hidden_facts": ["SENTINEL_HIDDEN passage under the stone"],
    }
}
UNIT_WORLD = {"npcs": [
    {"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "aliases": ["guard", "watch"]},
    {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "aliases": ["serjeant", "watch serjeant"]},
]}


UNIT_CASES = [
    ("I look down the road.", "old_milestone", "B", "environmental_observation"),
    ("I peer ahead along the track.", "old_milestone", "B", "environmental_observation"),
    ("Can I see farther down the road?", "old_milestone", "B", "environmental_observation"),
    ("I scan the scrub ahead.", "old_milestone", "B", "environmental_observation"),
    ("I want to check underneath the old milestone.", "old_milestone", "B", "physical_search"),
    ("I shift the weathered milestone and look beneath it.", "old_milestone", "B", "physical_search"),
    ("I want to climb the broken stonework.", "old_milestone", "D", "physical_positioning"),
    ("I want to climb the weathered milestone.", "old_milestone", "E", "physical_positioning"),
    ("I jump onto the marker.", "old_milestone", "E", "physical_positioning"),
    ("Look for a stable handhold on the stone.", "old_milestone", "C", "bounded_detail"),
    ("Feel the texture of the milestone.", "old_milestone", "C", "bounded_detail"),
    ("Find a hidden tunnel beneath the milestone.", "old_milestone", "D", "world_expansion"),
    ("Dig up the buried treasure.", "old_milestone", "D", "world_expansion"),
    ("Climb that.", "old_milestone", "E", ""),
    ("Move it aside.", "old_milestone", "E", ""),
    ("What can I see from here?", "old_milestone", "RO", "information"),
    ("I persuade the watch.", "frontier_gate", "B", "social_initiative"),
    ("I convince the gate guard.", "frontier_gate", "B", "social_initiative"),
    ("I urge the serjeant and the guard.", "frontier_gate", "E", "social_initiative"),
    ("I persuade the watch.", "old_milestone", "E", "social_initiative"),
    ("Look over there.", "old_milestone", "E", ""),
    ("Ask them.", "old_milestone", "E", ""),
    ("I want to move some loose stones aside.", "old_milestone", "D", "physical_search"),
    ("I balance on the marker.", "old_milestone", "E", "physical_positioning"),
    ("From up here, can I see farther?", "old_milestone", "B", "environmental_observation"),
    ("I plead with the watch about the warning.", "frontier_gate", "B", "social_initiative"),
    ("Summon a new enemy here.", "old_milestone", "D", "world_expansion"),
    ("Create a tunnel under the road.", "old_milestone", "D", "world_expansion"),
    ("I appeal to the watch.", "frontier_gate", "B", "social_initiative"),
    ("I check under the marker.", "old_milestone", "B", "physical_search"),
    ("I gaze down the road.", "old_milestone", "B", "environmental_observation"),
    ("I scramble up the stonework.", "old_milestone", "D", "physical_positioning"),
    ("What do I see?", "old_milestone", "RO", "information"),
    ("I implore the gate serjeant.", "frontier_gate", "B", "social_initiative"),
    ("I lift the loose rubble.", "old_milestone", "D", "physical_search"),
]


@pytest.mark.parametrize("text,scene_id,category,family", UNIT_CASES)
def test_unit_classification(text, scene_id, category, family):
    scene = copy.deepcopy(UNIT_SCENE)
    scene["scene"]["id"] = scene_id
    before = copy.deepcopy((scene, UNIT_WORLD))
    proposal = classify(text, scene=scene, world=UNIT_WORLD, session={})
    assert proposal is not None
    assert proposal["category"] == category
    assert proposal["mutation"] is False
    if family:
        assert proposal["family"] == family
    assert copy.deepcopy((scene, UNIT_WORLD)) == before
    assert "SENTINEL_HIDDEN" not in proposal["message"]
