"""CTIR ``world.progression`` projection from the world simulation backbone."""
from __future__ import annotations

from game import ctir
from game.ctir_runtime import build_runtime_ctir_for_narration
from game.world import ensure_defaults
from game.world_progression import (
    SESSION_PROGRESSION_FINGERPRINT_KEY,
    collect_changed_node_ids_from_resolution_signals,
    compose_ctir_world_progression_slice,
    merge_progression_changed_node_signals,
    progression_fingerprint_map,
    store_progression_fingerprint_on_session,
)


def _world(**kwargs):
    w = {
        "factions": kwargs.get("factions", []),
        "projects": kwargs.get("projects", []),
        "event_log": kwargs.get("event_log", []),
        "world_state": kwargs.get(
            "world_state",
            {"flags": {}, "counters": {}, "clocks": {}},
        ),
    }
    ensure_defaults(w)
    return w


def test_ctir_world_progression_bounded_ordering_and_no_full_world_mirror():
    world = _world(
        projects=[
            {
                "id": "b",
                "name": "B",
                "category": "research",
                "status": "active",
                "progress": 1,
                "target": 5,
                "tags": [],
                "notes": "",
                "metadata": {},
            },
            {
                "id": "a",
                "name": "A",
                "category": "research",
                "status": "active",
                "progress": 0,
                "target": 3,
                "tags": [],
                "notes": "",
                "metadata": {},
            },
        ],
        factions=[{"id": "guild", "name": "Guild", "pressure": 2, "agenda_progress": 1}],
        world_state={
            "flags": {"public_flag": True},
            "counters": {"noise": 99},
            "clocks": {"tension": {"id": "tension", "value": 3, "max_value": 10, "scope": "world"}},
        },
    )
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="look",
        builder_source="test",
        world={
            "events": [],
            "progression": compose_ctir_world_progression_slice(
                world, changed_node_ids=("project:a", "world_clock:tension")
            ),
        },
    )
    wct = c["world"]
    assert "progression" in wct
    prog = wct["progression"]
    ids = [p["id"] for p in prog["active_projects"]]
    assert ids == ["a", "b"]
    assert prog["faction_pressure"][0]["id"] == "guild"
    assert not any("noise" in str(x) for x in (prog, c))
    assert "counters" not in prog
    assert "world" not in c or "factions" not in c.get("world", {})


def test_build_runtime_ctir_includes_progression_without_event_log_world_progression():
    world = _world(
        projects=[
            {
                "id": "p1",
                "name": "P",
                "category": "research",
                "status": "active",
                "progress": 0,
                "target": 2,
                "tags": [],
                "notes": "",
                "metadata": {},
            }
        ],
        event_log=[],
    )
    session: dict = {}
    resolution = {
        "kind": "explore",
        "world_tick_events": [{"type": "faction_pressure", "text": "x", "source": "guild"}],
    }
    c = build_runtime_ctir_for_narration(
        turn_id=1,
        scene_id="s",
        player_input="go",
        builder_source="test",
        resolution=resolution,
        normalized_action=None,
        combat=None,
        session=session,
        world=world,
    )
    prog = c["world"]["progression"]
    assert isinstance(prog, dict)
    assert "faction_pressure:guild" in prog["changed_node_ids"]
    wp_rows = [e for e in world.get("event_log", []) if isinstance(e, dict) and e.get("type") == "world_progression"]
    assert wp_rows == []


def test_changed_nodes_merge_resolution_and_fingerprint():
    w1 = _world(
        projects=[
            {
                "id": "p1",
                "name": "P",
                "category": "research",
                "status": "active",
                "progress": 0,
                "target": 5,
                "tags": [],
                "notes": "",
                "metadata": {},
            }
        ],
    )
    session: dict = {}
    store_progression_fingerprint_on_session(session, w1)
    w2 = _world(
        projects=[
            {
                "id": "p1",
                "name": "P",
                "category": "research",
                "status": "active",
                "progress": 1,
                "target": 5,
                "tags": [],
                "notes": "",
                "metadata": {},
            }
        ],
    )
    res = {"set_flags": {"beacon": True}}
    merged = merge_progression_changed_node_signals(resolution=res, world=w2, session=session)
    assert "world_flag:beacon" in merged
    assert "project:p1" in merged


def test_collect_changed_node_ids_sorts_unique():
    r = {
        "advance_clocks": {"alpha": 1, "beta": 2},
        "world_tick_events": [{"type": "faction_operation_complete", "source": "f1"}],
    }
    out = collect_changed_node_ids_from_resolution_signals(r)
    assert out == sorted(out)
    assert "world_clock:alpha" in out
    assert "faction_agenda:f1" in out


def test_duplicate_faction_uid_world_iterator_stable_for_export():
    world = _world(
        factions=[
            {"pressure": 1, "agenda_progress": 0},
            {"pressure": 2, "agenda_progress": 0},
        ],
    )
    exp = compose_ctir_world_progression_slice(world)
    # Backbone dedupes by normalized uid; both rows share "unknown" uid — one visible pressure node.
    assert len(exp["faction_pressure"]) == 1


def test_fingerprint_key_constant_matches_store():
    session: dict = {}
    store_progression_fingerprint_on_session(session, _world())
    assert SESSION_PROGRESSION_FINGERPRINT_KEY in session
    assert isinstance(session[SESSION_PROGRESSION_FINGERPRINT_KEY], dict)


def test_progression_fingerprint_map_stable_keys():
    w = _world(factions=[{"id": "z", "name": "Z", "pressure": 0, "agenda_progress": 0}])
    m1 = progression_fingerprint_map(w)
    m2 = progression_fingerprint_map(w)
    assert m1 == m2
