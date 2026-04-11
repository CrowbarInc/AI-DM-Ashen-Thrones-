"""Regressions: human-adjacent listen / approach+listen focus vs physical inspection."""
import pytest

from game.diegetic_fallback_narration import render_observe_perception_fallback_line
from game.exploration import resolve_exploration_action
from game.human_adjacent_focus import classify_human_adjacent_intent_family, is_physical_clue_inspection_intent
from game.intent_parser import parse_freeform_to_action

pytestmark = pytest.mark.unit


def _env(inner: dict) -> dict:
    return {"scene": inner}


def test_eavesdrop_on_refugees_maps_observe_and_speaking_group_metadata():
    inner = {
        "id": "gate",
        "exits": [],
        "visible_facts": [
            "A muddy patch is strewn with crates, providing cover.",
            "A huddled group of refugees nearby murmurs about the missing patrol, their expressions grave.",
        ],
    }
    parsed = parse_freeform_to_action("I eavesdrop on the refugees", _env(inner))
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert (parsed.get("metadata") or {}).get("human_adjacent_intent_family") == "listen"

    res = resolve_exploration_action(
        _env(inner),
        {},
        {},
        parsed,
        raw_player_text="I eavesdrop on the refugees",
        list_scene_ids=lambda: [],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    md = res.get("metadata") or {}
    assert md.get("implicit_focus_resolution") == "speaking_group"
    assert md.get("human_adjacent_intent_family") == "listen"
    assert "refugee" in (md.get("implicit_focus_anchor_fact") or "").lower()
    assert "ENGINE FOCUS" in (res.get("hint") or "")


def test_move_closer_gossip_group_listen_in_metadata():
    inner = {
        "id": "square",
        "exits": [],
        "visible_facts": [
            "Two alleyways lead away from the square.",
            "A gossiping cluster of patrons trades rumors near the tavern door, voices rising and falling together.",
        ],
    }
    text = "I move closer to the gossiping group and listen in"
    parsed = parse_freeform_to_action(text, _env(inner))
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert (parsed.get("metadata") or {}).get("human_adjacent_intent_family") == "approach_listen"

    res = resolve_exploration_action(
        _env(inner),
        {},
        {},
        parsed,
        raw_player_text=text,
        list_scene_ids=lambda: [],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    md = res.get("metadata") or {}
    assert md.get("implicit_focus_resolution") == "speaking_group"
    assert "patron" in (md.get("implicit_focus_anchor_fact") or "").lower() or "gossip" in (
        md.get("implicit_focus_anchor_fact") or ""
    ).lower()


def test_inspect_footprints_near_crates_skips_human_adjacent_bridge():
    text = "I inspect the footprints near the crates"
    assert is_physical_clue_inspection_intent(text) is True
    assert classify_human_adjacent_intent_family(text) == "none"

    inner = {
        "id": "yard",
        "exits": [],
        "visible_facts": [
            "A huddled group of refugees nearby murmurs urgently.",
            "The muddy ground bears faint footprints leading toward stacked crates.",
        ],
    }
    parsed = parse_freeform_to_action(text, _env(inner))
    assert parsed is not None
    assert parsed.get("type") == "investigate"

    res = resolve_exploration_action(
        _env(inner),
        {},
        {},
        parsed,
        raw_player_text=text,
        list_scene_ids=lambda: [],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    md = res.get("metadata") or {}
    assert md.get("human_adjacent_intent_family") in (None, "none")
    assert md.get("implicit_focus_resolution") in (None, "none")


def test_listen_diegetic_null_without_human_focus_facts():
    inner = {
        "id": "quiet",
        "exits": [],
        "visible_facts": [
            "Rain drums on broken slate.",
            "Mud sucks at the cobbles.",
        ],
    }
    text = "I eavesdrop on the refugees"
    parsed = parse_freeform_to_action(text, _env(inner))
    res = resolve_exploration_action(
        _env(inner),
        {},
        {},
        parsed,
        raw_player_text=text,
        list_scene_ids=lambda: [],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    md = res.get("metadata") or {}
    assert md.get("implicit_focus_resolution") == "none"
    assert md.get("human_adjacent_diegetic_null") is True

    line = render_observe_perception_fallback_line(
        _env(inner),
        seed_key="unit|ha-null",
        player_text=text,
        resolution=res,
    )
    assert line is not None
    assert "crowd" in line.lower() or "noise" in line.lower() or "voices" in line.lower()
