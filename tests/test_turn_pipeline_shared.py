"""Shared turn-pipeline tests for /api/action and /api/chat.

These tests verify both endpoints exercise the same resolved-turn orchestration.

Per-test ``# feature: ...`` comments tag ownership for ``tools/test_audit.py``:
routing, retry, fallback, social, continuity, clues, leads, emission, legality.

Parametrized blocks (same setup + assertion shape): dialogue-lock prompt variants;
OOC adjudication without GPT; action vs chat runtime mutation before prompt build.
Table-style dialogue-lock routing (pure ``choose_interaction_route``) lives in
``test_dialogue_routing_lock.py``; this module keeps HTTP pipeline locks only.
Explicit multi-turn / retry / emission-gate bug locks stay non-parametrized.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.prompt_context import NO_VALIDATOR_VOICE_RULE

pytestmark = pytest.mark.integration

FAKE_GPT_RESPONSE = {
    "player_facing_text": "[Narration]",
    "tags": [],
    "scene_update": None,
    "activate_scene_id": None,
    "new_scene_draft": None,
    "world_updates": None,
    "suggested_action": None,
    "debug_notes": "",
}


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _seed_shared_world(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)

    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate", "reveals_clue": "desk_clue"},
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "desk_clue", "text": "A map indicates patrol locations."},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _gm_response(text: str, *, tags=None, debug_notes: str = ""):
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def _seed_runner_dialogue_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "They were seen near the east lanes.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)


def _assert_concrete_pressure(text: str) -> None:
    low = str(text or "").lower()
    assert any(
        phrase in low
        for phrase in (
            "\"",
            "cuts through the crowd",
            "stops at your shoulder",
            "comes straight to you",
            "squares up to you",
            "breaks the silence first",
            "if you're moving on this, move now",
            "question the runner",
            "work the notice",
            "east-road trail",
            "east road",
            "ask me now",
        )
    )


# feature: social, routing
def test_action_and_chat_social_use_equivalent_shared_turn_logic(tmp_path, monkeypatch):
    social_action = {
        "id": "question-runner",
        "label": "Talk to Tavern Runner",
        "type": "question",
        "prompt": "I talk to Tavern Runner.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }

    def _seed_and_add_runner():
        _seed_shared_world(tmp_path, monkeypatch)
        world = storage.load_world()
        world["npcs"] = [
            {
                "id": "runner",
                "name": "Tavern Runner",
                "location": "scene_investigate",
                "topics": [{"id": "gate_rumor", "text": "The gate closes at dusk.", "clue_id": "gate_rumor"}],
            }
        ]
        storage._save_json(storage.WORLD_PATH, world)

    _seed_and_add_runner()
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        action_resp = client.post(
            "/api/action",
            json={"action_type": "social", "intent": "I talk to Tavern Runner.", "social_action": social_action},
        )
    assert action_resp.status_code == 200
    action_data = action_resp.json()

    _seed_and_add_runner()
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        chat_resp = client.post("/api/chat", json={"text": "I talk to Tavern Runner."})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()

    assert action_data["ok"] is True
    assert chat_data["ok"] is True
    assert action_data["resolution"]["kind"] == "question"
    assert chat_data["resolution"]["kind"] == "question"
    assert action_data["resolution"]["requires_check"] is False
    assert chat_data["resolution"]["requires_check"] is False
    assert action_data["resolution"].get("check_request") is None
    assert chat_data["resolution"].get("check_request") is None
    assert action_data["resolution"]["social"]["npc_id"] == "runner"
    assert chat_data["resolution"]["social"]["npc_id"] == "runner"
    assert action_data["resolution"]["discovered_clues"] == chat_data["resolution"]["discovered_clues"]
    action_ctx = action_data.get("session", {}).get("interaction_context", {})
    chat_ctx = chat_data.get("session", {}).get("interaction_context", {})
    assert action_ctx.get("active_interaction_target_id") == "runner"
    assert chat_ctx.get("active_interaction_target_id") == "runner"
    assert action_ctx.get("active_interaction_kind") == "social"
    assert chat_ctx.get("active_interaction_kind") == "social"
    assert action_ctx.get("interaction_mode") == "social"
    assert chat_ctx.get("interaction_mode") == "social"
    assert action_ctx.get("engagement_level") == "engaged"
    assert chat_ctx.get("engagement_level") == "engaged"


# feature: clues
def test_action_and_chat_investigate_both_mark_runtime_discovery_memory(tmp_path, monkeypatch):
    explore_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }

    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        action_resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    action_rt = action_data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})

    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: explore_action)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        chat_resp = client.post("/api/chat", json={"text": "I investigate the desk."})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    chat_rt = chat_data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})

    assert action_data["resolution"]["kind"] == "discover_clue"
    assert chat_data["resolution"]["kind"] == "discover_clue"
    assert "A map indicates patrol locations." in (action_rt.get("discovered_clues") or [])
    assert "A map indicates patrol locations." in (chat_rt.get("discovered_clues") or [])
    # Ensure both endpoints mark the action id for discovery-memory relabeling.
    assert "inv-desk" in (action_rt.get("searched_targets") or [])
    assert "inv-desk" in (chat_rt.get("searched_targets") or [])


# feature: fallback
def test_chat_fallback_preserves_endpoint_specific_no_resolution_shape(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "hello there"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data.get("resolution") is None
    assert "gm_output" in data


# feature: retry, legality
def test_chat_targeted_retry_validator_voice_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Based on what's established, we can determine very little here.")
        return _gm_response("Rain beads on the gate stones while Captain Veyra watches the refugee line.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Describe the gate."})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_messages = captured_inputs[1]
    retry_tail = retry_messages[-1]["content"]
    assert "Retry target: validator_voice." in retry_tail
    assert "unresolved_question" not in retry_tail
    low = (data.get("gm_output") or {}).get("player_facing_text", "").lower()
    assert "based on what's established" not in low
    assert "we can determine" not in low
    assert "retry_strategy:selected=validator_voice" in ((data.get("gm_output") or {}).get("debug_notes") or "")


# feature: legality
def test_chat_prompt_carries_no_validator_voice_policy(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        return _gm_response("Rain beads on the gate stones while Captain Veyra watches the refugee line.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Describe the gate."})

    assert resp.status_code == 200
    assert len(captured_inputs) == 1
    system_prompt = captured_inputs[0][0]["content"]
    payload = json.loads(captured_inputs[0][1]["content"])
    instructions = " ".join(payload.get("instructions", []))
    assert NO_VALIDATOR_VOICE_RULE in system_prompt
    assert NO_VALIDATOR_VOICE_RULE in instructions
    assert payload["response_policy"]["no_validator_voice"]["enabled"] is True
    assert payload["response_policy"]["no_validator_voice"]["applies_to"] == "standard_narration"


# feature: leads
def test_chat_persists_recent_contextual_leads_from_gm_reply(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "Lady Misia waits near the tavern entrance while nearby guards keep glancing back to the missing patrol notice."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who should I watch here?"})

    assert resp.status_code == 200
    data = resp.json()
    rt = data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})
    recent = rt.get("recent_contextual_leads") or []
    assert any(entry.get("subject") == "Lady Misia" and entry.get("position") == "near the tavern entrance" for entry in recent)
    assert any("missing patrol" in str(entry.get("subject") or "").lower() for entry in recent)


# feature: fallback, leads
def test_chat_known_follow_up_bypasses_uncertainty_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "lady-misia-near-the-tavern-entrance",
            "kind": "recent_named_figure",
            "subject": "Lady Misia",
            "position": "near the tavern entrance",
            "named": True,
            "positioned": True,
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Captain Veyra folds her arms and watches the road."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where do I find that person?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_output = data.get("gm_output") or {}
    assert (gm_output.get("player_facing_text") or "").startswith("Lady Misia is near the tavern entrance.")
    assert "known_fact_guard" in (gm_output.get("tags") or [])
    assert not any(str(tag).startswith("uncertainty:") for tag in (gm_output.get("tags") or []))
    assert "known_fact_guard:recent_dialogue_continuity" in (gm_output.get("debug_notes") or "")


# feature: retry, legality
def test_chat_targeted_retry_unresolved_question_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Captain Veyra folds her arms and watches the road.")
        return _gm_response(
            "The report is usually copied to the notice board before dusk, though no one here will swear the last sheet is still hanging there. "
            "Best lead: read the posted notices and ask Captain Veyra who took the last copy."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where is the missing patrol report?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: unresolved_question." in retry_tail
    assert "validator_voice" not in retry_tail
    assert "Sentence one MUST directly answer the exact player question." in retry_tail
    assert "Do not begin with atmosphere, scene summary, or recap." in retry_tail
    assert "No advisory phrasing" in retry_tail
    low = (data.get("gm_output") or {}).get("player_facing_text", "").lower()
    assert "i can't answer" not in low
    assert "answer the player" not in low
    assert low.startswith("the report is")
    assert "retry_strategy:selected=unresolved_question" in ((data.get("gm_output") or {}).get("debug_notes") or "")


# feature: retry
def test_chat_targeted_retry_prefers_highest_priority_failure_first(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("I can't answer that. Based on what's established, we can determine very little here.")
        return _gm_response(
            "No one here has pinned the report to one locked drawer, but Captain Veyra says the gate board carried the last official notice before dusk. "
            "Best lead: check the board, then press her on who removed the fresh copy."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where is the missing patrol report?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: unresolved_question." in retry_tail
    assert "Retry target: validator_voice." not in retry_tail
    low = (data.get("gm_output") or {}).get("player_facing_text", "").lower()
    assert "i can't answer" not in low
    assert "based on what's established" not in low
    assert "retry_strategy:selected=unresolved_question" in ((data.get("gm_output") or {}).get("debug_notes") or "")


# feature: retry, fallback
def test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Rain rolls over the checkpoint and the crowd shifts under dripping banners.")
        return _gm_response("The checkpoint feels tense and crowded as boots splash through mud.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where are we?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    gm_output = data.get("gm_output") or {}
    text = (gm_output.get("player_facing_text") or "").lower()
    assert text.startswith("you are in")
    assert "checkpoint feels tense" not in text
    assert "question_retry_fallback" in (gm_output.get("tags") or [])
    assert "known_fact_guard" in (gm_output.get("tags") or [])
    dbg = gm_output.get("debug_notes") or ""
    assert "retry_strategy:selected=unresolved_question" in dbg
    assert "retry_fallback:unresolved_question:known_fact_guard:current_scene_state" in dbg


# feature: retry, fallback
def test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Rain rattles over the shutters while everyone keeps their own counsel.")
        return _gm_response("Fog hangs low by the gate and no one steps forward first.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    gm_output = data.get("gm_output") or {}
    text = gm_output.get("player_facing_text") or ""
    low = text.lower()
    assert "fog hangs low" not in low
    assert "tavern runner" in low
    assert "question_retry_fallback" in (gm_output.get("tags") or [])
    assert "retry_fallback:unresolved_question" in (gm_output.get("debug_notes") or "")
    assert "retry_strategy:selected=unresolved_question" in (gm_output.get("debug_notes") or "")


# feature: retry
def test_chat_targeted_retry_scene_stall_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["momentum_exchanges_since"] = 2
    scene_runtime["momentum_next_due_in"] = 3
    storage._save_json(storage.SESSION_PATH, session)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Captain Veyra studies you in silence.")
        return _gm_response(
            "A runner splashes up from the road with a torn dispatch and thrusts it toward Captain Veyra. "
            "\"East road, half an hour old,\" he pants, giving you a fresh trail to follow.",
            tags=["scene_momentum:new_information"],
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I wait."})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: scene_stall." in retry_tail
    assert "validator_voice" not in retry_tail
    low = (data.get("gm_output") or {}).get("player_facing_text", "").lower()
    assert "answer the player" not in low
    assert "rule priority" not in low
    assert "retry_strategy:selected=scene_stall" in ((data.get("gm_output") or {}).get("debug_notes") or "")


# feature: social, continuity
def test_chat_single_wait_in_tense_scene_forces_interaction_pressure(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    scene = storage.load_scene("scene_investigate")
    scene["scene"]["visible_facts"] = [
        "Guards keep glancing at a missing patrol notice beside the checkpoint.",
        "A tavern runner lingers under an awning, selling rumors for coin.",
    ]
    storage.save_scene(scene)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Rain beads on the checkpoint while nobody moves first."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I wait."})

    assert resp.status_code == 200
    data = resp.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    _assert_concrete_pressure(text)
    assert "passive_scene_pressure" in ((data.get("gm_output") or {}).get("tags") or [])


# feature: social
def test_chat_repeated_passive_actions_do_not_stall_into_atmosphere(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    scene = storage.load_scene("scene_investigate")
    scene["scene"]["visible_facts"] = [
        "A guard leans near the checkpoint, watching the road.",
        "A missing patrol notice curls in the damp beside him.",
    ]
    storage.save_scene(scene)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The damp air hangs over the gate as everyone watches everyone else."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "I wait."})
        second = client.post("/api/chat", json={"text": "I hold position and watch."})

    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    _assert_concrete_pressure(text)
    debug_notes = (((data.get("gm_output") or {}).get("debug_notes")) or "")
    assert "passive_scene_pressure:" in debug_notes
    assert "streak=2" in debug_notes


# feature: social
def test_chat_passive_scene_prefers_already_introduced_suspicious_figure(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The square stays hushed except for the scrape of boots on wet stone."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I remain silent and observe."})

    assert resp.status_code == 200
    data = resp.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    assert "the tattered man" in text.lower()
    _assert_concrete_pressure(text)
    assert "passive_scene_pressure:lead_figure" in (((data.get("gm_output") or {}).get("debug_notes")) or "")


# feature: emission
def test_chat_roll_requirement_question_routes_to_adjudication_without_gpt(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is Sleight of Hand needed?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert adjudication.get("category") == "roll_requirement_query"
    assert adjudication.get("answer_type") == "check_required"
    assert (data.get("resolution") or {}).get("requires_check") is True
    check_request = (data.get("resolution") or {}).get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert isinstance(check_request.get("player_prompt"), str)
    assert "adjudication_query" in (data.get("gm_output") or {}).get("tags", [])


# feature: routing, social
def test_chat_active_target_location_question_routes_to_social_exchange(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where can I find them?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param(
            "Runner, do you know where can I find those figures?",
            id="runner_direct_address",
        ),
        pytest.param("Who attacked them?", id="pronoun_who_attacked"),
        pytest.param("What are they planning?", id="pronoun_what_planning"),
        pytest.param("Who saw this happen?", id="who_saw"),
    ],
)
def test_chat_dialogue_lock_routes_npc_directed_question_regressions(tmp_path, monkeypatch, user_text):
    """Pipeline lock: directed / pronominal questions stay social_exchange on active runner."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    # GM legality for procedural phrasing is covered by sanitizer / emission-gate tests below.


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param("Well? What should I do next?", id="what_next_well"),
        pytest.param("So? What's the next step?", id="next_step_so"),
        pytest.param("Where does this lead?", id="where_lead"),
    ],
)
def test_chat_dialogue_lock_routes_ambiguous_next_step_questions_to_active_npc(
    tmp_path, monkeypatch, user_text
):
    """Meta / ambiguous follow-ups stay dialogue lane (question or social_probe), not adjudication."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"question", "social_probe"}
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: social
def test_chat_repeated_social_questions_keep_npc_uncertainty_voice(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Rain rattles over the shutters while the crowd churns."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        prompts = ["Who attacked them?", "Who is behind it?"]
        for prompt in prompts:
            resp = client.post("/api/chat", json={"text": prompt})
            assert resp.status_code == 200
            data = resp.json()
            text = ((data.get("gm_output") or {}).get("player_facing_text") or "")
            low = text.lower()
            assert "tavern runner" in low
            assert '"' in text
            assert "resolve that procedurally" not in low
            assert "state exactly what you do" not in low


# feature: social
def test_chat_repeated_topic_questions_skip_policy_topic_pressure_for_strict_social(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    stale = _gm_response(
        "The runner rubs his neck. Rumor says the crossroads turned ugly, but no one can name the culprits yet "
        "and people keep repeating the same whispers without anything solid."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: stale)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.gm.resolve_known_fact_before_uncertainty", lambda *_args, **_kwargs: None)
        m.setattr(
            "game.gm.question_resolution_rule_check",
            lambda **_kwargs: {"applies": False, "ok": True, "reasons": []},
        )
        m.setattr("game.gm.enforce_question_resolution_rule", lambda gm, **_kwargs: gm)
        client = TestClient(app)
        prompts = [
            "Who is behind the crossroads attack?",
            "Who is really behind it?",
            "Who ordered it?",
            "Who funds them?",
        ]
        for idx, prompt in enumerate(prompts, start=1):
            resp = client.post("/api/chat", json={"text": prompt})
            assert resp.status_code == 200
            data = resp.json()
            gm_output = data.get("gm_output") or {}
            tags = gm_output.get("tags") or []
            if idx >= 4:
                assert "topic_pressure_escalation" not in tags
                assert not any(str(tag).startswith("scene_momentum:") for tag in tags)


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param("I lean in and ask quietly who saw it.", id="lean_in_quiet_question"),
        pytest.param("I scan the crowd while asking who saw it.", id="scan_crowd_question"),
    ],
)
def test_chat_dialogue_lock_mixed_questioning_keeps_dialogue_lane(tmp_path, monkeypatch, user_text):
    """Action-flavored wording with a question still routes to dialogue, not world/adjudication."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"question", "social_probe"}
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing
def test_chat_dialogue_lock_does_not_override_forceful_world_action(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I follow the runner."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") != "question"
    assert resolution.get("kind") != "social_probe"
    assert resolution.get("kind") != "adjudication_query"


