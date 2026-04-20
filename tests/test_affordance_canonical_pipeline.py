"""Block C — affordance + interaction-target canonical pipeline (schema_contracts ingress)."""
from __future__ import annotations

import pytest

from game import schema_contracts as sc
from game.affordances import (
    _affordance_dedupe_key,
    _affordance_rank,
    _ingress_affordance,
    generate_scene_affordances,
    get_available_affordances,
)
from game.interaction_context import _legacy_addressable_field, scene_addressables_from_envelope
from game.scene_actions import normalize_scene_action


pytestmark = pytest.mark.unit


def test_legacy_camel_case_affordance_adapts_at_ingress():
    raw = {
        "id": "x",
        "label": "Go",
        "type": "scene_transition",
        "prompt": "p",
        "targetSceneId": "north",
        "targetEntityId": "bob",
        "targetLocationId": "loc1",
    }
    a = _ingress_affordance(raw)
    assert a["target_scene_id"] == "north"
    assert a["target_id"] == "bob"
    assert a["target_location_id"] == "loc1"
    assert "targetSceneId" not in a
    ok, _ = sc.validate_affordance(a)
    assert ok


def test_dedupe_key_matches_for_legacy_vs_canonical_targets():
    canonical = _ingress_affordance(
        sc.normalize_affordance(
            {
                "id": "a1",
                "label": "Talk to Bob",
                "type": "question",
                "prompt": "I talk to Bob.",
                "target_id": "bob",
                "target_scene_id": None,
                "target_location_id": None,
            }
        )
    )
    legacy = _ingress_affordance(
        {"id": "a2", "label": "Talk to Bob", "type": "question", "prompt": "I talk to Bob.", "targetEntityId": "bob"}
    )
    assert _affordance_dedupe_key(canonical) == _affordance_dedupe_key(legacy)


def test_ranking_prefers_explicit_scene_action_and_social_target():
    scene = {
        "scene": {
            "id": "s1",
            "actions": [{"id": "explicit", "label": "Talk", "type": "question", "prompt": "p", "target_id": "n1"}],
        }
    }
    explicit = _ingress_affordance(normalize_scene_action(scene["scene"]["actions"][0]))
    implicit = _ingress_affordance(
        sc.normalize_affordance(
            {
                "id": "implicit",
                "label": "Talk",
                "type": "question",
                "prompt": "p",
                "target_id": "n1",
            }
        )
    )
    assert _affordance_rank(explicit, scene) > _affordance_rank(implicit, scene)


def test_interaction_target_addressable_normalization_and_legacy_field_reader():
    env = {
        "scene": {
            "id": "gate",
            "addressables": [
                {"id": "crier", "name": "Town crier", "role": "herald", "topics": ["news"], "address_roles": ["crowd"]}
            ],
        }
    }
    rows = scene_addressables_from_envelope(env)
    assert len(rows) == 1
    r = rows[0]
    ok, _ = sc.validate_interaction_target(r)
    assert ok
    assert r["id"] == "crier"
    assert _legacy_addressable_field(r, "role") == "herald"
    assert _legacy_addressable_field(r, "topics") == ["news"]


def test_social_npc_affordance_binds_target_id():
    scene = {"scene": {"id": "here", "mode": "exploration", "visible_facts": [], "exits": [], "actions": []}}
    session = {"scene_runtime": {"here": {}}, "active_scene_id": "here"}
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {}}, "npcs": [{"id": "u1", "name": "Pat", "location": "here"}]}
    affs = get_available_affordances(scene, session, world)
    talk = next((a for a in affs if a.get("type") == "question" and a.get("target_id") == "u1"), None)
    assert talk is not None
    assert "Pat" in (talk.get("label") or "")


def test_generate_scene_merges_scene_action_with_target_scene_id():
    scene = {
        "scene": {
            "id": "here",
            "mode": "exploration",
            "visible_facts": [],
            "exits": [],
            "actions": [
                {
                    "id": "travel-x",
                    "label": "Crossroads",
                    "type": "scene_transition",
                    "prompt": "Go.",
                    "targetSceneId": "crossroads",
                }
            ],
        }
    }
    session = {"scene_runtime": {"here": {}}}
    affs = generate_scene_affordances(scene, "exploration", session)
    t = next((a for a in affs if a.get("id") == "travel-x"), None)
    assert t is not None
    assert t.get("target_scene_id") == "crossroads"
