"""Tests for world_state flags, counters, and clocks."""
from game.storage import (
    get_world_flag,
    set_world_flag,
    increment_world_counter,
    advance_world_clock,
    load_world,
    save_world,
)
from game.world import (
    advance_world_tick,
    apply_resolution_world_updates,
    apply_world_updates,
    ensure_defaults,
    upsert_world_npc,
)


import pytest

pytestmark = pytest.mark.unit

def test_set_world_flag_persists():
    """Setting a flag updates the world dict and persists via save/load."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    assert get_world_flag(world, "alliance_sealed") is None
    set_world_flag(world, "alliance_sealed", True)
    assert get_world_flag(world, "alliance_sealed") is True
    set_world_flag(world, "quest_giver", "merchant_marcus")
    assert get_world_flag(world, "quest_giver") == "merchant_marcus"


def test_flags_persist_via_save_load(tmp_path, monkeypatch):
    """Flags persist when saved to disk and loaded back."""
    import game.storage as st

    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)

    world = load_world()
    set_world_flag(world, "war_declared", True)
    save_world(world)

    world2 = load_world()
    assert get_world_flag(world2, "war_declared") is True


def test_increment_world_counter():
    """Counters increment correctly and return new value."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    v1 = increment_world_counter(world, "kills", 1)
    assert v1 == 1
    v2 = increment_world_counter(world, "kills", 3)
    assert v2 == 4
    assert world["world_state"]["counters"]["kills"] == 4


def test_increment_world_counter_persists(tmp_path, monkeypatch):
    """Counter increments persist via save/load."""
    import game.storage as st

    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)

    world = load_world()
    increment_world_counter(world, "patrols_defeated", 5)
    save_world(world)

    world2 = load_world()
    assert world2["world_state"]["counters"]["patrols_defeated"] == 5


def test_advance_world_clock_advances_and_clamps():
    """Clocks advance by amount and clamp to max."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    p1 = advance_world_clock(world, "sahuagin_war", 2)
    assert p1 == 2
    c = world["world_state"]["clocks"]["sahuagin_war"]
    assert c["id"] == "sahuagin_war" and c["value"] == 2 and c["max_value"] == 10 and c["scope"] == "world"

    # Advance more
    p2 = advance_world_clock(world, "sahuagin_war", 5)
    assert p2 == 7

    # Clamp to max: advance past max
    p3 = advance_world_clock(world, "sahuagin_war", 10)
    assert p3 == 10
    assert world["world_state"]["clocks"]["sahuagin_war"]["value"] == 10
    assert world["world_state"]["clocks"]["sahuagin_war"]["max_value"] == 10


def test_advance_world_clock_with_custom_max():
    """Clock can be initialized with custom max via world_updates, then advanced."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    ensure_defaults(world)
    apply_world_updates(world, {
        "world_state": {
            "clocks": {"invasion": {"progress": 0, "max": 8}},
        },
    })
    assert world["world_state"]["clocks"]["invasion"]["max_value"] == 8

    p1 = advance_world_clock(world, "invasion", 3)
    assert p1 == 3
    p2 = advance_world_clock(world, "invasion", 10)  # would go to 13, clamped to 8
    assert p2 == 8


def test_gm_world_state_updates_apply():
    """GM world_updates.world_state merges flags, counters, clocks."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    ensure_defaults(world)

    apply_world_updates(world, {
        "world_state": {
            "flags": {"quest_started": True},
            "counters": {"clues_found": 2},
            "clocks": {"sahuagin_war": {"progress": 2, "max": 8}},
        },
    })

    assert get_world_flag(world, "quest_started") is True
    assert world["world_state"]["counters"]["clues_found"] == 2
    assert world["world_state"]["clocks"]["sahuagin_war"]["value"] == 2
    assert world["world_state"]["clocks"]["sahuagin_war"]["max_value"] == 8


def test_hidden_keys_excluded_from_gm_updates():
    """Keys starting with _ are not applied from world_state updates."""
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    ensure_defaults(world)
    # world.py _apply_world_state_updates skips _ keys
    apply_world_updates(world, {
        "world_state": {
            "flags": {"_internal": "secret", "public": "visible"},
        },
    })
    assert get_world_flag(world, "_internal") is None
    assert get_world_flag(world, "public") == "visible"


def test_upsert_world_npc_world_state_owner_path():
    world: dict = {"npcs": [], "world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    ensure_defaults(world)
    rec = upsert_world_npc(
        world,
        {
            "id": "test_npc_authority",
            "name": "Authority NPC",
            "location": "frontier_gate",
            "topics": [],
        },
    )
    assert rec.get("id") == "test_npc_authority"
    assert any(n.get("id") == "test_npc_authority" for n in world.get("npcs", []) if isinstance(n, dict))


def test_apply_resolution_world_updates_merges_flags_and_counters():
    world: dict = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    ensure_defaults(world)
    apply_resolution_world_updates(
        world,
        {
            "set_flags": {"resolved_probe": True},
            "increment_counters": {"ticks": 2},
        },
    )
    assert world["world_state"]["flags"].get("resolved_probe") is True
    assert world["world_state"]["counters"].get("ticks") == 2


def test_advance_world_tick_advances_under_world_state_owner():
    world: dict = {
        "npcs": [],
        "factions": [{"id": "f_test", "name": "Test Faction", "pressure": 0, "agenda_progress": 0}],
        "projects": [],
        "event_log": [],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ensure_defaults(world)
    out = advance_world_tick(world, {})
    assert "world" in out
    assert isinstance(out.get("events"), list)
