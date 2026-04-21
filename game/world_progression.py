"""World simulation backbone: orchestration over native world-owned roots only.

This module exposes a normalized *view* of persistent progression (projects,
faction pressure/agenda, world_state clocks/flags). It does not introduce a new
persisted store or shadow JSON subtree.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from game.state_authority import WORLD_STATE, assert_owner_can_mutate_domain
from game.schema_contracts import (
    adapt_legacy_clock,
    adapt_legacy_project,
    coerce_world_state_clock_row,
    normalize_clock,
    normalize_id,
    normalize_project,
    validate_clock,
    validate_project,
)
from game.world import (
    AGENDA_PROGRESS_MAX,
    PRESSURE_MAX,
    _ensure_faction_agenda,
    ensure_defaults,
)

# --- Stable node id grammar (single source for parse + emit; avoids cross-root collisions) ---

_PREFIX_KIND: Tuple[Tuple[str, str], ...] = (
    ("faction_pressure:", "faction_pressure"),
    ("faction_agenda:", "faction_agenda"),
    ("project:", "project"),
    ("world_clock:", "world_clock"),
    ("world_flag:", "world_flag"),
)

_MAX_SNAPSHOT_NODES = 512
_MAX_RECENT_FACTS = 8

# CTIR / prompt projection caps (transport-only; aligned with snapshot node budget)
_MAX_CTIR_CHANGED_NODES = 64
_MAX_CTIR_ACTIVE_PROJECTS = 32
_MAX_CTIR_FACTION_PRESSURE = 32
_MAX_CTIR_FACTION_AGENDA = 32
_MAX_CTIR_WORLD_CLOCKS = 32
_MAX_CTIR_SET_FLAGS = 32

SESSION_PROGRESSION_FINGERPRINT_KEY = "_runtime_progression_nodes_fingerprint_v1"

_PROGRESSION_EVENT_TYPES = frozenset(
    {
        "world_progression",
        "project_completed",
        "faction_pressure",
        "faction_operation_complete",
    }
)


def faction_pressure_node_id(faction_id: str) -> str:
    uid = normalize_id(faction_id)
    return f"faction_pressure:{uid}" if uid else "faction_pressure:unknown"


def faction_agenda_node_id(faction_id: str) -> str:
    uid = normalize_id(faction_id)
    return f"faction_agenda:{uid}" if uid else "faction_agenda:unknown"


def progression_event(
    *,
    operation: str,
    node_id: str,
    node_kind: str,
    text: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one deterministic ``event_log`` row for backbone operations."""
    prog: Dict[str, Any] = {
        "operation": operation,
        "node_id": node_id,
        "node_kind": node_kind,
    }
    if reason is not None and str(reason).strip():
        prog["reason"] = str(reason).strip()
    return {
        "type": "world_progression",
        "text": str(text).strip() or f"{operation} {node_id}",
        "progression": prog,
    }


def _parse_node_id(node_id: str) -> Optional[Tuple[str, str]]:
    if not isinstance(node_id, str):
        return None
    nid = node_id.strip()
    if not nid:
        return None
    for prefix, kind in _PREFIX_KIND:
        if nid.startswith(prefix):
            rest = nid[len(prefix) :]
            if kind in ("faction_pressure", "faction_agenda", "project", "world_clock", "world_flag"):
                if not rest:
                    return None
            return kind, rest
    return None


def _faction_uid(faction: Mapping[str, Any]) -> str:
    uid = normalize_id(faction.get("id"))
    if uid:
        return uid
    return normalize_id(faction.get("name")) or "unknown"


def _flag_status(value: Any) -> str:
    if value is False or value is None:
        return "unset"
    return "set"


def _append_log(world: Dict[str, Any], event_log: Optional[List[Dict[str, Any]]], row: Dict[str, Any]) -> None:
    target = event_log if event_log is not None else world.setdefault("event_log", [])
    if not isinstance(target, list):
        return
    target.append(copy.deepcopy(row) if isinstance(row, dict) else row)


def _project_node(project: Mapping[str, Any]) -> Dict[str, Any]:
    pid = str(project.get("id") or "").strip()
    tags = project.get("tags") if isinstance(project.get("tags"), list) else []
    meta = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    return {
        "id": f"project:{pid}",
        "kind": "project",
        "scope": "world",
        "status": str(project.get("status") or "active"),
        "value": int(project.get("progress", 0) or 0),
        "target": int(project.get("target", 1) or 1),
        "source_ref": {"root": "projects", "id": pid},
        "tags": [str(t) for t in tags if isinstance(t, str)],
        "metadata": copy.deepcopy(meta),
    }


