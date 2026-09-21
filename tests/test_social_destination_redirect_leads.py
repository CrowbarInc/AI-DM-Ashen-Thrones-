"""Regression: directional social narration promotes authored destination evidence to official follow-up.

RC-21 B+C: spoken names do not instantiate NPCs. Official follow-up comes from authored/realized
scene evidence, written to the canonical lead registry. ``pending_leads`` and clue knowledge are
projections. Named-crier binding still requires authored discoverable name plus a crier id from
addressables / active_entities — see ``_crier_npc_id_from_addressables`` in ``game.clues``.
Current ``frontier_gate`` canon authors the notice board, not Lirael / ``emergent_town_crier``.
"""
from __future__ import annotations

from game.clues import apply_social_narration_lead_supplements, apply_socially_revealed_leads
from game.leads import SESSION_LEAD_REGISTRY_KEY, ensure_lead_registry, get_lead
from game.defaults import default_world
from game.storage import add_pending_lead, get_scene_runtime, load_scene


import pytest

pytestmark = pytest.mark.integration

NOTICE_BOARD_LEAD_ID = "lead_frontier_gate_notice_board"
CRIER_NPC_ID = "emergent_town_crier"
NOTICE_BOARD_LABEL = "Check the notice board"


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


def _apply_lirael_redirect(session: dict, world: dict, scene: dict, narr: str) -> None:
    res = _lirael_notice_board_resolution()
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


def _pending_rows(session: dict) -> list[dict]:
    rt = get_scene_runtime(session, "frontier_gate")
    return [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]


def _crier_pending(pending: list[dict]) -> list[dict]:
    return [p for p in pending if p.get("leads_to_npc") == CRIER_NPC_ID]


def _notice_board_pending(pending: list[dict]) -> list[dict]:
    return [
        p
        for p in pending
        if p.get("authoritative_lead_id") == NOTICE_BOARD_LEAD_ID
        or p.get("clue_id") == NOTICE_BOARD_LEAD_ID
        or p.get("leads_to_rumor") == NOTICE_BOARD_LABEL
    ]


def _assert_no_spoken_lirael_instantiation(session: dict, pending: list[dict]) -> None:
    assert _crier_pending(pending) == []
    for row in (session.get(SESSION_LEAD_REGISTRY_KEY) or {}).values():
        if isinstance(row, dict):
            assert CRIER_NPC_ID not in (row.get("related_npc_ids") or [])


def _assert_notice_board_registry_is_canonical(session: dict, pending: list[dict]) -> dict:
    board_pending = _notice_board_pending(pending)
    assert len(board_pending) == 1
    assert board_pending[0].get("authoritative_lead_id") == NOTICE_BOARD_LEAD_ID
    assert board_pending[0].get("leads_to_rumor") == NOTICE_BOARD_LABEL
    assert not board_pending[0].get("leads_to_npc")

    row = get_lead(session, NOTICE_BOARD_LEAD_ID)
    assert row is not None
    assert row.get("type") == "location"
    assert row.get("title") == NOTICE_BOARD_LABEL
    knowledge = session.get("clue_knowledge") or {}
    assert NOTICE_BOARD_LEAD_ID in knowledge
    return row


def test_lirael_near_notice_board_creates_authored_notice_board_followup_and_registry():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    ensure_lead_registry(session)
    scene = load_scene("frontier_gate")
    narr = (
        'The runner jerks his chin toward the press. "Check with Lirael—she posts the notices. '
        'You\'ll find Lirael near the notice board."'
    )
    _apply_lirael_redirect(session, world, scene, narr)

    pending = _pending_rows(session)
    _assert_no_spoken_lirael_instantiation(session, pending)
    row = _assert_notice_board_registry_is_canonical(session, pending)
    assert "tavern_runner" in (row.get("related_npc_ids") or [])
    reg = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
    assert isinstance(reg, dict)
    assert NOTICE_BOARD_LEAD_ID in reg


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

    pending = _pending_rows(session)
    _assert_no_spoken_lirael_instantiation(session, pending)
    _assert_notice_board_registry_is_canonical(session, pending)
    assert len(_notice_board_pending(pending)) == 1
    assert sum(1 for key in (session.get(SESSION_LEAD_REGISTRY_KEY) or {}) if key == NOTICE_BOARD_LEAD_ID) == 1


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
    narr = 'He points. "Ask Lirael—check the notice board."'
    _apply_lirael_redirect(session, world, scene, narr)

    pending = _pending_rows(session)
    milestone = [p for p in pending if p.get("leads_to_scene") == "old_milestone"]
    assert len(milestone) == 1
    assert milestone[0].get("authoritative_lead_id") == "lead_frontier_gate_old_milestone"
    _assert_no_spoken_lirael_instantiation(session, pending)
    _assert_notice_board_registry_is_canonical(session, pending)
    assert get_lead(session, NOTICE_BOARD_LEAD_ID) is not None


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
    pending = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    anchor_leads = [
        p
        for p in pending
        if str(p.get("clue_id") or "").startswith("lead_frontier_gate_")
    ]
    assert anchor_leads == []
    assert _crier_pending(pending) == []
    assert NOTICE_BOARD_LEAD_ID not in (session.get(SESSION_LEAD_REGISTRY_KEY) or {})