# feature: routing, social
def test_chat_social_pressure_line_prefers_dialogue_over_adjudication(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Footman? I require an audience."})

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("resolution") is None
    assert (data.get("gm_output") or {}).get("player_facing_text") == FAKE_GPT_RESPONSE["player_facing_text"]
    assert "adjudication_query" not in ((data.get("gm_output") or {}).get("tags") or [])


# feature: routing, social
def test_chat_active_target_direct_command_routes_to_social_exchange(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "They were seen near the east lanes.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Tell me plainly."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "social_probe"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing, emission
@pytest.mark.parametrize(
    "user_text, expected_category",
    [
        pytest.param("OOC: does this need a roll?", "roll_requirement_query", id="ooc_roll_question"),
        pytest.param("OOC, what actions are available?", None, id="ooc_actions_available"),
    ],
)
def test_chat_explicit_ooc_stays_adjudication_without_gpt(
    tmp_path, monkeypatch, user_text, expected_category
):
    """Explicit OOC/mechanical questions bypass dialogue lock and resolve as adjudication (no GPT)."""
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})

    assert resp.status_code == 200
    data = resp.json()
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    if expected_category is not None:
        adjudication = (data.get("resolution") or {}).get("adjudication") or {}
        assert adjudication.get("category") == expected_category


