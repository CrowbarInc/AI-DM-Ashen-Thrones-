"""Unit tests for ``game.schema_contracts`` (Objective 4 schema foundation)."""
from __future__ import annotations

import pytest

from game import schema_contracts as sc
from game.exploration import resolve_exploration_action
from game.scene_actions import normalize_scene_action


pytestmark = pytest.mark.unit


# --- Shared toolkit ---


def test_clean_optional_str():
    assert sc.clean_optional_str("  x  ") == "x"
    assert sc.clean_optional_str("") is None
    assert sc.clean_optional_str("   ") is None
    assert sc.clean_optional_str(3) is None


def test_normalize_enum():
    allowed = frozenset({"a", "b"})
    assert sc.normalize_enum("A", allowed, fallback="b") == "a"
    assert sc.normalize_enum("nope", allowed, fallback="b") == "b"


def test_normalize_str_list_and_id():
    assert sc.normalize_str_list([" a ", "", "b"]) == ["a", "b"]
    assert sc.normalize_str_list(None) == []
    assert sc.normalize_id("  nid ") == "nid"
    assert sc.normalize_id(True) is None


def test_drop_unknown_keys_parks_in_metadata():
    meta: dict = {}
    raw = {"keep": 1, "drop_me": 2}
    out = sc.drop_unknown_keys(raw, frozenset({"keep"}), park_unknown_in_metadata=True, metadata_target=meta)
    assert out == {"keep": 1}
    assert meta["unknown_legacy_keys"] == {"drop_me": 2}


# --- Engine result ---


def test_normalize_engine_result_parks_unknown_top_level():
    raw = {
        "kind": "observe",
        "action_id": "a1",
        "label": "L",
        "prompt": "P",
        "success": None,
        "resolved_transition": False,
        "target_scene_id": None,
        "clue_id": None,
        "discovered_clues": [],
        "world_updates": None,
        "state_changes": {},
        "hint": "",
        "weird_legacy": {"x": 1},
    }
    n = sc.normalize_engine_result(raw)
    assert "weird_legacy" not in n
    assert n["metadata"]["unknown_legacy_keys"]["weird_legacy"] == {"x": 1}


def test_validate_engine_result_missing_required():
    ok, reasons = sc.validate_engine_result({"kind": "k"})
    assert ok is False
    assert any("missing_required" in r for r in reasons)


def test_validate_engine_result_unknown_key():
    ok, reasons = sc.validate_engine_result(
        {
            "kind": "observe",
            "action_id": "a",
            "label": "l",
            "prompt": "p",
            "success": None,
            "resolved_transition": False,
            "target_scene_id": None,
            "clue_id": None,
            "discovered_clues": [],
            "world_updates": None,
            "state_changes": {},
            "hint": "",
            "bogus": 1,
        }
    )
    assert ok is False
    assert any("unknown_key:bogus" in r for r in reasons)


def test_adapt_legacy_engine_result_world_update_singular():
    n = sc.adapt_legacy_engine_result(
        {
            "kind": "custom",
            "action_id": "x",
            "label": "L",
            "prompt": "P",
            "success": None,
            "resolved_transition": False,
            "target_scene_id": None,
            "clue_id": None,
            "discovered_clues": [],
            "state_changes": {},
            "hint": "",
            "world_update": {"set_flags": {"a": True}},
        }
    )
    assert n["world_updates"] == {"set_flags": {"a": True}}
    ok, _ = sc.validate_engine_result(n)
    assert ok


def test_exploration_resolution_still_validates_after_normalize():
    scene = {"scene": {"id": "test", "location": "Here"}}
    action = normalize_scene_action(
        {"id": "observe-a", "label": "Observe the area", "type": "observe", "prompt": "Look around."}
    )
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="Look around.", list_scene_ids=lambda: [])
    normalized = sc.normalize_engine_result(resolution)
    ok, reasons = sc.validate_engine_result(normalized)
    assert ok, reasons
    assert sc.is_canonical_engine_result(normalized)


# --- World update ---


def test_normalize_world_update_parks_unknown():
    wu = sc.normalize_world_update({"append_events": [], "flags_patch": {}, "not_allowed": 99})
    assert "not_allowed" not in wu
    assert wu["metadata"]["unknown_legacy_keys"]["not_allowed"] == 99


def test_adapt_legacy_world_update_gm_shape():
    adapted = sc.adapt_legacy_world_update(
        {
            "append_events": ["hello"],
            "projects": [{"id": "p1", "name": "Bridge", "progress": 1, "target": 4}],
            "world_state": {"flags": {"f": True}, "counters": {"c": 2}, "clocks": {"clock_a": {"progress": 1, "max": 5}}},
        }
    )
    assert adapted["flags_patch"] == {"f": True}
    assert adapted["counters_patch"] == {"c": 2}
    assert adapted["clocks_patch"]["clock_a"]["progress"] == 1
    assert len(adapted["projects_patch"]) == 1
    assert adapted["append_events"][0]["text"] == "hello"
    ok, _ = sc.validate_world_update(adapted)
    assert ok


