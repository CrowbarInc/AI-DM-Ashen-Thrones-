"""Regression: repeated clue discovery paths must not duplicate canonical state or one-shot side effects."""
from __future__ import annotations

import copy

import pytest

from game.clues import apply_authoritative_clue_discovery, apply_socially_revealed_leads, run_inference
from game.defaults import default_world
from game.exploration import process_investigation_discovery
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _canonical_clue_snapshot(session: dict, scene_id: str, world: dict) -> dict:
    rt = get_scene_runtime(session, scene_id)
    ck = session.get("clue_knowledge") or {}
    knowledge_keys = sorted(k for k in ck if isinstance(k, str))
    return {
        "discovered_clue_ids": list(rt.get("discovered_clue_ids") or []),
        "discovered_clues": list(rt.get("discovered_clues") or []),
        "pending_leads": copy.deepcopy(rt.get("pending_leads") or []),
        "knowledge_keys": knowledge_keys,
        "knowledge": copy.deepcopy(ck),
        "event_log_len": len(world.get("event_log") or []),
        "social_lead_event_ids": list(session.get("social_lead_event_ids") or []),
    }


def test_apply_authoritative_clue_discovery_twice_runs_inference_once(monkeypatch):
    """Authoritative gateway must not re-fire inference when the same structured clue is re-applied."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "inferred_only",
                "requires": ["anchor_clue"],
                "inferred_clue_text": "Synthesized fact.",
            }
        ],
        "clues": {},
    }
    calls: list[int] = []
    real = run_inference

    def spy(s, w):
        calls.append(1)
        return real(s, w)

    monkeypatch.setattr("game.clues.run_inference", spy)

    apply_authoritative_clue_discovery(
        session,
        "gate",
        clue_id="anchor_clue",
        clue_text="Anchor text.",
        discovered_clues=["Anchor text."],
        world=world,
    )
    apply_authoritative_clue_discovery(
        session,
        "gate",
        clue_id="anchor_clue",
        clue_text="Anchor text.",
        discovered_clues=["Anchor text."],
        world=world,
    )

    assert len(calls) == 1
    assert session["clue_knowledge"]["inferred_only"]["state"] == "inferred"
    rt = get_scene_runtime(session, "gate")
    assert rt["discovered_clue_ids"] == ["anchor_clue"]
    assert rt["discovered_clues"] == ["Anchor text."]


def test_apply_socially_revealed_leads_twice_preserves_canonical_state():
    """Second pass through the social landing path must match first-pass session/world clue bookkeeping."""
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "frontier_gate"
    res = {
        "kind": "question",
        "action_id": "q",
        "label": "Ask",
        "prompt": "Ask",
        "success": True,
        "resolved_transition": False,
        "target_scene_id": None,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "world_updates": None,
        "state_changes": {"topic_revealed": True},
        "hint": "h",
        "social": {
            "npc_id": "guard_captain",
            "npc_name": "Captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
        "requires_check": False,
    }
    scene = {"scene": {"id": scene_id}}

    apply_socially_revealed_leads(session, scene_id, world, res, scene=scene)
    snap1 = _canonical_clue_snapshot(session, scene_id, world)

    apply_socially_revealed_leads(session, scene_id, world, res, scene=scene)
    snap2 = _canonical_clue_snapshot(session, scene_id, world)

    assert snap2 == snap1
    social_events = [
        e
        for e in world.get("event_log") or []
        if isinstance(e, dict) and e.get("type") == "social_lead_revealed"
    ]
    assert len([e for e in social_events if e.get("clue_id") == "missing_patrol"]) == 1
    extracted = [
        e
        for e in world.get("event_log") or []
        if isinstance(e, dict) and e.get("type") == "social_extracted_lead"
    ]
    assert len(extracted) == 1


def test_process_investigation_discovery_second_call_is_noop():
    """Investigation pipeline uses the authoritative gateway; re-running must not append or re-reveal."""
    scene_envelope = {
        "scene": {
            "id": "lab_scene",
            "discoverable_clues": [
                {
                    "id": "residue_clue",
                    "text": "A faint alchemical residue.",
                    "leads_to_scene": "old_milestone",
                },
            ],
        }
    }
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    world: dict = {"inference_rules": [], "clues": {}}

    first = process_investigation_discovery(scene_envelope, session, world=world)
    snap_after_first = _canonical_clue_snapshot(session, "lab_scene", world)

    second = process_investigation_discovery(scene_envelope, session, world=world)
    snap_after_second = _canonical_clue_snapshot(session, "lab_scene", world)

    assert len(first) == 1
    assert second == []
    assert snap_after_second == snap_after_first
