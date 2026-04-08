"""Integration tests for apply_final_emission_gate speaker-contract enforcement ordering and metadata."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _runner_strict_bundle():
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


def test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True
    assert isinstance(eff, dict)

    order: list[str] = []
    orig_rd = feg._apply_response_delta_layer
    orig_enf = feg.enforce_emitted_speaker_with_contract

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", enf)

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "No names, only rumors."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Tavern Runner says, "No names, only rumors."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert order.index("response_delta") < order.index("speaker_contract")
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" in em
    reason = (out.get("_final_emission_meta") or {}).get("speaker_contract_enforcement_reason")
    assert reason == em["speaker_contract_enforcement"]["final_reason_code"]


def test_apply_final_emission_gate_strict_social_contract_missing_skips_tightening(monkeypatch):
    """Legacy / missing contract: enforcement must not invent a stricter policy."""
    session, world, sid, resolution = _runner_strict_bundle()
    empty_contract = get_speaker_selection_contract(None, None, None)
    assert empty_contract["debug"].get("contract_missing") is True

    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: empty_contract)

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        # Would be forbidden repair if a real contract were present.
        return 'Ragged stranger says, "Pay me."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Ragged stranger says, "Pay me."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    assert "Ragged stranger" in text
    assert (out.get("_final_emission_meta") or {}).get("speaker_contract_enforcement_reason") == "speaker_contract_match"
    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("speaker_contract_enforcement") or {}
    assert payload.get("validation", {}).get("details", {}).get("skipped") == "no_contract"


def test_apply_final_emission_gate_non_strict_path_does_not_attach_speaker_enforcement():
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" not in em
