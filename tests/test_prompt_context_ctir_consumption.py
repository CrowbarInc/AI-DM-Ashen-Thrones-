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
    ctx = build_narration_context(**_minimal_narration_kwargs(session=session))
    assert ctx["turn_summary"]["resolution_kind"] == "travel"


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
