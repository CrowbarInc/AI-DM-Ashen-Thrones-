"""PR-BR C24: contract before unparsed adjudication. Stubbed. No paid model calls."""
from __future__ import annotations

from fastapi.testclient import TestClient

from game.api import app
from game.contract_adjudication_bridge import (
    CATEGORY_A_IDS,
    resolve_selected_family,
    select_resolver_family,
)
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.resolution_contract import construct_resolution_contract
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

C22 = (
    'I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. '
    '"Thank you for the warning. Have you heard anything about who or what might be causing trouble there? '
    "Any chance I could find shelter or supplies nearby before investigating further?"
)


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


def _client(monkeypatch):
    monkeypatch.setattr(
        "game.semantic_interpreter._invoke_interpretation_model",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("interpretation model")),
    )
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_a, **_k: _gm_response('The tavern runner says, "I heard the trouble is northwest of the crates."'),
    )
    monkeypatch.setattr("game.gm.call_gpt", lambda *_a, **_k: _gm_response("The tavern runner says, \"I heard the trouble is northwest of the crates.\""))
    return TestClient(app)


def _contract(payload):
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    return resolution, meta, contract


def _visible(payload):
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    return str(gm.get("player_facing_text") or "")


def _accepted(payload):
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    return str(accepted.get("text") or "")


def _built(text):
    contract = construct_resolution_contract(player_text=text).as_dict()
    return contract, select_resolver_family(contract)


def test_category_a_exclusions_are_named_and_not_chat_sentences():
    assert CATEGORY_A_IDS == (
        "session_administration",
        "initiative_status_line",
        "end_turn_status_line",
        "campaign_start_cue",
    )


def test_no_contract_refuses_specialized_resolution():
    assert select_resolver_family(None) is None
    assert select_resolver_family({"operation": "ask"}) is None
    assert (
        resolve_selected_family(
            "earshot",
            {"operation": "ask", "raw_input": "Who is nearby?"},
            scene={},
            session={},
            world={},
            character={},
        )
        is None
    )


def test_nearby_contrast_g1_through_g5():
    who, who_family = _built("Who is nearby?")
    supplies, supplies_family = _built("Can I find supplies nearby?")
    ask, ask_family = _built("I ask the runner if there are supplies nearby.")
    shelter, shelter_family = _built("Is there shelter nearby?")
    listen, listen_family = _built("I listen for anyone nearby.")
    assert who["operation"] == "ask" and who_family in {"earshot", "nearby_presence"}
    assert supplies_family == "place_location"
    assert supplies_family != who_family
    assert ask["operation"] == "ask" and ask_family is None
    assert shelter_family == "place_location"
    assert listen["operation"] == "perceive" and listen_family == "earshot"


