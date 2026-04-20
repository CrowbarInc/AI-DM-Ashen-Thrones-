from __future__ import annotations

"""Player-facing journal snapshot (``player_visible_state`` publication).

Lead-related fields are derived from the session ``lead_registry`` (via
``list_session_leads``), not from clue text. ``discovered_clues`` comes from the
clue knowledge layer and is intentionally independent of lead buckets.
``unresolved_leads`` is a backward-compatibility alias: sorted titles of
non-terminal (active / pursued / stale) registry rows only.

Merging runtime ``revealed_hidden_facts`` into ``known_facts`` is an explicit
**publication seam** (``journal_merge_revealed_hidden_facts``); the journal remains
a derived view and must not back-write ``hidden_state`` or ``world_state``.
"""

from typing import Any, Dict, List, Tuple

from game.clues import get_all_known_clue_texts
from game.leads import LeadLifecycle, LeadStatus, list_session_leads
from game.state_authority import (
    HIDDEN_STATE,
    PLAYER_VISIBLE_STATE,
    assert_cross_domain_write_allowed,
    assert_owner_can_mutate_domain,
    build_state_mutation_trace,
)
from game.storage import append_debug_trace

# When a scene has no ``journal_seed_facts``, only this many ``visible_facts`` lines
# are copied into the journal. Full ``visible_facts`` may be long (GM/debug/prompt
# context); the journal should stay a player-knowledge summary, not a scene dump.
_JOURNAL_FALLBACK_VISIBLE_CAP = 8

# Recency missing: sort after any real turn at the same priority.
_JOURNAL_MISSING_RECENCY = -(10**18)


def _norm_str_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for item in values:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _journal_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _journal_priority_int(value: Any) -> int:
    n = _journal_optional_int(value)
    return 0 if n is None else n


def _journal_recency_turn(lead: Dict[str, Any]) -> int:
    u = _journal_optional_int(lead.get("last_updated_turn"))
    t = _journal_optional_int(lead.get("last_touched_turn"))
    if u is None and t is None:
        return _JOURNAL_MISSING_RECENCY
    if u is None:
        return t if t is not None else _JOURNAL_MISSING_RECENCY
    if t is None:
        return u
    return max(u, t)


def _journal_priority_sort_key(lead: Dict[str, Any]) -> Tuple[Any, ...]:
    pri = _journal_priority_int(lead.get("priority"))
    rec = _journal_recency_turn(lead)
    title = str(lead.get("title") or "").lower()
    lid = str(lead.get("id") or "")
    return (-pri, -rec, title, lid)


