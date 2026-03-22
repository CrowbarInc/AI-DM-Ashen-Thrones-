"""Transcript-style regression tests: multi-step gameplay flows end to end.

These tests protect the play loop from sequencing regressions. They are deterministic,
use no live GPT/network calls, and assert stable state transitions, engine results,
and runtime behavior across realistic multi-step flows.
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
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

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
    """Patch storage paths to use tmp_path. Matches pattern from other tests."""
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
    """Seed a minimal world for transcript tests.

    Creates:
    - scene_investigate: interactable 'desk' reveals 'desk_clue', with optional skill_check
    - scene_a: exits to scene_b
    - scene_b: exits back to scene_a
    - scene_isolated: no exit from scene_a (unreachable for transition tests)

    overrides:
        active: initial active_scene_id (default: scene_investigate)
        with_skill_check: if True, add skill_check to desk interactable
        with_goblin: if True, add goblin enemy to scene_investigate for combat
    """
    _patch_storage(tmp_path, monkeypatch)
    active = overrides.get("active", "scene_investigate")

    # Scene with investigable desk + clue
    inv_scene = default_scene("scene_investigate")
    inv_scene["scene"]["id"] = "scene_investigate"
    inv_scene["scene"]["location"] = "Investigation room"
    inv_scene["scene"]["interactables"] = [
        {
            "id": "desk",
            "type": "investigate",
            "reveals_clue": "desk_clue",
        }
    ]
    inv_scene["scene"]["discoverable_clues"] = [
        {"id": "desk_clue", "text": "A map indicates patrol locations."}
    ]
    if overrides.get("with_skill_check"):
        inv_scene["scene"]["interactables"][0]["skill_check"] = {
            "skill_id": "perception",
            "dc": 10,
        }
    if overrides.get("with_goblin"):
        inv_scene["scene"]["enemies"] = [
            {
                "id": "goblin_1",
                "name": "Goblin",
                "hp": {"current": 6, "max": 6},
                "initiative_bonus": -10,  # Ensure player wins initiative when both roll 15
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

    # scene_a -> scene_b
    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)

    # scene_b -> scene_a
    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    sb["scene"]["exits"] = [{"label": "To A", "target_scene_id": "scene_a"}]
    storage._save_json(storage.scene_path("scene_b"), sb)

    # scene_isolated: only exit to scene_b; no path FROM scene_a
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


def _post_action(client, exploration_action: dict, intent: str | None = None):
    """POST /api/action with exploration action. Returns response JSON."""
    payload = {"action_type": "exploration", "exploration_action": exploration_action}
    if intent:
        payload["intent"] = intent
    r = client.post("/api/action", json=payload)
    assert r.status_code == 200
    return r.json()


def test_transcript_exploration_social_affordance_routes_social_engine(tmp_path, monkeypatch):
    """Exploration-posted social affordance should resolve through social engine."""
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

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r = _post_action(
            client,
            {
                "id": "question-runner",
                "label": "Talk to Tavern Runner",
                "type": "question",
                "prompt": "I talk to Tavern Runner.",
                "targetEntityId": "runner",
            },
            intent="I talk to Tavern Runner.",
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert res["kind"] == "question"
    assert res["social"]["npc_id"] == "runner"
    ctx = (r.get("session", {}).get("interaction_context") or {})
    assert ctx.get("active_interaction_target_id") == "runner"
    assert ctx.get("active_interaction_kind") == "social"


def test_chat_fallback_does_not_clear_existing_interaction_context(tmp_path, monkeypatch):
    """Chat fallback (no parsed action kind) should preserve existing social context."""
    _seed_transcript_world(tmp_path, monkeypatch)
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
    session["interaction_context"] = {
        "active_interaction_target_id": "runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": "lowered_voice",
        "player_position_context": "seated_with_target",
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "hello there"})

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    ctx = (data.get("session", {}).get("interaction_context") or {})
    assert ctx.get("active_interaction_target_id") == "runner"
    assert ctx.get("active_interaction_kind") == "social"
    assert ctx.get("interaction_mode") == "social"
    assert ctx.get("engagement_level") == "engaged"
    assert ctx.get("conversation_privacy") == "lowered_voice"
    assert ctx.get("player_position_context") == "seated_with_target"


def test_chat_narration_text_alone_does_not_discover_clue(tmp_path, monkeypatch):
    """GPT wording that includes a clue text does not mutate clue discovery without engine resolution."""
    _seed_transcript_world(tmp_path, monkeypatch)
    clue_text = "A map indicates patrol locations."
    gpt_with_clue = dict(FAKE_GPT_RESPONSE)
    gpt_with_clue["player_facing_text"] = f"As you investigate, you notice: {clue_text}"

    with monkeypatch.context() as m:
        # Force chat fallback path (no deterministic action resolution).
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.call_gpt", lambda _: gpt_with_clue)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I investigate the desk carefully."})

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    rt = data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})
    assert clue_text not in (rt.get("discovered_clues") or [])
    assert data.get("resolution") is None


# ---------------------------------------------------------------------------
# Transcript 1: investigate target -> clue discovered -> scene/runtime updated
# ---------------------------------------------------------------------------


def test_transcript_investigate_clue_discovery_runtime_updated(tmp_path, monkeypatch):
    """Investigate interactable -> discover_clue -> session runtime and scene updated."""
    _seed_transcript_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        r = _post_action(
            client,
            {
                "id": "inv-desk",
                "label": "Investigate the desk",
                "type": "investigate",
                "prompt": "I investigate the desk",
            },
            intent="I investigate the desk",
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert res["kind"] == "discover_clue"
    assert res["interactable_id"] == "desk"
    assert res["clue_id"] == "desk_clue"
    assert res["clue_text"] == "A map indicates patrol locations."
    assert res["discovered_clues"] == ["A map indicates patrol locations."]
    assert res["state_changes"].get("clue_revealed") is True

    session = r["session"]
    rt = session.get("scene_runtime", {}).get("scene_investigate", {})
    assert "A map indicates patrol locations." in (rt.get("discovered_clues") or [])
    assert "desk" in (rt.get("resolved_interactables") or [])
    assert "inv-desk" in (rt.get("searched_targets") or []) or "desk" in (rt.get("searched_targets") or [])


# ---------------------------------------------------------------------------
# Transcript 2: repeat same target -> no duplicate discovery / exhausted result
# ---------------------------------------------------------------------------


def test_transcript_repeat_investigate_already_searched(tmp_path, monkeypatch):
    """Repeat investigate same target -> already_searched, no duplicate clue."""
    _seed_transcript_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        # Step 1: First investigate -> discover_clue
        r1 = _post_action(
            client,
            {
                "id": "inv-desk",
                "label": "Investigate the desk",
                "type": "investigate",
                "prompt": "I investigate the desk",
            },
            intent="I investigate the desk",
        )
        assert r1["ok"] is True
        assert r1["resolution"]["kind"] == "discover_clue"
        clues_after_first = (r1["session"].get("scene_runtime", {}).get("scene_investigate", {}).get("discovered_clues") or [])

        # Step 2: Repeat same action -> already_searched
        r2 = _post_action(
            client,
            {
                "id": "inv-desk",
                "label": "Investigate the desk",
                "type": "investigate",
                "prompt": "I investigate the desk",
            },
            intent="I investigate the desk",
        )

    assert r2["ok"] is True
    res2 = r2["resolution"]
    assert res2["kind"] == "already_searched"
    assert res2["discovered_clues"] == []
    assert res2["clue_id"] is None
    assert res2["state_changes"].get("already_searched") is True

    clues_after_second = (r2["session"].get("scene_runtime", {}).get("scene_investigate", {}).get("discovered_clues") or [])
    assert clues_after_second == clues_after_first
    assert len(clues_after_second) == 1

    # Anti-stall: repeated action increments repeated_action_count
    rt2 = r2["session"].get("scene_runtime", {}).get("scene_investigate", {})
    assert rt2.get("repeated_action_count", 0) >= 2


# ---------------------------------------------------------------------------
# Transcript 3: valid scene transition -> active scene updates correctly
# ---------------------------------------------------------------------------


def test_transcript_valid_transition_active_scene_updated(tmp_path, monkeypatch):
    """Valid scene_transition -> active_scene_id and visited updated."""
    _seed_transcript_world(tmp_path, monkeypatch, active="scene_a")
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        r = _post_action(
            client,
            {
                "id": "go-b",
                "label": "Go to B",
                "type": "scene_transition",
                "targetSceneId": "scene_b",
                "prompt": "I go to B.",
            },
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert res["resolved_transition"] is True
    assert res["target_scene_id"] == "scene_b"
    assert res["state_changes"].get("scene_changed") is True

    session = r["session"]
    assert session["active_scene_id"] == "scene_b"
    assert "scene_b" in (session.get("visited_scene_ids") or [])

    scene = r["scene"]
    assert scene["scene"]["id"] == "scene_b"


# ---------------------------------------------------------------------------
# Transcript 4: invalid/unreachable transition -> fails cleanly and deterministically
# ---------------------------------------------------------------------------


def test_transcript_invalid_transition_fails_cleanly(tmp_path, monkeypatch):
    """Invalid transition to unreachable scene -> resolved_transition=False, stay in place."""
    _seed_transcript_world(tmp_path, monkeypatch, active="scene_a")
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        # scene_a has exit only to scene_b. scene_isolated has no incoming from scene_a.
        r = _post_action(
            client,
            {
                "id": "go-isolated",
                "label": "Go to isolated",
                "type": "scene_transition",
                "targetSceneId": "scene_isolated",
                "prompt": "I go to the isolated area.",
            },
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert res["resolved_transition"] is False
    hint = res.get("hint", "")
    assert "not reachable" in hint or "blocked" in hint.lower() or "path" in hint.lower()

    session = r["session"]
    assert session["active_scene_id"] == "scene_a"

    scene = r["scene"]
    assert scene["scene"]["id"] == "scene_a"


# ---------------------------------------------------------------------------
# Transcript 5: checked exploration action -> skill_check result represented
# ---------------------------------------------------------------------------


def test_transcript_skill_check_exploration_result_represented(tmp_path, monkeypatch):
    """Exploration action with skill_check -> resolution has skill_check, roll, dc, success."""
    _seed_transcript_world(tmp_path, monkeypatch, with_skill_check=True)
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 15)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        r = _post_action(
            client,
            {
                "id": "inv-desk",
                "label": "Investigate the desk",
                "type": "investigate",
                "prompt": "I investigate the desk",
            },
            intent="I investigate the desk",
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert "skill_check" in res
    sc = res["skill_check"]
    assert sc["roll"] == 15
    assert "total" in sc
    assert sc["dc"] == 10
    assert sc["success"] is True
    assert res["kind"] == "discover_clue"


def test_transcript_failed_skill_check_does_not_reveal_clue(tmp_path, monkeypatch):
    """Failed gated investigate check never reveals clue even if narration mentions it."""
    _seed_transcript_world(tmp_path, monkeypatch, with_skill_check=True)
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 1)
    gpt_with_clue = dict(FAKE_GPT_RESPONSE)
    gpt_with_clue["player_facing_text"] = "You fail to notice anything decisive, but a map indicates patrol locations."

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: gpt_with_clue)
        client = TestClient(app)
        r = _post_action(
            client,
            {
                "id": "inv-desk",
                "label": "Investigate the desk",
                "type": "investigate",
                "prompt": "I investigate the desk",
            },
            intent="I investigate the desk",
        )

    assert r["ok"] is True
    res = r["resolution"]
    assert res["kind"] == "investigate"
    assert res["success"] is False
    rt = r["session"].get("scene_runtime", {}).get("scene_investigate", {})
    assert "A map indicates patrol locations." not in (rt.get("discovered_clues") or [])
    assert (rt.get("discovered_clue_ids") or []) == []


# ---------------------------------------------------------------------------
# Transcript 6: combat start -> action -> turn/state
# ---------------------------------------------------------------------------


def test_transcript_combat_initiative_action_turn(tmp_path, monkeypatch):
    """Roll initiative -> attack -> resolution has canonical combat shape, state updates."""
    _seed_transcript_world(tmp_path, monkeypatch, with_goblin=True)
    # Both combat and exploration use game.utils.roll_die
    monkeypatch.setattr("game.utils.roll_die", lambda _: 15)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)

        # Step 1: Roll initiative
        r1 = client.post("/api/action", json={"action_type": "roll_initiative"})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["ok"] is True
        res1 = d1["resolution"]
        assert res1["kind"] == "initiative"
        assert "combat" in res1
        assert res1["combat"]["round"] == 1
        assert res1["combat"]["order"]
        combat1 = d1["combat"]
        assert combat1["in_combat"] is True

        # Step 2: Attack
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
        assert "combat" in res2
        assert res2["combat"]["combat_phase"] == "attack"
        assert "hit" in res2
        assert "damage_dealt" in res2["combat"] or "damage" in res2
        assert res2["combat"]["actor"]["id"] == "galinor"
        assert res2["combat"]["target"]["id"] == "goblin_1"
