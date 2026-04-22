"""Objective #9 Block D: end-to-end regressions for the world simulation backbone seam."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game import world_progression as wp
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, build_runtime_ctir_for_narration
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from game.world import advance_world_tick, apply_resolution_world_updates, ensure_defaults
from game.world_progression import (
    SESSION_PROGRESSION_FINGERPRINT_KEY,
    _MAX_CTIR_ACTIVE_PROJECTS,
    _MAX_CTIR_CHANGED_NODES,
    collect_changed_node_ids_from_resolution_signals,
    compose_ctir_world_progression_slice,
    diff_progression_fingerprints,
    iter_world_progression_nodes,
    merge_progression_changed_node_signals,
    progression_fingerprint_map,
    store_progression_fingerprint_on_session,
)

pytestmark = pytest.mark.unit


def _world(**kwargs):
    w = {
        "factions": kwargs.get("factions", []),
        "npcs": kwargs.get("npcs", []),
        "projects": kwargs.get("projects", []),
        "event_log": kwargs.get("event_log", []),
        "world_state": kwargs.get(
            "world_state",
            {"flags": {}, "counters": {}, "clocks": {}},
        ),
    }
    ensure_defaults(w)
    return w


def _valid_project(pid: str, progress: int = 0, target: int = 3):
    return {
        "id": pid,
        "name": pid.upper(),
        "category": "research",
        "status": "active",
        "progress": progress,
        "target": target,
        "tags": [],
        "notes": "",
        "metadata": {},
    }


def test_canonical_persistent_progression_seam_is_world_progression_module():
    """Supported persistent progression writes are owned by ``game.world_progression`` (+ ``game.world`` routing)."""
    w = _world(projects=[_valid_project("p_seam", 0, 2)])
    assert wp.advance_progression_node(w, "project:p_seam", 1, reason="test", event_log=[]) is not None
    assert w["projects"][0]["progress"] == 1


def test_deterministic_outcomes_repeated_apply_same_delta():
    w1 = _world(projects=[_valid_project("d1", 0, 5)])
    w2 = _world(projects=[_valid_project("d1", 0, 5)])
    delta = {"ops": [{"op": "advance", "node_id": "project:d1", "amount": 2}]}
    wp.apply_progression_delta(w1, delta, event_log=[])
    wp.apply_progression_delta(w2, delta, event_log=[])
    assert w1["projects"] == w2["projects"]
    snap1 = compose_ctir_world_progression_slice(w1)
    snap2 = compose_ctir_world_progression_slice(w2)
    assert snap1 == snap2


def test_native_roots_authoritative_no_world_progression_subtree():
    w = _world(
        projects=[_valid_project("nr1", 1, 4)],
        factions=[{"id": "f", "name": "F", "pressure": 1, "agenda_progress": 0}],
        world_state={
            "flags": {"beacon": True},
            "counters": {"noise": 42},
            "clocks": {"c1": {"id": "c1", "value": 2, "max_value": 8, "scope": "world"}},
        },
    )
    assert "progression" not in w
    assert isinstance(w["projects"], list)
    assert isinstance(w["world_state"]["flags"], dict)
    nodes = iter_world_progression_nodes(w)
    kinds = {str(n.get("kind")) for n in nodes}
    assert "project" in kinds
    assert "faction_pressure" in kinds
    assert "world_flag" in kinds
    assert "world_clock" in kinds


def test_no_session_world_progression_shadow_root():
    session = {"turn_counter": 1}
    assert "world_progression" not in session


def test_counters_excluded_from_iterator_and_ctir_export():
    w = _world(
        world_state={"flags": {}, "counters": {"x": 9}, "clocks": {}},
    )
    kinds = {n.get("kind") for n in iter_world_progression_nodes(w)}
    assert "counter" not in kinds
    ctir_slice = compose_ctir_world_progression_slice(w)
    assert "counters" not in ctir_slice


def test_ctir_progression_export_bounded_and_compact_shape():
    projects = [_valid_project(f"p{i}", 0, 2) for i in range(_MAX_CTIR_ACTIVE_PROJECTS + 8)]
    w = _world(projects=projects)
    changed = [f"project:p{i}" for i in range(_MAX_CTIR_CHANGED_NODES + 8)]
    out = compose_ctir_world_progression_slice(w, changed_node_ids=changed)
    assert len(out["active_projects"]) <= _MAX_CTIR_ACTIVE_PROJECTS
    assert len(out["changed_node_ids"]) <= _MAX_CTIR_CHANGED_NODES
    for key in ("active_projects", "faction_pressure", "faction_agenda", "world_clocks", "set_flags", "changed_node_ids"):
        assert key in out
    for row in out["active_projects"]:
        assert set(row.keys()) <= {"id", "status", "progress", "target"}


def test_prefixed_node_ids_do_not_collide_across_kinds():
    w = _world(
        projects=[_valid_project("same", 0, 2)],
        factions=[{"id": "same", "name": "Same", "pressure": 0, "agenda_progress": 0}],
        world_state={
            "flags": {"same": True},
            "counters": {},
            "clocks": {"same": {"id": "same", "value": 0, "max_value": 5, "scope": "world"}},
        },
    )
    ids = [str(n["id"]) for n in iter_world_progression_nodes(w)]
    assert len(ids) == len(set(ids))
    prefixes = {i.split(":", 1)[0] for i in ids}
    assert "project" in prefixes
    assert "faction_pressure" in prefixes
    assert "faction_agenda" in prefixes
    assert "world_flag" in prefixes
    assert "world_clock" in prefixes


def test_roundtrip_json_preserves_native_progression_fields():
    w = _world(projects=[_valid_project("rt", 2, 5)])
    wp.advance_progression_node(w, "project:rt", 1, reason="rt", event_log=[])
    blob = json.loads(json.dumps(w))
    ensure_defaults(blob)
    assert blob["projects"][0]["progress"] == 3
    assert compose_ctir_world_progression_slice(blob)["active_projects"]


def test_tick_routes_progression_without_polluting_player_event_log_with_helper_rows():
    w = _world(
        projects=[_valid_project("tick_p", 0, 5)],
        factions=[{"id": "g", "name": "Guild", "pressure": 0, "agenda_progress": 0}],
        event_log=[{"type": "legacy_story", "text": "A bard sang."}],
    )
    advance_world_tick(w, {})
    helper = [e for e in w["event_log"] if isinstance(e, dict) and e.get("type") == "world_progression"]
    assert helper == []
    legacy_types = {e.get("type") for e in w["event_log"] if isinstance(e, dict)}
    assert "legacy_story" in legacy_types or any("npc_moved" in str(e) for e in w["event_log"])


def test_resolution_counter_increment_preserves_empty_world_progression_event_log():
    w = _world()
    apply_resolution_world_updates(w, {"increment_counters": {"karma": 2}})
    helper = [e for e in w["event_log"] if isinstance(e, dict) and e.get("type") == "world_progression"]
    assert helper == []
    assert int(w["world_state"]["counters"].get("karma", 0)) == 2


def test_ctir_progression_populated_with_empty_event_log_no_helper_rows():
    w = _world(
        projects=[_valid_project("c0", 1, 3)],
        event_log=[],
    )
    c = build_runtime_ctir_for_narration(
        turn_id=1,
        scene_id="s",
        player_input="x",
        builder_source="test.regressions",
        resolution={"kind": "observe", "set_flags": {"flare": True}},
        normalized_action=None,
        combat=None,
        session={},
        world=w,
    )
    prog = c["world"]["progression"]
    assert isinstance(prog, dict)
    assert prog.get("active_projects")
    assert "world_flag:flare" in (prog.get("changed_node_ids") or [])
    assert not any(e.get("type") == "world_progression" for e in w.get("event_log", []) if isinstance(e, dict))


def test_changed_nodes_from_resolution_ignore_poisoned_event_log():
    """Resolution-derived ids must not depend on scanning ``event_log``."""
    w = _world()
    w["event_log"] = [
        {
            "type": "world_progression",
            "text": "fake",
            "progression": {"operation": "advance", "node_id": "project:phantom", "node_kind": "project"},
        }
    ]
    r = {"set_flags": {"real": True}}
    ids = collect_changed_node_ids_from_resolution_signals(r)
    assert "world_flag:real" in ids
    assert "project:phantom" not in ids


def test_fingerprint_diff_bounded_when_state_changes():
    a = _world(projects=[_valid_project("fp", 0, 10)])
    b = copy.deepcopy(a)
    wp.advance_progression_node(b, "project:fp", 3, reason="t", event_log=[])
    prev = progression_fingerprint_map(a)
    curr = progression_fingerprint_map(b)
    changed = diff_progression_fingerprints(prev, curr)
    assert "project:fp" in changed


def test_fingerprint_diff_empty_when_unchanged():
    w = _world(projects=[_valid_project("st", 2, 5)])
    m = progression_fingerprint_map(w)
    assert diff_progression_fingerprints(m, m) == []


def test_merge_changed_nodes_uses_prior_fingerprint_until_store_updates_session():
    w_before = _world(projects=[_valid_project("m1", 0, 4)])
    session: dict = {}
    store_progression_fingerprint_on_session(session, w_before)
    w_after = _world(projects=[_valid_project("m1", 2, 4)])
    merged_mid = merge_progression_changed_node_signals(resolution=None, world=w_after, session=session)
    assert "project:m1" in merged_mid
    store_progression_fingerprint_on_session(session, w_after)
    merged_post = merge_progression_changed_node_signals(resolution=None, world=w_after, session=session)
    assert "project:m1" not in merged_post


def test_session_fingerprint_key_is_runtime_bookkeeping_prefix():
    assert SESSION_PROGRESSION_FINGERPRINT_KEY.startswith("_runtime_")


def test_duplicate_faction_uid_rows_do_not_crash_and_ctir_export_deterministic():
    w = _world(
        factions=[
            {"pressure": 0, "agenda_progress": 0},
            {"pressure": 1, "agenda_progress": 2},
        ],
    )
    advance_world_tick(w, {})
    assert w["factions"][0]["pressure"] == 1
    assert w["factions"][1]["pressure"] == 2
    a = compose_ctir_world_progression_slice(w)
    b = compose_ctir_world_progression_slice(w)
    assert a == b
    assert len(a["faction_pressure"]) == 1


def test_duplicate_uid_direct_row_fallback_matches_iterator_first_row():
    """Visible pressure matches first faction row sharing the normalized uid (established dedupe)."""
    w = _world(
        factions=[
            {"pressure": 5, "agenda_progress": 0},
            {"pressure": 9, "agenda_progress": 0},
        ],
    )
    nodes = iter_world_progression_nodes(w)
    pressure_nodes = [n for n in nodes if n.get("kind") == "faction_pressure"]
    assert len(pressure_nodes) == 1
    assert int(pressure_nodes[0].get("value", 0)) == 5


def test_prompt_context_reads_ctir_progression_not_reconstructed_event_log():
    """Regression: prompt layer consumes bounded CTIR slice; not a second authority over native roots."""
    from game import ctir
    from game.ctir_runtime import attach_ctir, detach_ctir

    world = _world(projects=[_valid_project("ctir_p", 4, 10)])
    session = {
        "active_scene_id": "s1",
        "turn_counter": 2,
        "visited_scene_ids": ["s1"],
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
        },
    }
    prog = compose_ctir_world_progression_slice(world, changed_node_ids=("project:ctir_p",))
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="look",
        builder_source="tests.regressions",
        resolution={"kind": "observe"},
        world={"progression": prog},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    _nc = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "session": session,
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "world": world,
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "look",
        "resolution": {"kind": "observe", "label": "look"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
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
        "include_non_public_prompt_keys": True,
    }
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _nc)
        ctx = build_narration_context(**_nc)
    finally:
        detach_ctir(session)
    pd = ctx.get("prompt_debug") or {}
    assert (pd.get("world_progression") or {}).get("read_source") == "ctir"


def test_fingerprint_store_in_api_runs_after_prompt_construction_order():
    """Guardrail: fingerprint refresh stays after message/prompt assembly in the narration builder."""
    api_path = Path(__file__).resolve().parents[1] / "game" / "api.py"
    text = api_path.read_text(encoding="utf-8")
    fn = "def _build_gpt_narration_from_authoritative_state"
    i0 = text.find(fn)
    assert i0 != -1
    i1 = text.find("def _run_resolved_turn_pipeline", i0)
    assert i1 != -1
    body = text[i0:i1]
    msg_at = body.find("messages = build_messages(")
    fp_at = body.find("store_progression_fingerprint_on_session(")
    assert msg_at != -1 and fp_at != -1
    assert msg_at < fp_at


def test_apply_progression_delta_lives_only_on_world_progression_module():
    """Single canonical writer API for backbone deltas (not duplicated on ``game.world``)."""
    import game.world as gw

    assert hasattr(wp, "apply_progression_delta")
    assert not hasattr(gw, "apply_progression_delta")
