"""Scene-transition authority tests.

Engine/resolution path is authoritative for scene activation in a turn.
GPT transition fields are advisory-only.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.intent_parser import maybe_build_declared_travel_action, segment_mixed_player_turn
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
from game.storage import get_scene_runtime
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)

import pytest

pytestmark = pytest.mark.integration

# feature: routing, emission


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


def _seed_three_scenes(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)

    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    storage._save_json(storage.scene_path("scene_b"), sb)

    sc = default_scene("scene_c")
    sc["scene"]["id"] = "scene_c"
    storage._save_json(storage.scene_path("scene_c"), sc)

    session = default_session()
    session["active_scene_id"] = "scene_a"
    session["visited_scene_ids"] = ["scene_a"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _gm_with_transition_proposal(target: str) -> dict:
    return {
        "player_facing_text": "Narration.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": target,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def _gm_with_full_transition_proposal(*, activate: str, draft_title: str = "Proposed scene") -> dict:
    return {
        "player_facing_text": "Narration.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": activate,
        "new_scene_draft": {"title": draft_title, "summary": "GPT-only draft"},
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def test_resolver_scene_transition_remains_authoritative(tmp_path, monkeypatch):
    """Resolver transition applies; conflicting GPT proposal stays advisory."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "Go to B",
                "exploration_action": {
                    "id": "go-b",
                    "label": "Go to B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to B.",
                },
            },
        )

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("resolution", {}).get("resolved_transition") is True
    assert data.get("resolution", {}).get("target_scene_id") == "scene_b"
    assert data.get("session", {}).get("active_scene_id") == "scene_b"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_b"
    # Proposal remains present but non-authoritative.
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_c"
    assert "scene_c" not in (data.get("session", {}).get("visited_scene_ids") or [])


def test_gpt_transition_proposal_does_not_apply_without_resolver_transition(tmp_path, monkeypatch):
    """Chat turn with only GPT transition proposal does not activate scene."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_b"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "hello there"})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_b"
    assert data.get("session", {}).get("active_scene_id") == "scene_a"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_a"


def test_gpt_transition_proposals_cannot_mutate_state_without_authoritative_transition(
    tmp_path, monkeypatch,
):
    """GM output may include activate_scene_id and new_scene_draft; engine must not resolve a transition."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _: _gm_with_full_transition_proposal(activate="scene_b", draft_title="Hallucinated locale"),
        )
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I wonder what the weather is like."})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    gm = data.get("gm_output") or {}
    assert gm.get("activate_scene_id") == "scene_b"
    assert isinstance(gm.get("new_scene_draft"), dict)
    dbg = str(gm.get("debug_notes") or "")
    assert "advisory_only" in dbg
    assert "activate_scene_id" in dbg
    assert "new_scene_draft" in dbg
    assert data.get("session", {}).get("active_scene_id") == "scene_a"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_a"
    traces = data.get("debug_traces") or []
    assert traces, "expected persisted debug_traces on session"
    last = traces[-1]
    res = last.get("resolution")
    if isinstance(res, dict):
        assert res.get("resolved_transition") in (None, False)
        assert res.get("target_scene_id") in (None, "")


def test_farewell_only_does_not_trigger_declared_travel(tmp_path, monkeypatch):
    """Quoted goodbye alone: no declared-travel action, no movement override, no scene change."""
    _patch_storage(tmp_path, monkeypatch)
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["exits"] = [{"label": "Path to the old milestone", "target_scene_id": "old_milestone"}]
    for ad in tavern["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "tavern"
    storage._save_json(storage.scene_path("tavern"), tavern)
    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    session = default_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    line = '"Farewell."'
    seg = segment_mixed_player_turn(line)
    assert maybe_build_declared_travel_action(
        seg,
        scene=tavern["scene"],
        session=session,
        world={},
        known_scene_ids={"tavern", "old_milestone"},
    ) is None

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("old_milestone"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": line})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "tavern"
    assert data.get("scene", {}).get("scene", {}).get("id") == "tavern"
    res = data.get("resolution") or {}
    assert res.get("kind") != "scene_transition"
    assert res.get("resolved_transition") is not True
    traces = data.get("debug_traces") or []
    assert traces
    dt = traces[-1].get("declared_travel_override") or {}
    assert dt.get("applied") is not True


def test_no_double_scene_switch_when_resolver_transition_and_gpt_proposal_both_present(tmp_path, monkeypatch):
    """Only one activation call occurs in a turn when both sources exist."""
    _seed_three_scenes(tmp_path, monkeypatch)
    activate_calls: list[str] = []

    def wrapped_activate(scene_id: str):
        activate_calls.append(scene_id)
        return storage.activate_scene(scene_id)

    with monkeypatch.context() as m:
        m.setattr("game.api.activate_scene", wrapped_activate)
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "exploration_action": {
                    "id": "go-b",
                    "label": "Go to B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to B.",
                },
            },
        )

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "scene_b"
    assert activate_calls == ["scene_b"]