def test_adapt_legacy_world_update_parks_unknown_top_level_lists():
    adapted = sc.adapt_legacy_world_update(
        {
            "append_events": [],
            "factions": [{"id": "fx", "name": "Guild"}],
            "assets": [{"id": "ax"}],
        }
    )
    unk = adapted["metadata"]["unknown_legacy_keys"]
    assert unk.get("factions") == [{"id": "fx", "name": "Guild"}]
    assert unk.get("assets") == [{"id": "ax"}]


def test_adapt_legacy_world_update_increment_counters_parked():
    adapted = sc.adapt_legacy_world_update({"increment_counters": {"x": 2}})
    assert adapted["counters_patch"] == {}
    assert adapted["metadata"]["legacy_increment_counters"] == {"x": 2}


# --- Affordance ---


def test_adapt_legacy_affordance_camel_case_targets():
    a = sc.adapt_legacy_affordance(
        {
            "id": "go-north",
            "label": "Go north",
            "type": "scene_transition",
            "targetSceneId": "north_room",
            "prompt": "Go north",
        }
    )
    assert a["target_scene_id"] == "north_room"
    assert "targetSceneId" not in a


def test_normalize_affordance_unknown_parked_in_metadata():
    a = sc.normalize_affordance({"id": "i", "label": "L", "prompt": "p", "extra_field": 3})
    assert a["metadata"]["unknown_legacy_keys"]["extra_field"] == 3


# --- Interaction target ---


def test_adapt_legacy_interaction_target_actor_id():
    t = sc.adapt_legacy_interaction_target({"actor_id": "npc_1", "name": "Guard", "scene_id": "gate"}, scene_id_fallback="gate")
    assert t["id"] == "npc_1"
    ok, _ = sc.validate_interaction_target(t)
    assert ok


# --- Clue ---


def test_adapt_legacy_clue_string_uses_slug_id():
    c = sc.adapt_legacy_clue("  A secret note  ")
    assert c["text"] == "A secret note"
    assert c["id"]
    ok, _ = sc.validate_clue(c)
    assert ok


def test_adapt_legacy_clue_leads_and_reveal_requires():
    c = sc.adapt_legacy_clue(
        {
            "id": "c1",
            "text": "t",
            "leads_to_scene": "scene_b",
            "leads_to_npc": "npc_x",
            "reveal_requires": ["flag_a"],
        }
    )
    assert c["leads_to_scene_id"] == "scene_b"
    assert c["leads_to_npc_id"] == "npc_x"
    assert c["metadata"]["reveal_requires"] == ["flag_a"]


def test_validate_clue_rejects_unknown_top_level_after_manual_merge():
    bad = {"id": "x", "text": "t", "state": "unknown", "presentation": None, "bogus": 1}
    ok, reasons = sc.validate_clue(bad)
    assert ok is False
    assert any("unknown_key" in r for r in reasons)


# --- Project ---


def test_adapt_legacy_project_goal_to_target():
    p = sc.adapt_legacy_project({"id": "p", "name": "P", "goal": 7})
    assert p["target"] == 7
    ok, _ = sc.validate_project(p)
    assert ok


# --- Clock ---


def test_adapt_legacy_clock_progress_to_value():
    c = sc.adapt_legacy_clock({"name": "heat", "progress": 3, "max": 8})
    assert c["id"] == "heat"
    assert c["value"] == 3
    assert c["max_value"] == 8
    ok, _ = sc.validate_clock(c)
    assert ok


def test_validate_clock_rejects_bad_max_type():
    ok, reasons = sc.validate_clock({"id": "c", "value": 0, "min_value": 0, "max_value": "x", "scope": "", "metadata": {}})
    assert ok is False
    assert any("max_value_not_int" in r for r in reasons)


def test_adapt_legacy_clue_moves_engine_type_to_metadata():
    c = sc.adapt_legacy_clue({"id": "x", "text": "t", "type": "investigation", "state": "discoverable"})
    assert "type" not in c
    assert c["metadata"]["engine_lead_type"] == "investigation"


def test_coerce_world_state_clock_row_legacy_and_canonical():
    leg = sc.coerce_world_state_clock_row("heat", {"progress": 2, "max": 7})
    assert leg["id"] == "heat" and leg["value"] == 2 and leg["max_value"] == 7 and leg["scope"] == "world"
    can = sc.coerce_world_state_clock_row("heat", leg)
    assert can == leg


def test_world_clock_row_summary_line_accepts_legacy_row():
    line = sc.world_clock_row_summary_line("tension", {"progress": 4, "max": 12})
    assert line == "tension: 4/12"
