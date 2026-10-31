"""PR-BR Continuation 20: incidental entity binding and intent-preserving abstention.

Deterministic only. No paid model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus, note_emitted_npc_claim, read_discourse_focus
from game.immutable_valid_response import (
    PROVENANCE_REGENERATION,
    run_preserve_if_valid,
    validate_generated_response,
)
from game.proposition_authority import NPC_CLAIM_KIND, unauthorized_authoritative_rules
from game.resolution_contract import construct_resolution_contract
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads((ROOT / "data" / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
C19_TURNS = ROOT / "artifacts" / "pr_br_continuation19" / "20261002T002239Z" / "turns.json"

RUNNER = {"id": "tavern_runner", "type": "interlocutor", "label": "Tavern Runner", "aliases": ["runner", "tavern runner"], "source": "scene"}
GUARD = {"id": "guard_captain", "type": "interlocutor", "label": "Guard Captain", "aliases": ["captain", "guard"], "source": "scene"}
NOTICE = {"id": "notice_board", "type": "object", "label": "Notice board", "aliases": ["notice", "board"], "source": "scene"}
CATALOG = [RUNNER, GUARD, NOTICE]

THIRD_BELL = "The gate officially closes at the third bell."
HEARD = "I heard patrols have been delayed."

POPULATED = {
    "scene": {
        "id": "gate_crowd",
        "summary": "A crowded gate market. Travelers, wagons, and vendors fill the approach.",
        "visible_facts": ["People press through the queue beside the tavern."],
    }
}
CRYPT = {"scene": {"id": "sealed_crypt", "summary": "A sealed empty crypt. Nobody remains.", "visible_facts": ["The chamber is empty and sealed."]}}
SHRINE = {"scene": {"id": "mountain_shrine", "summary": "An isolated mountain shrine. The place is deserted.", "visible_facts": ["No one keeps this shrine."]}}
RUIN = {"scene": {"id": "abandoned_ruin", "summary": "An abandoned ruin. No one remains.", "visible_facts": ["The ruin is deserted."]}}


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
    return {"active_scene_id": "frontier_gate", "turn_counter": 4, DISCOURSE_FOCUS_KEY: focus, "bounded_improvisation": {"entries": [], "incidental_entities": []}}


def _contract(text, session=None, scene=SCENE, catalog=None, interpreter=None, scene_id="frontier_gate"):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id=scene_id,
        canonical_referents=CATALOG if catalog is None else catalog,
        model_interpreter=interpreter,
        scene=scene,
    )


def _binding(contract):
    return contract.construction["entity_binding"]


def _entities(session):
    ledger = session.get("bounded_improvisation") or {}
    return [row for row in ledger.get("incidental_entities") or [] if isinstance(row, dict)]


def test_canonical_entity_binds_without_incidental_instantiation():
    session = _focus()
    contract = _contract("I ask the tavern runner what travelers are saying about the gate tonight.", session)
    binding = _binding(contract)
    assert contract.operation == "ask"
    assert contract.interlocutor_id == "tavern_runner"
    assert binding["status"] == "bound_canonical"
    assert binding["entity_class"] == "canonical_established"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert _entities(session) == []


def test_cloth_merchant_binds_and_does_not_keep_the_tavern_runner():
    session = _focus()
    text = "I walk over to the cloth merchant and ask whether anyone has come through from the north road today."
    contract = _contract(text, session)
    binding = _binding(contract)
    assert contract.operation == "ask"
    assert binding["proposed_interlocutor"] == "cloth merchant"
    assert binding["status"] == "bound_incidental"
    assert contract.interlocutor_id != "tavern_runner"
    assert str(contract.interlocutor_id).startswith("inc_")
    assert binding["label"] == "cloth merchant"
    assert "pr_bn:accepted" in binding["authority_reasons"]
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    stored = _entities(session)
    assert len(stored) == 1
    assert stored[0]["entity_id"] == contract.interlocutor_id
    assert read_discourse_focus(session)["active_interlocutor"]["id"] == contract.interlocutor_id
    follow = _contract("Who told you that?", session)
    assert follow.operation == "ask"
    assert follow.dimension == "source"
    assert follow.interlocutor_id == contract.interlocutor_id
    assert follow.interlocutor_id != "tavern_runner"
    assert _binding(follow)["claim_binding"] == "unresolved"


def test_source_inquiry_survives_a_model_that_proposes_content():
    session = _focus(active_interlocutor={"id": "tavern_runner", "label": "Tavern Runner", "kind": "interlocutor"}, active_claim=None)

    def _content(_ctx):
        return {
            "status": "proposed",
            "api_calls": 0,
            "proposal": {
                "primary_operation": "ask",
                "dimension": "content",
                "dimensions": ["content", "source"],
                "interlocutor_id": "tavern_runner",
            },
        }

    contract = _contract("Who told you that?", session, interpreter=_content)
    assert contract.operation == "ask"
    assert contract.dimension == "source"
    assert "content" not in contract.dimensions
    assert _binding(contract)["claim_binding"] == "unresolved"
    assert contract.discourse_ref is None or contract.discourse_ref.type != "claim" or not contract.discourse_ref.id


def test_source_with_an_active_claim_still_binds_the_claim():
    session = _focus(active_claim={"id": "claim-9", "label": "Patrols have been delayed.", "kind": "claim", "turn_index": 2})
    contract = _contract("Who told you that?", session)
    assert contract.operation == "ask"
    assert contract.dimension == "source"
    assert contract.interlocutor_id == "tavern_runner"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-9"
    assert _binding(contract)["claim_binding"] == "bound"


def test_incidental_variants_bind_in_a_populated_scene():
    samples = (
        "I ask one of the porters whether the wagons are through.",
        "I stop a passing traveler and ask if the road is quiet.",
        "I speak to the stable hand about the horses.",
        "I ask the woman sweeping the steps whether the gate is busy.",
        "I turn to a nearby merchant and ask what people are carrying.",
    )
    for text in samples:
        session = _focus()
        session["active_scene_id"] = "gate_crowd"
        contract = _contract(text, session, scene=POPULATED, scene_id="gate_crowd")
        binding = _binding(contract)
        assert contract.operation == "ask", text
        assert contract.interlocutor_id != "tavern_runner", text
        assert binding["status"] == "bound_incidental", (text, binding)
        assert str(contract.interlocutor_id).startswith("inc_"), text


def test_implausible_entities_are_not_instantiated():
    samples = (
        (CRYPT, "sealed_crypt", "I ask the cloth merchant whether anyone is here."),
        (SHRINE, "mountain_shrine", "I speak to the dockworker about the tide."),
        (RUIN, "abandoned_ruin", "I ask the tavern patron what happened here."),
    )
    for scene, scene_id, text in samples:
        session = _focus()
        session["active_scene_id"] = scene_id
        contract = _contract(text, session, scene=scene, scene_id=scene_id)
        binding = _binding(contract)
        assert contract.operation == "ask", text
        assert contract.interlocutor_id != "tavern_runner", text
        assert binding["status"] == "unresolved", (text, binding)
        assert binding["explicit_new_interlocutor"] is True
        commit_discourse_focus(session, contract=contract.as_dict(), scene_id=scene_id)
        assert _entities(session) == [], text
        assert read_discourse_focus(session)["active_interlocutor"] is None


def test_consequential_and_authority_roles_are_not_instantiated():
    samples = (
        "I ask the assassin who killed the duke.",
        "I speak to the spy working for the Ash Compact.",
        "I find the officer who ordered the patrol murdered.",
        "I question the wizard who knows the secret entrance.",
        "I ask the king's secret adviser.",
        "I speak to the commander of the hidden rebel cell.",
        "I ask the magistrate who secretly takes bribes.",
    )
    for text in samples:
        session = _focus()
        contract = _contract(text, session)
        binding = _binding(contract)
        assert contract.operation == "ask", text
        assert contract.interlocutor_id != "tavern_runner", text
        assert binding["status"] == "rejected_consequential", (text, binding)
        assert binding["entity_class"] == "unsupported_consequential"
        commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
        assert _entities(session) == [], text
        assert read_discourse_focus(session)["active_interlocutor"] is None


def test_stable_identity_across_pronoun_and_role():
    session = _focus()
    first = _contract("I ask one of the porters whether the wagons are through.", session)
    commit_discourse_focus(session, contract=first.as_dict(), scene_id="frontier_gate")
    pronoun = _contract("I ask him where he heard that.", session)
    role = _contract("I ask the porter whether the line has moved.", session)
    assert first.interlocutor_id == pronoun.interlocutor_id == role.interlocutor_id
    commit_discourse_focus(session, contract=role.as_dict(), scene_id="frontier_gate")
    assert len(_entities(session)) == 1


def test_incidental_record_stays_minimal():
    session = _focus()
    contract = _contract(
        "I walk over to the cloth merchant and ask whether anyone has come through from the north road today.",
        session,
    )
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    record = _entities(session)[0]
    assert record["label"] == "cloth merchant"
    assert record["role"] == "cloth merchant"
    assert record["provenance"] == "bounded_incidental"
    for forbidden in ("name", "faction", "family", "secret", "inventory", "quest", "biography"):
        assert forbidden not in record
    assert record["label"] == record["label"].lower()


def test_incidental_hearsay_stays_a_claim():
    verdict = validate_generated_response(f'The porter says, "{HEARD}"', player_text="What have you heard?")
    assert verdict["hard_valid"] is True
    assert any(row["kind"] == NPC_CLAIM_KIND for row in verdict["authority"])
    assert unauthorized_authoritative_rules(HEARD) == []
    session = _focus()
    scene = {"scene": {"id": "frontier_gate", "visible_facts": ["Rain on the gate approach."]}}
    assert note_emitted_npc_claim(session, emitted_text=f'The porter says, "{HEARD}"', scene_id="frontier_gate") is True
    claim = read_discourse_focus(session)["active_claim"]
    assert claim["epistemic_status"] in {"hearsay", "rumor", "uncertain"}
    assert HEARD.lower() not in " ".join(scene["scene"]["visible_facts"]).lower()


def test_incidental_speaker_cannot_bypass_the_authority_boundary():
    verdict = validate_generated_response(
        f'The porter says, "{THIRD_BELL}"',
        player_text="When does the gate close?",
        contract={"operation": "ask", "interlocutor_id": "inc_porter", "construction": {"entity_binding": {"status": "bound_incidental", "label": "porter"}}},
    )
    assert verdict["hard_valid"] is False
    assert "ungrounded_authoritative_rule" in verdict["reasons"]

    def _retry(_note):
        return {"player_facing_text": 'The porter says, "I cannot give you an hour that is settled here."', "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": f'The porter says, "{THIRD_BELL}"', "metadata": {}},
        regenerate=_retry,
        resolution={"kind": "question", "metadata": {"resolution_contract": {"operation": "ask", "contract_id": "rc"}}},
        player_text="When does the gate close?",
    )
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert "third bell" not in sealed["player_facing_text"].lower()


def test_pronoun_resolution_still_inherits_the_canonical_interlocutor():
    session = _focus(active_interlocutor={"id": "guard_captain", "label": "Guard Captain", "kind": "interlocutor"})
    contract = _contract("What does he mean by that?", session)
    assert contract.interlocutor_id == "guard_captain"
    assert contract.operation == "ask"


def test_c19_live_turns_replay_with_incidental_binding_and_source_dimension():
    turns = json.loads(C19_TURNS.read_text(encoding="utf-8"))
    by_number = {int(row["turn_number"]): row for row in turns}
    assert len(by_number) == 4
    session = _focus()
    first = _contract(by_number[1]["player_input"], session)
    assert first.operation == "ask"
    assert first.interlocutor_id == "tavern_runner"
    assert _binding(first)["status"] == "bound_canonical"
    second = _contract(by_number[2]["player_input"], session)
    assert second.operation == "ask"
    assert second.dimension == "source"
    assert second.interlocutor_id == "tavern_runner"
    assert _binding(second)["claim_binding"] == "unresolved"
    third = _contract(by_number[3]["player_input"], session)
    assert third.operation == "ask"
    assert third.interlocutor_id != "tavern_runner"
    assert _binding(third)["status"] == "bound_incidental"
    assert _binding(third)["label"] == "cloth merchant"
    fourth = _contract(by_number[4]["player_input"], session)
    assert fourth.operation == "inspect"
    assert "notice" in str(fourth.target_ref.id_or_text or "").lower()
    assert fourth.interlocutor_id != "tavern_runner"


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


def _player_text(user: str) -> str:
    try:
        payload = json.loads(user)
    except (TypeError, ValueError, json.JSONDecodeError):
        return user
    if isinstance(payload, dict):
        return str(payload.get("player_input") or payload.get("raw_player_input") or payload.get("raw_input") or user)
    return user


def test_raw_chat_stub_covers_incidental_binding_and_authority(chat, monkeypatch):
    calls = {"n": 0}

    def fake_gpt(messages, **kwargs):
        calls["n"] += 1
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        current = _player_text(user).lower()
        reason = str(kwargs.get("retry_reason") or "")
        if reason == "hard_invalid" or int(kwargs.get("retry_attempt") or 0) >= 1:
            return _gm_response('The porter says, "I cannot give you an hour that is settled here."')
        if "assassin" in current or "killed the duke" in current:
            return _gm_response("No one here can answer that from what is settled here.")
        if "who told you that" in current:
            return _gm_response('The speaker says, "I cannot name who told me."')
        if "official closing" in current:
            return _gm_response(f'The porter says, "{THIRD_BELL}"')
        if "heard about the patrols" in current:
            return _gm_response(f'The cloth merchant says, "{HEARD}"')
        if "cloth merchant" in current or "north road" in current:
            return _gm_response('The cloth merchant says, "A few travelers came through before the rain."')
        if "passing traveler" in current:
            return _gm_response('The traveler says, "The road is quiet."')
        if "tavern runner" in current or "stew" in current:
            return _gm_response('The tavern runner says, "I have not heard a particular account."')
        return _gm_response('The tavern runner says, "I cannot add to what is already settled."')

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)

    canonical = chat.post("/api/chat", json={"text": "I ask the tavern runner what the stew costs."}).json()
    canonical_contract = canonical["resolution"]["metadata"]["resolution_contract"]
    assert canonical_contract["operation"] == "ask"
    assert canonical_contract["interlocutor_id"] == "tavern_runner"
    assert canonical_contract["construction"]["entity_binding"]["status"] == "bound_canonical"

    source = chat.post("/api/chat", json={"text": "Who told you that?"}).json()
    source_contract = source["resolution"]["metadata"]["resolution_contract"]
    assert source_contract["operation"] == "ask"
    assert source_contract["dimension"] == "source"
    assert source_contract["construction"]["entity_binding"]["claim_binding"] == "unresolved"

    traveler = chat.post("/api/chat", json={"text": "I stop a passing traveler and ask if the road is quiet."}).json()
    traveler_contract = traveler["resolution"]["metadata"]["resolution_contract"]
    assert traveler_contract["operation"] == "ask"
    assert traveler_contract["interlocutor_id"] != "tavern_runner"
    assert traveler_contract["construction"]["entity_binding"]["status"] == "bound_incidental"
    assert "traveler" in traveler["gm_output"]["player_facing_text"].lower()

    merchant = chat.post(
        "/api/chat",
        json={"text": "I walk over to the cloth merchant and ask whether anyone has come through from the north road today."},
    ).json()
    merchant_contract = merchant["resolution"]["metadata"]["resolution_contract"]
    assert merchant_contract["operation"] == "ask"
    assert merchant_contract["interlocutor_id"] != "tavern_runner"
    assert merchant_contract["construction"]["entity_binding"]["status"] == "bound_incidental"
    assert "cloth merchant" in merchant["gm_output"]["player_facing_text"].lower()
    assert "tavern runner" not in merchant["gm_output"]["player_facing_text"].lower()

    rumor = chat.post("/api/chat", json={"text": "I ask the cloth merchant what he has heard about the patrols."}).json()
    assert HEARD.lower() in rumor["gm_output"]["player_facing_text"].lower()
    claimed = chat.post("/api/chat", json={"text": "Who told you that?"}).json()
    claimed_contract = claimed["resolution"]["metadata"]["resolution_contract"]
    assert claimed_contract["operation"] == "ask"
    assert claimed_contract["dimension"] == "source"
    assert claimed_contract["interlocutor_id"] == merchant_contract["interlocutor_id"]
    assert claimed_contract["construction"]["entity_binding"]["claim_binding"] == "bound"

    assassin = chat.post("/api/chat", json={"text": "I ask the assassin who killed the duke."}).json()
    assassin_contract = assassin["resolution"]["metadata"]["resolution_contract"]
    assert assassin_contract["operation"] == "ask"
    assert assassin_contract["construction"]["entity_binding"]["status"] == "rejected_consequential"
    assert assassin_contract["interlocutor_id"] != "tavern_runner"
    assert "duke" not in assassin["gm_output"]["player_facing_text"].lower()

    ruled = chat.post("/api/chat", json={"text": "I ask the porter what the official closing hour is."}).json()
    ruled_text = ruled["gm_output"]["player_facing_text"]
    assert "third bell" not in ruled_text.lower()
    assert ruled["gm_output"]["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert calls["n"] >= 2
