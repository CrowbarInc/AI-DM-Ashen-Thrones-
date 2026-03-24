from __future__ import annotations

from typing import Any, Dict

from game.clues import get_all_known_clue_texts


def build_player_journal(session: Dict[str, Any], world: Dict[str, Any] | None = None, scene_envelope: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Construct a lightweight, player-facing journal/codex view.

    Merges bootstrap (scene ``visible_facts`` from disk, faction rows from ``world``)
    with runtime (``clue_knowledge``, ``scene_runtime``). Not a persistence boundary.
    """
    world = world or {}
    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}

    active_scene_id = session.get('active_scene_id')
    scene_runtime = session.get('scene_runtime', {}) or {}
    rt = scene_runtime.get(active_scene_id, {}) if isinstance(scene_runtime, dict) else {}

    known_facts = list(scene.get('visible_facts', []) or [])
    # Include discovered + inferred clues from clue knowledge layer
    discovered_clues = list(get_all_known_clue_texts(session))

    # For v1, treat all discovered clues as unresolved leads.
    unresolved_leads = list(discovered_clues)

    factions = list(world.get('factions', []) or [])
    recent_events = list((world.get('event_log', []) or [])[-10:])
    projects = list(world.get('projects', []) or [])

    return {
        'known_facts': known_facts,
        'discovered_clues': discovered_clues,
        'unresolved_leads': unresolved_leads,
        'npcs': [],  # NPC summarization can be added in a later pass.
        'factions': factions,
        'recent_events': recent_events,
        'projects': projects,
    }

