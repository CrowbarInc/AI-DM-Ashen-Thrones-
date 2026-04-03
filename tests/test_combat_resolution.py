"""Tests for combat canonical engine result and resolution pipeline."""
from game import storage
from game.api import app
from game.combat import (
    roll_initiative,
    resolve_attack,
    resolve_skill,
    resolve_spell,
    build_end_turn_result,
    enemy_take_turn,
)
from game.defaults import (
    default_scene,
    default_session,
    default_world,
    default_character,
    default_campaign,
    default_combat,
    default_conditions,
)
from fastapi.testclient import TestClient

# Canonical engine result top-level keys (same contract as exploration)
COMBAT_CANONICAL_TOP_KEYS = frozenset({
    "kind", "action_id", "label", "prompt", "success", "resolved_transition",
    "target_scene_id", "clue_id", "discovered_clues", "world_updates", "state_changes", "hint",
    "combat",
})


import pytest

pytestmark = pytest.mark.integration

def _assert_canonical_combat_result(resolution: dict, expected_kind: str) -> None:
    """Assert combat resolution conforms to the standardized engine result schema."""
    assert isinstance(resolution, dict), "resolution must be a dict"
    for key in COMBAT_CANONICAL_TOP_KEYS:
        assert key in resolution, f"resolution must have '{key}'"
    assert resolution["kind"] == expected_kind
    assert resolution["resolved_transition"] is False
    assert resolution["target_scene_id"] is None
    assert resolution["clue_id"] is None
    assert resolution["discovered_clues"] == []
    assert resolution["world_updates"] is None
    assert isinstance(resolution["combat"], dict), "combat sub-payload must be present"
    combat = resolution["combat"]
    assert "combat_phase" in combat
    assert "actor" in combat or combat.get("actor") is None
    assert "turn_advanced" in combat or combat.get("turn_advanced") is not None
    assert "combat_ended" in combat or combat.get("combat_ended") is not None


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _scene_with_goblin():
    """Scene with one goblin enemy for combat tests."""
    scene = default_scene("frontier_gate")
    scene["scene"]["enemies"] = [
        {
            "id": "goblin_1",
            "name": "Goblin",
            "hp": {"current": 6, "max": 6},
            "initiative_bonus": 2,
            "creature_type": "humanoid",
            "hd": 1,
            "saves": {"will": 0},
            "attacks": [
                {
                    "id": "dagger",
                    "name": "Dagger",
                    "attack_bonus": 1,
                    "damage": {"dice_count": 1, "dice_sides": 4, "bonus": 0, "type": "piercing"},
                }
            ],
        }
    ]
    return scene


def test_roll_initiative_returns_canonical_engine_result(tmp_path, monkeypatch):
    """roll_initiative returns the canonical engine result shape with combat sub-payload."""
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _scene_with_goblin())
    storage._save_json(storage.SESSION_PATH, default_session())
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    character = default_character()
    scene = storage._load_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    combat = default_combat()
    conditions = default_conditions()
    scene["scene"]["enemies"] = _scene_with_goblin()["scene"]["enemies"]

    resolution = roll_initiative(character, scene, combat, conditions)
    _assert_canonical_combat_result(resolution, "initiative")
    assert resolution["combat"]["round"] == 1
    assert resolution["combat"]["order"]
    assert resolution["combat"]["active_actor_id"] in [c["id"] for c in resolution["combat"]["order"]]
    assert "order" in resolution  # backward compat top-level


def test_resolve_attack_returns_canonical_engine_result(tmp_path, monkeypatch):
    """resolve_attack returns the canonical engine result with hit/damage in combat payload."""
    _patch_storage(tmp_path, monkeypatch)
    character = default_character()
    scene = {"scene": _scene_with_goblin()["scene"]}
    combat = {"in_combat": True, "round": 1, "initiative_order": [], "turn_index": 0, "active_actor_id": "galinor", "player_turn_used": False}
    conditions = default_conditions()

    resolution = resolve_attack(
        character, scene, "quarterstaff", "goblin_1", [], conditions
    )
    _assert_canonical_combat_result(resolution, "attack")
    assert "hit" in resolution  # backward compat
    assert resolution["combat"]["combat_phase"] == "attack"
    assert resolution["combat"]["actor"]["id"] == "galinor"
    assert resolution["combat"]["target"]["id"] == "goblin_1"
    assert "rolls" in resolution["combat"]
    assert "damage_dealt" in resolution["combat"]
    assert "damage" in resolution  # backward compat when hit


def test_build_end_turn_result_returns_canonical_engine_result():
    """build_end_turn_result returns the canonical engine result for end_turn."""
    combat = {"round": 2, "active_actor_id": "galinor", "in_combat": True}
    resolution = build_end_turn_result(combat)
    _assert_canonical_combat_result(resolution, "end_turn")
    assert resolution["combat"]["combat_phase"] == "end_turn"
    assert resolution["combat"]["turn_advanced"] is True
    assert resolution["combat"]["round"] == 2


def test_api_roll_initiative_returns_canonical_resolution(tmp_path, monkeypatch):
    """POST /api/action roll_initiative returns resolution with canonical shape."""
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _scene_with_goblin())
    storage._save_json(storage.SESSION_PATH, default_session())
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    client = TestClient(app)
    r = client.post("/api/action", json={"action_type": "roll_initiative"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    resolution = data.get("resolution")
    assert resolution is not None
    _assert_canonical_combat_result(resolution, "initiative")


def test_resolve_skill_returns_canonical_engine_result():
    """resolve_skill (combat skill check) returns canonical engine result."""
    character = default_character()
    resolution = resolve_skill(character, "perception", "Search for hidden enemies")
    _assert_canonical_combat_result(resolution, "skill_check")
    assert resolution["combat"]["combat_phase"] == "skill_check"
    assert "rolls" in resolution["combat"]


def test_resolve_spell_magic_missile_returns_canonical_engine_result(tmp_path, monkeypatch):
    """resolve_spell (magic missile) returns canonical engine result."""
    _patch_storage(tmp_path, monkeypatch)
    character = default_character()
    scene = {"scene": _scene_with_goblin()["scene"]}
    conditions = default_conditions()

    resolution = resolve_spell(character, scene, "magic_missile", "goblin_1", conditions)
    _assert_canonical_combat_result(resolution, "spell")
    assert resolution["combat"]["combat_phase"] == "spell"
    assert resolution["combat"]["damage_dealt"] >= 0
    assert resolution["success"] is True
