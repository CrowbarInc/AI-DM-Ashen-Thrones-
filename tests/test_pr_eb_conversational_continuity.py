from __future__ import annotations

import copy

import pytest

from experiments.pr_dq.world import LANTERN_ID, MARA_ID
from game import storage
from game.api import chat
from game.interaction_context import set_social_target
from game.models import ChatRequest
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution, _seed_pr_du_world

pytestmark = pytest.mark.unit


def _activate_mara() -> None:
    session = storage.load_session()
    set_social_target(session, MARA_ID)
    storage.save_session(session)


def test_pr_eb_active_npc_followup_routes_to_existing_social_resolver(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    _activate_mara()
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
    monkeypatch.setattr(
        "game.live_chat_interpretation.request_interpretation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("interpretation provider called")),
    )

    data = chat(ChatRequest(text="Which captain?", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["kind"] == "question"
    assert data["resolution"]["social"]["npc_id"] == MARA_ID
    assert data["resolution"]["metadata"]["stored_interpretation"]["operation"] == "ASK"
    assert storage.load_session()["turn_counter"] == 1


def test_pr_eb_conversation_exit_clears_active_interlocutor_without_world_mutation(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    _activate_mara()
    before_world = copy.deepcopy(storage.load_world())
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
    )

    data = chat(ChatRequest(text="That's enough for now.", ui_mode="player"))

    assert data["resolution"]["kind"] == "conversational_answer"
    session = storage.load_session()
    ctx = session["interaction_context"]
    assert ctx["active_interaction_target_id"] is None
    assert ctx["active_interaction_kind"] is None
    assert storage.load_world() == before_world


def test_pr_eb_ambiguous_pronoun_inspection_resumes_after_clarification(tmp_path, monkeypatch) -> None:
    _seed_pr_du_world(tmp_path, monkeypatch)
    scene = storage.load_active_scene()
    scene["scene"]["interactables"].append(
        {
            "id": "courtyard-shield",
            "label": "weathered shield",
            "aliases": ["shield"],
            "reveals_clue": "Old paint marks the shield.",
        }
    )
    storage.save_scene(scene)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    clarify = chat(ChatRequest(text="I examine it.", ui_mode="player"))

    assert clarify["resolution"]["kind"] == "conversational_clarify"
    assert "lantern" in clarify["gm_output"]["player_facing_text"].lower()
    assert "weathered shield" in clarify["gm_output"]["player_facing_text"].lower()
    pending = storage.load_session()["conversational_context"]["pending_clarification"]
    assert pending["operation"] == "INSPECT"

    resolved = chat(ChatRequest(text="the lantern", ui_mode="player"))

    assert resolved["ok"] is True
    assert resolved["resolution"]["kind"] in {"investigate", "observe"}
    assert resolved["resolution"]["action_id"] == LANTERN_ID
    assert storage.load_session()["conversational_context"]["pending_clarification"] is None
