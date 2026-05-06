"""Planner head-state module ownership (shape parity + import seams)."""

from __future__ import annotations

from pathlib import Path

import pytest

from game.narration_plan_bundle import build_narration_plan_bundle
from game.planner_head_state import EXPECTED_PLANNER_HEAD_STATE_KEYS, build_planner_head_state
from game.planner_seam_fencing import GUARD_LEGACY_NO_CTIR_ONLY, GUARD_NON_CTIR_SEMANTIC_PATH
from game.prompt_context import _build_narration_context_head_state

pytestmark = pytest.mark.unit


def _minimal_head_kwargs(**overrides: object) -> dict:
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


def test_build_planner_head_state_return_keys_match_contract() -> None:
    head = build_planner_head_state(**_minimal_head_kwargs())
    assert set(head.keys()) == EXPECTED_PLANNER_HEAD_STATE_KEYS


def test_prompt_context_shim_is_same_callable_as_build_planner_head_state() -> None:
    assert _build_narration_context_head_state is build_planner_head_state


def test_head_from_shim_equals_direct_call() -> None:
    kw = _minimal_head_kwargs()
    assert _build_narration_context_head_state(**kw) == build_planner_head_state(**kw)


def test_narration_plan_bundle_sources_head_from_planner_module_not_prompt_internals() -> None:
    bundle_path = Path(__file__).resolve().parents[1] / "game" / "narration_plan_bundle.py"
    text = bundle_path.read_text(encoding="utf-8")
    assert "from game.planner_head_state import build_planner_head_state" in text
    assert "prompt_context._build_narration_context_head_state" not in text
    assert "from game.prompt_context import _build_narration_context_head_state" not in text


def test_planner_seam_head_state_labels_no_ctir() -> None:
    rp = build_planner_head_state(**_minimal_head_kwargs())["response_policy"]
    pst = rp.get("planner_seam_trace") or {}
    hs = pst.get("head_state") or {}
    assert hs.get(GUARD_LEGACY_NO_CTIR_ONLY) is True
    assert hs.get(GUARD_NON_CTIR_SEMANTIC_PATH) is True
    assert hs.get("ctir_backed_head_state") is False


def test_bundle_no_ctir_still_labels_legacy_metadata() -> None:
    bundle = build_narration_plan_bundle(session={}, narration_context_kwargs={})
    pm = bundle["plan_metadata"]
    assert pm.get(GUARD_LEGACY_NO_CTIR_ONLY) is True
    assert pm.get(GUARD_NON_CTIR_SEMANTIC_PATH) is True
