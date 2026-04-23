"""Objective N3: narrative_roles integration in prompt_context (guidance, debug, safe degradation)."""

from __future__ import annotations

import json

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import attach_narration_plan_bundle, get_attached_narration_plan_bundle
from game.narrative_planning import NARRATIVE_ROLE_FAMILY_KEYS
from game import prompt_context as pc
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from tests.helpers.n3_prompt_debug import assert_narrative_roles_skim_when_trusted


def _minimal_narration_kwargs(**overrides: object) -> dict:
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
        "user_text": "What do you hear?",
        "resolution": {"kind": "travel", "label": "move", "action_id": "raw-walk"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    base.update(overrides)
    return base


def _attach_question_ctir(session: dict) -> None:
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="What do you hear?",
        builder_source="tests.test_prompt_context_narrative_roles",
        intent={"raw_text": "What do you hear?", "labels": ["general"], "mode": "social"},
        resolution={
            "kind": "question",
            "label": "ask",
            "action_id": "ctir-q",
            "authoritative_outputs": {},
            "metadata": {},
        },
        interaction={"active_target_id": "npc_x", "interaction_mode": "social", "interaction_kind": "question"},
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
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"


def test_struct_guidance_mentions_all_five_role_families() -> None:
    blob = "\n".join(pc._NARRATIVE_PLAN_STRUCT_GUIDANCE)
    for key in NARRATIVE_ROLE_FAMILY_KEYS:
        assert key in blob, f"missing role key {key!r}"


def test_struct_guidance_precedence_language() -> None:
    blob = "\n".join(pc._NARRATIVE_PLAN_STRUCT_GUIDANCE)
    assert "narration_visibility" in blob
    assert "N3 precedence" in blob or "narrative_authority" in blob
    assert "answer_completeness" in blob
    assert "CTIR" in blob


def test_struct_guidance_avoids_rigid_template_phrasing() -> None:
    """N3 guidance stays abstract: no ordering mandates or 'exactly one of each' style rules."""
    blob = "\n".join(pc._NARRATIVE_PLAN_STRUCT_GUIDANCE) + "\n".join(pc._narrative_plan_roles_trusted_lane())
    lowered = blob.lower()
    assert "must emit" not in lowered
    assert "exactly one of each" not in lowered
    assert "sentence 1" not in lowered
    assert "sentence 2" not in lowered
    assert "paragraph 1" not in lowered
    assert "first sentence" not in lowered  # N3 block must not impose sentence-slot rules


def test_prompt_debug_roles_skim_when_plan_valid() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    pd = ctx.get("prompt_debug") or {}
    npd = pd.get("narrative_plan") or {}
    skim = npd.get("narrative_roles_skim") or {}
    assert_narrative_roles_skim_when_trusted(skim)
    assert npd.get("narrative_plan_validation_error") is None
    skim_json = json.dumps(skim, sort_keys=True)
    assert len(skim_json) < 1400, "operator skim should stay compact"


def test_trusted_lane_appended_only_when_plan_validates() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    instr = "\n".join(ctx.get("instructions") or [])
    assert "NARRATIVE ROLES (N3 supplemental)" in instr


def test_partial_plan_without_roles_degrades_without_exception() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = get_attached_narration_plan_bundle(session)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        tampered = dict(plan)
        tampered.pop("narrative_roles", None)
        bundle2 = dict(bundle)
        bundle2["narrative_plan"] = tampered
        attach_narration_plan_bundle(session, bundle2)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    pd = ctx.get("prompt_debug") or {}
    npd = pd.get("narrative_plan") or {}
    assert npd.get("present") is True
    skim = npd.get("narrative_roles_skim") or {}
    assert skim.get("present") is False
    assert npd.get("narrative_plan_validation_error")
    instr = "\n".join(ctx.get("instructions") or [])
    assert "NARRATIVE ROLES (N3 supplemental)" not in instr


@pytest.mark.parametrize(
    "plan_obj,expect_trust",
    [
        ({}, False),
        ({"version": 1}, False),
    ],
)
def test_roles_trustworthy_false_on_garbage(plan_obj: dict, expect_trust: bool) -> None:
    assert pc._narrative_plan_roles_trustworthy(plan_obj) is expect_trust


def test_rule_priority_precedes_narrative_plan_guidance_in_instructions() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    instr = ctx.get("instructions") or []
    idx_rule = next((i for i, line in enumerate(instr) if "When rules conflict" in line), None)
    idx_np = next((i for i, line in enumerate(instr) if "NARRATIVE PLAN (STRUCTURAL GUIDANCE)" in line), None)
    assert idx_rule is not None and idx_np is not None
    assert idx_rule < idx_np


def test_tampered_plan_version_drops_trusted_lane_and_upstream_instruction() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = get_attached_narration_plan_bundle(session)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        tampered = dict(plan)
        tampered["version"] = 999
        bundle2 = dict(bundle)
        bundle2["narrative_plan"] = tampered
        attach_narration_plan_bundle(session, bundle2)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    instr = "\n".join(ctx.get("instructions") or [])
    assert "NARRATIVE ROLES (N3 supplemental)" not in instr
    assert "N3 bundle upstream" not in instr
    npd = (ctx.get("prompt_debug") or {}).get("narrative_plan") or {}
    assert npd.get("narrative_plan_validation_error")
