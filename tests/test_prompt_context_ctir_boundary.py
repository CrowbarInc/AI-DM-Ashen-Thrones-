"""Regression: prompt_context CTIR seam — single session read, adapter mapping, bounded fallbacks."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import SESSION_NARRATION_PLAN_BUNDLE_KEY
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


def _base_kwargs() -> dict:
    return {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 2,
            "visited_scene_ids": ["s1"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Look.",
        "resolution": {"kind": "travel", "label": "raw-travel"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"], "allow_discoverable_clues": True},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }


def test_get_attached_ctir_called_once_per_build_narration_context() -> None:
    """``get_attached_ctir`` is read during bundle planning and again during ``build_narration_context``."""
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Look.",
        builder_source="tests.boundary.once",
        intent={"raw_text": "Look.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "observe", "label": "look"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    calls = 0

    def counting_get(sess: object) -> dict | None:
        nonlocal calls
        calls += 1
        from game.ctir_runtime import get_attached_ctir as real

        return real(sess)

    try:
        with patch("game.prompt_context.get_attached_ctir", side_effect=counting_get):
            _bk = {**_base_kwargs(), "session": session}
            ensure_narration_plan_bundle_for_manual_ctir_tests(session, _bk)
            build_narration_context(**_bk)
    finally:
        detach_ctir(session)
    # Bundle seam calls ``get_attached_ctir`` during upstream plan construction, then again in ``build_narration_context``.
    assert calls == 2


def test_classifier_only_intent_merged_when_ctir_present() -> None:
    """Bounded canonical/classifier field not duplicated into CTIR — merged at prompt boundary."""
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Look.",
        builder_source="tests.boundary.classifier",
        intent={"raw_text": "Look.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "observe"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        _bk = {**_base_kwargs(), "session": session}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _bk)
        ctx = build_narration_context(**_bk)
    finally:
        detach_ctir(session)
    scene_block = ctx.get("scene")
    assert isinstance(scene_block, dict)
    intent_block = scene_block.get("intent")
    assert isinstance(intent_block, dict)
    assert intent_block.get("allow_discoverable_clues") is True


def test_no_build_ctir_symbol_in_prompt_context_source() -> None:
    path = Path(__file__).resolve().parents[1] / "game" / "prompt_context.py"
    src = path.read_text(encoding="utf-8")
    assert "build_ctir" not in src
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in ("game.ctir", "ctir"):
            for alias in node.names:
                assert alias.name != "build_ctir"


def test_raw_resolution_fallback_when_no_ctir() -> None:
    session = dict(_base_kwargs()["session"])
    detach_ctir(session)
    ctx = build_narration_context(**{**_base_kwargs(), "session": session})
    assert ctx["turn_summary"]["resolution_kind"] == "travel"


def test_action_outcome_mode_ships_structured_mechanics_not_raw_hint_text() -> None:
    """Regression guard: action_outcome mode must not ship raw resolution.hint/prompt as mechanics."""
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Attack.",
        builder_source="tests.boundary.action_outcome",
        intent={"raw_text": "Attack.", "labels": ["attack"], "mode": "activity"},
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "label": "Attack",
            "prompt": "Player hit the orc... Narrate the outcome.",  # legacy hint-like seam
            "combat": {
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "damage_dealt": 3,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 11, "attack_total": 15, "target_ac": 13},
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Attack."
        kw["scene_runtime"] = {}
        kw["resolution"] = {"kind": "attack", "hint": "Narrate the outcome.", "prompt": "Narrate the outcome."}
        kw["mode_instruction"] = "Standard."
        kw["public_scene"] = {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        ctx = build_narration_context(**{**kw, "include_non_public_prompt_keys": True})
    finally:
        detach_ctir(session)
    mech = ctx.get("mechanical_resolution")
    assert isinstance(mech, dict)
    assert "action_outcome" in mech
    # Ensure we didn't ship the raw resolution dict under action_outcome mode.
    assert "hint" not in mech
    ts = ctx.get("turn_summary")
    assert isinstance(ts, dict)
    assert ts.get("resolved_prompt") is None
    assert "Narrate" not in str(ts.get("action_descriptor") or "")


def test_action_outcome_skill_mode_no_raw_hint_in_mechanical_or_turn_summary() -> None:
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Search.",
        builder_source="tests.boundary.action_outcome_skill",
        intent={"raw_text": "Search.", "labels": ["investigate"], "mode": "activity"},
        resolution={
            "kind": "investigate",
            "action_id": "desk",
            "success_state": "success",
            "skill_check": {
                "skill": "perception",
                "dc": 10,
                "difficulty": 10,
                "modifier": 0,
                "roll": 15,
                "total": 15,
                "success": True,
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Search."
        kw["scene_runtime"] = {}
        kw["resolution"] = {
            "kind": "investigate",
            "hint": "Describe what they find.",
            "prompt": "Describe what they find.",
        }
        kw["mode_instruction"] = "Standard."
        kw["public_scene"] = {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        ctx = build_narration_context(**{**kw, "include_non_public_prompt_keys": True})
    finally:
        detach_ctir(session)
    mech = ctx.get("mechanical_resolution")
    assert isinstance(mech, dict)
    ao = mech.get("action_outcome")
    assert isinstance(ao, dict)
    assert ao.get("source_kind") == "skill_check"
    assert "hint" not in mech
    assert "prompt" not in mech
    ts = ctx.get("turn_summary")
    assert isinstance(ts, dict)
    assert ts.get("resolved_prompt") is None
    assert "Describe" not in str(ts.get("action_descriptor") or "")


def test_action_outcome_ctir_missing_plan_action_outcome_fails_closed() -> None:
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Attack.",
        builder_source="tests.boundary.ao_missing",
        intent={"raw_text": "Attack.", "labels": ["attack"], "mode": "activity"},
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "combat": {
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "damage_dealt": 3,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 11, "attack_total": 15, "target_ac": 13},
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Attack."
        kw["resolution"] = {"kind": "attack", "prompt": "Narrate the bloody hit in slow motion."}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        bundle = deepcopy(session[SESSION_NARRATION_PLAN_BUNDLE_KEY])
        plan = dict(bundle["narrative_plan"])
        plan.pop("action_outcome", None)
        bundle["narrative_plan"] = plan
        session[SESSION_NARRATION_PLAN_BUNDLE_KEY] = bundle
        ctx = build_narration_context(**{**kw, "include_non_public_prompt_keys": True})
    finally:
        detach_ctir(session)
    assert ctx.get("turn_summary", {}).get("action_outcome_contract_blocked") is True
    assert ctx.get("mechanical_resolution") is None
    assert ctx.get("narrative_plan") is None
    audit = ctx.get("narration_seam_audit")
    assert isinstance(audit, dict)
    assert audit.get("action_outcome_contract_blocked") is True
    assert audit.get("semantic_bypass_blocked") is True
    dbg = (ctx.get("prompt_debug") or {}).get("action_outcome_contract")
    assert isinstance(dbg, dict)
    assert dbg.get("action_outcome_plan_valid") is False
    assert dbg.get("action_outcome_plan_failure_reasons")


def test_action_outcome_ctir_prose_hint_on_action_outcome_object_fails_closed() -> None:
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Attack.",
        builder_source="tests.boundary.ao_prose",
        intent={"raw_text": "Attack.", "labels": ["attack"], "mode": "activity"},
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "combat": {
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "damage_dealt": 3,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 11, "attack_total": 15, "target_ac": 13},
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Attack."
        kw["resolution"] = {"kind": "attack"}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        bundle = deepcopy(session[SESSION_NARRATION_PLAN_BUNDLE_KEY])
        plan = dict(bundle["narrative_plan"])
        ao = dict(plan["action_outcome"])
        ao["hint"] = "forbidden prose leak"
        plan["action_outcome"] = ao
        bundle["narrative_plan"] = plan
        session[SESSION_NARRATION_PLAN_BUNDLE_KEY] = bundle
        ctx = build_narration_context(**{**kw, "include_non_public_prompt_keys": True})
    finally:
        detach_ctir(session)
    assert ctx.get("turn_summary", {}).get("action_outcome_contract_blocked") is True
    assert ctx.get("mechanical_resolution") is None
    reasons = (ctx.get("prompt_debug") or {}).get("action_outcome_contract", {}).get("action_outcome_plan_failure_reasons") or []
    assert any("bad_keys" in str(x) or "narrative_plan_invalid" in str(x) for x in reasons)


def test_action_outcome_ctir_present_false_fails_closed() -> None:
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Attack.",
        builder_source="tests.boundary.ao_present_false",
        intent={"raw_text": "Attack.", "labels": ["attack"], "mode": "activity"},
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "combat": {
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "damage_dealt": 3,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 11, "attack_total": 15, "target_ac": 13},
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Attack."
        kw["resolution"] = {"kind": "attack", "prompt": "Roll narration should not anchor here."}
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        bundle = deepcopy(session[SESSION_NARRATION_PLAN_BUNDLE_KEY])
        plan = dict(bundle["narrative_plan"])
        ao = dict(plan["action_outcome"])
        ao["present"] = False
        plan["action_outcome"] = ao
        bundle["narrative_plan"] = plan
        session[SESSION_NARRATION_PLAN_BUNDLE_KEY] = bundle
        ctx = build_narration_context(**{**kw, "include_non_public_prompt_keys": True})
    finally:
        detach_ctir(session)
    assert ctx.get("mechanical_resolution") is None
    assert "slow motion" not in str(ctx.get("turn_summary") or {})
    assert "Roll narration" not in str(ctx.get("turn_summary") or {})
