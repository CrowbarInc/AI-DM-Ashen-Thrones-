"""Carried-object grounding and unresolved-target turn withholding.

Examination of a resolved inventory object stays on the existing information
contract: identity can be acknowledged, and unestablished details stay
unestablished. That is not a successful examination.
"""
import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate
from tests.test_ordinary_semantic_admission import state


UNMATCHED = "Nothing here matches that reference. Which established object do you mean?"
NOTICE = "The missing patrol was last seen taking the northwest mud track past the crates."


@pytest.fixture
def client(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    for key in (
        "ASHEN_DISABLE_PROVIDER_CALLS",
        "ASHEN_DISABLE_LIVE_INTERPRETATION",
        "ASHEN_DISABLE_EXPRESSION_GENERATION",
        "ASHEN_DISABLE_PROVIDER_RETRIES",
    ):
        monkeypatch.setenv(key, "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    with TestClient(app) as http:
        yield http


def _post(client, text, key):
    before = state()
    providers = len(snapshot()["records"])
    response = client.post("/api/chat?ui_mode=player", json={"text": text, "client_request_id": key})
    after = state()
    assert response.status_code == 200
    body = response.json()
    visible = body["gm_output"]["player_facing_text"]
    logged = storage.load_log()
    latest = logged[-1] if logged else {}
    decision = ((latest.get("resolution") or {}).get("metadata") or {}).get("conversational_decision") or {}
    return {
        "visible": visible,
        "before": before,
        "after": after,
        "providers": len(snapshot()["records"]) - providers,
        "decision": decision,
        "body": body,
        "turn_delta": after["session"].get("turn_counter") - before["session"].get("turn_counter"),
    }


def _auth(result):
    return (result["decision"].get("authorization") or {})


def _quiet(result):
    assert result["providers"] == 0
    assert result["before"]["character"] == result["after"]["character"]
    assert result["before"]["world"] == result["after"]["world"]
    assert result["before"]["scene"] == result["after"]["scene"]
    assert result["before"]["combat"] == result["after"]["combat"]
    assert result["before"]["session"].get("clocks") == result["after"]["session"].get("clocks")
    assert result["before"]["session"].get("active_scene_id") == result["after"]["session"].get("active_scene_id")


def _add_book(name, item_id, aliases=None):
    character = storage.load_character()
    row = {"id": item_id, "name": name, "quantity": 1, "usable": False}
    if aliases:
        row["aliases"] = aliases
    character["inventory"].append(row)
    storage.save_character(character)


def _add_scene_book():
    scene = storage.load_active_scene()
    scene["scene"]["interactables"].append({
        "id": "gate_ledger",
        "label": "gate ledger",
        "name": "Gate ledger",
        "aliases": ["book", "ledger"],
        "type": "investigate",
        "reveals_clue": "ledger_secret",
    })
    scene["scene"].setdefault("discoverable_clues", []).append({
        "id": "ledger_secret",
        "text": "CANARY_LEDGER_EXAMINATION",
    })
    storage.save_scene(scene)


def test_unique_carried_spellbook_short_reference(client):
    result = _post(client, "I examine the book.", "book")
    _quiet(result)
    assert result["turn_delta"] == 0
    assert "Spellbook" in result["visible"]
    assert "not established" in result["visible"]
    assert "Nothing here matches" not in result["visible"]
    assert NOTICE not in result["visible"]
    assert "closer looking yields" not in result["visible"].casefold()
    assert _auth(result).get("subject_id") == "spellbook"
    assert _auth(result).get("information_disposition") == "ANSWERABLE"
    assert _auth(result).get("reference_disposition") == "RESOLVED"


def test_explicit_spellbook_and_spacing_variant(client):
    explicit = _post(client, "I examine the spellbook.", "explicit")
    spaced = _post(client, "I examine the spell book.", "spaced")
    for result in (explicit, spaced):
        _quiet(result)
        assert result["turn_delta"] == 0
        assert "Spellbook" in result["visible"]
        assert "not established" in result["visible"]
        assert _auth(result).get("subject_id") == "spellbook"
        assert _auth(result).get("reference_disposition") == "RESOLVED"


def test_authored_alias_resolves_without_a_new_identity(client):
    character = storage.load_character()
    character["inventory"][0]["aliases"] = ["grimoire"]
    storage.save_character(character)
    result = _post(client, "I examine the grimoire.", "alias")
    _quiet(result)
    assert result["turn_delta"] == 0
    assert "Spellbook" in result["visible"]
    assert _auth(result).get("subject_id") == "spellbook"
    assert result["after"]["character"]["inventory"][0]["aliases"] == ["grimoire"]


def test_unique_scene_object_still_examines(client):
    before_turn = storage.load_session()["turn_counter"]
    result = _post(client, "I examine the notice board.", "notice")
    assert result["providers"] == 0
    assert NOTICE in result["visible"]
    assert "Spellbook" not in result["visible"]
    assert result["after"]["session"]["turn_counter"] == before_turn + 1
    assert result["before"]["character"] == result["after"]["character"]
    assert result["after"]["session"]["active_scene_id"] == "frontier_gate"


def test_two_carried_books_are_ambiguous(client):
    _add_book("Prayer book", "prayer_book")
    result = _post(client, "I examine the book.", "two-books")
    _quiet(result)
    assert result["turn_delta"] == 0
    low = result["visible"].casefold()
    assert "which object" in low
    assert "spellbook" in low
    assert "prayer book" in low
    assert "not established" not in low
    assert "records prayer book" not in low
    assert _auth(result).get("information_disposition") == "AMBIGUOUS"
    assert _auth(result).get("reference_disposition") == "AMBIGUOUS"
    assert _auth(result).get("subject_id") in (None, "")


def test_carried_book_plus_scene_book_is_ambiguous(client):
    _add_scene_book()
    result = _post(client, "I examine the book.", "scene-book")
    _quiet(result)
    assert result["turn_delta"] == 0
    low = result["visible"].casefold()
    assert "which object" in low
    assert "spellbook" in low
    assert "gate ledger" in low
    assert "canary_ledger_examination" not in low
    assert "provider calls are disabled" not in low
    assert _auth(result).get("reference_disposition") == "AMBIGUOUS"


def test_clarifying_the_spellbook_then_binds(client):
    _add_book("Prayer book", "prayer_book")
    first = _post(client, "I examine the book.", "ambig")
    assert _auth(first).get("reference_disposition") == "AMBIGUOUS"
    second = _post(client, "I examine the spellbook.", "choose-spellbook")
    _quiet(second)
    assert second["turn_delta"] == 0
    assert "Spellbook" in second["visible"]
    assert "Prayer book" not in second["visible"]
    assert _auth(second).get("subject_id") == "spellbook"
    assert _auth(second).get("reference_disposition") == "RESOLVED"


def test_unmatched_object_does_not_advance_or_substitute(client):
    result = _post(client, "I examine the silver astrolabe.", "astrolabe")
    _quiet(result)
    assert result["turn_delta"] == 0
    assert result["visible"] == UNMATCHED
    low = result["visible"].casefold()
    assert "spellbook" not in low
    assert "notice board" not in low
    assert "spotter" not in low
    assert "written list" not in low
    assert _auth(result).get("reference_disposition") == "UNMATCHED"
    assert _auth(result).get("subject_id") in (None, "")
    assert result["after"]["character"]["inventory"] == result["before"]["character"]["inventory"]


def test_previously_referenced_book_and_unrelated_dialogue(client):
    first = _post(client, "I examine the book.", "first")
    assert _auth(first).get("subject_id") == "spellbook"
    follow = _post(client, "Examine it.", "pronoun")
    assert "Spellbook" in follow["visible"]
    assert _auth(follow).get("subject_id") == "spellbook"
    _post(client, "Where am I?", "topic")
    pronoun = _post(client, "Examine it.", "stale-pronoun")
    assert "Spellbook" not in pronoun["visible"]
    assert NOTICE not in pronoun["visible"]
    assert pronoun["turn_delta"] == 0
    named = _post(client, "I examine the book.", "named-again")
    assert _auth(named).get("subject_id") == "spellbook"
    assert named["turn_delta"] == 0


def test_reference_survives_reload(client):
    first = _post(client, "I examine the book.", "before-reload")
    assert _auth(first).get("subject_id") == "spellbook"
    _LANES.clear()
    storage.load_session()
    storage.load_character()
    with TestClient(app) as again:
        renamed = _post(again, "I examine the book.", "after-reload")
        pronoun = _post(again, "Examine it.", "after-reload-it")
    assert _auth(renamed).get("subject_id") == "spellbook"
    assert "not established" in renamed["visible"]
    assert _auth(pronoun).get("subject_id") == "spellbook"
    assert renamed["turn_delta"] == 0


def test_retry_does_not_duplicate_effects(client):
    first = client.post("/api/chat?ui_mode=player", json={"text": "I examine the book.", "client_request_id": "retry-book"})
    before = state()
    second = client.post("/api/chat?ui_mode=player", json={"text": "I examine the book.", "client_request_id": "retry-book"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert state() == before
    fresh = _post(client, "I examine the book.", "retry-new-id")
    _quiet(fresh)
    assert fresh["turn_delta"] == 0
    assert fresh["before"]["character"]["inventory"] == fresh["after"]["character"]["inventory"]


def test_equip_resolved_book_does_not_mutate_inventory(client):
    before = copy.deepcopy(storage.load_character())
    result = _post(client, "I equip the spellbook.", "equip")
    assert result["providers"] == 0
    assert storage.load_character()["inventory"] == before["inventory"]
    low = result["visible"].casefold()
    assert "you equip" not in low
    assert "now equipped" not in low
    assert "d20=" not in low


def test_person_negation_and_conditional_still_hold(client):
    person = _post(client, "I ask Warden Cole about the gate.", "warden")
    _quiet(person)
    assert person["turn_delta"] == 0
    low = person["visible"].casefold()
    assert "warden cole" in low
    assert "which person do you mean: guard captain" not in low
    assert "tavern runner" not in low or "no established person" in low
    negated = _post(client, "I do not persuade the guard captain.", "negated")
    conditional = _post(client, "If he is listening, I try to persuade the guard captain.", "conditional")
    assert "nothing has been attempted" in negated["visible"].casefold()
    assert "conditional" in conditional["visible"].casefold()
    assert "d20=" not in negated["visible"] and "d20=" not in conditional["visible"]
    assert negated["turn_delta"] == 0 and conditional["turn_delta"] == 0
    assert negated["after"]["session"].get("npc_runtime", {}) == negated["before"]["session"].get("npc_runtime", {})
