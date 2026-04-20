"""CTIR-first prompt-context consumption (session-backed CTIR, no in-module CTIR construction)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from game import ctir
from game.ctir_runtime import attach_ctir, detach_ctir
from game.prompt_context import _ctir_to_prompt_semantics, build_narration_context


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
        builder_source="tests.test_prompt_context_ctir_consumption",
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


def test_ctir_first_turn_summary_ignores_raw_resolution_kind() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    try:
        ctx = build_narration_context(**_minimal_narration_kwargs(session=session))
    finally:
        detach_ctir(session)
    assert ctx["turn_summary"]["resolution_kind"] == "question"
    assert ctx["turn_summary"]["action_id"] == "ctir-q"


def test_no_ctir_session_still_builds() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    detach_ctir(session)
    ctx = build_narration_context(
        **_minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    )
    assert ctx["turn_summary"]["resolution_kind"] == "travel"
    assert ctx.get("narrative_plan") is None
    pd = ctx.get("prompt_debug") or {}
    assert isinstance(pd, dict)
    npd = pd.get("narrative_plan") or {}
    assert npd.get("present") is False


def test_ctir_session_attaches_narrative_plan_and_stable_on_repeat() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True)
    try:
        ctx_a = build_narration_context(**kw)
        ctx_b = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    plan = ctx_a.get("narrative_plan")
    assert isinstance(plan, dict)
    assert plan.get("version") == 1
    assert plan.get("narrative_mode") in {
        "opening",
        "continuation",
        "action_outcome",
        "dialogue",
        "transition",
        "exposition_answer",
    }
    assert plan.get("narrative_mode") == "dialogue"
    assert plan.get("narrative_mode") == plan.get("narrative_mode_contract", {}).get("mode")
    assert ctx_a.get("narrative_plan") == ctx_b.get("narrative_plan")
    pd = ctx_a.get("prompt_debug") or {}
    npd = pd.get("narrative_plan") or {}
    assert npd.get("present") is True
    assert npd.get("narrative_mode") == plan.get("narrative_mode")
    assert isinstance(npd.get("derivation_codes"), list)
    nmi = pd.get("narrative_mode_instructions") or {}
    assert nmi.get("mode") == plan.get("narrative_mode")
    assert nmi.get("instruction_count", 0) > 0


def test_response_policy_carries_response_type_contract_when_ctir_present() -> None:
    """Narrative mode derivation must see the same RTC slice shipped on response_policy (Objective #6 seam)."""
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    try:
        ctx = build_narration_context(**_minimal_narration_kwargs(session=session, include_non_public_prompt_keys=True))
    finally:
        detach_ctir(session)
    rp = ctx.get("response_policy") or {}
    rtc = rp.get("response_type_contract")
    assert isinstance(rtc, dict)
    assert rtc.get("required_response_type") == "dialogue"


def test_public_scene_convenience_slice_does_not_drift_narrative_mode() -> None:
    """Bounded public_scene fields may relabel anchors; coarse ``narrative_mode`` stays CTIR-derived."""
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    base_ps = {"id": "s1", "name": "First Title", "location_tokens": ["dock"]}
    alt_ps = {"id": "s1", "name": "Different Title", "location_tokens": ["market", "square"]}
    try:
        ctx_a = build_narration_context(**_minimal_narration_kwargs(session=session, public_scene=base_ps))
        ctx_b = build_narration_context(**_minimal_narration_kwargs(session=session, public_scene=alt_ps))
    finally:
        detach_ctir(session)
    pa = ctx_a.get("narrative_plan")
    pb = ctx_b.get("narrative_plan")
    assert isinstance(pa, dict) and isinstance(pb, dict)
    assert pa.get("narrative_mode") == pb.get("narrative_mode") == "dialogue"
    assert (pa.get("scene_anchors") or {}).get("scene_name") == "First Title"
    assert (pb.get("scene_anchors") or {}).get("scene_name") == "Different Title"


def test_legacy_resolution_kwargs_do_not_override_ctir_or_plan_semantics() -> None:
    """Caller ``resolution`` may differ for legacy paths; CTIR-backed summary and plan follow CTIR."""
    session = dict(_minimal_narration_kwargs()["session"])
    _attach_question_ctir(session)
    kw = _minimal_narration_kwargs(session=session, resolution={"kind": "travel", "action_id": "legacy"})
    try:
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    assert ctx["turn_summary"]["resolution_kind"] == "question"
    plan = ctx.get("narrative_plan")
    assert isinstance(plan, dict)
    assert plan.get("narrative_mode") == "dialogue"


def test_prompt_context_module_has_no_build_ctir() -> None:
    root = Path(__file__).resolve().parents[1] / "game" / "prompt_context.py"
    src = root.read_text(encoding="utf-8")
    assert "build_ctir" not in src
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in ("game.ctir", "ctir"):
            for alias in node.names:
                assert alias.name != "build_ctir"


def test_empty_narrative_anchors_does_not_break_assembly() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="look",
        builder_source="tests.empty_anchors",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    try:
        ctx = build_narration_context(**_minimal_narration_kwargs(session=session, resolution=None))
    finally:
        detach_ctir(session)
    assert isinstance(ctx.get("turn_summary"), dict)


def test_ctir_to_prompt_semantics_is_deterministic() -> None:
    c = ctir.build_ctir(
        turn_id=9,
        scene_id="z",
        player_input="ping",
        builder_source="tests.det",
        resolution={"kind": "observe"},
        intent={"mode": "activity"},
        interaction={"interaction_mode": "activity"},
        world={"events": [{"id": "e1"}]},
        narrative_anchors={
            "scene_framing": [{"id": "a1"}],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    a = _ctir_to_prompt_semantics(c)
    b = _ctir_to_prompt_semantics(c)
    assert a == b


@pytest.mark.parametrize(
    "anchors",
    [
        None,
        {
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    ],
)
def test_semantics_does_not_require_prose_in_ctir(anchors: dict | None) -> None:
    kwargs = dict(
        turn_id=0,
        scene_id=None,
        player_input="x",
        builder_source="tests.prose_absent",
        narrative_anchors=anchors,
    )
    c = ctir.build_ctir(**kwargs)
    sem = _ctir_to_prompt_semantics(c)
    na = sem["narrative_anchors"]
    assert isinstance(na, dict)
    for bucket in ("scene_framing", "actors_speakers", "outcomes", "uncertainty", "next_leads_affordances"):
        assert bucket in na
