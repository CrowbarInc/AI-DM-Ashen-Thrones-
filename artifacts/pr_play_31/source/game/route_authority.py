"""Conservative route eligibility shared by deterministic routing and its bridge."""
from __future__ import annotations


def authored_exit_rows(scene: dict) -> list[dict]:
    """Adapt legacy id-less exits using the existing affordance ID convention.

    This is a view of current authored rows, never a new graph edge.
    """
    from game.utils import slugify
    current = scene.get("scene", scene)
    rows = []
    used = set()
    for item in current.get("exits") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        label = str(row.get("label") or "Travel").strip()
        short = label if len(label) <= 44 else label[:41] + "..."
        identifier = str(row.get("id") or slugify(f"Leave for {short}") or "leave")
        if identifier in used:
            identifier = f"{identifier}-{len(rows)}"
        used.add(identifier)
        row["id"] = identifier
        rows.append(row)
    return rows


def route_status(row: dict, scene_id: str, session: dict, world: dict) -> str:
    # No inference from destination prose or from an investigation intention.
    if (row.get("hidden") or row.get("visible") is False
            or row.get("source_scene_id", scene_id) != scene_id):
        return "hidden"
    if (row.get("locked") or row.get("accessible") is False
            or row.get("available") is False or row.get("reachable") is False
            or row.get("availability", "available") != "available"):
        return "blocked"
    from game.affordances import _affordance_passes_conditions
    if not _affordance_passes_conditions(row, scene_id, session, world):
        return "blocked"
    # Uninterpreted restrictions must never become permission to travel.
    if any(row.get(key) for key in ("prerequisites", "required_discoveries")):
        return "blocked"
    return "available"
