"""Reusable HTTP turn-pipeline fixtures and seed helpers.

These helpers are test setup only. They intentionally avoid assertions and keep
seed contents stable for suites that exercise the shared ``/api/chat`` and
``/api/action`` pipeline.

Import HTTP seeds and GPT stubs from this module — not from
``tests/test_turn_pipeline_shared.py`` (Cycle AL1 / BA-8).
"""
from __future__ import annotations

from typing import Any, Mapping

from game import storage
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from tests.helpers.gate_orchestration_smoke import gm_response_stub as _gm_response

FAKE_GPT_RESPONSE = {
    "player_facing_text": "[Narration]",
    "tags": [],
    "scene_update": None,
    "activate_scene_id": None,
    "new_scene_draft": None,
    "world_updates": None,
    "suggested_action": None,
    "debug_notes": "",
}

CAMPAIGN_START_SCENE_IDS: tuple[str, ...] = ("frontier_gate", "market_quarter", "old_milestone")


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


def _seed_shared_world(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)

    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = (
        "Lamplight pools over clutter: ink-stained maps, a ledger half-shut, and the damp smell of rain through the shutters."
    )
    scene["scene"]["visible_facts"] = [
        "Filing shelves crowd one wall; loose papers curl at the edges.",
        "A brass compass sits beside a blot of spilled ink on the desk.",
        "Rain taps at shutter slats while distant bells mark the ward.",
    ]
    scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate", "reveals_clue": "desk_clue"},
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "desk_clue", "text": "A map indicates patrol locations."},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _seed_runner_dialogue_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "They were seen near the east lanes.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage.save_session(session)


def _write_campaign_start_scene_files(
    *,
    frontier_gate_overrides: Mapping[str, Any] | None = None,
) -> None:
    """Write default campaign-start scene envelopes under the patched storage tree."""
    for sid in CAMPAIGN_START_SCENE_IDS:
        scene = default_scene(sid)
        if sid == "frontier_gate" and frontier_gate_overrides:
            scene["scene"].update(dict(frontier_gate_overrides))
        storage._save_json(storage.scene_path(sid), scene)


def _seed_campaign_start_storage(
    tmp_path,
    monkeypatch,
    *,
    frontier_gate_overrides: Mapping[str, Any] | None = None,
) -> None:
    """Patch storage to ``tmp_path`` and seed campaign-start scene files."""
    _patch_storage(tmp_path, monkeypatch)
    _write_campaign_start_scene_files(frontier_gate_overrides=frontier_gate_overrides)
