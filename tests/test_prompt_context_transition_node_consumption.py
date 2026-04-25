"""Block B — prompt_context consumes narrative_plan.transition_node only (no inference)."""

from __future__ import annotations

import copy

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import SESSION_NARRATION_PLAN_BUNDLE_KEY
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


def _minimal_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 3,
            "visited_scene_ids": ["s0", "s1"],
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
        "user_text": "Go.",
        "resolution": {"kind": "scene_transition", "label": "move", "action_id": "raw-walk"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["travel"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
        "include_non_public_prompt_keys": True,
    }
    base.update(overrides)
    return base


def _attach_transition_ctir(session: dict, *, resolved: bool = True) -> None:
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="Go.",
        builder_source="tests.test_prompt_context_transition_node_consumption",
        intent={"raw_text": "Go.", "labels": ["travel"], "mode": "activity"},
        resolution={
            "kind": "scene_transition",
            "label": "Go",
            "action_id": "ctir-go",
            "authoritative_outputs": {
                "resolved_transition": bool(resolved),
                "target_scene_id": "s2",
            },
            "metadata": {},
        },
        interaction={"interaction_mode": "activity"},
        world={},
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
        session[SESSION_CTIR_STAMP_KEY] = "transition_node_bundle_stamp_v1"


def test_valid_transition_node_exposed_in_prompt_context() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_transition_ctir(session)
    kw = _minimal_kwargs(session=session)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        # Ensure the projected plan contains transition_node (Block A owner), but keep test robust
        # by injecting a known-good node when absent.
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        # Force a known-good node (do not rely on whatever the planner emitted).
        plan["transition_node"] = {
            "transition_required": True,
            "transition_type": "scene_cut",
            "before_anchor": {"scene_id": "s1"},
            "after_anchor": {"scene_id": "s2"},
            "continuity_anchor_ids": ["a1"],
            "derivation_codes": ["ctir:scene_transition"],
            "source_fields": ["ctir.resolution.authoritative_outputs.target_scene_id"],
        }
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert isinstance(ctx.get("transition"), dict)
    assert ctx["transition"]["transition_required"] is True
    if isinstance(ctx.get("narrative_plan"), dict):
        assert isinstance(ctx["narrative_plan"].get("transition_node"), dict)


def test_prompt_context_does_not_infer_transition_when_plan_node_missing() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_transition_ctir(session)
    kw = _minimal_kwargs(session=session)
    try:
        # Do NOT attach narration bundle → narrative_plan is absent.
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert ctx.get("transition") is None
    obligations = ctx.get("narration_obligations") or {}
    assert obligations.get("must_advance_scene") is False
    seam = ctx.get("narration_seam_audit") or {}
    tna = seam.get("transition_node_consumer") or {}
    assert tna.get("transition_signal_present") is True
    assert tna.get("transition_node_present") is False
    assert tna.get("blocked_inference_path") is True
    # No fallback prose / guidance
    instructions = " ".join(ctx.get("instructions", [])).lower()
    assert "elsewhere" not in instructions
    assert "time passes" not in instructions
    assert "you arrive" not in instructions
    assert "brief bridge from the prior location" not in instructions


def test_missing_plan_node_produces_seam_metadata_not_payload() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_transition_ctir(session)
    kw = _minimal_kwargs(session=session)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        plan.pop("transition_node", None)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert ctx.get("transition") is None
    seam = ctx.get("narration_seam_audit") or {}
    tna = seam.get("transition_node_consumer") or {}
    assert tna.get("transition_signal_present") is True
    assert tna.get("transition_node_present") is False


def test_required_transition_with_incomplete_anchors_is_seam_issue() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_transition_ctir(session)
    kw = _minimal_kwargs(session=session)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        plan["transition_node"] = {
            "transition_required": True,
            "transition_type": "scene_cut",
            "before_anchor": {},
            "after_anchor": {"scene_id": "s2"},
            "continuity_anchor_ids": [],
            "derivation_codes": ["ctir:scene_transition"],
            "source_fields": ["ctir.resolution.authoritative_outputs.target_scene_id"],
        }
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    seam = ctx.get("narration_seam_audit") or {}
    tna = seam.get("transition_node_consumer") or {}
    assert tna.get("transition_required") is True
    assert tna.get("incomplete_required_anchors") is True


def test_no_transition_node_remains_stable() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_transition_ctir(session, resolved=False)
    kw = _minimal_kwargs(
        session=session,
        resolution={"kind": "observe", "action_id": "observe", "label": "Observe"},
        intent={"labels": ["observation"]},
    )
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        plan["transition_node"] = {
            "transition_required": False,
            "transition_type": "none",
            "before_anchor": {},
            "after_anchor": {},
            "continuity_anchor_ids": [],
            "derivation_codes": ["ctir:none"],
            "source_fields": [],
        }
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert isinstance(ctx.get("transition"), dict)
    assert ctx["transition"]["transition_required"] is False
    obligations = ctx.get("narration_obligations") or {}
    assert obligations.get("must_advance_scene") is False

