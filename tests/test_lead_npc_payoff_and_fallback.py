"""Block 5B — NPC-target lead payoff on grounded contact + neutral fallback for failed pursuit turns."""
from __future__ import annotations

from game.api import _apply_authoritative_resolution_state_mutation
from game.exploration import (
    NPC_PURSUIT_CONTACT_SESSION_KEY,
    RESOLUTION_TYPE_REACHED_DESTINATION,
    RESOLUTION_TYPE_REACHED_NPC,
    maybe_finalize_pursued_lead_npc_contact_payoff,
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition,
)
from game.final_emission_gate import apply_final_emission_gate
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
from game.scene_actions import normalize_scene_action


def _scene_env(scene_id: str) -> dict:
    return {"scene": {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}}


def test_npc_target_lead_not_resolved_on_scene_arrival_only(monkeypatch):
    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 2}
    upsert_lead(
        session,
        create_lead(
            title="Find NPC",
            summary="",
            id="npc_only_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["gate", "old_milestone"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "go",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "metadata": {
                "authoritative_lead_id": "npc_only_lead",
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
        "metadata": {"committed_lead_id": "npc_only_lead"},
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=_scene_env("gate"),
        resolution=resolution,
        normalized_action=norm,
    )
    row = get_lead(session, "npc_only_lead")
    assert row is not None
    assert row.get("lifecycle") == LeadLifecycle.COMMITTED.value
    assert row.get("status") == LeadStatus.PURSUED.value
    assert row.get("resolution_type") != RESOLUTION_TYPE_REACHED_NPC
    ctx = session.get(NPC_PURSUIT_CONTACT_SESSION_KEY)
    assert isinstance(ctx, dict)
    assert ctx.get("target_npc_id") == "emergent_town_crier"


def test_api_mutation_finalizes_npc_contact_via_session_context():
    session: dict = {"turn_counter": 11}
    upsert_lead(
        session,
        create_lead(
            title="Thread",
            summary="",
            id="api_npc_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["old_milestone"],
        ),
    )
    session[NPC_PURSUIT_CONTACT_SESSION_KEY] = {
        "authoritative_lead_id": "api_npc_lead",
        "target_kind": "npc",
        "target_npc_id": "emergent_town_crier",
        "destination_scene_id": "old_milestone",
        "commitment_source": "explicit_player_pursuit",
        "commitment_strength": 2,
    }
    norm = normalize_scene_action({"id": "q1", "type": "question", "prompt": "Hello."})
    resolution = {
        "kind": "question",
        "action_id": "q1",
        "success": True,
        "social": {
            "npc_id": "emergent_town_crier",
            "target_resolved": True,
            "grounded_speaker_id": "emergent_town_crier",
        },
    }
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world={},
        combat={},
        scene=_scene_env("old_milestone"),
        resolution=resolution,
        normalized_action=norm,
    )
    row = get_lead(session, "api_npc_lead")
    assert row.get("resolution_type") == RESOLUTION_TYPE_REACHED_NPC
    assert session.get(NPC_PURSUIT_CONTACT_SESSION_KEY) is None


def test_npc_target_lead_resolves_on_grounded_social_match():
    session: dict = {"turn_counter": 4}
    upsert_lead(
        session,
        create_lead(
            title="Thread",
            summary="",
            id="npc_payoff_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["old_milestone"],
        ),
    )
    session[NPC_PURSUIT_CONTACT_SESSION_KEY] = {
        "authoritative_lead_id": "npc_payoff_lead",
        "target_kind": "npc",
        "target_npc_id": "emergent_town_crier",
        "destination_scene_id": "old_milestone",
        "commitment_source": "explicit_player_pursuit",
        "commitment_strength": 2,
    }
    norm = normalize_scene_action(
        {
            "id": "ask",
            "type": "question",
            "prompt": "I need a word with you.",
            "metadata": {},
        }
    )
    resolution = {
        "kind": "question",
        "action_id": "ask",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "emergent_town_crier",
            "npc_name": "Lirael",
            "target_resolved": True,
            "grounded_speaker_id": "emergent_town_crier",
        },
    }
    maybe_finalize_pursued_lead_npc_contact_payoff(session, resolution, norm)
    row = get_lead(session, "npc_payoff_lead")
    assert row is not None
    assert row.get("lifecycle") == "resolved"
    assert row.get("status") == "resolved"
    assert row.get("resolution_type") == RESOLUTION_TYPE_REACHED_NPC
    assert session.get(NPC_PURSUIT_CONTACT_SESSION_KEY) is None


