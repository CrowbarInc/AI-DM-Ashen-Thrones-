"""C1-A scene-opening convergence metrics on scenario-spine evaluation (offline, observational)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.scenario_spine import scenario_spine_from_dict
from game.scenario_spine_eval import evaluate_scenario_spine_session, minimal_complete_transcript_turn_meta
from game.scenario_spine_opening_convergence import (
    capture_opening_convergence_meta_from_chat_payload,
    evaluate_opening_convergence_for_turn_rows,
)

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_OPENING = ROOT / "data" / "validation" / "scenario_spines" / "c1a_opening_convergence_paths.json"
FIXTURE_LONG = ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _so_campaign() -> dict:
    return {
        "opening_required": True,
        "opening_reason": "campaign_start",
        "scene_id": "s_gate",
        "location_anchors": ["Cinderwatch Gate"],
        "actor_anchors": [{"entity_id": "npc_serjeant", "anchor_role": "interlocutor"}],
        "active_pressures": {},
        "visible_fact_categories": ["A"],
        "visible_fact_anchor_ids": ["vf_slot:0"],
        "prohibited_content_codes": ["no_hidden_gm_facts_as_immediate_perception"],
        "derivation_codes": [],
        "validator": {"ok": True},
    }


def _meta(
    oc: dict,
    *,
    spine_id: str = "c1a_opening_convergence_paths",
    branch_id: str = "branch_campaign_start_probe",
    turn_id: str = "cs_01",
    turn_index: int = 0,
) -> dict:
    m = minimal_complete_transcript_turn_meta(
        spine_id=spine_id,
        branch_id=branch_id,
        turn_id=str(turn_id),
        turn_index=int(turn_index),
    )
    m["opening_convergence"] = oc
    return m


def test_clean_campaign_opening_passes() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = _so_campaign()
    gm = (
        "Cinderwatch Gate rises ahead; the serjeant watches the yard while census lines "
        "snarl traffic. Ash drifts across cobbles."
    )
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "Begin.",
            "gm_text": gm,
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": so,
                    "seam_trace": None,
                },
            ),
        },
    ]
    out = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)
    sh = out["session_health"]
    assert sh["opening_turns_checked"] == 1
    assert sh["opening_plan_backed_count"] == 1
    assert sh["opening_convergence_verdict"] == "pass"
    assert sh["opening_resume_entry_checked"] == 0


def test_clean_post_transition_opening_passes() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = {
        **_so_campaign(),
        "opening_reason": "post_transition",
    }
    turns = [
        {
            "turn_index": 0,
            "turn_id": "pt_01",
            "player_text": "x",
            "gm_text": "Cinderwatch Gate district noise returns; npc_serjeant is visible near the notice board.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": so,
                },
                branch_id="branch_post_transition_probe",
                turn_id="pt_01",
            ),
        },
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_post_transition_probe", turns)["session_health"]
    assert sh["opening_plan_backed_count"] == 1
    assert sh["opening_convergence_verdict"] == "pass"


def test_clean_resume_entry_opening_passes() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = {
        **_so_campaign(),
        "opening_reason": "resume_entry",
    }
    turns = [
        {
            "turn_index": 0,
            "turn_id": "re_01",
            "player_text": "resume",
            "gm_text": "Cinderwatch Gate and npc_serjeant still hold the line you remember.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {"resume_entry": True},
                    "scene_opening": so,
                },
                branch_id="branch_resume_entry_probe",
                turn_id="re_01",
            ),
        },
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_resume_entry_probe", turns)["session_health"]
    assert sh["opening_resume_entry_checked"] == 1
    assert sh["opening_convergence_verdict"] == "pass"


def test_opening_without_plan_fails_verdict_detected_failures() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "x",
            "gm_text": "Some narration.",
            "api_ok": True,
            "meta": _meta(
                {
                    "is_opening_turn": True,
                    "bundle_present": False,
                    "narrative_plan_present": False,
                    "planning_session_interaction": {},
                    "scene_opening": None,
                },
            ),
        },
    ]
    out = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)
    sh = out["session_health"]
    assert sh["opening_plan_missing_count"] == 1
    assert sh["opening_convergence_verdict"] == "fail"
    assert any(f.get("axis") == "opening_convergence" for f in out["detected_failures"])


def test_invalid_scene_opening_increments_invalid_count() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    bad = {**_so_campaign(), "opening_reason": "not_a_real_reason"}
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "x",
            "gm_text": "Cinderwatch Gate.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": bad,
                },
            ),
        },
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)["session_health"]
    assert sh["opening_invalid_plan_count"] == 1
    assert sh["opening_convergence_verdict"] == "fail"


def test_scene_opening_seam_invalid_increments_seam_count() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "x",
            "gm_text": "Blocked seam output.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": None,
                    "seam_trace": {
                        "reason": "scene_opening_seam_invalid",
                        "opening_required": True,
                        "opening_reason_inferred": "post_transition",
                        "validate_scene_opening": "scene_opening_missing_when_required",
                    },
                },
            ),
        },
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)["session_health"]
    assert sh["opening_seam_failure_count"] == 1
    assert sh["opening_convergence_verdict"] == "fail"


def test_stock_fallback_hit_on_opening_turn_scoring_only() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = _so_campaign()
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "x",
            "gm_text": "You wake in darkness, then Cinderwatch Gate resolves; the serjeant watches the yard.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": so,
                },
            ),
        },
    ]
    out = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)
    sh = out["session_health"]
    assert sh["opening_stock_fallback_hits"] == 1
    assert sh["opening_convergence_verdict"] == "pass"
    assert any(w.get("code") == "opening_style_signal" for w in out["warnings"])


def test_anchor_grounding_failure_when_anchors_exist() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = _so_campaign()
    turns = [
        {
            "turn_index": 0,
            "turn_id": "cs_01",
            "player_text": "x",
            "gm_text": "Generic crowd noise with no location or serjeant cues.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": so,
                },
            ),
        },
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)["session_health"]
    assert sh["opening_anchor_grounding_failures"] >= 1
    assert sh["opening_convergence_verdict"] == "fail"


def test_non_opening_turn_stock_phrase_not_attributed() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_LONG.read_text(encoding="utf-8")))
    turns = [
        {
            "turn_index": 0,
            "turn_id": "t0",
            "player_text": "x",
            "gm_text": "You wake in darkness but this is a continuation beat.",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": None,
                },
            ),
        },
    ]
    block = evaluate_opening_convergence_for_turn_rows(turns)
    assert block["opening_turns_checked"] == 0
    assert block["opening_stock_fallback_hits"] == 0


def test_capture_meta_shape_from_minimal_payload() -> None:
    payload = {
        "ok": True,
        "session": {
            "debug_traces": [
                {
                    "operation": "semantic_bypass_blocked",
                    "reason": "scene_opening_seam_invalid",
                    "extra": {
                        "opening_reason_inferred": "resume_entry",
                        "opening_required": True,
                        "validate_scene_opening": "scene_opening_missing_when_required",
                    },
                },
            ],
            "_runtime_narration_plan_bundle_v1": {
                "plan_metadata": {"planning_session_interaction": {"resume_entry": True}},
                "narrative_plan": {"scene_opening": {"opening_reason": "resume_entry", "opening_required": True}},
            },
        },
        "gm_output": {"metadata": {"narration_seam": {"path_kind": "resolved_turn_ctir_bundle", "plan_driven": True}}},
    }
    cap = capture_opening_convergence_meta_from_chat_payload(payload)
    assert cap["bundle_present"] is True
    assert cap["seam_trace"]["reason"] == "scene_opening_seam_invalid"


def test_frontier_fixture_clean_session_has_no_opening_observations_by_default() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_LONG.read_text(encoding="utf-8")))
    turns = [
        {
            "turn_index": i,
            "turn_id": f"t{i}",
            "player_text": "p",
            "gm_text": "Cinderwatch Gate district patrol rumor notice board Captain Thoran.",
            "api_ok": True,
            "meta": minimal_complete_transcript_turn_meta(
                spine_id=spine.spine_id,
                branch_id="branch_social_inquiry",
                turn_id=f"t{i}",
                turn_index=i,
            ),
        }
        for i in range(3)
    ]
    sh = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)["session_health"]
    assert sh["opening_turns_checked"] == 0
    assert sh["opening_convergence_verdict"] == "no_observations"


def test_validate_scenario_spine_fixture_loads() -> None:
    from game.scenario_spine import validate_scenario_spine_definition

    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    assert validate_scenario_spine_definition(spine) == []
    multi = next(b for b in spine.branches if b.branch_id == "branch_multi_transition_smoke")
    assert len(multi.turns) >= 12


def test_repeated_generic_first_line_warning_without_fail_verdict() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    so = _so_campaign()
    shared_first = (
        "Cinderwatch Gate rises through drifting ash as census lines choke the yard ahead; "
        "npc_serjeant watches the cobbles."
    )
    base_meta = {
        "bundle_present": True,
        "narrative_plan_present": True,
        "planning_session_interaction": {},
        "scene_opening": so,
        "seam_trace": None,
    }
    turns = [
        {
            "turn_index": i,
            "turn_id": f"rep_{i}",
            "player_text": "x",
            "gm_text": f"{shared_first}\nDetail line {i}.",
            "api_ok": True,
            "meta": _meta(
                {**base_meta, "is_opening_turn": True},
                turn_index=i,
                turn_id=f"rep_{i}",
            ),
        }
        for i in range(3)
    ]
    out = evaluate_scenario_spine_session(spine, "branch_campaign_start_probe", turns)
    sh = out["session_health"]
    assert sh["opening_convergence_verdict"] == "pass"
    assert sh["opening_repeated_generic_first_line"] is True
    assert any(w.get("code") == "opening_style_signal" for w in out["warnings"])


def test_opening_convergence_failure_detail_row_shape() -> None:
    spine = scenario_spine_from_dict(json.loads(FIXTURE_OPENING.read_text(encoding="utf-8")))
    turns_missing = [
        {
            "turn_index": 0,
            "turn_id": "t0",
            "player_text": "x",
            "gm_text": "x",
            "api_ok": True,
            "meta": _meta(
                {
                    "is_opening_turn": True,
                    "bundle_present": False,
                    "narrative_plan_present": False,
                    "planning_session_interaction": {},
                    "scene_opening": None,
                },
            ),
        },
    ]
    block = evaluate_opening_convergence_for_turn_rows(turns_missing)
    assert block["opening_convergence_failure_details"]
    row = block["opening_convergence_failure_details"][0]
    for key in (
        "turn_index",
        "opening_reason",
        "scene_id",
        "marker",
        "seam_failure_reason",
        "anchor_grounding_category",
        "suspected_source",
    ):
        assert key in row

    turns_seam = [
        {
            "turn_index": 1,
            "turn_id": "t1",
            "player_text": "x",
            "gm_text": "blocked",
            "api_ok": True,
            "meta": _meta(
                {
                    "bundle_present": True,
                    "narrative_plan_present": True,
                    "planning_session_interaction": {},
                    "scene_opening": None,
                    "seam_trace": {
                        "reason": "scene_opening_seam_invalid",
                        "opening_required": True,
                        "opening_reason_inferred": "scene_entry",
                        "validate_scene_opening": "scene_opening_missing_when_required",
                    },
                },
            ),
        },
    ]
    seam_block = evaluate_opening_convergence_for_turn_rows(turns_seam)
    seam_row = seam_block["opening_convergence_failure_details"][0]
    assert seam_row["marker"] == "scene_opening_seam_invalid"
    assert seam_row.get("seam_failure_reason")
