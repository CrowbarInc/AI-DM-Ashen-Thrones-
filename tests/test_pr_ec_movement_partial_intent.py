from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.pr_dq.world import COURTYARD_ID, GATE_ID, LANTERN_ID, STREET_ID
from game import storage
from game.api import chat
from game.conversational_orchestration import (
    ConversationalDecisionCategory,
    deterministic_conversational_decision,
)
from game.interaction_context import set_social_target
from game.models import ChatRequest
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution, _seed_pr_du_world

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_PATH = ROOT / "tests" / "fixtures" / "pr_ec_holdout_expressions.json"
DOCKS_ID = "exit_docks"
NORTH_GATE_ID = "exit_north_gate"
MARKET_GATE_ID = "exit_market_gate"
WALL_ID = "sealed_wall"
LOCK_ID = "iron_lock"

DEVELOPMENT_CASES = [
    ("I go to the docks.", "execute"),
    ("I make for the harbor.", "execute"),
    ("Let's head down to the waterfront.", "execute"),
    ("I leave the guard and walk toward the docks.", "execute"),
    ("Can I get to the docks from here?", "answer"),
    ("I was thinking about visiting the docks.", "answer"),
]


def _install_routes(tmp_path, monkeypatch, *, include_wall: bool = False) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    scene = storage.load_active_scene()
    exits = [
        {
            "id": DOCKS_ID,
            "label": "the docks",
            "aliases": ["docks", "harbor", "waterfront", "quay", "wharf", "pier", "landing"],
            "target_scene_id": STREET_ID,
        },
        {
            "id": NORTH_GATE_ID,
            "label": "northern gate",
            "aliases": ["north gate", "northern gate"],
            "target_scene_id": STREET_ID,
        },
        {
            "id": MARKET_GATE_ID,
            "label": "market gate",
            "aliases": ["market gate", "south gate"],
            "target_scene_id": STREET_ID,
        },
        {
            "id": GATE_ID,
            "label": "Courtyard gate",
            "aliases": ["courtyard gate"],
            "target_scene_id": STREET_ID,
        },
    ]
    if include_wall:
        exits.append(
            {
                "id": WALL_ID,
                "label": "sealed stone wall",
                "aliases": ["stone wall", "sealed stone wall"],
                "target_scene_id": "",
            }
        )
    scene["scene"]["exits"] = exits
    scene["scene"]["interactables"].append(
        {
            "id": LOCK_ID,
            "label": "iron lock",
            "aliases": ["lock", "the lock"],
            "reveals_clue": "The lock is rusted.",
        }
    )
    storage.save_scene(scene)


def _no_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "game.live_chat_interpretation.request_interpretation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("interpretation provider called")),
    )


def _narrate(monkeypatch, text: str = "You reach the docks.") -> None:
    def _gm(_messages):
        return {
            "player_facing_text": text,
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "pr_ec_narration_stub",
        }

    monkeypatch.setattr("game.api.call_gpt", _gm)


def _decision(text: str):
    scene = storage.load_active_scene()
    return deterministic_conversational_decision(
        player_text=text,
        scene=scene,
        world=storage.load_world(),
        session=storage.load_session(),
        log=storage.load_log(),
    )


@pytest.mark.parametrize(("text", "expected"), DEVELOPMENT_CASES, ids=[item[0] for item in DEVELOPMENT_CASES])
def test_pr_ec_development_movement_family(tmp_path, monkeypatch, text: str, expected: str) -> None:
    _install_routes(tmp_path, monkeypatch)
    decision = _decision(text)
    assert decision is not None
    if expected == "execute":
        assert decision.category == ConversationalDecisionCategory.EXECUTE
        assert decision.proposed_operation == "MOVE"
        assert decision.proposed_target == DOCKS_ID
        assert decision.requires_authoritative_execution is True
    else:
        assert decision.category != ConversationalDecisionCategory.EXECUTE
        assert decision.requires_authoritative_execution is False


def test_pr_ec_holdout_wording_is_not_hardcoded() -> None:
    source = (ROOT / "game" / "conversational_orchestration.py").read_text(encoding="utf-8")
    for row in json.loads(HOLDOUT_PATH.read_text(encoding="utf-8")):
        assert row["text"] not in source


@pytest.mark.parametrize("row", json.loads(HOLDOUT_PATH.read_text(encoding="utf-8")), ids=lambda row: row["id"])
def test_pr_ec_holdout_semantic_family(tmp_path, monkeypatch, row: dict) -> None:
    _install_routes(tmp_path, monkeypatch)
    decision = _decision(row["text"])
    assert decision is not None
    if row["expect"] == "execute":
        assert decision.category == ConversationalDecisionCategory.EXECUTE
        assert decision.proposed_operation == "MOVE"
        assert decision.requires_authoritative_execution is True
    elif row["expect"] == "clarify":
        assert decision.category == ConversationalDecisionCategory.CLARIFY
        assert decision.requires_authoritative_execution is False
    else:
        assert decision.category in {ConversationalDecisionCategory.ANSWER, ConversationalDecisionCategory.PLAN}
        assert decision.requires_authoritative_execution is False
        assert decision.proposed_operation is None