def test_npc_target_lead_not_resolved_when_grounded_npc_mismatches():
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(
            title="Thread",
            summary="",
            id="wrong_npc_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["old_milestone"],
        ),
    )
    session[NPC_PURSUIT_CONTACT_SESSION_KEY] = {
        "authoritative_lead_id": "wrong_npc_lead",
        "target_kind": "npc",
        "target_npc_id": "emergent_town_crier",
        "destination_scene_id": "old_milestone",
        "commitment_source": "explicit_player_pursuit",
        "commitment_strength": 2,
    }
    resolution = {
        "kind": "question",
        "success": True,
        "social": {
            "npc_id": "other_npc",
            "target_resolved": True,
            "grounded_speaker_id": "other_npc",
        },
    }
    maybe_finalize_pursued_lead_npc_contact_payoff(session, resolution, None)
    row = get_lead(session, "wrong_npc_lead")
    assert row.get("lifecycle") == LeadLifecycle.COMMITTED.value
    assert row.get("status") == LeadStatus.PURSUED.value


def test_npc_target_lead_not_resolved_on_social_fail_closed():
    session: dict = {"turn_counter": 3}
    upsert_lead(
        session,
        create_lead(
            title="Thread",
            summary="",
            id="fail_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["old_milestone"],
        ),
    )
    session[NPC_PURSUIT_CONTACT_SESSION_KEY] = {
        "authoritative_lead_id": "fail_lead",
        "target_kind": "npc",
        "target_npc_id": "emergent_town_crier",
        "commitment_source": "explicit_player_pursuit",
        "commitment_strength": 2,
    }
    resolution = {
        "kind": "question",
        "success": False,
        "social": {
            "npc_id": None,
            "target_resolved": False,
        },
    }
    maybe_finalize_pursued_lead_npc_contact_payoff(session, resolution, None)
    assert get_lead(session, "fail_lead").get("lifecycle") == LeadLifecycle.COMMITTED.value


def test_emission_gate_replaces_stock_global_fallback_for_failed_npc_pursuit_social(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: False,
    )
    session: dict = {}
    session[NPC_PURSUIT_CONTACT_SESSION_KEY] = {
        "authoritative_lead_id": "lead_x",
        "target_kind": "npc",
        "target_npc_id": "emergent_town_crier",
        "commitment_source": "explicit_player_pursuit",
        "commitment_strength": 2,
    }
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": None,
            "target_resolved": False,
        },
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "From here, no certain answer presents itself about the patrol.",
            "tags": [],
        },
        resolution=resolution,
        session=session,
        scene_id="old_milestone",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert "For a breath, the scene holds while voices shift around you." not in text
    assert "voices shift around you" not in text.lower()
    assert "unresolved" in text.lower() or "nothing confirms" in text.lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("final_emitted_source") == "npc_pursuit_neutral_fallback"


def test_destination_scene_payoff_unchanged_for_scene_target_kind(monkeypatch):
    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        return _scene_env(tid), session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 9}
    upsert_lead(
        session,
        create_lead(
            title="Place",
            summary="",
            id="scene_kind_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
            related_scene_ids=["a", "dest_scene"],
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "type": "scene_transition",
            "targetSceneId": "dest_scene",
            "metadata": {
                "authoritative_lead_id": "scene_kind_lead",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
                "target_kind": "scene",
                "target_scene_id": "dest_scene",
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "dest_scene",
        "success": True,
    }
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
        session, resolution, norm, target_scene_id="dest_scene"
    )
    row = get_lead(session, "scene_kind_lead")
    assert row is not None
    assert row.get("lifecycle") == "resolved"
    assert row.get("resolution_type") == RESOLUTION_TYPE_REACHED_DESTINATION
