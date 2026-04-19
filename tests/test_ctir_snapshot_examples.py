"""Small representative CTIR shapes: bounded, serializable, no prose authority drift."""

from __future__ import annotations

import json

import pytest

from game.ctir import build_ctir
from game.ctir_runtime import build_runtime_ctir_for_narration

pytestmark = pytest.mark.unit

def _assert_stable_json(obj: object) -> None:
    json.dumps(obj, sort_keys=True)


def test_example_social_turn_minimal() -> None:
    c = build_ctir(
        turn_id=2,
        scene_id="hall",
        player_input="I ask the guard about the cellar.",
        builder_source="tests.snapshot.social",
        intent={"raw_text": "I ask the guard about the cellar.", "labels": ["social"], "mode": "social"},
        resolution={
            "kind": "question",
            "label": "ask",
            "action_id": "social_q",
            "social": {"npc_reply_expected": True, "reply_kind": "answer"},
        },
        interaction={"interaction_mode": "social", "interaction_kind": "question", "active_target_id": "npc_guard"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _assert_stable_json(c)
    assert c["resolution"]["kind"] == "question"
    assert c["interaction"].get("interaction_kind") == "question"
    soc = c["resolution"].get("social")
    assert isinstance(soc, dict) and soc.get("reply_kind") == "answer"


def test_example_exploration_discovery() -> None:
    c = build_runtime_ctir_for_narration(
        turn_id=4,
        scene_id="ruins",
        player_input="Search the rubble.",
        builder_source="tests.snapshot.discovery",
        resolution={
            "kind": "observe",
            "success": True,
            "state_changes": {"clue_surface": True},
            "clue_id": "clue_rubble",
        },
        normalized_action={"type": "observe", "labels": ["investigation"]},
        combat=None,
        session={"active_scene_id": "ruins", "interaction_context": {}},
    )
    _assert_stable_json(c)
    assert c["intent"].get("labels") == ["investigation"]
    auth = c["resolution"].get("authoritative_outputs")
    assert isinstance(auth, dict) and auth.get("clue_id") == "clue_rubble"


def test_example_scene_transition() -> None:
    c = build_runtime_ctir_for_narration(
        turn_id=5,
        scene_id="road",
        player_input="I enter the inn.",
        builder_source="tests.snapshot.transition",
        resolution={
            "kind": "scene_transition",
            "resolved_transition": True,
            "target_scene_id": "inn",
            "state_changes": {"scene_transition_occurred": True, "arrived_at_scene": True},
        },
        normalized_action={"type": "travel"},
        combat=None,
        session={"active_scene_id": "inn", "interaction_context": {}},
    )
    _assert_stable_json(c)
    sc = c["resolution"].get("state_changes")
    assert isinstance(sc, dict)
    assert sc.get("scene_transition_occurred") is True


def test_example_combat_mechanical() -> None:
    c = build_runtime_ctir_for_narration(
        turn_id=6,
        scene_id="arena",
        player_input="I attack the goblin.",
        builder_source="tests.snapshot.combat",
        resolution={"kind": "attack", "success": True, "outcome_type": "hit"},
        normalized_action={"type": "attack"},
        combat={"in_combat": True, "round": 2, "phase": "player"},
        session={"active_scene_id": "arena", "interaction_context": {}},
    )
    _assert_stable_json(c)
    assert c["state_mutations"]["combat"].get("combat_active") is True
    assert c["resolution"].get("outcome_type") == "hit"


def test_examples_avoid_prose_like_payload_roots() -> None:
    c = build_ctir(
        turn_id=0,
        scene_id="z",
        player_input="ping",
        builder_source="tests.snapshot.prose_guard",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    blob = json.dumps(c, sort_keys=True).lower()
    assert "player_facing_text" not in blob
    assert "system_prompt" not in blob
