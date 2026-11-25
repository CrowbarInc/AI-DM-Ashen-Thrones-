"""Unmatched person references and DM information requests.

The visible roster is not a substitute for a person the player named.
"Tell me about ..." asks the DM. "I ask someone" can still name the people
who are actually present.
"""
import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.interaction_completion import addressed_person_nominal
from game.ordinary_semantic_ownership import assess_addressee_grounding, gm_information_disposition
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate

HIDDEN = (
    "coordinated signal",
    "noble house",
    "northwest mud track",
    "ash cowl",
)


def _quiet():
    session = storage.load_session()
    return {
        "turn": session.get("turn_counter"),
        "scene": session.get("active_scene_id"),
        "clocks": copy.deepcopy(session.get("clocks")),
        "runtime": copy.deepcopy(session.get("npc_runtime")),
        "receipts": copy.deepcopy(session.get("mechanical_action_receipts")),
        "inventory": copy.deepcopy(storage.load_character().get("inventory")),
        "ruleset": copy.deepcopy(session.get("ruleset_binding")),
        "flags": copy.deepcopy((storage.load_world().get("world_state") or {}).get("flags")),
    }


def _chat(client, text, request_id):
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": text, "client_request_id": request_id},
    )
    body = response.json()
    visible = (body.get("gm_output") or {}).get("player_facing_text") or ""
    return response.status_code, visible


