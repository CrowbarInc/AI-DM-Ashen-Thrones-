"""Production-safe bridge from stored interpretation records to engine actions.

The bridge accepts an already-produced interpretation record. It does not call a
model and it does not execute a resolver. Its job is only to validate that the
record names a visible target and convert it into the normalized action shape
the existing production turn pipeline already understands.
"""

from __future__ import annotations

from typing import Any, Callable


CONNECTED_OPERATIONS = {
    "PERCEIVE": "observe",
    "INSPECT": "investigate",
    "ASK": "question",
    "MOVE": "scene_transition",
}

_EXPECTED_VISIBLE_KIND = {
    "PERCEIVE": "perceive_target",
    "INSPECT": "inspect_target",
    "ASK": "npc",
    "MOVE": "exit",
}


def _scene_obj(scene: dict | None) -> dict:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, dict) else scene


def visible_catalog(scene: dict | None, world: dict | None) -> dict[str, dict[str, Any]]:
    """Return visible entity ids for the active scene, with coarse engine kinds."""
    current_scene = _scene_obj(scene)
    scene_id = str(current_scene.get("id") or "").strip()
    out: dict[str, dict[str, Any]] = {}
    for item in current_scene.get("interactables") or []:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id:
            continue
        out[entity_id] = {
            "kind": "inspect_target" if item.get("reveals_clue") else "perceive_target",
            "row": item,
        }
    for item in current_scene.get("exits") or []:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id:
            continue
        out[entity_id] = {"kind": "exit", "row": item}
    for npc in (world or {}).get("npcs") or []:
        if not isinstance(npc, dict):
            continue
        entity_id = str(npc.get("id") or "").strip()
        if not entity_id:
            continue
        if str(npc.get("location") or "").strip() == scene_id:
            out[entity_id] = {"kind": "npc", "row": npc}
    return out


def _single_component(record: dict[str, Any]) -> tuple[str, str | None]:
    components = record.get("action_components")
    if not isinstance(components, list) or len(components) != 1:
        return "", None
    component = components[0] if isinstance(components[0], dict) else {}
    return str(component.get("operation_class") or "").strip().upper(), component.get("target_ref")


def _record_from_interpretation(interpretation: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(interpretation, dict):
        return None
    if isinstance(interpretation.get("record"), dict):
        return interpretation["record"]
    return interpretation


def normalized_action_from_interpretation(
    interpretation: dict[str, Any] | None,
    *,
    scene: dict,
    world: dict,
    player_text: str,
    known_scene_ids: Callable[[], list[str]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Validate a stored interpretation and return a production normalized action.

    The metadata return value is intended for traces and failure reports.
    """
    record = _record_from_interpretation(interpretation)
    if not isinstance(record, dict):
        return None, {"source": "stored_interpretation", "accepted": False, "reason": "missing_record"}
    if str(record.get("communication_mode") or "").strip() != "IN_WORLD_ACTION":
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "not_in_world_action",
            "communication_mode": record.get("communication_mode"),
        }
    if str(record.get("interpretation_status") or "").strip() != "INTERPRETED":
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "not_interpreted",
            "interpretation_status": record.get("interpretation_status"),
        }
    refs = record.get("references") if isinstance(record.get("references"), dict) else {}
    unresolved = refs.get("unresolved_references") if isinstance(refs, dict) else []
    if unresolved:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "unresolved_references",
            "unresolved_references": list(unresolved),
        }
    operation, target_ref = _single_component(record)
    if operation not in CONNECTED_OPERATIONS:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "unsupported_operation",
            "operation": operation,
        }
    target_id = str(target_ref or "").strip()
    if not target_id:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "missing_target",
            "operation": operation,
        }

    catalog = visible_catalog(scene, world)
    target = catalog.get(target_id)
    if not target:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "target_not_visible",
            "operation": operation,
            "target_ref": target_id,
        }
    expected_kind = _EXPECTED_VISIBLE_KIND[operation]
    target_kind = str(target.get("kind") or "")
    visible_surface_inspection = False
    if operation == "INSPECT" and target_kind == "perceive_target":
        visible_surface_inspection = True
    elif target_kind != expected_kind:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "operation_incompatible_with_entity_kind",
            "operation": operation,
            "target_ref": target_id,
            "target_kind": target_kind,
        }

    normalized: dict[str, Any] = {
        "id": target_id,
        "label": target_id,
        "type": CONNECTED_OPERATIONS[operation],
        "prompt": player_text,
        "target_id": target_id,
        "targetEntityId": target_id,
        "metadata": {
            "stored_interpretation": {
                "operation": operation,
                "target_ref": target_id,
                "visible_surface_inspection": visible_surface_inspection,
            }
        },
    }
    if visible_surface_inspection:
        normalized["metadata"]["stored_interpretation"]["compatibility"] = "visible_surface_inspection"
    if operation == "MOVE":
        row = target.get("row") if isinstance(target.get("row"), dict) else {}
        destination = str(row.get("target_scene_id") or "").strip()
        if not destination:
            return None, {
                "source": "stored_interpretation",
                "accepted": False,
                "reason": "exit_has_no_authored_destination",
                "operation": operation,
                "target_ref": target_id,
            }
        if known_scene_ids is not None and destination not in set(known_scene_ids()):
            return None, {
                "source": "stored_interpretation",
                "accepted": False,
                "reason": "unknown_destination_scene",
                "operation": operation,
                "target_ref": target_id,
                "target_scene_id": destination,
            }
        normalized["targetSceneId"] = destination
        normalized["target_scene_id"] = destination
    return normalized, {
        "source": "stored_interpretation",
        "accepted": True,
        "operation": operation,
        "target_ref": target_id,
        "engine_type": normalized["type"],
        "visible_surface_inspection": visible_surface_inspection,
    }
