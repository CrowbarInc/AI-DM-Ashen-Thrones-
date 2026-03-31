"""Tests for clue knowledge state and inference rules."""
from __future__ import annotations

import pytest

from game.clues import (
    add_clue_to_knowledge,
    apply_authoritative_clue_discovery,
    get_clue_presentation,
    get_all_known_clue_ids,
    get_all_known_clue_texts,
    get_known_clues_with_presentation,
    is_clue_known,
    record_discovered_clue,
    reveal_clue,
    run_inference,
    set_clue_presentation,
)
from game.storage import load_session, save_session, load_world, save_world

pytestmark = pytest.mark.unit


def test_discovered_clues_update_player_knowledge():
    """Discovered clues are added to player knowledge (clue_knowledge + scene_runtime)."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    scene_id = "test_scene"

    reveal_clue(session, scene_id, "clue_a", clue_text="The guard was bribed.")
    assert "clue_a" in get_all_known_clue_ids(session)
    assert "The guard was bribed." in get_all_known_clue_texts(session)
    assert is_clue_known(session, "clue_a")
    assert is_clue_known(session, "The guard was bribed.")
    assert session["clue_knowledge"]["clue_a"]["state"] == "discovered"


def test_inference_rules_require_all_prerequisites():
    """Inferred clues appear only once every required prerequisite is known (two- and three-prereq rules)."""
    session_pair = {"scene_runtime": {}, "clue_knowledge": {}}
    world_pair = {
        "inference_rules": [
            {
                "inferred_clue_id": "conspiracy",
                "requires": ["clue_a", "clue_b"],
                "inferred_clue_text": "A conspiracy links the guard and the noble.",
            }
        ],
        "clues": {},
    }
    add_clue_to_knowledge(session_pair, "clue_a", "discovered", clue_text="Guard took gold.")
    add_clue_to_knowledge(session_pair, "clue_b", "discovered", clue_text="Noble met the guard.")
    newly_pair = run_inference(session_pair, world_pair)
    assert "conspiracy" in newly_pair
    assert "conspiracy" in get_all_known_clue_ids(session_pair)
    assert "A conspiracy links the guard and the noble." in get_all_known_clue_texts(session_pair)
    assert session_pair["clue_knowledge"]["conspiracy"]["state"] == "inferred"

    session = {"scene_runtime": {}, "clue_knowledge": {}}
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "conspiracy",
                "requires": ["clue_a", "clue_b", "clue_c"],
                "inferred_clue_text": "Full picture.",
            }
        ],
    }

    add_clue_to_knowledge(session, "clue_a", "discovered")
    run_inference(session, world)
    assert "conspiracy" not in get_all_known_clue_ids(session)

    add_clue_to_knowledge(session, "clue_b", "discovered")
    run_inference(session, world)
    assert "conspiracy" not in get_all_known_clue_ids(session)

    add_clue_to_knowledge(session, "clue_c", "discovered")
    run_inference(session, world)
    assert "conspiracy" in get_all_known_clue_ids(session)


def test_reveal_clue_duplicate_does_not_reinvoke_inference(monkeypatch):
    """Retrying the same clue does not call run_inference again or duplicate runtime rows."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "deduction",
                "requires": ["first", "second"],
                "inferred_clue_text": "Deduced.",
            }
        ],
    }
    calls: list[int] = []

    def spy(s, w):
        calls.append(1)
        return run_inference(s, w)

    monkeypatch.setattr("game.clues.run_inference", spy)
    reveal_clue(session, "gate", "first", clue_text="First.", world=world)
    reveal_clue(session, "gate", "first", clue_text="First.", world=world)
    assert len(calls) == 1
    assert session["scene_runtime"]["gate"]["discovered_clue_ids"] == ["first"]


