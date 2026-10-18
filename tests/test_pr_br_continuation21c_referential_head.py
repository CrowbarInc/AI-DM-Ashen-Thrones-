"""PR-BR C21 continuation 3: the referential head is the noun, not the last word.

Deterministic. The stubbed /api/chat path does not call a paid model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus
from game.immutable_valid_response import semantic_equal
from game.incidental_entity import (
    _NONPERSON_HEADS,
    personhood_of_span,
    referential_head,
    referential_nominal,
    referential_person_nominal,
    resolve_proposed_interlocutor,
)
from game.intent_parser import parse_freeform_to_action
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
        "exits": SCENE["scene"]["exits"],
    }
}

TURN3 = (
    "I thank the tavern runner and turn toward the muddy lane northwest of the crates, "
    "carefully stepping through the rain to inspect the footprints they mentioned. "
    "I look for any signs or clues nearby that might hint at what happened to the missing patrol "
    "before deciding whether to follow the road toward the old milestone."
)

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
    "the muddy lane northwest of the crates",
    "muddy lane northwest",
    "the gate",
    "the crowded gate",
    "the quieter fringe of the square",
    "the crowd",
    "here at Cinderwa",
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
    TURN3,
)

VALID_PEOPLE = {
    "a porter": "porter",
    "the porter": "porter",
    "the tired porter": "tired porter",
    "the tired porter carrying crates": "tired porter",
    "the porter by the gate": "porter",
    "the porter who carried the crates": "porter",
    "the merchant to ask": "merchant",
    "the woman sweeping the steps": "woman",
    "the traveler waiting by the wall": "traveler",
    "the traveler from the north road": "traveler",
    "the innkeeper behind the counter": "innkeeper",
    "the gate guard": "gate guard",
    "the stable hand": "stable hand",
    "the cloth merchant": "cloth merchant",
    "the caravan master": "caravan master",
}

NONPEOPLE = (
    "the muddy lane",
    "the muddy lane northwest of the crates",
    "the lane beside the wall",
    "the road to follow",
    "the inn to visit",
    "the tavern by the square",
    "the gate to inspect",
    "the market to find",
    "the notice board to read",
    "the crate beside the wagon",
    "the wagon blocking the road",
    "the room upstairs",
    "the underbrush beside the road",
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


def test_lane_phrase_head_is_lane_not_northwest():
    span = "the muddy lane northwest of the crates"
    assert referential_head(span) == "lane"
    assert "northwest" not in referential_head(span)
    assert referential_nominal(span) == "muddy lane"
    assert referential_person_nominal(span) is None
    assert personhood_of_span(span) == "unknown"
    assert "northwest" not in _NONPERSON_HEADS
    assert "lane" not in _NONPERSON_HEADS


def test_adjective_noun_heads():
    assert referential_head("the muddy lane") == "lane"
    assert referential_head("the tired porter") == "porter"
    assert referential_head("the old innkeeper") == "innkeeper"
    assert referential_person_nominal("the tired porter") == "tired porter"
    assert referential_person_nominal("the muddy lane") is None


def test_compound_person_roles_keep_context_when_required():
    assert referential_head("the stable hand") == "stable hand"
    assert referential_person_nominal("the stable hand") == "stable hand"
    assert referential_person_nominal("the hand") is None
    assert referential_head("the gate guard") == "guard"
    assert referential_person_nominal("the gate guard") == "gate guard"
    assert referential_person_nominal("the cloth merchant") == "cloth merchant"
    assert referential_person_nominal("the caravan master") == "caravan master"
    assert referential_person_nominal("the tavern keeper") == "tavern keeper"
    assert referential_head("the notice board") == "board"
    assert referential_person_nominal("the notice board") is None


def test_postnominal_modifiers_do_not_replace_the_head():
    assert referential_head("the porter by the gate") == "porter"
    assert referential_head("the innkeeper behind the counter") == "innkeeper"
    assert referential_head("the lane northwest of the crates") == "lane"
    assert referential_head("the wagon beside the wall") == "wagon"
    assert referential_head("the room upstairs") == "room"
    assert referential_person_nominal("the porter by the gate") == "porter"
    assert referential_person_nominal("the lane northwest of the crates") is None
    assert referential_person_nominal("the room upstairs") is None


def test_participles_infinitives_and_relatives_leave_the_noun():
    assert referential_head("the porter carrying crates") == "porter"
    assert referential_head("the woman sweeping the steps") == "woman"
    assert referential_head("the traveler waiting by the wall") == "traveler"
    assert referential_head("the wagon blocking the road") == "wagon"
    assert referential_head("the merchant to ask") == "merchant"
    assert referential_head("the guard to speak with") == "guard"
    assert referential_head("the inn to visit") == "inn"
    assert referential_head("the gate to inspect") == "gate"
    assert referential_head("the porter who carried the crates") == "porter"
    assert referential_head("the wagon that blocked the road") == "wagon"
    assert referential_person_nominal("the woman sweeping the steps") == "woman"
    assert referential_person_nominal("the merchant to ask") == "merchant"
    assert referential_person_nominal("the inn to see") is None
    assert referential_person_nominal("the wagon that blocked the road") is None


def test_direction_cannot_become_the_head():
    for span in (
        "the muddy lane northwest of the crates",
        "the road northwest of the gate",
        "the lane northwest",
        "the room upstairs",
    ):
        head = referential_head(span)
        assert head not in {"northwest", "upstairs", "north", "west"}
        assert referential_person_nominal(span) is None


def test_unknown_personhood_abstains_and_agentive_roles_still_bind():
    assert personhood_of_span("the beadle") == "unknown"
    assert referential_person_nominal("the beadle") is None
    assert referential_person_nominal("the lamplighter") == "lamplighter"
    decision = resolve_proposed_interlocutor(
        "the beadle",
        "the beadle",
        scene=POPULATED,
        session=_focus(active_interlocutor=None),
        scene_id="frontier_gate",
        catalog=CATALOG,
    )
    assert decision["status"] != "bound_incidental"
    assert "personhood_unresolved" in " ".join(decision["authority_reasons"])
    lamplighter = resolve_proposed_interlocutor(
        "the lamplighter",
        "the lamplighter",
        scene=POPULATED,
        session=_focus(active_interlocutor=None),
        scene_id="frontier_gate",
        catalog=CATALOG,
    )
    assert lamplighter["status"] == "bound_incidental"
    assert lamplighter["label"] == "lamplighter"


def test_model_person_label_cannot_override_a_nonperson_head():
    decision = resolve_proposed_interlocutor(
        "the muddy lane northwest of the crates",
        "the muddy lane northwest of the crates",
        scene=POPULATED,
        session=_focus(active_interlocutor=None),
        scene_id="frontier_gate",
        catalog=CATALOG,
    )
    assert decision["status"] != "bound_incidental"
    assert decision["entity_id"] is None
    assert referential_head("the muddy lane northwest of the crates") == "lane"


def test_coordination_does_not_invent_one_person():
    assert personhood_of_span("the inn and the porter") == "coordinated"
    assert referential_person_nominal("the inn and the porter") is None
    assert referential_nominal("the inn and the porter") is None


def test_historical_malformed_spans_are_not_people():
    for span in HISTORICAL_SPANS:
        assert referential_person_nominal(span) is None, span


def test_valid_person_controls():
    assert len(VALID_PEOPLE) == 15
    for span, label in VALID_PEOPLE.items():
        assert referential_person_nominal(span) == label, span
        assert personhood_of_span(span) == "person"


def test_nonperson_controls():
    assert len(NONPEOPLE) == 13
    for span in NONPEOPLE:
        assert referential_person_nominal(span) is None, span
        assert referential_nominal(span), span
        assert referential_head(span) not in {"northwest", "upstairs", "see", "inspect", "follow", "blocking"}


def test_structural_variations_generalize():
    people = {
        "the cold tired porter": "cold tired porter",
        "those travelers": "travelers",
        "an old innkeeper": "old innkeeper",
        "this sentry": "sentry",
        "the brewer by the barrels": "brewer",
    }
    for span, label in people.items():
        assert referential_head(span) in {"porter", "travelers", "innkeeper", "sentry", "brewer"}
        assert referential_person_nominal(span) == label, span
    blocked = {
        "the narrow stone bridge beside the tower": "bridge",
        "the iron lantern above the door": "lantern",
        "the cellar under the inn": "cellar",
        "the porter's lantern": "lantern",
        "the woman's brother": "brother",
    }
    assert referential_person_nominal("the narrow stone bridge beside the tower") is None
    assert referential_head("the narrow stone bridge beside the tower") == "bridge"
    assert referential_person_nominal("the iron lantern above the door") is None
    assert referential_head("the iron lantern above the door") == "lantern"
    assert referential_head("the cellar under the inn") == "cellar"
    assert referential_person_nominal("the cellar under the inn") is None
    assert referential_head("the porter's lantern") == "lantern"
    assert referential_person_nominal("the porter's lantern") is None
    assert referential_head("the woman's brother") == "brother"
    assert referential_person_nominal("the woman's brother") == "brother"
    assert personhood_of_span("the gate and the porter") == "coordinated"
    assert blocked


def test_player_input_integration():
    cases = (
        ("I head down the muddy lane northwest of the crates.", None),
        (
            "I ask the tired porter carrying crates whether anyone came through the north road.",
            "tired porter",
        ),
        ("I go to the inn to see if the innkeeper knows anything.", "innkeeper"),
        ("I inspect the wagon beside the wall.", None),
        ("I speak with the woman sweeping the steps.", "woman"),
        ("I follow the road northwest of the gate.", None),
        ("I approach the merchant to ask about the missing patrol.", "merchant"),
        ("I examine the underbrush for whatever is moving out there.", None),
    )
    for text, person in cases:
        session = _focus()
        contract = _contract(text, session)
        binding = _binding(contract)
        if person:
            assert binding["status"] == "bound_incidental", (text, binding)
            assert binding["label"] == person
            assert "inn to see" not in str(binding.get("label") or "")
            assert "northwest" not in str(binding.get("label") or "")
        else:
            assert binding["status"] != "bound_incidental", (text, binding)
            span = str(binding.get("proposed_span") or "")
            label = str(binding.get("label") or "")
            assert label not in {"muddy lane", "muddy lane northwest", "inn to see", "wagon", "underbrush"}
            if binding.get("explicit_new_interlocutor"):
                assert contract.interlocutor_id != "tavern_runner"
            if span:
                assert referential_head(span) not in {"northwest", "see"}
                assert referential_person_nominal(span) is None
            commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
            stored = {str(row.get("label") or "") for row in _entities(session)}
            assert stored.isdisjoint({"muddy lane", "muddy lane northwest", "inn to see", "wagon", "underbrush"})


def test_historical_player_turns_do_not_persist_malformed_people():
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
        "muddy lane northwest",
        "muddy lane",
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


def test_turn3_movement_is_not_caused_by_the_lane_binding():
    session = _focus()
    contract = _contract(TURN3, session)
    binding = _binding(contract)
    assert contract.operation == "inspect"
    assert binding["status"] != "bound_incidental"
    assert binding["label"] is None
    assert referential_head(binding.get("proposed_span") or "") == "lane"
    assert "personhood_unresolved" in " ".join(binding["authority_reasons"])
    assert contract.interlocutor_id != "tavern_runner"
    action = parse_freeform_to_action(TURN3, SCENE, session=session)
    # The lane binding never selected the exit. The exit matcher was firing on
    # "before deciding whether to follow ... old milestone". That clause is not
    # a current commitment, so the transition does not run.
    assert action is None or action.get("type") != "scene_transition"
    assert action is None or action.get("target_scene_id") != "old_milestone"


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


def test_raw_chat_stub_covers_referential_heads(chat, monkeypatch):
    def fake_gpt(messages, **kwargs):
        blob = " ".join(
            str(message.get("content") or "")
            for message in messages
            if isinstance(message, dict) and message.get("role") == "user"
        ).lower()
        if "tired porter" in blob or "ask a porter" in blob:
            return _gm_response('The tired porter says, "A few wagons came down the north road."')
        if "woman" in blob:
            return _gm_response('The woman says, "The steps are slick."')
        if "merchant" in blob:
            return _gm_response('The merchant says, "The patrol has not come back."')
        if "innkeeper" in blob:
            return _gm_response('The innkeeper says, "There is stew, if you can pay."')
        return _gm_response("The road runs on. No one new steps forward.")

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)

    porter = chat.post(
        "/api/chat",
        json={"text": "I ask the tired porter carrying crates whether the wagons are through."},
    ).json()
    _porter_contract, porter_binding = _contract_of(porter)
    assert porter_binding.get("status") == "bound_incidental"
    porter_id = porter_binding.get("bound_interlocutor_id")

    lane = chat.post(
        "/api/chat",
        json={"text": "I turn toward the muddy lane northwest of the crates."},
    ).json()
    lane_contract, lane_binding = _contract_of(lane)
    assert lane_binding.get("status") != "bound_incidental"
    assert lane_contract.get("interlocutor_id") != porter_id
    assert referential_head(lane_binding.get("proposed_span") or "") == "lane"
    assert semantic_equal(
        lane["gm_output"]["player_facing_text"],
        lane["gm_output"]["metadata"]["accepted_response"]["text"],
    )

    woman = chat.post(
        "/api/chat",
        json={"text": "I speak with the woman sweeping the steps."},
    ).json()
    _woman_contract, woman_binding = _contract_of(woman)
    assert woman_binding.get("status") == "bound_incidental"
    assert woman_binding.get("label") == "woman"

    merchant = chat.post(
        "/api/chat",
        json={"text": "I approach the merchant to ask about the missing patrol."},
    ).json()
    _merchant_contract, merchant_binding = _contract_of(merchant)
    assert merchant_binding.get("status") == "bound_incidental"
    assert merchant_binding.get("label") == "merchant"

    inn = chat.post(
        "/api/chat",
        json={"text": "I go to the inn to see if the innkeeper knows anything."},
    ).json()
    _inn_contract, inn_binding = _contract_of(inn)
    assert inn_binding.get("status") == "bound_incidental"
    assert inn_binding.get("label") == "innkeeper"
    assert "inn to see" not in str(inn_binding.get("label") or "")

    wagon = chat.post("/api/chat", json={"text": "I inspect the wagon beside the wall."}).json()
    _wagon_contract, wagon_binding = _contract_of(wagon)
    assert wagon_binding.get("status") != "bound_incidental"

    road = chat.post(
        "/api/chat",
        json={"text": "I follow the road northwest of the gate."},
    ).json()
    _road_contract, road_binding = _contract_of(road)
    assert road_binding.get("status") != "bound_incidental"
    if road_binding.get("proposed_span"):
        assert referential_head(road_binding["proposed_span"]) != "northwest"

    session = storage.load_session()
    labels = {
        str(row.get("label") or "")
        for row in (session.get("bounded_improvisation") or {}).get("incidental_entities") or []
    }
    assert "muddy lane" not in labels
    assert "muddy lane northwest" not in labels
    assert "inn to see" not in labels
    assert "wagon" not in labels
    assert any(label == "tired porter" for label in labels)
    assert any(label == "woman" for label in labels)
    assert any(label == "merchant" for label in labels)
    assert any(label == "innkeeper" for label in labels)
