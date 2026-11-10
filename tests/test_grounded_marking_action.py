"""End-to-end grounded marking through the HTTP gameplay harness."""
import copy
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from game import object_observation, storage
from game.api import app
from game.marking_action import recognize_marking, resolve_marking
from tests.pr_play_79df3_harness import seed_gate
from tests.test_pr_play_post_npc_handoff import _env, _say

WARNING = "Warning: keep to the north wall."
NAME = "The name is Mara Voss."
ACTION = "I copy the warning onto my sleeve using the available mud."


def _identity(campaign_id, item_id, name, **extra):
    row = {
        "id": item_id,
        "name": name,
        "quantity": 1,
        "usable": True,
        "instance_id": str(uuid4()),
        "revision": 0,
        "provenance": {
            "version": 1,
            "campaign_run_id": campaign_id,
            "operation_id": "grounded-marking-fixture",
            "source": {"host": "character.inventory", "legacy_id": item_id},
        },
    }
    row.update(extra)
    return row


def _surface(surface_id, name, kind, aliases):
    return {
        "id": surface_id,
        "name": name,
        "aliases": aliases,
        "kind": kind,
        "ordinary_writing": True,
        "accessible": True,
    }


def _medium(medium_id, name, surfaces, aliases):
    return {
        "id": medium_id,
        "name": name,
        "aliases": aliases,
        "compatible_surfaces": surfaces,
        "accessible": True,
        "consumption": "none",
    }


def _equip(ruleset="rules_light"):
    session = storage.load_session()
    character = storage.load_character()
    campaign_id = session["campaign_run_id"]
    coat = _identity(
        campaign_id, "travel_coat", "Travel coat",
        marking_surfaces=[_surface("sleeve", "sleeve", "cloth", ["sleeve", "coat sleeve"])],
    )
    mud = _identity(
        campaign_id, "carried_mud", "Mud",
        marking_medium=_medium("mud", "mud", ["cloth", "paper", "wood"], ["mud", "available mud"]),
    )
    paper = _identity(
        campaign_id, "loose_paper", "Paper",
        marking_surfaces=[_surface("page", "page", "paper", ["paper", "page"])],
    )
    charcoal = _identity(
        campaign_id, "charcoal_stub", "Charcoal",
        marking_medium=_medium("charcoal", "charcoal", ["paper", "wood", "cloth"], ["charcoal"]),
    )
    character["inventory"] = [coat, mud, paper, charcoal]
    character["ruleset_extension"] = {"id": ruleset, "preserved": True, "skill_name": "not-used"}
    character["physical_status"] = {"ordinary_marking": "able"}
    storage.save_character(character)
    knowledge = session.setdefault("clue_knowledge", {})
    knowledge["north_warning"] = {
        "state": "discovered", "text": WARNING, "aliases": ["warning", "the warning"],
        "presentation": "explicit",
    }
    knowledge["known_name"] = {
        "state": "discovered", "text": NAME, "aliases": ["name", "the name"],
        "presentation": "explicit",
    }
    storage.save_session(session)
    return character


def _markings(item_id="travel_coat"):
    character = storage.load_character()
    row = next(item for item in character["inventory"] if item["id"] == item_id)
    return character, row, list(row.get("markings") or [])


def _observe(row, *, concealed=False):
    character = storage.load_character()
    session = storage.load_session()
    request = {
        "version": 1,
        "campaign_run_id": session["campaign_run_id"],
        "character_id": character["id"],
        "instance_id": row["instance_id"],
        "observer_id": "player",
        "scope": "carried",
        "categories": ["markings"],
    }
    grant = object_observation._establish_observation_authorization(
        character, request, decision_ref="grounded-marking-observation",
        visibility_ref="committed-classification", access_ref="carried-object",
        concealed=concealed, restricted_scopes=(("*",) if concealed else ()), complete=concealed,
    )
    return object_observation.observe_object(character, request, authorization=grant)


def _contents(observed):
    if observed.get("status") != "observed":
        return []
    return [value["content"] for value in observed["properties"][0]["values"]]


@pytest.fixture
def client(tmp_path, monkeypatch):
    _env(monkeypatch)
    from tests.helpers.storage_isolation import install

    install(tmp_path)
    seed_gate(tmp_path, monkeypatch)
    http = TestClient(app)
    http.__enter__()
    try:
        yield http
    finally:
        http.__exit__(None, None, None)


