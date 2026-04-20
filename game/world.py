from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional

from game.state_authority import WORLD_STATE, assert_owner_can_mutate_domain
from game.npc_promotion import (
    ensure_npc_social_fields,
    normalize_promoted_npc_record,
    promote_scene_actor_to_npc,
    promoted_npc_id_for_actor,
)
from game.schema_contracts import (
    adapt_legacy_clue,
    adapt_legacy_project,
    coerce_world_state_clock_row,
    normalize_clue,
    normalize_project,
    validate_clue,
    validate_clock,
    validate_project,
)


# -----------------------------------------------------------------------------
# Agenda simulation constants (deterministic, threshold-based)
# -----------------------------------------------------------------------------
PRESSURE_THRESHOLD_EVENT = 3  # when pressure crosses this, append event (once)
AGENDA_THRESHOLD_FLAG = 3    # when agenda_progress crosses this, set world flag (once)
AGENDA_THRESHOLD_OP_COMPLETE = 5  # when agenda_progress crosses this, append operation-complete event (once)
AGENDA_PROGRESS_MAX = 10     # cap faction agenda progress
PRESSURE_MAX = 10            # cap faction pressure


def ensure_defaults(world: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure expected top-level keys exist on a world dict (read-time / save-time shape).

    Idempotent ``setdefault`` only—not an authoritative semantic mutation path and
    not a substitute for guarded world updates (see callers such as ``load_world``).
    """
    world.setdefault('settlements', [])
    world.setdefault('factions', [])
    world.setdefault('npcs', [])
    world.setdefault('assets', [])
    world.setdefault('projects', [])
    world.setdefault('world_flags', [])
    world.setdefault('event_log', [])
    world.setdefault('inference_rules', [])
    world.setdefault('clues', {})
    world.setdefault('world_state', {})
    ws = world['world_state']
    if not isinstance(ws, dict):
        world['world_state'] = {'flags': {}, 'counters': {}, 'clocks': {}}
    else:
        ws.setdefault('flags', {})
        ws.setdefault('counters', {})
        ws.setdefault('clocks', {})
    return world


def get_world_npc_by_id(world: Dict[str, Any], npc_id: str) -> Optional[Dict[str, Any]]:
    """Return the NPC dict from ``world[\"npcs\"]`` by id, with social fields normalized."""
    ensure_defaults(world)
    nid = str(npc_id or "").strip()
    if not nid:
        return None
    for npc in world.get("npcs") or []:
        if not isinstance(npc, dict):
            continue
        if str(npc.get("id") or "").strip() == nid:
            ensure_npc_social_fields(npc)
            return npc
    return None


def upsert_world_npc(world: Dict[str, Any], npc_record: Dict[str, Any]) -> Dict[str, Any]:
    """Insert or merge an NPC by ``id`` into ``world[\"npcs\"]``. Idempotent for identical input."""
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="upsert_world_npc")
    ensure_defaults(world)
    if not isinstance(npc_record, dict):
        raise TypeError("npc_record must be a dict")
    npcs = world["npcs"]
    if not isinstance(npcs, list):
        world["npcs"] = []
        npcs = world["npcs"]
    nid = str(npc_record.get("id") or "").strip()
    if not nid:
        raise ValueError("npc_record must include a non-empty id")
    idx = -1
    for i, row in enumerate(npcs):
        if isinstance(row, dict) and str(row.get("id") or "").strip() == nid:
            idx = i
            break
    if idx >= 0:
        merged = {**npcs[idx], **npc_record}
    else:
        merged = copy.deepcopy(npc_record)
    normalized = normalize_promoted_npc_record(merged)
    if idx >= 0:
        npcs[idx] = normalized
    else:
        npcs.append(normalized)
    return normalized


def _ensure_faction_agenda(faction: Dict[str, Any]) -> None:
    """Ensure faction has agenda fields. Backward compatible."""
    if not isinstance(faction, dict):
        return
    faction.setdefault('goal', '')
    faction.setdefault('current_plan', '')
    faction.setdefault('agenda_progress', 0)
    if 'assets' not in faction:
        faction['assets'] = []
    # Normalize to int
    try:
        faction['agenda_progress'] = int(faction.get('agenda_progress', 0) or 0)
    except (TypeError, ValueError):
        faction['agenda_progress'] = 0


def _ensure_npc_agenda(npc: Dict[str, Any]) -> None:
    """Ensure NPC has agenda fields. Backward compatible. location = scene_id."""
    if not isinstance(npc, dict):
        return
    npc.setdefault('role', '')
    npc.setdefault('affiliation', '')
    npc.setdefault('current_agenda', '')
    npc.setdefault('availability', 'available')
    if 'location' not in npc and 'scene_id' in npc:
        npc['location'] = npc['scene_id']
    elif 'location' not in npc:
        npc['location'] = ''
    ensure_npc_social_fields(npc)


def advance_world_tick(world: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Advance world by one tick. Project progression unchanged. Adds deterministic
    faction agenda, pressure thresholds, NPC movement. Return shape preserved."""
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="advance_world_tick")
    ensure_defaults(world)
    generated: List[Dict[str, Any]] = []
    ws = world['world_state']
    if not isinstance(ws, dict):
        ws = world.setdefault('world_state', {'flags': {}, 'counters': {}, 'clocks': {}})
    flags = ws.setdefault('flags', {})
    if not isinstance(flags, dict):
        flags = {}
        ws['flags'] = flags

    # --- Project progression (schema-contract canonical rows) ---
    projects = world.get('projects') or []
    if not isinstance(projects, list):
        projects = []
        world['projects'] = projects
    for i, project in enumerate(projects):
        if not isinstance(project, dict):
            continue
        if project.get('status', 'active') == 'active':
            canon_proj = normalize_project(adapt_legacy_project(project))
            okp, _ = validate_project(canon_proj)
            if not okp:
                continue
            target_val = max(1, int(canon_proj.get('target') or 1))
            progress_val = int(canon_proj.get('progress', 0) or 0)
            canon_proj['progress'] = min(target_val, progress_val + 1)
            canon_proj['target'] = target_val
            if canon_proj['progress'] >= target_val:
                canon_proj['status'] = 'complete'
                generated.append({
                    'type': 'project_completed',
                    'text': f"Project completed: {canon_proj.get('name', 'Project')}"
                })
            world['projects'][i] = canon_proj

    # --- Faction agenda simulation ---
    for faction in world.get('factions') or []:
        if not isinstance(faction, dict):
            continue
        _ensure_faction_agenda(faction)
        fid = faction.get('id', '') or str(faction.get('name', 'unknown'))

        old_pressure = int(faction.get('pressure', 0) or 0)
        old_agenda = int(faction.get('agenda_progress', 0) or 0)

        # Pressure: +1 per tick (deterministic). Original stalled at 3; extended for agenda simulation.
        new_pressure = min(PRESSURE_MAX, old_pressure + 1)
        faction['pressure'] = new_pressure

        # Agenda progress: +1 per tick (deterministic)
        new_agenda = min(AGENDA_PROGRESS_MAX, old_agenda + 1)
        faction['agenda_progress'] = new_agenda

        # Threshold: pressure crosses PRESSURE_THRESHOLD_EVENT -> event once
        if old_pressure < PRESSURE_THRESHOLD_EVENT and new_pressure >= PRESSURE_THRESHOLD_EVENT:
            fname = faction.get('name', fid)
            generated.append({
                'type': 'faction_pressure',
                'text': f"{fname}'s pressure mounts.",
                'source': fid,
            })

        # Threshold: agenda crosses AGENDA_THRESHOLD_FLAG -> set world flag once
        if old_agenda < AGENDA_THRESHOLD_FLAG and new_agenda >= AGENDA_THRESHOLD_FLAG:
            flag_key = f"faction_{fid}_agenda_advanced"
            flags[flag_key] = True

        # Threshold: agenda crosses AGENDA_THRESHOLD_OP_COMPLETE -> operation complete event once
        if old_agenda < AGENDA_THRESHOLD_OP_COMPLETE and new_agenda >= AGENDA_THRESHOLD_OP_COMPLETE:
            fname = faction.get('name', fid)
            generated.append({
                'type': 'faction_operation_complete',
                'text': f"{fname} completes an off-screen operation.",
                'source': fid,
            })

    # --- NPC movement (deterministic: mobile + agenda_move_to_scene_id) ---
    for npc in world.get('npcs') or []:
        if not isinstance(npc, dict):
            continue
        _ensure_npc_agenda(npc)
        avail = str(npc.get('availability', 'available') or 'available').strip().lower()
        if avail != 'mobile':
            continue
        move_to = npc.get('agenda_move_to_scene_id') or npc.get('move_to_scene_id')
        if not move_to or not isinstance(move_to, str):
            continue
        move_to = move_to.strip()
        if not move_to:
            continue
        loc = str(npc.get('location', '') or npc.get('scene_id', '') or '')
        if loc == move_to:
            continue
        npc['location'] = move_to
        if 'scene_id' in npc:
            npc['scene_id'] = move_to
        nname = npc.get('name', npc.get('id', 'Unknown'))
        generated.append({
            'type': 'npc_moved',
            'text': f"{nname} moves off-screen to {move_to}.",
            'npc_id': npc.get('id', ''),
            'from_scene': loc,
            'to_scene': move_to,
        })

    if generated:
        world.setdefault('event_log', []).extend(generated)
    return {'events': generated, 'world': world}


def _apply_world_state_updates(world: Dict[str, Any], ws_updates: Dict[str, Any]) -> None:
    """Apply world_state updates from GM: flags, counters, clocks. Keys starting with _ are skipped."""
    if not ws_updates or not isinstance(ws_updates, dict):
        return
    ensure_defaults(world)
    ws = world['world_state']
    flags_up = ws_updates.get('flags')
    if isinstance(flags_up, dict):
        for k, v in flags_up.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                ws.setdefault('flags', {})
                if isinstance(ws['flags'], dict):
                    ws['flags'][k] = v
    counters_up = ws_updates.get('counters')
    if isinstance(counters_up, dict):
        for k, v in counters_up.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                ws.setdefault('counters', {})
                if isinstance(ws['counters'], dict):
                    try:
                        ws['counters'][k] = int(v)
                    except (TypeError, ValueError):
                        pass
    clocks_up = ws_updates.get('clocks')
    if isinstance(clocks_up, dict):
        for name, entry in clocks_up.items():
            if not isinstance(name, str) or not name.strip() or name.startswith('_'):
                continue
            if not isinstance(entry, dict):
                continue
            ws.setdefault('clocks', {})
            if not isinstance(ws['clocks'], dict):
                ws['clocks'] = {}
            canon = coerce_world_state_clock_row(name, entry)
            okc, _ = validate_clock(canon)
            if okc:
                ws['clocks'][str(canon['id'])] = canon


def apply_world_updates(world: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """Apply world_updates conservatively: no blind replacement of collections.
    - append_events: appended to event_log.
    - projects: each entry normalized and merged by id (update or append). Malformed entries dropped.
    - world_state: flags, counters, clocks merged; keys starting with _ are internal and skipped.
    - settlements, factions, assets, world_flags: not replaced from updates (avoid wiping state).
    """
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="apply_world_updates")
    if not updates:
        return
    if 'append_events' in updates and isinstance(updates['append_events'], list):
        world.setdefault('event_log', []).extend(updates['append_events'])

    projects_list = updates.get('projects')
    if isinstance(projects_list, list):
        world.setdefault('projects', [])
        if not isinstance(world['projects'], list):
            world['projects'] = []
        for entry in projects_list:
            if not isinstance(entry, dict):
                continue
            row = normalize_project(adapt_legacy_project(entry))
            okp, _ = validate_project(row)
            if not okp:
                continue
            pid = row.get('id')
            if not pid:
                continue
            found = False
            for i, p in enumerate(world['projects']):
                if isinstance(p, dict) and p.get('id') == pid:
                    world['projects'][i] = row
                    found = True
                    break
            if not found:
                world['projects'].append(row)

    ws_updates = updates.get('world_state')
    if isinstance(ws_updates, dict):
        _apply_world_state_updates(world, ws_updates)


def apply_normalized_world_updates(
    world: Dict[str, Any],
    normalized: Dict[str, Any],
    *,
    session: Optional[Dict[str, Any]] = None,
    scene_id: Optional[str] = None,
) -> None:
    """Apply a :func:`game.schema_contracts.normalize_world_update` / ``adapt_legacy_world_update`` payload.

    Merges patch fields into ``world_state``, upserts projects, merges ``world[\"clues\"]``,
    upserts NPC rows, and optionally appends pending leads when *session* and *scene_id* are set.
    Imperative deltas parked as ``metadata.legacy_increment_counters`` / ``legacy_advance_clocks``
    or present under ``metadata.unknown_legacy_keys`` for those spellings are applied using the
    same deterministic rules as :func:`apply_resolution_world_updates`.
    """
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="apply_normalized_world_updates")
    if not normalized or not isinstance(normalized, dict):
        return
    ensure_defaults(world)
    ws = world["world_state"]
    if not isinstance(ws, dict):
        ws = world.setdefault("world_state", {"flags": {}, "counters": {}, "clocks": {}})

    evs = normalized.get("append_events")
    if isinstance(evs, list) and evs:
        world.setdefault("event_log", []).extend(
            [copy.deepcopy(x) if isinstance(x, dict) else x for x in evs]
        )

    fp = normalized.get("flags_patch")
    if isinstance(fp, dict) and fp:
        ws.setdefault("flags", {})
        if isinstance(ws["flags"], dict):
            for k, v in fp.items():
                if isinstance(k, str) and k.strip() and not k.startswith("_"):
                    ws["flags"][k] = v

    cp = normalized.get("counters_patch")
    if isinstance(cp, dict) and cp:
        ws.setdefault("counters", {})
        if isinstance(ws["counters"], dict):
            for k, v in cp.items():
                if not isinstance(k, str) or not k.strip() or k.startswith("_"):
                    continue
                try:
                    ws["counters"][k] = int(v)
                except (TypeError, ValueError):
                    pass

    clk = normalized.get("clocks_patch")
    if isinstance(clk, dict) and clk:
        ws.setdefault("clocks", {})
        if not isinstance(ws["clocks"], dict):
            ws["clocks"] = {}
        for name, entry in clk.items():
            if not isinstance(name, str) or not name.strip() or name.startswith("_"):
                continue
            if not isinstance(entry, dict):
                continue
            canon = coerce_world_state_clock_row(name, entry)
            okc, _ = validate_clock(canon)
            if okc:
                ws["clocks"][str(canon["id"])] = canon

    projects_list = normalized.get("projects_patch")
    if isinstance(projects_list, list) and projects_list:
        world.setdefault("projects", [])
        if not isinstance(world["projects"], list):
            world["projects"] = []
        for entry in projects_list:
            if not isinstance(entry, dict):
                continue
            row = normalize_project(adapt_legacy_project(entry))
            okp, _ = validate_project(row)
            if not okp:
                continue
            pid = row.get("id")
            if not pid:
                continue
            found = False
            for i, p in enumerate(world["projects"]):
                if isinstance(p, dict) and p.get("id") == pid:
                    world["projects"][i] = row
                    found = True
                    break
            if not found:
                world["projects"].append(row)

    clues_patch = normalized.get("clues_patch")
    if isinstance(clues_patch, dict) and clues_patch:
        world.setdefault("clues", {})
        if isinstance(world["clues"], dict):
            for k, v in clues_patch.items():
                if not isinstance(k, str) or not k.strip() or not isinstance(v, dict):
                    continue
                merged = {**v, "id": str(v.get("id") or k).strip()}
                clue_row = normalize_clue(adapt_legacy_clue(merged))
                okc, _ = validate_clue(clue_row)
                if not okc:
                    continue
                cid = str(clue_row.get("id") or k).strip()
                if cid:
                    world["clues"][cid] = clue_row

    npcs_patch = normalized.get("npcs_patch")
    if isinstance(npcs_patch, list) and npcs_patch:
        for row in npcs_patch:
            if isinstance(row, dict) and str(row.get("id") or "").strip():
                upsert_world_npc(world, row)

    leads_patch = normalized.get("leads_patch")
    if (
        isinstance(leads_patch, list)
        and leads_patch
        and isinstance(session, dict)
        and isinstance(scene_id, str)
        and scene_id.strip()
    ):
        from game.storage import add_pending_lead

        sid = scene_id.strip()
        for lead in leads_patch:
            if isinstance(lead, dict):
                add_pending_lead(session, sid, lead)

    md = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
    res_frag: Dict[str, Any] = {}
    lic = md.get("legacy_increment_counters")
    lac = md.get("legacy_advance_clocks")
    unk = md.get("unknown_legacy_keys")
    incr: Dict[str, Any] = {}
    if isinstance(lic, dict):
        incr.update(copy.deepcopy(lic))
    if isinstance(unk, dict) and isinstance(unk.get("increment_counters"), dict):
        incr.update(copy.deepcopy(unk["increment_counters"]))
    if incr:
        res_frag["increment_counters"] = incr
    adv: Dict[str, Any] = {}
    if isinstance(lac, dict):
        adv.update(copy.deepcopy(lac))
    if isinstance(unk, dict) and isinstance(unk.get("advance_clocks"), dict):
        adv.update(copy.deepcopy(unk["advance_clocks"]))
    if adv:
        res_frag["advance_clocks"] = adv
    if res_frag:
        apply_resolution_world_updates(world, res_frag)


def apply_resolution_world_updates(world: Dict[str, Any], resolution_updates: Dict[str, Any]) -> None:
    """Apply structured world updates from exploration resolutions. Deterministic, engine-driven.

    Supported shape:
        set_flags: {key: value} — set world_state.flags
        increment_counters: {key: amount} — add amount to counter (amount defaults to 1)
        advance_clocks: {clock_name: amount} — advance clock progress by amount
    """
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="apply_resolution_world_updates")
    if not resolution_updates or not isinstance(resolution_updates, dict):
        return
    ensure_defaults(world)
    ws = world['world_state']

    set_flags = resolution_updates.get('set_flags')
    if isinstance(set_flags, dict):
        for k, v in set_flags.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                ws.setdefault('flags', {})
                if isinstance(ws['flags'], dict):
                    ws['flags'][k] = v

    incr = resolution_updates.get('increment_counters')
    if isinstance(incr, dict):
        for k, amt in incr.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                try:
                    amount = int(amt) if amt is not None else 1
                except (TypeError, ValueError):
                    amount = 1
                ws.setdefault('counters', {})
                if isinstance(ws['counters'], dict):
                    current = int(ws['counters'].get(k, 0) or 0)
                    ws['counters'][k] = current + amount

    advance = resolution_updates.get('advance_clocks')
    if isinstance(advance, dict):
        from game.storage import advance_world_clock
        for name, amt in advance.items():
            if isinstance(name, str) and name.strip() and not name.startswith('_'):
                try:
                    amount = int(amt) if amt is not None else 1
                except (TypeError, ValueError):
                    amount = 1
                advance_world_clock(world, name, amount)


def reset_world_playthrough_state(world: Dict[str, Any]) -> None:
    """Clear emergent world runtime (log, ticks, projects) and resync factions/NPCs from bootstrap template.

    Called on New Campaign after ``create_fresh_session_document`` replaces session: world.json on disk
    still holds prior playthrough mutations until this runs. Root replacement is not used for the whole
    world document because settlements/factions/npcs may be author-edited; we reset only layers that
    the engine appends during play and realign known IDs with ``default_world()`` defaults.
    """
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="reset_world_playthrough_state")
    from game.defaults import default_world

    ensure_defaults(world)
    template = default_world()

    world["event_log"] = []
    world["world_flags"] = []
    world["projects"] = []
    world["assets"] = []
    world["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}

    t_factions = {
        f["id"]: f
        for f in (template.get("factions") or [])
        if isinstance(f, dict) and f.get("id")
    }
    for fac in world.get("factions") or []:
        if not isinstance(fac, dict):
            continue
        fid = fac.get("id")
        tf = t_factions.get(fid) if fid else None
        if tf:
            for key in (
                "pressure",
                "agenda_progress",
                "influence",
                "attitude",
                "current_plan",
                "goal",
            ):
                if key in tf:
                    fac[key] = tf[key]
            fac["assets"] = list(tf["assets"]) if isinstance(tf.get("assets"), list) else []
        else:
            fac["pressure"] = 0
            fac["agenda_progress"] = 0
            fac.setdefault("assets", [])

    t_npcs = {
        n["id"]: n
        for n in (template.get("npcs") or [])
        if isinstance(n, dict) and n.get("id")
    }
    for npc in world.get("npcs") or []:
        if not isinstance(npc, dict):
            continue
        nid = npc.get("id")
        tn = t_npcs.get(nid) if nid else None
        if not tn:
            continue
        for key in ("location", "scene_id", "availability", "current_agenda", "disposition"):
            if key in tn:
                npc[key] = tn[key]
        ensure_npc_social_fields(npc)
