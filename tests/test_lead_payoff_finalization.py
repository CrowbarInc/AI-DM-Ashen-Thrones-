"""Block 4B — destination lead payoff finalizes pursued registry leads after grounded arrival."""
from __future__ import annotations

from game.affordances import generate_scene_affordances
from game.api import _apply_authoritative_resolution_state_mutation
from game.exploration import (
    RESOLUTION_TYPE_REACHED_DESTINATION,
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition,
)
from game.leads import LeadLifecycle, LeadStatus, create_lead, debug_dump_leads, get_lead, upsert_lead
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime


def _scene_env(scene_id: str) -> dict:
    return {"scene": {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}}


def test_ordinary_follow_scene_transition_finalizes_authoritative_destination_lead(monkeypatch):
    """Successful follow into the lead's destination scene resolves the lead (via API mutation path)."""

    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 7}
    upsert_lead(
        session,
        create_lead(
            title="Old milestone",
            summary="",
            id="payoff_lead_a",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["frontier_gate", "old_milestone"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "follow-x",
            "label": "Follow lead: rumor",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "prompt": "I follow.",
            "metadata": {
                "authoritative_lead_id": "payoff_lead_a",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
                "target_scene_id": "old_milestone",
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "action_id": "follow-x",
        "success": True,
    }
    world: dict = {}
    combat: dict = {}
    scene = _scene_env("frontier_gate")

    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=norm,
    )

    row = get_lead(session, "payoff_lead_a")
    assert row is not None
    assert row.get("lifecycle") == "resolved"
    assert row.get("status") == "resolved"
    assert row.get("resolved_at_turn") == 7
    assert row.get("resolution_type") == RESOLUTION_TYPE_REACHED_DESTINATION
    dump = debug_dump_leads(session)
    assert any(r.get("id") == "payoff_lead_a" for r in dump)


def test_finalize_drops_follow_affordance_pending_row_still_in_registry(monkeypatch):
    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(
            title="Thread",
            summary="",
            id="payoff_lead_b",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["gate", "dest_scene"],
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "payoff_lead_b",
            "text": "They went to dest.",
            "leads_to_scene": "dest_scene",
        }
    ]
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "exits": [],
            "mode": "exploration",
        }
    }
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead: …",
            "type": "scene_transition",
            "targetSceneId": "dest_scene",
            "metadata": {
                "authoritative_lead_id": "payoff_lead_b",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
                "target_scene_id": "dest_scene",
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "dest_scene",
        "action_id": "fl",
        "success": True,
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=scene,
        resolution=resolution,
        normalized_action=norm,
    )
    affs = generate_scene_affordances(
        scene,
        "exploration",
        session,
        list_scene_ids_fn=lambda: ["gate", "dest_scene"],
    )
    assert not any(
        isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs
    )
    assert get_lead(session, "payoff_lead_b") is not None


def test_no_finalize_when_registry_lacks_destination_scene(monkeypatch):
    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 3}
    upsert_lead(
        session,
        create_lead(
            title="No scene ids",
            summary="",
            id="payoff_lead_c",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "metadata": {
                "authoritative_lead_id": "payoff_lead_c",
                "commitment_source": "follow_lead_affordance",
                "target_scene_id": "old_milestone",
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "success": True,
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=_scene_env("gate"),
        resolution=resolution,
        normalized_action=norm,
    )
    row = get_lead(session, "payoff_lead_c")
    assert row is not None
    assert row.get("lifecycle") == LeadLifecycle.COMMITTED.value
    assert row.get("status") == LeadStatus.PURSUED.value


def test_no_finalize_when_encoded_action_destination_mismatches_resolution(monkeypatch):
    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(
            title="X",
            summary="",
            id="payoff_lead_d",
            lifecycle=LeadLifecycle.DISCOVERED,
            related_scene_ids=["a", "b"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "type": "scene_transition",
            "targetSceneId": "b",
            "metadata": {"authoritative_lead_id": "payoff_lead_d", "target_scene_id": "b"},
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "a",
        "success": True,
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=_scene_env("x"),
        resolution=resolution,
        normalized_action=norm,
    )
    row = get_lead(session, "payoff_lead_d")
    assert row.get("lifecycle") != "resolved"


def test_no_finalize_when_committed_lead_metadata_inconsistent():
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(
            title="Y",
            summary="",
            id="payoff_lead_e",
            lifecycle=LeadLifecycle.DISCOVERED,
            related_scene_ids=["here", "there"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "type": "scene_transition",
            "targetSceneId": "there",
            "metadata": {"authoritative_lead_id": "payoff_lead_e"},
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "there",
        "success": True,
        "metadata": {"committed_lead_id": "some_other_lead"},
    }
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
        session, resolution, norm, target_scene_id="there"
    )
    assert get_lead(session, "payoff_lead_e").get("lifecycle") != "resolved"


def test_qualified_pursuit_style_top_level_target_finalizes_without_metadata_target(monkeypatch):
    """Explicit pursuit uses target on the action root; payoff finalization still runs."""

    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 2}
    upsert_lead(
        session,
        create_lead(
            title="Pursuit",
            summary="",
            id="payoff_lead_f",
            lifecycle=LeadLifecycle.DISCOVERED,
            related_scene_ids=["gate", "old_milestone"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "pursue",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "metadata": {
                "authoritative_lead_id": "payoff_lead_f",
                "commitment_source": "explicit_player_pursuit",
                "commitment_strength": 1,
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "success": True,
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=_scene_env("gate"),
        resolution=resolution,
        normalized_action=norm,
    )
    row = get_lead(session, "payoff_lead_f")
    assert row.get("resolution_type") == RESOLUTION_TYPE_REACHED_DESTINATION
