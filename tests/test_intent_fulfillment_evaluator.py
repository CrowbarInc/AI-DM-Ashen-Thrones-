"""Tests for :mod:`game.behavioral_evaluators.intent_fulfillment`."""

from __future__ import annotations

import pytest

from game.behavioral_evaluators.intent_fulfillment import (
    evaluate_intent_fulfillment,
    maybe_attach_intent_fulfillment_eval,
)


def test_question_answered_strongly() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "Where is the inn?",
            "final_output": "The Red Hart is on Mill Street, two blocks north of the square.",
        }
    )
    assert r["score"] == 1.0
    assert r["fulfilled"] is True
    assert r["missed"] is False


def test_question_not_answered_atmospheric() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "Where is the inn?",
            "final_output": (
                "Wind threads the eaves. Distant thunder rolls; moonlight pools in the "
                "mud while shadows stretch along the lane, and silence hangs over the square."
            ),
        }
    )
    assert r["score"] == 0.0
    assert r["missed"] is True
    assert "rule:question_expects_direct_answer" in r["notes"]


def test_action_resolved() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "I try to open the stuck door.",
            "final_output": "The door groans, then gives way with a sharp crack.",
        }
    )
    assert r["score"] == 1.0
    assert r["fulfilled"] is True


def test_action_ignored() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "I attempt to pick the lock on the chest.",
            "final_output": (
                "The chamber is cold. Torchlight trembles on damp stone, and the air "
                "tastes of rust and old rain."
            ),
        }
    )
    assert r["score"] == 0.0
    assert r["missed"] is True
    assert "rule:action_expects_resolution" in r["notes"]


def test_multi_part_partial_coverage() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "Where is the guard post and who commands the watch tonight?",
            "final_output": (
                "The guard post is at the north gate barracks on Watchman's Lane. "
                "Torches gutter along the parapet."
            ),
        }
    )
    assert r["score"] == 0.5
    assert r["partial"] is True
    assert r["fulfilled"] is False
    assert "rule:multi_part_partial" in r["notes"]


def test_multi_part_fulfilled() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_input": "Where is the guard post and who commands the watch tonight?",
            "final_output": (
                "The guard post is at the north gate barracks. Captain Miressa commands "
                "the watch tonight; she posts two sentries at the gate."
            ),
        }
    )
    assert r["score"] == 1.0
    assert r["fulfilled"] is True


def test_turn_packet_field_aliases() -> None:
    r = evaluate_intent_fulfillment(
        {
            "player_text": "What is the tax rate?",
            "player_facing_text": "The answer is twelve percent on trade goods through the river gate.",
            "response_type": "narration",
        }
    )
    assert r["score"] == 1.0
    assert "response_type:" in "".join(r["notes"])


def test_maybe_attach_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    session: dict = {"last_action_debug": {}}
    monkeypatch.delenv("ASGM_RECORD_INTENT_FULFILLMENT_EVAL", raising=False)
    assert maybe_attach_intent_fulfillment_eval(session, player_input="hi", final_output="ho") is None
    assert "intent_fulfillment_eval" not in session["last_action_debug"]

    monkeypatch.setenv("ASGM_RECORD_INTENT_FULFILLMENT_EVAL", "1")
    out = maybe_attach_intent_fulfillment_eval(session, player_input="Where?", final_output="North.")
    assert out is not None
    assert session["last_action_debug"]["intent_fulfillment_eval"] is out
