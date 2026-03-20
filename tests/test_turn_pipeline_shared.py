"""Shared turn-pipeline tests for /api/action and /api/chat.

These tests verify both endpoints exercise the same resolved-turn orchestration.
"""
from __future__ import annotations

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


def test_chat_validator_voice_triggers_single_retry_instruction(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    first = {
        "player_facing_text": "Based on what's established, we can determine very little here.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    second = dict(FAKE_GPT_RESPONSE)

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        return first if len(captured_inputs) == 1 else second

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What do I know so far?"})

    assert resp.status_code == 200
    assert len(captured_inputs) == 2
    retry_messages = captured_inputs[1]
    retry_tail = retry_messages[-1]["content"]
    assert "Do not explain limitations. Answer in-world or via OC." in retry_tail


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


def test_chat_active_target_location_question_routes_to_social_exchange(tmp_path, monkeypatch):
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
        resp = client.post("/api/chat", json={"text": "Where can I find them?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    assert resolution.get("kind") != "adjudication_query"


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
    assert resolution.get("kind") != "adjudication_query"


def test_chat_explicit_ooc_roll_question_stays_adjudication(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "OOC: does this need a roll?"})

    assert resp.status_code == 200
    data = resp.json()
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert adjudication.get("category") == "roll_requirement_query"


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
    assert "need a concrete" in (((data.get("gm_output") or {}).get("player_facing_text") or "").lower())


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
    assert check_request.get("skill") == "diplomacy"
    assert "Roll" in (check_request.get("player_prompt") or "")
    assert "check_required" in ((data.get("gm_output") or {}).get("tags") or [])
    assert (data.get("gm_output") or {}).get("player_facing_text") == check_request.get("player_prompt")


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


def test_action_mutates_runtime_before_prompt_context_construction(tmp_path, monkeypatch):
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
        resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )

    assert resp.status_code == 200
    assert "A map indicates patrol locations." in (captured.get("discovered_clues") or [])
    assert "desk" in (captured.get("searched_targets") or [])


def test_chat_mutates_runtime_before_prompt_context_construction(tmp_path, monkeypatch):
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
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: explore_action)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I investigate the desk."})

    assert resp.status_code == 200
    assert "A map indicates patrol locations." in (captured.get("discovered_clues") or [])
    assert "desk" in (captured.get("searched_targets") or [])


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
