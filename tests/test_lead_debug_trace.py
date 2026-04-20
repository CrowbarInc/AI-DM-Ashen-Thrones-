"""Compact turn trace: lead registry_debug and delta_after_reconcile (post-authoritative reconcile)."""

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
from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    _LEAD_DEBUG_COMPACT_ROW_KEYS,
    create_lead,
    resolve_lead,
)
from tests.debug_trace_utils import latest_compact_debug_trace_entry

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


def _last_turn_leads_section(tmp_path, monkeypatch) -> dict:
    traces = storage.load_session().get("debug_traces") or []
    assert traces, "expected debug_traces on session"
    tt = latest_compact_debug_trace_entry(traces).get("turn_trace") or {}
    sec = tt.get("leads")
    assert isinstance(sec, dict), "turn_trace.leads missing or not a dict"
    return sec


def _assert_compact_rows_bounded(rows: list) -> None:
    allowed = frozenset(_LEAD_DEBUG_COMPACT_ROW_KEYS)
    for row in rows:
        assert isinstance(row, dict)
        assert set(row.keys()) == allowed
        assert "metadata" not in row
        fx = row.get("last_progression_effects")
        assert fx is None or isinstance(fx, list)


# feature: leads — turn trace observability
def test_turn_trace_noop_reconcile_empty_delta(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I look around."})
    assert r.status_code == 200
    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    assert sec["delta_after_reconcile"] == []
    assert sec["changed_count"] == 0
    assert sec["registry_debug"] == []


def test_turn_trace_stale_decay_reason_in_delta(tmp_path, monkeypatch):
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
        r1 = client.post("/api/chat", json={"text": "First beat."})
        assert r1.status_code == 200
        r2 = client.post("/api/chat", json={"text": "Second beat."})
        assert r2.status_code == 200

    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    assert sec["changed_count"] == 1
    d = sec["delta_after_reconcile"]
    assert len(d) == 1 and d[0]["id"] == "a"
    assert d[0]["change_kind"] == "changed"
    assert d[0]["reason"] == "stale_decay"
    assert d[0]["category"] == "status_change"
    assert d[0]["after"].get("status") == LeadStatus.STALE.value


def test_turn_trace_escalation_progression_effects_list(tmp_path, monkeypatch):
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
        resp = client.post("/api/chat", json={"text": "Time passes."})
    assert resp.status_code == 200

    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    assert sec["changed_count"] >= 1
    d = sec["delta_after_reconcile"]
    hit = next(x for x in d if x["id"] == "t")
    assert hit["change_kind"] == "changed"
    eff = hit["after"].get("last_progression_effects")
    assert isinstance(eff, list)
    assert any(isinstance(x, str) and x.startswith("escalation:") for x in eff)

    reg = sec["registry_debug"]
    _assert_compact_rows_bounded(reg)
    row_t = next(r for r in reg if r["id"] == "t")
    assert isinstance(row_t["last_progression_effects"], list)


def test_turn_trace_unlock_shows_lifecycle_change(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 3
    src = resolve_lead(
        create_lead(title="S", summary="", id="src", unlocks=["tgt"]),
        resolution_type="done",
        turn=3,
    )
    tgt = create_lead(title="T", summary="", id="tgt", lifecycle=LeadLifecycle.HINTED)
    session[SESSION_LEAD_REGISTRY_KEY] = {"src": src, "tgt": tgt}
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "A quiet moment."})
    assert resp.status_code == 200

    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    d = sec["delta_after_reconcile"]
    hit = next(x for x in d if x["id"] == "tgt")
    assert hit["change_kind"] == "changed"
    assert hit["reason"] == "unlock_trigger"
    assert hit["category"] in ("lifecycle_change", "progression")
    assert hit["after"].get("lifecycle") == LeadLifecycle.DISCOVERED.value
    eff = hit["after"].get("last_progression_effects")
    assert isinstance(eff, list) and "unlock:apply" in eff


def test_turn_trace_supersession_obsolete_in_delta(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session["turn_counter"] = 2
    new_l = create_lead(title="New", summary="", id="newer", supersedes=["old_rumor"])
    old = create_lead(title="Old", summary="", id="old_rumor", superseded_by="newer")
    done_r = resolve_lead(
        create_lead(title="Done", summary="", id="done_rumor", superseded_by="newer"),
        resolution_type="confirmed",
        turn=1,
    )
    session[SESSION_LEAD_REGISTRY_KEY] = {"newer": new_l, "old_rumor": old, "done_rumor": done_r}
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Rumors settle."})
    assert resp.status_code == 200

    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    d = sec["delta_after_reconcile"]
    hit = next(x for x in d if x["id"] == "old_rumor")
    assert hit["change_kind"] == "changed"
    assert hit["reason"] == "superseded"
    assert hit["category"] == "lifecycle_change"
    assert hit["after"].get("lifecycle") == LeadLifecycle.OBSOLETE.value
    eff = hit["after"].get("last_progression_effects")
    assert isinstance(eff, list) and "supersession:apply" in eff


def test_turn_trace_registry_and_delta_ordering_deterministic(tmp_path, monkeypatch):
    _seed_minimal_play(tmp_path, monkeypatch)
    session = storage.load_session()
    session[SESSION_LEAD_REGISTRY_KEY] = {
        "z": create_lead(title="Z", summary="", id="z"),
        "a": create_lead(title="A", summary="", id="a"),
    }
    storage._save_json(storage.SESSION_PATH, session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Idle."})
    assert resp.status_code == 200

    sec = _last_turn_leads_section(tmp_path, monkeypatch)
    reg_ids = [r["id"] for r in sec["registry_debug"]]
    assert reg_ids == ["a", "z"]
    delta_ids = [x["id"] for x in sec["delta_after_reconcile"]]
    assert delta_ids == sorted(delta_ids)


def test_turn_trace_single_reconcile_still(tmp_path, monkeypatch):
    """Regression: one chat request must not double-call reconcile (via wrapped capture)."""
    _seed_minimal_play(tmp_path, monkeypatch)
    from game import leads as leads_mod

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
        resp = client.post("/api/chat", json={"text": "Ping."})
    assert resp.status_code == 200
    assert len(calls) == 1