def test_chat_mixed_farewell_and_declared_travel_overrides_dialogue_lock(tmp_path, monkeypatch):
    """Segmented declared movement must resolve as exploration scene_transition, not social_probe."""
    _patch_storage(tmp_path, monkeypatch)
    tavern = default_scene("frontier_gate")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["exits"] = [{"label": "Path to the old milestone", "target_scene_id": "old_milestone"}]
    for ad in tavern["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "tavern"
    storage._save_json(storage.scene_path("tavern"), tavern)

    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    session = default_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [{"id": "rumor", "text": "Patrols vanished.", "clue_id": "c1"}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    line = (
        '"Okay... I\'ll be on my way." Galinor leaves the runner for the old milestone.'
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": line})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    assert data.get("scene", {}).get("scene", {}).get("id") == "old_milestone"
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    assert res.get("kind") == "scene_transition"
    # GPT scene proposal is non-authoritative when resolver already moved.
    assert data.get("gm_output", {}).get("activate_scene_id") == "scene_c"


def test_actionable_lead_declared_travel_authoritative_arrival_and_lead_metadata(tmp_path, monkeypatch):
    """Pending lead unlocks destination; declared movement overrides dialogue lock; lead metadata persists."""
    _patch_storage(tmp_path, monkeypatch)
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["exits"] = [{"label": "Side alley", "target_scene_id": "waste"}]
    for ad in tavern["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "tavern"
    storage._save_json(storage.scene_path("tavern"), tavern)

    waste = default_scene("waste")
    waste["scene"]["id"] = "waste"
    storage._save_json(storage.scene_path("waste"), waste)

    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    session = default_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    upsert_lead(
        session,
        create_lead(
            id="ms_lead",
            title="Milestone rumor",
            summary="",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    rt = get_scene_runtime(session, "tavern")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "ms_lead",
            "text": "Investigate the old milestone",
            "leads_to_scene": "old_milestone",
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [{"id": "rumor", "text": "Patrols vanished.", "clue_id": "c1"}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    line = '"Farewell." Galinor heads to the old milestone.'

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": line})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    res = data.get("resolution") or {}
    assert res.get("kind") == "scene_transition"
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    md = res.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "ms_lead"
    assert md.get("declared_travel_override") is True
    assert md.get("declared_travel_dest_hint")
    assert md.get("declared_travel_pattern")
    assert md.get("committed_lead_id") == "ms_lead"
    row = get_lead(data.get("session") or {}, "ms_lead")
    assert row is not None
    assert (row.get("lifecycle") or "").lower() == "resolved"
    assert (row.get("resolution_type") or "").strip() == "reached_destination"


def test_known_scene_transition_blocked_no_scene_mutation(tmp_path, monkeypatch):
    """Resolver has explicit target_scene_id but graph has no path: authoritative non-transition."""
    _seed_three_scenes(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "March to scene_c",
                "exploration_action": {
                    "id": "march-c",
                    "label": "March to scene_c",
                    "type": "scene_transition",
                    "targetSceneId": "scene_c",
                    "prompt": "Galinor marches to scene_c.",
                },
            },
        )

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "scene_a"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_a"
    res = data.get("resolution") or {}
    assert res.get("kind") == "scene_transition"
    assert res.get("resolved_transition") is False
    assert res.get("target_scene_id") in (None, "")
    assert res.get("success") is False
    assert "not reachable" in (res.get("hint") or "").lower() or "do not imply arrival" in (
        res.get("hint") or ""
    ).lower()


def test_declared_travel_unresolved_movement_no_social_no_scene_change(tmp_path, monkeypatch):
    """Declared destination unknown: exploration travel lane, not social resolution; scene unchanged."""
    _patch_storage(tmp_path, monkeypatch)
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["exits"] = [{"label": "Local road", "target_scene_id": "waste"}]
    for ad in tavern["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "tavern"
    storage._save_json(storage.scene_path("tavern"), tavern)
    waste = default_scene("waste")
    waste["scene"]["id"] = "waste"
    storage._save_json(storage.scene_path("waste"), waste)

    session = default_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [{"id": "rumor", "text": "Patrols vanished.", "clue_id": "c1"}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    line = '"Farewell." Galinor heads to the lost citadel of Zyxnon.'

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: _gm_with_transition_proposal("scene_c"))
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": line})

    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "tavern"
    res = data.get("resolution") or {}
    assert res.get("kind") == "travel"
    assert res.get("resolved_transition") is False
    assert res.get("target_scene_id") in (None, "")
    assert res.get("social") is None
    assert "npc_id" not in res
    md = res.get("metadata") or {}
    assert md.get("declared_travel_override") is True
    assert md.get("declared_travel_dest_hint")
    ictx = (data.get("session") or {}).get("interaction_context") or {}
    assert ictx.get("active_interaction_target_id") in (None, "")
    assert ictx.get("interaction_mode") == "activity"
    assert (ictx.get("engagement_level") or "").strip().lower() != "engaged"
