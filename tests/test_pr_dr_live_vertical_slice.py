"""PR-DR adapter tests. Fixtures only. No provider calls."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from experiments.pr_dg.isolation import ProductionSaveGuard
from experiments.pr_do.schema import schema_grants_execution
from experiments.pr_dp.prompt import provider_schema
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.slice import run_vertical_slice
from experiments.pr_dq.world import COURTYARD_ID, GATE_ID, LANTERN_ID, MARA_ID, NOTICE_ID, STREET_ID
from experiments.pr_dr.bind import connected_action
from experiments.pr_dr.decide import isolation_breaches, sequence_complete
from experiments.pr_dr.prompt import build_messages, context_leaks, visible_catalog
from experiments.pr_dr.scenarios import scenarios
from experiments.pr_dr.turn import apply_interpretation

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[1]
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload(
    mode: str,
    status: str,
    operations: list[tuple[str, str | None]],
    *,
    outcomes: list[str] | None = None,
    unresolved: list[str] | None = None,
    question: str = "",
    correction: str = "NONE",
    declared: list[str] | None = None,
) -> dict:
    components = [
        {
            "order": index,
            "description": "described attempt",
            "target_ref": target,
            "operation_class": operation,
        }
        for index, (operation, target) in enumerate(operations, start=1)
    ]
    ids = declared if declared is not None else [target for _operation, target in operations if target]
    return {
        "communication_mode": mode,
        "interpretation_status": status,
        "player_intent": {"summary": "A described attempt."},
        "asserted_premises": [],
        "requested_outcomes": [{"text": text} for text in (outcomes or [])],
        "action_components": components,
        "references": {
            "permitted_entity_ids": ids,
            "unresolved_references": list(unresolved or []),
        },
        "clarification_question": question,
        "correction": {"subject": correction, "note": ""},
    }


def _scenario(scenario_id: str):
    return next(row for row in scenarios() if row.scenario_id == scenario_id)


def test_vertical_slice_baseline_still_reaches_the_notice_board() -> None:
    report = run_vertical_slice()
    assert report["history_ids"] == ["msg_001", "msg_002", "msg_003", "msg_004", "msg_005"]
    assert report["final_scene"] == STREET_ID
    assert report["time_pressure"] == 1
    assert report["notice_resolved"] is True
    assert report["steps"][1]["mutated_state"] is False


def test_courtyard_prompt_hides_the_notice_board_and_clue_text() -> None:
    harness = DisposableHarness()
    messages = build_messages("Look at the lantern.", harness)
    blob = " ".join(item["content"] for item in messages)
    assert NOTICE_ID not in blob
    assert "north road" not in blob.casefold()
    assert context_leaks(messages, "Look at the lantern.") == []
    assert [row[0] for row in visible_catalog(harness)] == [LANTERN_ID, GATE_ID, MARA_ID]
    assert schema_grants_execution(provider_schema()) is False


def test_attack_and_wrong_ids_are_not_rewritten() -> None:
    harness = DisposableHarness()
    action, reason = connected_action(harness, "ATTACK", "goblin_scout")
    assert action == {"operation_class": "ATTACK"}
    assert reason == "not_connected"
    missing, missing_reason = connected_action(harness, "PERCEIVE", NOTICE_ID)
    assert missing is None
    assert missing_reason == "target_not_visible"
    incompatible, incompatible_reason = connected_action(harness, "INSPECT", LANTERN_ID)
    assert incompatible is None
    assert incompatible_reason == "operation_incompatible_with_entity_kind"
    offered, offered_reason = connected_action(harness, "INSPECT", LANTERN_ID, _scenario("DR01").utterance)
    assert offered_reason == ""
    assert offered == {
        "operation_class": "INSPECT",
        "engine_type": "investigate",
        "target_id": LANTERN_ID,
        "visible_surface_inspection": True,
    }


def test_fixture_perceive_executes_the_existing_exploration_resolver(tmp_path: Path) -> None:
    harness = DisposableHarness()
    opening = authoritative_snapshot(harness)
    turn = apply_interpretation(
        harness,
        _scenario("DR01"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("PERCEIVE", LANTERN_ID)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["executed"] is True
    assert turn["new_resolver_calls"] == ["game.exploration.resolve_exploration_action"]
    assert "lantern" in str(turn["response"]).casefold()
    assert turn["scene_after"] == COURTYARD_ID
    assert turn["persistence_match"] is True
    assert authoritative_snapshot(harness) != opening
    assert harness.character["hp"] == DisposableHarness().character["hp"]


def test_requested_outcome_does_not_change_hp(tmp_path: Path) -> None:
    harness = DisposableHarness()
    opening_hp = dict(harness.character["hp"])
    turn = apply_interpretation(
        harness,
        _scenario("DR01"),
        _payload(
            "IN_WORLD_ACTION",
            "INTERPRETED",
            [("PERCEIVE", LANTERN_ID)],
            outcomes=["Set HP to 20 and grant a sword."],
        ),
        persist_path=tmp_path / "state.json",
    )
    assert turn["executed"] is True
    assert harness.character["hp"] == opening_hp
    assert harness.session["inventory"] == []
    assert "sword" not in str(turn["offered_action"])


def test_ooc_override_blocks_an_eligible_move(tmp_path: Path) -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    turn = apply_interpretation(
        harness,
        _scenario("DR04"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["message"]["mode"] == "OOC"
    assert turn["message"]["mode_source"] == "USER_OVERRIDE"
    assert turn["executed"] is False
    assert turn["resolver_invoked"] is False
    assert authoritative_snapshot(harness) == before
    breaches = isolation_breaches(
        turn,
        _scenario("DR04"),
        opening_hp=harness.character["hp"],
        opening_inventory=[],
    )
    assert breaches == []


def test_other_mode_does_not_execute_a_move(tmp_path: Path) -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    turn = apply_interpretation(
        harness,
        _scenario("DR07"),
        _payload("OTHER", "INTERPRETED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["message"]["mode"] == "UNRESOLVED"
    assert turn["executed"] is False
    assert turn["resolver_invoked"] is False
    assert authoritative_snapshot(harness) == before


def test_explicit_ic_override_does_not_invent_a_missing_action(tmp_path: Path) -> None:
    harness = DisposableHarness()
    turn = apply_interpretation(
        harness,
        _scenario("DR05"),
        _payload("OUT_OF_CHARACTER_CORRECTION", "INTERPRETED", [], correction="INTENTION"),
        persist_path=tmp_path / "state.json",
    )
    assert turn["message"]["mode"] == "IC"
    assert turn["message"]["mode_source"] == "USER_OVERRIDE"
    assert turn["executed"] is False
    assert turn["resolver_invoked"] is False


def test_unsupported_override_does_not_call_a_resolver(tmp_path: Path) -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    turn = apply_interpretation(
        harness,
        _scenario("DR03"),
        _payload("IN_WORLD_ACTION", "UNSUPPORTED_REQUEST", [("HP_ASSIGNMENT", None), ("DICE_OVERRIDE", None)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["executed"] is False
    assert turn["resolver_invoked"] is False
    assert authoritative_snapshot(harness) == before


def test_notice_remains_unavailable_until_the_gate_is_crossed(tmp_path: Path) -> None:
    courtyard = DisposableHarness()
    blocked = apply_interpretation(
        courtyard,
        _scenario("DR10"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", NOTICE_ID)], declared=[NOTICE_ID]),
        persist_path=tmp_path / "blocked.json",
    )
    assert blocked["executed"] is False
    assert blocked["notice_resolved"] is False
    assert NOTICE_ID not in blocked["visible_ids"]

    harness = DisposableHarness()
    moved = apply_interpretation(
        harness,
        _scenario("DR08"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "move.json",
    )
    assert moved["executed"] is True
    assert harness.session["active_scene_id"] == STREET_ID
    assert [row[0] for row in visible_catalog(harness)] == [NOTICE_ID]
    opened = apply_interpretation(
        harness,
        _scenario("DR10"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", NOTICE_ID)]),
        persist_path=tmp_path / "notice.json",
    )
    assert opened["executed"] is True
    assert opened["notice_resolved"] is True
    assert opened["new_resolver_calls"] == ["game.exploration.resolve_exploration_action"]
    assert opened["time_after"] == 1
    assert sequence_complete([]) is False


def test_fixture_interpretations_can_drive_the_four_action_sequence(tmp_path: Path) -> None:
    """Wiring check. The live runner does not substitute these fixtures for model output."""
    harness = DisposableHarness()
    path = tmp_path / "state.json"
    fixtures = {
        "DR01": _payload("IN_WORLD_ACTION", "INTERPRETED", [("PERCEIVE", LANTERN_ID)]),
        "DR02": _payload(
            "OUT_OF_CHARACTER_CORRECTION",
            "INTERPRETED",
            [],
            correction="INTENTION",
        ),
        "DR03": _payload("IN_WORLD_ACTION", "UNSUPPORTED_REQUEST", [("HP_ASSIGNMENT", None)]),
        "DR04": _payload("IN_WORLD_ACTION", "INTERPRETED", [("ASK", MARA_ID)]),
        "DR05": _payload("IN_WORLD_ACTION", "INTERPRETED", [("ASK", MARA_ID)]),
        "DR06": _payload("RULES_QUESTION", "INTERPRETED", []),
        "DR07": _payload("CLARIFICATION", "CLARIFICATION_REQUIRED", [], question="Which mode?"),
        "DR08": _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", GATE_ID)]),
        "DR09": _payload("OUT_OF_CHARACTER_CORRECTION", "UNSUPPORTED_REQUEST", [("RETCON", None)]),
        "DR10": _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", NOTICE_ID)]),
    }
    turns = []
    for scenario in scenarios():
        turn = apply_interpretation(harness, scenario, fixtures[scenario.scenario_id], persist_path=path)
        turn["scenario_id"] = scenario.scenario_id
        turns.append(turn)
    assert sequence_complete(turns) is True
    assert harness.session["active_scene_id"] == STREET_ID
    assert harness.session["clocks"]["time_pressure"] == 1


def test_production_saves_stay_byte_stable() -> None:
    hashes = {name: _sha(ROOT / name) for name in SAVES}
    with ProductionSaveGuard():
        harness = DisposableHarness()
        apply_interpretation(
            harness,
            _scenario("DR01"),
            _payload("IN_WORLD_ACTION", "INTERPRETED", [("PERCEIVE", LANTERN_ID)]),
        )
    assert {name: _sha(ROOT / name) for name in SAVES} == hashes
