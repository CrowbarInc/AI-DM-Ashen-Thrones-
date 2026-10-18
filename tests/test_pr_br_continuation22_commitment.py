"""PR-BR C22: primary intent, commitment modality, unresolved addressee.

Deterministic. The stubbed /api/chat path does not call a paid model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.discourse_state import DISCOURSE_FOCUS_KEY
from game.immutable_valid_response import safe_nonresolution, semantic_equal, validate_generated_response
from game.intent_parser import parse_freeform_to_action, recover_actionable_explicit_world_action
from game.resolution_contract import construct_resolution_contract
from game.scene_destination_binding import resolve_authored_exit_from_player_travel
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads((ROOT / "data" / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
EXITS = SCENE["scene"]["exits"]
RUNNER = {
    "id": "tavern_runner",
    "type": "interlocutor",
    "label": "Tavern Runner",
    "aliases": ["runner", "tavern runner"],
    "source": "scene",
}
CAPTAIN = {
    "id": "guard_captain",
    "type": "interlocutor",
    "label": "Guard Captain",
    "aliases": ["captain", "guard", "guard captain"],
    "source": "scene",
}
SERJEANT = {
    "id": "gate_serjeant",
    "type": "interlocutor",
    "label": "Gate Serjeant",
    "aliases": ["serjeant", "guard", "guard serjeant"],
    "source": "scene",
}
CATALOG = [RUNNER, CAPTAIN]
H1 = (
    "I approach the tavern runner first, hoping to buy some hot stew and listen carefully "
    "to the whispered rumors he's offering, trying to learn more about the missing patrol "
    "and the overall mood among the crowd."
)
H2 = (
    "I thank the tavern runner and turn toward the muddy lane northwest of the crates, "
    "carefully stepping through the rain to inspect the footprints they mentioned. "
    "I look for any signs or clues nearby that might hint at what happened to the missing patrol "
    "before deciding whether to follow the road toward the old milestone."
)
H3 = (
    "I thank the tavern runner quietly, then turn toward the guard serjeant near the roster to ask "
    "about the missing patrol and the current state of affairs inside the gate. "
    "I observe the serjeant's demeanor carefully, looking for signs of stress or secrecy."
)
CAPTAIN_SPEECH = (
    '"I have no new information on the missing patrol," the guard captain replies in a steady voice.'
)
SERJEANT_SPEECH = '"The roster is all we have posted," the guard serjeant replies.'


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


def _contract(text, session=None, referents=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene=SCENE,
        canonical_referents=list(referents) if referents is not None else list(CATALOG),
    )


def _moved(text):
    action = parse_freeform_to_action(text, SCENE, session=_focus())
    if not isinstance(action, dict):
        return None
    if action.get("type") == "scene_transition":
        return action.get("target_scene_id")
    return None


def test_h1_listen_carefully_stays_a_social_ask():
    contract = _contract(H1)
    assert contract.operation == "ask"
    assert contract.interlocutor_id == "tavern_runner"
    assert contract.construction["commitment_status"] == "executed_now"
    assert contract.construction["primary_operation"] == "ask"
    assert "perceive" in contract.construction["secondary_operations"]
    assert "sound" not in contract.dimensions
    fallback = safe_nonresolution(contract.as_dict(), player_text=H1)
    assert "sound" not in fallback.lower()


def test_h2_inspection_does_not_take_the_milestone_exit():
    contract = _contract(H2)
    assert contract.operation == "inspect"
    assert contract.construction["commitment_status"] == "executed_now"
    assert resolve_authored_exit_from_player_travel(H2, EXITS) is None
    assert _moved(H2) is None
    bare = (
        "I thank the tavern runner and turn toward the muddy lane northwest of the crates, "
        "carefully stepping through the rain to inspect the footprints they mentioned."
    )
    assert resolve_authored_exit_from_player_travel(bare, EXITS) is None


def test_h3_unresolved_serjeant_blocks_the_captain():
    contract = _contract(H3)
    binding = contract.construction["entity_binding"]
    assert contract.operation == "ask"
    assert contract.interlocutor_id != "tavern_runner"
    assert contract.interlocutor_id != "guard_captain"
    assert binding["status"] in {"unresolved", "ambiguous"}
    assert binding["explicit_new_interlocutor"] is True
    assert "serjeant" in str(contract.construction["requested_addressee"]).lower()
    rejected = validate_generated_response(
        CAPTAIN_SPEECH,
        contract=contract.as_dict(),
        player_text=H3,
        referents=CATALOG,
    )
    assert rejected["hard_valid"] is False
    assert "wrong_interlocutor" in rejected["reasons"]
    allowed = validate_generated_response(
        SERJEANT_SPEECH,
        contract=contract.as_dict(),
        player_text=H3,
        referents=CATALOG,
    )
    assert allowed["hard_valid"] is True
    fallback = safe_nonresolution(contract.as_dict(), player_text=H3)
    assert "guard captain" not in fallback.lower()
    assert "sound" not in fallback.lower()


@pytest.mark.parametrize(
    ("text", "operation"),
    [
        ("I ask the runner what he heard and listen carefully.", "ask"),
        ("I listen carefully at the door.", "perceive"),
        ("I ask the guard what happened while watching his reaction.", "ask"),
        ("I watch the guard's reaction.", "perceive"),
        ("I walk to the merchant and ask about the patrol.", "ask"),
        ("I listen at the door.", "perceive"),
        ("I listen for footsteps.", "perceive"),
        ("I examine the footprints.", "inspect"),
        ("I smell the stew.", "perceive"),
    ],
)
def test_primary_intent_matrix(text, operation):
    contract = _contract(text)
    assert contract.operation == operation
    if operation == "ask":
        assert "perceive" == contract.operation or contract.operation == "ask"
    if operation == "perceive" and "listen" in text:
        assert contract.dimension == "sound"


def test_two_perception_intents_keep_the_sound_obligation():
    text = "I examine the lock and listen for movement behind the door."
    contract = _contract(text)
    assert contract.operation in {"inspect", "perceive"}
    assert "sound" in contract.dimensions
    assert contract.operation != "ask"


def test_committed_movement_still_reaches_the_authored_exit():
    text = "I follow the road toward the old milestone."
    contract = _contract(text)
    assert contract.construction["commitment_status"] == "executed_now"
    assert resolve_authored_exit_from_player_travel(text, EXITS) == "old_milestone"
    assert _moved(text) == "old_milestone"


@pytest.mark.parametrize(
    "text",
    [
        "If the tracks are fresh, I'll follow them toward the old milestone.",
        "I might follow the road toward the old milestone.",
        "I consider going to the old milestone.",
        "Would the road take me to the old milestone?",
        "I'll follow the road toward the old milestone after I finish here.",
        "I inspect the footprints before deciding whether to follow the road toward the old milestone.",
        "I inspect the footprints, then decide whether to follow the road toward the old milestone.",
    ],
)
def test_uncommitted_destination_mentions_do_not_move(text):
    assert resolve_authored_exit_from_player_travel(text, EXITS) is None
    assert _moved(text) is None


def test_conditional_and_hypothetical_are_not_executed_now():
    conditional = _contract("If the tracks are fresh, I'll follow them.")
    assert conditional.construction["commitment_status"] == "conditional"
    assert conditional.operation not in {"act", "follow"}
    hypothetical = _contract("Would the road take me to the old milestone?")
    assert hypothetical.construction["commitment_status"] == "hypothetical"
    assert hypothetical.operation == "ask"
    contemplated = _contract("I might follow the road.")
    assert contemplated.construction["commitment_status"] == "contemplated"
    later = _contract("Then I'll go to the inn.")
    assert later.construction["commitment_status"] == "intended_later"


def test_committed_sequence_is_not_treated_as_hypothetical():
    text = "I inspect the footprints, then follow them."
    contract = _contract(text)
    assert contract.operation == "inspect"
    assert contract.construction["commitment_status"] == "executed_now"
    assert "follow" in contract.raw_input
    assert _moved(text) is None


def test_conditional_open_does_not_fire_and_direct_open_does():
    session = _focus()
    closed = recover_actionable_explicit_world_action(
        "If necessary, I'll open the crate.",
        SCENE,
        session=session,
    )
    opened = recover_actionable_explicit_world_action(
        "I open the crate.",
        SCENE,
        session=session,
    )
    assert closed is None or (closed.get("metadata") or {}).get("physical_verb") != "open"
    assert opened is not None
    assert (opened.get("metadata") or {}).get("physical_verb") == "open"


def test_explicit_addressee_matrix():
    runner = _contract("I ask the tavern runner about the stew.")
    assert runner.interlocutor_id == "tavern_runner"
    assert runner.construction["addressee_binding_status"] == "bound_canonical"

    captain = _contract("I ask the guard captain about the patrol.")
    assert captain.interlocutor_id == "guard_captain"
    spoken = validate_generated_response(
        '"The notice is the whole of it," the guard captain replies.',
        contract=captain.as_dict(),
        player_text="I ask the guard captain about the patrol.",
        referents=CATALOG,
    )
    assert spoken["hard_valid"] is True

    guard = _contract("I ask the guard what the notice says.")
    assert guard.interlocutor_id == "guard_captain"

    ambiguous = _contract("I ask the guard about the patrol.", referents=[CAPTAIN, SERJEANT, RUNNER])
    assert ambiguous.interlocutor_id not in {"guard_captain", "gate_serjeant"}
    assert ambiguous.construction["entity_binding"]["status"] == "ambiguous"
    picked = validate_generated_response(
        CAPTAIN_SPEECH,
        contract=ambiguous.as_dict(),
        player_text="I ask the guard about the patrol.",
        referents=[CAPTAIN, SERJEANT, RUNNER],
    )
    assert picked["hard_valid"] is False
    assert "wrong_interlocutor" in picked["reasons"]

    inherited = _contract("What did he say about the patrol?")
    assert inherited.interlocutor_id == "tavern_runner"


def test_unresolved_addressee_does_not_inherit_the_runner():
    contract = _contract("I ask the guard serjeant about the patrol.")
    assert contract.interlocutor_id != "tavern_runner"
    assert contract.construction["entity_binding"]["status"] in {"unresolved", "ambiguous"}
    assert contract.construction["addressee_binding_status"] in {"unresolved", "ambiguous"}


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
    return contract


def test_raw_chat_stub_covers_commitment_and_addressee(chat, monkeypatch):
    calls = {"n": 0}

    def fake_gpt(messages, **kwargs):
        calls["n"] += 1
        blob = " ".join(
            str(message.get("content") or "")
            for message in messages
            if isinstance(message, dict) and message.get("role") == "user"
        ).lower()
        if "guard serjeant" in blob and "wrong speaker" not in blob and calls["n"] < 40:
            if "cannot be identified" in blob:
                return _gm_response("The person you addressed is not clearly in front of you.")
            return _gm_response(CAPTAIN_SPEECH)
        if "listen carefully at the door" in blob or "listen for footsteps" in blob or "listen at the door" in blob:
            return _gm_response("No further sound carries through from the far side.")
        if "watch the guard" in blob:
            return _gm_response("The guard's hands stay loose at his belt, and his eyes keep moving.")
        if "footprints" in blob or "examine the lock" in blob:
            return _gm_response("The footprints are shallow and already filling with rain.")
        if "open the crate" in blob and "if necessary" not in blob:
            return _gm_response("The crate's lid stays fast. Nothing inside is established.")
        if "tavern runner" in blob or "listen carefully" in blob:
            return _gm_response('The tavern runner says, "The notice is all the solid word I have."')
        if "guard captain" in blob:
            return _gm_response('"The notice is the whole of it," the guard captain replies.')
        return _gm_response("The gate stays as it is. Nothing further is established.")

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    cases = [
        ("I ask the tavern runner what he heard and listen carefully.", "ask", "frontier_gate"),
        ("I listen carefully at the door.", "perceive", "frontier_gate"),
        ("I ask the guard what happened while watching his reaction.", "ask", "frontier_gate"),
        ("I watch the guard's reaction.", "perceive", "frontier_gate"),
        (
            "I inspect the footprints before deciding whether to follow the road toward the old milestone.",
            "inspect",
            "frontier_gate",
        ),
        ("If the tracks are fresh, I'll follow them toward the old milestone.", None, "frontier_gate"),
        ("Would the road take me to the old milestone?", "ask", "frontier_gate"),
        ("I inspect the footprints, then follow them.", "inspect", "frontier_gate"),
        (H3, "ask", "frontier_gate"),
        ("I ask the guard serjeant where the patrol went.", "ask", "frontier_gate"),
        ("I ask the tavern runner whether the stew is hot.", "ask", "frontier_gate"),
        ("I follow the road toward the old milestone.", None, "old_milestone"),
    ]
    for text, operation, scene_id in cases:
        payload = chat.post("/api/chat", json={"text": text}).json()
        contract = _contract_of(payload)
        if operation:
            assert contract.get("operation") == operation, text
        assert payload["session"]["active_scene_id"] == scene_id, text
        visible = payload["gm_output"]["player_facing_text"]
        accepted = payload["gm_output"]["metadata"]["accepted_response"]["text"]
        assert semantic_equal(visible, accepted), text
        if "serjeant" in text.lower():
            assert "guard captain" not in visible.lower(), text
        construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
        assert construction.get("commitment_status"), text
