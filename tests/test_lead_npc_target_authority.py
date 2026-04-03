"""Block 5A — NPC-target pursuit preserves authoritative person identity vs scene travel."""
from __future__ import annotations

from game.exploration import maybe_finalize_pursued_lead_destination_payoff_after_scene_transition
from game.intent_parser import parse_freeform_to_action
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime


import pytest

pytestmark = pytest.mark.integration

def _scene_gate_exits_milestone():
    return {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "exits": [{"label": "Old milestone path", "target_scene_id": "old_milestone"}],
            "mode": "exploration",
        }
    }


def test_npc_target_lead_preserves_npc_metadata_qualified_pursuit():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Find Lirael (town crier)",
            summary="",
            id="lead_lirael",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_lirael",
            "authoritative_lead_id": "lead_lirael",
            "text": "Find Lirael (town crier)",
            "leads_to_npc": "emergent_town_crier",
        }
    ]
    world = {
        "npcs": [
            {
                "id": "emergent_town_crier",
                "name": "Lirael",
                "location": "old_milestone",
            }
        ]
    }
    raw = parse_freeform_to_action(
        "follow the lead to Lirael",
        _scene_gate_exits_milestone(),
        session=session,
        world=world,
    )
    assert raw is not None
    assert raw.get("target_scene_id") == "old_milestone"
    assert raw.get("target_id") == "emergent_town_crier"
    assert raw.get("targetEntityId") == "emergent_town_crier"
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "lead_lirael"
    assert md.get("target_kind") == "npc"
    assert md.get("target_npc_id") == "emergent_town_crier"
    assert md.get("target_npc_name") == "Lirael"
    assert md.get("destination_scene_id") == "old_milestone"


def test_qualified_pursuit_to_lirael_does_not_match_scene_only_milestone_with_world_npc():
    """World lists Lirael as an NPC but pending lead is scene-only — must not bind or travel-snap."""
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="to_milestone",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_ms",
            "authoritative_lead_id": "to_milestone",
            "text": "Investigate the old milestone",
            "leads_to_scene": "old_milestone",
        }
    ]
    world = {
        "npcs": [
            {
                "id": "lirael_npc",
                "name": "Lirael",
                "location": "old_milestone",
            }
        ]
    }
    raw = parse_freeform_to_action(
        "follow the lead to Lirael",
        _scene_gate_exits_milestone(),
        session=session,
        world=world,
    )
    assert raw is None


def test_qualified_npc_pursuit_fail_closed_without_grounded_npc_location():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Find Lirael (town crier)",
            summary="",
            id="lead_lirael",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_lirael",
            "authoritative_lead_id": "lead_lirael",
            "text": "Find Lirael (town crier)",
            "leads_to_npc": "emergent_town_crier",
        }
    ]
    world = {
        "npcs": [
            {
                "id": "emergent_town_crier",
                "name": "Lirael",
            }
        ]
    }
    raw = parse_freeform_to_action(
        "follow the lead to Lirael",
        _scene_gate_exits_milestone(),
        session=session,
        world=world,
    )
    assert raw is None


def test_bare_follow_single_actionable_npc_lead_unchanged():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Find Lirael (town crier)",
            summary="",
            id="lead_lirael",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_lirael",
            "authoritative_lead_id": "lead_lirael",
            "text": "Find Lirael (town crier)",
            "leads_to_npc": "emergent_town_crier",
        }
    ]
    world = {
        "npcs": [
            {
                "id": "emergent_town_crier",
                "name": "Lirael",
                "location": "old_milestone",
            }
        ]
    }
    raw = parse_freeform_to_action(
        "follow the lead",
        _scene_gate_exits_milestone(),
        session=session,
        world=world,
    )
    assert raw is not None
    assert raw.get("type") == "scene_transition"
    assert raw.get("target_scene_id") == "old_milestone"
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "lead_lirael"
    assert md.get("target_kind") == "npc"


def test_maybe_finalize_skips_destination_payoff_for_npc_target_kind():
    session: dict = {"turn_counter": 3}
    upsert_lead(
        session,
        create_lead(
            title="NPC thread",
            summary="",
            id="npc_lead_payoff",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["gate", "old_milestone"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "pursue-npc",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "targetEntityId": "emergent_town_crier",
            "metadata": {
                "authoritative_lead_id": "npc_lead_payoff",
                "commitment_source": "explicit_player_pursuit",
                "commitment_strength": 2,
                "target_kind": "npc",
                "target_npc_id": "emergent_town_crier",
                "destination_scene_id": "old_milestone",
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "success": True,
        "metadata": {"committed_lead_id": "npc_lead_payoff"},
    }
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
        session, resolution, norm, target_scene_id="old_milestone"
    )
    row = get_lead(session, "npc_lead_payoff")
    assert row is not None
    assert row.get("lifecycle") == "committed"
    assert row.get("status") == "pursued"
