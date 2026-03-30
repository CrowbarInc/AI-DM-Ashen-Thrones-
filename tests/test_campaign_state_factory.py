"""Canonical fresh runtime state factory."""

from __future__ import annotations

from game.campaign_state import (
    create_fresh_campaign_state,
    create_fresh_combat_state,
    create_fresh_session_document,
)
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.session import reset_session_state


def test_fresh_session_is_independent_graph():
    a = create_fresh_session_document()
    b = create_fresh_session_document()
    assert a is not b
    assert a["visited_scene_ids"] is not b["visited_scene_ids"]
    assert a["clocks"] is not b["clocks"]
    assert a[SESSION_LEAD_REGISTRY_KEY] is not b[SESSION_LEAD_REGISTRY_KEY]
    assert a["campaign_run_id"] != b["campaign_run_id"]
    a["visited_scene_ids"].append("market_quarter")
    assert "market_quarter" not in b["visited_scene_ids"]
    a[SESSION_LEAD_REGISTRY_KEY]["x"] = 1
    assert "x" not in b[SESSION_LEAD_REGISTRY_KEY]


def test_fresh_session_has_empty_lead_registry():
    s = create_fresh_session_document()
    assert SESSION_LEAD_REGISTRY_KEY in s
    reg = s[SESSION_LEAD_REGISTRY_KEY]
    assert reg == {}
    assert isinstance(reg, dict)


def test_fresh_session_lead_registry_not_shared_with_campaign_bundle():
    bundle = create_fresh_campaign_state()
    standalone = create_fresh_session_document()
    assert bundle["session"][SESSION_LEAD_REGISTRY_KEY] is not standalone[SESSION_LEAD_REGISTRY_KEY]


def test_fresh_campaign_bundle_shape():
    bundle = create_fresh_campaign_state()
    assert set(bundle.keys()) == {"session", "combat"}
    assert bundle["combat"] == create_fresh_combat_state()


def test_reset_session_state_clears_leaked_keys():
    session = {
        "active_scene_id": "x",
        "visited_scene_ids": ["x"],
        "legacy_only_field": {"nested": [1, 2, 3]},
    }
    reset_session_state(session)
    assert "legacy_only_field" not in session
    assert session["active_scene_id"] == "frontier_gate"
