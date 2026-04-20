"""Objective 4 Block B — runtime boundary adoption of ``schema_contracts`` / models gateways."""
from __future__ import annotations

import pytest

from game import schema_contracts as sc
from game.exploration import resolve_exploration_action
from game.models import (
    apply_normalized_world_updates,
    normalize_runtime_engine_result,
    normalize_runtime_world_updates,
    resolution_world_updates_use_engine_apply_only,
)
from game.scene_actions import normalize_scene_action
from game.world import apply_resolution_world_updates, ensure_defaults

pytestmark = pytest.mark.unit


def test_normalize_runtime_engine_result_keeps_world_updates_plural_and_parks_unknown():
    raw = {
        "kind": "observe",
        "action_id": "a1",
        "label": "L",
        "prompt": "P",
        "success": None,
        "transition_applied": True,
        "target_scene_id": None,
        "clue_id": None,
        "discovered_clues": [],
        "world_update": {"set_flags": {"gate_open": True}},
        "state_changes": {},
        "hint": "",
        "orphan_key": 42,
    }
    n = normalize_runtime_engine_result(raw)
    assert "world_updates" in n
    assert n["world_updates"] == {"set_flags": {"gate_open": True}}
    assert n["resolved_transition"] is True
    assert n["metadata"]["unknown_legacy_keys"]["orphan_key"] == 42
    ok, reasons = sc.validate_engine_result(n)
    assert ok, reasons


def test_normalize_runtime_engine_result_transition_applied_only():
    n = normalize_runtime_engine_result(
        {
            "kind": "custom",
            "action_id": "x",
            "label": "L",
            "prompt": "P",
            "success": None,
            "target_scene_id": None,
            "clue_id": None,
            "discovered_clues": [],
            "state_changes": {},
            "hint": "",
            "transition_applied": True,
        }
    )
    assert n["resolved_transition"] is True


def test_resolution_world_updates_use_engine_apply_only_subset():
    assert resolution_world_updates_use_engine_apply_only({"set_flags": {"a": True}}) is True
    assert resolution_world_updates_use_engine_apply_only({"increment_counters": {"k": 1}}) is True
    assert resolution_world_updates_use_engine_apply_only({"set_flags": {}, "projects": []}) is False


def test_normalize_runtime_world_updates_gm_metadata_unknown():
    n = normalize_runtime_world_updates({"unexpected_gm": [1, 2], "append_events": []})
    assert "unexpected_gm" not in n
    assert n["metadata"]["unknown_legacy_keys"]["unexpected_gm"] == [1, 2]


def test_apply_normalized_world_updates_applies_legacy_increment_counters():
    world: dict = {"event_log": [], "projects": [], "clues": {}, "npcs": []}
    ensure_defaults(world)
    world["world_state"]["counters"]["heat"] = 1
    normalized = sc.adapt_legacy_world_update({"increment_counters": {"heat": 2}})
    apply_normalized_world_updates(world, normalized)
    assert world["world_state"]["counters"]["heat"] == 3


def test_apply_resolution_and_normalized_equivalent_for_pure_engine_fragment():
    w1: dict = {"event_log": [], "projects": [], "clues": {}, "npcs": []}
    w2: dict = {"event_log": [], "projects": [], "clues": {}, "npcs": []}
    ensure_defaults(w1)
    ensure_defaults(w2)
    frag = {"set_flags": {"x": True}, "increment_counters": {"n": 1}}
    apply_resolution_world_updates(w1, frag)
    assert resolution_world_updates_use_engine_apply_only(frag) is True
    apply_normalized_world_updates(w2, normalize_runtime_world_updates(frag))
    assert w1["world_state"]["flags"].get("x") is True
    assert w2["world_state"]["flags"].get("x") is True
    assert (w1["world_state"]["counters"].get("n") or 0) == (w2["world_state"]["counters"].get("n") or 0)


def test_exploration_resolve_then_runtime_engine_normalize_validates():
    scene = {"scene": {"id": "test", "location": "Here"}}
    action = normalize_scene_action(
        {"id": "observe-a", "label": "Observe the area", "type": "observe", "prompt": "Look around."}
    )
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="Look around.", list_scene_ids=lambda: [])
    n = normalize_runtime_engine_result(resolution)
    ok, reasons = sc.validate_engine_result(n)
    assert ok, reasons
    assert "world_updates" in n


def test_apply_normalized_world_updates_stores_canonical_clues_projects_clocks():
    world: dict = {"event_log": [], "projects": [], "clues": {}, "npcs": []}
    ensure_defaults(world)
    normalized = sc.normalize_world_update(
        {
            "append_events": [],
            "flags_patch": {},
            "counters_patch": {},
            "clocks_patch": {"heat": {"name": "heat", "progress": 1, "max": 6}},
            "projects_patch": [{"id": "p1", "name": "Bridge", "goal": 5, "progress": 0}],
            "clues_patch": {
                "c1": {
                    "text": "A scrap of parchment.",
                    "leads_to_scene": "old_milestone",
                    "type": "investigation",
                }
            },
            "npcs_patch": [],
            "leads_patch": [],
            "metadata": {},
        }
    )
    apply_normalized_world_updates(world, normalized)
    clk = world["world_state"]["clocks"]["heat"]
    assert clk["value"] == 1 and clk["max_value"] == 6 and "progress" not in clk
    proj = world["projects"][0]
    assert proj["target"] == 5 and "goal" not in proj
    clue = world["clues"]["c1"]
    assert clue["leads_to_scene_id"] == "old_milestone"
    assert "leads_to_scene" not in clue
    assert clue["metadata"].get("engine_lead_type") == "investigation"