@pytest.fixture()
def gate(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    for key in (
        "ASHEN_DISABLE_PROVIDER_CALLS",
        "ASHEN_DISABLE_LIVE_INTERPRETATION",
        "ASHEN_DISABLE_EXPRESSION_GENERATION",
        "ASHEN_DISABLE_PROVIDER_RETRIES",
        "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT",
    ):
        monkeypatch.setenv(key, "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    before = _quiet()
    providers = len(snapshot()["records"])
    with TestClient(app) as client:
        yield client, before, providers
    _LANES.clear()


def _loaded():
    return storage.load_active_scene(), storage.load_world(), storage.load_session()


def test_explicit_captain_still_binds(gate):
    scene, world, session = _loaded()
    grounding = assess_addressee_grounding(
        "I ask the Guard Captain about the patrol.", scene=scene, world=world, session=session,
    )
    assert grounding["target_id"] == "guard_captain"
    assert grounding["operation_eligibility"] == "executable"
    assert "which person" not in grounding["clarification"].casefold()


def test_runner_alias_and_guard_description_still_bind(gate):
    scene, world, session = _loaded()
    runner = assess_addressee_grounding(
        "I ask the tavern runner about the stew.", scene=scene, world=world, session=session,
    )
    guard = assess_addressee_grounding(
        "I ask the guard about the patrol.", scene=scene, world=world, session=session,
    )
    assert runner["target_id"] == "tavern_runner"
    assert runner["operation_eligibility"] == "executable"
    assert guard["target_id"] == "guard_captain"
    assert guard["operation_eligibility"] == "executable"


def test_someone_still_offers_only_the_present_people(gate):
    scene, world, session = _loaded()
    grounding = assess_addressee_grounding(
        "I ask someone about the patrol.", scene=scene, world=world, session=session,
    )
    labels = {choice["label"] for choice in grounding["choices"]}
    assert grounding["operation_eligibility"] == "requires_clarification"
    assert grounding["target_id"] is None
    assert labels == {"Guard Captain", "Tavern Runner"}


def test_unmatched_description_does_not_offer_the_roster(gate):
    scene, world, session = _loaded()
    grounding = assess_addressee_grounding(
        "I ask the velvet inquisitor about the gate.", scene=scene, world=world, session=session,
    )
    assert grounding["target_resolution"] == "unresolved"
    assert grounding["choices"] == []
    assert "velvet inquisitor" in grounding["clarification"].casefold()
    assert "guard captain" not in grounding["clarification"].casefold()


def test_unmatched_name_does_not_offer_the_roster(gate):
    scene, world, session = _loaded()
    grounding = assess_addressee_grounding(
        "I ask Warden Cole about the gate.", scene=scene, world=world, session=session,
    )
    assert grounding["target_resolution"] == "unresolved"
    assert grounding["target_id"] is None
    assert grounding["choices"] == []
    assert grounding["mutation_eligibility"] is False
    assert "warden cole" in grounding["clarification"].casefold()
    assert "guard captain" not in grounding["clarification"].casefold()
    assert "tavern runner" not in grounding["clarification"].casefold()


def test_threadbare_watcher_is_known_and_not_replaced(gate):
    scene, world, session = _loaded()
    text = "Tell me the hidden motives of the threadbare watcher."
    assert "threadbare watcher" in addressed_person_nominal(text).casefold()
    row = gm_information_disposition(text, scene=scene, world=world, session=session)
    assert row["disposition"] == "unknown_information"
    assert row["person_id"] == "threadbare_watcher"
    grounding = assess_addressee_grounding(text, scene=scene, world=world, session=session)
    assert grounding["communication_ownership"] == "gm_directed"
    assert grounding["direct_address"] is False
    assert grounding["choices"] == []


def test_patrol_question_is_gm_directed(gate):
    scene, world, session = _loaded()
    text = "Tell me about the patrol."
    assert addressed_person_nominal(text) == "me"
    row = gm_information_disposition(text, scene=scene, world=world, session=session)
    assert row["disposition"] == "public_fact"
    assert row["person"] is None
    assert any("patrol" in line.casefold() for line in row["lines"])
    grounding = assess_addressee_grounding(text, scene=scene, world=world, session=session)
    assert grounding["communication_ownership"] == "gm_directed"
    assert grounding["choices"] == []


def test_http_watcher_and_patrol_do_not_substitute(gate):
    client, before, providers = gate
    code, watcher = _chat(client, "Tell me the hidden motives of the threadbare watcher.", "watcher")
    after_watcher = _quiet()
    assert code == 200
    low = watcher.casefold()
    assert "threadbare watcher" in low
    assert "guard captain" not in low
    assert "tavern runner" not in low
    assert "which person" not in low
    assert "nothing has been attempted" in low
    for secret in HIDDEN:
        assert secret not in low
    assert after_watcher["turn"] == before["turn"]
    assert after_watcher["runtime"] == before["runtime"]
    assert after_watcher["ruleset"] == before["ruleset"]
    assert after_watcher["flags"] == before["flags"]
    assert after_watcher["inventory"] == before["inventory"]

    code, patrol = _chat(client, "Tell me about the patrol.", "patrol")
    after_patrol = _quiet()
    patrol_low = patrol.casefold()
    assert code == 200
    assert "missing patrol" in patrol_low
    assert "which person" not in patrol_low
    assert "guard captain" not in patrol_low
    for secret in HIDDEN:
        assert secret not in patrol_low
    assert after_patrol["turn"] == before["turn"]
    assert after_patrol["scene"] == before["scene"]
    assert len(snapshot()["records"]) == providers


def test_http_followups_keep_identity_and_subject(gate):
    client, before, providers = gate
    _, first = _chat(client, "Tell me the hidden motives of the threadbare watcher.", "watch-1")
    _, second = _chat(client, "Tell me the hidden motives of the threadbare watcher again.", "watch-2")
    for visible in (first, second):
        low = visible.casefold()
        assert "threadbare watcher" in low
        assert "guard captain" not in low
        assert "tavern runner" not in low
        assert "coordinated signal" not in low
    _, patrol = _chat(client, "Tell me about the patrol.", "patrol-1")
    _, follow = _chat(client, "What else about the patrol?", "patrol-2")
    assert "missing patrol" in patrol.casefold()
    assert "missing patrol" in follow.casefold()
    assert "which person" not in follow.casefold()
    assert _quiet()["turn"] == before["turn"]
    assert len(snapshot()["records"]) == providers


def test_http_someone_then_captain_executes_once(gate):
    client, before, _providers = gate
    code, clarify = _chat(client, "I ask someone about the patrol.", "someone")
    held = _quiet()
    assert code == 200
    assert "guard captain" in clarify.casefold()
    assert "tavern runner" in clarify.casefold()
    assert held["turn"] == before["turn"]
    assert held["runtime"] == before["runtime"]
    _, chosen = _chat(client, "The Guard Captain.", "captain-choice")
    after = _quiet()
    assert "patrol went missing" in chosen.casefold()
    assert after["turn"] == before["turn"] + 1
    _, repeat = _chat(client, "The Guard Captain.", "captain-repeat")
    repeated = _quiet()
    assert repeated["turn"] == after["turn"]
    assert repeated["runtime"] == after["runtime"]
    assert repeated["receipts"] == after["receipts"]
    assert "tavern runner" not in repeat.casefold()
    assert "d20=" not in repeat.casefold()


def test_http_known_captain_and_indirect_followup(gate):
    client, before, providers = gate
    _, asked = _chat(client, "I ask the Guard Captain about the patrol.", "ask-captain")
    assert "patrol went missing" in asked.casefold()
    assert _quiet()["turn"] == before["turn"] + 1
    _, follow = _chat(client, "What did the guard captain say about the patrol?", "recall-captain")
    assert "patrol went missing" in follow.casefold()
    assert "which person" not in follow.casefold()
    assert len(snapshot()["records"]) == providers


def test_http_known_npc_hidden_motives_are_not_invented(gate):
    client, before, providers = gate
    _, visible = _chat(client, "Tell me the hidden motives of the Guard Captain.", "captain-motives")
    low = visible.casefold()
    assert "guard captain" in low
    assert "not established" in low
    assert "which person" not in low
    assert "couldn't tell you" not in low
    for secret in HIDDEN:
        assert secret not in low
    assert _quiet()["turn"] == before["turn"]
    assert _quiet()["runtime"] == before["runtime"]
    assert len(snapshot()["records"]) == providers


def test_http_unmatched_persuade_does_not_check_someone_else(gate):
    client, before, providers = gate
    _, visible = _chat(client, "I try to persuade Warden Cole.", "persuade-cole")
    low = visible.casefold()
    assert "d20=" not in low
    assert "guard captain" not in low or "no present person" in low or "warden cole" in low
    assert "trust is now" not in low
    assert _quiet()["turn"] == before["turn"]
    assert _quiet()["runtime"] == before["runtime"]
    assert _quiet()["receipts"] == before["receipts"]
    assert _quiet()["ruleset"] == before["ruleset"]
    assert len(snapshot()["records"]) == providers


def test_http_negation_and_conditional_still_withhold(gate):
    client, before, providers = gate
    _, negated = _chat(client, "I do not persuade the guard captain.", "negated")
    _, conditional = _chat(client, "If he is listening, I try to persuade the guard captain.", "conditional")
    assert "nothing has been attempted" in negated.casefold()
    assert "conditional" in conditional.casefold()
    assert "d20=" not in negated and "d20=" not in conditional
    after = _quiet()
    assert after["turn"] == before["turn"]
    assert after["runtime"] == before["runtime"]
    assert after["ruleset"] == before["ruleset"]
    assert len(snapshot()["records"]) == providers


def test_http_established_actor_is_not_replaced_by_the_roster(gate):
    client, before, providers = gate
    _, visible = _chat(client, "I ask the threadbare watcher about the gate.", "ask-watcher")
    low = visible.casefold()
    assert "threadbare watcher" in low
    assert "which person do you mean: guard captain" not in low
    assert "nothing has been attempted" in low
    for secret in HIDDEN:
        assert secret not in low
    assert _quiet()["turn"] == before["turn"]
    assert _quiet()["runtime"] == before["runtime"]
    assert len(snapshot()["records"]) == providers


def test_active_runner_tell_me_more_stays_with_that_runner(gate):
    scene, world, session = _loaded()
    session = copy.deepcopy(session)
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
    }
    text = "Tell me more about that."
    assert gm_information_disposition(text, scene=scene, world=world, session=session) is None
    grounding = assess_addressee_grounding(text, scene=scene, world=world, session=session)
    assert grounding["target_id"] == "tavern_runner"
    assert grounding["target_provenance"] == "established_interlocutor"
    assert grounding["operation_eligibility"] == "executable"
    assert grounding["communication_ownership"] == "npc_directed"


def test_http_retry_does_not_duplicate_a_withheld_reference(gate):
    client, before, providers = gate
    _, first = _chat(client, "I ask Warden Cole about the gate.", "cole-1")
    _, second = _chat(client, "I ask Warden Cole about the gate.", "cole-2")
    for visible in (first, second):
        low = visible.casefold()
        assert "warden cole" in low
        assert "which person do you mean: guard captain" not in low
        assert "nothing has been attempted" in low
    assert _quiet()["turn"] == before["turn"]
    assert _quiet()["runtime"] == before["runtime"]
    assert len(snapshot()["records"]) == providers
