"""C1-B continuation convergence metrics on scenario-spine evaluation (offline, observational)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from game.scenario_spine import scenario_spine_from_dict
from game.scenario_spine_eval import evaluate_continuation_convergence_for_turn_rows, evaluate_scenario_spine_session

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_LONG = ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _spine() -> Mapping[str, Any]:
    return json.loads(FIXTURE_LONG.read_text(encoding="utf-8"))


def _clean_social_gm(turn_index: int) -> str:
    # Keep aligned with existing evaluator fixture expectations (anchors/progression keywords present).
    return (
        f"Turn {turn_index + 1}: Cinderwatch Gate District stays rain-slick; choke traffic "
        "and the notice board glare under tavern heat at the edge. The posted warning and "
        "tax lines still whisper a missing patrol while crowd tension rises. Gate serjeant, "
        "tavern runner, threadbare watcher, hooded lurker, and noble townhouse colors all "
        "register your presence. You learn what the watch will admit, what the notice omits, "
        "and where the patrol rumor points. Captain Thoran is named on duty chatter; Ash "
        "Compact census lines still delay carts. Faint muddy footprints lead northwest among "
        "crates—hurried movement. The patrol disappearance deepens: named routes, last sightings, "
        "and clock pressure mount as investigation advances. Watch posture hardens—curfew "
        "enforcement and gate security escalate when panic spikes."
    )


def _row(
    *,
    turn_index: int,
    turn_id: str,
    gm_text: str = "x",
    ctir_backed: bool | None = True,
    path_kind: str = "resolved_turn_ctir_bundle",
    emergency_nonplan_output: bool = False,
    explicit_nonplan_model_narration: bool = False,
    continuation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    seam: dict[str, Any] = {
        "path_kind": path_kind,
        "ctir_backed": ctir_backed,
        "emergency_nonplan_output": emergency_nonplan_output,
        "explicit_nonplan_model_narration": explicit_nonplan_model_narration,
    }
    if continuation is not None:
        seam["continuation"] = dict(continuation)
    return {
        "turn_index": turn_index,
        "turn_id": turn_id,
        "player_text": "p",
        "gm_text": gm_text,
        "api_ok": True,
        "meta": {"narration_seam": seam},
    }


def _plan_driven_verified(*, is_continuation_turn: bool = True) -> dict[str, Any]:
    return {
        "is_continuation_turn": is_continuation_turn,
        "requires_plan_driven_continuation": True,
        "continuation_plan_verified": True,
        "continuation_plan_failure_reason": None,
        "continuation_source": "narrative_plan_bundle",
    }


def test_clean_plan_driven_continuation_passes_and_fields_present() -> None:
    turns = [
        _row(
            turn_index=1,
            turn_id="t1",
            gm_text=_clean_social_gm(1),
            continuation=_plan_driven_verified(),
        ),
        _row(
            turn_index=2,
            turn_id="t2",
            gm_text=_clean_social_gm(2),
            continuation=_plan_driven_verified(),
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_convergence_passed"] is True
    assert block["continuation_turns_checked"] == 2
    assert block["continuation_plan_verified_count"] == 2
    assert block["continuation_emergency_nonplan_count"] == 0
    assert block["continuation_explicit_nonplan_count"] == 0
    assert block["continuation_engine_only_count"] == 0
    assert block["continuation_failure_reasons"] == []
    assert block["first_continuation_failure_turn_id"] is None


def test_opening_turn_is_excluded_from_continuation_checks() -> None:
    turns = [
        _row(
            turn_index=0,
            turn_id="open",
            gm_text=_clean_social_gm(0),
            continuation=_plan_driven_verified(is_continuation_turn=False),
        ),
        _row(
            turn_index=1,
            turn_id="cont",
            gm_text=_clean_social_gm(1),
            continuation=_plan_driven_verified(),
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_turns_checked"] == 1
    assert block["continuation_plan_verified_count"] == 1
    assert block["continuation_failure_reasons"] == []


def test_passive_ctir_bundle_source_requires_verified_plan() -> None:
    turns = [
        _row(
            turn_index=1,
            turn_id="t1",
            gm_text=_clean_social_gm(1),
            continuation={
                "is_continuation_turn": True,
                "requires_plan_driven_continuation": False,
                "continuation_plan_verified": False,
                "continuation_plan_failure_reason": "narrative_plan_missing",
                "continuation_source": "narrative_plan_bundle",
            },
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_convergence_passed"] is False
    assert block["continuation_turns_checked"] == 1
    assert "bundle_source_without_verification" in block["continuation_failure_reasons"]
    assert block["first_continuation_failure_turn_id"] == "t1"


def test_pressure_driven_ctir_backed_requires_verified_plan() -> None:
    turns = [
        _row(
            turn_index=5,
            turn_id="t5",
            gm_text=_clean_social_gm(5),
            continuation={
                "is_continuation_turn": True,
                "requires_plan_driven_continuation": True,
                "continuation_plan_verified": False,
                "continuation_plan_failure_reason": "ctir_stamp_mismatch",
                "continuation_source": "unverified",
            },
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_convergence_passed"] is False
    assert block["continuation_turns_checked"] == 1
    assert any(r.startswith("continuation_plan_unverified:") for r in block["continuation_failure_reasons"])
    assert block["first_continuation_failure_turn_id"] == "t5"


def test_missing_or_unverified_bundle_fails_and_first_failure_turn_id_reported() -> None:
    turns = [
        _row(
            turn_index=3,
            turn_id="first_bad",
            gm_text=_clean_social_gm(3),
            continuation={
                "is_continuation_turn": True,
                "requires_plan_driven_continuation": True,
                "continuation_plan_verified": False,
                "continuation_plan_failure_reason": "narrative_plan_missing",
                "continuation_source": "unverified",
            },
        ),
        _row(
            turn_index=4,
            turn_id="second_bad",
            gm_text=_clean_social_gm(4),
            continuation={
                "is_continuation_turn": True,
                "requires_plan_driven_continuation": True,
                "continuation_plan_verified": False,
                "continuation_plan_failure_reason": "bundle_absent",
                "continuation_source": "unverified",
            },
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_convergence_passed"] is False
    assert block["continuation_turns_checked"] == 2
    assert block["first_continuation_failure_turn_id"] == "first_bad"
    assert any(r.startswith("continuation_plan_unverified:") for r in block["continuation_failure_reasons"])


def test_emergency_and_explicit_nonplan_are_counted_separately() -> None:
    turns = [
        _row(
            turn_index=1,
            turn_id="em",
            gm_text="Emergency path.",
            emergency_nonplan_output=True,
            continuation=_plan_driven_verified(),
        ),
        _row(
            turn_index=2,
            turn_id="xp",
            gm_text="Explicit nonplan path.",
            explicit_nonplan_model_narration=True,
            continuation=_plan_driven_verified(),
        ),
        _row(
            turn_index=3,
            turn_id="ok",
            gm_text=_clean_social_gm(3),
            continuation=_plan_driven_verified(),
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_emergency_nonplan_count"] == 1
    assert block["continuation_explicit_nonplan_count"] == 1
    assert block["continuation_turns_checked"] == 1
    assert block["continuation_plan_verified_count"] == 1
    assert block["continuation_failure_reasons"] == []


def test_engine_only_and_non_ctir_are_counted_separately() -> None:
    turns = [
        _row(
            turn_index=1,
            turn_id="engine",
            gm_text="Engine prompt.",
            ctir_backed=False,
            path_kind="engine_check_required_prompt",
            continuation={"is_continuation_turn": True},
        ),
        _row(
            turn_index=2,
            turn_id="non_ctir_other",
            gm_text="Non-CTIR freeform output.",
            ctir_backed=False,
            path_kind="non_resolution_model_narration",
            continuation={"is_continuation_turn": True},
        ),
        _row(
            turn_index=3,
            turn_id="ok",
            gm_text=_clean_social_gm(3),
            continuation=_plan_driven_verified(),
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_engine_only_count"] == 2
    assert block["continuation_turns_checked"] == 1
    assert block["continuation_plan_verified_count"] == 1


def test_generic_filler_fails_only_on_normal_plan_driven_continuation() -> None:
    turns = [
        _row(
            turn_index=1,
            turn_id="bad",
            gm_text="The scene holds. Nothing changes.",
            continuation=_plan_driven_verified(),
        ),
        _row(
            turn_index=2,
            turn_id="em_ok",
            gm_text="The scene holds. Nothing changes.",
            emergency_nonplan_output=True,
            continuation=_plan_driven_verified(),
        ),
        _row(
            turn_index=3,
            turn_id="xp_ok",
            gm_text="The scene holds. Nothing changes.",
            explicit_nonplan_model_narration=True,
            continuation=_plan_driven_verified(),
        ),
    ]
    block = evaluate_continuation_convergence_for_turn_rows(turns)
    assert block["continuation_convergence_passed"] is False
    assert block["first_continuation_failure_turn_id"] == "bad"
    assert any(r.startswith("continuation_generic_filler:") for r in block["continuation_failure_reasons"])
    assert block["continuation_emergency_nonplan_count"] == 1
    assert block["continuation_explicit_nonplan_count"] == 1


def test_session_health_includes_continuation_fields_from_evaluator() -> None:
    spine = scenario_spine_from_dict(_spine())
    raw = _spine()
    branch = next(b for b in raw["branches"] if b["branch_id"] == "branch_social_inquiry")
    turns: list[dict[str, Any]] = []
    for i in range(25):
        tid = branch["turns"][i]["turn_id"]
        if i == 0:
            cont = _plan_driven_verified(is_continuation_turn=False)
        else:
            cont = _plan_driven_verified()
        turns.append(
            _row(
                turn_index=i,
                turn_id=tid,
                gm_text=_clean_social_gm(i),
                continuation=cont,
            )
        )
    out = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    sh = out["session_health"]
    # Continuation convergence fields
    assert sh["continuation_convergence_passed"] is True
    assert sh["continuation_turns_checked"] == 24
    assert sh["continuation_plan_verified_count"] == 24
    assert sh["continuation_emergency_nonplan_count"] == 0
    assert sh["continuation_explicit_nonplan_count"] == 0
    assert sh["continuation_engine_only_count"] == 0
    assert sh["continuation_failure_reasons"] == []
    assert sh["first_continuation_failure_turn_id"] is None
