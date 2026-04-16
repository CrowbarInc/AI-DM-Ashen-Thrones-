"""Tests for :mod:`game.behavioral_evaluators.player_agency`."""

from __future__ import annotations

import pytest

from game.behavioral_evaluators.player_agency import (
    evaluate_player_agency,
    maybe_attach_player_agency_eval,
)


def test_neutral_narration_no_violation() -> None:
    r = evaluate_player_agency(
        "The hall is quiet. Torchlight trembles on the banners, and distant footsteps echo "
        "along the colonnade."
    )
    assert r["violation"] is False
    assert r["severity"] == "none"
    assert r["score"] == 1.0
    assert r["instances"] == []


def test_forced_action_high() -> None:
    r = evaluate_player_agency(
        "The blade sings free of the scabbard as you decide to attack the captain before she can speak."
    )
    assert r["violation"] is True
    assert r["severity"] == "high"
    assert r["score"] == 0.0
    assert any("you decide to" in s.lower() for s in r["instances"])


def test_forced_emotion_leading_to_action_medium() -> None:
    r = evaluate_player_agency(
        "Fear crawls up your throat; you feel cornered and you run for the postern gate."
    )
    assert r["violation"] is True
    assert r["severity"] == "medium"
    assert r["score"] == 0.5
    assert r["instances"]


def test_quoted_npc_you_should_no_violation() -> None:
    r = evaluate_player_agency(
        'The merchant shrugs. "You should try the river road," he says, "but mind the toll."'
    )
    assert r["violation"] is False
    assert r["severity"] == "none"
    assert r["score"] == 1.0


def test_suggestion_conditional_no_violation() -> None:
    r = evaluate_player_agency(
        "If you choose to press the matter, the magistrate will hear you in the morning."
    )
    assert r["violation"] is False
    assert r["severity"] == "none"
    assert r["score"] == 1.0


def test_maybe_attach_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    session: dict = {"last_action_debug": {}}
    text = "You choose to surrender your arms without a word."

    monkeypatch.delenv("ASGM_RECORD_PLAYER_AGENCY_EVAL", raising=False)
    maybe_attach_player_agency_eval(session, final_output=text)
    assert "player_agency_eval" not in session["last_action_debug"]

    monkeypatch.setenv("ASGM_RECORD_PLAYER_AGENCY_EVAL", "1")
    maybe_attach_player_agency_eval(session, final_output=text)
    ev = session["last_action_debug"]["player_agency_eval"]
    assert isinstance(ev, dict)
    assert ev["violation"] is True
    assert ev["severity"] == "high"
