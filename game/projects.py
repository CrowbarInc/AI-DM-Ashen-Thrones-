from __future__ import annotations

from typing import Any, Dict, List

from game.schema_contracts import adapt_legacy_project, normalize_project, validate_project
from game.utils import slugify


PROJECT_CATEGORIES = {"infrastructure", "faction", "research", "asset", "military", "ritual"}
PROJECT_STATUSES = {"active", "paused", "complete"}


def _normalize_project_shape(data: Dict[str, Any]) -> Dict[str, Any]:
    """Produce canonical project shape; accepts legacy 'goal' and 'completed'."""
    name = str(data.get("name", "") or "").strip()
    pid = data.get("id") or slugify(name or "project")
    category = str(data.get("category", "") or "").strip().lower()
    if category not in PROJECT_CATEGORIES:
        category = "infrastructure"
    status = str(data.get("status", "") or "").strip().lower()
    # Legacy: normalize "completed" -> "complete"
    if status == "completed":
        status = "complete"
    if status not in PROJECT_STATUSES:
        status = "active"
    progress = int(data.get("progress", 0) or 0)
    # Legacy: accept "goal" when "target" is missing
    target = int(data.get("target") or data.get("goal", 4) or 4)
    tags = list(data.get("tags", []) or [])
    notes = str(data.get("notes", "") or "")
    return {
        "id": pid,
        "name": name or pid,
        "category": category,
        "status": status,
        "progress": max(0, progress),
        "target": max(1, target),
        "tags": tags,
        "notes": notes,
    }


def normalize_project_entry(entry: Any) -> Dict[str, Any] | None:
    """Normalize a single project entry (e.g. from world_updates) to canonical shape. Returns None if entry is not a dict."""
    if not isinstance(entry, dict):
        return None
    return _normalize_project_shape(entry)


def list_projects(world: Dict[str, Any]) -> List[Dict[str, Any]]:
    projects = world.get("projects")
    if not isinstance(projects, list):
        return []
    return [p for p in projects if isinstance(p, dict)]


def create_project(world: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new project in world['projects'] and return it."""
    normalized = normalize_project(adapt_legacy_project(data or {}))
    ok, _ = validate_project(normalized)
    if not ok:
        normalized = _normalize_project_shape(data or {})
    projects = world.setdefault("projects", [])
    if not isinstance(projects, list):
        projects = []
        world["projects"] = projects
    # Avoid duplicate IDs.
    if any(p.get("id") == normalized["id"] for p in projects):
        return normalized
    projects.append(normalized)
    return normalized


def update_project(world: Dict[str, Any], project_id: str, patch: Dict[str, Any]) -> Dict[str, Any] | None:
    """Update an existing project; returns the updated project or None if not found."""
    projects = list_projects(world)
    for idx, proj in enumerate(projects):
        if proj.get("id") == project_id:
            merged = proj.copy()
            merged.update(patch or {})
            normalized = normalize_project(adapt_legacy_project(merged))
            ok, _ = validate_project(normalized)
            if not ok:
                normalized = _normalize_project_shape(merged)
            world["projects"][idx] = normalized
            return normalized
    return None

