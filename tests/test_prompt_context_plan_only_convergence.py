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


def _attach_question_ctir(session: dict) -> None:
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="Where did they go?",
        builder_source="tests.test_prompt_context_plan_only_convergence",
        intent={"raw_text": "Where did they go?", "labels": ["general"], "mode": "question"},
        resolution={"kind": "adjudication_query", "prompt": "Where did they go?"},
        interaction={"interaction_mode": "social_exchange"},
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


def test_prompt_context_ships_answer_exposition_plan_and_mirrors_into_answer_completeness() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
        np = ctx.get("narrative_plan")
        assert isinstance(np, dict)
        aep = np.get("answer_exposition_plan")
        assert isinstance(aep, dict)
        # prompt_context must not add facts beyond the plan; it only mirrors/ships.
        ac = (ctx.get("response_policy") or {}).get("answer_completeness") or {}
        assert isinstance(ac, dict)
        assert ac.get("answer_exposition_plan") == aep
        assert (ac.get("answer_exposition_plan") or {}).get("facts") == aep.get("facts")
    finally:
        detach_ctir(session)


def test_answer_required_missing_projected_answer_exposition_plan_is_traceable() -> None:
    session = dict(_minimal_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_kwargs(
        session=session,
        user_text="Where did they go?",
        resolution={"kind": "adjudication_query", "prompt": "Where did they go?"},
        include_non_public_prompt_keys=True,
    )
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = session.get(SESSION_NARRATION_PLAN_BUNDLE_KEY) or {}
        assert isinstance(bundle, dict)
        full = bundle.get("narrative_plan")
        assert isinstance(full, dict)
        # Break the projected surface: remove the plan-owned answer_exposition_plan.
        full.pop("answer_exposition_plan", None)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    ac = (ctx.get("response_policy") or {}).get("answer_completeness") or {}
    assert isinstance(ac, dict)
    assert ac.get("answer_required") is True
    assert ac.get("answer_exposition_plan") is None
    dbg = (ctx.get("prompt_debug") or {}).get("answer_exposition_plan_seam") or {}
    assert isinstance(dbg, dict)
    assert dbg.get("seam_open") is True


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


def _pressing_recent_log() -> list[dict]:
    return [
        {
            "log_meta": {"player_input": "Look around."},
            "gm_output": {
                "player_facing_text": "You get a quick survey of the area, but nothing definitive stands out at a glance."
            },
        }
    ]


def test_verified_ctir_continuation_does_not_use_recent_log_pressure() -> None:
    """Verified continuation must not derive progression/pressure from recent_log."""
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(
        session=session,
        user_text="Look around again.",
        recent_log_for_prompt=_pressing_recent_log(),
        include_non_public_prompt_keys=True,
    )
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert ctx.get("narrative_plan") is not None
    assert ctx.get("follow_up_pressure") is None
    ins = "\n".join(ctx.get("instructions") or [])
    assert "FOLLOW-UP ESCALATION RULE" not in ins
    cdbg = (ctx.get("prompt_debug") or {}).get("continuation_packaging") or {}
    assert cdbg.get("continuation_progression_source") == "narrative_plan_bundle"
    assert cdbg.get("prompt_context_reconstructed_continuation") is False
    assert cdbg.get("continuation_plan_projection_used") is True


def test_ctir_missing_plan_does_not_trigger_recent_log_continuity_reconstruction() -> None:
    """When CTIR is present but plan is missing, prompt_context must not 'patch' continuity from logs."""
    session = dict(_minimal_kwargs()["session"])
    _attach_observe_ctir(session)
    kw = _minimal_kwargs(
        session=session,
        user_text="Look around again.",
        recent_log_for_prompt=_pressing_recent_log(),
        include_non_public_prompt_keys=True,
    )
    try:
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    assert ctx.get("narrative_plan") is None
    assert ctx.get("follow_up_pressure") is None
    ins = "\n".join(ctx.get("instructions") or [])
    assert "FOLLOW-UP ESCALATION RULE" not in ins


def test_legacy_no_ctir_path_still_uses_recent_log_follow_up_pressure() -> None:
    """Non-CTIR paths may still use legacy recent_log-derived follow-up pressure."""
    session = dict(_minimal_kwargs()["session"])
    detach_ctir(session)
    kw = _minimal_kwargs(
        session=session,
        user_text="Look around again.",
        recent_log_for_prompt=_pressing_recent_log(),
        include_non_public_prompt_keys=True,
    )
    ctx = build_narration_context(**kw)
    fup = ctx.get("follow_up_pressure") or {}
    assert fup.get("pressed") is True
