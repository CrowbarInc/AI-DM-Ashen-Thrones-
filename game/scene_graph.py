"""Authoritative scene graph for movement validation.

The graph is derived from scene exits and optionally from pending leads (clue-based
unlocked paths). Transitions are only allowed when the destination is reachable from
the current scene.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set


def build_scene_graph(
    list_scene_ids_fn: Callable[[], List[str]],
    load_scene_fn: Callable[[str], Dict[str, Any]],
) -> Dict[str, Set[str]]:
    """Build adjacency map from scene exits. Graph[scene_id] = set of directly reachable scene ids.

    Only includes targets that exist in list_scene_ids. Supports both target_scene_id
    and targetSceneId keys for backward compatibility.
    """
    known_ids = set(list_scene_ids_fn())
    graph: Dict[str, Set[str]] = {}

    for scene_id in known_ids:
        targets: Set[str] = set()
        try:
            envelope = load_scene_fn(scene_id)
        except Exception:
            continue
        scene = envelope.get("scene") if isinstance(envelope, dict) else {}
        if not isinstance(scene, dict):
            continue
        for ex in scene.get("exits") or []:
            if not isinstance(ex, dict):
                continue
            tid = (ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
            if tid and tid in known_ids:
                targets.add(tid)
        graph[scene_id] = targets

    return graph


def get_reachable_from(
    from_scene_id: str,
    graph: Dict[str, Set[str]],
    *,
    session: Optional[Dict[str, Any]] = None,
    known_scene_ids: Optional[Set[str]] = None,
) -> Set[str]:
    """Return set of scene ids reachable from from_scene_id.

    Includes:
    - Exits from the scene (graph edges)
    - Pending leads with leads_to_scene in known_scene_ids (clue-unlocked paths)
    """
    reachable = set(graph.get(from_scene_id, set()))

    if session and known_scene_ids:
        rt = (session.get("scene_runtime") or {}).get(from_scene_id)
        if isinstance(rt, dict):
            for lead in rt.get("pending_leads") or []:
                if isinstance(lead, dict):
                    tid = (lead.get("leads_to_scene") or "").strip()
                    if tid and tid in known_scene_ids:
                        reachable.add(tid)

    return reachable


def is_transition_valid(
    from_scene_id: str,
    to_scene_id: str,
    graph: Dict[str, Set[str]],
    *,
    session: Optional[Dict[str, Any]] = None,
    known_scene_ids: Optional[Set[str]] = None,
) -> bool:
    """Return True if transitioning from_scene_id -> to_scene_id is allowed.

    Requires to_scene_id to be in known_scene_ids and in reachable set.
    """
    if not to_scene_id or not from_scene_id:
        return False
    if known_scene_ids and to_scene_id not in known_scene_ids:
        return False
    reachable = get_reachable_from(
        from_scene_id, graph, session=session, known_scene_ids=known_scene_ids or set()
    )
    return to_scene_id in reachable
