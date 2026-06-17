"""Strict-social gate harness bundle for equivalence and gauntlet smoke tests (Cycle AS1).

Session/world/resolution scaffold for strict-social gate paths. Owner legality remains
``tests/test_final_emission_gate.py`` and ``tests/test_social_exchange_emission.py``.
"""
from __future__ import annotations

from typing import Any

import pytest

import game.final_emission_strict_social_stack as strict_social_stack
from game.defaults import default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narrative_authority import build_narrative_authority_contract
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime

from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer

def runner_strict_bundle():
    session = default_session()
    world = default_world()
    sid = "scene_investigate"
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "East lanes.", "clue_id": "east_lanes"}],
        }
    ]
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    set_social_target(session, "runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who attacked them?"
    resolution = {
        "kind": "question",
        "prompt": "Who attacked them?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
        },
    }
    return session, world, sid, resolution


def _na_contract_for_resolution(resolution: dict) -> dict:
    return build_narrative_authority_contract(
        resolution=resolution,
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )


def run_strict_social_motive_overclaim_gate_case(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strict-social: NA is validate-only; motive overclaim remains visible in meta, not silently rewritten."""
    session, world, sid, resolution = runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True

    na = _na_contract_for_resolution(eff if isinstance(eff, dict) else resolution)
    bad = (
        'Tavern Runner says, "No names yet—only rumors."\n\n'
        "He plans to stall you until the watch arrives."
    )

    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(_candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

    out, meta = apply_final_emission_gate_consumer(
        {
            "player_facing_text": bad,
            "tags": [],
            "response_policy": {"narrative_authority": na},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("narrative_authority_repaired") is False
    assert meta.get("narrative_authority_failed") is True
    assert em.get("narrative_authority_boundary_semantic_repair_disabled") is True
    assert "plans to stall" in text.lower()
    assert "Tavern Runner" in text
    assert meta.get("speaker_contract_enforcement_reason") == "speaker_contract_match"
