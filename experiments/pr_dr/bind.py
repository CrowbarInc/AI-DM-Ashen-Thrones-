"""Map a validated interpretation onto the PR-DQ action dict.

Only INSPECT, PERCEIVE, ASK, and MOVE are connected. ATTACK is not.
Requested outcomes are never copied into the action.
"""

from __future__ import annotations

from typing import Any

from experiments.pr_do.schema import UNSUPPORTED_OPERATION_CLASSES
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.surface_compat import visible_surface_eligible
from experiments.pr_dr.prompt import visible_catalog

CONNECTED = {
    "PERCEIVE": "observe",
    "INSPECT": "investigate",
    "ASK": "question",
    "MOVE": "scene_transition",
}

_KIND = {
    "PERCEIVE": "perceive_target",
    "INSPECT": "inspect_target",
    "ASK": "npc",
    "MOVE": "exit",
}


def connected_action(
    harness: DisposableHarness,
    operation: str,
    target_ref: str | None,
    player_text: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """Return a resolver action, or a refusal that does not guess another target."""
    if operation == "ATTACK" or operation not in CONNECTED:
        if operation in UNSUPPORTED_OPERATION_CLASSES or operation == "ATTACK":
            return {"operation_class": operation}, "not_connected"
        return None, "not_connected"
    if not isinstance(target_ref, str) or not target_ref.strip():
        return None, "missing_target"
    target_ref = target_ref.strip()
    catalog = {entity_id: kind for entity_id, _label, kind in visible_catalog(harness)}
    if target_ref not in catalog:
        return None, "target_not_visible"
    if operation == "INSPECT" and catalog[target_ref] == "perceive_target":
        if visible_surface_eligible(harness, target_ref, player_text):
            return {
                "operation_class": "INSPECT",
                "engine_type": "investigate",
                "target_id": target_ref,
                "visible_surface_inspection": True,
            }, ""
        return None, "operation_incompatible_with_entity_kind"
    if catalog[target_ref] != _KIND[operation]:
        return None, "operation_incompatible_with_entity_kind"
    action: dict[str, Any] = {
        "operation_class": operation,
        "engine_type": CONNECTED[operation],
        "target_id": target_ref,
    }
    if operation == "MOVE":
        scene = harness.active_envelope().get("scene") or {}
        exit_row = None
        for item in scene.get("exits") or []:
            if isinstance(item, dict) and str(item.get("id") or "") == target_ref:
                exit_row = item
                break
        destination = str((exit_row or {}).get("target_scene_id") or "")
        if not destination:
            return None, "exit_has_no_authored_destination"
        action["target_scene_id"] = destination
    return action, ""
