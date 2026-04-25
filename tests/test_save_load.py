"""Tests for save/load flow: persistence of active scene, clues, world flags, character name."""
from __future__ import annotations

import game.storage as st
from game.storage import (
    activate_scene,
    get_save_summary,
    get_runtime_scene_overlay,
    assert_canon_immutable,
    load_character,
    load_combat,
    load_log,
    load_active_scene,
    load_session,
    load_world,
    mark_clue_discovered,
    save_character,
    save_combat,
    save_session,
    save_world,
)
from game.world import apply_resolution_world_updates


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
    # Seed scenes
    from game.defaults import default_scene
    import json
    for sid in ("frontier_gate", "market_quarter"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def test_save_load_active_scene(tmp_path, monkeypatch):
    """Save then load returns same active scene."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    activate_scene("market_quarter")
    session = load_session()
    assert session["active_scene_id"] == "market_quarter"
    # Simulate reload
    session2 = load_session()
    assert session2["active_scene_id"] == "market_quarter"


def test_clues_persist_across_save_load(tmp_path, monkeypatch):
    """Discovered clues persist across save/load."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    mark_clue_discovered(session, "frontier_gate", "The tavern runner knows more.")
    mark_clue_discovered(session, "frontier_gate", "Bootprints lead toward the river.")
    save_session(session)
    session2 = load_session()
    rt = session2.get("scene_runtime", {}).get("frontier_gate", {})
    clues = rt.get("discovered_clues", [])
    assert "The tavern runner knows more." in clues
    assert "Bootprints lead toward the river." in clues
    overlay_clues = session2.get("runtime_scene_overlays", {}).get("frontier_gate", {}).get("discovered_clues", [])
    assert "The tavern runner knows more." in overlay_clues


def test_runtime_scene_overlay_persists_and_active_scene_merges_without_scene_file_write(tmp_path, monkeypatch):
    """Runtime scene facts live in session overlays; active scene reads return the merged view."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    overlay = get_runtime_scene_overlay(session, "frontier_gate")
    overlay["visible_facts_add"].append("A new runtime-only omen hangs over the gate.")
    save_session(session)

    canon = st.load_scene("frontier_gate")
    assert "A new runtime-only omen hangs over the gate." not in canon["scene"]["visible_facts"]

    effective = load_active_scene()
    assert "A new runtime-only omen hangs over the gate." in effective["scene"]["visible_facts"]
    assert not effective.get("_is_canon")


def test_loaded_canon_scene_is_marked_and_rejected_by_mutation_guard(tmp_path, monkeypatch):
    _setup_data_dir(tmp_path, monkeypatch)
    canon = st.load_scene("frontier_gate")

    assert canon.get("_is_canon") is True
    with pytest.raises(RuntimeError, match="Canonical scene mutation attempted"):
        assert_canon_immutable(canon)
    with pytest.raises(RuntimeError, match="Canonical scene mutation attempted"):
        st.save_scene(canon)


def test_world_flags_persist_across_save_load(tmp_path, monkeypatch):
    """World flags persist across save/load."""
    _setup_data_dir(tmp_path, monkeypatch)
    world = load_world()
    world.setdefault("world_state", {})
    world["world_state"].setdefault("flags", {})
    world["world_state"]["flags"]["patrol_route_known"] = True
    world["world_state"].setdefault("counters", {})
    world["world_state"]["counters"]["clues_found"] = 3
    save_world(world)
    world2 = load_world()
    assert world2["world_state"]["flags"].get("patrol_route_known") is True
    assert world2["world_state"]["counters"].get("clues_found") == 3


def test_character_player_name_persists(tmp_path, monkeypatch):
    """Character/player name persists across save/load."""
    _setup_data_dir(tmp_path, monkeypatch)
    character = load_character()
    character["name"] = "Elena Shadowmere"
    save_character(character)
    session = load_session()
    session["character_name"] = "Elena Shadowmere"
    save_session(session)
    character2 = load_character()
    session2 = load_session()
    assert character2["name"] == "Elena Shadowmere"
    assert session2.get("character_name") == "Elena Shadowmere"


def test_get_save_summary_returns_expected_shape(tmp_path, monkeypatch):
    """get_save_summary returns expected keys."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    session["active_scene_id"] = "frontier_gate"
    mark_clue_discovered(session, "frontier_gate", "A clue.")
    save_session(session)
    summary = get_save_summary()
    assert "saved_at" in summary
    assert "active_scene_id" in summary
    assert summary["active_scene_id"] == "frontier_gate"
    assert "chat_messages" in summary
    assert "discovered_clues" in summary
    assert summary["discovered_clues"] >= 1
    assert "world_flags_count" in summary
    assert "player_name" in summary
    assert "save_data_exists" in summary
