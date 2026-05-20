"""Thin transcript harness: clean campaign + chat turns + per-turn snapshots.

Uses stable internal entrypoints (``apply_new_campaign_hard_reset``, ``chat``) - no TestClient.
Snapshot-only helpers live in ``tests.helpers.transcript_snapshots`` so evaluator tests can
collect without importing the live API/GPT stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from game import storage
from game.api import chat
from game.campaign_reset import apply_new_campaign_hard_reset
from game.defaults import default_scene
from game.models import ChatRequest
from tests.helpers.transcript_snapshots import (
    compact_snapshot_summary,
    format_turn_debug,
    latest_target_id,
    latest_target_source,
    snapshot_from_chat_payload,
)


def patch_transcript_storage(monkeypatch: Any, tmp_path: Path) -> None:
    """Point ``game.storage`` paths at *tmp_path* (same pattern as ``test_campaign_reset``)."""
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
    monkeypatch.setattr(storage, "SNAPSHOTS_DIR", storage.DATA_DIR / "snapshots")
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def write_default_bootstrap_scenes(
    scene_ids: tuple[str, ...] = ("frontier_gate", "market_quarter")
) -> None:
    """Ensure on-disk scene templates exist (matches ``ensure_data_files_exist`` seed set)."""
    for sid in scene_ids:
        path = storage.scene_path(sid)
        if not path.exists():
            storage._save_json(path, default_scene(sid))


def new_clean_campaign(*, starting_scene_id: str | None = None) -> dict[str, Any]:
    """Hard reset runtime; optionally pin active scene if the id is known on disk."""
    meta = apply_new_campaign_hard_reset()
    if starting_scene_id:
        sid = str(starting_scene_id).strip()
        if sid and storage.is_known_scene_id(sid):
            storage.activate_scene(sid)
    return meta


def run_transcript_turns(
    turns: list[str],
    *,
    starting_scene_id: str | None = None,
    chat_fn: Callable[[ChatRequest], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """After ``new_clean_campaign`` (and storage patch + scene seed), run chat strings and collect snapshots."""
    fn = chat_fn or chat
    snapshots: list[dict[str, Any]] = []
    new_clean_campaign(starting_scene_id=starting_scene_id)
    for i, text in enumerate(turns):
        payload = fn(ChatRequest(text=text))
        if not isinstance(payload, dict):
            raise TypeError("chat_fn must return a dict payload")
        snapshots.append(snapshot_from_chat_payload(i, text, payload))
    return snapshots


def run_transcript(
    tmp_path: Path,
    monkeypatch: Any,
    turns: list[str],
    *,
    starting_scene_id: str | None = None,
    extra_scene_ids: tuple[str, ...] = (),
    chat_fn: Callable[[ChatRequest], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Patch storage, seed default scenes (+ optional extras), new campaign, run *turns*."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    for sid in extra_scene_ids:
        path = storage.scene_path(sid)
        if not path.exists():
            storage._save_json(path, default_scene(sid))
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return run_transcript_turns(turns, starting_scene_id=starting_scene_id, chat_fn=chat_fn)