# feature: emission
def test_chat_earshot_question_routes_to_adjudication_with_state_answer(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
        {"id": "guard", "name": "Guard Captain", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is anyone else in earshot?"})

    assert resp.status_code == 200
    data = resp.json()
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    assert adjudication.get("category") == "perception_query"
    assert adjudication.get("answer_type") == "direct_answer"
    assert "Guard Captain" in ((data.get("gm_output") or {}).get("player_facing_text") or "")


# feature: emission
def test_chat_adjudication_refuses_over_answer_without_basis(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "How far away is he?"})

    assert resp.status_code == 200
    data = resp.json()
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    assert adjudication.get("answer_type") == "needs_concrete_action"
    low = (((data.get("gm_output") or {}).get("player_facing_text") or "").lower())
    assert "state exactly what you do" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "need a concrete" in low
        or "nothing in the scene points to a clear answer yet" in low
        or "from here, no certain answer presents itself" in low
        or "the truth is still buried beneath rumor and rain" in low
        or "no answer presents itself from here" in low
        or "truth stays locked until someone pushes a concrete move" in low
        or "answer has not formed yet" in low
    )


# feature: continuity, emission
def test_chat_mixed_turn_preserves_embedded_adjudication_metadata(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "I investigate the desk (Is Perception needed?)"},
        )
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"discover_clue", "investigate"}
    metadata = resolution.get("metadata") or {}
    embedded = metadata.get("embedded_adjudication") or {}
    assert embedded.get("category") == "roll_requirement_query"
    assert embedded.get("requires_check") is True
    assert "Perception" in (embedded.get("question") or "")