def test_pr_ec_direct_movement_uses_existing_resolver(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    _narrate(monkeypatch)

    data = chat(ChatRequest(text="I go to the docks.", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["action_id"] == DOCKS_ID
    assert data["resolution"]["target_scene_id"] == STREET_ID
    assert data["resolution"]["metadata"]["stored_interpretation"]["operation"] == "MOVE"
    assert storage.load_session()["active_scene_id"] == STREET_ID
    assert "pick" not in data["gm_output"]["player_facing_text"].lower()


def test_pr_ec_movement_question_does_not_move_or_advance_time(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="Can I reach the docks from here?", ui_mode="player"))

    after = storage.load_session()
    text = data["gm_output"]["player_facing_text"].lower()
    assert data["resolution"]["kind"] == "conversational_answer"
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["turn_counter"] == before["turn_counter"]
    assert after["clocks"] == before["clocks"]
    assert data["resolution"]["metadata"]["provider_calls"]["interpretation_requests"] == 0
    assert "you have not moved" in text
    assert "arrive" not in text
    assert "valid action" not in text


def test_pr_ec_tentative_movement_does_not_execute(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="I was thinking about visiting the docks.", ui_mode="player"))

    after = storage.load_session()
    assert data["resolution"]["metadata"]["resolver_invoked"] is False
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["turn_counter"] == before["turn_counter"]
    assert "nothing has been attempted" in data["gm_output"]["player_facing_text"].lower()


def test_pr_ec_incomplete_movement_clarifies_without_context_and_uses_focused_destination(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)

    unclear = chat(ChatRequest(text="I head out.", ui_mode="player"))
    assert unclear["resolution"]["kind"] == "conversational_clarify"
    assert unclear["gm_output"]["player_facing_text"] == "Where are you trying to go?"
    assert storage.load_session()["active_scene_id"] == COURTYARD_ID

    session = storage.load_session()
    session["conversational_context"]["focused_destination"] = {
        "exit_id": DOCKS_ID,
        "label": "the docks",
        "scene_id": COURTYARD_ID,
    }
    session["conversational_context"]["pending_clarification"] = None
    storage.save_session(session)
    _narrate(monkeypatch)

    moved = chat(ChatRequest(text="I start heading out.", ui_mode="player"))
    assert moved["resolution"]["action_id"] == DOCKS_ID
    assert storage.load_session()["active_scene_id"] == STREET_ID


def test_pr_ec_impossible_wall_stays_with_existing_authority(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch, include_wall=True)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="I walk through the sealed stone wall.", ui_mode="player"))

    after = storage.load_session()
    assert data["resolution"]["kind"] != "scene_transition"
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["turn_counter"] == before["turn_counter"]
    bridge = data["resolution"]["metadata"]["stored_interpretation_bridge"]
    assert bridge["reason"] == "exit_has_no_authored_destination"
    assert "stay where you are" in data["gm_output"]["player_facing_text"].lower()


def test_pr_ec_dialogue_to_movement_clears_talk_and_moves(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    session = storage.load_session()
    set_social_target(session, "sergeant_mara")
    storage.save_session(session)
    _no_provider(monkeypatch)
    _narrate(monkeypatch, "You reach the docks.")

    data = chat(ChatRequest(text="I thank the guard and head toward the docks.", ui_mode="player"))

    after = storage.load_session()
    assert data["resolution"]["action_id"] == DOCKS_ID
    assert after["active_scene_id"] == STREET_ID
    assert after["interaction_context"]["active_interaction_target_id"] is None
    assert "arrive" in data["gm_output"]["player_facing_text"].lower()


def test_pr_ec_compound_actions_are_named_and_not_executed(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="I put away my sword and open the door.", ui_mode="player"))

    text = data["gm_output"]["player_facing_text"].lower()
    assert data["resolution"]["kind"] == "conversational_clarify"
    assert "sword" in text and "door" in text
    assert "i have not done any of them yet" in text
    assert storage.load_session()["active_scene_id"] == before["active_scene_id"]
    assert storage.load_session()["turn_counter"] == before["turn_counter"]


