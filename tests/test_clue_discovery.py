"""Tests for clue discovery: investigation reveals clues, no repeats, leads generate affordances."""
from __future__ import annotations

from game.exploration import process_investigation_discovery, resolve_exploration_action
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime, mark_clue_discovered, add_pending_lead
from game.affordances import generate_scene_affordances
from game.clues import get_clue_presentation


import pytest

pytestmark = pytest.mark.integration

def test_investigation_reveals_new_clue_once():
    """First investigate reveals the next undiscovered clue; second investigate reveals the next."""
    scene = {
        "scene": {
            "id": "test_scene",
            "discoverable_clues": [
                {"id": "clue_1", "text": "Bootprints lead toward the river."},
                {"id": "clue_2", "text": "A torn scrap of cloth lies in the mud."},
            ],
        }
    }
    session = {}

    revealed1 = process_investigation_discovery(scene, session)
    assert len(revealed1) == 1
    assert revealed1[0]["text"] == "Bootprints lead toward the river."

    rt = get_scene_runtime(session, "test_scene")
    assert "Bootprints lead toward the river." in rt["discovered_clues"]

    revealed2 = process_investigation_discovery(scene, session)
    assert len(revealed2) == 1
    assert revealed2[0]["text"] == "A torn scrap of cloth lies in the mud."

    revealed3 = process_investigation_discovery(scene, session)
    assert len(revealed3) == 0


def test_same_clue_not_repeated_twice():
    """Once a clue is discovered, it is not revealed again."""
    scene = {
        "scene": {
            "id": "repeat_test",
            "discoverable_clues": [{"id": "only", "text": "Single clue here."}],
        }
    }
    session = {}

    r1 = process_investigation_discovery(scene, session)
    assert len(r1) == 1

    r2 = process_investigation_discovery(scene, session)
    assert len(r2) == 0

    rt = get_scene_runtime(session, "repeat_test")
    assert rt["discovered_clues"] == ["Single clue here."]


def test_clue_leads_generate_exploration_affordances():
    """Clues with leads_to_scene produce 'Follow lead' affordances when target scene exists."""
    scene = {
        "scene": {
            "id": "frontier_gate",
            "visible_facts": [],
            "exits": [],
            "mode": "exploration",
        }
    }
    session = {}
    rt = get_scene_runtime(session, "frontier_gate")
    rt["discovered_clues"] = ["Bootprints toward the river."]
    rt["pending_leads"] = [
        {
            "clue_id": "tracks",
            "text": "Bootprints toward the river.",
            "leads_to_scene": "market_quarter",
        }
    ]

    affs = generate_scene_affordances(
        scene, "exploration", session, list_scene_ids_fn=lambda: ["frontier_gate", "market_quarter"]
    )
    labels = [a.get("label", "") for a in affs]
    follow_leads = [l for l in labels if "Follow lead" in l]
    assert len(follow_leads) >= 1
    market_aff = next((a for a in affs if a.get("target_scene_id") == "market_quarter" and "lead" in a.get("label", "").lower()), None)
    assert market_aff is not None


def test_pending_lead_added_when_clue_has_leads_to_scene():
    """Discovering a clue with leads_to_scene adds a pending lead."""
    scene = {
        "scene": {
            "id": "gate",
            "discoverable_clues": [
                {
                    "id": "missing_patrol_tracks",
                    "text": "Bootprints leading toward the river road",
                    "leads_to_scene": "river_road_ambush",
                }
            ],
        }
    }
    session = {}

    revealed = process_investigation_discovery(scene, session)
    assert len(revealed) == 1
    assert revealed[0].get("leads_to_scene") == "river_road_ambush"

    rt = get_scene_runtime(session, "gate")
    assert "Bootprints leading toward the river road" in rt["discovered_clues"]
    leads = rt.get("pending_leads", [])
    assert any(l.get("leads_to_scene") == "river_road_ambush" for l in leads)
    assert get_clue_presentation(session, clue_id="missing_patrol_tracks") == "actionable"
