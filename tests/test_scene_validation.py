"""Tests for scene validation: fail-fast on broken references and missing fields."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from game.validation import SceneValidationError, validate_all_scenes, validate_scene
from game.validation import SceneValidationError, validate_all_scenes, validate_scene



pytestmark = pytest.mark.unit

def _minimal_valid_scene(scene_id: str = "test_scene") -> dict:
    """Build a minimal valid scene envelope."""
    return {
        "scene": {
            "id": scene_id,
            "location": "Test Location",
            "summary": "A test summary.",
            "mode": "exploration",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
            "actions": [],
            "interactables": [],
        }
    }


def test_valid_scene_passes():
    """Valid scenes pass validation."""
    scene = _minimal_valid_scene("valid_scene")
    known = {"valid_scene", "other_scene"}
    validate_scene(scene, "valid_scene", known)


def test_missing_target_scene():
    """Exit with missing target_scene_id raises."""
    scene = _minimal_valid_scene("frontier")
    scene["scene"]["exits"] = [
        {"label": "Go to nowhere", "target_scene_id": "crossroads_north"},
    ]
    known = {"frontier"}  # crossroads_north not in known

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "frontier", known)
    assert "points to missing target_scene_id 'crossroads_north'" in str(exc_info.value)
    assert exc_info.value.scene_id == "frontier"
    assert "target_scene_id" in exc_info.value.field


def test_valid_exit_target_passes():
    """Exits with valid target_scene_id pass."""
    scene = _minimal_valid_scene("gate")
    scene["scene"]["exits"] = [
        {"label": "Enter", "target_scene_id": "market"},
    ]
    known = {"gate", "market"}
    validate_scene(scene, "gate", known)


def test_duplicate_affordance_ids():
    """Duplicate affordance action ids raise."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["actions"] = [
        {"id": "same_id", "label": "Action A", "type": "custom", "prompt": "Do A"},
        {"id": "same_id", "label": "Action B", "type": "custom", "prompt": "Do B"},
    ]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "duplicate affordance action id 'same_id'" in str(exc_info.value)


def test_duplicate_interactable_ids():
    """Duplicate interactable ids raise."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate"},
        {"id": "desk", "type": "investigate"},
    ]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "duplicate interactable id 'desk'" in str(exc_info.value)


def test_missing_required_location():
    """Missing location raises."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["location"] = ""

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "missing required field 'location'" in str(exc_info.value)


def test_missing_required_summary():
    """Missing summary raises."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["summary"] = None

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "missing required field 'summary'" in str(exc_info.value)


def test_missing_scene_id():
    """Missing scene id raises."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["id"] = ""

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "Scene id is missing or empty" in str(exc_info.value)


def test_scene_id_mismatch():
    """Scene id not matching file scene_id raises."""
    scene = _minimal_valid_scene("wrong_id")

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "actual_file_stem", {"actual_file_stem"})
    assert "does not match file scene_id" in str(exc_info.value)


def test_interactable_missing_id():
    """Interactable without id raises."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["interactables"] = [{"type": "investigate"}]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "missing required field 'id'" in str(exc_info.value)


def test_action_target_scene_missing():
    """Action with targetSceneId pointing to unknown scene raises."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["actions"] = [
        {"id": "travel_action", "label": "Go", "type": "scene_transition", "targetSceneId": "unknown_place"},
    ]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "points to missing targetSceneId 'unknown_place'" in str(exc_info.value)


def test_interactable_reveals_clue_invalid():
    """Interactable with reveals_clue not in discoverable_clues raises when clues exist."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["discoverable_clues"] = ["A visible clue about the patrol."]
    scene["scene"]["interactables"] = [
        {"id": "map", "type": "investigate", "reveals_clue": "nonexistent_clue_id"},
    ]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene, "room", {"room"})
    assert "references unknown clue" in str(exc_info.value)


def test_interactable_reveals_clue_valid():
    """Interactable with reveals_clue matching discoverable_clues passes."""
    scene = _minimal_valid_scene("room")
    scene["scene"]["discoverable_clues"] = ["A map indicates the patrol route."]
    scene["scene"]["interactables"] = [
        {"id": "map", "type": "investigate", "reveals_clue": "a-map-indicates-the-patrol-route"},
    ]

    validate_scene(scene, "room", {"room"})


def test_validate_all_scenes_valid(tmp_path):
    """validate_all_scenes passes when all scenes are valid."""
    scene = _minimal_valid_scene("valid")
    (tmp_path / "valid.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")

    def list_ids():
        return [p.stem for p in tmp_path.glob("*.json")]

    validate_all_scenes(tmp_path, list_ids)


def test_validate_all_scenes_missing_target(tmp_path):
    """validate_all_scenes raises when a scene has broken exit."""
    scene = _minimal_valid_scene("broken")
    scene["scene"]["exits"] = [{"label": "Go", "target_scene_id": "nonexistent"}]
    (tmp_path / "broken.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")

    def list_ids():
        return ["broken"]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_all_scenes(tmp_path, list_ids)
    assert "points to missing target_scene_id 'nonexistent'" in str(exc_info.value)


def test_validate_all_scenes_empty_file(tmp_path):
    """validate_all_scenes raises on empty scene file."""
    (tmp_path / "empty.json").write_text("", encoding="utf-8")

    def list_ids():
        return ["empty"]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_all_scenes(tmp_path, list_ids)
    assert "empty" in str(exc_info.value).lower()


def test_validate_all_scenes_invalid_json(tmp_path):
    """validate_all_scenes raises on invalid JSON."""
    (tmp_path / "bad.json").write_text("{ invalid }", encoding="utf-8")

    def list_ids():
        return ["bad"]

    with pytest.raises(SceneValidationError) as exc_info:
        validate_all_scenes(tmp_path, list_ids)
    assert "JSON" in str(exc_info.value)
