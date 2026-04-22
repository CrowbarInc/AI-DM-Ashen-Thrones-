"""Prompt context consumes bounded world progression via CTIR-first seam."""
from __future__ import annotations

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from game.world import ensure_defaults
from game.world_progression import compose_ctir_world_progression_slice


def _base_kw():
    return {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 1,
            "visited_scene_ids": ["s1"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "look around",
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
    }


def _world_with_project():
    w = {
        "projects": [
            {
                "id": "q1",
                "name": "Quest",
                "category": "research",
                "status": "active",
                "progress": 2,
                "target": 10,
                "tags": [],
                "notes": "",
                "metadata": {},
            }
        ],
        "factions": [],
        "event_log": [],
        "world_state": {"flags": {}, "counters": {"side_noise": 5}, "clocks": {}},
    }
    ensure_defaults(w)
    return w


def test_prompt_prefers_ctir_progression_over_backbone_recompute():
    world = _world_with_project()
    session = dict(_base_kw()["session"])
    prog = compose_ctir_world_progression_slice(world, changed_node_ids=("project:q1",))
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="look around",
        builder_source="tests.wp",
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
    try:
        kw = _base_kw()
        kw["world"] = world
        kw["session"] = session
        kw["include_non_public_prompt_keys"] = True
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    pd = ctx.get("prompt_debug") or {}
    wp = pd.get("world_progression") or {}
    assert wp.get("read_source") == "ctir"
    summary = ctx.get("world_progression_summary") or []
    assert any("project q1" in str(line).lower() or "q1" in str(line) for line in summary)


def test_prompt_fallback_when_ctir_missing_uses_backbone_only():
    world = _world_with_project()
    session = dict(_base_kw()["session"])
    detach_ctir(session)
    kw = _base_kw()
    kw["world"] = world
    kw["session"] = session
    kw["include_non_public_prompt_keys"] = True
    ctx = build_narration_context(**kw)
    pd = ctx.get("prompt_debug") or {}
    wp = pd.get("world_progression") or {}
    assert wp.get("read_source") == "backbone_fallback"
    assert ctx.get("world_progression_summary")


def test_counters_do_not_appear_in_progression_summary_lines():
    world = _world_with_project()
    session = dict(_base_kw()["session"])
    detach_ctir(session)
    kw = _base_kw()
    kw["world"] = world
    kw["session"] = session
    kw["include_non_public_prompt_keys"] = True
    ctx = build_narration_context(**kw)
    blob = "\n".join(str(x) for x in (ctx.get("world_progression_summary") or []))
    assert "side_noise" not in blob


def test_compress_world_includes_progression_counts_not_counters_in_progression():
    world = _world_with_project()
    session = dict(_base_kw()["session"])
    detach_ctir(session)
    kw = _base_kw()
    kw["world"] = world
    kw["session"] = session
    kw["include_non_public_prompt_keys"] = True
    ctx = build_narration_context(**kw)
    cw = ctx.get("world") or {}
    pc = cw.get("progression_counts") or {}
    assert pc.get("active_projects", 0) >= 1
    assert "counters" not in pc