def test_record_discovered_clue_returns_structured_status(capsys):
    """record_discovered_clue reports newly_recorded vs duplicate_ignored."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    r1 = record_discovered_clue(session, "s", "c1", clue_text="text")
    assert r1["status"] == "newly_recorded" and r1["clue_id"] == "c1"
    assert r1.get("authoritative_lead_status") == "created"
    assert r1.get("authoritative_lead_id") == "c1"
    out1 = capsys.readouterr().out
    assert "[CLUE DISCOVERED]" in out1
    assert "[CLUE DUPLICATE IGNORED]" not in out1

    r2 = record_discovered_clue(session, "s", "c1", clue_text="text")
    assert r2["status"] == "duplicate_ignored" and r2["clue_id"] == "c1"
    assert r2.get("authoritative_lead_status") == "unchanged"
    out2 = capsys.readouterr().out
    assert "[CLUE DUPLICATE IGNORED] c1" in out2
    assert "[CLUE DISCOVERED]" not in out2


def test_reveal_clue_triggers_inference():
    """reveal_clue runs inference when world is provided."""
    session = {
        "scene_runtime": {"gate": {"discovered_clue_ids": [], "discovered_clues": []}},
        "clue_knowledge": {},
    }
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "deduction",
                "requires": ["first", "second"],
                "inferred_clue_text": "Deduced from first and second.",
            }
        ],
    }

    reveal_clue(session, "gate", "first", clue_text="First clue.", world=world)
    assert "first" in get_all_known_clue_ids(session)
    assert "deduction" not in get_all_known_clue_ids(session)

    reveal_clue(session, "gate", "second", clue_text="Second clue.", world=world)
    assert "second" in get_all_known_clue_ids(session)
    assert "deduction" in get_all_known_clue_ids(session)
    assert "Deduced from first and second." in get_all_known_clue_texts(session)


def test_save_load_preserves_clue_knowledge(tmp_path, monkeypatch):
    """Session save/load preserves clue_knowledge."""
    import game.storage as storage

    monkeypatch.setattr(storage, "SESSION_PATH", tmp_path / "session.json")
    tmp_path.mkdir(parents=True, exist_ok=True)

    session = {
        "active_scene_id": "gate",
        "scene_runtime": {
            "gate": {
                "discovered_clue_ids": ["patrol_route"],
                "discovered_clues": ["A map shows patrol locations."],
            }
        },
        "clue_knowledge": {
            "patrol_route": {"state": "discovered", "text": "A map shows patrol locations.", "source_scene": "gate"},
            "inferred_secret": {"state": "inferred", "text": "The patrol was ambushed.", "source_scene": None},
        },
    }
    storage.save_session(session)
    loaded = storage.load_session()
    assert loaded.get("clue_knowledge") == session["clue_knowledge"]
    assert "patrol_route" in (loaded.get("clue_knowledge") or {})
    assert loaded["clue_knowledge"]["inferred_secret"]["state"] == "inferred"


def test_authoritative_clue_gateway_dedupes_duplicate_writes():
    """Single clue gateway avoids duplicate writes across id/text inputs."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}

    added1 = apply_authoritative_clue_discovery(
        session,
        "gate",
        clue_id="patrol_route",
        clue_text="A map shows patrol locations.",
        discovered_clues=["A map shows patrol locations."],
    )
    assert added1 == ["A map shows patrol locations."]

    added2 = apply_authoritative_clue_discovery(
        session,
        "gate",
        clue_id="patrol_route",
        clue_text="A map shows patrol locations.",
        discovered_clues=["A map shows patrol locations."],
    )
    assert added2 == []

    rt = session["scene_runtime"]["gate"]
    assert rt["discovered_clues"] == ["A map shows patrol locations."]
    assert rt["discovered_clue_ids"] == ["patrol_route"]


def test_inferred_clue_can_remain_implicit_until_promoted():
    """A clue can exist in state while remaining implicit presentation-wise."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "hidden_pattern",
                "requires": ["a", "b"],
                "inferred_clue_text": "The tracks form a deliberate pattern.",
            }
        ],
        "clues": {},
    }
    add_clue_to_knowledge(session, "a", "discovered", clue_text="First piece.")
    add_clue_to_knowledge(session, "b", "discovered", clue_text="Second piece.")

    inferred = run_inference(session, world)
    assert "hidden_pattern" in inferred
    assert "hidden_pattern" in get_all_known_clue_ids(session)
    assert get_clue_presentation(session, clue_id="hidden_pattern") == "implicit"


def test_explicit_clue_can_become_actionable():
    """Presentation can be promoted from explicit to actionable without changing clue ownership."""
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    reveal_clue(session, "gate", "patrol_route", clue_text="A map shows patrol locations.")
    assert get_clue_presentation(session, clue_id="patrol_route") == "explicit"

    promoted = set_clue_presentation(session, clue_id="patrol_route", level="actionable")
    assert promoted is True
    assert get_clue_presentation(session, clue_id="patrol_route") == "actionable"

    clues = get_known_clues_with_presentation(session)
    assert any(c["id"] == "patrol_route" and c["presentation"] == "actionable" for c in clues)
