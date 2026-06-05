"""Snapshot-only transcript helpers.

This module intentionally avoids the live API/GPT stack so evaluator/boundary
tests can collect without live API config.
"""

from __future__ import annotations

from typing import Any

from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output
from game.interaction_context import inspect as inspect_interaction_context
from game.narrative_authenticity_eval import _extract_final_emission_meta


def _journal_summary(journal: Any) -> dict[str, Any]:
    if not isinstance(journal, dict):
        return {}
    kf = journal.get("known_facts")
    dc = journal.get("discovered_clues")
    revents = journal.get("recent_events")
    return {
        "known_facts_count": len(kf) if isinstance(kf, list) else 0,
        "discovered_clues_count": len(dc) if isinstance(dc, list) else 0,
        "recent_events_count": len(revents) if isinstance(revents, list) else 0,
        "recent_events_tail": (revents[-5:] if isinstance(revents, list) else []),
    }


def _world_summary(world: Any) -> dict[str, Any]:
    if not isinstance(world, dict):
        return {}
    ws = world.get("world_state") if isinstance(world.get("world_state"), dict) else {}
    flags = ws.get("flags") if isinstance(ws.get("flags"), dict) else {}
    ev = world.get("event_log") if isinstance(world.get("event_log"), list) else []
    proj = world.get("projects") if isinstance(world.get("projects"), list) else []
    out: dict[str, Any] = {
        "event_log_count": len(ev),
        "projects_count": len(proj),
        "flag_keys": sorted(flags.keys()),
    }
    try:
        from game.world_progression import compose_ctir_world_progression_slice

        _pe = compose_ctir_world_progression_slice(world, changed_node_ids=())
        out["progression_row_counts"] = {
            "active_projects": len(_pe.get("active_projects") or []),
            "faction_pressure": len(_pe.get("faction_pressure") or []),
            "faction_agenda": len(_pe.get("faction_agenda") or []),
            "world_clocks": len(_pe.get("world_clocks") or []),
            "set_flags": len(_pe.get("set_flags") or []),
        }
    except Exception:
        pass
    return out


def _compact_resolution(res: Any) -> dict[str, Any] | None:
    if not isinstance(res, dict):
        return None
    keys = (
        "kind",
        "action_id",
        "label",
        "success",
        "resolved_transition",
        "target_scene_id",
        "social",
        "requires_check",
        "adjudication",
    )
    out = {k: res[k] for k in keys if k in res}
    return out or None


def snapshot_from_chat_payload(
    turn_index: int, player_text: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Build a single turn snapshot from ``chat``'s return payload shape."""
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    gm_text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    fem = _extract_final_emission_meta(payload) or {}

    scene = payload.get("scene") if isinstance(payload.get("scene"), dict) else {}
    scene_inner = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
    scene_id = str(scene_inner.get("id") or "").strip() or None

    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    scene_state = session.get("scene_state") if isinstance(session.get("scene_state"), dict) else {}
    raw_interlocutor = scene_state.get("current_interlocutor")
    current_interlocutor: str | None
    if raw_interlocutor is None or raw_interlocutor == "":
        current_interlocutor = None
    else:
        current_interlocutor = str(raw_interlocutor).strip() or None

    ic = inspect_interaction_context(session)
    resolution = payload.get("resolution")
    social = (
        resolution.get("social")
        if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict)
        else None
    )

    journal = payload.get("journal")
    world = payload.get("world")
    event_log = (
        world.get("event_log")
        if isinstance(world, dict) and isinstance(world.get("event_log"), list)
        else []
    )

    traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []

    return {
        "turn_index": turn_index,
        "player_text": player_text,
        "gm_text": gm_text,
        "_final_emission_meta": fem,
        "scene_id": scene_id,
        "current_interlocutor": current_interlocutor,
        "interaction_context": dict(ic),
        "social_resolution": social,
        "journal_state": _journal_summary(journal),
        "world_state": _world_summary(world),
        "event_log": {"count": len(event_log), "tail": event_log[-8:]},
        "debug": {
            "last_action_debug": session.get("last_action_debug"),
            "last_debug_trace": traces[-1] if traces else None,
            "resolution_compact": _compact_resolution(resolution),
        },
    }


