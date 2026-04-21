"""Contract tests for ``game.noncombat_resolution`` (Objective #8 Block A)."""
from __future__ import annotations

import pytest

from game.noncombat_resolution import (
    NONCOMBAT_FRAMEWORK_VERSION,
    NONCOMBAT_KINDS,
    attach_noncombat_contract,
    classify_noncombat_kind,
    normalize_noncombat_resolution,
    resolve_noncombat_action,
)
from game.scene_actions import normalize_scene_action

pytestmark = pytest.mark.unit

_CANONICAL_KEYS = frozenset(
    {
        "framework_version",
        "kind",
        "subkind",
        "authority_domain",
        "deterministic_resolved",
        "requires_check",
        "check_request",
        "outcome_type",
        "success_state",
        "discovered_entities",
        "surfaced_facts",
        "state_changes",
        "blocked_reason_codes",
        "ambiguous_reason_codes",
        "unsupported_reason_codes",
        "authoritative_outputs",
    }
)


def test_noncombat_kind_taxonomy_is_stable():
    assert NONCOMBAT_KINDS == (
        "perception",
        "investigation",
        "social_probe",
        "exploration",
        "downtime",
    )


def test_classify_observe_maps_to_perception():
    c = classify_noncombat_kind({"type": "observe", "id": "x", "label": "L", "prompt": "p"})
    assert c.kind == "perception"
    assert c.subkind == "observe"
    assert c.route == "exploration"
    assert c.authority_domain == "scene_state"


def test_classify_social_kind_routes_social():
    c = classify_noncombat_kind({"type": "persuade", "id": "s", "label": "L", "prompt": "p"})
    assert c.kind == "social_probe"
    assert c.subkind == "persuade"
    assert c.route == "social"


def test_classify_attack_is_out_of_scope():
    c = classify_noncombat_kind({"type": "attack", "id": "a"})
    assert c.route == "none"
    assert "combat_action_not_noncombat" in c.unsupported_reason_codes


def test_classify_unknown_type_fail_closed():
    c = classify_noncombat_kind({"type": "not_a_real_engine_type", "id": "z"})
    assert c.route == "none"
    assert "unknown_action_type_for_noncombat" in c.ambiguous_reason_codes


def test_classify_explicit_route_mismatch():
    c = classify_noncombat_kind(
        {"type": "observe", "id": "o"},
        explicit_route="social",
    )
    assert c.route == "none"
    assert "route_explicit_mismatch" in c.ambiguous_reason_codes


def test_normalize_omits_prose_fields():
    raw = {
        "kind": "observe",
        "action_id": "a1",
        "label": "Label prose",
        "prompt": "Player prose",
        "success": None,
        "resolved_transition": False,
        "target_scene_id": None,
        "clue_id": None,
        "discovered_clues": [],
        "world_updates": None,
        "state_changes": {"x": 1},
        "hint": "Narrator should say something flowery.",
        "metadata": {},
    }
    cls = classify_noncombat_kind({"type": "observe", "id": "a1"})
    nc = normalize_noncombat_resolution(raw, cls, route="exploration", source_engine="game.exploration")
    assert "hint" not in nc
    assert "prompt" not in nc
    assert "label" not in nc
    assert nc["framework_version"] == NONCOMBAT_FRAMEWORK_VERSION
    assert set(nc.keys()) <= _CANONICAL_KEYS | {"narration_constraints"}


def test_resolve_noncombat_observe_minimal_scene():
    scene = {"scene": {"id": "test_scene", "location": "Here"}}
    action = normalize_scene_action(
        {"id": "observe-a", "label": "Observe", "type": "observe", "prompt": "Look around."}
    )
    out = resolve_noncombat_action(scene, {}, {}, action, raw_player_text="Look around.")
    nc = out["noncombat_resolution"]
    assert nc["kind"] == "perception"
    assert nc["outcome_type"] == "closed"
    assert nc["requires_check"] is False
    assert out.get("kind") is not None


def test_resolve_noncombat_attack_returns_unsupported():
    nc = resolve_noncombat_action(
        {"scene": {"id": "s"}},
        {},
        {},
        {"type": "attack", "id": "atk", "label": "Hit", "prompt": "hit goblin"},
    )
    assert nc["outcome_type"] == "unsupported"
    assert "combat_action_not_noncombat" in nc["unsupported_reason_codes"]


def test_resolve_noncombat_downtime_not_wired():
    nc = resolve_noncombat_action(
        {"scene": {"id": "s"}},
        {},
        {},
        {"type": "downtime", "id": "d", "label": "Rest", "prompt": "rest"},
    )
    assert nc["kind"] == "downtime"
    assert nc["outcome_type"] == "unsupported"
    assert "downtime_engine_not_wired" in nc["unsupported_reason_codes"]


def test_attach_noncombat_contract_embeds_payload():
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
        "state_changes": {},
        "hint": "",
        "metadata": {},
    }
    out = attach_noncombat_contract(raw, {"type": "observe", "id": "a1"})
    assert "noncombat_resolution" in out
    assert out["noncombat_resolution"]["kind"] == "perception"
