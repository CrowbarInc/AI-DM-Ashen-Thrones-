"""Runtime integration for :mod:`game.noncombat_resolution` (Objective #8 Block B)."""
from __future__ import annotations

import pytest

from game.api import _resolve_engine_noncombat_seam
from game.defaults import default_character, default_world
from game.noncombat_resolution import classify_noncombat_kind, resolve_noncombat_action
from game.scene_actions import normalize_scene_action

pytestmark = pytest.mark.integration


def _explore_kw():
    return {"list_scene_ids": lambda: [], "load_scene_fn": lambda _sid: {"scene": {"id": _sid}}}


def test_runtime_seam_routes_perception():
    scene = {"scene": {"id": "test_scene", "location": "Here", "exits": []}}
    action = normalize_scene_action(
        {"id": "observe-a", "label": "Observe", "type": "observe", "prompt": "Look around."}
    )
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="Look around.",
        character=None,
        turn_counter=0,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    nc = res["noncombat_resolution"]
    assert nc["kind"] == "perception"
    assert nc["subkind"] == "observe"


def test_runtime_seam_routes_investigation():
    scene = {"scene": {"id": "test_scene", "location": "Here", "exits": []}}
    action = normalize_scene_action(
        {"id": "inv1", "label": "Search", "type": "investigate", "prompt": "Search the room."}
    )
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="Search the room.",
        character=None,
        turn_counter=0,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    nc = res["noncombat_resolution"]
    assert nc["kind"] == "investigation"
    assert nc["subkind"] == "investigate"


def test_runtime_seam_routes_social_probe_preserving_domain():
    world = default_world()
    world["npcs"] = [
        {"id": "merchant", "name": "Merchant", "location": "market", "disposition": "neutral"},
    ]
    scene = {"scene": {"id": "market", "exits": []}}
    character = default_character()
    character["skills"]["diplomacy"] = 20
    action = {
        "id": "persuade-merchant",
        "label": "Persuade the merchant",
        "type": "persuade",
        "prompt": "I persuade the merchant to lower the price.",
        "target_id": "merchant",
        "targetEntityId": "merchant",
    }
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        world,
        action,
        raw_player_text="Persuade the merchant",
        character=character,
        turn_counter=1,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    assert res.get("kind") == "persuade"
    nc = res["noncombat_resolution"]
    assert nc["kind"] == "social_probe"
    assert nc["subkind"] == "persuade"


def test_runtime_seam_pending_check_matches_raw_contract():
    world = default_world()
    world["npcs"] = [
        {"id": "merchant", "name": "Merchant", "location": "market", "disposition": "neutral"},
    ]
    scene = {"scene": {"id": "market", "exits": []}}
    character = default_character()
    character["skills"]["diplomacy"] = 20
    action = {
        "id": "persuade-merchant",
        "label": "Persuade the merchant",
        "type": "persuade",
        "prompt": "I persuade the merchant to lower the price.",
        "target_id": "merchant",
        "targetEntityId": "merchant",
    }
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        world,
        action,
        raw_player_text="Persuade the merchant",
        character=character,
        turn_counter=1,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    assert res["requires_check"] is True
    assert isinstance(res.get("check_request"), dict)
    nc = res["noncombat_resolution"]
    assert nc["requires_check"] is True
    assert nc["outcome_type"] == "pending_check"
    assert isinstance(nc.get("check_request"), dict)
    assert nc["check_request"] == res["check_request"]


def test_runtime_seam_exploration_kind_unchanged_owner():
    scene = {"scene": {"id": "test_scene", "location": "Here", "exits": []}}
    action = normalize_scene_action(
        {"id": "t1", "label": "Travel", "type": "travel", "prompt": "Go elsewhere.", "target_scene_id": None}
    )
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="Go elsewhere.",
        character=None,
        turn_counter=0,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    nc = res["noncombat_resolution"]
    assert nc["kind"] == "exploration"
    assert nc["subkind"] == "travel"
    assert "kind" in res


def test_attack_noncombat_resolver_stays_isolated_from_domain():
    out = resolve_noncombat_action(
        {"scene": {"id": "s"}},
        {},
        {},
        {"type": "attack", "id": "atk", "label": "Hit", "prompt": "hit goblin"},
    )
    assert "noncombat_resolution" not in out
    assert out["outcome_type"] == "unsupported"


def test_unknown_type_fail_closed_no_framework_route():
    c = classify_noncombat_kind({"type": "not_a_real_engine_type", "id": "z"})
    assert c.route == "none"


def test_runtime_seam_unknown_action_type_fail_closed_contract():
    scene = {"scene": {"id": "test_scene", "location": "Here", "exits": []}}
    action = {"type": "not_a_real_engine_type", "id": "z", "label": "X", "prompt": "x"}
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="x",
        character=None,
        turn_counter=0,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    nc = res["noncombat_resolution"]
    assert "unknown_action_type_for_noncombat" in nc["ambiguous_reason_codes"]


def test_downtime_unsupported_contract():
    out = resolve_noncombat_action(
        {"scene": {"id": "s"}},
        {},
        {},
        {"type": "downtime", "id": "d", "label": "Rest", "prompt": "rest"},
    )
    assert out["kind"] == "downtime"
    assert out["outcome_type"] == "unsupported"
    assert "downtime_engine_not_wired" in out["unsupported_reason_codes"]


def test_runtime_seam_downtime_stays_unsupported_not_synthetic_success():
    scene = {"scene": {"id": "test_scene", "location": "Here", "exits": []}}
    # Do not run ``normalize_scene_action`` here: it strips unknown ``type`` values such as
    # ``downtime`` down to ``custom``, which would erase the downtime taxonomy signal.
    action = {"type": "downtime", "id": "d", "label": "Rest", "prompt": "rest"}
    res = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="rest",
        character=None,
        turn_counter=0,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    nc = res["noncombat_resolution"]
    assert nc["kind"] == "downtime"
    assert nc["outcome_type"] == "unsupported"
    assert "downtime_engine_not_wired" in nc["unsupported_reason_codes"]
