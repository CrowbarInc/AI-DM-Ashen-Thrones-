"""Visible-surface inspection compatibility for one experimental adapter.

INSPECT stays on the investigate resolver. PERCEIVE stays on observe.
This module does not rename operations or replace a target.
"""

from __future__ import annotations

from typing import Any

from game.referenced_surface import (
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    classify_referenced_surface,
)


def _interactable(harness: Any, target_id: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    scene = harness.active_envelope().get("scene") or {}
    for item in scene.get("interactables") or []:
        if isinstance(item, dict) and str(item.get("id") or "") == target_id:
            return item, scene
    return None, scene


def _visible_facts(scene: dict[str, Any]) -> list[str]:
    return [str(row).strip() for row in (scene.get("visible_facts") or []) if isinstance(row, str) and str(row).strip()]


def _matches(classified: dict[str, Any], target_id: str, description: str) -> bool:
    if not classified.get("visibility"):
        return False
    if str(classified.get("hidden_fact") or "").strip():
        return False
    authority = str(classified.get("authority") or "")
    if authority == AUTHORITY_AUTHORED_VISIBLE_FEATURE:
        return (
            str(classified.get("visible_fact") or "").strip() == description
            and not str(classified.get("interactable_id") or "").strip()
        )
    if authority == AUTHORITY_AUTHORED_INTERACTABLE:
        return (
            str(classified.get("interactable_id") or "") == target_id
            and str(classified.get("inspectable_text") or "").strip() == description
        )
    return False


def visible_surface_eligible(harness: Any, target_id: str, player_text: str) -> bool:
    """True when this utterance's inspection of this target is an already-visible description."""
    text = str(player_text or "").strip()
    if not text:
        return False
    item, scene = _interactable(harness, target_id)
    if item is None:
        return False
    if str(item.get("reveals_clue") or "").strip():
        return False
    description = str(item.get("description") or "").strip()
    if not description or description not in _visible_facts(scene):
        return False
    classified = classify_referenced_surface(
        text,
        harness.active_envelope(),
        world=harness.world,
        explicit_target=target_id,
    )
    return _matches(classified, target_id, description)


def accepted_visible_surface_text(
    harness: Any,
    action: dict[str, Any],
    resolution: dict[str, Any],
) -> str | None:
    """Return the already-visible description, or None when the resolver result is not that inspection."""
    if str(action.get("operation_class") or "") != "INSPECT":
        return None
    if str(action.get("engine_type") or "") != "investigate":
        return None
    if action.get("visible_surface_inspection") is not True:
        return None
    target_id = str(action.get("target_id") or "")
    item, scene = _interactable(harness, target_id)
    if item is None or str(item.get("reveals_clue") or "").strip():
        return None
    description = str(item.get("description") or "").strip()
    if not description or description not in _visible_facts(scene):
        return None
    if str(resolution.get("kind") or "") != "investigate":
        return None
    if resolution.get("success") is not True:
        return None
    if resolution.get("discovered_clues") or resolution.get("clue_id"):
        return None
    if resolution.get("world_updates") or resolution.get("skill_check") or resolution.get("resolved_transition"):
        return None
    if resolution.get("state_changes"):
        return None
    bound = resolution.get("interactable_id")
    if bound not in (None, "", target_id):
        return None
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    if meta.get("skill_check") or meta.get("hidden_fact_revealed"):
        return None
    if not meta.get("referenced_surface_visibility"):
        return None
    authority = str(meta.get("referenced_surface_authority") or "")
    if authority == AUTHORITY_AUTHORED_VISIBLE_FEATURE:
        fact = str(meta.get("referenced_surface_visible_fact") or "").strip()
        extra_id = str(meta.get("referenced_surface_interactable_id") or "").strip()
        extra_text = str(meta.get("referenced_surface_inspectable_text") or "").strip()
        if fact != description or extra_id or extra_text:
            return None
    elif authority == AUTHORITY_AUTHORED_INTERACTABLE:
        if str(meta.get("referenced_surface_interactable_id") or "") != target_id:
            return None
        if str(meta.get("referenced_surface_inspectable_text") or "").strip() != description:
            return None
    else:
        return None
    return description
