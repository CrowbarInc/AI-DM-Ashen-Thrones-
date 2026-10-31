from __future__ import annotations
import copy
from typing import Any, Dict, List, Mapping, Optional

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
    normalize_id,
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


# Imported after ``ensure_defaults`` / faction helpers because ``game.world_progression`` imports this module.
# Backbone seam: persistent projects, faction pressure/agenda, ``world_state`` clocks/flags only.
# Session-scoped clocks and counters are intentionally not modeled as progression nodes here.
from game import world_progression as wp


def _faction_progression_uid(faction: Mapping[str, Any]) -> str:
    """Stable uid for ``game.world_progression`` node ids (matches backbone faction resolution)."""
    uid = normalize_id(faction.get("id"))
    if uid:
        return uid
    return normalize_id(faction.get("name")) or "unknown"


def _faction_progression_uid_counts(world: Mapping[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for faction in world.get("factions") or []:
        if isinstance(faction, dict):
            u = _faction_progression_uid(faction)
            counts[u] = counts.get(u, 0) + 1
    return counts


def _tick_direct_faction_row_advance(faction: Dict[str, Any]) -> None:
    """Per-list-row +1 pressure/agenda when uid collisions prevent disambiguated backbone node ids."""
    _ensure_faction_agenda(faction)
    try:
        op = int(faction.get("pressure", 0) or 0)
    except (TypeError, ValueError):
        op = 0
    try:
        oa = int(faction.get("agenda_progress", 0) or 0)
    except (TypeError, ValueError):
        oa = 0
    faction["pressure"] = min(PRESSURE_MAX, op + 1)
    faction["agenda_progress"] = min(AGENDA_PROGRESS_MAX, oa + 1)


def _merge_validated_clock_row(world: Dict[str, Any], name: str, entry: Dict[str, Any]) -> bool:
    """Merge one GM/template clock row into ``world_state.clocks`` (full row, not a tick advance).

    Persistent world clocks in JSON are the source of truth; session-scoped clocks live on the
    session document and are intentionally excluded from the progression backbone.
    """
    if not isinstance(name, str) or not name.strip() or name.startswith("_"):
        return False
    if not isinstance(entry, dict):
        return False
    ensure_defaults(world)
    ws = world["world_state"]
    if not isinstance(ws, dict):
        return False
    ws.setdefault("clocks", {})
    if not isinstance(ws["clocks"], dict):
        ws["clocks"] = {}
    canon = coerce_world_state_clock_row(name, entry)
    okc, _ = validate_clock(canon)
    if not okc:
        return False
    ws["clocks"][str(canon["id"])] = canon
    return True


def _upsert_canonical_project_row(world: Dict[str, Any], entry: Dict[str, Any]) -> None:
    """Normalize and merge one project row into ``world[\"projects\"]`` by id."""
    row = normalize_project(adapt_legacy_project(entry))
    okp, _ = validate_project(row)
    if not okp:
        return
    pid = row.get("id")
    if not pid:
        return
    world.setdefault("projects", [])
    if not isinstance(world["projects"], list):
        world["projects"] = []
    found = False
    for i, p in enumerate(world["projects"]):
        if isinstance(p, dict) and p.get("id") == pid:
            world["projects"][i] = row
            found = True
            break
    if not found:
        world["projects"].append(row)


def _tick_advance_active_projects(
    world: Dict[str, Any], progression_sink: List[Dict[str, Any]], generated: List[Dict[str, Any]]
) -> None:
    """+1 progress per active valid project via ``advance_progression_node``; legacy ``project_completed`` events only."""
    projects = world.get("projects") or []
    if not isinstance(projects, list):
        world["projects"] = []
        projects = world["projects"]
    for project in projects:
        if not isinstance(project, dict):
            continue
        if project.get("status", "active") != "active":
            continue
        canon_proj = normalize_project(adapt_legacy_project(project))
        okp, _ = validate_project(canon_proj)
        if not okp:
            continue
        pid = str(canon_proj.get("id") or "").strip()
        if not pid:
            continue
        target_val = max(1, int(canon_proj.get("target") or 1))
        progress_val = int(canon_proj.get("progress", 0) or 0)
        before_complete = progress_val >= target_val
        node = wp.advance_progression_node(
            world, f"project:{pid}", 1, reason="world_tick", event_log=progression_sink
        )
        if not node:
            continue
        if not before_complete and str(node.get("status") or "") == "complete":
            generated.append(
                {
                    "type": "project_completed",
                    "text": f"Project completed: {canon_proj.get('name', 'Project')}",
                }
            )


def _tick_advance_factions_one_step(
    world: Dict[str, Any], progression_sink: List[Dict[str, Any]], generated: List[Dict[str, Any]]
) -> None:
    """+1 pressure and agenda per faction via backbone; threshold triggers preserve legacy shapes."""
    uid_counts = _faction_progression_uid_counts(world)
    for faction in world.get("factions") or []:
        if not isinstance(faction, dict):
            continue
        _ensure_faction_agenda(faction)
        fid = faction.get("id", "") or str(faction.get("name", "unknown"))
        uid = _faction_progression_uid(faction)
        old_pressure = int(faction.get("pressure", 0) or 0)
        old_agenda = int(faction.get("agenda_progress", 0) or 0)

        if uid_counts.get(uid, 0) > 1:
            _tick_direct_faction_row_advance(faction)
        else:
            wp.advance_progression_node(
                world,
                wp.faction_pressure_node_id(uid),
                1,
                reason="world_tick",
                event_log=progression_sink,
            )
            wp.advance_progression_node(
                world,
                wp.faction_agenda_node_id(uid),
                1,
                reason="world_tick",
                event_log=progression_sink,
            )

        new_pressure = int(faction.get("pressure", 0) or 0)
        new_agenda = int(faction.get("agenda_progress", 0) or 0)

        if old_pressure < PRESSURE_THRESHOLD_EVENT and new_pressure >= PRESSURE_THRESHOLD_EVENT:
            fname = faction.get("name", fid)
            generated.append(
                {
                    "type": "faction_pressure",
                    "text": f"{fname}'s pressure mounts.",
                    "source": fid,
                }
            )

        if old_agenda < AGENDA_THRESHOLD_FLAG and new_agenda >= AGENDA_THRESHOLD_FLAG:
            flag_key = f"faction_{fid}_agenda_advanced"
            wp.set_progression_node_value(
                world,
                f"world_flag:{flag_key}",
                True,
                reason="world_tick_agenda_threshold",
                event_log=progression_sink,
            )

        if old_agenda < AGENDA_THRESHOLD_OP_COMPLETE and new_agenda >= AGENDA_THRESHOLD_OP_COMPLETE:
            fname = faction.get("name", fid)
            generated.append(
                {
                    "type": "faction_operation_complete",
                    "text": f"{fname} completes an off-screen operation.",
                    "source": fid,
                }
            )


def advance_world_tick(world: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Advance persistent world simulation by one deterministic tick.

    Active projects and faction pressure/agenda move through ``game.world_progression``
    with a detached progression-event sink so helper rows do not enter ``event_log``.
    Legacy threshold events (pressure, agenda milestones, project completion) and
    eligible NPC moves are appended to the player-facing ``event_log``. Return shape preserved.
    """
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="advance_world_tick")
    ensure_defaults(world)
    generated: List[Dict[str, Any]] = []
    ws = world['world_state']
    if not isinstance(ws, dict):
        ws = world.setdefault('world_state', {'flags': {}, 'counters': {}, 'clocks': {}})

    # Routine backbone writes attach ``world_progression`` rows only to ``progression_sink``;
    # player-facing ``event_log`` carries legacy threshold shapes instead.
    progression_sink: List[Dict[str, Any]] = []

    _tick_advance_active_projects(world, progression_sink, generated)
    _tick_advance_factions_one_step(world, progression_sink, generated)

    # --- NPC movement (deterministic: mobile + agenda_move_to_scene_id) ---
    # Not a supported progression node kind; remains local to this tick until unified elsewhere.
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
    progression_sink: List[Dict[str, Any]] = []
    flags_up = ws_updates.get('flags')
    if isinstance(flags_up, dict):
        ops: List[Dict[str, Any]] = []
        for k, v in flags_up.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                ops.append({"op": "set_value", "node_id": f"world_flag:{k}", "value": v})
        if ops:
            wp.apply_progression_delta(world, {"ops": ops}, event_log=progression_sink)
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
            _merge_validated_clock_row(world, name, entry)


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
        for entry in projects_list:
            if isinstance(entry, dict):
                _upsert_canonical_project_row(world, entry)

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
        ops_fp: List[Dict[str, Any]] = []
        for k, v in fp.items():
            if isinstance(k, str) and k.strip() and not k.startswith("_"):
                ops_fp.append({"op": "set_value", "node_id": f"world_flag:{k}", "value": v})
        if ops_fp:
            wp.apply_progression_delta(world, {"ops": ops_fp}, event_log=[])

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
        for name, entry in clk.items():
            if not isinstance(name, str) or not name.strip() or name.startswith("_"):
                continue
            if not isinstance(entry, dict):
                continue
            _merge_validated_clock_row(world, name, entry)

    projects_list = normalized.get("projects_patch")
    if isinstance(projects_list, list) and projects_list:
        for entry in projects_list:
            if isinstance(entry, dict):
                _upsert_canonical_project_row(world, entry)

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

    progression_sink: List[Dict[str, Any]] = []
    set_flags = resolution_updates.get('set_flags')
    if isinstance(set_flags, dict):
        ops_sf: List[Dict[str, Any]] = []
        for k, v in set_flags.items():
            if isinstance(k, str) and k.strip() and not k.startswith('_'):
                ops_sf.append({"op": "set_value", "node_id": f"world_flag:{k}", "value": v})
        if ops_sf:
            wp.apply_progression_delta(world, {"ops": ops_sf}, event_log=progression_sink)

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
        ops_clk: List[Dict[str, Any]] = []
        for name, amt in advance.items():
            if isinstance(name, str) and name.strip() and not name.startswith('_'):
                try:
                    amount = int(amt) if amt is not None else 1
                except (TypeError, ValueError):
                    amount = 1
                ops_clk.append({"op": "advance", "node_id": f"world_clock:{name.strip()}", "amount": amount})
        if ops_clk:
            wp.apply_progression_delta(world, {"ops": ops_clk}, event_log=progression_sink)


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
