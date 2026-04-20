"""Deterministic scene destination binding: named places vs lead-derived targets.

Scene Transition Integrity (STI) closeout — end-to-end chain invariants (parser → binding →
compatibility → authoritative mutation → final emission metadata):

Explicit named destination beats a discovered lead suggestion unless the player explicitly
pursues the lead; incompatible destinations do not commit; blocked travel-like turns do not
receive wrong-scene global fallback narration (integrity-safe fallback / stock line instead).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

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
from game.exploration import resolve_exploration_action
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.intent_parser import parse_freeform_to_action
from game.narrative_authenticity_eval import _extract_final_emission_meta
from game.leads import LeadLifecycle, LeadStatus, create_lead, upsert_lead
from game.scene_destination_binding import (
    evaluate_destination_semantic_compatibility,
    extract_last_explicit_named_place,
    infer_travel_semantic_bucket_for_scene,
    reconcile_scene_transition_destination,
)
from game.storage import get_scene_runtime


def _gate_with_stone_boar_and_milestone_exits() -> dict:
    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["exits"] = [
        {"label": "Enter the Stone Boar", "target_scene_id": "stone_boar_tavern"},
        {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"},
    ]
    return gate


def test_enter_stone_boar_not_old_milestone_when_follows_instructions_in_same_sentence():
    """Regression: 'follows' must not arm legacy follow exit latch onto a different exit."""
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    text = "Galinor follows the instructions, entering the Stone Boar."
    act = parse_freeform_to_action(text, env, session=default_session(), world=default_world())
    assert act is not None
    assert act.get("type") == "scene_transition"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "stone_boar_tavern"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) != "old_milestone"


def test_reconcile_prefers_explicit_named_place_over_wrong_proposed_target():
    """Engine layer: authoritative embedded place beats an unrelated parser target."""
    scene = _gate_with_stone_boar_and_milestone_exits()
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor follows the instructions, entering the Stone Boar.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {"parser_lane": "legacy_follow_exit_match"},
    }
    out = reconcile_scene_transition_destination(
        normalized_action=na,
        prompt=na["prompt"],
        raw_player_text=na["prompt"],
        exits=scene["scene"]["exits"],
        known_scene_ids={"stone_boar_tavern", "old_milestone", "frontier_gate"},
        proposed_target_scene_id="old_milestone",
        inferred_target_scene_id=None,
    )
    assert out["effective_target_scene_id"] == "stone_boar_tavern"
    assert out["destination_binding_conflict"] is True
    assert set(out["destination_binding_conflict_candidates"]) == {"old_milestone", "stone_boar_tavern"}
    assert out["destination_semantic_kind"] == "named_place"


def test_lead_derived_scene_transition_still_works_without_competing_named_place():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    upsert_lead(
        session,
        create_lead(
            id="ms_lead",
            title="Milestone rumor",
            summary="",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    rt = get_scene_runtime(session, "frontier_gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "ms_lead",
            "text": "Patrol rumor",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    act = parse_freeform_to_action(
        "follow the lead",
        env,
        session=session,
        world=default_world(),
    )
    assert act is not None
    assert act.get("type") == "scene_transition"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "old_milestone"


def test_reconcile_keeps_authoritative_pursuit_when_no_named_place_in_text():
    na = {
        "id": "a",
        "label": "follow the lead",
        "type": "scene_transition",
        "prompt": "follow the lead",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {
            "authoritative_lead_id": "ms_lead",
            "commitment_source": "explicit_player_pursuit",
            "destination_scene_id": "old_milestone",
        },
    }
    out = reconcile_scene_transition_destination(
        normalized_action=na,
        prompt=na["prompt"],
        raw_player_text=na["prompt"],
        exits=[],
        known_scene_ids={"old_milestone"},
        proposed_target_scene_id="old_milestone",
    )
    assert out["effective_target_scene_id"] == "old_milestone"
    assert out["destination_semantic_kind"] == "lead_scene"


def test_unresolved_named_place_does_not_keep_legacy_follow_exit():
    """Fail safe: dangling place name + legacy follow latch → no silent unrelated scene."""
    scene = default_scene("frontier_gate")
    scene["scene"]["id"] = "frontier_gate"
    scene["scene"]["exits"] = [
        {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"},
    ]
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor follows the instructions, entering the Ghost Palace.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {"parser_lane": "legacy_follow_exit_match"},
    }
    res = resolve_exploration_action(
        {"scene": scene["scene"]},
        default_session(),
        default_world(),
        na,
        raw_player_text=na["prompt"],
        list_scene_ids=lambda: ["frontier_gate", "old_milestone"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("resolved_transition") is not True
    assert res.get("target_scene_id") in (None, "")
    md = res.get("metadata") or {}
    assert md.get("destination_binding_source") == "explicit_named_place_unresolved"


def test_extract_last_explicit_named_place_prefers_final_embedded_clause():
    text = "We talk, then enter the Stone Boar."
    assert extract_last_explicit_named_place(text) == "Stone Boar"


def test_evaluate_compatibility_blocks_enter_stone_boar_against_old_milestone():
    na = {"id": "x", "type": "scene_transition", "metadata": {}}
    scene = _gate_with_stone_boar_and_milestone_exits()
    out = evaluate_destination_semantic_compatibility(
        normalized_action=na,
        raw_player_text="Galinor enters the Stone Boar.",
        prompt="Galinor enters the Stone Boar.",
        effective_target_scene_id="old_milestone",
        destination_semantic_kind="explicit_scene_id",
        exits=scene["scene"]["exits"],
        load_scene_fn=None,
    )
    assert out["destination_compatibility_checked"] is True
    assert out["destination_compatibility_passed"] is False
    assert out["blocked_incompatible_scene_transition"] is True
    assert out["compatibility_clear_target"] is True
    assert "mismatch" in (out.get("destination_compatibility_failure_reason") or "")


def test_infer_bucket_old_milestone_is_outdoor():
    assert infer_travel_semantic_bucket_for_scene(None, scene_id="old_milestone") == "outdoor_road_wilderness_ruin"


def test_infer_bucket_tavern_id_is_interior():
    assert infer_travel_semantic_bucket_for_scene(None, scene_id="stone_boar_tavern") == "interior_establishment"


def test_resolve_exploration_blocks_hypothetical_wrong_bind_stone_boar_to_milestone():
    """Backstop: if binding ever returned the wrong outdoor scene for a tavern phrase, exploration must not resolve."""
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor enters the Stone Boar.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {"parser_lane": "legacy_follow_exit_match"},
    }
    fake_rebind = {
        "effective_target_scene_id": "old_milestone",
        "destination_binding_source": "normalized_action_target",
        "destination_binding_conflict": False,
        "destination_binding_conflict_candidates": [],
        "destination_binding_resolution_reason": "forced_test_bind",
        "destination_semantic_kind": "explicit_scene_id",
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }
    with patch("game.exploration.reconcile_scene_transition_destination", return_value=fake_rebind):
        res = resolve_exploration_action(
            env,
            default_session(),
            default_world(),
            na,
            raw_player_text=na["prompt"],
            list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
            scene_graph=None,
            load_scene_fn=None,
        )
    assert res.get("resolved_transition") is not True
    assert res.get("target_scene_id") in (None, "")
    md = res.get("metadata") or {}
    assert md.get("blocked_incompatible_scene_transition") is True
    assert md.get("destination_compatibility_passed") is False


def test_head_to_old_milestone_still_resolves():
    """Outdoor declared place + outdoor target: binding and compatibility both allow the transition."""
    scene = _gate_with_stone_boar_and_milestone_exits()
    scene["scene"]["exits"] = list(scene["scene"]["exits"]) + [
        {"label": "The old milestone", "target_scene_id": "old_milestone"},
    ]
    env = {"scene": scene["scene"]}
    text = "I head to the old milestone"
    na = {
        "id": "travel_milestone",
        "label": text,
        "type": "scene_transition",
        "prompt": text,
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {"parser_lane": "declared_travel_test"},
    }
    res = resolve_exploration_action(
        env,
        default_session(),
        default_world(),
        na,
        raw_player_text=text,
        list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    md = res.get("metadata") or {}
    assert md.get("destination_compatibility_passed") is True
    assert md.get("blocked_incompatible_scene_transition") is not True


def test_enter_stone_boar_named_place_transition_compatible():
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    text = "Galinor enters the Stone Boar."
    act = parse_freeform_to_action(text, env, session=default_session(), world=default_world())
    assert act is not None
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "stone_boar_tavern"
    res = resolve_exploration_action(
        env,
        default_session(),
        default_world(),
        act,
        raw_player_text=text,
        list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "stone_boar_tavern"
    md = res.get("metadata") or {}
    assert md.get("destination_compatibility_passed") is True


def test_active_scene_unchanged_after_api_apply_when_compatibility_blocked_resolution():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    world = default_world()
    combat: dict = {}
    scene = _gate_with_stone_boar_and_milestone_exits()
    fake_rebind = {
        "effective_target_scene_id": "old_milestone",
        "destination_binding_source": "normalized_action_target",
        "destination_binding_conflict": False,
        "destination_binding_conflict_candidates": [],
        "destination_binding_resolution_reason": "forced_test_bind",
        "destination_semantic_kind": "explicit_scene_id",
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor enters the Stone Boar.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {},
    }
    with patch("game.exploration.reconcile_scene_transition_destination", return_value=fake_rebind):
        resolution = resolve_exploration_action(
            {"scene": scene["scene"]},
            session,
            world,
            na,
            raw_player_text=na["prompt"],
            list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
            scene_graph=None,
            load_scene_fn=None,
        )
    assert resolution.get("resolved_transition") is not True
    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=na,
    )
    assert session.get("active_scene_id") == "frontier_gate"


_REPO_ROOT = Path(__file__).resolve().parents[1]

_STI_SCENE_INTEGRITY_META_KEYS = frozenset(
    {
        "scene_integrity_checked",
        "scene_integrity_passed",
        "scene_integrity_failure_reasons",
        "scene_integrity_blocked_global_fallback",
        "scene_integrity_named_destination",
    }
)


def _load_old_milestone_envelope() -> dict:
    p = _REPO_ROOT / "data" / "scenes" / "old_milestone.json"
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _banned_stock_gm_line() -> str:
    """Triggers ``banned_stock_phrase`` handling on the non-strict final emission path."""
    return (
        "From here, no certain answer presents itself about the road ahead, "
        "so you watch the dust settle instead."
    )


def _session_with_milestone_lead() -> dict:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    upsert_lead(
        session,
        create_lead(
            id="ms_lead",
            title="Milestone rumor",
            summary="",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    rt = get_scene_runtime(session, "frontier_gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "ms_lead",
            "text": "Patrol rumor",
            "leads_to_scene": "old_milestone",
        }
    ]
    return session


def _stone_boar_minimal_scene() -> dict:
    return {
        "scene": {
            "id": "stone_boar_tavern",
            "location": "The Stone Boar",
            "summary": "A noisy frontier tavern common room.",
            "mode": "exploration",
            "visible_facts": ["Hearth smoke, spilled ale, low voices."],
            "exits": [{"label": "Return to the gate", "target_scene_id": "frontier_gate"}],
        }
    }


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


def _seed_sti_http_pack(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    gate = _gate_with_stone_boar_and_milestone_exits()
    gate["scene"]["exits"] = list(gate["scene"]["exits"]) + [
        {"label": "The old milestone", "target_scene_id": "old_milestone"},
    ]
    storage._save_json(storage.scene_path("frontier_gate"), gate)
    storage._save_json(storage.scene_path("stone_boar_tavern"), _stone_boar_minimal_scene())
    storage._save_json(storage.scene_path("old_milestone"), _load_old_milestone_envelope())
    session = _session_with_milestone_lead()
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _assert_sti_binding_and_compat_present(md: dict, *, expect_compat_failed: bool) -> None:
    assert md.get("destination_binding_source")
    assert "destination_semantic_kind" in md
    assert md.get("destination_compatibility_checked") is True
    if expect_compat_failed:
        assert md.get("destination_compatibility_passed") is False
        assert md.get("blocked_incompatible_scene_transition") is True
        assert str(md.get("destination_compatibility_failure_reason") or "").strip()
    else:
        assert md.get("destination_compatibility_passed") is True
        assert md.get("blocked_incompatible_scene_transition") is not True


def _assert_scene_integrity_meta_shape(fem: dict, *, expect_failure: bool) -> None:
    keys = {k for k in fem.keys() if k.startswith("scene_integrity_")}
    assert keys <= _STI_SCENE_INTEGRITY_META_KEYS
    assert fem.get("scene_integrity_checked") is True
    if expect_failure:
        assert fem.get("scene_integrity_passed") is False
        assert fem.get("scene_integrity_blocked_global_fallback") is True
        assert fem.get("final_emitted_source") == "scene_emit_integrity_safe_fallback"
    else:
        assert fem.get("scene_integrity_passed") is True
        assert fem.get("scene_integrity_blocked_global_fallback") is not True


def test_sti_e2e_enter_stone_boar_does_not_land_old_milestone():
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    text = "Galinor enters the Stone Boar."
    act = parse_freeform_to_action(text, env, session=default_session(), world=default_world())
    assert act is not None
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "stone_boar_tavern"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) != "old_milestone"
    assert (act.get("metadata") or {}).get("parser_lane") != "legacy_follow_exit_match"


def test_sti_e2e_head_to_old_milestone_still_resolves_through_chain():
    scene = _gate_with_stone_boar_and_milestone_exits()
    scene["scene"]["exits"] = list(scene["scene"]["exits"]) + [
        {"label": "The old milestone", "target_scene_id": "old_milestone"},
    ]
    env = {"scene": scene["scene"]}
    text = "I head to the old milestone"
    act = parse_freeform_to_action(text, env, session=default_session(), world=default_world())
    assert act is not None
    assert act.get("type") == "scene_transition"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "old_milestone"
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    world = default_world()
    combat: dict = {}
    res = resolve_exploration_action(
        env,
        session,
        world,
        act,
        raw_player_text=text,
        list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    scene2, session2, combat2, _, _ = _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=res,
        normalized_action=act,
    )
    assert session2.get("active_scene_id") == "old_milestone"
    assert scene2["scene"]["id"] == "old_milestone"


def test_sti_e2e_named_place_beats_discovered_lead_without_explicit_pursuit():
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    session = _session_with_milestone_lead()
    text = "Galinor enters the Stone Boar."
    act = parse_freeform_to_action(text, env, session=session, world=default_world())
    assert act is not None
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "stone_boar_tavern"
    world = default_world()
    combat: dict = {}
    res = resolve_exploration_action(
        env,
        session,
        world,
        act,
        raw_player_text=text,
        list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "stone_boar_tavern"
    md = res.get("metadata") or {}
    assert md.get("destination_semantic_kind") == "named_place"


def test_sti_e2e_incompatible_forced_target_blocks_before_scene_mutation_and_gate_safe_fallback():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    world = default_world()
    combat: dict = {}
    scene = _gate_with_stone_boar_and_milestone_exits()
    fake_rebind = {
        "effective_target_scene_id": "old_milestone",
        "destination_binding_source": "normalized_action_target",
        "destination_binding_conflict": False,
        "destination_binding_conflict_candidates": [],
        "destination_binding_resolution_reason": "forced_test_bind",
        "destination_semantic_kind": "explicit_scene_id",
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor enters the Stone Boar.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {},
    }
    with patch("game.exploration.reconcile_scene_transition_destination", return_value=fake_rebind):
        resolution = resolve_exploration_action(
            {"scene": scene["scene"]},
            session,
            world,
            na,
            raw_player_text=na["prompt"],
            list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
            scene_graph=None,
            load_scene_fn=None,
        )
    assert resolution.get("resolved_transition") is not True
    assert resolution.get("target_scene_id") in (None, "")
    md = resolution.get("metadata") or {}
    _assert_sti_binding_and_compat_present(md, expect_compat_failed=True)

    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=na,
    )
    assert session.get("active_scene_id") == "frontier_gate"

    wrong_envelope = _load_old_milestone_envelope()
    out = apply_final_emission_gate(
        {"player_facing_text": _banned_stock_gm_line(), "tags": []},
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=wrong_envelope,
        world=world,
    )
    fem = read_final_emission_meta_dict(out) or {}
    _assert_scene_integrity_meta_shape(fem, expect_failure=True)
    low = str(out.get("player_facing_text") or "").lower()
    assert "blasted scrub" not in low
    assert "black rainwater" not in low
    assert "carrion" not in low
    assert "weathered milestone" not in low


def test_sti_e2e_valid_aligned_transition_allows_global_scene_fallback_line():
    session = default_session()
    session["active_scene_id"] = "old_milestone"
    world = default_world()
    envelope = _load_old_milestone_envelope()
    resolution = {
        "kind": "scene_transition",
        "prompt": "I head to the old milestone.",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "metadata": {
            "destination_binding_source": "normalized_action_target",
            "destination_semantic_kind": "named_place",
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "blocked_incompatible_scene_transition": False,
        },
    }
    out = apply_final_emission_gate(
        {"player_facing_text": _banned_stock_gm_line(), "tags": []},
        resolution=resolution,
        session=session,
        scene_id="old_milestone",
        scene=envelope,
        world=world,
    )
    fem = read_final_emission_meta_dict(out) or {}
    _assert_scene_integrity_meta_shape(fem, expect_failure=False)
    assert fem.get("final_emitted_source") == "global_scene_fallback"
    low = str(out.get("player_facing_text") or "").lower()
    assert "milestone" in low or "road" in low or "rain" in low or "scrub" in low


def test_sti_integration_innkeeper_bed_stone_boar_with_milestone_lead_bug_shape():
    """Minimal real-bug shape: milestone lead present + NPC-style instruction + enter named tavern."""
    scene = _gate_with_stone_boar_and_milestone_exits()
    env = {"scene": scene["scene"]}
    session = _session_with_milestone_lead()
    text = "As instructed, I enter the Stone Boar and head for a bed."
    act = parse_freeform_to_action(text, env, session=session, world=default_world())
    assert act is not None
    assert act.get("type") == "scene_transition"
    assert (act.get("targetSceneId") or act.get("target_scene_id")) == "stone_boar_tavern"
    assert (act.get("metadata") or {}).get("parser_lane") != "legacy_follow_exit_match"

    world = default_world()
    combat: dict = {}
    res = resolve_exploration_action(
        env,
        session,
        world,
        act,
        raw_player_text=text,
        list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
        scene_graph=None,
        load_scene_fn=None,
    )
    assert res.get("target_scene_id") == "stone_boar_tavern"
    assert res.get("resolved_transition") is True
    md = res.get("metadata") or {}
    assert md.get("destination_semantic_kind") == "named_place"
    _assert_sti_binding_and_compat_present(md, expect_compat_failed=False)

    fake_rebind = {
        "effective_target_scene_id": "old_milestone",
        "destination_binding_source": "normalized_action_target",
        "destination_binding_conflict": False,
        "destination_binding_conflict_candidates": [],
        "destination_binding_resolution_reason": "hypothetical_bad_bind",
        "destination_semantic_kind": "explicit_scene_id",
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }
    na_bad = {**act, "targetSceneId": "old_milestone", "target_scene_id": "old_milestone"}
    with patch("game.exploration.reconcile_scene_transition_destination", return_value=fake_rebind):
        blocked = resolve_exploration_action(
            env,
            session,
            world,
            na_bad,
            raw_player_text=text,
            list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
            scene_graph=None,
            load_scene_fn=None,
        )
    assert blocked.get("resolved_transition") is not True
    assert blocked.get("target_scene_id") in (None, "")
    assert (blocked.get("metadata") or {}).get("blocked_incompatible_scene_transition") is True

    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=blocked,
        normalized_action=na_bad,
    )
    assert session.get("active_scene_id") == "frontier_gate"

    gate_out = apply_final_emission_gate(
        {"player_facing_text": _banned_stock_gm_line(), "tags": []},
        resolution=blocked,
        session=session,
        scene_id="frontier_gate",
        scene=_load_old_milestone_envelope(),
        world=world,
    )
    low = str(gate_out.get("player_facing_text") or "").lower()
    assert "blasted scrub" not in low
    assert "black rainwater" not in low
    assert "weathered milestone" not in low
    assert (read_final_emission_meta_dict(gate_out) or {}).get("final_emitted_source") == "scene_emit_integrity_safe_fallback"


def test_sti_metadata_invariants_blocked_case_layers_sti1_sti2_sti3():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    world = default_world()
    scene = _gate_with_stone_boar_and_milestone_exits()
    fake_rebind = {
        "effective_target_scene_id": "old_milestone",
        "destination_binding_source": "normalized_action_target",
        "destination_binding_conflict": False,
        "destination_binding_conflict_candidates": [],
        "destination_binding_resolution_reason": "forced_test_bind",
        "destination_semantic_kind": "explicit_scene_id",
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }
    na = {
        "id": "x",
        "label": "x",
        "type": "scene_transition",
        "prompt": "Galinor enters the Stone Boar.",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {},
    }
    with patch("game.exploration.reconcile_scene_transition_destination", return_value=fake_rebind):
        resolution = resolve_exploration_action(
            {"scene": scene["scene"]},
            session,
            world,
            na,
            raw_player_text=na["prompt"],
            list_scene_ids=lambda: ["frontier_gate", "old_milestone", "stone_boar_tavern"],
            scene_graph=None,
            load_scene_fn=None,
        )
    md = resolution.get("metadata") or {}
    for k in (
        "destination_binding_source",
        "destination_binding_resolution_reason",
        "destination_semantic_kind",
        "destination_compatibility_checked",
        "destination_compatibility_passed",
        "destination_compatibility_failure_reason",
        "blocked_incompatible_scene_transition",
    ):
        assert k in md

    out = apply_final_emission_gate(
        {"player_facing_text": _banned_stock_gm_line(), "tags": []},
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=_load_old_milestone_envelope(),
        world=world,
    )
    fem = read_final_emission_meta_dict(out) or {}
    for k in _STI_SCENE_INTEGRITY_META_KEYS:
        assert k in fem
    assert "blocked_incompatible_scene_transition" in (fem.get("scene_integrity_failure_reasons") or [])


@pytest.mark.integration
def test_sti_http_chat_enter_stone_boar_full_stack(tmp_path, monkeypatch):
    """Thin HTTP chain: persisted scenes + session → /api/chat → transition + emission meta."""
    _seed_sti_http_pack(tmp_path, monkeypatch)
    fake_gpt = {
        "player_facing_text": "[Narration: you step into the Stone Boar.]",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_a, **_k: fake_gpt)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Galinor enters the Stone Boar."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "stone_boar_tavern"
    res = data.get("resolution") or {}
    assert res.get("kind") == "scene_transition"
    assert res.get("target_scene_id") == "stone_boar_tavern"
    rmd = res.get("metadata") or {}
    assert rmd.get("destination_compatibility_passed") is True
    fem = _extract_final_emission_meta(data) or {}
    assert fem.get("scene_integrity_checked") is True
    assert fem.get("scene_integrity_passed") is True


def test_authoritative_pursuit_skips_compatibility_even_if_buckets_differ():
    na = {
        "id": "a",
        "label": "follow",
        "type": "scene_transition",
        "prompt": "I enter the Stone Boar",
        "targetSceneId": "old_milestone",
        "target_scene_id": "old_milestone",
        "metadata": {
            "authoritative_lead_id": "ms_lead",
            "commitment_source": "explicit_player_pursuit",
            "destination_scene_id": "old_milestone",
        },
    }
    out = evaluate_destination_semantic_compatibility(
        normalized_action=na,
        raw_player_text="I enter the Stone Boar",
        prompt="I enter the Stone Boar",
        effective_target_scene_id="old_milestone",
        destination_semantic_kind="lead_scene",
        exits=[],
        load_scene_fn=None,
    )
    assert out["destination_compatibility_passed"] is True
    assert out["compatibility_clear_target"] is False
