"""Block 3 — lead lifecycle + strict-social transcript/regression boundaries.

Transcript-style turns (storage patch + TestClient) plus tight regression hooks where
the engine must stay deterministic (explicit pursuit parse, same-scene suppression).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import _apply_authoritative_resolution_state_mutation, app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.affordances import generate_scene_affordances
from game.exploration import finalize_followed_lead
from game.intent_parser import parse_freeform_to_action
from game.leads import LeadLifecycle, LeadStatus, create_lead, debug_dump_leads, get_lead, upsert_lead
from game.storage import get_scene_runtime

pytestmark = [pytest.mark.transcript, pytest.mark.regression]


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _seed_shared_investigate_scene(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate", "reveals_clue": "desk_clue"},
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "desk_clue", "text": "A map indicates patrol locations."},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _seed_runner_dialogue_context(tmp_path, monkeypatch):
    _seed_shared_investigate_scene(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "They were seen near the east lanes.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage._save_json(storage.SESSION_PATH, session)


def _gm_response(text: str, *, tags=None, debug_notes: str = "") -> dict:
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def _scene_envelope(scene_id: str) -> dict:
    return {"scene": {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}}


def _seed_frontier_with_actionable_lead(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["exits"] = [{"label": "To Old Milestone", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("frontier_gate"), gate)
    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rt = get_scene_runtime(session, "frontier_gate")
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="lead_to_ms",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt["pending_leads"] = [
        {
            "clue_id": "c_ms",
            "authoritative_lead_id": "lead_to_ms",
            "text": "Investigate the old milestone",
            "leads_to_scene": "old_milestone",
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_block3_boundary_post_dialogue_reflective_non_social_strict_suppression(tmp_path, monkeypatch):
    """After dialogue engagement, exploration-shaped turns stay GM-safe: no NPC-voiced fallback; meta when suppressed."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        # Substantive narration so retry/guard does not empty the line into social repair; prompt avoids
        # vocative "runner" so npc_directed_guard does not re-bind strict-social on this explore beat.
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "Tacked handbills curl at the desk edge; beneath them, a patrol route is sketched in pencil "
                "along the margin of a grocer's invoice."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "I examine the desk for anything tied to patrol routes.",
                "exploration_action": {
                    "id": "desk",
                    "type": "investigate",
                    "label": "Examine the desk",
                    "prompt": "I examine the desk for anything tied to patrol routes.",
                },
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    gm = data.get("gm_output") or {}
    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert "mutters" not in low
    assert "whispers" not in low
    assert "tavern runner" not in low
    meta = gm.get("_final_emission_meta") or {}
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    assert meta.get("strict_social_suppression_reason") == "exploration_resolution_kind"
    assert meta.get("strict_social_active") is False


def test_block3_boundary_post_dialogue_gate_unit_reflective_question_without_social():
    """Engine-shaped question row without social payload: reflective line must not coerce NPC writer."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "I consider what the runner said about the patrol."
    gm = {
        "player_facing_text": "The noise of the square thins; you hold the thread of it without speaking.",
        "tags": [],
    }
    resolution = {"kind": "question", "prompt": rt["last_player_action_text"]}
    out = apply_final_emission_gate(gm, resolution=resolution, session=session, scene_id=sid, world=world)
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    assert meta.get("strict_social_suppression_reason") == "reflective_or_world_action_prompt"
    assert "mutters" not in out["player_facing_text"].lower()


def test_block3_boundary_post_dialogue_gate_unit_invalid_blob_uses_global_not_npc_on_suppressed_turn():
    """When strict social is suppressed, invalid candidate repair must not attach NPC-voiced fallback."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "I consider the rumors and say nothing."
    gm = {
        "player_facing_text": "From here, no certain answer presents itself in the wet stone and passing boots.",
        "tags": [],
    }
    resolution = {"kind": "observe", "prompt": rt["last_player_action_text"]}
    out = apply_final_emission_gate(gm, resolution=resolution, session=session, scene_id=sid, world=world)
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    low = out["player_facing_text"].lower()
    assert "mutters" not in low
    assert "shakes their head" not in low
    assert "for a breath, the scene holds" in low or "voices shift" in low


