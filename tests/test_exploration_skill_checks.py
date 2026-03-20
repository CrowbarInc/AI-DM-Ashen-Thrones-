"""Tests for deterministic exploration skill checks."""
from game.exploration import resolve_exploration_action
from game.gm import build_messages
from game.scene_actions import normalize_scene_action
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_world


def test_investigate_with_successful_skill_check(monkeypatch):
    """Investigate with skill_check configured and roll that passes: returns success, discover_clue, skill_check in result."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 20)  # Always pass
    character = default_character()
    character["skills"]["perception"] = 5
    scene = {
        "scene": {
            "id": "test",
            "location": "Here",
            "interactables": [
                {
                    "id": "desk",
                    "type": "investigate",
                    "reveals_clue": "note-clue",
                    "skill_check": {"skill_id": "perception", "dc": 10, "on_failure": {"hint": "You miss it."}},
                }
            ],
            "discoverable_clues": [{"id": "note-clue", "text": "A hidden note under the desk."}],
        }
    }
    action = normalize_scene_action({"id": "inv-desk", "label": "Investigate the desk", "type": "investigate", "prompt": "I investigate the desk"})
    resolution = resolve_exploration_action(scene, {}, default_world(), action, raw_player_text="I investigate the desk", list_scene_ids=lambda: [], character=character)
    assert resolution["kind"] == "discover_clue"
    assert resolution["success"] is True
    assert "skill_check" in resolution
    sc = resolution["skill_check"]
    assert sc["roll"] == 20
    assert sc["total"] >= 10
    assert sc["success"] is True
    assert sc["dc"] == 10
    assert resolution["clue_text"] == "A hidden note under the desk."


def test_investigate_with_failed_skill_check(monkeypatch):
    """Investigate with skill_check: failed roll returns kind=investigate, success=False, no clue."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 1)  # Always fail
    character = default_character()
    character["skills"]["perception"] = 0
    scene = {
        "scene": {
            "id": "test",
            "location": "Here",
            "interactables": [
                {
                    "id": "chest",
                    "type": "investigate",
                    "reveals_clue": "chest-clue",
                    "skill_check": {"skill_id": "perception", "dc": 15},
                }
            ],
            "discoverable_clues": [{"id": "chest-clue", "text": "Trapped mechanism."}],
        }
    }
    action = normalize_scene_action({"id": "inv-chest", "label": "Investigate the chest", "type": "investigate", "prompt": "I investigate the chest"})
    resolution = resolve_exploration_action(scene, {}, default_world(), action, raw_player_text="I investigate the chest", list_scene_ids=lambda: [], character=character)
    assert resolution["kind"] == "investigate"
    assert resolution["success"] is False
    assert "skill_check" in resolution
    assert resolution["skill_check"]["success"] is False
    assert resolution["discovered_clues"] == []
    assert resolution["state_changes"].get("skill_check_failed") is True


def test_observe_with_configured_check_success(monkeypatch):
    """Observe with scene skill_check_defaults: engine rolls and attaches result."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 15)
    character = default_character()
    character["skills"]["perception"] = 4
    scene = {
        "scene": {
            "id": "test",
            "location": "Room",
            "skill_check_defaults": {"observe": {"skill_id": "perception", "dc": 12}},
        }
    }
    action = normalize_scene_action({"id": "observe-area", "label": "Observe", "type": "observe", "prompt": "I look around."})
    resolution = resolve_exploration_action(scene, {}, default_world(), action, list_scene_ids=lambda: [], character=character)
    assert resolution["kind"] == "observe"
    assert resolution["success"] is True
    assert "skill_check" in resolution
    assert resolution["skill_check"]["roll"] == 15
    assert resolution["skill_check"]["total"] == 19
    assert resolution["skill_check"]["dc"] == 12
    assert resolution["skill_check"]["success"] is True


def test_action_without_configured_check_works_normally():
    """Action without skill_check config works as before: no skill_check in result, success=None."""
    scene = {"scene": {"id": "test", "location": "Here"}}
    session = {}
    world = default_world()
    action = normalize_scene_action({"id": "observe-a", "label": "Observe the area", "type": "observe", "prompt": "Look around."})
    resolution = resolve_exploration_action(scene, session, world, action, raw_player_text="Look around.", list_scene_ids=lambda: [])
    assert resolution["kind"] == "observe"
    assert "skill_check" not in resolution or resolution.get("skill_check") is None
    assert resolution.get("success") is None
    assert "hint" in resolution


def test_gpt_payload_includes_skill_check_when_resolved(monkeypatch):
    """build_messages includes skill_check in payload when resolution has it."""
    monkeypatch.setattr("game.skill_checks._deterministic_d20", lambda _: 10)
    character = default_character()
    character["skills"]["perception"] = 2
    scene = {"scene": {"id": "x", "location": "X", "skill_check_defaults": {"investigate": {"skill_id": "perception", "dc": 8}}}}
    action = normalize_scene_action({"id": "inv", "label": "Investigate", "type": "investigate", "prompt": "Search."})
    resolution = resolve_exploration_action(scene, {}, default_world(), action, list_scene_ids=lambda: [], character=character)
    assert "skill_check" in resolution
    campaign, world, session, char, combat, recent_log = default_campaign(), default_world(), {}, character, {"in_combat": False}, []
    messages = build_messages(campaign, world, session, char, scene, combat, recent_log, "Search.", resolution, scene_runtime={})
    import json
    for m in messages:
        if m.get("role") == "user" and "content" in m:
            payload = json.loads(m["content"])
            assert "skill_check" in payload
            assert payload["skill_check"]["roll"] == 10
            assert payload["skill_check"]["total"] == 12
            assert payload["skill_check"]["dc"] == 8
            assert payload["skill_check"]["success"] is True
            # Instruction about not inventing dice
            instructions = " ".join(payload.get("instructions", []))
            assert "skill check" in instructions.lower() or "resolved" in instructions.lower()
            break
