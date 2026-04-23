"""Contract tests for :mod:`game.planner_convergence` (Block A). No GPT."""

from __future__ import annotations

import json

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir
from game.narration_plan_bundle import (
    SESSION_NARRATION_PLAN_BUNDLE_KEY,
    SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY,
)
from game.planner_convergence import (
    MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN,
    NARRATIVE_PLAN_STAMP_MISMATCH,
    PROMPT_PAYLOAD_MISSING_NARRATIVE_PLAN,
    PROMPT_PAYLOAD_USES_RAW_SEMANTIC_SHORTCUT,
    UNREGISTERED_NARRATION_PATH,
    build_planner_convergence_report,
    planner_convergence_ok,
)


def _anchors() -> dict:
    return {
        "scene_framing": [],
        "actors_speakers": [],
        "outcomes": [],
        "uncertainty": [],
        "next_leads_affordances": [],
    }


def _attach_ctir(session: dict, *, stamp: str) -> None:
    attach_ctir(
        session,
        ctir.build_ctir(
            turn_id=1,
            scene_id="s1",
            player_input="look",
            builder_source="tests.test_planner_convergence_contract",
            intent={"raw_text": "look", "labels": ["general"], "mode": "social"},
            resolution={"kind": "observe"},
            interaction={"interaction_mode": "none"},
            world={},
            narrative_anchors=_anchors(),
        ),
    )
    session[SESSION_CTIR_STAMP_KEY] = stamp


def _attach_bundle(session: dict, *, stamp: str, plan: dict | None) -> None:
    session[SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY] = stamp
    session[SESSION_NARRATION_PLAN_BUNDLE_KEY] = {
        "plan_metadata": {"ctir_stamp": stamp},
        "narrative_plan": plan,
        "renderer_inputs": {},
    }


def test_report_passes_with_ctir_plan_matching_stamp_and_prompt() -> None:
    stamp = "turn:1a:9f"
    session: dict = {}
    _attach_ctir(session, stamp=stamp)
    _attach_bundle(session, stamp=stamp, plan={"narrative_mode": "observe"})
    prompt = {"narrative_plan": {"narrative_mode": "observe"}}
    r = build_planner_convergence_report(
        path_label="continuation",
        owner_module="tests",
        session=session,
        prompt_payload=prompt,
    )
    assert json.dumps(r)  # JSON-serializable
    assert r["ctir_present"] is True
    assert r["narrative_plan_present"] is True
    assert r["stamp_matches"] is True
    assert r["prompt_consumes_plan"] is True
    assert r["raw_state_prompt_bypass_detected"] is False
    assert r["emergency_nonplan_allowed"] is False
    assert r["failure_codes"] == []
    assert planner_convergence_ok(r) is True


def test_fails_ctir_without_plan() -> None:
    stamp = "turn:2b:1c"
    session: dict = {}
    _attach_ctir(session, stamp=stamp)
    r = build_planner_convergence_report(
        path_label="action_outcome",
        owner_module="tests",
        session=session,
        prompt_payload={"narrative_plan": {"narrative_mode": "observe"}},
    )
    assert r["failure_codes"] == [MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN]
    assert planner_convergence_ok(r) is False


def test_fails_stamp_mismatch() -> None:
    session: dict = {}
    _attach_ctir(session, stamp="aaa")
    _attach_bundle(session, stamp="bbb", plan={"narrative_mode": "observe"})
    r = build_planner_convergence_report(
        path_label="dialogue_social",
        owner_module="tests",
        session=session,
        prompt_payload={"narrative_plan": {"narrative_mode": "observe"}},
    )
    assert NARRATIVE_PLAN_STAMP_MISMATCH in r["failure_codes"]
    assert planner_convergence_ok(r) is False


def test_emergency_explicitly_allowed_records_nonplan_without_failures() -> None:
    stamp = "turn:3c:2d"
    session: dict = {}
    _attach_ctir(session, stamp=stamp)
    r = build_planner_convergence_report(
        path_label="transition",
        owner_module="tests",
        session=session,
        prompt_payload=None,
        emergency_nonplan_allowed=True,
        emergency_fallback_label="upstream_api_fast_fallback",
    )
    assert r["emergency_nonplan_allowed"] is True
    assert r["narrative_plan_present"] is False
    assert r["failure_codes"] == []
    assert planner_convergence_ok(r) is True


def test_unknown_player_facing_path_fails() -> None:
    r = build_planner_convergence_report(
        path_label="not_a_registered_block_a_label",
        owner_module="tests",
        session={},
    )
    assert UNREGISTERED_NARRATION_PATH in r["failure_codes"]
    assert planner_convergence_ok(r) is False


def test_prompt_missing_plan_when_chain_ok() -> None:
    stamp = "turn:4d:3e"
    session: dict = {}
    _attach_ctir(session, stamp=stamp)
    _attach_bundle(session, stamp=stamp, plan={"narrative_mode": "observe"})
    r = build_planner_convergence_report(
        path_label="exposition_answer",
        owner_module="tests",
        session=session,
        prompt_payload={"narrative_plan": None},
    )
    assert PROMPT_PAYLOAD_MISSING_NARRATIVE_PLAN in r["failure_codes"]


def test_raw_semantic_shortcut_from_narration_seam_audit() -> None:
    stamp = "turn:5e:4f"
    session: dict = {}
    _attach_ctir(session, stamp=stamp)
    _attach_bundle(session, stamp=stamp, plan={"narrative_mode": "observe"})
    r = build_planner_convergence_report(
        path_label="scene_opening",
        owner_module="tests",
        session=session,
        prompt_payload={
            "narrative_plan": {"narrative_mode": "observe"},
            "narration_seam_audit": {"semantic_bypass_blocked": True},
        },
    )
    assert r["raw_state_prompt_bypass_detected"] is True
    assert PROMPT_PAYLOAD_USES_RAW_SEMANTIC_SHORTCUT in r["failure_codes"]


def test_non_narrative_debug_path_disables_enforcement() -> None:
    r = build_planner_convergence_report(
        path_label="non_narrative_debug",
        owner_module="tests",
        session={},
    )
    assert r["enabled"] is False
    assert r["failure_codes"] == []
