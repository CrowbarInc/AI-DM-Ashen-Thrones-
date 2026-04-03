"""Block 2 — qualified pursuit: fail-closed resolution, leads_to_scene + leads_to_npc."""
from __future__ import annotations

from game.intent_parser import parse_freeform_to_action
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
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


def test_qualified_pursuit_npc_destination_by_name():
    session: dict = {"turn_counter": 1}
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
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action(
        "follow the lead to Lirael",
        scene,
        session=session,
        world=world,
    )
    assert raw is not None
    assert raw.get("type") == "scene_transition"
    assert raw.get("target_scene_id") == "old_milestone"
    assert raw.get("target_id") == "emergent_town_crier"
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "lead_lirael"
    assert md.get("commitment_source") == "explicit_player_pursuit"
    assert md.get("commitment_strength") == 2
    assert md.get("target_kind") == "npc"
    assert md.get("target_npc_id") == "emergent_town_crier"
    assert md.get("target_npc_name") == "Lirael"
    assert md.get("destination_scene_id") == "old_milestone"


def test_qualified_pursuit_missing_npc_target_returns_none_not_milestone():
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
    world = {"npcs": []}
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action(
        "follow the lead to Lirael",
        scene,
        session=session,
        world=world,
    )
    assert raw is None


def test_qualified_pursuit_does_not_snap_to_only_scene_lead():
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
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action(
        "pursue the Lirael lead",
        scene,
        session=session,
        world={"npcs": []},
    )
    assert raw is None
    assert get_lead(session, "to_milestone")["lifecycle"] == LeadLifecycle.DISCOVERED.value


def test_qualified_pursuit_two_scene_matches_same_destination_returns_none():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="La", lifecycle=LeadLifecycle.DISCOVERED))
    upsert_lead(session, create_lead(title="B", summary="", id="Lb", lifecycle=LeadLifecycle.DISCOVERED))
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "a",
            "authoritative_lead_id": "La",
            "text": "One rumor",
            "leads_to_scene": "old_milestone",
        },
        {
            "clue_id": "b",
            "authoritative_lead_id": "Lb",
            "text": "Other rumor",
            "leads_to_scene": "old_milestone",
        },
    ]
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action(
        "follow the lead to old_milestone",
        scene,
        session=session,
        world=None,
    )
    assert raw is None


def test_qualified_pursuit_scene_by_exit_label_exact():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(title="M", summary="", id="to_milestone", lifecycle=LeadLifecycle.DISCOVERED),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_ms",
            "authoritative_lead_id": "to_milestone",
            "text": "Rumor at the old milestone.",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action(
        "follow the lead to Old milestone path",
        scene,
        session=session,
        world=None,
    )
    assert raw is not None
    assert raw.get("target_scene_id") == "old_milestone"
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "to_milestone"
    assert md.get("target_kind") == "scene"
    assert md.get("destination_scene_id") == "old_milestone"


def test_legacy_follow_the_lead_single_actionable_includes_npc_lead():
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
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action("follow the lead", scene, session=session, world=world)
    assert raw is not None
    assert raw.get("type") == "scene_transition"
    assert raw.get("target_scene_id") == "old_milestone"
    md = raw.get("metadata") or {}
    assert md.get("target_kind") == "npc"
    assert md.get("target_npc_id") == "emergent_town_crier"
    assert md.get("destination_scene_id") == "old_milestone"


def test_qualified_pursuit_without_session_returns_none():
    scene = _scene_gate_exits_milestone()
    raw = parse_freeform_to_action("follow the lead to Lirael", scene, session=None, world=None)
    assert raw is None
