"""Regression tests for gm_retry paths that integrate open-social solicitation recovery."""
from __future__ import annotations

import game.social_exchange_emission as social_exchange_emission
from game.campaign_state import create_fresh_session_document
from game.interaction_context import rebuild_active_scene_entities
from game.social_exchange_emission import apply_social_exchange_retry_fallback_gm
from game.storage import load_scene

import pytest

pytestmark = pytest.mark.unit


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def test_apply_social_exchange_retry_fallback_gm_prefers_open_social_recovery(monkeypatch):
    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "Anyone listening?",
        "social": {
            "social_intent_class": "social_exchange",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["guard_captain", "tavern_runner"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }

    sentinel = (
        "DETERMINISTIC_SOCIAL_FALLBACK_SENTINEL_XYZ "
        "If this text appears, deterministic_social_fallback_line was used instead of open-social recovery."
    )

    def _boom(*a, **k):
        raise AssertionError("deterministic_social_fallback_line must not run when open-social recovery succeeds")

    monkeypatch.setattr(social_exchange_emission, "deterministic_social_fallback_line", _boom)

    gm = {"player_facing_text": "The square stays vague.", "tags": [], "metadata": {}}
    out = apply_social_exchange_retry_fallback_gm(
        gm,
        player_text="Anyone listening?",
        session=session,
        world=world,
        resolution=resolution,
        scene_id="frontier_gate",
    )
    assert sentinel not in out.get("player_facing_text", "")
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "open_social_recovery" in tags
    assert "open_social_solicitation_recovery" in tags
    assert "social_exchange_retry_fallback" not in tags
    assert "social_exchange_fallback:" not in " ".join(tags)

    low = str(out.get("player_facing_text") or "").lower()
    assert "guard captain" in low or "tavern runner" in low
    assert low.strip() not in {"no one answers.", "the moment passes.", "nobody steps forward."}

    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is True
    assert em.get("open_social_recovery_mode") in ("concrete_responder", "concrete_lead")
    assert str(em.get("open_social_recovery_reason") or "").strip()
    assert em.get("open_social_recovery_suppressed_retry_fallback") is True
    assert "retry_fallback:suppressed:social_exchange_template" in str(out.get("debug_notes") or "")