def test_concealed_marking_stays_out_of_ordinary_observation(client):
    _equip()
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": "I secretly copy the warning onto my sleeve using the available mud.", "client_request_id": "concealed-copy"},
    )
    assert response.status_code == 200
    visible = response.json()["gm_output"]["player_facing_text"]
    assert "concealed" in visible.casefold()
    assert "on it now" not in visible.casefold()
    _character, row, marks = _markings()
    assert marks[0]["content"] == WARNING
    assert row["marking_visibility"]["markings"][marks[0]["modification_id"]]["classification"] == "concealed"
    assert _contents(_observe(row)) == []
    assert _contents(_observe(row, concealed=True)) == [WARNING]
    assert "request_id" not in json.dumps(_observe(row, concealed=True))


def test_recognition_rejects_non_marking_language():
    for text in (
        "I write down what happened.",
        "I remember the warning.",
        "I copy his fighting stance.",
        "I make a mental note.",
        "I tell him to write the warning.",
        "What is written on the board?",
    ):
        assert recognize_marking(text) is None
    assert recognize_marking("I mark the location on my map.")["target_phrase"] == "my map"
    assert recognize_marking("I scratch the words into the metal.")["destructive"] is True


def test_http_success_persists_reloads_and_replays(client):
    before = _equip("pf1e")
    assert _observe(before["inventory"][0])["status"] in {"observed", "unresolved"}
    assert _contents(_observe(before["inventory"][0])) == []
    snapshot_before = storage.create_snapshot("S0 before marking")
    result = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "grounded-copy-1"},
    )
    assert result.status_code == 200, result.text
    visible = result.json()["gm_output"]["player_facing_text"]
    assert "The marking is on it now." in visible
    assert WARNING in visible
    assert "request_id" not in visible and "prepare_marking" not in visible
    character, row, marks = _markings()
    assert len(marks) == 1 and marks[0]["content"] == WARNING
    assert row["revision"] == 2
    assert row["marking_visibility"]["markings"][marks[0]["modification_id"]] == {"classification": "visible"}
    assert character["ruleset_extension"] == {"id": "pf1e", "preserved": True, "skill_name": "not-used"}
    assert _contents(_observe(row)) == [WARNING]
    raw = storage.CHARACTER_PATH.read_bytes()
    assert json.loads(raw)["inventory"][0]["markings"][0]["content"] == WARNING
    observed = _contents(_observe(storage.load_character()["inventory"][0]))
    assert observed == [WARNING]
    again = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "grounded-copy-1"},
    )
    assert again.status_code == 200
    assert len(_markings()[2]) == 1
    from game.integrated_play import _LANES

    _LANES.clear()
    replay = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "grounded-copy-1"},
    )
    assert replay.status_code == 200
    assert WARNING in replay.json()["gm_output"]["player_facing_text"]
    assert len(_markings()[2]) == 1
    _LANES.clear()
    changed = client.post(
        "/api/chat?ui_mode=player",
        json={"text": 'I copy "OTHER WORDS" onto my sleeve using the available mud.', "client_request_id": "grounded-copy-1"},
    )
    assert changed.status_code == 200
    assert "Nothing further was written." in changed.json()["gm_output"]["player_facing_text"]
    assert len(_markings()[2]) == 1 and _markings()[2][0]["content"] == WARNING
    second = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "grounded-copy-2"},
    )
    assert second.status_code == 200
    assert len(_markings()[2]) == 2
    assert _contents(_observe(_markings()[0]["inventory"][0])) == [WARNING, WARNING]
    snapshot_after = storage.create_snapshot("S1 after marking")
    assert storage.load_snapshot(snapshot_before["id"])
    assert _markings()[2] == []
    assert storage.load_snapshot(snapshot_after["id"])
    assert [mark["content"] for mark in _markings()[2]] == [WARNING, WARNING]
    assert _contents(_observe(_markings()[0]["inventory"][0])) == [WARNING, WARNING]


