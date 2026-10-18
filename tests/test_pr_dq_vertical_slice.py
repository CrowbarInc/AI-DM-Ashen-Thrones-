"""PR-DQ four-turn slice. The OOC interruption sits between turn 1 and turn 2."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.slice import OOC_INTERRUPTION, SEQUENCE, TURN_1, TURN_2, TURN_3, TURN_4, run_vertical_slice
from experiments.pr_dq.world import LANTERN_TEXT, MARA_ANSWER, NOTICE_TEXT, STREET_ARRIVAL, STREET_ID

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[1]
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _play(harness: DisposableHarness, spec: dict):
    return harness.submit(
        spec["text"],
        message_id=spec["message_id"],
        mode_override=spec["mode_override"],
        intent=spec["intent"],
        action=spec["action"],
    )


def test_four_turn_sequence_keeps_the_ooc_interruption_in_one_history() -> None:
    hashes = {name: _sha(ROOT / name) for name in SAVES}
    harness = DisposableHarness()
    opening_hp = dict(harness.character["hp"])

    lantern = _play(harness, TURN_1)
    assert lantern.mode == "IC"
    assert lantern.mode_source == "USER_OVERRIDE"
    assert lantern.processing_result["resolution_kind"] == "observe"
    assert lantern.processing_result["resolution_success"] is None
    assert lantern.processing_result["rolls_dice"] is False
    assert lantern.processing_result["response"] == LANTERN_TEXT
    assert harness.session["active_scene_id"] == "waystation_courtyard"
    assert harness.session["clocks"]["time_pressure"] == 0
    assert harness.session["npc_runtime"] == {}

    before_ooc = authoritative_snapshot(harness)
    interruption = _play(harness, OOC_INTERRUPTION)
    assert interruption.mode == "OOC"
    assert interruption.committed is False
    assert interruption.processing_result["executed"] is False
    assert interruption.processing_result["resolver_invoked"] is False
    assert interruption.processing_result["advances_time"] is False
    assert authoritative_snapshot(harness) == before_ooc
    assert harness.resolver_calls == ["game.exploration.resolve_exploration_action"]

    mara = _play(harness, TURN_2)
    assert mara.destination == "IC_DIALOGUE"
    assert mara.processing_result["resolution_kind"] == "question"
    assert mara.processing_result["response"] == MARA_ANSWER
    assert "sergeant_mara" in harness.session["npc_runtime"]
    assert harness.session["active_scene_id"] == "waystation_courtyard"
    assert harness.session["clocks"]["time_pressure"] == 0

    gate = _play(harness, TURN_3)
    assert gate.processing_result["resolution_kind"] == "scene_transition"
    assert gate.processing_result["advances_time"] is True
    assert gate.processing_result["response"] == STREET_ARRIVAL
    assert harness.session["active_scene_id"] == STREET_ID
    assert harness.session["clocks"]["time_pressure"] == 1

    board = _play(harness, TURN_4)
    assert board.processing_result["resolution_kind"] == "discover_clue"
    assert board.processing_result["response"] == NOTICE_TEXT
    assert harness.session["active_scene_id"] == STREET_ID
    runtime = harness.session["scene_runtime"][STREET_ID]
    assert "notice_board" in runtime["resolved_interactables"]

    assert harness.history.ids() == [spec["message_id"] for spec in SEQUENCE]
    assert [item.text for item in harness.history] == [spec["text"] for spec in SEQUENCE]
    assert [item.mode for item in harness.history] == ["IC", "OOC", "IC", "IC", "IC"]
    assert harness.history.messages()[1] is interruption
    assert harness.session["turn_counter"] == 4
    assert harness.character["hp"] == opening_hp
    assert harness.session["inventory"] == []
    assert harness.combat["player_turn_used"] is False
    assert all(item.processing_result.get("rolls_dice") is False for item in harness.history)
    for name, digest in hashes.items():
        assert _sha(ROOT / name) == digest


def test_slice_report_matches_the_played_sequence() -> None:
    report = run_vertical_slice()
    assert report["history_ids"] == ["msg_001", "msg_002", "msg_003", "msg_004", "msg_005"]
    assert report["history_length"] == 5
    assert report["final_scene"] == STREET_ID
    assert report["time_pressure"] == 1
    assert report["turn_counter"] == 4
    assert report["notice_resolved"] is True
    assert report["npc_ids"] == ["sergeant_mara"]
    assert report["combat_action_used"] is False
    assert report["steps"][1]["mutated_state"] is False
    assert report["steps"][1]["resolver_invoked"] is False
    assert report["resolver_calls"] == [
        "game.exploration.resolve_exploration_action",
        "game.social.resolve_social_action",
        "game.exploration.resolve_exploration_action",
        "game.exploration.resolve_exploration_action",
    ]
    assert all(step["rolls_dice"] is False for step in report["steps"])


def test_notice_board_is_blocked_while_the_courtyard_is_active() -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    message = _play(harness, {**TURN_4, "message_id": "msg_early_board"})
    assert message.status == "REJECTED"
    assert message.processing_result["reason"] == "target_not_in_active_scene"
    assert message.processing_result["resolver_invoked"] is False
    assert harness.session["active_scene_id"] == "waystation_courtyard"
    assert authoritative_snapshot(harness) == before
