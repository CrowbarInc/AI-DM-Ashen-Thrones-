"""PR-BR C21 continuation 2: personhood is the semantic head, not nominal shape.

Deterministic. The stubbed /api/chat path does not call a paid model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus, read_discourse_focus
from game.immutable_valid_response import semantic_equal
from game.incidental_entity import (
    nominal_semantic_head,
    referential_nominal,
    referential_person_nominal,
    resolve_proposed_interlocutor,
)
from game.resolution_contract import construct_resolution_contract
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads((ROOT / "data" / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
RUNNER = {"id": "tavern_runner", "type": "interlocutor", "label": "Tavern Runner", "aliases": ["runner", "tavern runner"], "source": "scene"}
NOTICE = {"id": "notice_board", "type": "object", "label": "Notice board", "aliases": ["notice", "board", "the board"], "source": "scene"}
CATALOG = [RUNNER, NOTICE]
POPULATED = {
    "scene": {
        "id": "frontier_gate",
        "summary": "A crowded gate market. Travelers, wagons, and vendors fill the approach.",
        "visible_facts": ["People press through the queue beside the tavern."],
    }
}

HISTORICAL_SPANS = (
    "exact coin modest fee so i",
    "the exact coin of that modest fee so I",
    "first local i pass",
    "the first local I pass",
    "i lean in",
    "I lean in",
    "for crate yards",
    "for the crate yards",
    "they lingered on",
    "underbrush for whatever is moving out there",
    "the underbrush for whatever is moving out there",
    "still patch brush at steady pace",
    "the still patch of brush at a steady pace",
    "the inn to see",
    "inn to see",
)

HISTORICAL_TURNS = (
    "I set my pack open for the guard and ask the exact coin of that modest fee so I can pay it while they look.",
    "I stay on the main road and ask the first local I pass where a traveler can get a bed and a meal before curfew.",
    'I lean in, matching the captain\'s low voice. "Whose orders are these?"',
    "I step back from the board and scan the gate approach for the crate yards, looking northwest for the mud track.",
    "I let the silence stand and look into the knot of guards and refugees their eyes just left, picking out which face they lingered on and who went still when I spoke.",
    "I walk the few dozen paces to the old crates and check the muddy ruts for fresh boot prints or drag marks, then listen toward the underbrush for whatever is moving out there.",
    "I walk toward the still patch of brush at a steady pace, hands empty and in sight, until I can tell whether a person is waiting there.",
    (
        'I nod at the tavern runner and say, "Thank you for the guidance. I will make my way to the inn near the market square '
        'for rest and warmth first." Then I proceed toward the town gates, aiming to enter Cinderwatch and find the inn to see '
        "if I can barter or earn a meal and shelter."
    ),
)


def _focus(**slots):
    focus = {
        "scene_id": "frontier_gate",
        "active_interlocutor": {"id": "tavern_runner", "label": "Tavern Runner", "kind": "interlocutor"},
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {
        "active_scene_id": "frontier_gate",
        "turn_counter": 4,
        DISCOURSE_FOCUS_KEY: focus,
        "bounded_improvisation": {"entries": [], "incidental_entities": []},
    }


def _contract(text, session=None, catalog=None, scene=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=CATALOG if catalog is None else catalog,
        scene=scene or POPULATED,
    )


def _binding(contract):
    return contract.construction["entity_binding"]


def _entities(session):
    ledger = session.get("bounded_improvisation") or {}
    return [row for row in ledger.get("incidental_entities") or [] if isinstance(row, dict)]


def test_semantic_head_not_the_last_token_decides_personhood():
    assert nominal_semantic_head("the inn to see") == "inn"
    assert nominal_semantic_head("the merchant to ask") == "merchant"
    assert nominal_semantic_head("the tired porter carrying crates") == "porter"
    assert nominal_semantic_head("the porter by the gate") == "porter"
    assert referential_nominal("the inn to see") == "inn"
    assert referential_person_nominal("the inn to see") is None
    assert referential_person_nominal("the merchant to ask") == "merchant"


def test_simple_and_modified_people_remain_people():
    people = {
        "a porter": "porter",
        "the porter": "porter",
        "a merchant": "merchant",
        "the innkeeper": "innkeeper",
        "a traveler": "traveler",
        "the guard": "guard",
        "a nearby porter": "nearby porter",
        "the tired porter": "tired porter",
        "the tired porter carrying crates": "tired porter",
        "the porter by the gate": "porter",
        "the woman sweeping the steps": "woman",
        "the traveler wearing a red cloak": "traveler",
        "the innkeeper behind the counter": "innkeeper",
        "the guard near the wagon": "guard",
        "the traveler waiting by the wall": "traveler",
        "the merchant near the fountain": "merchant",
        "the traveler from the north road": "traveler",
        "a cooper": "cooper",
        "the sentry beside the wagon": "sentry",
    }
    for span, label in people.items():
        assert referential_person_nominal(span) == label, span
        assert nominal_semantic_head(span)


def test_person_infinitive_stays_a_person_and_nonperson_infinitive_does_not():
    assert referential_person_nominal("the merchant to ask") == "merchant"
    assert referential_person_nominal("the guard to speak with") == "guard"
    assert referential_person_nominal("the porter to question") == "porter"
    blocked = (
        "the inn to see",
        "the gate to inspect",
        "the market to find",
        "the board to read",
        "the road to follow",
        "the crate to examine",
        "the room to search",
        "the tavern to visit",
        "the shop to enter",
    )
    for span in blocked:
        assert referential_person_nominal(span) is None, span
        assert referential_nominal(span)
        assert nominal_semantic_head(span) not in {"see", "inspect", "find", "read", "follow", "examine", "search", "visit", "enter"}


def test_simple_nonpeople_are_nominals_but_not_persons():
    for span in (
        "the inn",
        "the gate",
        "the market",
        "the board",
        "the road",
        "the crate",
        "the room",
        "the rumor",
        "the price",
    ):
        assert referential_nominal(span), span
        assert referential_person_nominal(span) is None, span


def test_clause_fragments_and_pronouns_are_not_people():
    for span in (
        "i lean in",
        "they lingered on",
        "for crate yards",
        "underbrush for whatever is moving out there",
        "him",
        "exact coin modest fee so i",
        "first local i pass",
        "still patch brush at steady pace",
    ):
        assert referential_person_nominal(span) is None, span


def test_historical_malformed_spans_are_not_person_candidates():
    for span in HISTORICAL_SPANS:
        assert referential_person_nominal(span) is None, span


def test_model_person_label_does_not_bypass_the_head_check():
    decision = resolve_proposed_interlocutor(
        "the inn to see",
        "the inn to see",
        scene=POPULATED,
        session=_focus(active_interlocutor=None),
        scene_id="frontier_gate",
        catalog=CATALOG,
    )
    assert decision["status"] != "bound_incidental"
    assert decision["entity_id"] is None
    assert "not_a_person" in " ".join(decision["authority_reasons"])


def test_long_question_binds_the_porter_and_keeps_the_question():
    text = (
        "I ask the tired porter carrying crates whether anyone came through "
        "the north road this morning."
    )
    session = _focus()
    contract = _contract(text, session)
    binding = _binding(contract)
    assert contract.operation == "ask"
    assert binding["status"] == "bound_incidental"
    assert binding["label"] == "tired porter"
    assert "north road" in contract.raw_input
    assert "whether anyone came through" not in str(binding["label"])
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert _entities(session)[0]["label"] == "tired porter"


def test_place_plus_infinitive_does_not_instantiate_a_person_or_restore_the_runner():
    text = "I head to the inn to see whether anyone there knows about the patrol."
    session = _focus()
    contract = _contract(text, session)
    binding = _binding(contract)
    assert binding["status"] != "bound_incidental"
    assert binding.get("label") != "inn to see"
    assert "inn to see" not in str(binding.get("proposed_span") or "")
    assert contract.interlocutor_id != "tavern_runner"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert _entities(session) == []


def test_live_turn_five_sentence_does_not_persist_the_inn_to_see():
    text = HISTORICAL_TURNS[-1]
    session = _focus()
    contract = _contract(text, session)
    binding = _binding(contract)
    assert referential_person_nominal("the inn to see") is None
    assert binding["status"] != "bound_incidental"
    assert "inn to see" not in str(binding.get("label") or "")
    assert contract.interlocutor_id != "tavern_runner"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    labels = [row["label"] for row in _entities(session)]
    assert labels == []
    assert read_discourse_focus(session)["active_interlocutor"] is None


def test_inn_and_innkeeper_stay_separate():
    text = "I head to the inn and ask the innkeeper about the patrol."
    session = _focus()
    contract = _contract(text, session)
    binding = _binding(contract)
    assert contract.operation == "ask"
    assert binding["status"] == "bound_incidental"
    assert binding["label"] == "innkeeper"
    assert "inn and" not in str(binding["label"])
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert [row["label"] for row in _entities(session)] == ["innkeeper"]


def test_board_remains_an_object_target():
    session = _focus(active_interlocutor=None)
    contract = _contract("I read the notice board.", session)
    assert contract.operation in {"inspect", "perceive"}
    binding = _binding(contract)
    assert binding["status"] != "bound_incidental"
    assert _entities(session) == []


def test_pronoun_does_not_create_a_person_and_does_inherit():
    session = _focus(active_interlocutor=None)
    first = _contract("I ask a nearby porter whether the wagons are through.", session)
    assert _binding(first)["status"] == "bound_incidental"
    commit_discourse_focus(session, contract=first.as_dict(), scene_id="frontier_gate")
    pronoun = _contract("I ask him whether the line has moved.", session)
    assert pronoun.interlocutor_id == first.interlocutor_id
    assert _binding(pronoun).get("label") != "him"
    assert referential_person_nominal("him") is None
    commit_discourse_focus(session, contract=pronoun.as_dict(), scene_id="frontier_gate")
    assert len(_entities(session)) == 1


def test_malformed_candidate_does_not_restore_the_previous_interlocutor():
    session = _focus()
    contract = _contract("I look toward the underbrush for whatever is moving out there.", session)
    binding = _binding(contract)
    assert binding["status"] != "bound_incidental"
    assert contract.interlocutor_id != "tavern_runner"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert _entities(session) == []
    assert read_discourse_focus(session)["active_interlocutor"] is None


def test_new_incidental_replaces_the_previous_interlocutor():
    session = _focus()
    contract = _contract("I ask the tired porter carrying crates about the road.", session)
    assert contract.interlocutor_id != "tavern_runner"
    assert _binding(contract)["status"] == "bound_incidental"
    assert _binding(contract)["label"] == "tired porter"


def test_historical_player_turns_do_not_persist_malformed_people__pr_br_continuation21b_referential_personhood():
    forbidden = {
        "exact coin modest fee so i",
        "first local i pass",
        "i lean in",
        "for crate yards",
        "they lingered on",
        "underbrush for whatever is moving out there",
        "still patch brush at steady pace",
        "inn to see",
        "the inn to see",
    }
    for text in HISTORICAL_TURNS:
        session = _focus()
        contract = _contract(text, session)
        binding = _binding(contract)
        label = str(binding.get("label") or "").lower()
        assert binding["status"] != "bound_incidental" or label not in forbidden, text
        assert label not in forbidden, (text, binding)
        commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
        stored = {str(row.get("label") or "").lower() for row in _entities(session)}
        assert stored.isdisjoint(forbidden), (text, stored)


def test_consequential_person_still_reaches_rejection():
    session = _focus()
    contract = _contract("I speak to the spy working for the Ash Compact.", session)
    binding = _binding(contract)
    assert binding["status"] == "rejected_consequential"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert _entities(session) == []


def _seed(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["turn_counter"] = 1
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())


@pytest.fixture()
def chat(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unpatched")))
    return TestClient(app)


def _contract_of(payload):
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), dict) else {}
    return contract, binding


def test_raw_chat_stub_rejects_nonpersons_and_keeps_people(chat, monkeypatch):
    def fake_gpt(messages, **kwargs):
        blob = " ".join(
            str(message.get("content") or "")
            for message in messages
            if isinstance(message, dict) and message.get("role") == "user"
        ).lower()
        if "tired porter" in blob:
            return _gm_response('The tired porter says, "A few wagons came down the north road."')
        if "innkeeper" in blob:
            return _gm_response('The innkeeper says, "There is stew, if you can pay."')
        if "nearby porter" in blob or "ask a porter" in blob:
            return _gm_response('The porter says, "The wagons are through."')
        if "underbrush" in blob or "inn to see" in blob or "head to the inn" in blob:
            return _gm_response("The road runs on toward the market. No one stops you.")
        if "notice board" in blob or "the gate" in blob:
            return _gm_response("The board is posted. The gate stands open.")
        return _gm_response("The square holds its line.")

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)

    inn = chat.post(
        "/api/chat",
        json={"text": "I head to the inn to see what is happening."},
    ).json()
    _inn_contract, inn_binding = _contract_of(inn)
    assert inn_binding.get("status") != "bound_incidental"
    assert "inn to see" not in str(inn_binding.get("label") or "")
    assert semantic_equal(
        inn["gm_output"]["player_facing_text"],
        inn["gm_output"]["metadata"]["accepted_response"]["text"],
    )

    keeper = chat.post("/api/chat", json={"text": "I ask the innkeeper for a meal."}).json()
    _keeper_contract, keeper_binding = _contract_of(keeper)
    assert keeper_binding.get("status") == "bound_incidental"
    assert keeper_binding.get("label") == "innkeeper"

    porter = chat.post(
        "/api/chat",
        json={"text": "I ask the tired porter carrying crates whether the wagons are through."},
    ).json()
    _porter_contract, porter_binding = _contract_of(porter)
    assert porter_binding.get("status") == "bound_incidental"
    assert "porter" in str(porter_binding.get("label") or "")

    places = chat.post(
        "/api/chat",
        json={"text": "I ask about the gate, the road, and the notice board."},
    ).json()
    _place_contract, place_binding = _contract_of(places)
    assert place_binding.get("status") != "bound_incidental"

    fresh = chat.post("/api/chat", json={"text": "I ask the tavern runner who came through."}).json()
    runner_contract, runner_binding = _contract_of(fresh)
    assert runner_binding.get("status") == "bound_canonical"
    assert runner_contract.get("interlocutor_id") == "tavern_runner"
    switched = chat.post("/api/chat", json={"text": "I ask a porter whether the line has moved."}).json()
    _switched_contract, switched_binding = _contract_of(switched)
    assert switched_binding.get("status") == "bound_incidental"
    assert "porter" in str(switched_binding.get("label") or "")
    assert switched_binding.get("bound_interlocutor_id") != "tavern_runner"

    malformed = chat.post(
        "/api/chat",
        json={"text": "I look toward the underbrush for whatever is moving out there."},
    ).json()
    malformed_contract, malformed_binding = _contract_of(malformed)
    assert malformed_binding.get("status") != "bound_incidental"
    assert malformed_contract.get("interlocutor_id") != switched_binding.get("bound_interlocutor_id")
    session = storage.load_session()
    labels = {
        str(row.get("label") or "")
        for row in (session.get("bounded_improvisation") or {}).get("incidental_entities") or []
    }
    assert "inn to see" not in labels
    assert "underbrush" not in " ".join(labels)
    assert any("porter" in label for label in labels)
    assert any(label == "innkeeper" for label in labels)
