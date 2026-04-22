"""Deterministic fake-GM helpers for synthetic harness plumbing.

This module is test-only and intentionally avoids production imports.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any


def _latest_text_from_messages(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            continue
        if isinstance(message, str) and message.strip():
            return message.strip()
    return ""


def extract_latest_player_text(*args: Any, **kwargs: Any) -> str:
    """Best-effort extraction of latest player text from common call shapes."""
    for key in ("latest_player_text", "player_text", "user_text", "prompt"):
        value = kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    messages = kwargs.get("messages")
    if isinstance(messages, Sequence) and not isinstance(messages, (str, bytes)):
        candidate = _latest_text_from_messages(messages)
        if candidate:
            return candidate

    for arg in reversed(args):
        if isinstance(arg, str) and arg.strip():
            return arg.strip()
        if isinstance(arg, Sequence) and not isinstance(arg, (str, bytes)):
            candidate = _latest_text_from_messages(arg)
            if candidate:
                return candidate

    return ""


def make_deterministic_fake_responder() -> Callable[[str], dict[str, Any]]:
    """Return a stable fake responder for deterministic synthetic tests."""

    def _responder(latest_player_text: str) -> dict[str, Any]:
        normalized = latest_player_text.strip().lower()

        if not normalized:
            branch = "fallback"
            player_facing_text = "A quiet beat passes, and the scene remains in motion."
        elif "?" in normalized or normalized.startswith(
            ("what", "where", "when", "why", "how", "who", "can ", "do ", "is ", "are ")
        ):
            branch = "question"
            player_facing_text = "Brief answer: yes, and the situation is stable for now."
        elif any(
            token in normalized
            for token in ("investigate", "inspect", "search", "look for", "examine", "scan", "check")
        ):
            branch = "investigation"
            player_facing_text = "You spot a concrete clue: fresh marks point toward a side passage."
        elif any(
            token in normalized
            for token in ("hello", "hi ", "greet", "talk to", "ask ", "tell ", "please", "thank")
        ):
            branch = "social"
            player_facing_text = '"I hear you," the NPC replies. "Speak plainly."'
        else:
            branch = "fallback"
            player_facing_text = "The scene advances with a clear, immediate shift in tension."

        return {
            "ok": True,
            "source": "synthetic_fake_gm",
            "branch": branch,
            "player_facing_text": player_facing_text,
        }

    return _responder


def build_fake_gm_snapshot(
    *,
    player_text_history: Iterable[str],
    responder: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic snapshot from player text history."""
    history = tuple(player_text_history)
    latest_player_text = history[-1] if history else ""
    active_responder = responder or make_deterministic_fake_responder()
    response = active_responder(latest_player_text)
    snapshot: dict[str, Any] = {
        "latest_player_text": latest_player_text,
        "response": response,
    }
    if isinstance(response, dict):
        sid = response.get("scene_id")
        if isinstance(sid, str) and sid.strip():
            snapshot["scene_id"] = sid.strip()
    return snapshot


def install_fake_responder_monkeypatches(
    *,
    monkeypatch: Any,
    target_paths: Iterable[str],
    responder: Callable[[str], dict[str, Any]] | None = None,
) -> Callable[[str], dict[str, Any]]:
    """Patch model-call seams to route through deterministic fake responder."""
    active_responder = responder or make_deterministic_fake_responder()

    def _fake_model_call(*args: Any, **kwargs: Any) -> dict[str, Any]:
        latest_player_text = extract_latest_player_text(*args, **kwargs)
        return active_responder(latest_player_text)

    for target_path in target_paths:
        monkeypatch.setattr(target_path, _fake_model_call, raising=False)

    return active_responder
