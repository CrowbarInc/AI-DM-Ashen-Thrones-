"""Integration: lead progression reconciliation runs on authoritative turn finalization only."""

from __future__ import annotations

import copy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from game import leads as leads_mod
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
from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    create_lead,
    resolve_lead,
)
from game.prompt_context import (
    build_authoritative_lead_prompt_context,
    build_narration_context,
)

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


def _seed_minimal_play(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
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
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _narration_minimal_kwargs(**overrides):
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {},
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "scene_investigate", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Look around.",
        "resolution": None,
        "scene_runtime": {},
        "public_scene": {"id": "scene_investigate", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    base.update(overrides)
    return base


# feature: leads
def test_chat_turn_advances_stale_lead_after_two_turns(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "a": create_lead(
            title="Tracked",
            summary="",
            id="a",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            stale_after_turns=2,
            first_discovered_turn=0,
        )
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        r1 = client.post("/api/chat", json={"text": "I glance around the room."})
        assert r1.status_code == 200
        reg1 = (r1.json().get("session") or {}).get(SESSION_LEAD_REGISTRY_KEY) or {}
        assert reg1.get("a", {}).get("status") == LeadStatus.ACTIVE.value

        r2 = client.post("/api/chat", json={"text": "I wait and watch."})
        assert r2.status_code == 200
        reg2 = (r2.json().get("session") or {}).get(SESSION_LEAD_REGISTRY_KEY) or {}
        assert reg2.get("a", {}).get("status") == LeadStatus.STALE.value


# feature: leads
def test_chat_turn_escalates_threat_lead(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 9
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "t": create_lead(
            title="Looming danger",
            summary="",
            id="t",
            type=LeadType.THREAT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            first_discovered_turn=0,
        )
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Another beat passes."})
    assert resp.status_code == 200
    reg = (resp.json().get("session") or {}).get(SESSION_LEAD_REGISTRY_KEY) or {}
    assert int(reg.get("t", {}).get("escalation_level") or 0) >= 1


# feature: leads
def test_post_chat_prompt_lead_context_reflects_reconciled_threat_escalation(tmp_path, monkeypatch):
    """After /api/chat finalization, prompt lead surfacing reads reconciled registry (no extra reconcile in prompt)."""
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 9
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "t": create_lead(
            title="Looming danger",
            summary="",
            id="t",
            type=LeadType.THREAT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            first_discovered_turn=0,
        )
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Another beat passes."})
    assert resp.status_code == 200

    after = storage.load_session()
    pc = build_authoritative_lead_prompt_context(
        after,
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    assert pc["follow_up_pressure_from_leads"]["has_escalated_threat"] is True
    t_row = next((r for r in pc["top_active_leads"] if r.get("id") == "t"), None)
    assert t_row is not None
    assert int(t_row.get("escalation_level") or 0) >= 1


# feature: leads
def test_prompt_context_builders_do_not_mutate_lead_registry():
    row = create_lead(
        title="R",
        summary="",
        id="r",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    session = {
        "active_scene_id": "scene_investigate",
        "turn_counter": 5,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {"r": row},
    }
    snap_before = copy.deepcopy(session[SESSION_LEAD_REGISTRY_KEY])
    build_authoritative_lead_prompt_context(
        session,
        world={},
        public_scene={},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    assert session[SESSION_LEAD_REGISTRY_KEY] == snap_before

    build_narration_context(**_narration_minimal_kwargs(session=session))
    assert session[SESSION_LEAD_REGISTRY_KEY] == snap_before


# feature: leads
def test_single_chat_request_calls_reconcile_once_despite_gpt_retries(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    reconcile_calls: list[int] = []
    orig = leads_mod.reconcile_session_lead_progression

    def counting_reconcile(sess, *, turn=None):
        reconcile_calls.append(1)
        return orig(sess, turn=turn)

    gpt_calls = {"n": 0}

    def counting_gpt(_msgs):
        gpt_calls["n"] += 1
        return FAKE_GPT_RESPONSE

    detect_calls = {"n": 0}

    def detect_then_clean(*args, **kwargs):
        detect_calls["n"] += 1
        if detect_calls["n"] == 1:
            return [{"failure_class": "scene_stall", "reasons": ["integration_force_retry"]}]
        return []

    with monkeypatch.context() as m:
        m.setattr("game.leads.reconcile_session_lead_progression", counting_reconcile)
        m.setattr("game.api.detect_retry_failures", detect_then_clean)
        m.setattr("game.api.call_gpt", counting_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I study the empty hall."})

    assert resp.status_code == 200
    assert gpt_calls["n"] >= 2
    assert len(reconcile_calls) == 1


# feature: leads
@patch("game.leads.reconcile_session_lead_progression")
def test_build_narration_context_twice_does_not_invoke_reconcile(mock_reconcile):
    row = create_lead(title="X", summary="", id="x")
    session = {
        "active_scene_id": "scene_investigate",
        "turn_counter": 1,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {"x": row},
    }
    kw = _narration_minimal_kwargs(session=session)
    build_narration_context(**kw)
    build_narration_context(**kw)
    mock_reconcile.assert_not_called()


# feature: leads — authoritative path + persisted / response alignment
def test_chat_single_reconcile_and_response_session_matches_disk(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 8
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "t": create_lead(
            title="Looming",
            summary="",
            id="t",
            type=LeadType.THREAT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            first_discovered_turn=0,
        )
    }
    storage._save_json(storage.SESSION_PATH, session)

    calls: list[int] = []
    orig = leads_mod.reconcile_session_lead_progression

    def counting(s, *, turn=None):
        calls.append(1)
        return orig(s, turn=turn)

    with monkeypatch.context() as m:
        m.setattr("game.leads.reconcile_session_lead_progression", counting)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Time passes."})

    assert resp.status_code == 200
    assert len(calls) == 1
    api_reg = (resp.json().get("session") or {}).get(SESSION_LEAD_REGISTRY_KEY) or {}
    disk_reg = (storage.load_session().get(SESSION_LEAD_REGISTRY_KEY) or {})
    assert api_reg.get("t", {}).get("escalation_level") == disk_reg.get("t", {}).get("escalation_level")
    traces = storage.load_session().get("debug_traces") or []
    assert traces
    tt = traces[-1].get("turn_trace") or {}
    assert isinstance(tt, dict) and tt.get("interaction_after") is not None


# feature: leads
def test_chat_threat_ranks_above_high_priority_rumor_in_prompt_slice(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 8
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "rumor": create_lead(
            title="Loose talk",
            summary="",
            id="rumor",
            type=LeadType.RUMOR,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=5,
            last_updated_turn=8,
            last_touched_turn=8,
            first_discovered_turn=0,
        ),
        "t": create_lead(
            title="Real danger",
            summary="",
            id="t",
            type=LeadType.THREAT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=0,
            first_discovered_turn=0,
        ),
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Another moment."})
    assert resp.status_code == 200

    after = storage.load_session()
    pc = build_authoritative_lead_prompt_context(
        after,
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    assert pc["top_active_leads"][0]["id"] == "t"
    assert pc["top_active_leads"][1]["id"] == "rumor"
    assert pc["follow_up_pressure_from_leads"]["has_escalated_threat"] is True


# feature: leads
def test_chat_resolved_parent_unlocks_hinted_child_to_discovered(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 3
    parent = resolve_lead(
        create_lead(title="Parent", summary="", id="parent", unlocks=["child"]),
        resolution_type="done",
        turn=2,
    )
    child = create_lead(title="Child", summary="", id="child", lifecycle=LeadLifecycle.HINTED)
    session[SESSION_LEAD_REGISTRY_KEY] = {"parent": parent, "child": child}
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I move on."})
    assert resp.status_code == 200

    reg = (storage.load_session().get(SESSION_LEAD_REGISTRY_KEY) or {})
    ch = reg.get("child") or {}
    assert ch.get("lifecycle") == LeadLifecycle.DISCOVERED.value
    assert ch.get("lifecycle") != LeadLifecycle.COMMITTED.value
    assert ch.get("unlocked_by_lead_id") == "parent"

    pc = build_authoritative_lead_prompt_context(
        storage.load_session(),
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    assert pc["follow_up_pressure_from_leads"]["has_newly_unlocked"] is True
    assert any(r["id"] == "child" for r in pc["top_active_leads"])


# feature: leads
def test_chat_supersession_removes_obsolete_from_prompt_emphasis_slices(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 4
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "newer": create_lead(title="New", summary="", id="newer", supersedes=["old_r"]),
        "old_r": create_lead(
            title="Old",
            summary="",
            id="old_r",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            superseded_by="newer",
            related_npc_ids=["npc_gate"],
        ),
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "News spreads."})
    assert resp.status_code == 200

    after = storage.load_session()
    assert (after.get(SESSION_LEAD_REGISTRY_KEY) or {}).get("old_r", {}).get("lifecycle") == LeadLifecycle.OBSOLETE.value

    pc = build_authoritative_lead_prompt_context(
        after,
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id="npc_gate",
    )
    assert pc["follow_up_pressure_from_leads"]["has_supersession_cleanup"] is True
    for bucket in ("top_active_leads", "urgent_or_stale_leads", "npc_relevant_leads"):
        assert all(r["id"] != "old_r" for r in pc[bucket])


# feature: leads
def test_chat_multi_effect_single_turn_prompt_contract(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 9
    parent = resolve_lead(
        create_lead(title="Src", summary="", id="src_u", unlocks=["child_u"]),
        resolution_type="done",
        turn=1,
    )
    child_u = create_lead(title="Ch", summary="", id="child_u", lifecycle=LeadLifecycle.HINTED)
    stale_me = create_lead(
        title="Stale thread",
        summary="",
        id="stale_me",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    threat_e = create_lead(
        title="Threat",
        summary="",
        id="threat_e",
        type=LeadType.THREAT,
        first_discovered_turn=0,
    )
    newer_m = create_lead(title="Newer", summary="", id="newer_m", supersedes=["old_m"])
    old_m = create_lead(
        title="Old rumor",
        summary="",
        id="old_m",
        lifecycle=LeadLifecycle.DISCOVERED,
        superseded_by="newer_m",
    )
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "src_u": parent,
        "child_u": child_u,
        "stale_me": stale_me,
        "threat_e": threat_e,
        "newer_m": newer_m,
        "old_m": old_m,
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Everything shifts at once."})
    assert resp.status_code == 200

    after = storage.load_session()
    pc = build_authoritative_lead_prompt_context(
        after,
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    p = pc["follow_up_pressure_from_leads"]
    assert p["has_stale"] and p["has_escalated_threat"] and p["has_newly_unlocked"] and p["has_supersession_cleanup"]
    assert any(r["id"] == "stale_me" for r in pc["urgent_or_stale_leads"])
    assert any(r["id"] == "threat_e" for r in pc["urgent_or_stale_leads"])
    for bucket in ("top_active_leads", "urgent_or_stale_leads"):
        assert all(r["id"] != "old_m" for r in pc[bucket])
    reg = after.get(SESSION_LEAD_REGISTRY_KEY) or {}
    assert reg.get("child_u", {}).get("lifecycle") == LeadLifecycle.DISCOVERED.value
    assert reg.get("old_m", {}).get("lifecycle") == LeadLifecycle.OBSOLETE.value


# feature: leads
def test_chat_stale_lead_surfaces_in_urgent_slice_after_threshold(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 1
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "a": create_lead(
            title="Tracked",
            summary="",
            id="a",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            stale_after_turns=2,
            first_discovered_turn=0,
        )
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        r1 = client.post("/api/chat", json={"text": "First beat."})
        assert r1.status_code == 200
        r2 = client.post("/api/chat", json={"text": "Second beat."})
        assert r2.status_code == 200

    after = storage.load_session()
    pc = build_authoritative_lead_prompt_context(
        after,
        world={},
        public_scene={"id": "scene_investigate"},
        runtime={},
        recent_log=[],
        active_npc_id=None,
    )
    assert any(r["id"] == "a" for r in pc["urgent_or_stale_leads"])
    assert any(r["id"] == "a" for r in pc["recent_lead_changes"])
    assert all(r["id"] != "a" for r in pc["top_active_leads"])