# feature: routing, social
def test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "alleys", "text": "Try the alley by the bathhouse.", "clue_id": "bathhouse_alley"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": '"Where can I find them?" (Does that require Sleight of Hand?)'},
        )

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    metadata = resolution.get("metadata") or {}
    embedded = metadata.get("embedded_adjudication") or {}
    assert embedded.get("category") == "roll_requirement_query"
    assert embedded.get("requires_check") is True


# feature: emission
def test_chat_persuasion_returns_engine_check_prompt_without_gpt(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "guard", "name": "Gate Guard", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)
    social_action = {
        "id": "persuade-guard",
        "label": "Persuade the guard",
        "type": "persuade",
        "prompt": "I persuade the gate guard to let me pass.",
        "target_id": "guard",
        "targetEntityId": "guard",
    }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I persuade the gate guard to let me pass."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "persuade"
    assert resolution.get("requires_check") is True

    check_request = resolution.get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert check_request.get("skill") == "diplomacy"
    assert "Roll" in (check_request.get("player_prompt") or "")
    assert "Gate Guard" in (check_request.get("player_prompt") or "")

    gm_output = data.get("gm_output") or {}
    tags = gm_output.get("tags") or []
    crowd_text = gm_output.get("player_facing_text") or ""

    assert "check_required" in tags
    assert "gate guard" in crowd_text.lower()
    assert crowd_text.strip()


