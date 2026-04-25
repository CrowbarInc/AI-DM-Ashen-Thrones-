"""Snapshot-style schema tests for :mod:`game.ctir` (CTIR foundation)."""

from __future__ import annotations

import copy
import json

import pytest

from game import ctir


def _minimal_ctir() -> dict:
    return ctir.build_ctir(
        turn_id="t-1",
        scene_id="scene_a",
        player_input="look around",
        builder_source="test.builder",
    )


def test_builds_minimal_ctir_with_sane_defaults() -> None:
    c = _minimal_ctir()
    assert c["version"] == ctir.ctir_version()
    assert c["turn_id"] == "t-1"
    assert c["scene_id"] == "scene_a"
    assert c["player_input"] == "look around"
    assert isinstance(c["intent"], dict)
    assert isinstance(c["resolution"], dict)
    assert isinstance(c["state_mutations"], dict)
    assert c["state_mutations"]["scene"] == {}
    assert c["provenance"]["builder_source"] == "test.builder"
    assert ctir.looks_like_ctir(c) is True


def test_omits_prose_like_anchor_fields() -> None:
    c = ctir.build_ctir(
        turn_id=1,
        scene_id=None,
        player_input="hello",
        builder_source="test",
        narrative_anchors={
            "scene_framing": [{"id": "sf1", "narration": "FORBIDDEN", "tone": "tense"}],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    framing = c["narrative_anchors"]["scene_framing"]
    assert framing
    assert "narration" not in framing[0]
    assert framing[0].get("id") == "sf1"
    notes = c["debug"]["normalization_notes"]
    assert any("dropped_prose_like_key" in n for n in notes)


def test_serializes_cleanly() -> None:
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s",
        player_input="act",
        builder_source="test",
        intent={"raw_text": "act", "targets": ["door"]},
        resolution={"kind": "action", "consequences": ["moved"]},
        interaction={"active_target_id": "door", "continuity": {"last_topic": "patrol"}},
        world={"pressure": [{"id": "p1", "delta": 1}]},
    )
    json.dumps(c)


def test_stable_for_repeated_identical_inputs() -> None:
    kwargs = dict(
        turn_id="x",
        scene_id="y",
        player_input="z",
        builder_source="b",
        intent={"raw_text": "z", "mode": "action"},
        state_mutations={
            "scene": {"changed_keys": ["b", "a"], "scene_id": "y"},
            "clues_leads": {"clue_ids": ["c2", "c1"]},
        },
    )
    a = ctir.build_ctir(**kwargs)
    b = ctir.build_ctir(**kwargs)
    assert a == b


def test_does_not_mirror_oversized_or_unknown_state_blobs() -> None:
    huge = {"layer": {str(i): {"k": "v"} for i in range(50)}}
    c = ctir.build_ctir(
        turn_id=0,
        scene_id="here",
        player_input="poke",
        builder_source="test",
        state_mutations={
            "session": {
                "changed_keys": ["gold", "inventory"],
                "rogue_payload": huge,
            },
            "orphan_block": huge,
        },
    )
    sm = c["state_mutations"]
    assert "rogue_payload" not in sm.get("session", {})
    assert "orphan_block" not in sm
    dumped = json.dumps(sm)
    assert len(dumped) < 2000


def test_optional_absent_vs_malformed_required() -> None:
    ok = ctir.build_ctir(
        turn_id=None,
        scene_id=None,
        player_input="",
        builder_source="ok",
        intent=None,
        resolution=None,
    )
    assert ok["intent"]["raw_text"] is None
    assert "intent_input" in ok["debug"]["missing_optional_sections"]
    assert "resolution_input" in ok["debug"]["missing_optional_sections"]

    with pytest.raises(TypeError):
        ctir.build_ctir(
            turn_id=1,
            scene_id="s",
            player_input=123,  # type: ignore[arg-type]
            builder_source="x",
        )
    with pytest.raises(ValueError):
        ctir.build_ctir(
            turn_id=1,
            scene_id="s",
            player_input="x",
            builder_source="   ",
        )


def test_normalize_intent_drops_prose_bearing_top_level_keys_and_slenders_check_request() -> None:
    ni = ctir.normalize_intent(
        {
            "raw_text": "Search the desk",
            "labels": ["investigate"],
            "player_prompt": "Describe what they find.",
            "prompt": "GM hint",
            "hint": "More hint",
            "check_request": {
                "requires_check": True,
                "check_type": "skill",
                "skill": "perception",
                "player_prompt": "Roll perception",
                "difficulty": 12,
            },
        }
    )
    assert "player_prompt" not in ni
    assert "prompt" not in ni
    assert "hint" not in ni
    cr = ni.get("check_request")
    assert isinstance(cr, dict)
    assert "player_prompt" not in cr
    assert cr.get("skill") == "perception"


def test_accessors_are_deterministic() -> None:
    c = _minimal_ctir()
    assert ctir.get_ctir_section(c, "intent", default=None)["mode"] is None
    assert ctir.get_ctir_section(c, "nope", default=1) == 1
    assert ctir.get_ctir_field(c, "provenance.builder_source") == "test.builder"
    assert ctir.get_ctir_field(c, "intent.missing", default="d") == "d"


def test_looks_like_ctir_rejects_wrong_shape() -> None:
    assert ctir.looks_like_ctir({}) is False
    assert ctir.looks_like_ctir({"version": ctir.ctir_version()}) is False
    bad = copy.deepcopy(_minimal_ctir())
    bad["provenance"] = {}
    assert ctir.looks_like_ctir(bad) is False
