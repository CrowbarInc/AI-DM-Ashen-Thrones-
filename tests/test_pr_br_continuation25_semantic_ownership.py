"""PR-BR C25: one Resolution Contract owns ordinary gameplay semantics. Stubbed."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from game.api import app
from game.contract_adjudication_bridge import CATEGORY_A_IDS
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.ordinary_semantic_ownership import (
    OFFSCENE_SOCIAL_CLASS,
    PEER_PARSER_ROLES,
    PENDING_CHECK_CLASS,
    RESOLVER_CONTRACTS,
    SEGMENTATION_ROLE,
    action_contradicts_contract,
    select_ordinary_resolver,
    stage_permitted,
)
from game.player_commitment import EXECUTED_NOW
from game.resolution_contract import construct_resolution_contract
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]


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
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: _gm_response("The gate is quiet."))
    monkeypatch.setattr("game.gm.call_gpt", lambda *_a, **_k: _gm_response("The gate is quiet."))
    return TestClient(app)


def _built(text: str):
    contract = construct_resolution_contract(player_text=text).as_dict()
    resolver, family = select_ordinary_resolver(contract, in_combat=False)
    return contract, resolver, family


def _contract(payload):
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    return resolution, meta, contract


def test_peer_parsers_have_one_role():
    expected = {
        "segmentation": "structural",
        "directed_social_entry": "structural",
        "social_parser": "resolver",
        "dialogue_first": "resolver",
        "exploration": "resolver",
        "world_action_recovery": "resolver_helper",
        "generic_intent": "resolver_helper",
        "declared_travel": "resolver",
        "in_chat_attack": "resolver",
        "adjudication": "resolver",
        "offscene_social_text": "downstream_consequence",
        "pending_check_prompt": "downstream_consequence",
        "resolution_contract": "contract_constructor",
        "interpretation_validation": "contract_validator",
    }
    assert PEER_PARSER_ROLES == expected
    assert SEGMENTATION_ROLE == "structural"
    assert OFFSCENE_SOCIAL_CLASS == "downstream_consequence"
    assert PENDING_CHECK_CLASS == "downstream_consequence"
    assert CATEGORY_A_IDS == (
        "session_administration",
        "initiative_status_line",
        "end_turn_status_line",
        "campaign_start_cue",
    )


def test_resolver_contracts_name_failure_behavior():
    for name, spec in RESOLVER_CONTRACTS.items():
        assert spec["required"]
        assert "failure" in spec
        assert "preserve contract" in spec["failure"]
    assert "social" in RESOLVER_CONTRACTS
    assert "travel" in RESOLVER_CONTRACTS
    assert "combat" in RESOLVER_CONTRACTS


def test_no_contract_selects_generation_and_rejects_action():
    assert select_ordinary_resolver(None) == ("generation", None)
    assert select_ordinary_resolver({"operation": "ask"}) == ("generation", None)
    assert action_contradicts_contract({"type": "travel"}, {"operation": "ask"}) is True


def test_y1_through_y20_matrix():
    cases = [
        ("I ask the guard about the patrol.", "ask", "social", None),
        ("I ask the runner what he heard and listen carefully.", "ask", "social", None),
        ("What have you heard?", "ask", "social", None),
        ("I ask Serjeant Voss about the gate.", "ask", "social", None),
        ("I inspect the crate.", "inspect", "exploration", None),
        ("I inspect the tracks before deciding whether to follow them.", "inspect", "exploration", None),
        ("I listen at the door.", "perceive", "exploration", None),
        ("I follow the road to the milestone.", "act", "travel", None),
        ("Would the road lead to the milestone?", "ask", "adjudication", "feasibility"),
        ("If the road is clear, I will head to the milestone.", "ask", "social", None),
        ("I open the door.", "act", "world_action", None),
        ("I open the door and ask what is inside.", "unresolved", "generation", None),
        ("I attack the bandit.", "act", "generation", None),
        ("If he draws, I attack the bandit.", "ask", "social", None),
        ("Who is nearby?", "ask", "adjudication", "nearby_presence"),
        ("Can I find supplies nearby?", "ask", "adjudication", "place_location"),
        ("Can I sneak past without being seen?", "ask", "adjudication", "feasibility"),
        ("I inspect the tracks, then follow them.", "inspect", "exploration", None),
        ("I ask the guard about the crate or the road.", "ask", "social", None),
        ("Please transmute the moon into cheese.", "ask", "social", None),
    ]
    assert len(cases) == 20
    for text, operation, resolver, family in cases:
        contract, got, got_family = _built(text)
        assert contract.get("contract_id"), text
        assert contract.get("operation") == operation, text
        assert got == resolver, text
        assert got_family == family, text
        construction = contract.get("construction") or {}
        if text.startswith("If "):
            assert construction.get("commitment_status") != EXECUTED_NOW
        if resolver == "travel":
            assert construction.get("commitment_status") == EXECUTED_NOW


def test_attack_resolver_requires_combat_and_commitment():
    contract = construct_resolution_contract(player_text="I attack the bandit.").as_dict()
    assert select_ordinary_resolver(contract, in_combat=False)[0] == "generation"
    assert select_ordinary_resolver(contract, in_combat=True)[0] == "combat"
    hypothetical = construct_resolution_contract(player_text="If he draws, I attack the bandit.").as_dict()
    assert select_ordinary_resolver(hypothetical, in_combat=True)[0] != "combat"


def test_multi_clause_primary_is_not_stolen():
    ask, ask_resolver, _family = _built("I ask the runner what he heard and listen carefully.")
    inspect, inspect_resolver, _family = _built("I inspect the tracks before deciding whether to follow them.")
    sequence, sequence_resolver, _family = _built("I inspect the tracks, then follow them.")
    before, before_resolver, _family = _built("I ask the guard whether the road is safe before heading out.")
    walk, walk_resolver, _family = _built("I walk to the merchant and ask about supplies.")
    listen, listen_resolver, _family = _built("I listen at the door.")
    assert ask["operation"] == "ask" and ask_resolver == "social"
    assert inspect["operation"] == "inspect" and inspect_resolver == "exploration"
    assert sequence["operation"] == "inspect" and sequence_resolver == "exploration"
    assert before["operation"] == "ask" and before_resolver == "social"
    assert walk["operation"] == "ask" and walk_resolver == "social"
    assert listen["operation"] == "perceive" and listen_resolver == "exploration"
    assert not stage_permitted("social", "travel")
    assert not stage_permitted("exploration", "social")
    assert stage_permitted("adjudication", "social") is False


def test_ask_contract_rejects_travel_and_perception_takeover():
    contract, _resolver, _family = _built("I ask the guard about the patrol.")
    assert action_contradicts_contract({"type": "travel"}, contract)
    assert action_contradicts_contract({"type": "observe"}, contract)
    assert action_contradicts_contract({"type": "question"}, contract) is False


def test_ordinary_contract_is_established_before_peer_parsers():
    source = (ROOT / "game" / "api.py").read_text(encoding="utf-8")
    establish = source.index("establish_ordinary_gameplay_contract(")
    assert establish < source.index("parse_social_intent(", establish)
    assert establish < source.index("parse_exploration_intent(", establish)
    assert establish < source.index("recover_actionable_explicit_world_action(", establish)
    assert establish < source.index("parse_intent(", establish)
    assert establish < source.index("maybe_build_declared_travel_action(", establish)
    assert "player_text=req.text" in source[establish:establish + 600]


def test_chat_turns_keep_one_contract_and_do_not_execute_uncommitted_travel(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    client = _client(monkeypatch)
    scene_before = storage.load_session().get("active_scene_id")
    texts = [
        "I ask the guard about the patrol.",
        "I inspect the crate.",
        "I listen at the door.",
        "If the road is clear, I will head to the milestone.",
        "Who is nearby?",
        "I follow the road to the milestone.",
    ]
    for text in texts:
        payload = client.post("/api/chat", json={"text": text}).json()
        resolution, meta, contract = _contract(payload)
        assert contract.get("contract_id"), text
        assert meta.get("semantic_owner") == "resolution_contract"
        assert meta.get("contract_before_resolver") is True
        assert meta.get("selected_resolver")
        if text.startswith("If "):
            assert storage.load_session().get("active_scene_id") == scene_before
        if text == "Who is nearby?":
            assert resolution.get("kind") == "adjudication_query"
            assert meta.get("adjudication_resolver_family") == "nearby_presence"
    assert storage.load_combat().get("in_combat") is not True