@pytest.mark.parametrize("ruleset", ["pf1e", "rules_light", "science_fiction"])
def test_ruleset_extension_is_not_consulted(client, ruleset):
    _equip(ruleset)
    visible = _say(client, "Use the charcoal to write the name on the paper.")["visible"]
    assert NAME in visible
    character, row, marks = _markings("loose_paper")
    assert marks[0]["content"] == NAME
    assert character["ruleset_extension"]["id"] == ruleset
    assert "linguistics" not in visible.casefold() and "difficulty class" not in visible.casefold()
    assert row["revision"] == 2


def test_paraphrases_and_unsupported_scratch(client):
    _equip()
    sleeve = _say(client, "Copy the warning onto my sleeve with the mud.")
    assert WARNING in sleeve["visible"]
    cloth = _say(client, "I jot the message onto the cloth.")
    assert "nothing was written" in cloth["visible"].lower()
    assert "no usable writing medium" in cloth["visible"].lower()
    before = storage.load_character()
    metal = _identity(
        storage.load_session()["campaign_run_id"], "metal_plate", "Metal plate",
        marking_surfaces=[_surface("face", "face", "metal", ["metal", "plate"])],
    )
    before["inventory"].append(metal)
    storage.save_character(before)
    scratched = _say(client, "I scratch the words into the metal.")
    assert "scratching or engraving" in scratched["visible"].lower()
    assert storage.load_character()["inventory"][-1].get("markings") in (None, [])


def test_original_gaps_do_not_invent_resources(client):
    character = storage.load_character()
    session = storage.load_session()
    session.setdefault("clue_knowledge", {})["north_warning"] = {
        "state": "discovered", "text": WARNING, "aliases": ["warning"], "presentation": "explicit",
    }
    storage.save_session(session)
    scene = storage.load_scene("frontier_gate")
    assert any("mud" in str(fact).casefold() for fact in (scene.get("scene") or {}).get("visible_facts") or [])
    before = copy.deepcopy(storage.load_character())
    visible = _say(client, ACTION)["visible"].lower()
    assert "nothing was written" in visible
    assert "no established object" in visible
    assert storage.load_character() == before
    character["inventory"] = [{"id": "mud", "name": "Mud", "quantity": 1, "usable": True}]
    storage.save_character(character)
    named = _say(client, ACTION)["visible"].lower()
    assert "nothing was written" in named
    assert storage.load_character()["inventory"] == character["inventory"]


def test_hidden_text_and_ambiguous_targets_do_not_write(client):
    _equip()
    before = copy.deepcopy(storage.load_character())
    hidden = _say(client, "I copy the noble agent hidden signal onto my sleeve with mud.")
    assert "coordinated signal" not in hidden["visible"].lower()
    assert "nothing was written" in hidden["visible"].lower()
    assert storage.load_character()["inventory"][0].get("markings", []) == []
    character = storage.load_character()
    twin = copy.deepcopy(character["inventory"][0])
    twin["id"] = "second_coat"
    twin["instance_id"] = str(uuid4())
    twin["provenance"] = dict(twin["provenance"], source={"host": "character.inventory", "legacy_id": "second_coat"})
    character["inventory"].insert(0, twin)
    storage.save_character(character)
    ambiguous = _say(client, ACTION)["visible"].lower()
    assert "more than one established object" in ambiguous
    assert all(not item.get("markings") for item in storage.load_character()["inventory"])
    assert before["inventory"][0]["instance_id"] != twin["instance_id"]


def test_incompatible_mechanics_capability_and_consumption(client):
    _equip()
    character = storage.load_character()
    character["inventory"][1]["marking_medium"]["compatible_surfaces"] = ["wood"]
    storage.save_character(character)
    incompatible = _say(client, ACTION)["visible"].lower()
    assert "not established as usable" in incompatible
    assert _markings()[2] == []
    character = storage.load_character()
    character["inventory"][1]["marking_medium"]["compatible_surfaces"] = ["cloth"]
    character["inventory"][0]["marking_surfaces"][0]["mechanics"] = "required"
    storage.save_character(character)
    mechanics = _say(client, ACTION)["visible"].lower()
    assert "rules decision" in mechanics and "linguistics" not in mechanics
    assert _markings()[2] == []
    character = storage.load_character()
    character["inventory"][0]["marking_surfaces"][0].pop("mechanics")
    character["physical_status"] = {"ordinary_marking": "unable"}
    storage.save_character(character)
    unable = _say(client, ACTION)["visible"].lower()
    assert "not established as able" in unable
    character = storage.load_character()
    character["physical_status"] = {"ordinary_marking": "able"}
    character["inventory"][1]["marking_medium"]["consumption"] = "required"
    storage.save_character(character)
    consumed = _say(client, ACTION)["visible"].lower()
    assert "cannot be recorded safely" in consumed
    assert _markings()[2] == []
    assert storage.load_character()["inventory"][1]["quantity"] == 1


