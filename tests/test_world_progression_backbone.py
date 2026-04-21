"""Focused tests for ``game.world_progression`` (read model, writes, determinism)."""
from __future__ import annotations

import pytest

from game import world_progression as wp
from game.world import ensure_defaults


pytestmark = pytest.mark.unit


def _sample_world() -> dict:
    return {
        "projects": [
            {
                "id": "bridge",
                "name": "Bridge repair",
                "category": "infrastructure",
                "status": "active",
                "progress": 1,
                "target": 4,
                "tags": ["infra"],
                "notes": "",
                "metadata": {},
            }
        ],
        "factions": [
            {"id": "guild", "name": "Guild", "pressure": 2, "agenda_progress": 1},
        ],
        "world_state": {
            "flags": {"war_rumor": True, "quiet": False},
            "counters": {},
            "clocks": {
                "siege": {"id": "siege", "value": 3, "min_value": 0, "max_value": 8, "scope": "world", "metadata": {}},
            },
        },
        "event_log": [{"type": "faction_pressure", "text": "Pressure mounts", "source": "guild"}],
    }


def test_snapshot_covers_all_kinds_and_sorted_stable():
    w = _sample_world()
    ensure_defaults(w)
    a = wp.iter_world_progression_nodes(w)
    b = wp.iter_world_progression_nodes(w)
    assert a == b
    assert {n["kind"] for n in a} == {"faction_agenda", "faction_pressure", "project", "world_clock", "world_flag"}
    assert a == sorted(a, key=lambda n: (str(n["kind"]), str(n["id"])))


def test_no_duplicate_node_ids_duplicate_projects_skipped():
    w = {
        "projects": [
            {"id": "dup", "name": "A", "category": "research", "status": "active", "progress": 0, "target": 2},
            {"id": "dup", "name": "B", "category": "research", "status": "active", "progress": 5, "target": 2},
        ],
        "factions": [],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ensure_defaults(w)
    nodes = wp.iter_world_progression_nodes(w)
    assert len([n for n in nodes if n["kind"] == "project"]) == 1
    assert len({n["id"] for n in nodes}) == len(nodes)


def test_writes_project_to_native_projects():
    w = _sample_world()
    ensure_defaults(w)
    nid = "project:bridge"
    out = wp.advance_progression_node(w, nid, 1, reason="test")
    assert out is not None
    proj = next(p for p in w["projects"] if p["id"] == "bridge")
    assert proj["progress"] == 2
    assert "progression" in (w["event_log"][-1])
    assert w["event_log"][-1]["type"] == "world_progression"


def test_writes_faction_pressure_and_agenda():
    w = _sample_world()
    ensure_defaults(w)
    pid = wp.faction_pressure_node_id("guild")
    aid = wp.faction_agenda_node_id("guild")
    assert wp.advance_progression_node(w, pid, 2) is not None
    fac = w["factions"][0]
    assert fac["pressure"] == 4
    assert wp.set_progression_node_value(w, aid, 5) is not None
    assert fac["agenda_progress"] == 5


def test_writes_world_clock_native_root():
    w = _sample_world()
    ensure_defaults(w)
    cid = "world_clock:siege"
    assert wp.set_progression_node_value(w, cid, 7) is not None
    assert w["world_state"]["clocks"]["siege"]["value"] == 7


def test_writes_world_flag_native_root():
    w = _sample_world()
    ensure_defaults(w)
    fid = "world_flag:war_rumor"
    assert wp.set_progression_node_value(w, fid, False) is not None
    assert "war_rumor" not in w["world_state"]["flags"]


def test_apply_progression_delta_batch():
    w = _sample_world()
    ensure_defaults(w)
    buf: list = []
    res = wp.apply_progression_delta(
        w,
        {
            "ops": [
                {"op": "advance", "node_id": "project:bridge", "amount": 1},
                {"op": "set_value", "node_id": "world_flag:quiet", "value": True},
            ]
        },
        event_log=buf,
    )
    assert res["ok"] is True
    assert len(buf) == 2
    assert w["world_state"]["flags"]["quiet"] is True


def test_no_progression_shadow_key():
    w = _sample_world()
    ensure_defaults(w)
    wp.advance_progression_node(w, "project:bridge", 1)
    assert "progression" not in w


def test_session_clocks_not_included():
    w = _sample_world()
    session = {"clocks": {"suspicion": 9}}
    ensure_defaults(w)
    nodes = wp.iter_world_progression_nodes(w)
    assert not any("suspicion" in n["id"] for n in nodes)
    assert session["clocks"]["suspicion"] == 9


def test_invalid_malformed_project_skipped_deterministically():
    w = {
        "projects": [
            {
                "id": "p1",
                "name": "bad",
                "category": "research",
                "status": "active",
                "progress": "not-an-int",
                "target": 1,
            },
        ],
        "factions": [],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ensure_defaults(w)
    nodes = wp.iter_world_progression_nodes(w)
    assert all(n["kind"] != "project" for n in nodes)


def test_invalid_clock_row_skipped():
    w = {
        "projects": [],
        "factions": [],
        "world_state": {
            "flags": {},
            "counters": {},
            # Underscore keys are ignored (same hygiene as world_state merge paths).
            "clocks": {
                "_internal": {"id": "x", "value": 0, "min_value": 0, "max_value": 10, "scope": "world", "metadata": {}},
            },
        },
    }
    ensure_defaults(w)
    nodes = wp.iter_world_progression_nodes(w)
    assert all(n["kind"] != "world_clock" for n in nodes)


def test_invalid_node_id_returns_none_and_delta_fails():
    w = _sample_world()
    ensure_defaults(w)
    assert wp.advance_progression_node(w, "not_a_real_id", 1) is None
    assert wp.get_world_progression_node(w, "not_a_real_id") is None
    res = wp.apply_progression_delta(w, {"ops": [{"op": "advance", "node_id": "nope", "amount": 1}]})
    assert res["ok"] is False
    assert res["failed"]


def test_advance_world_flag_unsupported():
    w = _sample_world()
    ensure_defaults(w)
    assert wp.advance_progression_node(w, "world_flag:war_rumor", 1) is None


def test_snapshot_summary_and_bounded():
    w = _sample_world()
    ensure_defaults(w)
    snap = wp.build_world_progression_snapshot(w)
    assert "nodes" in snap and "summary" in snap and "recent_facts" in snap
    assert snap["summary"]["by_kind"]["project"] == 1
    assert len(snap["recent_facts"]) <= wp._MAX_RECENT_FACTS


def test_faction_node_helpers():
    assert wp.faction_pressure_node_id("guild") == "faction_pressure:guild"
    assert wp.faction_agenda_node_id("guild") == "faction_agenda:guild"


def test_progression_event_shape_stable_keys():
    ev = wp.progression_event(
        operation="advance",
        node_id="project:x",
        node_kind="project",
        text="t",
        reason="r",
    )
    assert list(ev.keys()) == ["type", "text", "progression"]
    assert list(ev["progression"].keys()) == ["operation", "node_id", "node_kind", "reason"]
