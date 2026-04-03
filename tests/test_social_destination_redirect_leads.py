"""Regression: directional social narration promotes concrete destination anchors to actionable leads.

Named crier redirects (e.g. Lirael) require resolving ``emergent_town_crier`` from scene state; the
engine may list that NPC in ``active_entities`` before it appears in addressables — see
``_crier_npc_id_from_addressables`` in ``game.clues``.
"""
from __future__ import annotations

from game.clues import apply_social_narration_lead_supplements, apply_socially_revealed_leads
from game.leads import SESSION_LEAD_REGISTRY_KEY, ensure_lead_registry, get_lead
from game.defaults import default_world
from game.storage import add_pending_lead, get_scene_runtime, load_scene


import pytest

pytestmark = pytest.mark.integration

def _lirael_notice_board_resolution() -> dict:
    return {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "narration_ctx_frontier_gate_notice_board",
        "discovered_clues": ["notice board"],
        "social": {
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "narration_repair_frontier_gate_directional_phrase",
                "text": "notice board",
                "clue_text": "notice board",
                "clue_id": "narration_ctx_frontier_gate_notice_board",
            },
        },
    }


def test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    ensure_lead_registry(session)
    scene = load_scene("frontier_gate")
    res = _lirael_notice_board_resolution()
    narr = (
        'The runner jerks his chin toward the press. "Check with Lirael—she posts the notices. '
        'You\'ll find Lirael near the notice board."'
    )
    apply_socially_revealed_leads(
        session,
        "frontier_gate",
        world,
        res,
        player_facing_text=narr,
        player_facing_text_is_reconciled=True,
        scene=scene,
    )
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)

    rt = get_scene_runtime(session, "frontier_gate")
    pending = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    npc_pending = [p for p in pending if p.get("leads_to_npc") == "emergent_town_crier"]
    assert len(npc_pending) == 1
    assert npc_pending[0].get("authoritative_lead_id")
    # Regression: NPC anchor must not degrade to a rumor-only pending row when crier is in active_entities.
    assert not npc_pending[0].get("leads_to_rumor")
    auth = npc_pending[0]["authoritative_lead_id"]
    row = get_lead(session, auth)
    assert row is not None
    assert row.get("type") == "social"
    assert "emergent_town_crier" in (row.get("related_npc_ids") or [])
    reg = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
    assert isinstance(reg, dict)
    assert sum(1 for k in reg if isinstance(k, str)) >= 1


def test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    ensure_lead_registry(session)
    scene = load_scene("frontier_gate")
    res = _lirael_notice_board_resolution()
    narr = 'She nods. "Lirael—near the notice board. Same as I said—seek Lirael by the notice board."'
    apply_socially_revealed_leads(
        session,
        "frontier_gate",
        world,
        res,
        player_facing_text=narr,
        player_facing_text_is_reconciled=True,
        scene=scene,
    )
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)

    rt = get_scene_runtime(session, "frontier_gate")
    npc_pending = [
        p
        for p in (rt.get("pending_leads") or [])
        if isinstance(p, dict) and p.get("leads_to_npc") == "emergent_town_crier"
    ]
    assert len(npc_pending) == 1


def test_destination_lead_distinct_from_existing_milestone_pending():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    ensure_lead_registry(session)
    scene = load_scene("frontier_gate")
    add_pending_lead(
        session,
        "frontier_gate",
        {
            "clue_id": "lead_frontier_gate_old_milestone",
            "text": "Investigate the old milestone",
            "authoritative_lead_id": "lead_frontier_gate_old_milestone",
            "leads_to_scene": "old_milestone",
        },
    )
    res = _lirael_notice_board_resolution()
    narr = 'He points. "Ask Lirael—she\'s by the notice board."'
    apply_socially_revealed_leads(
        session,
        "frontier_gate",
        world,
        res,
        player_facing_text=narr,
        player_facing_text_is_reconciled=True,
        scene=scene,
    )
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)

    rt = get_scene_runtime(session, "frontier_gate")
    pending = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    ms = [p for p in pending if p.get("leads_to_scene") == "old_milestone"]
    npc = [p for p in pending if p.get("leads_to_npc") == "emergent_town_crier"]
    assert len(ms) == 1
    assert len(npc) == 1


def test_flavor_directional_text_no_scene_anchor_lead():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    scene = load_scene("frontier_gate")
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "flavor_clue",
        "discovered_clues": ["The gate smells of wet wool."],
        "social": {
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "f1",
                "text": "The gate smells of wet wool.",
                "clue_text": "The gate smells of wet wool.",
            },
        },
    }
    narr = "Rain drums on the cobbles; somewhere a cart creaks toward the square, but the runner says nothing new."
    apply_socially_revealed_leads(
        session,
        "frontier_gate",
        world,
        res,
        player_facing_text=narr,
        player_facing_text_is_reconciled=True,
        scene=scene,
    )
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)
    rt = get_scene_runtime(session, "frontier_gate")
    anchor_leads = [
        p
        for p in (rt.get("pending_leads") or [])
        if isinstance(p, dict)
        and str(p.get("clue_id") or "").startswith("lead_frontier_gate_")
        and p.get("leads_to_npc") == "emergent_town_crier"
    ]
    assert anchor_leads == []
