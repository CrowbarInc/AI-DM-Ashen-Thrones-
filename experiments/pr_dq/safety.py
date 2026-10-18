"""OOC isolation. Non-IC handling must leave authoritative state unchanged."""

from __future__ import annotations

import json
from typing import Any

from experiments.pr_dq.envelope import PlayerMessage


class OOCSafetyError(RuntimeError):
    """A non-executing message changed authoritative state."""


def authoritative_snapshot(harness: Any) -> str:
    session = harness.session
    runtime = session.get("scene_runtime") or {}
    resolved = {
        scene_id: {
            "resolved_interactables": runtime_row.get("resolved_interactables"),
            "discovered_clues": runtime_row.get("discovered_clues"),
        }
        for scene_id, runtime_row in runtime.items()
        if isinstance(runtime_row, dict)
    }
    payload = {
        "scene": session.get("active_scene_id"),
        "visited": session.get("visited_scene_ids"),
        "clocks": session.get("clocks"),
        "turn": session.get("turn_counter"),
        "npc_runtime": session.get("npc_runtime"),
        "scene_state": session.get("scene_state"),
        "resolved": resolved,
        "flags": session.get("flags"),
        "inventory": session.get("inventory"),
        "hp": harness.character.get("hp"),
        "combat_action_used": harness.combat.get("player_turn_used"),
        "combat_round": harness.combat.get("round"),
        "world_flags": harness.world.get("world_flags"),
        "world_state": harness.world.get("world_state"),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def nonmutating_response(message: PlayerMessage) -> str:
    """Deterministic deferral. This is not an answer from a provider."""
    if message.destination == "OOC_CORRECTION" and (
        message.correction_subject == "COMMITTED_ACTION" or message.adjudication_required
    ):
        return (
            "That correction concerns a committed action. "
            "Explicit adjudication is required. No state was changed."
        )
    if message.destination == "OOC_CORRECTION":
        return "Correction noted. It does not change committed state."
    if message.destination == "OOC_RULES_QUERY":
        return "Rules question deferred. No gameplay action was executed."
    if message.destination == "OOC_QUESTION":
        return "Out-of-character question noted. No gameplay action was executed."
    if message.destination == "MIXED_MESSAGE":
        return "This message mixes in-character and out-of-character content. Clarification is required."
    return "Message deferred. No gameplay action was executed."


def refuse_unexecuted_mutation(before: str, after: str, message: PlayerMessage) -> None:
    if before != after:
        raise OOCSafetyError(
            f"{message.message_id} changed authoritative state without an accepted IC execution"
        )