def test_pr_ec_dependent_sequence_does_not_narrate_the_second_step(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)

    first = chat(ChatRequest(text="I examine the lock, then try to pick it.", ui_mode="player"))
    text = first["gm_output"]["player_facing_text"].lower()
    assert first["resolution"]["kind"] == "conversational_clarify"
    assert "examine the lock" in text
    assert "pick" in text
    assert "should i do the first one now" in text
    assert storage.load_session()["active_scene_id"] == COURTYARD_ID

    _narrate(monkeypatch, "You examine the iron lock. It is rusted.")
    second = chat(ChatRequest(text="yes", ui_mode="player"))
    assert second["resolution"]["action_id"] == LOCK_ID
    assert "pick" not in second["gm_output"]["player_facing_text"].lower()
    pending = storage.load_session()["conversational_context"]["pending_clarification"]
    assert pending["steps"][0]["operation"] == "OTHER"
    assert "pick" in pending["steps"][0]["text"]


def test_pr_ec_hypothetical_action_does_not_mutate(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="What would happen if I opened the door?", ui_mode="player"))

    after = storage.load_session()
    text = data["gm_output"]["player_facing_text"].lower()
    assert "can't say what would happen" in text
    assert "opened the door" not in text or "nothing has been attempted" in text
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["clocks"] == before["clocks"]
    assert data["resolution"]["metadata"]["provider_calls"]["interpretation_requests"] == 0


def test_pr_ec_ambiguous_destination_then_continuation(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)

    clarify = chat(ChatRequest(text="I go to the gate.", ui_mode="player"))
    assert clarify["resolution"]["kind"] == "conversational_clarify"
    assert "northern gate" in clarify["gm_output"]["player_facing_text"].lower()
    assert "market gate" in clarify["gm_output"]["player_facing_text"].lower()
    assert storage.load_session()["active_scene_id"] == COURTYARD_ID

    _narrate(monkeypatch, "You reach the northern gate road.")
    moved = chat(ChatRequest(text="the northern gate", ui_mode="player"))
    assert moved["resolution"]["action_id"] == NORTH_GATE_ID
    assert storage.load_session()["active_scene_id"] == STREET_ID
    assert storage.load_session()["conversational_context"]["pending_clarification"] is None


def test_pr_ec_pending_destination_survives_save_and_load(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)

    chat(ChatRequest(text="I leave.", ui_mode="player"))
    raw = storage.SESSION_PATH.read_text(encoding="utf-8")
    storage.SESSION_PATH.write_text(raw, encoding="utf-8")
    reloaded = storage.load_session()
    assert reloaded["conversational_context"]["pending_clarification"]["kind"] == "missing_destination"
    assert reloaded["turn_counter"] == 0

    _narrate(monkeypatch)
    moved = chat(ChatRequest(text="the docks", ui_mode="player"))
    assert moved["resolution"]["action_id"] == DOCKS_ID
    assert storage.load_session()["turn_counter"] == 1
    assert storage.load_session()["conversational_context"]["pending_clarification"] is None


def test_pr_ec_ordinary_inspection_still_reaches_existing_resolver(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    assert _decision("I examine the courtyard lantern.") is None
    payload = {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "player_intent": {"summary": "Inspect the lantern."},
        "action_components": [
            {"operation_class": "INSPECT", "target_ref": LANTERN_ID, "description": "Inspect the lantern."}
        ],
        "references": {"resolved_references": [], "unresolved_references": []},
    }
    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_args: payload)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    data = chat(ChatRequest(text="I examine the courtyard lantern.", ui_mode="player"))

    assert data["resolution"]["action_id"] == LANTERN_ID
    assert storage.load_session()["active_scene_id"] == COURTYARD_ID
    assert storage.load_session()["turn_counter"] == 1


def test_pr_ec_return_uses_previous_visited_scene(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    scene = storage.load_active_scene()
    scene["scene"]["exits"] = [
        {
            "id": "exit_tavern",
            "label": "the tavern",
            "aliases": ["tavern"],
            "target_scene_id": STREET_ID,
        }
    ]
    storage.save_scene(scene)
    session = storage.load_session()
    session["visited_scene_ids"] = [STREET_ID, COURTYARD_ID]
    storage.save_session(session)
    _no_provider(monkeypatch)
    _narrate(monkeypatch, "You return to the tavern.")

    data = chat(ChatRequest(text="I turn around and go back.", ui_mode="player"))

    assert data["resolution"]["action_id"] == "exit_tavern"
    assert storage.load_session()["active_scene_id"] == STREET_ID


def test_pr_ec_unknown_destination_is_not_canonicalized(tmp_path, monkeypatch) -> None:
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch)
    before = storage.load_session()

    data = chat(ChatRequest(text="I go to the moon tavern.", ui_mode="player"))

    after = storage.load_session()
    assert data["resolution"]["kind"] == "conversational_decline"
    assert after["active_scene_id"] == before["active_scene_id"]
    assert "not an established destination" in data["gm_output"]["player_facing_text"].lower()
    assert "valid action" not in data["gm_output"]["player_facing_text"].lower()
