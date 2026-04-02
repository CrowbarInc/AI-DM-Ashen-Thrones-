from __future__ import annotations

from typing import Any, Dict, List

from game.clues import _canonical_registry_lead_id, get_all_known_clue_texts
from game.leads import get_lead, is_lead_terminal

# When a scene has no ``journal_seed_facts``, only this many ``visible_facts`` lines
# are copied into the journal. Full ``visible_facts`` may be long (GM/debug/prompt
# context); the journal should stay a player-knowledge summary, not a scene dump.
_JOURNAL_FALLBACK_VISIBLE_CAP = 8


def _norm_str_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for item in values:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _journal_bootstrap_known_facts(scene: Dict[str, Any]) -> List[str]:
    """Opening journal lines: curated seed, not the full visible-fact list."""
    seed = _norm_str_list(scene.get('journal_seed_facts'))
    if seed:
        return seed
    visible = _norm_str_list(scene.get('visible_facts'))
    return visible[:_JOURNAL_FALLBACK_VISIBLE_CAP]


def _runtime_revealed_hidden_facts(session: Dict[str, Any]) -> List[str]:
    """Facts the player earned after hidden-to-visible revelation (any scene)."""
    root = session.get('scene_runtime') or {}
    if not isinstance(root, dict):
        return []
    gathered: List[str] = []
    seen_lower: set[str] = set()
    for _sid in sorted(root.keys()):
        data = root.get(_sid)
        if not isinstance(data, dict):
            continue
        for fact in data.get('revealed_hidden_facts') or []:
            if not isinstance(fact, str) or not fact.strip():
                continue
            s = fact.strip()
            key = s.lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            gathered.append(s)
    return gathered


def _clue_text_surfaces_as_unresolved_lead(session: Dict[str, Any], world: Dict[str, Any] | None, text: str) -> bool:
    """Player unresolved-lead list: exclude when every known clue identity for this text maps to a terminal lead."""
    knowledge = session.get("clue_knowledge") if isinstance(session, dict) else None
    if not isinstance(knowledge, dict):
        return True
    stripped = text.strip()
    matching_ids = [
        cid
        for cid, entry in knowledge.items()
        if isinstance(cid, str)
        and cid.strip()
        and isinstance(entry, dict)
        and str(entry.get("text") or "").strip() == stripped
    ]
    if not matching_ids:
        return True
    w = world if isinstance(world, dict) else None
    for cid in matching_ids:
        lid = _canonical_registry_lead_id(cid.strip(), w, None)
        row = get_lead(session, lid)
        if row is None or not is_lead_terminal(row):
            return True
    return False


def _merge_known_fact_lines(bootstrap: List[str], revealed: List[str]) -> List[str]:
    """Preserve order: seed first, then earned reveals; drop duplicates (case-insensitive)."""
    out: List[str] = []
    seen_lower: set[str] = set()
    for line in bootstrap + revealed:
        key = line.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        out.append(line)
    return out


def build_player_journal(session: Dict[str, Any], world: Dict[str, Any] | None = None, scene_envelope: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Construct a lightweight, player-facing journal/codex view.

    Merges bootstrap (scene ``journal_seed_facts`` or a capped slice of
    ``visible_facts`` — intentionally narrower than full scene visibility for GM)
    with runtime (``clue_knowledge``, ``scene_runtime``). Not a persistence boundary.
    """
    world = world or {}
    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}

    # Journal ``known_facts`` is intentionally narrower than ``scene.visible_facts``:
    # visible facts anchor narration, affordances, and debug; the journal should read
    # as established player knowledge, not a raw export of scene state.
    scene_dict = scene if isinstance(scene, dict) else {}
    bootstrap = _journal_bootstrap_known_facts(scene_dict)
    revealed = _runtime_revealed_hidden_facts(session)
    known_facts = _merge_known_fact_lines(bootstrap, revealed)

    # Include discovered + inferred clues from clue knowledge layer
    discovered_clues = list(get_all_known_clue_texts(session))

    # Unresolved leads: same pool as discovered clue texts, minus rows whose authoritative registry
    # lead is terminal (resolved/obsolete). Presentation-only; registry and debug dumps unchanged.
    unresolved_leads = [t for t in discovered_clues if _clue_text_surfaces_as_unresolved_lead(session, world, t)]

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