def _faction_pressure_node(faction: Mapping[str, Any]) -> Dict[str, Any]:
    uid = _faction_uid(faction)
    try:
        pressure = int(faction.get("pressure", 0) or 0)
    except (TypeError, ValueError):
        pressure = 0
    pressure = max(0, min(PRESSURE_MAX, pressure))
    fid = str(faction.get("id") or "").strip() or uid
    return {
        "id": faction_pressure_node_id(uid),
        "kind": "faction_pressure",
        "scope": "world",
        "status": "active",
        "value": pressure,
        "target": PRESSURE_MAX,
        "source_ref": {"root": "factions", "id": fid, "field": "pressure"},
        "tags": [],
        "metadata": {},
    }


def _faction_agenda_node(faction: Mapping[str, Any]) -> Dict[str, Any]:
    uid = _faction_uid(faction)
    try:
        agenda = int(faction.get("agenda_progress", 0) or 0)
    except (TypeError, ValueError):
        agenda = 0
    agenda = max(0, min(AGENDA_PROGRESS_MAX, agenda))
    fid = str(faction.get("id") or "").strip() or uid
    return {
        "id": faction_agenda_node_id(uid),
        "kind": "faction_agenda",
        "scope": "world",
        "status": "active",
        "value": agenda,
        "target": AGENDA_PROGRESS_MAX,
        "source_ref": {"root": "factions", "id": fid, "field": "agenda_progress"},
        "tags": [],
        "metadata": {},
    }


def _world_clock_node(clock_key: str, raw: Any) -> Optional[Dict[str, Any]]:
    canon = coerce_world_state_clock_row(clock_key, raw if isinstance(raw, dict) else {})
    ok, _ = validate_clock(canon)
    if not ok:
        return None
    cid = str(canon.get("id") or "").strip()
    if not cid:
        return None
    meta = canon.get("metadata") if isinstance(canon.get("metadata"), dict) else {}
    return {
        "id": f"world_clock:{cid}",
        "kind": "world_clock",
        "scope": "world",
        "status": "active",
        "value": int(canon.get("value", 0) or 0),
        "target": int(canon.get("max_value", 10) or 10),
        "source_ref": {"root": "world_state.clocks", "id": cid},
        "tags": [],
        "metadata": copy.deepcopy(meta),
    }


def _world_flag_node(flag_key: str, value: Any) -> Optional[Dict[str, Any]]:
    fk = str(flag_key or "").strip()
    if not fk or fk.startswith("_"):
        return None
    return {
        "id": f"world_flag:{fk}",
        "kind": "world_flag",
        "scope": "world",
        "status": _flag_status(value),
        "value": value,
        "target": None,
        "source_ref": {"root": "world_state.flags", "id": fk},
        "tags": [],
        "metadata": {},
    }


