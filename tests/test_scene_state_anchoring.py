"""Unit tests for ``validate_scene_state_anchoring`` and contract-shape edge cases (Objective #8)."""
from __future__ import annotations

import pytest

from game.scene_state_anchoring import validate_scene_state_anchoring

pytestmark = pytest.mark.unit


def _contract(**kwargs):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "test_scene",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(kwargs)
    return base


def test_validate_disabled_contract_skips_check():
    out = validate_scene_state_anchoring("anything", _contract(enabled=False))
    assert out["checked"] is False
    assert out["passed"] is True


def test_validate_invalid_contract_shape():
    out = validate_scene_state_anchoring("anything", None)
    assert out["checked"] is False
    assert out["passed"] is True
    assert "invalid_contract" in (out.get("failure_reasons") or [])


def test_validate_empty_text_failure():
    out = validate_scene_state_anchoring("", _contract())
    assert out["checked"] is True
    assert out["passed"] is False
    assert "empty_text" in (out.get("failure_reasons") or [])


def test_validate_match_kind_actor_only():
    c = _contract(actor_tokens=["keira"])
    out = validate_scene_state_anchoring("Keira taps the map once.", c)
    assert out["passed"] is True
    assert out["matched_anchor_kinds"] == ["actor"]


def test_validate_match_kind_location_only():
    c = _contract(location_tokens=["quay", "stone"])
    out = validate_scene_state_anchoring("Stone pilings line the quay.", c)
    assert out["passed"] is True
    assert "location" in out["matched_anchor_kinds"]


def test_validate_match_kind_player_action_only():
    c = _contract(player_action_tokens=["observe", "listen", "north gate"])
    out = validate_scene_state_anchoring("You listen; the north gate stays shut.", c)
    assert out["passed"] is True
    assert "player_action" in out["matched_anchor_kinds"]


def test_validate_no_anchor_match_failure_reason():
    c = _contract(actor_tokens=["zorro"])
    out = validate_scene_state_anchoring("The room is quiet.", c)
    assert out["passed"] is False
    assert "no_anchor_match" in (out.get("failure_reasons") or [])