def test_place_resolver_does_not_list_earshot(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    contract, family = _built("Can I find supplies nearby?")
    result = resolve_selected_family(
        family,
        contract,
        scene=storage.load_scene("frontier_gate"),
        session=storage.load_session(),
        world=storage.load_world(),
        character=storage.load_character(),
    )
    text = str((result or {}).get("player_facing_text") or "")
    assert family == "place_location"
    assert "In earshot" not in text
    assert result.get("contract_operation") == contract["operation"]
    assert result.get("contract_id") == contract["contract_id"]


def test_ask_contract_cannot_be_replaced_by_earshot():
    contract = construct_resolution_contract(player_text="I ask the runner if there are supplies nearby.").as_dict()
    contract["interlocutor_id"] = "tavern_runner"
    contract["operation"] = "ask"
    assert select_resolver_family(contract) is None
    assert (
        resolve_selected_family(
            "earshot",
            contract,
            scene={},
            session={},
            world={},
            character={},
        )
        is None
    )


def test_p1_c22_after_runner_keeps_contract_and_runner(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    client = _client(monkeypatch)
    first = client.post(
        "/api/chat",
        json={"text": "I ask the tavern runner what he heard about the patrol."},
    ).json()
    _, _, first_contract = _contract(first)
    second = client.post("/api/chat", json={"text": C22}).json()
    resolution, meta, contract = _contract(second)
    visible = _visible(second)
    assert first_contract.get("interlocutor_id") == "tavern_runner"
    assert contract.get("contract_id")
    assert meta.get("contract_before_resolver") is True
    assert contract.get("operation") == "ask"
    assert resolution.get("kind") != "adjudication_query"
    assert "The guard says" not in visible
    assert "In earshot right now" not in visible
    assert _accepted(second) == visible


def test_p2_through_p8_and_nearby_controls(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    client = _client(monkeypatch)
    scene_before = storage.load_session().get("active_scene_id")
    cases = [
        ("Who is nearby?", {"earshot", "nearby_presence"}, True),
        ("Can I find supplies nearby?", {"place_location"}, False),
        ("I ask the runner if there are supplies nearby.", set(), False),
        ("I listen for anyone nearby.", {"earshot"}, False),
        ("Is there shelter nearby?", {"place_location"}, False),
        ("Would the road nearby take me to the milestone?", {"feasibility"}, False),
        ("If the guard refuses, I'll look for shelter nearby.", set(), False),
    ]
    for text, families, allow_roster in cases:
        payload = client.post("/api/chat", json={"text": text}).json()
        resolution, meta, contract = _contract(payload)
        visible = _visible(payload)
        assert contract.get("contract_id"), text
        assert meta.get("contract_before_resolver") is True or resolution.get("kind") != "adjudication_query"
        family = meta.get("adjudication_resolver_family")
        if resolution.get("kind") == "adjudication_query":
            assert family in families, (text, family)
            assert _accepted(payload) == visible
        else:
            assert family in families or family is None
        if not allow_roster:
            assert "In earshot right now" not in visible
        assert "The guard says" not in visible
        assert storage.load_session().get("active_scene_id") == scene_before


def test_adjudication_family_matrix():
    rows = [
        ("Is anyone else in earshot?", "earshot"),
        ("Who is nearby?", "nearby_presence"),
        ("Is there shelter nearby?", "place_location"),
        ("Can I sneak past without being seen?", "feasibility"),
        ("What actions are available?", "state_query"),
        ("Is Sleight of Hand needed?", "roll_mechanical"),
    ]
    for text, expected in rows:
        contract, family = _built(text)
        assert family == expected, (text, family)
        assert contract.get("contract_id")
        bare = dict(contract)
        bare.pop("contract_id", None)
        assert resolve_selected_family("earshot", bare, scene={}, session={}, world={}, character={}) is None
    generic = construct_resolution_contract(player_text="What actions are available?").as_dict()
    generic_result = resolve_selected_family(
        "generic_adjudication",
        generic,
        scene={"scene": {"id": "frontier_gate"}},
        session={},
        world={"npcs": []},
        character={},
    )
    assert generic_result is not None
    assert generic_result.get("contract_id") == generic["contract_id"]
    assert generic_result.get("contract_operation") == generic["operation"]


def test_s1_through_s8_compound_turns_keep_contract(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    client = _client(monkeypatch)
    client.post("/api/chat", json={"text": "I ask the tavern runner what he heard about the patrol."})
    compounds = [
        "Have you heard who is causing the trouble? Could I find supplies nearby?",
        "I ask the runner what he heard, and I listen carefully.",
        "I inspect the notice. Later I might head for the milestone.",
        "If the guard refuses, I'll look for shelter nearby.",
        "I inspect the notice and then ask the runner what he heard.",
        "Where did he hear that, and is there shelter nearby?",
        "Could I get past the gate if he allows it?",
        "Do I need to roll to convince him?",
    ]
    for text in compounds:
        payload = client.post("/api/chat", json={"text": text}).json()
        resolution, meta, contract = _contract(payload)
        visible = _visible(payload)
        assert contract.get("contract_id"), text
        assert "In earshot right now" not in visible
        assert "The guard says" not in visible
        if resolution.get("kind") == "adjudication_query":
            assert meta.get("contract_before_resolver") is True
            assert _accepted(payload) == visible
            assert meta.get("adjudication_resolver_family") not in {"earshot", "nearby_presence"}