def iter_world_progression_nodes(world: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Return normalized progression nodes from native world roots (sorted, deduped by node id)."""
    if not isinstance(world, dict):
        return []
    ensure_defaults(world)  # type: ignore[arg-type]
    nodes: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    projects = world.get("projects") or []
    if isinstance(projects, list):
        for p in projects:
            if not isinstance(p, dict):
                continue
            try:
                canon = normalize_project(adapt_legacy_project(p))
                ok, _ = validate_project(canon)
            except (TypeError, ValueError):
                continue
            if not ok:
                continue
            pid = str(canon.get("id") or "").strip()
            if not pid:
                continue
            row = _project_node(canon)
            nid = str(row["id"])
            if nid in seen_ids:
                continue
            seen_ids.add(nid)
            nodes.append(row)

    factions = world.get("factions") or []
    if isinstance(factions, list):
        for f in factions:
            if not isinstance(f, dict):
                continue
            _ensure_faction_agenda(f)  # type: ignore[arg-type]
            pn = _faction_pressure_node(f)
            an = _faction_agenda_node(f)
            for row in (pn, an):
                nid = str(row["id"])
                if nid in seen_ids:
                    continue
                seen_ids.add(nid)
                nodes.append(row)

    ws = world.get("world_state") or {}
    if isinstance(ws, dict):
        clocks = ws.get("clocks") or {}
        if isinstance(clocks, dict):
            for ck in sorted(clocks.keys(), key=lambda x: str(x)):
                cks = str(ck)
                if not cks.strip() or cks.startswith("_"):
                    continue
                cn = _world_clock_node(cks, clocks.get(ck))
                if cn:
                    nid = str(cn["id"])
                    if nid not in seen_ids:
                        seen_ids.add(nid)
                        nodes.append(cn)
        flags = ws.get("flags") or {}
        if isinstance(flags, dict):
            for fk in sorted(flags.keys(), key=lambda x: str(x)):
                fn = _world_flag_node(str(fk), flags.get(fk))
                if fn:
                    nid = str(fn["id"])
                    if nid not in seen_ids:
                        seen_ids.add(nid)
                        nodes.append(fn)

    nodes.sort(key=lambda n: (str(n.get("kind") or ""), str(n.get("id") or "")))
    return nodes


def get_world_progression_node(world: Mapping[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    parsed = _parse_node_id(node_id)
    if not parsed:
        return None
    kind, _ = parsed
    for n in iter_world_progression_nodes(world):
        if n.get("id") == node_id and n.get("kind") == kind:
            return n
    return None


def _summary_counts(nodes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_kind: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_kind_status: Dict[str, int] = {}
    for n in nodes:
        k = str(n.get("kind") or "")
        s = str(n.get("status") or "")
        by_kind[k] = by_kind.get(k, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        ks = f"{k}|{s}"
        by_kind_status[ks] = by_kind_status.get(ks, 0) + 1
    return {
        "by_kind": dict(sorted(by_kind.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_kind_status": dict(sorted(by_kind_status.items())),
    }


def _recent_progression_facts(world: Mapping[str, Any]) -> List[Dict[str, Any]]:
    log = world.get("event_log") or []
    if not isinstance(log, list):
        return []
    out: List[Dict[str, Any]] = []
    for e in reversed(log):
        if len(out) >= _MAX_RECENT_FACTS:
            break
        if not isinstance(e, dict):
            continue
        et = str(e.get("type") or "")
        if et in _PROGRESSION_EVENT_TYPES:
            out.append(
                {
                    "type": et,
                    "text": str(e.get("text") or ""),
                }
            )
    out.reverse()
    return out


def build_world_progression_snapshot(world: Mapping[str, Any]) -> Dict[str, Any]:
    """Bounded, deterministic snapshot over normalized nodes (no raw world blobs)."""
    all_nodes = iter_world_progression_nodes(world)
    truncated = len(all_nodes) > _MAX_SNAPSHOT_NODES
    nodes = all_nodes[:_MAX_SNAPSHOT_NODES] if truncated else all_nodes
    return {
        "version": 1,
        "nodes": [copy.deepcopy(n) for n in nodes],
        "summary": _summary_counts(nodes),
        "recent_facts": _recent_progression_facts(world),
        "meta": {
            "total_nodes": len(all_nodes),
            "truncated": truncated,
            "node_limit": _MAX_SNAPSHOT_NODES,
        },
    }


def _node_state_token(node: Mapping[str, Any]) -> str:
    kind = str(node.get("kind") or "")
    status = str(node.get("status") or "")
    val = node.get("value")
    tgt = node.get("target")
    if kind == "world_flag":
        return f"{status}|{repr(val)}"
    try:
        vi = int(val) if val is not None else 0
    except (TypeError, ValueError):
        vi = 0
    try:
        ti = int(tgt) if tgt is not None else 0
    except (TypeError, ValueError):
        ti = 0
    return f"{status}|{vi}|{ti}"


def progression_fingerprint_map(world: Mapping[str, Any]) -> Dict[str, str]:
    """Per-node stable state tokens for lightweight before/after diff (no event_log)."""
    fp: Dict[str, str] = {}
    for n in iter_world_progression_nodes(world):
        nid = str(n.get("id") or "").strip()
        if not nid:
            continue
        fp[nid] = _node_state_token(n)
    return fp


def diff_progression_fingerprints(
    prev: Mapping[str, str] | None, curr: Mapping[str, str]
) -> List[str]:
    """Return sorted node ids whose state token changed or appeared (bounded)."""
    if not isinstance(curr, dict) or not curr:
        return []
    if not prev:
        return []
    changed: List[str] = []
    for nid, tok in sorted(curr.items(), key=lambda kv: kv[0]):
        if len(changed) >= _MAX_CTIR_CHANGED_NODES:
            break
        if prev.get(nid) != tok:
            changed.append(nid)
    return changed


def _faction_uid_from_tick_source(source: Any) -> str:
    s = normalize_id(source) if source is not None else ""
    return s or "unknown"


def collect_changed_node_ids_from_resolution_signals(resolution: Mapping[str, Any] | None) -> List[str]:
    """Derive progression node ids from resolution-local signals (not ``world[\"event_log\"]``)."""
    if not isinstance(resolution, dict):
        return []
    out: List[str] = []
    seen: set[str] = set()

    def _add(nid: str) -> None:
        if not nid or nid in seen or len(out) >= _MAX_CTIR_CHANGED_NODES:
            return
        seen.add(nid)
        out.append(nid)

    evs = resolution.get("world_tick_events")
    if isinstance(evs, list):
        for e in evs:
            if not isinstance(e, dict):
                continue
            et = str(e.get("type") or "").strip()
            src = e.get("source")
            uid = _faction_uid_from_tick_source(src)
            if et == "faction_pressure":
                _add(faction_pressure_node_id(uid))
            elif et == "faction_operation_complete":
                _add(faction_agenda_node_id(uid))
            elif et == "project_completed":
                pid = str(e.get("project_id") or e.get("id") or "").strip()
                if pid:
                    _add(f"project:{normalize_id(pid)}")

    def _from_flags(adv: Mapping[str, Any]) -> None:
        sf = adv.get("set_flags")
        if isinstance(sf, dict):
            for k in sorted(sf.keys(), key=lambda x: str(x)):
                ks = str(k).strip()
                if not ks or ks.startswith("_"):
                    continue
                _add(f"world_flag:{ks}")

    def _from_clocks(adv: Mapping[str, Any]) -> None:
        ac = adv.get("advance_clocks")
        if isinstance(ac, dict):
            for name in sorted(ac.keys(), key=lambda x: str(x)):
                nm = str(name).strip()
                if not nm or nm.startswith("_"):
                    continue
                _add(f"world_clock:{nm}")

    _from_flags(resolution)
    _from_clocks(resolution)
    wu = resolution.get("world_updates")
    if isinstance(wu, dict):
        _from_flags(wu)
        _from_clocks(wu)

    return sorted(out)


def merge_progression_changed_node_signals(
    *,
    resolution: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> List[str]:
    """Union resolution-derived hints with optional session fingerprint diff (bounded, sorted)."""
    merged: List[str] = []
    seen: set[str] = set()
    for nid in collect_changed_node_ids_from_resolution_signals(resolution):
        if nid not in seen and len(merged) < _MAX_CTIR_CHANGED_NODES:
            seen.add(nid)
            merged.append(nid)
    if isinstance(session, dict) and isinstance(world, dict):
        prev = session.get(SESSION_PROGRESSION_FINGERPRINT_KEY)
        prev_map = prev if isinstance(prev, dict) else None
        curr = progression_fingerprint_map(world)
        for nid in diff_progression_fingerprints(prev_map, curr):
            if nid not in seen and len(merged) < _MAX_CTIR_CHANGED_NODES:
                seen.add(nid)
                merged.append(nid)
    return sorted(merged)


def store_progression_fingerprint_on_session(session: MutableMapping[str, Any] | None, world: Mapping[str, Any] | None) -> None:
    """Persist post-turn fingerprint for next-turn diffing (transport-only; not a persisted authority root)."""
    if not isinstance(session, MutableMapping) or not isinstance(world, dict):
        return
    session[SESSION_PROGRESSION_FINGERPRINT_KEY] = progression_fingerprint_map(world)


def _compact_project_row(node: Mapping[str, Any]) -> Dict[str, Any]:
    nid = str(node.get("id") or "").strip()
    rest = nid[len("project:") :] if nid.startswith("project:") else nid
    tgt = node.get("target")
    try:
        ti = int(tgt) if tgt is not None else 1
    except (TypeError, ValueError):
        ti = 1
    try:
        vi = int(node.get("value", 0) or 0)
    except (TypeError, ValueError):
        vi = 0
    return {
        "id": rest or nid,
        "status": str(node.get("status") or "active"),
        "progress": vi,
        "target": max(1, ti),
    }


def _compact_faction_pressure_row(node: Mapping[str, Any]) -> Dict[str, Any]:
    nid = str(node.get("id") or "").strip()
    rest = nid[len("faction_pressure:") :] if nid.startswith("faction_pressure:") else nid
    try:
        vi = int(node.get("value", 0) or 0)
    except (TypeError, ValueError):
        vi = 0
    return {"id": rest or nid, "value": vi, "status": str(node.get("status") or "active")}


def _compact_faction_agenda_row(node: Mapping[str, Any]) -> Dict[str, Any]:
    nid = str(node.get("id") or "").strip()
    rest = nid[len("faction_agenda:") :] if nid.startswith("faction_agenda:") else nid
    try:
        vi = int(node.get("value", 0) or 0)
    except (TypeError, ValueError):
        vi = 0
    return {"id": rest or nid, "value": vi, "status": str(node.get("status") or "active")}


def _compact_world_clock_row(node: Mapping[str, Any]) -> Dict[str, Any]:
    nid = str(node.get("id") or "").strip()
    rest = nid[len("world_clock:") :] if nid.startswith("world_clock:") else nid
    try:
        vi = int(node.get("value", 0) or 0)
    except (TypeError, ValueError):
        vi = 0
    try:
        ti = int(node.get("target", 0) or 0)
    except (TypeError, ValueError):
        ti = 0
    return {
        "id": rest or nid,
        "value": vi,
        "target": max(1, ti),
        "status": str(node.get("status") or "active"),
    }


def _compact_world_flag_row(node: Mapping[str, Any]) -> Dict[str, Any]:
    nid = str(node.get("id") or "").strip()
    rest = nid[len("world_flag:") :] if nid.startswith("world_flag:") else nid
    st = str(node.get("status") or "unset")
    row: Dict[str, Any] = {"id": rest or nid, "status": st}
    if st == "set" and node.get("value") is not None and node.get("value") is not False:
        v = node.get("value")
        if isinstance(v, (bool, int, float, str)):
            row["value"] = v
    return row


def compose_ctir_world_progression_slice(
    world: Mapping[str, Any] | None,
    *,
    changed_node_ids: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """Bounded CTIR ``world.progression`` slice from backbone nodes (no event_log, no raw world blobs)."""
    nodes = iter_world_progression_nodes(world) if isinstance(world, dict) else []
    active_projects: List[Dict[str, Any]] = []
    faction_pressure: List[Dict[str, Any]] = []
    faction_agenda: List[Dict[str, Any]] = []
    world_clocks: List[Dict[str, Any]] = []
    set_flags: List[Dict[str, Any]] = []
    for n in nodes:
        k = str(n.get("kind") or "")
        if k == "project":
            st = str(n.get("status") or "").lower()
            if st == "active" and len(active_projects) < _MAX_CTIR_ACTIVE_PROJECTS:
                active_projects.append(_compact_project_row(n))
        elif k == "faction_pressure" and len(faction_pressure) < _MAX_CTIR_FACTION_PRESSURE:
            faction_pressure.append(_compact_faction_pressure_row(n))
        elif k == "faction_agenda" and len(faction_agenda) < _MAX_CTIR_FACTION_AGENDA:
            faction_agenda.append(_compact_faction_agenda_row(n))
        elif k == "world_clock" and len(world_clocks) < _MAX_CTIR_WORLD_CLOCKS:
            world_clocks.append(_compact_world_clock_row(n))
        elif k == "world_flag" and len(set_flags) < _MAX_CTIR_SET_FLAGS:
            row = _compact_world_flag_row(n)
            if row.get("status") == "set":
                set_flags.append(row)
    ch = [str(x).strip() for x in (changed_node_ids or []) if str(x).strip()]
    ch = sorted(set(ch))[:_MAX_CTIR_CHANGED_NODES]
    return {
        "changed_node_ids": ch,
        "active_projects": active_projects,
        "faction_pressure": faction_pressure,
        "faction_agenda": faction_agenda,
        "world_clocks": world_clocks,
        "set_flags": set_flags,
    }


def build_prompt_world_progression_hints(
    progression: Mapping[str, Any] | None,
    *,
    max_lines: int = 12,
) -> List[str]:
    """Short, stable summary lines from a CTIR-style progression dict (read-only transport)."""
    if not isinstance(progression, dict):
        return []
    lines: List[str] = []
    ch = progression.get("changed_node_ids")
    if isinstance(ch, list) and ch:
        tail = ", ".join(str(x) for x in ch[:8] if str(x).strip())
        if tail:
            lines.append(f"World progression touched: {tail}")
    for p in progression.get("active_projects") or []:
        if not isinstance(p, dict) or len(lines) >= max_lines:
            break
        pid = str(p.get("id") or "").strip()
        if not pid:
            continue
        try:
            pr = int(p.get("progress", 0) or 0)
            tg = int(p.get("target", 1) or 1)
        except (TypeError, ValueError):
            continue
        lines.append(f"Active project {pid}: {pr}/{tg} ({p.get('status')})")
    for row in progression.get("faction_pressure") or []:
        if not isinstance(row, dict) or len(lines) >= max_lines:
            break
        fid = str(row.get("id") or "").strip()
        if fid:
            lines.append(f"Faction pressure {fid}: {row.get('value', 0)}")
    for row in progression.get("faction_agenda") or []:
        if not isinstance(row, dict) or len(lines) >= max_lines:
            break
        fid = str(row.get("id") or "").strip()
        if fid:
            lines.append(f"Faction agenda {fid}: {row.get('value', 0)}")
    for row in progression.get("world_clocks") or []:
        if not isinstance(row, dict) or len(lines) >= max_lines:
            break
        cid = str(row.get("id") or "").strip()
        if cid:
            lines.append(f"World clock {cid}: {row.get('value', 0)}/{row.get('target', 0)}")
    for row in progression.get("set_flags") or []:
        if not isinstance(row, dict) or len(lines) >= max_lines:
            break
        fk = str(row.get("id") or "").strip()
        if fk and row.get("status") == "set":
            lines.append(f"World flag {fk}: set")
    return lines[:max_lines]


def _find_faction(world: Dict[str, Any], uid: str) -> Optional[Dict[str, Any]]:
    factions = world.get("factions") or []
    if not isinstance(factions, list):
        return None
    for f in factions:
        if not isinstance(f, dict):
            continue
        if _faction_uid(f) == uid:
            return f
    return None


def _advance_project(world: Dict[str, Any], pid: str, amount: int, reason: Optional[str], event_log: Optional[List]) -> Dict[str, Any]:
    projects = world.setdefault("projects", [])
    if not isinstance(projects, list):
        world["projects"] = []
        projects = world["projects"]
    node_id = f"project:{pid}"
    for i, p in enumerate(projects):
        if not isinstance(p, dict):
            continue
        if str(p.get("id") or "").strip() != pid:
            continue
        try:
            canon = normalize_project(adapt_legacy_project(p))
            ok, reasons = validate_project(canon)
        except (TypeError, ValueError):
            return {"ok": False, "errors": ["invalid_project:normalize_failed"], "node_id": node_id}
        if not ok:
            return {"ok": False, "errors": [f"invalid_project:{reasons[0] if reasons else 'unknown'}"], "node_id": node_id}
        tgt = max(1, int(canon.get("target") or 1))
        prog = int(canon.get("progress", 0) or 0) + int(amount)
        prog = max(0, min(tgt, prog))
        canon["progress"] = prog
        canon["target"] = tgt
        if prog >= tgt:
            canon["status"] = "complete"
        projects[i] = canon
        ev = progression_event(
            operation="advance",
            node_id=node_id,
            node_kind="project",
            text=f"Project progress {pid} -> {prog}/{tgt}",
            reason=reason,
        )
        _append_log(world, event_log, ev)
        return {"ok": True, "node": _project_node(canon), "event": ev}
    return {"ok": False, "errors": ["project_not_found"], "node_id": node_id}


def _set_project(world: Dict[str, Any], pid: str, value: Any, reason: Optional[str], event_log: Optional[List]) -> Dict[str, Any]:
    projects = world.setdefault("projects", [])
    if not isinstance(projects, list):
        world["projects"] = []
        projects = world["projects"]
    node_id = f"project:{pid}"
    try:
        v = int(value)
    except (TypeError, ValueError):
        return {"ok": False, "errors": ["project_value_not_int"], "node_id": node_id}
    for i, p in enumerate(projects):
        if not isinstance(p, dict):
            continue
        if str(p.get("id") or "").strip() != pid:
            continue
        try:
            canon = normalize_project(adapt_legacy_project(p))
            ok, reasons = validate_project(canon)
        except (TypeError, ValueError):
            return {"ok": False, "errors": ["invalid_project:normalize_failed"], "node_id": node_id}
        if not ok:
            return {"ok": False, "errors": [f"invalid_project:{reasons[0] if reasons else 'unknown'}"], "node_id": node_id}
        tgt = max(1, int(canon.get("target") or 1))
        prog = max(0, min(tgt, v))
        canon["progress"] = prog
        canon["target"] = tgt
        if prog >= tgt:
            canon["status"] = "complete"
        projects[i] = canon
        ev = progression_event(
            operation="set_value",
            node_id=node_id,
            node_kind="project",
            text=f"Project progress {pid} set to {prog}/{tgt}",
            reason=reason,
        )
        _append_log(world, event_log, ev)
        return {"ok": True, "node": _project_node(canon), "event": ev}
    return {"ok": False, "errors": ["project_not_found"], "node_id": node_id}


def _advance_faction_field(
    world: Dict[str, Any],
    uid: str,
    field: str,
    cap: int,
    node_kind: str,
    amount: int,
    reason: Optional[str],
    event_log: Optional[List],
) -> Dict[str, Any]:
    node_id = faction_pressure_node_id(uid) if field == "pressure" else faction_agenda_node_id(uid)
    fac = _find_faction(world, uid)
    if not fac:
        return {"ok": False, "errors": ["faction_not_found"], "node_id": node_id}
    _ensure_faction_agenda(fac)
    try:
        cur = int(fac.get(field, 0) or 0)
    except (TypeError, ValueError):
        cur = 0
    new_v = max(0, min(cap, cur + int(amount)))
    fac[field] = new_v
    ev = progression_event(
        operation="advance",
        node_id=node_id,
        node_kind=node_kind,
        text=f"{node_kind} {uid} -> {new_v}",
        reason=reason,
    )
    _append_log(world, event_log, ev)
    node = _faction_pressure_node(fac) if field == "pressure" else _faction_agenda_node(fac)
    return {"ok": True, "node": node, "event": ev}


def _set_faction_field(
    world: Dict[str, Any],
    uid: str,
    field: str,
    cap: int,
    node_kind: str,
    value: Any,
    reason: Optional[str],
    event_log: Optional[List],
) -> Dict[str, Any]:
    node_id = faction_pressure_node_id(uid) if field == "pressure" else faction_agenda_node_id(uid)
    fac = _find_faction(world, uid)
    if not fac:
        return {"ok": False, "errors": ["faction_not_found"], "node_id": node_id}
    _ensure_faction_agenda(fac)
    try:
        v = int(value)
    except (TypeError, ValueError):
        return {"ok": False, "errors": ["faction_value_not_int"], "node_id": node_id}
    new_v = max(0, min(cap, v))
    fac[field] = new_v
    ev = progression_event(
        operation="set_value",
        node_id=node_id,
        node_kind=node_kind,
        text=f"{node_kind} {uid} set to {new_v}",
        reason=reason,
    )
    _append_log(world, event_log, ev)
    node = _faction_pressure_node(fac) if field == "pressure" else _faction_agenda_node(fac)
    return {"ok": True, "node": node, "event": ev}


def _advance_world_clock(
    world: Dict[str, Any], cid: str, amount: int, reason: Optional[str], event_log: Optional[List]
) -> Dict[str, Any]:
    ensure_defaults(world)
    ws = world["world_state"]
    if not isinstance(ws, dict):
        return {"ok": False, "errors": ["world_state_invalid"], "node_id": f"world_clock:{cid}"}
    clocks = ws.setdefault("clocks", {})
    if not isinstance(clocks, dict):
        ws["clocks"] = {}
        clocks = ws["clocks"]
    raw = clocks.get(cid)
    if raw is None:
        raw = {}
    canon = coerce_world_state_clock_row(cid, raw if isinstance(raw, dict) else {})
    ok, reasons = validate_clock(canon)
    if not ok:
        return {"ok": False, "errors": [f"invalid_clock:{reasons[0] if reasons else 'unknown'}"], "node_id": f"world_clock:{cid}"}
    lo = int(canon.get("min_value", 0) or 0)
    hi = int(canon.get("max_value", 10) or 10)
    val = int(canon.get("value", 0) or 0) + int(amount)
    val = max(lo, min(hi, val))
    canon["value"] = val
    clocks[str(canon["id"])] = canon
    node_id = f"world_clock:{cid}"
    ev = progression_event(
        operation="advance",
        node_id=node_id,
        node_kind="world_clock",
        text=f"Clock {cid} -> {val}/{hi}",
        reason=reason,
    )
    _append_log(world, event_log, ev)
    return {"ok": True, "node": _world_clock_node(cid, canon), "event": ev}


def _set_world_clock(
    world: Dict[str, Any], cid: str, value: Any, reason: Optional[str], event_log: Optional[List]
) -> Dict[str, Any]:
    ensure_defaults(world)
    ws = world["world_state"]
    if not isinstance(ws, dict):
        return {"ok": False, "errors": ["world_state_invalid"], "node_id": f"world_clock:{cid}"}
    clocks = ws.setdefault("clocks", {})
    if not isinstance(clocks, dict):
        ws["clocks"] = {}
        clocks = ws["clocks"]
    raw = clocks.get(cid)
    if raw is None:
        raw = {}
    work = adapt_legacy_clock(dict(raw) if isinstance(raw, dict) else {})
    if not normalize_id(work.get("id")):
        work["id"] = cid
    if not str(work.get("scope") or "").strip():
        work["scope"] = "world"
    try:
        work["value"] = int(value)
    except (TypeError, ValueError):
        return {"ok": False, "errors": ["clock_value_not_int"], "node_id": f"world_clock:{cid}"}
    canon = normalize_clock(work)
    ok, reasons = validate_clock(canon)
    if not ok:
        return {"ok": False, "errors": [f"invalid_clock:{reasons[0] if reasons else 'unknown'}"], "node_id": f"world_clock:{cid}"}
    lo = int(canon.get("min_value", 0) or 0)
    hi = int(canon.get("max_value", 10) or 10)
    val = max(lo, min(hi, int(canon.get("value", 0) or 0)))
    canon["value"] = val
    clocks[str(canon["id"])] = canon
    node_id = f"world_clock:{cid}"
    ev = progression_event(
        operation="set_value",
        node_id=node_id,
        node_kind="world_clock",
        text=f"Clock {cid} set to {val}/{hi}",
        reason=reason,
    )
    _append_log(world, event_log, ev)
    return {"ok": True, "node": _world_clock_node(cid, canon), "event": ev}


def _set_world_flag(
    world: Dict[str, Any], fk: str, value: Any, reason: Optional[str], event_log: Optional[List]
) -> Dict[str, Any]:
    ensure_defaults(world)
    ws = world["world_state"]
    if not isinstance(ws, dict):
        return {"ok": False, "errors": ["world_state_invalid"], "node_id": f"world_flag:{fk}"}
    flags = ws.setdefault("flags", {})
    if not isinstance(flags, dict):
        ws["flags"] = {}
        flags = ws["flags"]
    node_id = f"world_flag:{fk}"
    if not fk or fk.startswith("_"):
        return {"ok": False, "errors": ["invalid_flag_key"], "node_id": node_id}
    if value is False or value is None:
        flags.pop(fk, None)
        display_val: Any = None
    else:
        flags[fk] = value
        display_val = flags.get(fk)
    ev = progression_event(
        operation="set_value",
        node_id=node_id,
        node_kind="world_flag",
        text=f"Flag {fk} updated",
        reason=reason,
    )
    _append_log(world, event_log, ev)
    fn = _world_flag_node(fk, display_val)
    if not fn:
        return {"ok": False, "errors": ["invalid_flag_key"], "node_id": node_id}
    return {"ok": True, "node": fn, "event": ev}


def _advance_dispatch(
    world: Dict[str, Any], kind: str, rest: str, amount: int, reason: Optional[str], event_log: Optional[List]
) -> Dict[str, Any]:
    if kind == "project":
        return _advance_project(world, rest, amount, reason, event_log)
    if kind == "faction_pressure":
        return _advance_faction_field(world, rest, "pressure", PRESSURE_MAX, "faction_pressure", amount, reason, event_log)
    if kind == "faction_agenda":
        return _advance_faction_field(world, rest, "agenda_progress", AGENDA_PROGRESS_MAX, "faction_agenda", amount, reason, event_log)
    if kind == "world_clock":
        return _advance_world_clock(world, rest, amount, reason, event_log)
    if kind == "world_flag":
        return {"ok": False, "errors": ["advance_not_supported_for_world_flag"], "node_id": f"world_flag:{rest}"}
    return {"ok": False, "errors": ["unknown_kind"], "node_id": ""}


def _set_dispatch(
    world: Dict[str, Any], kind: str, rest: str, value: Any, reason: Optional[str], event_log: Optional[List]
) -> Dict[str, Any]:
    if kind == "project":
        return _set_project(world, rest, value, reason, event_log)
    if kind == "faction_pressure":
        return _set_faction_field(world, rest, "pressure", PRESSURE_MAX, "faction_pressure", value, reason, event_log)
    if kind == "faction_agenda":
        return _set_faction_field(world, rest, "agenda_progress", AGENDA_PROGRESS_MAX, "faction_agenda", value, reason, event_log)
    if kind == "world_clock":
        return _set_world_clock(world, rest, value, reason, event_log)
    if kind == "world_flag":
        return _set_world_flag(world, rest, value, reason, event_log)
    return {"ok": False, "errors": ["unknown_kind"], "node_id": ""}


def advance_progression_node(
    world: Dict[str, Any],
    node_id: str,
    amount: int = 1,
    *,
    reason: Optional[str] = None,
    event_log: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Advance a single node; mutates native roots. Returns updated node dict or None on failure."""
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="advance_progression_node")
    parsed = _parse_node_id(node_id)
    if not parsed:
        return None
    kind, rest = parsed
    res = _advance_dispatch(world, kind, rest, amount, reason, event_log)
    if not res.get("ok"):
        return None
    return res.get("node") if isinstance(res.get("node"), dict) else None


def set_progression_node_value(
    world: Dict[str, Any],
    node_id: str,
    value: Any,
    *,
    reason: Optional[str] = None,
    event_log: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="set_progression_node_value")
    parsed = _parse_node_id(node_id)
    if not parsed:
        return None
    kind, rest = parsed
    res = _set_dispatch(world, kind, rest, value, reason, event_log)
    if not res.get("ok"):
        return None
    return res.get("node") if isinstance(res.get("node"), dict) else None


def apply_progression_delta(
    world: Dict[str, Any],
    delta: Mapping[str, Any],
    *,
    event_log: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Apply a list of operations through the backbone seam. Deterministic, no shadow stores."""
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="apply_progression_delta")
    ensure_defaults(world)
    if not isinstance(delta, dict):
        return {"ok": False, "errors": ["delta_not_dict"], "applied": [], "failed": []}
    ops = delta.get("ops")
    if not isinstance(ops, list):
        return {"ok": False, "errors": ["missing_ops_list"], "applied": [], "failed": []}
    applied: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            failed.append({"index": i, "errors": ["op_not_dict"]})
            continue
        name = str(op.get("op") or "").strip().lower()
        nid = str(op.get("node_id") or "").strip()
        parsed = _parse_node_id(nid)
        if not parsed:
            failed.append({"index": i, "node_id": nid, "errors": ["invalid_node_id"]})
            continue
        kind, rest = parsed
        if name == "advance":
            amt = op.get("amount", 1)
            try:
                amt_i = int(amt)
            except (TypeError, ValueError):
                failed.append({"index": i, "node_id": nid, "errors": ["amount_not_int"]})
                continue
            res = _advance_dispatch(world, kind, rest, amt_i, op.get("reason") if isinstance(op.get("reason"), str) else None, event_log)
        elif name == "set_value":
            res = _set_dispatch(
                world,
                kind,
                rest,
                op.get("value"),
                op.get("reason") if isinstance(op.get("reason"), str) else None,
                event_log,
            )
        else:
            failed.append({"index": i, "node_id": nid, "errors": [f"unknown_op:{name}"]})
            continue
        if res.get("ok"):
            applied.append({"index": i, "node_id": nid, "op": name})
        else:
            failed.append({"index": i, "node_id": nid, "errors": res.get("errors") or ["apply_failed"]})
    return {
        "ok": len(failed) == 0,
        "applied": applied,
        "failed": failed,
    }
