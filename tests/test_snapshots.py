"""Tests for snapshot/save-slot system: create, list, load, default persistence unchanged."""
from __future__ import annotations

import json

import game.storage as st
from game.defaults import (
    default_character,
    default_combat,
    default_scene,
    default_session,
    default_world,
)
from game.storage import (
    activate_scene,
    create_snapshot,
    list_snapshots,
    load_character,
    load_combat,
    load_log,
    load_session,
    load_snapshot,
    load_world,
    mark_clue_discovered,
    save_character,
    save_combat,
    save_session,
    save_world,
)


def _setup_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    monkeypatch.setattr(st, "SNAPSHOTS_DIR", st.DATA_DIR / "snapshots")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for sid in ("frontier_gate", "market_quarter"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def test_create_snapshot(tmp_path, monkeypatch):
    """create_snapshot captures current state and returns meta."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    session["active_scene_id"] = "market_quarter"
    session["turn_counter"] = 5
    save_session(session)
    world = load_world()
    world.setdefault("world_state", {})
    world["world_state"].setdefault("flags", {})
    world["world_state"]["flags"]["test_flag"] = True
    save_world(world)

    meta = create_snapshot(label="Before boss")
    assert "id" in meta
    assert "created_at" in meta
    assert meta["label"] == "Before boss"


def test_list_snapshots(tmp_path, monkeypatch):
    """list_snapshots returns created snapshots, newest first."""
    _setup_data_dir(tmp_path, monkeypatch)
    assert list_snapshots() == []

    create_snapshot(label="First")
    create_snapshot(label="Second")
    snaps = list_snapshots()
    assert len(snaps) == 2
    assert snaps[0]["label"] == "Second"  # newest first
    assert snaps[1]["label"] == "First"
    for s in snaps:
        assert "id" in s
        assert "created_at" in s


def test_load_snapshot_restores_state(tmp_path, monkeypatch):
    """load_snapshot overwrites session, world, combat, character, log with snapshot data."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    session["active_scene_id"] = "market_quarter"
    mark_clue_discovered(session, "frontier_gate", "A clue.")
    save_session(session)
    meta = create_snapshot(label="Checkpoint")

    # Change state
    session2 = load_session()
    session2["active_scene_id"] = "frontier_gate"
    save_session(session2)

    loaded_meta = load_snapshot(meta["id"])
    assert loaded_meta is not None
    assert loaded_meta["label"] == "Checkpoint"

    session3 = load_session()
    assert session3["active_scene_id"] == "market_quarter"
    rt = session3.get("scene_runtime", {}).get("frontier_gate", {})
    assert "A clue." in (rt.get("discovered_clues") or [])


def test_load_nonexistent_snapshot_returns_none(tmp_path, monkeypatch):
    """load_snapshot returns None for unknown id."""
    _setup_data_dir(tmp_path, monkeypatch)
    result = load_snapshot("nonexistent_id_12345")
    assert result is None


def test_default_save_load_still_works(tmp_path, monkeypatch):
    """Default persistence (session, world, etc.) is unchanged when snapshots are not used."""
    _setup_data_dir(tmp_path, monkeypatch)
    session = load_session()
    session["active_scene_id"] = "market_quarter"
    save_session(session)

    session2 = load_session()
    assert session2["active_scene_id"] == "market_quarter"

    # Create a snapshot but don't load it
    create_snapshot()
    session3 = load_session()
    assert session3["active_scene_id"] == "market_quarter"
