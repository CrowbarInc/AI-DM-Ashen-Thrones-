"""New Campaign hard reset: session root replacement, world runtime clear, log empty."""
from __future__ import annotations

import json

import game.storage as st
from game.campaign_reset import apply_new_campaign_hard_reset
from game.campaign_state import create_fresh_combat_state, create_fresh_session_document
from game.defaults import default_world
from game.fresh_campaign_verify import collect_fresh_campaign_violations
from game.storage import load_log, load_session, load_world, save_session, save_world


import pytest

pytestmark = pytest.mark.integration

def _setup_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    from game.defaults import default_scene

    for sid in ("frontier_gate", "market_quarter"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def test_apply_new_campaign_hard_reset_clears_runtime_and_rotates_run_id(tmp_path, monkeypatch):
    _setup_data_dir(tmp_path, monkeypatch)

    session = load_session()
    session["scene_runtime"] = {"frontier_gate": {"discovered_clues": ["x"], "searched_targets": ["t"]}}
    session["clue_knowledge"] = {"k1": {"state": "discovered", "text": "secret"}}
    session["legacy_leak"] = True
    rid_before = session.get("campaign_run_id")
    save_session(session)

    world = load_world()
    world.setdefault("world_state", {}).setdefault("flags", {})["old"] = True
    world.setdefault("event_log", []).append({"type": "test", "text": "happened"})
    world.setdefault("projects", []).append({"id": "p1", "name": "P", "status": "active", "progress": 1, "target": 5})
    save_world(world)

    st.SESSION_LOG_PATH.write_text(json.dumps({"x": 1}) + "\n", encoding="utf-8")

    meta = apply_new_campaign_hard_reset()
    assert meta.get("campaign_run_id")
    assert meta.get("session_id") == meta.get("campaign_run_id")

    session2 = load_session()
    assert "legacy_leak" not in session2
    assert session2.get("scene_runtime") == {}
    assert session2.get("clue_knowledge") == {}
    assert session2["campaign_run_id"] != rid_before

    world2 = load_world()
    assert world2.get("event_log") == []
    assert world2.get("projects") == []
    assert world2.get("world_state", {}).get("flags") == {}

    assert load_log() == []


def test_world_factions_resync_to_template_defaults(tmp_path, monkeypatch):
    _setup_data_dir(tmp_path, monkeypatch)
    world = load_world()
    for fac in world.get("factions", []) or []:
        if isinstance(fac, dict) and fac.get("id") == "house_verevin":
            fac["pressure"] = 99
            fac["agenda_progress"] = 99
    save_world(world)

    apply_new_campaign_hard_reset()
    world2 = load_world()
    template = default_world()
    t_by_id = {f["id"]: f for f in template["factions"] if isinstance(f, dict)}
    for fac in world2.get("factions", []) or []:
        if isinstance(fac, dict) and fac.get("id") == "house_verevin":
            assert fac["pressure"] == t_by_id["house_verevin"]["pressure"]
            assert fac["agenda_progress"] == t_by_id["house_verevin"]["agenda_progress"]


def test_dev_verify_reports_clean_after_contaminated_reset(tmp_path, monkeypatch):
    """Runtime fields cleared; dev verification passes when ASHEN_THRONES_DEV_VERIFY=1."""
    monkeypatch.setenv("ASHEN_THRONES_DEV_VERIFY", "1")
    _setup_data_dir(tmp_path, monkeypatch)

    session = load_session()
    session["interaction_context"]["active_interaction_target_id"] = "guard_captain"
    session["interaction_context"]["interaction_mode"] = "social"
    session["scene_state"]["current_interlocutor"] = "guard_captain"
    session["scene_runtime"] = {
        "frontier_gate": {
            "topic_pressure": {"t": {"repeat_count": 3}},
            "momentum_exchanges_since": 2,
            "passive_action_streak": 1,
        }
    }
    session["campaign_run_id"] = "stale_run"
    save_session(session)

    world = load_world()
    world.setdefault("event_log", []).append({"type": "x", "text": "y"})
    save_world(world)

    meta = apply_new_campaign_hard_reset()
    assert meta.get("dev_verify_ok") is True
    assert meta.get("dev_verify_violations") == []


def test_collect_violations_flags_stale_interaction_lock():
    s = create_fresh_session_document()
    s["interaction_context"]["active_interaction_target_id"] = "npc_x"
    w = default_world()
    c = create_fresh_combat_state()
    v = collect_fresh_campaign_violations(s, w, c, log_entries=[])
    assert any("active_interaction_target_id" in msg for msg in v)


def test_new_campaign_replaces_nested_references_no_alias(tmp_path, monkeypatch):
    """Stale session-scoped nested dicts must not be reused after root replacement."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    contaminated = {"frontier_gate": {"topic_pressure": {"k": {}}}}
    session["scene_runtime"] = contaminated
    prior_run = session["campaign_run_id"]
    save_session(session)

    apply_new_campaign_hard_reset()

    s2 = load_session()
    assert s2["scene_runtime"] is not contaminated
    assert s2["scene_runtime"] == {}
    assert s2["campaign_run_id"] != prior_run
