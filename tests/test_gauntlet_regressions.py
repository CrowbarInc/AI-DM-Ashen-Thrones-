from __future__ import annotations

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

pytestmark = [pytest.mark.integration, pytest.mark.regression]


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


def _seed_gate_and_roadside(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["visible_facts"] = [
        "A missing patrol notice hangs beside the checkpoint.",
        "A tavern runner offers rumors for coin under a torn awning.",
    ]
    gate["scene"]["exits"] = [{"label": "To Roadside", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("frontier_gate"), gate)

    roadside = default_scene("old_milestone")
    roadside["scene"]["id"] = "old_milestone"
    roadside["scene"]["visible_facts"] = [
        "A tattered man watches the road from a milestone.",
    ]
    roadside["scene"]["exits"] = [{"label": "Back to Gate", "target_scene_id": "frontier_gate"}]
    storage._save_json(storage.scene_path("old_milestone"), roadside)

    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [],
        },
        {
            "id": "tattered_man",
            "name": "Tattered Man",
            "location": "old_milestone",
            "topics": [{"id": "ditch", "text": "They moved through the ditch line before dawn."}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session.setdefault("interaction_context", {}).update(
        {
            "active_interaction_target_id": "runner",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
        }
    )
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_gauntlet_repeated_runner_probe_skips_policy_topic_pressure_for_strict_social(tmp_path, monkeypatch):
    _seed_gate_and_roadside(tmp_path, monkeypatch)
    stale_reply = {
        "player_facing_text": (
            "The runner shrugs and repeats old rumor: the crossroads were bad, "
            "but no one has names yet and the same whispers keep circling."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: stale_reply)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        # Keep this focused on topic-pressure behavior.
        m.setattr("game.gm.resolve_known_fact_before_uncertainty", lambda *_args, **_kwargs: None)
        m.setattr("game.gm.enforce_question_resolution_rule", lambda gm, **_kwargs: gm)
        client = TestClient(app)
        prompts = [
            "Who hit the patrol?",
            "Who is really behind it?",
            "Who ordered it?",
        ]
        out = None
        for prompt in prompts:
            out = client.post("/api/chat", json={"text": prompt})

    assert out is not None and out.status_code == 200
    data = out.json()
    tags = (data.get("gm_output") or {}).get("tags") or []
    # Strict-social turns skip topic_pressure / scene_momentum policy mutators; final emission gate owns the rewrite.
    assert "topic_pressure_escalation" not in tags
    assert not any(str(tag).startswith("scene_momentum:") for tag in tags)


def test_gauntlet_vague_npc_question_stays_dialogue_and_not_procedural(tmp_path, monkeypatch):
    _seed_gate_and_roadside(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: {
                "player_facing_text": "I need a more concrete action or target to resolve that procedurally.",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            },
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Runner, who saw this happen?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"question", "social_probe"}
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    low = ((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "resolve that procedurally" not in low


def test_gauntlet_scene_transition_locks_runner_out_of_roadside_dialogue(tmp_path, monkeypatch):
    _seed_gate_and_roadside(tmp_path, monkeypatch)
    transition_action = {
        "id": "follow-tattered-man",
        "label": "Follow the tattered man",
        "type": "scene_transition",
        "prompt": "I follow the tattered man to the roadside.",
        "targetSceneId": "old_milestone",
    }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: {"player_facing_text": "[Narration]", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""})
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: transition_action)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        moved = client.post("/api/chat", json={"text": "I follow the tattered man."})
        assert moved.status_code == 200
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called for offscene target guard")))
        blocked = client.post("/api/chat", json={"text": "Runner, what happened to the patrol?"})

    assert blocked.status_code == 200
    data = blocked.json()
    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    assert social.get("npc_id") == "runner"
    assert social.get("offscene_target") is True
    assert data.get("scene", {}).get("scene", {}).get("id") == "old_milestone"


def test_gauntlet_final_output_strips_internal_scaffold_terms(tmp_path, monkeypatch):
    _seed_gate_and_roadside(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: {
                "player_facing_text": "Planner: use router path. Validator: based on established state.",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            },
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What now?"})

    assert resp.status_code == 200
    low = ((resp.json().get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "planner:" not in low
    assert "router" not in low
    assert "validator:" not in low


def test_gauntlet_malformed_splice_does_not_leak_fragment_concat(tmp_path, monkeypatch):
    _seed_gate_and_roadside(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: {
                "player_facing_text": "there's no solid evidence... you might start leaves by speaking to the runner.",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            },
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where should I start?"})

    assert resp.status_code == 200
    low = ((resp.json().get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "start leaves by speaking" not in low
    assert "state exactly what you do" not in low
    assert "start with " not in low


def test_gauntlet_slice_strict_social_narrative_authority_repair(monkeypatch):
    """Thin integration hook: strict-social NA + speaker stability (canonical case in emission tests)."""
    from tests.test_final_emission_gate import test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker

    test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker(monkeypatch)
