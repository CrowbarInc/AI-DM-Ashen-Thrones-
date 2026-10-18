"""Disposable JSON round-trip. This file is not under data/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.pr_dq.envelope import PlayerMessage
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.history import ConversationHistory
from experiments.pr_dq.safety import authoritative_snapshot


def export_state(harness: DisposableHarness) -> dict[str, Any]:
    return {
        "session": harness.session,
        "world": harness.world,
        "character": harness.character,
        "combat": harness.combat,
        "resolver_calls": list(harness.resolver_calls),
        "history": harness.history.records(),
        "snapshot": authoritative_snapshot(harness),
    }


def write_state(path: Path, harness: DisposableHarness) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(export_state(harness), indent=2, default=str) + "\n", encoding="utf-8")


def _message(row: dict[str, Any]) -> PlayerMessage:
    message = PlayerMessage(
        message_id=str(row["message_id"]),
        text=str(row["text"]),
        mode=str(row["mode"]),
        mode_source=str(row["mode_source"]),
        intent=str(row["intent"]),
        status="PENDING",
        requested_override=str(row.get("requested_override") or "AUTO"),
        destination="",
        correction_subject=str(row.get("correction_subject") or "NONE"),
        classification_basis=str(row.get("classification_basis") or ""),
    )
    message.destination = str(row.get("destination") or "")
    message.status = str(row["status"])
    message.processing_result = dict(row.get("processing_result") or {})
    message.committed = bool(row.get("committed"))
    message.adjudication_required = bool(row.get("adjudication_required"))
    return message


def read_state(path: Path) -> tuple[DisposableHarness, str]:
    """Load a fresh harness from disk and return it with the saved snapshot."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    harness = DisposableHarness()
    harness.session = payload["session"]
    harness.world = payload["world"]
    harness.character = payload["character"]
    harness.combat = payload["combat"]
    harness.resolver_calls = list(payload.get("resolver_calls") or [])
    history = ConversationHistory()
    for row in payload.get("history") or []:
        history.append(_message(row))
    harness.history = history
    return harness, str(payload.get("snapshot") or "")
