"""Transcript-style tests: multi-POST sequencing and session continuity (not single-turn correctness).

Single-turn routing, discovery shape, and combat engine details are covered by integration/unit tests
(e.g. ``test_turn_pipeline_shared``, ``test_exploration_resolution``, ``test_discovery_memory``,
``test_combat_resolution``). This module locks **ordering** across requests (state from turn N
must be visible on turn N+1) and a small slice of **retry-budget exhaustion** end-to-end on
``/api/action`` (terminal forward progress, not narration wording).
"""
from __future__ import annotations

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
from game.gm import MAX_TARGETED_RETRY_ATTEMPTS
from fastapi.testclient import TestClient

import pytest

pytestmark = [pytest.mark.transcript, pytest.mark.slow]

DESK_CLUE_ID = "desk_clue"

# Triggers ``validator_voice`` retry failures on every attempt (no ``?`` player line → no unresolved-question race).
_VALIDATOR_VOICE_TRAP_TEXT = (
    "Based on what's established, we can determine very little here."
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


def _seed_transcript_world(tmp_path, monkeypatch, **overrides):
    """Minimal graph: investigation scene, a<->b loop, isolated unreachable from a; optional goblin."""
    _patch_storage(tmp_path, monkeypatch)
    active = overrides.get("active", "scene_investigate")

    inv_scene = default_scene("scene_investigate")
    inv_scene["scene"]["id"] = "scene_investigate"
    inv_scene["scene"]["location"] = "Investigation room"
    inv_scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate", "reveals_clue": DESK_CLUE_ID},
    ]
    inv_scene["scene"]["discoverable_clues"] = [
        {"id": DESK_CLUE_ID, "text": "A map indicates patrol locations."},
    ]
    if overrides.get("with_goblin"):
        inv_scene["scene"]["enemies"] = [
            {
                "id": "goblin_1",
                "name": "Goblin",
                "hp": {"current": 6, "max": 6},
                "initiative_bonus": -10,
                "creature_type": "humanoid",
                "hd": 1,
                "saves": {"will": 0},
                "attacks": [
                    {
                        "id": "dagger",
                        "name": "Dagger",
                        "attack_bonus": 1,
                        "damage": {"dice_count": 1, "dice_sides": 4, "bonus": 0, "type": "piercing"},
                    }
                ],
            }
        ]
    inv_scene["scene"]["exits"] = [{"label": "To Scene B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_investigate"), inv_scene)

    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)

    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    sb["scene"]["exits"] = [{"label": "To A", "target_scene_id": "scene_a"}]
    storage._save_json(storage.scene_path("scene_b"), sb)

    si = default_scene("scene_isolated")
    si["scene"]["id"] = "scene_isolated"
    si["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_isolated"), si)

    session = default_session()
    session["active_scene_id"] = active
    session["visited_scene_ids"] = ["scene_investigate", "scene_a", "scene_b", "scene_isolated"]
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


def _seed_transcript_world_with_runner(tmp_path, monkeypatch):
    """Transcript seed plus a single NPC for directed social turns on the investigation scene."""
    _seed_transcript_world(tmp_path, monkeypatch)
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


def _assert_player_facing_text_is_usable(text: str) -> None:
    t = (text or "").strip()
    assert t, "player-facing text must be non-empty"
    assert not t.startswith("{"), "player-facing text must not look like a raw JSON object"
    assert '"player_facing_text"' not in t, "player-facing text must not embed serialized payload keys"
    assert '"scene_update"' not in t


def _assert_terminal_retry_or_repair_metadata(gm: dict) -> None:
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    assert (
        gm.get("targeted_retry_terminal") is True
        or gm.get("retry_exhausted") is True
        or "forced_retry_fallback" in tags
        or "retry_escape_hatch" in tags
        or "retry_exhausted" in tags
        or "forced_retry_fallback" in dbg
        or "retry_escape_hatch" in dbg
    ), "expected terminal retry / escape-hatch signals on gm_output"


def _post_explore(client, exploration_action: dict, intent: str | None = None):
    payload = {"action_type": "exploration", "exploration_action": exploration_action}
    if intent:
        payload["intent"] = intent
    r = client.post("/api/action", json=payload)
    assert r.status_code == 200
    return r.json()


def test_transcript_sequence_investigate_then_repeat_is_idempotent(tmp_path, monkeypatch):
    """Turn 1 discovers; turn 2 must see persisted runtime and return already_searched (not a second clue)."""
    _seed_transcript_world(tmp_path, monkeypatch)
    desk_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk",
    }
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r1 = _post_explore(client, desk_action, intent="I investigate the desk")
        r2 = _post_explore(client, desk_action, intent="I investigate the desk")

    assert r1["resolution"]["kind"] == "discover_clue"
    assert r1["resolution"]["clue_id"] == DESK_CLUE_ID
    ids_1 = r1["session"]["scene_runtime"]["scene_investigate"]["discovered_clue_ids"]
    assert ids_1 == [DESK_CLUE_ID]

    assert r2["resolution"]["kind"] == "already_searched"
    assert r2["resolution"]["clue_id"] is None
    ids_2 = r2["session"]["scene_runtime"]["scene_investigate"]["discovered_clue_ids"]
    assert ids_2 == [DESK_CLUE_ID]
    assert r2["session"]["scene_runtime"]["scene_investigate"].get("repeated_action_count", 0) >= 2


