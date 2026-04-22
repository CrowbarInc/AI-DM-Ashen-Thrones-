"""Regression: prompt_context CTIR seam — single session read, adapter mapping, bounded fallbacks."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
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
