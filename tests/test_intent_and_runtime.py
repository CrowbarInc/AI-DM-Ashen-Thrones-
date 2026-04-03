from game.gm import classify_player_intent
from game.storage import (
    get_scene_runtime,
    mark_clue_discovered,
    mark_hidden_fact_revealed,
    add_suspicion_flag,
)


import pytest

pytestmark = pytest.mark.unit

def test_intent_classification_examples():
    info = classify_player_intent("I search the wagon carefully.")
    assert "investigation" in info["labels"]
    assert info["allow_discoverable_clues"] is True

    info = classify_player_intent("I question the guard about the caravans.")
    assert "social_probe" in info["labels"]
    assert info["allow_discoverable_clues"] is True

    info = classify_player_intent("I walk north to the market.")
    assert info["allow_discoverable_clues"] is False


def test_scene_runtime_initialization_and_dedup():
    session = {}
    rt = get_scene_runtime(session, "scene1")
    assert rt["discovered_clues"] == []
    assert rt["revealed_hidden_facts"] == []
    assert rt["suspicion_flags"] == []

    assert mark_clue_discovered(session, "scene1", "clue A") is True
    assert mark_clue_discovered(session, "scene1", "clue A") is False
    assert rt["discovered_clues"] == ["clue A"]

    assert mark_hidden_fact_revealed(session, "scene1", "secret X") is True
    assert mark_hidden_fact_revealed(session, "scene1", "secret X") is False
    assert rt["revealed_hidden_facts"] == ["secret X"]

    assert add_suspicion_flag(session, "scene1", "shifty_guard") is True
    assert add_suspicion_flag(session, "scene1", "shifty_guard") is False
    assert rt["suspicion_flags"] == ["shifty_guard"]