def test_block3_boundary_follow_lead_to_missing_npc_fail_closed_no_snap(tmp_path, monkeypatch):
    """Qualified 'follow the lead to Lirael' with only a milestone lead must not resolve or snap to milestone."""
    _seed_frontier_with_actionable_lead(tmp_path, monkeypatch)
    envelope = storage.load_active_scene()
    session = storage.load_session()
    parsed = parse_freeform_to_action(
        "follow the lead to Lirael",
        envelope,
        session=session,
        world=storage.load_world(),
    )
    assert parsed is None


def test_block3_boundary_explicit_pursuit_non_actionable_does_not_transition_commit_or_snap_lead(
    tmp_path, monkeypatch
):
    """Mismatched explicit pursuit phrase: no transition, no follow-lead commitment, no wrong lead binding."""
    _seed_frontier_with_actionable_lead(tmp_path, monkeypatch)
    scene_before = "frontier_gate"

    envelope = storage.load_active_scene()
    session = storage.load_session()
    parsed = parse_freeform_to_action(
        "Pursue the phantom curfew rumor lead",
        envelope,
        session=session,
    )
    assert parsed is None

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You hold the rumor-line loosely; nothing resolves into a path yet."))
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Pursue the phantom curfew rumor lead."})

    assert resp.status_code == 200
    data = resp.json()
    scene_after = str((data.get("scene") or {}).get("scene", {}).get("id") or "").strip()
    assert scene_after == scene_before
    res = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
    assert not (res.get("resolved_transition") is True and res.get("target_scene_id"))
    row = get_lead(storage.load_session(), "lead_to_ms")
    assert row is not None
    assert row.get("lifecycle") != LeadLifecycle.COMMITTED.value


def test_block3_boundary_repeated_pursuit_current_scene_suppressed_no_follow_lead(tmp_path, monkeypatch):
    """Authoritative same-scene transition: suppress reload, strip transition flags, no follow-lead commitment."""
    transition_calls: list[str] = []
    follow_lead_calls: list[tuple[str, ...]] = []

    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        transition_calls.append(str(tid))
        return scene, session, combat

    def fake_follow_lead(session, resolution, normalized_action, *, target_scene_id: str):
        follow_lead_calls.append((str(target_scene_id),))

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)
    monkeypatch.setattr(
        "game.api.apply_follow_lead_commitment_after_resolved_scene_transition",
        fake_follow_lead,
    )

    session: dict = {"turn_counter": 1}
    world: dict = {}
    combat: dict = {}
    scene = _scene_envelope("old_milestone")
    upsert_lead(
        session,
        create_lead(
            title="Loop",
            summary="",
            id="loop_lead",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    normalized_action = {
        "id": "fl",
        "type": "scene_transition",
        "metadata": {"authoritative_lead_id": "loop_lead"},
    }
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "action_id": "fl",
        "state_changes": {
            "scene_changed": True,
            "scene_transition_occurred": True,
            "arrived_at_scene": True,
            "new_scene_context_available": True,
        },
    }

    scene_out, session_out, combat_out, _clues, _rt = _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=normalized_action,
    )

    assert transition_calls == []
    assert follow_lead_calls == []
    assert resolution.get("same_scene_transition_suppressed") is True
    assert resolution.get("transition_applied") is False
    assert resolution.get("resolved_transition") is False
    assert resolution.get("target_scene_id") is None
    assert resolution.get("originating_scene_id") == "old_milestone"
    sc = resolution.get("state_changes") or {}
    assert sc.get("scene_transition_occurred") is None
    assert sc.get("scene_changed") is None
    assert sc.get("arrived_at_scene") is None
    assert sc.get("new_scene_context_available") is None
    row = get_lead(session_out, "loop_lead")
    assert row is not None
    assert row.get("lifecycle") != LeadLifecycle.COMMITTED.value
    assert str(scene_out.get("scene", {}).get("id") or "").strip() == "old_milestone"


