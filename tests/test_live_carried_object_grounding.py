"""Carried-object grounding on the ordinary path and on captured live records.

Captured model JSON is loaded unchanged from the configuration-recovery probe.
These tests do not call a provider.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.carried_object_grounding import interpretation_catalog
from game.integrated_play import _LANES
from game.player_interpretation_bridge import visible_catalog
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate
from tests.test_ordinary_semantic_admission import state

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "artifacts" / "pr_play_live_probe_configuration_recovery"
NOTICE = "The missing patrol was last seen taking the northwest mud track past the crates."
UNMATCHED = "Nothing here matches that reference. Which established object do you mean?"
SPELLS = ("Daze", "Detect Magic", "Magic Missile", "Shield")


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
    assert response.status_code == 200, response.text
    body = response.json()
    logged = storage.load_log()
    latest = logged[-1] if logged else {}
    decision = ((latest.get("resolution") or {}).get("metadata") or {}).get("conversational_decision") or {}
    return {
        "visible": body["gm_output"]["player_facing_text"],
        "before": before,
        "after": after,
        "providers": len(snapshot()["records"]) - providers,
        "decision": decision,
        "turn_delta": after["session"].get("turn_counter") - before["session"].get("turn_counter"),
    }


def _auth(result):
    return result["decision"].get("authorization") or {}


def _quiet(result):
    assert result["providers"] == 0
    assert result["turn_delta"] == 0
    assert result["before"]["character"] == result["after"]["character"]
    assert result["before"]["world"] == result["after"]["world"]
    assert result["before"]["scene"] == result["after"]["scene"]
    assert result["before"]["combat"] == result["after"]["combat"]
    assert result["before"]["session"].get("clocks") == result["after"]["session"].get("clocks")
    assert result["before"]["session"].get("active_scene_id") == result["after"]["session"].get("active_scene_id")


def _add_book(name, item_id, **extra):
    character = storage.load_character()
    character["inventory"].append({"id": item_id, "name": name, "quantity": 1, "usable": False, **extra})
    storage.save_character(character)


def _add_scene_book():
    scene = storage.load_active_scene()
    scene["scene"]["interactables"].append({
        "id": "gate_ledger",
        "label": "gate ledger",
        "name": "Gate ledger",
        "aliases": ["book", "ledger"],
        "type": "investigate",
    })
    storage.save_scene(scene)


def _captured(case_id):
    payload = json.loads((PROBE / f"{case_id}_trace.json").read_text(encoding="utf-8"))
    utterance = payload["utterance"]
    raw = None
    for entry in payload["log"]:
        if entry.get("player_input") != utterance:
            continue
        live = ((entry.get("resolution") or {}).get("metadata") or {}).get("live_chat_interpretation") or {}
        if live.get("raw_interpretation"):
            raw = live["raw_interpretation"]
    assert isinstance(raw, str) and raw.startswith("{")
    record = json.loads(raw)
    assert "spellbook" not in record.get("references", {}).get("permitted_entity_ids", [])
    return record


def _replay(monkeypatch, record):
    monkeypatch.setattr(
        "game.api._stored_interpretation_for_player_text",
        lambda *_args, **_kwargs: json.loads(json.dumps(record)),
    )


def test_catalog_includes_spellbook_and_keeps_scene_entities(client):
    del client
    character = storage.load_character()
    scene = storage.load_active_scene()
    world = storage.load_world()
    before = visible_catalog(scene, world)
    catalog = interpretation_catalog(scene, world, character)
    assert "spellbook" not in before
    assert "spellbook" in catalog
    assert catalog["spellbook"]["kind"] == "carried_object"
    assert catalog["spellbook"]["row"]["scope"] == "carried"
    for entity_id, info in before.items():
        assert catalog[entity_id] == info
    blob = json.dumps(catalog)
    assert "Daze" not in blob
    assert "Default template" not in blob
    assert list(catalog) == sorted(catalog)


def test_catalog_skips_hidden_stored_and_duplicate_ids(client):
    del client
    character = storage.load_character()
    character["inventory"].append({"id": "spellbook", "name": "Spellbook", "quantity": 1, "usable": False})
    character["inventory"].append({
        "id": "sealed_tome", "name": "Sealed tome", "quantity": 1, "usable": False, "hidden": True,
    })
    character["inventory"].append({
        "id": "wagon_ledger", "name": "Wagon ledger", "quantity": 1, "usable": False, "stored": True,
    })
    character["inventory"][0]["equipped"] = True
    character["notes"] = "GM_ONLY_CANARY"
    scene = storage.load_active_scene()
    scene["scene"]["interactables"].append({"id": "rope", "label": "rope", "name": "Rope"})
    catalog = interpretation_catalog(scene, storage.load_world(), character)
    assert catalog["spellbook"]["kind"] == "equipped_object"
    assert "sealed_tome" not in catalog
    assert "wagon_ledger" not in catalog
    assert sum(1 for key in catalog if key == "spellbook") == 1
    assert "GM_ONLY_CANARY" not in json.dumps(catalog)
    character["inventory"].append({"id": "notice_board", "name": "Packed board", "quantity": 1, "usable": False})
    collided = interpretation_catalog(scene, storage.load_world(), character)
    assert collided["notice_board"]["kind"] != "carried_object"


def test_case_unique_explicit_and_indirect_volume(client):
    explicit = _post(client, "I read the spellbook.", "explicit")
    indirect = _post(client, "I leaf through the volume I've been carrying.", "volume")
    for result in (explicit, indirect):
        _quiet(result)
        assert "Spellbook" in result["visible"]
        assert "not established" in result["visible"]
        assert _auth(result).get("subject_id") == "spellbook"
        assert _auth(result).get("binding_layer") == "host_reference_resolution"
        assert NOTICE not in result["visible"]
        for name in SPELLS:
            assert name not in result["visible"]


def test_case_follow_up_and_recorded_contents_are_not_invented(client):
    first = _post(client, "I leaf through the volume I've been carrying.", "leaf")
    assert _auth(first).get("subject_id") == "spellbook"
    second = _post(client, "What spells are written in that same book?", "written")
    _quiet(second)
    assert "does not record the spells written" in second["visible"]
    assert _auth(second).get("subject_id") == "spellbook"
    assert _auth(second).get("information_type") == "recorded_spells"
    for name in SPELLS:
        assert name not in second["visible"]
    assert second["after"]["character"]["spells"] == first["before"]["character"]["spells"]


def test_case_prepared_spells_are_the_sheet_list(client):
    result = _post(client, "Remind me what spells I have prepared.", "prepared")
    _quiet(result)
    for name in SPELLS:
        assert name in result["visible"]
    assert "prepared" in result["visible"].casefold()
    assert "not a record of spells written" in result["visible"]
    assert "Nothing has been cast" in result["visible"]
    assert result["after"]["character"]["spells"]["slots"] == {"0": 3, "1": 1}
    assert all(row["cast"] is False for row in result["after"]["character"]["spells"]["prepared"])


def test_case_ready_spells_from_the_carried_book_stay_prepared(client):
    result = _post(client, "From that same book, what spells do I actually have ready?", "ready")
    _quiet(result)
    for name in SPELLS:
        assert name in result["visible"]
    assert _auth(result).get("subject_id") == "spellbook"
    assert _auth(result).get("information_type") == "prepared_spells"
    assert "not a record of spells written" in result["visible"]


def test_case_follow_up_keeps_the_book_already_named(client):
    _add_book("Prayer book", "prayer_book")
    first = _post(client, "I read the spellbook.", "named")
    assert _auth(first).get("subject_id") == "spellbook"
    second = _post(client, "What can I find in that same book?", "same")
    _quiet(second)
    assert _auth(second).get("subject_id") == "spellbook"
    assert "Prayer book" not in second["visible"]
    assert "not established" in second["visible"]


def test_case_two_books_and_unknown_object(client):
    _add_book("Prayer book", "prayer_book")
    ambiguous = _post(client, "I leaf through the volume in my pack.", "two")
    _quiet(ambiguous)
    low = ambiguous["visible"].casefold()
    assert "which object" in low
    assert "spellbook" in low
    assert "prayer book" in low
    assert _auth(ambiguous).get("subject_id") in (None, "")
    assert "Your inventory records" not in ambiguous["visible"]
    unknown = _post(client, "I leaf through the silver astrolabe.", "unknown")
    _quiet(unknown)
    assert unknown["visible"] == UNMATCHED
    assert "spellbook" not in unknown["visible"].casefold()


def test_case_scene_object_stays_distinct_from_the_carried_book(client):
    _add_scene_book()
    carried = _post(client, "I leaf through the volume I've been carrying.", "carried")
    _quiet(carried)
    assert _auth(carried).get("subject_id") == "spellbook"
    assert "gate ledger" not in carried["visible"].casefold()
    mixed = _post(client, "I leaf through the book.", "mixed")
    _quiet(mixed)
    low = mixed["visible"].casefold()
    assert "which object" in low
    assert "spellbook" in low
    assert "gate ledger" in low
    board = _post(client, "I examine the notice board.", "board")
    assert board["providers"] == 0
    assert NOTICE in board["visible"]
    assert board["turn_delta"] == 1
    assert "Spellbook" not in board["visible"]


def test_case_unsupported_negated_and_conditional_do_not_mutate(client):
    burned = _post(client, "I burn the spellbook.", "burn")
    _quiet(burned)
    assert "cannot carry out that use" in burned["visible"]
    assert burned["decision"]["category"] == "DECLINE"
    assert _auth(burned).get("subject_id") == "spellbook"
    negated = _post(client, "I do not leaf through the spellbook.", "negated")
    _quiet(negated)
    assert "Nothing has been attempted" in negated["visible"]
    assert "Your inventory records" not in negated["visible"]
    conditional = _post(client, "If the rain stops, I leaf through the spellbook.", "conditional")
    _quiet(conditional)
    assert "only conditional" in conditional["visible"]
    assert "Your inventory records" not in conditional["visible"]


def test_case_information_then_executable_scene_action(client):
    asked = _post(client, "What spells do I actually have ready?", "ask")
    _quiet(asked)
    for name in SPELLS:
        assert name in asked["visible"]
    board = _post(client, "I examine the notice board.", "then-board")
    assert NOTICE in board["visible"]
    assert board["turn_delta"] == 1
    assert board["before"]["character"]["spells"] == board["after"]["character"]["spells"]
    assert board["before"]["character"]["inventory"] == board["after"]["character"]["inventory"]


def test_replay_null_target_binds_unique_spellbook(client, monkeypatch):
    record = _captured("A1")
    assert record["action_components"][0]["target_ref"] is None
    _replay(monkeypatch, record)
    result = _post(client, "I leaf through the volume I've been carrying.", "replay-a1")
    _quiet(result)
    assert "Spellbook" in result["visible"]
    assert "condition is not established" not in result["visible"]
    assert _auth(result).get("subject_id") == "spellbook"
    assert _auth(result).get("binding_layer") == "host_reference_resolution"


def test_replay_clarification_does_not_invent_a_second_spellbook(client, monkeypatch):
    record = _captured("A2")
    assert record["interpretation_status"] == "CLARIFICATION_REQUIRED"
    assert "Which spellbook" in record["clarification_question"]
    _replay(monkeypatch, record)
    result = _post(client, "The one I mean is the spellbook in my pack.", "replay-a2")
    _quiet(result)
    assert "Spellbook" in result["visible"]
    assert "Which spellbook" not in result["visible"]
    assert _auth(result).get("subject_id") == "spellbook"
    assert _auth(result).get("binding_layer") == "host_reference_resolution"


def test_replay_spell_question_publishes_prepared_names(client, monkeypatch):
    record = _captured("A3")
    assert record["interpretation_status"] == "CLARIFICATION_REQUIRED"
    _replay(monkeypatch, record)
    result = _post(client, "From that same book, what spells do I actually have ready?", "replay-a3")
    _quiet(result)
    for name in SPELLS:
        assert name in result["visible"]
    assert _auth(result).get("information_type") == "prepared_spells"
    assert result["after"]["character"]["spells"]["prepared"][2]["cast"] is False


def test_replay_null_target_stays_ambiguous_for_two_books(client, monkeypatch):
    _add_book("Prayer book", "prayer_book")
    record = _captured("A1")
    _replay(monkeypatch, record)
    result = _post(client, "I leaf through the volume I've been carrying.", "replay-ambiguous")
    _quiet(result)
    low = result["visible"].casefold()
    assert "which object" in low
    assert "spellbook" in low
    assert "prayer book" in low
    assert _auth(result).get("subject_id") in (None, "")
    assert _auth(result).get("binding_layer") == "host_reference_resolution"


def test_replay_fabricated_id_is_rejected_without_substitution(client, monkeypatch):
    record = _captured("A1")
    record["action_components"][0]["target_ref"] = "spellbook_of_shadows"
    _replay(monkeypatch, record)
    result = _post(client, "I leaf through the volume I've been carrying.", "fabricated")
    _quiet(result)
    assert result["decision"]["reason"] == "fabricated_object_id"
    assert _auth(result).get("binding_layer") == "model_rejected"
    assert _auth(result).get("rejected_id") == "spellbook_of_shadows"
    assert "Spellbook" not in result["visible"]
    assert "not among the established objects" in result["visible"]


def test_replay_matching_model_id_is_the_model_binding(client, monkeypatch):
    record = _captured("A1")
    record["action_components"][0]["target_ref"] = "spellbook"
    record["references"]["permitted_entity_ids"].append("spellbook")
    _replay(monkeypatch, record)
    result = _post(client, "I leaf through the volume I've been carrying.", "model-id")
    _quiet(result)
    assert _auth(result).get("subject_id") == "spellbook"
    assert _auth(result).get("binding_layer") == "model_interpretation"


def test_replay_conflicting_scene_id_is_not_executed(client, monkeypatch):
    record = _captured("A1")
    record["action_components"][0]["target_ref"] = "notice_board"
    _replay(monkeypatch, record)
    result = _post(client, "I leaf through the volume I've been carrying.", "conflict")
    _quiet(result)
    assert result["decision"]["reason"] == "model_target_conflict"
    assert NOTICE not in result["visible"]
    assert _auth(result).get("subject_id") in (None, "")