# feature: emission
def test_chat_covert_concealment_under_observation_prompts_engine_check(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is a roll needed if I conceal the letter while the guard is watching?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "adjudication_query"
    assert resolution.get("requires_check") is True
    check_request = resolution.get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert check_request.get("skill") == "sleight_of_hand"
    assert "covert" in (check_request.get("reason") or "")
    assert "Roll" in (check_request.get("player_prompt") or "")
    tags = ((data.get("gm_output") or {}).get("tags") or [])
    assert ("check_required" in tags) or ("adjudication_query" in tags)


# feature: legality
def test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "How far away is he?"})

    assert resp.status_code == 200
    data = resp.json()
    text = ((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "resolve that procedurally" not in low
    assert "adjudication:" not in low
    assert "authoritative state" not in low
    assert "state exactly what you do" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "distance is unclear" in low
        or "nothing in the scene points to a clear answer yet" in low
        or "from here, no certain answer presents itself" in low
        or "the truth is still buried beneath rumor and rain" in low
        or "no answer presents itself from here" in low
        or "truth stays locked until someone pushes a concrete move" in low
        or "answer has not formed yet" in low
    )


# feature: legality
def test_chat_final_output_sanitizer_blocks_internal_scaffold_labels(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("Planner: route via router. Validator: unresolved."),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where should I start?"})

    assert resp.status_code == 200
    data = resp.json()
    text = ((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "planner:" not in low
    assert "router" not in low
    assert "validator:" not in low


# feature: emission
def test_resolved_turn_trace_is_compact_and_authoritative(tmp_path, monkeypatch):
    explore_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )

    assert resp.status_code == 200
    data = resp.json()
    traces = data.get("debug_traces") or []
    assert traces
    latest = traces[-1]
    turn_trace = latest.get("turn_trace") or {}

    assert turn_trace.get("player_input") == "I investigate the desk."
    assert (turn_trace.get("classification") or {}).get("resolved_kind") == "discover_clue"
    assert turn_trace.get("resolution_path") == "exploration_engine"

    clues = turn_trace.get("clues") or {}
    assert "A map indicates patrol locations." in (clues.get("discovered_texts") or [])
    clue_counts = clues.get("known_counts") or {}
    assert clue_counts.get("explicit", 0) >= 1

    interaction_after = turn_trace.get("interaction_after") or {}
    session_ctx = data.get("session", {}).get("interaction_context", {})
    assert interaction_after.get("interaction_mode") == session_ctx.get("interaction_mode")

    affordances_after = turn_trace.get("affordances_after") or []
    assert any(a.get("id") == "desk" for a in affordances_after if isinstance(a, dict))


# feature: emission
@pytest.mark.parametrize(
    "channel",
    [
        pytest.param("action", id="via_api_action"),
        pytest.param("chat", id="via_api_chat"),
    ],
)
def test_action_and_chat_mutate_runtime_before_prompt_context_construction(
    tmp_path, monkeypatch, channel
):
    """Exploration resolution updates scene_runtime before build_messages sees it (action and chat)."""
    explore_action = {
        "id": "desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    captured: dict = {}

    def _fake_build_messages(*_args, **kwargs):
        scene_runtime = kwargs.get("scene_runtime") or {}
        captured["discovered_clues"] = list(scene_runtime.get("discovered_clues") or [])
        captured["searched_targets"] = list(scene_runtime.get("searched_targets") or [])
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        if channel == "action":
            resp = client.post(
                "/api/action",
                json={
                    "action_type": "exploration",
                    "intent": "I investigate the desk.",
                    "exploration_action": explore_action,
                },
            )
        else:
            m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
            m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: explore_action)
            m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
            resp = client.post("/api/chat", json={"text": "I investigate the desk."})

    assert resp.status_code == 200
    assert "A map indicates patrol locations." in (captured.get("discovered_clues") or [])
    assert "desk" in (captured.get("searched_targets") or [])


# feature: emission
def test_affordances_are_state_derived_not_from_gpt_text(tmp_path, monkeypatch):
    explore_action = {
        "id": "desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    gm_with_unrelated_text = {
        "player_facing_text": "A mysterious red button appears in your mind.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": {"id": "push-red-button", "label": "Push the red button", "type": "interact", "prompt": "I push the red button."},
        "debug_notes": "",
    }
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: gm_with_unrelated_text)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )

    assert resp.status_code == 200
    data = resp.json()
    affordances = data.get("ui", {}).get("affordances") or []
    affordance_ids = {a.get("id") for a in affordances if isinstance(a, dict)}
    assert "push-red-button" not in affordance_ids
    desk_affs = [a for a in affordances if isinstance(a, dict) and a.get("id") == "desk"]
    assert desk_affs
    assert "(already searched)" in str(desk_affs[0].get("label") or "")


# feature: social
def test_chat_implied_lowered_voice_is_applied_before_prompt_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured: dict = {}

    def _fake_build_messages(*args, **_kwargs):
        session = args[2]
        ctx = (session.get("interaction_context") or {}).copy()
        captured["conversation_privacy"] = ctx.get("conversation_privacy")
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I lower my voice and ask quietly about the gate."})

    assert resp.status_code == 200
    assert captured.get("conversation_privacy") == "lowered_voice"


# feature: social
def test_chat_implied_sit_with_target_is_applied_before_prompt_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)
    captured: dict = {}
    social_action = {
        "id": "question-runner",
        "label": "Talk to Tavern Runner",
        "type": "question",
        "prompt": "I talk to Tavern Runner.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }

    def _fake_build_messages(*args, **_kwargs):
        session = args[2]
        ctx = (session.get("interaction_context") or {}).copy()
        captured["player_position_context"] = ctx.get("player_position_context")
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I sit down with the tavern runner and ask about the gate."})

    assert resp.status_code == 200
    assert captured.get("player_position_context") == "seated_with_target"


# feature: emission
def test_final_emission_gate_replaces_invalid_social_exchange_blob_before_emit(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "From here, no certain answer presents itself. "
                "The runner keeps repeating the same rumors while rain hits the shutters."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    text = str(gm_out.get("player_facing_text") or "")
    low = text.lower()
    assert "from here, no certain answer presents itself" not in low
    assert "truth is still buried beneath rumor and rain" not in low
    assert "tavern runner" in low
    tags = gm_out.get("tags") or []
    dbg = str(gm_out.get("debug_notes") or "").lower()
    assert (
        "final_emission_gate_replaced" in tags
        or "question_retry_fallback" in tags
        or "social_exchange_retry_fallback" in tags
        or "retry_fallback" in dbg
        or "final_emission_gate" in dbg
    )


# feature: emission, legality
def test_final_emission_gate_blocks_advisory_prose_inside_social_exchange(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "I'd suggest you question the notice board clerk before the lane goes cold."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "i'd suggest you" not in low
    assert "you should" not in low
    assert "you could" not in low
    gm_out = data.get("gm_output") or {}
    gtags = gm_out.get("tags") or []
    dbg = str(gm_out.get("debug_notes") or "").lower()
    assert (
        "final_emission_gate_replaced" in gtags
        or "question_retry_fallback" in gtags
        or "social_exchange_retry_fallback" in gtags
        or "retry_fallback" in dbg
        or "final_emission_gate" in dbg
    )


# feature: emission
def test_final_emission_gate_strips_unresolved_stock_phrases_from_social_output(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "The truth is still buried beneath rumor and rain. "
                "The answer has not formed yet."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "truth is still buried beneath rumor and rain" not in low
    assert "answer has not formed yet" not in low
    gm_out = data.get("gm_output") or {}
    gtags = gm_out.get("tags") or []
    dbg = str(gm_out.get("debug_notes") or "").lower()
    assert (
        "final_emission_gate_replaced" in gtags
        or "question_retry_fallback" in gtags
        or "social_exchange_retry_fallback" in gtags
        or "retry_fallback" in dbg
        or "final_emission_gate" in dbg
    )


# feature: emission
def test_final_emission_gate_keeps_interruption_output_coherent(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                'Tavern Runner says, "No names. Only rumors." A shout erupts in the crowd. '
                "I'd suggest you ask the captain and check the board."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "i'd suggest you" not in low
    assert "check the board" not in low
    assert any(
        phrase in low
        for phrase in (
            "shouting breaks out",
            "shout cuts across the square",
            "\"i don't know.\"",
            "\"no names. only rumors.\"",
            "no names",
            "rumors",
            "that's all i've got",
        )
    )


# feature: emission
def test_final_emission_gate_repeated_questioning_can_end_clean_refusal(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    stale_blob = _gm_response(
        "From here, no certain answer presents itself. "
        "The runner says no names and then lists rumors while I'd suggest you check the board."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: stale_blob)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        client.post("/api/chat", json={"text": "Who attacked them?"})
        client.post("/api/chat", json={"text": "Who is really behind it?"})
        third = client.post("/api/chat", json={"text": "Who ordered it?"})

    assert third.status_code == 200
    data = third.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert any(
        phrase in low
        for phrase in (
            "i've told you what i know",
            "no more questions",
            "shout cuts across the square",
            "shouting breaks out",
            "don't know",
            "do not know",
            "heard talk",
            "not names",
            "tightens their jaw",
            "all you're getting from me",
            "that's all i've got",
            "frowns",
        )
    )
    assert "from here, no certain answer presents itself" not in low
    assert "i'd suggest you" not in low
