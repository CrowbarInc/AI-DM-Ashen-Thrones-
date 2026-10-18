"""Production-save write guard and provider-call tripwire for PR-DG."""
from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

from game.storage import (
    CAMPAIGN_PATH,
    CHARACTER_PATH,
    COMBAT_PATH,
    CONDITIONS_PATH,
    DATA_DIR,
    SESSION_LOG_PATH,
    SESSION_PATH,
    WORLD_PATH,
    _atomic_write_bytes,
    _save_json,
    append_log,
)

WATCHED = (
    SESSION_PATH,
    WORLD_PATH,
    COMBAT_PATH,
    SESSION_LOG_PATH,
    CHARACTER_PATH,
    CAMPAIGN_PATH,
    CONDITIONS_PATH,
)


class IsolationError(RuntimeError):
    """Raised when a production save or a provider call cannot be prevented."""


def _fingerprint() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for path in WATCHED:
        if path.exists():
            data = path.read_bytes()
            out[path.name] = {
                "mtime_ns": path.stat().st_mtime_ns,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        else:
            out[path.name] = {"mtime_ns": None, "sha256": None, "size": None}
    return out


def _protected(path: Path) -> bool:
    try:
        path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        return False
    return True


class ProductionSaveGuard:
    """Block every write under data/ and prove the watched saves did not change."""

    def __init__(self) -> None:
        self.attempts: list[dict[str, str]] = []
        self.memory_sink: dict[str, bytes] = {}
        self._fingerprint_before: dict[str, dict[str, object]] = {}
        self._patches: list = []
        self.verified = False

    def _remember(self, path: Path, content: bytes) -> None:
        key = str(path)
        self.attempts.append({"path": key, "bytes": str(len(content))})
        self.memory_sink[key] = content

    def _blocked_bytes(self, path: Path, content: bytes) -> None:
        if _protected(path):
            self._remember(path, content)
            return
        _atomic_write_bytes(path, content)

    def _blocked_json(self, path: Path, data: dict) -> None:
        if _protected(path):
            import json

            self._remember(path, json.dumps(data).encode("utf-8"))
            return
        _save_json(path, data)

    def _blocked_log(self, entry: dict) -> None:
        import json

        payload = (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")
        self._remember(SESSION_LOG_PATH, payload)

    def __enter__(self) -> "ProductionSaveGuard":
        self._fingerprint_before = _fingerprint()
        import game.storage as storage

        self._patches = [
            patch.object(storage, "_atomic_write_bytes", self._blocked_bytes),
            patch.object(storage, "_save_json", self._blocked_json),
            patch.object(storage, "append_log", self._blocked_log),
        ]
        for item in self._patches:
            item.start()
        self._probe()
        self.verified = True
        return self

    def _probe(self) -> None:
        import game.storage as storage

        before = _fingerprint()
        storage.save_session({"pr_dg_probe": "must-not-touch-disk"})
        storage.save_world({"pr_dg_probe": True, "npcs": []})
        storage.append_log({"pr_dg_probe": True})
        after = _fingerprint()
        if before != after:
            self._stop_patches()
            raise IsolationError("production save changed during the write-guard probe")
        if len(self.attempts) < 3:
            self._stop_patches()
            raise IsolationError("write-guard probe did not intercept session, world, and log writes")
        self.attempts.clear()
        self.memory_sink.clear()

    def _stop_patches(self) -> None:
        for item in reversed(self._patches):
            item.stop()
        self._patches.clear()

    def assert_unchanged(self) -> None:
        after = _fingerprint()
        if after != self._fingerprint_before:
            raise IsolationError(f"production save fingerprint changed: {after}")

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self.verified:
                self.assert_unchanged()
        finally:
            self._stop_patches()


@contextmanager
def forbid_provider_calls() -> Iterator[list[str]]:
    """Any narration or interpretation model call aborts the experiment."""
    import game.gm as gm
    import game.semantic_interpreter as interpreter

    hits: list[str] = []

    def _blocked(name: str):
        def _inner(*_args, **_kwargs):
            hits.append(name)
            raise IsolationError(f"provider call attempted: {name}")

        return _inner

    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    with patch.object(gm, "call_gpt", _blocked("game.gm.call_gpt")), patch.object(
        interpreter, "_invoke_interpretation_model", _blocked("semantic_interpreter._invoke_interpretation_model")
    ):
        yield hits
