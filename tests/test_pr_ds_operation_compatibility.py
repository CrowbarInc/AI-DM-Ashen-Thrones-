"""PR-DS compatibility and stored-output replay. No provider calls."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from experiments.pr_dg.isolation import ProductionSaveGuard
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.world import (
    COURTYARD_ID,
    GATE_ID,
    LANTERN_ID,
    LANTERN_TEXT,
    MARA_ID,
    NOTICE_ID,
    NOTICE_TEXT,
    STREET_ID,
)
from experiments.pr_dr.bind import connected_action
from experiments.pr_dr.scenarios import scenarios
from experiments.pr_dr.turn import apply_interpretation
from experiments.pr_ds.replay import replay_stored_outputs

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[1]
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")
SECRET = "A brass token is sealed inside the lantern glass."


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scenario(scenario_id: str):
    return next(row for row in scenarios() if row.scenario_id == scenario_id)


def _payload(mode: str, status: str, operations: list[tuple[str, str | None]], *, outcomes: list[str] | None = None) -> dict:
    components = [
        {"order": index, "description": "described attempt", "target_ref": target, "operation_class": operation}
        for index, (operation, target) in enumerate(operations, start=1)
    ]
    return {
        "communication_mode": mode,
        "interpretation_status": status,
        "player_intent": {"summary": "A described attempt."},
        "asserted_premises": [],
        "requested_outcomes": [{"text": text} for text in (outcomes or [])],
        "action_components": components,
        "references": {
            "permitted_entity_ids": [target for _operation, target in operations if target],
            "unresolved_references": [],
        },
        "clarification_question": "",
        "correction": {"subject": "NONE", "note": ""},
    }


def _seal_hidden_token(harness: DisposableHarness) -> None:
    scene = harness.active_envelope()["scene"]
    scene["hidden_facts"] = [SECRET]
    scene["interactables"].append(
        {
            "id": "sealed_token",
            "label": "sealed token",
            "type": "examine",
            "description": SECRET,
        }
    )


def test_lantern_inspect_uses_the_investigate_resolver_and_visible_fact(tmp_path: Path) -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    turn = apply_interpretation(
        harness,
        _scenario("DR01"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", LANTERN_ID)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["compatibility"] == "visible_surface_inspection"
    assert turn["offered_action"]["operation_class"] == "INSPECT"
    assert turn["offered_action"]["engine_type"] == "investigate"
    assert turn["operation_classes"] == ["INSPECT"]
    assert turn["executed"] is True
    assert turn["new_resolver_calls"] == ["game.exploration.resolve_exploration_action"]
    assert turn["response"] == LANTERN_TEXT
    assert NOTICE_TEXT not in str(turn["response"])
    assert turn["scene_after"] == COURTYARD_ID
    assert turn["time_after"] == 0
    assert turn["rolls_dice"] is False
    assert turn["notice_resolved"] is False
    assert turn["persistence_match"] is True
    assert authoritative_snapshot(harness) != before
    runtime = (harness.session.get("scene_runtime") or {}).get(COURTYARD_ID) or {}
    assert LANTERN_ID not in (runtime.get("resolved_interactables") or [])


def test_perceive_lantern_stays_on_observe(tmp_path: Path) -> None:
    harness = DisposableHarness()
    turn = apply_interpretation(
        harness,
        _scenario("DR01"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("PERCEIVE", LANTERN_ID)]),
        persist_path=tmp_path / "state.json",
    )
    assert turn["compatibility"] == ""
    assert turn["offered_action"]["engine_type"] == "observe"
    assert turn["executed"] is True
    assert turn["response"] == LANTERN_TEXT
    assert turn["time_after"] == 0


def test_requested_outcome_on_lantern_inspect_does_not_grant_hp_or_items(tmp_path: Path) -> None:
    harness = DisposableHarness()
    opening_hp = harness.character["hp"]
    turn = apply_interpretation(
        harness,
        _scenario("DR01"),
        _payload(
            "IN_WORLD_ACTION",
            "INTERPRETED",
            [("INSPECT", LANTERN_ID)],
            outcomes=["Set HP to 99 and grant a sword."],
        ),
        persist_path=tmp_path / "state.json",
    )
    assert turn["executed"] is True
    assert harness.character["hp"] == opening_hp
    assert harness.session["inventory"] == []
    assert "sword" not in str(turn["offered_action"])


def test_notice_inspect_after_transition_still_discovers_the_clue(tmp_path: Path) -> None:
    harness = DisposableHarness()
    moved = apply_interpretation(
        harness,
        _scenario("DR08"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "move.json",
    )
    assert moved["executed"] is True
    blocked = connected_action(harness, "PERCEIVE", NOTICE_ID, "Let me read the notice board.")
    assert blocked[0] is None
    assert blocked[1] == "operation_incompatible_with_entity_kind"
    opened = apply_interpretation(
        harness,
        _scenario("DR10"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", NOTICE_ID)]),
        persist_path=tmp_path / "notice.json",
    )
    assert opened["compatibility"] == ""
    assert opened["offered_action"]["engine_type"] == "investigate"
    assert opened["offered_action"].get("visible_surface_inspection") is not True
    assert opened["executed"] is True
    assert opened["response"] == NOTICE_TEXT
    assert opened["notice_resolved"] is True
    assert opened["time_after"] == 1


def test_visible_surface_flag_does_not_accept_the_notice_clue() -> None:
    harness = DisposableHarness()
    harness.submit(
        "I'll head out through the gate.",
        message_id="move",
        mode_override="IC",
        intent="ACTION",
        action={
            "operation_class": "MOVE",
            "engine_type": "scene_transition",
            "target_id": GATE_ID,
            "target_scene_id": STREET_ID,
        },
    )
    before = authoritative_snapshot(harness)
    message = harness.submit(
        "Let me read the notice board.",
        message_id="forced",
        mode_override="IC",
        intent="ACTION",
        action={
            "operation_class": "INSPECT",
            "engine_type": "investigate",
            "target_id": NOTICE_ID,
            "visible_surface_inspection": True,
        },
    )
    assert message.processing_result["executed"] is False
    assert NOTICE_TEXT not in str(message.processing_result["response"])
    assert authoritative_snapshot(harness) == before
    runtime = (harness.session.get("scene_runtime") or {}).get(STREET_ID) or {}
    assert NOTICE_ID not in (runtime.get("resolved_interactables") or [])


def test_negative_targets_stay_blocked(tmp_path: Path) -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    hidden, hidden_reason = connected_action(harness, "INSPECT", "brass_token", "I inspect the brass token.")
    assert hidden is None and hidden_reason == "target_not_visible"
    unknown, unknown_reason = connected_action(harness, "INSPECT", "invented_relic", "I inspect the invented relic.")
    assert unknown is None and unknown_reason == "target_not_visible"
    wrong_scene, wrong_reason = connected_action(harness, "INSPECT", NOTICE_ID, "Let me read the notice board.")
    assert wrong_scene is None and wrong_reason == "target_not_visible"
    person, person_reason = connected_action(harness, "INSPECT", MARA_ID, "I inspect Sergeant Mara.")
    assert person is None and person_reason == "operation_incompatible_with_entity_kind"
    gate, gate_reason = connected_action(harness, "INSPECT", GATE_ID, "I inspect the courtyard gate.")
    assert gate is None and gate_reason == "operation_incompatible_with_entity_kind"
    perceive_hidden, perceive_reason = connected_action(harness, "PERCEIVE", "brass_token", "I look at the brass token.")
    assert perceive_hidden is None and perceive_reason == "target_not_visible"
    _seal_hidden_token(harness)
    sealed = authoritative_snapshot(harness)
    secret, secret_reason = connected_action(harness, "INSPECT", "sealed_token", "I inspect the sealed token.")
    assert secret is None and secret_reason == "operation_incompatible_with_entity_kind"
    redirected = apply_interpretation(
        harness,
        replace(
            _scenario("DR01"),
            scenario_id="DR01_HIDDEN",
            utterance="I inspect the brass token hidden under the lantern.",
        ),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("INSPECT", LANTERN_ID)]),
        persist_path=tmp_path / "redirect.json",
    )
    assert redirected["executed"] is False
    assert redirected["resolver_invoked"] is False
    assert SECRET not in str(redirected["response"])
    assert "brass token" not in str(redirected["response"]).casefold()
    unsupported = apply_interpretation(
        harness,
        replace(_scenario("DR03"), scenario_id="DR03_HP"),
        _payload("IN_WORLD_ACTION", "UNSUPPORTED_REQUEST", [("HP_ASSIGNMENT", None)]),
        persist_path=tmp_path / "hp.json",
    )
    assert unsupported["executed"] is False and unsupported["resolver_invoked"] is False
    granted = apply_interpretation(
        harness,
        replace(_scenario("DR03"), scenario_id="DR03_GRANT"),
        _payload("IN_WORLD_ACTION", "UNSUPPORTED_REQUEST", [("INVENTORY_GRANT", None)]),
        persist_path=tmp_path / "grant.json",
    )
    assert granted["executed"] is False
    assert harness.session["inventory"] == []
    ooc = apply_interpretation(
        harness,
        replace(_scenario("DR09"), scenario_id="DR09_OOC"),
        _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "ooc.json",
    )
    assert ooc["message"]["mode"] == "OOC"
    assert ooc["executed"] is False and ooc["resolver_invoked"] is False
    ambiguous = apply_interpretation(
        harness,
        replace(_scenario("DR07"), scenario_id="DR07_AMBIGUOUS"),
        _payload("CLARIFICATION", "CLARIFICATION_REQUIRED", [("MOVE", GATE_ID)]),
        persist_path=tmp_path / "ambiguous.json",
    )
    assert ambiguous["executed"] is False and ambiguous["resolver_invoked"] is False
    malformed = apply_interpretation(
        harness,
        replace(_scenario("DR01"), scenario_id="DR01_MALFORMED"),
        None,
        persist_path=tmp_path / "malformed.json",
    )
    assert malformed["executed"] is False and malformed["schema_valid"] is False
    broken = apply_interpretation(
        harness,
        replace(_scenario("DR01"), scenario_id="DR01_BROKEN"),
        {"communication_mode": "IN_WORLD_ACTION"},
        persist_path=tmp_path / "broken.json",
    )
    assert broken["executed"] is False
    assert harness.character["hp"] == DisposableHarness().character["hp"]
    assert harness.session["active_scene_id"] == COURTYARD_ID
    assert harness.session["clocks"]["time_pressure"] == 0
    assert authoritative_snapshot(harness) == sealed
    assert sealed == before


def test_stored_live_outputs_execute_the_four_actions_without_rewriting_them(tmp_path: Path) -> None:
    hashes = {name: _sha(ROOT / name) for name in SAVES}
    raw = ROOT / "artifacts" / "pr_dr_live_vertical_slice" / "raw_results.json"
    raw_hash = _sha(raw)
    with ProductionSaveGuard():
        report = replay_stored_outputs(tmp_path / "state.json")
    assert {name: _sha(ROOT / name) for name in SAVES} == hashes
    assert _sha(raw) == raw_hash
    assert report["provider_hits"] == []
    assert report["production_saves_unchanged"] is True
    assert report["prompt_mismatches"] == []
    assert report["persistence_failures"] == []
    assert report["gameplay_executed"] == ["DR01", "DR05", "DR08", "DR10"]
    assert report["non_gameplay_executed"] == []
    assert report["pr_dr_sequence_complete"] is False
    assert report["final_scene"] == STREET_ID
    assert report["time_pressure"] == 1
    assert report["notice_resolved"] is True
    assert report["hp"] == report["opening_hp"]
    assert report["inventory"] == []
    assert report["lantern_text_disclosed"] is True
    assert report["notice_text_on_dr01"] is False
    by_id = {row["scenario_id"]: row for row in report["rows"]}
    assert by_id["DR01"]["operation_classes"] == ["INSPECT"]
    assert by_id["DR01"]["target_refs"] == [LANTERN_ID]
    assert by_id["DR01"]["compatibility"] == "visible_surface_inspection"
    assert by_id["DR01"]["time_after"] == 0
    assert by_id["DR01"]["meaningful_change"] is False
    assert by_id["DR05"]["executed"] is True
    assert by_id["DR05"]["new_resolver_calls"] == ["game.social.resolve_social_action"]
    assert by_id["DR08"]["scene_after"] == STREET_ID
    assert by_id["DR08"]["time_after"] == 1
    assert by_id["DR08"]["meaningful_change"] is True
    assert by_id["DR10"]["response"] == NOTICE_TEXT
    assert by_id["DR10"]["notice_resolved"] is True
    for scenario_id in ("DR02", "DR03", "DR04", "DR06", "DR07", "DR09"):
        row = by_id[scenario_id]
        assert row["executed"] is False
        assert row["resolver_invoked"] is False
        assert row["meaningful_change"] is False
        assert row["time_after"] == row["time_before"]
    assert report["history_ids"] == [row.scenario_id.lower() for row in scenarios()]
    assert report["notice_before_transition"]["executed"] is False
    assert report["notice_before_transition"]["notice_resolved"] is False
    assert NOTICE_ID not in report["notice_before_transition"]["visible_ids"]
    assert "resp_" in str(report["dr09_usage"]["request_id"])
    assert report["harness_note"]