def test_block3_boundary_native_social_control_still_allows_speaker_owned_emission():
    """Sanity: true social exchange with social payload remains strict-social active (regression anchor)."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    resolution = {
        "kind": "question",
        "prompt": "Who ordered the patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    gm = {
        "player_facing_text": (
            'Tavern Runner leans in. "Hard to say for certain names—but the watch sergeant signed the route sheet."'
        ),
        "tags": [],
    }
    out = apply_final_emission_gate(gm, resolution=resolution, session=session, scene_id=sid, world=world)
    assert "Tavern Runner" in out["player_facing_text"] or "tavern runner" in out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_active") is True
    assert meta.get("strict_social_suppressed_non_social_turn") is False


def test_block3_transcript_ended_lead_drops_follow_surfaces_registry_retained():
    """After payoff-time resolution, follow affordances / explicit pursuit stop; registry history remains."""
    session: dict = {"turn_counter": 2}
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="lead_to_ms",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "frontier_gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_ms",
            "authoritative_lead_id": "lead_to_ms",
            "text": "Investigate the old milestone",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = {
        "scene": {
            "id": "frontier_gate",
            "visible_facts": [],
            "exits": [{"label": "To Old Milestone", "target_scene_id": "old_milestone"}],
            "mode": "exploration",
        }
    }
    affs_before = generate_scene_affordances(
        scene,
        "exploration",
        session,
        list_scene_ids_fn=lambda: ["frontier_gate", "old_milestone"],
    )
    assert any(
        isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs_before
    )

    finalize_followed_lead(
        session,
        "lead_to_ms",
        terminal_mode="resolved",
        turn=2,
        resolution_type="confirmed",
        resolution_summary="Milestone checked; thread closed.",
    )

    affs_after = generate_scene_affordances(
        scene,
        "exploration",
        session,
        list_scene_ids_fn=lambda: ["frontier_gate", "old_milestone"],
    )
    assert not any(
        isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs_after
    )
    parsed = parse_freeform_to_action(
        "follow the lead",
        scene,
        session=session,
    )
    assert parsed is None

    row = get_lead(session, "lead_to_ms")
    assert row is not None
    assert row.get("lifecycle") == "resolved"
    dump = debug_dump_leads(session)
    assert any(str(r.get("id") or "") == "lead_to_ms" for r in dump)


def test_block3_boundary_different_scene_still_transitions_and_commits(tmp_path, monkeypatch):
    """Control: distinct target scene still applies transition and follow-lead commitment."""
    _patch_storage(tmp_path, monkeypatch)
    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["exits"] = [{"label": "To Old Milestone", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("frontier_gate"), gate)
    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    transition_calls: list[str] = []

    def fake_apply_transition(tid: str, scene: dict, session: dict, combat: dict, world: dict):
        transition_calls.append(str(tid))
        scene2 = _scene_envelope(tid)
        return scene2, session, combat

    monkeypatch.setattr("game.api._apply_authoritative_scene_transition", fake_apply_transition)

    session: dict = {"turn_counter": 1}
    world = {}
    combat = {}
    scene = _scene_envelope("frontier_gate")
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="to_ms",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    normalized_action = {
        "id": "go",
        "type": "scene_transition",
        "metadata": {"authoritative_lead_id": "to_ms"},
    }
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "action_id": "go",
    }

    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=normalized_action,
    )

    assert transition_calls == ["old_milestone"]
    assert resolution.get("same_scene_transition_suppressed") is None
    assert resolution.get("transition_applied") is None
    row = get_lead(session, "to_ms")
    assert row is not None
    assert row.get("lifecycle") == LeadLifecycle.COMMITTED.value
