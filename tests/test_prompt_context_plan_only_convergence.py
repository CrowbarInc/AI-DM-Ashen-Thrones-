"""Block C: prompt_context consumes bundled narrative plan only (no second planner)."""

from __future__ import annotations

import copy

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import (
    SESSION_NARRATION_PLAN_BUNDLE_KEY,
    SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY,
    public_narrative_plan_projection_for_prompt,
)
from game.planner_convergence import (
    MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN,
    NARRATIVE_PLAN_STAMP_MISMATCH,
)
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


def _minimal_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 3,
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
        "user_text": "Look around.",
        "resolution": {"kind": "observe"},
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


def _attach_observe_ctir(session: dict) -> None:
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="Look around.",
        builder_source="tests.test_prompt_context_plan_only_convergence",
        intent={"raw_text": "Look around.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "observe"},
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
        session[SESSION_CTIR_STAMP_KEY] = "plan_only_conv_stamp_v1"


def test_ctir_prompt_context_succeeds_when_build_narrative_plan_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bundle supplies the plan; prompt_context must not call build_narrative_plan."""

    def boom(*_a: object, **_k: object) -> dict:
        raise AssertionError("build_narrative_plan must not run in prompt_context path")

    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        monkeypatch.setattr("game.narrative_planning.build_narrative_plan", boom)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    assert isinstance(ctx.get("narrative_plan"), dict)
    assert ctx["narrative_plan"].get("narrative_mode") == "continuation"
    assert "debug" not in ctx["narrative_plan"]


def test_ctir_missing_bundle_seam_metadata_no_synthetic_plan() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan") is None
    audit = ctx.get("narration_seam_audit")
    assert isinstance(audit, dict)
    assert audit.get("semantic_bypass_blocked") is True
    pcc = (ctx.get("prompt_debug") or {}).get("planner_convergence_consumer") or {}
    assert pcc.get("ctir_present") is True
    assert pcc.get("bundle_present") is False
    assert pcc.get("stamp_matches") is False
    assert MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN in (pcc.get("seam_failure_codes") or [])


def test_ctir_stamp_mismatch_seam_metadata() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        session[SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY] = "wrong_stamp_for_tests"
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan") is None
    pcc = (ctx.get("prompt_debug") or {}).get("planner_convergence_consumer") or {}
    assert pcc.get("bundle_present") is True
    assert pcc.get("stamp_matches") is False
    assert NARRATIVE_PLAN_STAMP_MISMATCH in (pcc.get("seam_failure_codes") or [])


def test_prompt_narrative_plan_equals_bundle_projection() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY)
        assert isinstance(bundle, dict)
        full = bundle.get("narrative_plan")
        assert isinstance(full, dict)
        assert ctx["narrative_plan"] == public_narrative_plan_projection_for_prompt(full)
    finally:
        detach_ctir(session)


def test_raw_state_mutations_after_bundle_do_not_change_projected_plan() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = session[SESSION_NARRATION_PLAN_BUNDLE_KEY]
        assert isinstance(bundle, dict)
        full_before = copy.deepcopy(bundle.get("narrative_plan"))
        ctx_a = build_narration_context(**kw)
        # Mutate live engine/session presentation slices after bundle attachment.
        kw["world"]["extra_noise_marker"] = "post_bundle_mutation"
        kw["session"]["presentation_only_noise"] = True
        ctx_b = build_narration_context(**kw)
        assert ctx_a["narrative_plan"] == ctx_b["narrative_plan"]
        assert ctx_a["narrative_plan"] == public_narrative_plan_projection_for_prompt(full_before)
    finally:
        detach_ctir(session)


def test_legacy_no_ctir_path_unaffected() -> None:
    session = dict(_minimal_kwargs()["session"])
    detach_ctir(session)
    ctx = build_narration_context(**_minimal_kwargs(session=session, include_non_public_prompt_keys=True))
    assert ctx.get("narrative_plan") is None
    pcc = (ctx.get("prompt_debug") or {}).get("planner_convergence_consumer") or {}
    assert pcc.get("ctir_present") is False
    assert pcc.get("seam_failure_codes") == []
