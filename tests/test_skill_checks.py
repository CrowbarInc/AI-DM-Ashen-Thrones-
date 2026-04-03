"""Tests for deterministic skill check authority layer."""
import pytest
from game.skill_checks import resolve_skill_check, should_trigger_check
from game.defaults import default_character, default_world



pytestmark = pytest.mark.unit

def test_action_that_does_not_require_roll():
    """Action without config or safe context does NOT require a roll."""
    action = {"id": "observe-a", "type": "observe", "label": "Look around"}
    scene = {"scene": {"id": "test", "location": "Here"}}
    ctx = {"engine": "exploration", "action": action, "scene": scene, "session": {}}
    decision = should_trigger_check(action, ctx)
    assert decision["requires_check"] is False
    assert decision["skill"] is None
    assert decision["difficulty"] is None
    assert "no_config" in decision["reason"] or "safe" in decision["reason"]


def test_persuasion_does_require_roll():
    """Persuasion attempt requires a skill check."""
    action = {"id": "persuade-merchant", "type": "persuade", "label": "Persuade the merchant"}
    ctx = {"engine": "social", "action": action, "npc": {"id": "merchant"}, "session": {}}
    decision = should_trigger_check(action, ctx)
    assert decision["requires_check"] is True
    assert decision["skill"] == "diplomacy"
    assert decision["difficulty"] is not None
    assert "persuade" in decision["reason"]


def test_failure_path_no_info_revealed(monkeypatch):
    """Failed check: no info revealed, meaningful but non-blocking."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 1)
    character = default_character()
    character["skills"]["intimidate"] = -5
    ctx = {"seed_parts": ["fail", "gate", "intimidate-guard", "social"]}
    result = resolve_skill_check("intimidate", 10, character, ctx)
    assert result["success"] is False
    assert result["roll"] == 1
    assert result["total"] == -4
    assert result["difficulty"] == 10
    assert result["skill"] == "intimidate"


def test_success_path_info_revealed(monkeypatch):
    """Successful check: info can be revealed (engine branches on this)."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 20)
    character = default_character()
    character["skills"]["diplomacy"] = 4
    ctx = {"seed_parts": ["pass", "market", "persuade-merchant", "social"]}
    result = resolve_skill_check("diplomacy", 10, character, ctx)
    assert result["success"] is True
    assert result["roll"] == 20
    assert result["total"] == 24
    assert result["difficulty"] == 10
    assert result["skill"] == "diplomacy"


def test_deterministic_output_consistency():
    """Same seed_parts always produce same roll and result."""
    character = default_character()
    character["skills"]["perception"] = 3
    ctx = {"seed_parts": [0, "test_scene", "inv-desk", "galinor"]}
    r1 = resolve_skill_check("perception", 12, character, ctx)
    r2 = resolve_skill_check("perception", 12, character, ctx)
    assert r1["roll"] == r2["roll"]
    assert r1["total"] == r2["total"]
    assert r1["success"] == r2["success"]


def test_no_skill_fallback_clean():
    """Missing skill falls back to modifier 0."""
    character = default_character()
    character.pop("skills", None)
    ctx = {"seed_parts": ["test"]}
    result = resolve_skill_check("unknown_skill", 10, character, ctx)
    assert result["modifier"] == 0
    assert "roll" in result
    assert "total" in result
    assert "success" in result


def test_should_trigger_investigate_with_explicit_skill_check():
    """Investigate with interactable that has explicit skill_check config triggers check."""
    action = {"id": "inv-chest", "type": "investigate"}
    interactable = {
        "id": "chest",
        "type": "investigate",
        "reveals_clue": "chest-clue",
        "skill_check": {"skill_id": "perception", "dc": 12},
    }
    ctx = {
        "engine": "exploration",
        "action": action,
        "scene": {"scene": {}},
        "interactable": interactable,
        "session": {},
    }
    decision = should_trigger_check(action, ctx)
    assert decision["requires_check"] is True
    assert decision["skill"] == "perception"
    assert decision["difficulty"] == 12
    assert decision["reason"] == "scene_config"


def test_should_trigger_investigate_without_config_no_check():
    """Investigate with interactable that has reveals_clue but no skill_check does NOT trigger.
    Preserves legacy: auto-success for interactables without explicit config."""
    action = {"id": "inv-desk", "type": "investigate"}
    interactable = {"id": "desk", "type": "investigate", "reveals_clue": "desk-clue"}
    ctx = {
        "engine": "exploration",
        "action": action,
        "scene": {"scene": {}},
        "interactable": interactable,
        "session": {},
    }
    decision = should_trigger_check(action, ctx)
    assert decision["requires_check"] is False
    assert decision["skill"] is None
    assert decision["difficulty"] is None


def test_result_structure():
    """resolve_skill_check returns canonical structure with skill, difficulty, roll, modifier, total, success."""
    character = default_character()
    character["skills"]["perception"] = 2
    ctx = {"seed_parts": ["a", "b"]}
    result = resolve_skill_check("perception", 14, character, ctx)
    assert set(result.keys()) >= {"skill", "difficulty", "dc", "modifier", "roll", "total", "success"}
    assert result["skill"] == "perception"
    assert result["difficulty"] == 14
    assert result["dc"] == 14
    assert result["modifier"] == 2
    assert 1 <= result["roll"] <= 20
    assert result["total"] == result["roll"] + result["modifier"]
    assert result["success"] == (result["total"] >= 14)
