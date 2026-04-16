"""Tests for :mod:`game.behavioral_evaluators.session_cohesion`."""

from __future__ import annotations

import pytest

from game.behavioral_evaluators.session_cohesion import (
    evaluate_session_cohesion,
    extract_player_facing_text,
    extract_player_input,
    extract_scene_hint,
    maybe_attach_session_cohesion_eval,
)


def _n(text: str) -> dict:
    return {"player_facing_text": text, "player_input": "look around"}


def test_stable_sequence_strong_cohesion() -> None:
    turns = [
        _n(
            "You are in Coldspire Inn. Captain Mira studies the ledger while you examine the iron key on the table."
        ),
        _n(
            "Captain Mira looks up from the ledger. The iron key still lies where you left it in Coldspire Inn."
        ),
        _n(
            "In Coldspire Inn, Captain Mira slides the iron key toward you without a word."
        ),
        _n(
            "The common room of Coldspire Inn is quiet. Captain Mira waits for your answer about the iron key."
        ),
    ]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] == 0
    assert r["score"] == 1.0
    assert r["cohesive"] is True
    assert r["callback_hits"] >= 1  # "still"
    assert "Coldspire Inn" in " ".join(r["tracked_entities"]["locations"]) or any(
        "Coldspire" in x for x in r["tracked_entities"]["locations"]
    )


def test_abrupt_unexplained_reset_scores_down() -> None:
    turns = [
        _n("You sit in Coldspire Inn. The hearth crackles. Captain Mira pours wine."),
        _n("In Coldspire Inn, Captain Mira asks what you saw on the road."),
        _n(
            "In the Salt Flats, heat shimmers off the cracked earth. There is no inn, no captain, only distance."
        ),
    ]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] >= 1
    assert r["cohesive"] is False


def test_explicit_transition_no_false_failure() -> None:
    turns = [
        _n("You are in Coldspire Inn. Captain Mira closes the shutters."),
        _n("In Coldspire Inn, Captain Mira agrees to ride with you at dawn."),
        _n(
            "The next morning, the road carries you east until you stand in the Salt Flats, empty and white."
        ),
    ]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] == 0
    assert r["score"] == 1.0
    assert r["cohesive"] is True


def test_callback_rich_short_history_rewarded() -> None:
    turns = [
        _n("Earlier you marked the trail. The same guard watches you again."),
        _n("Still uneasy, you recall the same guard from before, still at his post."),
    ]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] == 0
    assert r["callback_hits"] >= 2
    assert r["score"] == 1.0


def test_sparse_history_partial_not_hard_failure() -> None:
    turns = [_n("The hall is quiet and the torches gutter.")]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] == 0
    assert r["score"] == 0.5
    assert r["cohesive"] is False


def test_malformed_and_minimal_dicts_tolerant() -> None:
    r = evaluate_session_cohesion([{}, None, "not-a-mapping", 123])  # type: ignore[list-item]
    assert r["score"] == 0.5
    assert r["memory_failures"] == 0

    r2 = evaluate_session_cohesion([{"debug": "x" * 50}])
    assert r2["score"] == 0.5


def test_extract_helpers() -> None:
    assert extract_player_input({"player_text": "  open door  "}) == "open door"
    assert extract_player_facing_text({"gm": {"player_facing_text": "hello"}}) == "hello"
    assert extract_scene_hint({"scene": {"id": "frontier_gate"}}) == "frontier_gate"


def test_maybe_attach_respects_env_and_requires_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session: dict = {"last_action_debug": {}}
    hist = [
        _n("You stand in Coldspire Inn and take stock of the room, quiet and close."),
        _n("In Coldspire Inn again you hear boots on the stairs, the same rhythm as before."),
    ]

    monkeypatch.delenv("ASGM_RECORD_SESSION_COHESION_EVAL", raising=False)
    assert maybe_attach_session_cohesion_eval(session, turn_history=hist) is None
    assert "session_cohesion_eval" not in session["last_action_debug"]

    monkeypatch.setenv("ASGM_RECORD_SESSION_COHESION_EVAL", "1")
    ev = maybe_attach_session_cohesion_eval(session, turn_history=hist)
    assert isinstance(ev, dict)
    assert session["last_action_debug"]["session_cohesion_eval"] is ev
    assert ev["callback_hits"] >= 1


def test_maybe_attach_optional_session_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    hist = [
        _n("You wait in Coldspire Inn while rain taps the shutters, patient and still."),
        _n("Still in Coldspire Inn, the same draft crawls under the door as before."),
    ]
    session: dict = {"last_action_debug": {}, "session_cohesion_turn_history": hist}
    monkeypatch.setenv("ASGM_RECORD_SESSION_COHESION_EVAL", "1")
    ev = maybe_attach_session_cohesion_eval(session)
    assert ev is not None
    assert ev["callback_hits"] >= 1


def test_multiple_reset_edges_score_zero() -> None:
    """Two disjoint jumps without transitions -> conservative breakdown score."""
    turns = [
        _n("In Coldspire Inn you meet Captain Mira."),
        _n("In Coldspire Inn Captain Mira leaves the room."),
        _n("In the Salt Flats, noon light flares off salt crust until your eyes water."),
        _n("In the Salt Flats you find a dry well, its stones too hot to touch."),
        _n("In Greyvault Warrens, damp air replaces the glare; the salt glare is gone."),
    ]
    r = evaluate_session_cohesion(turns)
    assert r["memory_failures"] >= 2
    assert r["score"] == 0.0
    assert r["cohesive"] is False