def _journal_str_id_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _journal_optional_id(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _journal_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _journal_compact_lead_record(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(lead.get("id") or ""),
        "title": str(lead.get("title") or ""),
        "summary": str(lead.get("summary") or ""),
        "type": str(lead.get("type") or ""),
        "status": str(lead.get("status") or ""),
        "confidence": str(lead.get("confidence") or ""),
        "priority": _journal_priority_int(lead.get("priority")),
        "next_step": str(lead.get("next_step") or ""),
        "related_npc_ids": _journal_str_id_list(lead.get("related_npc_ids")),
        "related_location_ids": _journal_str_id_list(lead.get("related_location_ids")),
        "parent_lead_id": _journal_optional_id(lead.get("parent_lead_id")),
        "superseded_by": _journal_optional_id(lead.get("superseded_by")),
    }


def _journal_terminal_lead_record(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(lead.get("id") or ""),
        "title": str(lead.get("title") or ""),
        "summary": str(lead.get("summary") or ""),
        "type": str(lead.get("type") or ""),
        "lifecycle": str(lead.get("lifecycle") or ""),
        "status": str(lead.get("status") or ""),
        "resolution_type": _journal_optional_str(lead.get("resolution_type")),
        "resolution_summary": _journal_optional_str(lead.get("resolution_summary")),
        "resolved_at_turn": _journal_optional_int(lead.get("resolved_at_turn")),
        "obsolete_reason": _journal_optional_str(lead.get("obsolete_reason")),
        "superseded_by": _journal_optional_id(lead.get("superseded_by")),
        "consequence_ids": _journal_str_id_list(lead.get("consequence_ids")),
    }


def _journal_sort_lead_rows(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(leads, key=_journal_priority_sort_key)


def _build_authoritative_journal_lead_sections(session: Dict[str, Any]) -> Dict[str, Any]:
    """Bucket registry leads for the journal (presentation-only copies).

    Each row lands in exactly one bucket: ``resolved`` / ``obsolete`` by
    lifecycle; among non-terminal rows, ``active`` / ``pursued`` / ``stale`` by
    ``LeadStatus``. Unknown or empty non-terminal status defaults to *active*.
    """
    raw = list_session_leads(session, include_terminal=True)
    active_src: List[Dict[str, Any]] = []
    pursued_src: List[Dict[str, Any]] = []
    stale_src: List[Dict[str, Any]] = []
    resolved_src: List[Dict[str, Any]] = []
    obsolete_src: List[Dict[str, Any]] = []

    lc_res = LeadLifecycle.RESOLVED.value
    lc_obs = LeadLifecycle.OBSOLETE.value
    st_act = LeadStatus.ACTIVE.value
    st_pur = LeadStatus.PURSUED.value
    st_stl = LeadStatus.STALE.value

    for lead in raw:
        lc = str(lead.get("lifecycle") or "").strip().lower()
        if lc == lc_res:
            resolved_src.append(lead)
        elif lc == lc_obs:
            obsolete_src.append(lead)
        else:
            st = str(lead.get("status") or "").strip().lower()
            if st == st_act:
                active_src.append(lead)
            elif st == st_pur:
                pursued_src.append(lead)
            elif st == st_stl:
                stale_src.append(lead)
            else:
                active_src.append(lead)

    active_leads = [_journal_compact_lead_record(x) for x in _journal_sort_lead_rows(active_src)]
    pursued_leads = [_journal_compact_lead_record(x) for x in _journal_sort_lead_rows(pursued_src)]
    stale_leads = [_journal_compact_lead_record(x) for x in _journal_sort_lead_rows(stale_src)]
    resolved_leads = [_journal_terminal_lead_record(x) for x in _journal_sort_lead_rows(resolved_src)]
    obsolete_leads = [_journal_terminal_lead_record(x) for x in _journal_sort_lead_rows(obsolete_src)]

    nonterminal = len(active_leads) + len(pursued_leads) + len(stale_leads)
    total = len(active_leads) + len(pursued_leads) + len(stale_leads) + len(resolved_leads) + len(obsolete_leads)

    lead_counts = {
        "active": len(active_leads),
        "pursued": len(pursued_leads),
        "stale": len(stale_leads),
        "resolved": len(resolved_leads),
        "obsolete": len(obsolete_leads),
        "nonterminal": nonterminal,
        "total": total,
    }

    return {
        "active_leads": active_leads,
        "pursued_leads": pursued_leads,
        "stale_leads": stale_leads,
        "resolved_leads": resolved_leads,
        "obsolete_leads": obsolete_leads,
        "lead_counts": lead_counts,
    }


def _compat_unresolved_lead_titles(lead_sections: Dict[str, Any]) -> List[str]:
    """Sorted unique titles from non-terminal buckets (registry titles, not clue strings)."""
    titles: List[str] = []
    for key in ("active_leads", "pursued_leads", "stale_leads"):
        for rec in lead_sections.get(key) or []:
            if isinstance(rec, dict):
                t = str(rec.get("title") or "").strip()
                if t:
                    titles.append(t)
    return sorted(set(titles))


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


def merge_player_journal_known_facts_publication(
    bootstrap: List[str],
    revealed_hidden_runtime: List[str],
) -> List[str]:
    """Publication seam: merge ``scene_runtime.revealed_hidden_facts`` into journal ``known_facts``.

    ``known_facts`` is a derived player-facing view only; must not be written back as hidden or world truth.
    """
    rev = [x for x in revealed_hidden_runtime if isinstance(x, str) and x.strip()]
    if rev:
        assert_cross_domain_write_allowed(
            HIDDEN_STATE,
            PLAYER_VISIBLE_STATE,
            operation="journal_merge_revealed_hidden_facts",
        )
    assert_owner_can_mutate_domain(__name__, PLAYER_VISIBLE_STATE, operation="journal_known_facts_merge")
    return _merge_known_fact_lines(bootstrap, rev)


def build_player_journal(session: Dict[str, Any], world: Dict[str, Any] | None = None, scene_envelope: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Construct a lightweight, player-facing journal/codex view.

    Merges bootstrap (scene ``journal_seed_facts`` or a capped slice of
    ``visible_facts`` — intentionally narrower than full scene visibility for GM)
    with runtime (``clue_knowledge``, ``scene_runtime``). Not a persistence boundary.

    Stable keys (in this order): ``known_facts``, ``discovered_clues``,
    ``unresolved_leads``, ``active_leads``, ``pursued_leads``, ``stale_leads``,
    ``resolved_leads``, ``obsolete_leads``, ``lead_counts``, ``npcs``, ``factions``,
    ``recent_events``, ``projects``. Lead buckets and ``lead_counts`` come from the
    authoritative registry; ``unresolved_leads`` duplicates non-terminal titles for
    callers that expect a flat list. Terminal rows use a history-oriented shape
    (``resolved_leads`` vs ``obsolete_leads`` are kept separate).
    """
    world = world or {}
    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}

    # Journal ``known_facts`` is intentionally narrower than ``scene.visible_facts``:
    # visible facts anchor narration, affordances, and debug; the journal should read
    # as established player knowledge, not a raw export of scene state.
    scene_dict = scene if isinstance(scene, dict) else {}
    bootstrap = _journal_bootstrap_known_facts(scene_dict)
    revealed = _runtime_revealed_hidden_facts(session)
    known_facts = merge_player_journal_known_facts_publication(bootstrap, revealed)
    if isinstance(session, dict) and revealed:
        append_debug_trace(
            session,
            build_state_mutation_trace(
                domain=PLAYER_VISIBLE_STATE,
                owner_module=__name__,
                operation="journal_known_facts_merge",
                cross_domain=(HIDDEN_STATE, PLAYER_VISIBLE_STATE, "journal_merge_revealed_hidden_facts"),
                extra={"changed_area": "journal.known_facts"},
            ),
        )

    # Clue texts from ``clue_knowledge``; not merged with or filtered by lead buckets.
    discovered_clues = list(get_all_known_clue_texts(session))

    lead_sections = _build_authoritative_journal_lead_sections(session)
    unresolved_leads = _compat_unresolved_lead_titles(lead_sections)

    factions = list(world.get('factions', []) or [])
    recent_events = list((world.get('event_log', []) or [])[-10:])
    projects = list(world.get('projects', []) or [])

    return {
        'known_facts': known_facts,
        'discovered_clues': discovered_clues,
        'unresolved_leads': unresolved_leads,
        'active_leads': lead_sections['active_leads'],
        'pursued_leads': lead_sections['pursued_leads'],
        'stale_leads': lead_sections['stale_leads'],
        'resolved_leads': lead_sections['resolved_leads'],
        'obsolete_leads': lead_sections['obsolete_leads'],
        'lead_counts': lead_sections['lead_counts'],
        'npcs': [],  # NPC summarization can be added in a later pass.
        'factions': factions,
        'recent_events': recent_events,
        'projects': projects,
    }