def compact_snapshot_summary(snap: dict[str, Any], *, gm_chars: int = 120) -> str:
    """One-line-ish summary for assertions and failure messages."""
    gm = str(snap.get("gm_text") or "")
    if len(gm) > gm_chars:
        gm = gm[: gm_chars - 3] + "..."
    tgt = latest_target_id(snap) or "-"
    src = latest_target_source(snap) or "-"
    fem = final_emission_meta_from_output(snap)
    dt = fem.get("dead_turn") if isinstance(fem.get("dead_turn"), dict) else {}
    dead_hint = ""
    if dt.get("is_dead_turn"):
        cls = dt.get("dead_turn_class")
        dead_hint = f" dead_turn_class={cls!r}"
    return (
        f"t{snap.get('turn_index')!r} scene={snap.get('scene_id')!r} "
        f"interlocutor={snap.get('current_interlocutor')!r} "
        f"target={tgt!r}({src}) gm={gm!r}{dead_hint}"
    )


def latest_target_id(snap: dict[str, Any]) -> str | None:
    """Best-effort resolved target id from interaction context, social resolution, or action debug."""
    ctx = snap.get("interaction_context") if isinstance(snap.get("interaction_context"), dict) else {}
    tid = str(ctx.get("active_interaction_target_id") or "").strip()
    if tid:
        return tid
    soc = snap.get("social_resolution") if isinstance(snap.get("social_resolution"), dict) else {}
    for key in ("target_id", "npc_id", "resolved_target_id"):
        v = soc.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    dbg = snap.get("debug") if isinstance(snap.get("debug"), dict) else {}
    lad = dbg.get("last_action_debug") if isinstance(dbg.get("last_action_debug"), dict) else {}
    na = lad.get("normalized_action") if isinstance(lad.get("normalized_action"), dict) else {}
    for key in ("targetEntityId", "target_id", "targetSceneId"):
        v = na.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def latest_target_source(snap: dict[str, Any]) -> str | None:
    """Where :func:`latest_target_id` found its value, or None."""
    ctx = snap.get("interaction_context") if isinstance(snap.get("interaction_context"), dict) else {}
    if str(ctx.get("active_interaction_target_id") or "").strip():
        return "interaction_context.active_interaction_target_id"
    soc = snap.get("social_resolution") if isinstance(snap.get("social_resolution"), dict) else {}
    for key in ("target_id", "npc_id", "resolved_target_id"):
        v = soc.get(key)
        if isinstance(v, str) and v.strip():
            return f"social_resolution.{key}"
    dbg = snap.get("debug") if isinstance(snap.get("debug"), dict) else {}
    lad = dbg.get("last_action_debug") if isinstance(dbg.get("last_action_debug"), dict) else {}
    na = lad.get("normalized_action") if isinstance(lad.get("normalized_action"), dict) else {}
    for key in ("targetEntityId", "target_id", "targetSceneId"):
        v = na.get(key)
        if isinstance(v, str) and v.strip():
            return f"last_action_debug.normalized_action.{key}"
    return None


def format_turn_debug(snap: dict[str, Any], *, gm_chars: int = 200) -> str:
    """Multi-line block for printing when a transcript assertion fails."""
    gm = str(snap.get("gm_text") or "")
    if len(gm) > gm_chars:
        gm = gm[: gm_chars - 3] + "..."
    lines = [
        f"turn_index: {snap.get('turn_index')}",
        f"player_text: {snap.get('player_text')!r}",
        f"gm_excerpt: {gm!r}",
        f"scene_id: {snap.get('scene_id')!r}",
        f"current_interlocutor: {snap.get('current_interlocutor')!r}",
        f"latest_target_id: {latest_target_id(snap)!r}",
        f"latest_target_source: {latest_target_source(snap)!r}",
    ]
    return "\n".join(lines)
