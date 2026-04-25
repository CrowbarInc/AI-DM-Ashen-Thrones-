"""C1-A: Narrative Plan ``scene_opening`` projection and validation (prose-free, CTIR-shaped)."""

from __future__ import annotations

import copy

import pytest

from game.ctir import build_ctir
from game.defaults import default_session, default_world
from game.narrative_plan_upstream import SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY
from game.narrative_planning import (
    build_narrative_plan,
    infer_scene_opening_reason,
    validate_narrative_plan,
    validate_scene_opening,
)

pytestmark = pytest.mark.unit

_DIALOGUE_CONTRACT_INPUTS = {
    "narration_obligations": {"active_npc_reply_expected": True, "active_npc_reply_kind": "answer"},
}


def _minimal_ctir(**kwargs: object) -> dict:
    base = dict(
        turn_id=2,
        scene_id="s_open",
        player_input="look",
        builder_source="tests.scene_opening_narrative_plan",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    base.update(kwargs)
    return build_ctir(**base)


def test_valid_campaign_start_scene_opening() -> None:
    c = _minimal_ctir(
        resolution={
            "kind": "observe",
            "action_id": "campaign_start_opening_scene",
            "state_changes": {"opening_scene_turn": True},
        },
    )
    plan = build_narrative_plan(
        ctir=c,
        narration_obligations={"is_opening_scene": True},
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Courtyard", "Gate"]},
        opening_visible_fact_strings=["Ash drifts across the yard.", "Spear-butts ring on stone."],
    )
    so = plan.get("scene_opening")
    assert isinstance(so, dict)
    assert so.get("opening_required") is True
    assert so.get("opening_reason") == "campaign_start"
    assert so.get("scene_id") == "s_open"
    assert so.get("location_anchors")
    assert "A" in (so.get("visible_fact_categories") or [])
    assert so.get("validator", {}).get("ok") is True
    assert validate_narrative_plan(plan, strict=True) is None


def test_valid_post_transition_scene_opening() -> None:
    c = _minimal_ctir(
        resolution={
            "kind": "observe",
            "state_changes": {"scene_transition_occurred": True},
        },
    )
    plan = build_narrative_plan(
        ctir=c,
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Road"]},
        **_DIALOGUE_CONTRACT_INPUTS,
    )
    so = plan.get("scene_opening")
    assert isinstance(so, dict)
    assert so.get("opening_reason") == "post_transition"
    assert validate_narrative_plan(plan, strict=True) is None


def test_invalid_prose_key_in_scene_opening_rejected() -> None:
    c = _minimal_ctir(
        resolution={"kind": "observe", "state_changes": {"opening_scene_turn": True}},
    )
    plan = build_narrative_plan(
        ctir=c,
        narration_obligations={"is_opening_scene": True},
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Yard"]},
    )
    bad = copy.deepcopy(plan)
    so = dict(bad["scene_opening"])
    so["narration"] = "illegal prose bucket"
    bad["scene_opening"] = so
    assert validate_narrative_plan(bad, strict=True) is not None


def test_invalid_scene_opening_missing_scene_id_when_required() -> None:
    c = _minimal_ctir(
        resolution={"kind": "observe", "state_changes": {"opening_scene_turn": True}},
    )
    plan = build_narrative_plan(
        ctir=c,
        narration_obligations={"is_opening_scene": True},
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Yard"]},
    )
    bad = copy.deepcopy(plan)
    so = dict(bad["scene_opening"])
    so["scene_id"] = None
    bad["scene_opening"] = so
    err = validate_narrative_plan(bad, strict=True)
    assert err is not None


def test_no_opening_turn_scene_opening_null() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert plan.get("scene_opening") is None
    assert validate_narrative_plan(plan, strict=True) is None


def test_resume_entry_scene_opening_via_session_interaction() -> None:
    c = _minimal_ctir(resolution={"kind": "observe"})
    plan = build_narrative_plan(
        ctir=c,
        session_interaction={"resume_entry": True},
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Road"]},
        **_DIALOGUE_CONTRACT_INPUTS,
    )
    so = plan.get("scene_opening")
    assert isinstance(so, dict)
    assert so.get("opening_reason") == "resume_entry"
    assert validate_narrative_plan(plan, strict=True) is None


def test_scene_entry_opening_reason() -> None:
    c = _minimal_ctir(resolution={"kind": "observe"})
    plan = build_narrative_plan(
        ctir=c,
        narration_obligations={
            "is_opening_scene": True,
            "active_npc_reply_expected": True,
            "active_npc_reply_kind": "answer",
        },
        public_scene_slice={"scene_id": "s_open", "location_tokens": ["Yard"]},
    )
    so = plan.get("scene_opening")
    assert isinstance(so, dict)
    assert so.get("opening_reason") == "scene_entry"
    assert infer_scene_opening_reason(
        c,
        narration_obligations={"is_opening_scene": True},
        session_interaction=None,
    ) == "scene_entry"


def test_compress_session_surfaces_resume_entry_for_planning_slice() -> None:
    from game.prompt_context import _compress_session

    s = default_session()
    s[SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY] = True
    sv = _compress_session(s, default_world(), {"id": "s_x", "visible_facts": []})
    assert sv.get("resume_entry") is True


def test_infer_scene_opening_reason_matches_resume_pending_contract() -> None:
    c = _minimal_ctir(resolution={"kind": "observe"})
    assert (
        infer_scene_opening_reason(
            c,
            narration_obligations={},
            session_interaction={"resume_entry": True},
        )
        == "resume_entry"
    )


def test_validate_scene_opening_api_no_opening() -> None:
    c = _minimal_ctir(resolution={"kind": "observe"})
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert (
        validate_scene_opening(
            None,
            ctir=c,
            public_scene_slice=None,
            plan_active_pressures=plan["active_pressures"],
            scene_anchors=plan["scene_anchors"],
            opening_required=False,
        )
        is None
    )