def test_transcript_sequence_travel_then_blocked_respects_updated_scene(tmp_path, monkeypatch):
    """After a successful transition, the next request uses the new scene's exit graph (blocked hop stays put)."""
    _seed_transcript_world(tmp_path, monkeypatch, active="scene_a")
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r_ok = _post_explore(
            client,
            {
                "id": "go-b",
                "label": "Go to B",
                "type": "scene_transition",
                "targetSceneId": "scene_b",
                "prompt": "I go to B.",
            },
        )
        r_bad = _post_explore(
            client,
            {
                "id": "go-isolated",
                "label": "Go to isolated",
                "type": "scene_transition",
                "targetSceneId": "scene_isolated",
                "prompt": "I go to the isolated area.",
            },
        )

    assert r_ok["session"]["active_scene_id"] == "scene_b"
    assert r_ok["resolution"]["resolved_transition"] is True

    assert r_bad["resolution"]["resolved_transition"] is False
    assert r_bad["session"]["active_scene_id"] == "scene_b"


def test_transcript_sequence_combat_initiative_then_attack(tmp_path, monkeypatch):
    """Combat state from roll_initiative must persist for the following attack POST."""
    _seed_transcript_world(tmp_path, monkeypatch, with_goblin=True)
    monkeypatch.setattr("game.utils.roll_die", lambda _: 15)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r1 = client.post("/api/action", json={"action_type": "roll_initiative"})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["ok"] and d1["resolution"]["kind"] == "initiative"
        assert d1["combat"]["in_combat"] is True

        r2 = client.post(
            "/api/action",
            json={
                "action_type": "attack",
                "attack_id": "quarterstaff",
                "target_id": "goblin_1",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()

    assert d2["ok"] is True
    res2 = d2["resolution"]
    assert res2["kind"] == "attack"
    assert res2["combat"]["combat_phase"] == "attack"
    assert res2["combat"]["actor"]["id"] == "galinor"
    assert res2["combat"]["target"]["id"] == "goblin_1"


def test_transcript_social_retry_exhaustion_terminal_forward_progress(tmp_path, monkeypatch):
    """Social POST: every GPT attempt fails ``validator_voice`` until the budget is exhausted; response still completes."""
    _seed_transcript_world_with_runner(tmp_path, monkeypatch)
    social_action = {
        "id": "greet-runner",
        "label": "Acknowledge the runner",
        "type": "question",
        "prompt": "I nod to the Tavern Runner, giving them room to speak.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }
    gpt_calls: list = []

    def _always_fail_validator_voice(_messages):
        gpt_calls.append(_messages)
        return _gm_response(_VALIDATOR_VOICE_TRAP_TEXT)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _always_fail_validator_voice)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "social",
                "intent": "I nod to the Tavern Runner, giving them room to speak.",
                "social_action": social_action,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    gm = data.get("gm_output") or {}
    pft = gm.get("player_facing_text")
    _assert_player_facing_text_is_usable(str(pft or ""))
    assert _VALIDATOR_VOICE_TRAP_TEXT.lower() not in str(pft or "").lower()
    _assert_terminal_retry_or_repair_metadata(gm)

    assert len(gpt_calls) == 1 + MAX_TARGETED_RETRY_ATTEMPTS

    ctx = (data.get("session") or {}).get("interaction_context") or {}
    assert ctx.get("active_interaction_target_id") == "runner"
    assert ctx.get("active_interaction_kind") == "social"
    assert ctx.get("interaction_mode") == "social"
    assert (ctx.get("engagement_level") or "").strip().lower() == "engaged"

    res = data.get("resolution") or {}
    assert res.get("kind") == "question"
    assert (res.get("social") or {}).get("npc_id") == "runner"


def test_transcript_nonsocial_retry_exhaustion_terminal_forward_progress(tmp_path, monkeypatch):
    """Exploration POST: retry budget exhausts on repeated ``validator_voice``; clue discovery and narration still complete."""
    _seed_transcript_world(tmp_path, monkeypatch)
    desk_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk",
    }
    gpt_calls: list = []

    def _always_fail_validator_voice(_messages):
        gpt_calls.append(_messages)
        return _gm_response(_VALIDATOR_VOICE_TRAP_TEXT)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _always_fail_validator_voice)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "I investigate the desk",
                "exploration_action": desk_action,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    gm = data.get("gm_output") or {}
    _assert_player_facing_text_is_usable(str(gm.get("player_facing_text") or ""))
    _assert_terminal_retry_or_repair_metadata(gm)
    assert len(gpt_calls) == 1 + MAX_TARGETED_RETRY_ATTEMPTS

    assert (data.get("session") or {}).get("active_scene_id") == "scene_investigate"
    res = data.get("resolution") or {}
    assert res.get("kind") == "discover_clue"
    assert res.get("clue_id") == DESK_CLUE_ID
    rt = (data.get("session") or {}).get("scene_runtime", {}).get("scene_investigate") or {}
    assert DESK_CLUE_ID in (rt.get("discovered_clue_ids") or [])