def test_failure_injection_does_not_publish_success(client, monkeypatch):
    import game.immutable_valid_response as immutable
    import game.marking_action as marking

    _equip()
    before = copy.deepcopy(storage.load_character())
    original_visibility = marking.prepare_visibility
    original_marking = marking.prepare_marking
    original_save = __import__("game.api", fromlist=["save_character"]).save_character
    original_seal = immutable.seal_host_speech

    def reject_visibility(*_args, **_kwargs):
        return {"status": "rejected", "error": "unauthorized_visibility"}

    monkeypatch.setattr(marking, "prepare_visibility", reject_visibility)
    visible = _say(client, ACTION)["visible"].lower()
    assert "could not be confirmed" in visible
    assert storage.load_character() == before
    monkeypatch.setattr(marking, "prepare_visibility", original_visibility)

    def reject_marking(*_args, **_kwargs):
        return {"status": "rejected", "error": "unauthorized_content"}

    monkeypatch.setattr(marking, "prepare_marking", reject_marking)
    assert "could not be confirmed" in _say(client, ACTION)["visible"].lower()
    assert storage.load_character() == before
    monkeypatch.setattr(marking, "prepare_marking", original_marking)

    def boom(*_args, **_kwargs):
        raise RuntimeError("marking save interrupted")

    monkeypatch.setattr("game.api.save_character", boom)
    interrupted = client.post("/api/chat?ui_mode=player", json={"text": ACTION, "client_request_id": "interrupted"})
    assert interrupted.status_code == 500
    assert "marking is on it now" not in interrupted.json().get("gm_output", {}).get("player_facing_text", "").lower()
    assert storage.load_character() == before
    monkeypatch.setattr("game.api.save_character", original_save)

    def seal_boom(*_args, **_kwargs):
        raise RuntimeError("publication failed")

    monkeypatch.setattr(immutable, "seal_host_speech", seal_boom)
    failed_publication = client.post(
        "/api/chat?ui_mode=player", json={"text": ACTION, "client_request_id": "publish-fail"},
    )
    assert failed_publication.status_code == 200
    assert WARNING in failed_publication.json()["gm_output"]["player_facing_text"]
    assert "on it now" in failed_publication.json()["gm_output"]["player_facing_text"].lower()
    assert len(_markings()[2]) == 1
    from game.integrated_play import _LANES

    _LANES.clear()
    monkeypatch.setattr(immutable, "seal_host_speech", original_seal)
    recovered = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "publish-fail"},
    )
    assert recovered.status_code == 200
    assert WARNING in recovered.json()["gm_output"]["player_facing_text"]
    assert len(_markings()[2]) == 1


def test_stale_revision_and_direct_resolution_do_not_guess(client):
    from game.marking_action import stage_grounded_marking

    _equip()
    character = storage.load_character()
    session = storage.load_session()
    proposal = recognize_marking(ACTION)
    ready = resolve_marking(proposal, character, session)
    assert ready["outcome"] == "ready"
    ready["expected_revision"] = 9
    staged = stage_grounded_marking(character, ready, "stale-operation")
    assert staged["error"] == "stale_revision"
    assert storage.load_character() == character
    character = {
        "id": "actor",
        "inventory": [],
        "physical_status": {"ordinary_marking": "able"},
    }
    session = {"campaign_run_id": "campaign-1", "clue_knowledge": {}}
    proposal = recognize_marking(ACTION)
    resolution = resolve_marking(proposal, character, session)
    assert resolution["outcome"] == "unresolved"
    assert "target" in resolution["missing"] and "medium" in resolution["missing"]
    assert "Keep to the north wall" not in resolution["player_text"]
