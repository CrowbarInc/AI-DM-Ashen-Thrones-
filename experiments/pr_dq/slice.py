"""Four hand-authored IC turns plus one OOC interruption.

Interpretations are fixtures. No provider is asked what they mean.
"""

from __future__ import annotations

from typing import Any

from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.world import GATE_ID, LANTERN_ID, MARA_ID, NOTICE_ID, STREET_ID

TURN_1 = {
    "message_id": "msg_001",
    "text": "I look at the lantern by the gate.",
    "mode_override": "IC",
    "intent": "ACTION",
    "action": {
        "operation_class": "PERCEIVE",
        "engine_type": "observe",
        "target_id": LANTERN_ID,
    },
}
OOC_INTERRUPTION = {
    "message_id": "msg_002",
    "text": "Wait, which street did Mara mention?",
    "mode_override": "OOC",
    "intent": "QUESTION",
    "action": None,
}
TURN_2 = {
    "message_id": "msg_003",
    "text": "I ask Sergeant Mara whether the street is beyond the gate.",
    "mode_override": "IC",
    "intent": "DIALOGUE",
    "action": {
        "operation_class": "ASK",
        "engine_type": "question",
        "target_id": MARA_ID,
    },
}
TURN_3 = {
    "message_id": "msg_004",
    "text": "I go through the courtyard gate.",
    "mode_override": "IC",
    "intent": "ACTION",
    "action": {
        "operation_class": "MOVE",
        "engine_type": "scene_transition",
        "target_id": GATE_ID,
        "target_scene_id": STREET_ID,
    },
}
TURN_4 = {
    "message_id": "msg_005",
    "text": "I read the notice board.",
    "mode_override": "IC",
    "intent": "ACTION",
    "action": {
        "operation_class": "INSPECT",
        "engine_type": "investigate",
        "target_id": NOTICE_ID,
    },
}

SEQUENCE = (TURN_1, OOC_INTERRUPTION, TURN_2, TURN_3, TURN_4)


def run_vertical_slice(harness: DisposableHarness | None = None) -> dict[str, Any]:
    """Play the four IC turns and the OOC interruption on one disposable session."""
    harness = harness or DisposableHarness()
    steps = []
    for spec in SEQUENCE:
        before = authoritative_snapshot(harness)
        calls_before = len(harness.resolver_calls)
        message = harness.submit(
            spec["text"],
            message_id=spec["message_id"],
            mode_override=spec["mode_override"],
            intent=spec["intent"],
            action=spec["action"],
        )
        after = authoritative_snapshot(harness)
        steps.append(
            {
                "message_id": message.message_id,
                "text": message.text,
                "mode": message.mode,
                "mode_source": message.mode_source,
                "intent": message.intent,
                "status": message.status,
                "destination": message.destination,
                "committed": message.committed,
                "executed": bool(message.processing_result.get("executed")),
                "resolver_invoked": bool(message.processing_result.get("resolver_invoked")),
                "mutated_state": before != after,
                "new_resolver_calls": harness.resolver_calls[calls_before:],
                "resolution_kind": message.processing_result.get("resolution_kind"),
                "resolution_success": message.processing_result.get("resolution_success"),
                "rolls_dice": message.processing_result.get("rolls_dice"),
                "response": message.processing_result.get("response"),
                "reason": message.processing_result.get("reason"),
                "scene": harness.session.get("active_scene_id"),
                "time_pressure": (harness.session.get("clocks") or {}).get("time_pressure"),
                "turn_counter": harness.session.get("turn_counter"),
            }
        )
    return {
        "steps": steps,
        "history_ids": harness.history.ids(),
        "history_length": len(harness.history),
        "final_scene": harness.session.get("active_scene_id"),
        "time_pressure": (harness.session.get("clocks") or {}).get("time_pressure"),
        "turn_counter": harness.session.get("turn_counter"),
        "hp": harness.character.get("hp"),
        "inventory": harness.session.get("inventory"),
        "combat_action_used": harness.combat.get("player_turn_used"),
        "resolver_calls": list(harness.resolver_calls),
        "notice_resolved": _notice_resolved(harness),
        "npc_ids": sorted((harness.session.get("npc_runtime") or {}).keys()),
    }


def _notice_resolved(harness: DisposableHarness) -> bool:
    runtime = (harness.session.get("scene_runtime") or {}).get(STREET_ID) or {}
    resolved = runtime.get("resolved_interactables") or []
    return NOTICE_ID in resolved
