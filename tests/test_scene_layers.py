import json


import pytest

pytestmark = pytest.mark.integration

def test_scene_without_discoverable_clues_loads_with_default(tmp_path, monkeypatch):
    # Import locally so monkeypatch works even if module caches paths.
    from game import storage

    # Redirect storage directories to tmp.
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")

    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)

    # Old schema: no discoverable_clues key.
    scene_id = "legacy_scene"
    raw = {
        "scene": {
            "id": scene_id,
            "location": "Legacy",
            "summary": "Old scene",
            "mode": "exploration",
            "visible_facts": ["A thing you can see."],
            "hidden_facts": ["A secret."],
            "exits": [],
            "enemies": [],
        }
    }
    (storage.SCENES_DIR / f"{scene_id}.json").write_text(json.dumps(raw), encoding="utf-8")

    loaded = storage.load_scene(scene_id)
    assert loaded["scene"]["discoverable_clues"] == []
    assert loaded["scene"]["visible_facts"] == ["A thing you can see."]
    assert loaded["scene"]["hidden_facts"] == ["A secret."]


def test_normalize_scene_draft_does_not_merge_layers():
    from game.gm import normalize_scene_draft

    draft = {
        "id": "x",
        "location": "X",
        "summary": "S",
        "mode": "exploration",
        "visible_facts": ["Visible A"],
        "discoverable_clues": ["Clue A"],
        "hidden_facts": ["Secret A"],
        "exits": [],
        "enemies": [],
    }
    env = normalize_scene_draft(draft)
    assert env["scene"]["visible_facts"] == ["Visible A"]
    assert env["scene"]["discoverable_clues"] == ["Clue A"]
    assert env["scene"]["hidden_facts"] == ["Secret A"]

