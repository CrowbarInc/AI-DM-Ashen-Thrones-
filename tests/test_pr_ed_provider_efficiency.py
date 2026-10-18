"""PR-ED provider efficiency: duplicate prompt fields, narration skips, retry stops."""

from __future__ import annotations

import copy

import pytest

from experiments.pr_dq.world import COURTYARD_ID, GATE_ID, MARA_ID, STREET_ID, build_disposable_world
from game import storage
from game.api import chat, deterministic_provider_skip_line, narration_retry_should_stop
from game.gm import omit_duplicate_turn_packet_policy
from game.models import ChatRequest
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

pytestmark = pytest.mark.unit


def _seed(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)
    built = build_disposable_world()
    built["scenes"][COURTYARD_ID]["scene"]["exits"] = [
        {
            "id": GATE_ID,
            "label": "courtyard gate",
            "aliases": ["gate", "the gate", "courtyard gate"],
            "target_scene_id": STREET_ID,
        }
    ]
    session = copy.deepcopy(built["session"])
    session.setdefault("scene_state", {})["active_scene_id"] = COURTYARD_ID
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, built["world"])
    storage._save_json(storage.CHARACTER_PATH, built["character"])
    storage._save_json(storage.COMBAT_PATH, built["combat"])
    storage._save_json(storage.CONDITIONS_PATH, {"conditions": []})
    storage._save_json(storage.CAMPAIGN_PATH, {"title": "PR-ED", "premise": "", "tone": "", "gm_guidance": []})
    for scene_id, envelope in built["scenes"].items():
        storage._save_json(storage.scene_path(scene_id), envelope)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_duplicate_turn_packet_policy_is_omitted_without_mutating_input() -> None:
    policy = {"answer_completeness": {"must": True}, "tone_escalation": {"max": "firm"}}
    payload = {
        "response_policy": policy,
        "turn_packet": {
            "version": 1,
            "response_policy": dict(policy),
            "contracts": {"answer_completeness": {"must": True}, "route_only": {"id": "keep"}},
        },
    }
    original_packet = copy.deepcopy(payload["turn_packet"])
    projected = omit_duplicate_turn_packet_policy(payload)
    assert "response_policy" not in projected["turn_packet"]
    assert projected["turn_packet"]["contracts"] == {"route_only": {"id": "keep"}}
    assert payload["turn_packet"] == original_packet
    assert projected["response_policy"] == policy


def test_unequal_turn_packet_policy_stays() -> None:
    payload = {
        "response_policy": {"answer_completeness": {"must": True}},
        "turn_packet": {"response_policy": {"answer_completeness": {"must": False}}},
    }
    assert omit_duplicate_turn_packet_policy(payload)["turn_packet"]["response_policy"]["answer_completeness"]["must"] is False


def test_narration_retry_stops_for_unsent_or_identical_output() -> None:
    assert narration_retry_should_stop(
        provider_not_sent=True, retry_attempt=0, previous_text="", current_text="The gate is shut."
    )
    assert narration_retry_should_stop(
        provider_not_sent=False,
        retry_attempt=1,
        previous_text="The gate is shut.",
        current_text="The gate is shut.",
    )
    assert not narration_retry_should_stop(
        provider_not_sent=False,
        retry_attempt=0,
        previous_text="",
        current_text="The gate is shut.",
    )
    assert not narration_retry_should_stop(
        provider_not_sent=False,
        retry_attempt=1,
        previous_text="The gate is shut.",
        current_text="The gate opens onto the street.",
    )


def test_completed_move_skips_provider_and_keeps_resolver_arrival(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch)
    calls = {"n": 0}

    def _boom(*_args, **_kwargs):
        calls["n"] += 1
        return {
            "player_facing_text": "A invented watchtower appears beyond the gate.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
        }

    monkeypatch.setattr("game.api.call_gpt", _boom)
    monkeypatch.setattr("game.gm.call_gpt", _boom)
    before = storage.load_session()
    response = chat(ChatRequest(text="I go through the courtyard gate."))
    after = storage.load_session()
    text = response["gm_output"]["player_facing_text"]
    resolution = response["resolution"]
    assert calls["n"] == 0
    assert resolution["kind"] == "scene_transition"
    assert resolution["resolved_transition"] is True
    assert resolution["target_scene_id"] == STREET_ID
    assert "watchtower" not in text.casefold()
    assert "waystation street" in text.casefold()
    assert after["scene_state"]["active_scene_id"] == STREET_ID
    assert before["scene_state"]["active_scene_id"] == COURTYARD_ID
    performance = (resolution.get("metadata") or {}).get("performance") or {}
    assert performance.get("provider_call_count") == 0
    assert performance.get("provider_narration_skipped") is True
    assert performance.get("successful") is True


def test_authorized_dialogue_skips_provider_restatement(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch)
    calls = {"n": 0}

    def _reply(*_args, **_kwargs):
        calls["n"] += 1
        return {
            "player_facing_text": 'Sergeant Mara says, "The street beyond the gate is the north road."',
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
        }

    monkeypatch.setattr("game.api.call_gpt", _reply)
    monkeypatch.setattr("game.gm.call_gpt", _reply)
    response = chat(ChatRequest(text="I ask Sergeant Mara about the road beyond the gate."))
    text = response["gm_output"]["player_facing_text"]
    assert calls["n"] == 0
    accepted = response["gm_output"]["metadata"]["accepted_response"]
    assert accepted["speech_adoption"] == "AUTHORIZED_HOST_SPEECH"
    assert accepted["text"] == text
    assert storage.load_session()["scene_state"]["active_scene_id"] == COURTYARD_ID
    assert "mara" in text.casefold() or "north road" in text.casefold()


def test_context_question_then_move_then_followup_stays_grounded(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_args, **_kwargs: {
            "player_facing_text": "unused",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
        },
    )
    first = chat(ChatRequest(text="Where are we?"))
    assert "courtyard" in first["gm_output"]["player_facing_text"].casefold()
    assert first["resolution"]["metadata"]["provider_calls"]["narration_requests"] == 0
    moved = chat(ChatRequest(text="I go through the courtyard gate."))
    assert moved["resolution"]["target_scene_id"] == STREET_ID
    follow = chat(ChatRequest(text="Where are we?"))
    assert "street" in follow["gm_output"]["player_facing_text"].casefold()
    assert MARA_ID


def test_local_observation_skip_does_not_require_a_provider(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch)
    skipped = deterministic_provider_skip_line(
        resolution={"kind": "observe", "metadata": {"parser_lane": "local_observation_question"}},
        scene=storage.load_active_scene(),
        world=storage.load_world(),
        session=storage.load_session(),
        player_text="What do I see?",
    )
    assert skipped is not None
    assert skipped[1] == "local_observation"
    assert skipped[0]
