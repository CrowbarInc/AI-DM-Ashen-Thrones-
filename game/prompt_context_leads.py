"""Lead/interlocutor prompt-context helpers extracted from prompt_context."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from game.leads import (
    effective_lead_pressure_score,
    get_lead,
    is_lead_terminal,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    list_session_leads,
)
from game.social import (
    _social_turn_counter,
    list_recent_npc_lead_discussions,
)


INTERLOCUTOR_DISCUSSION_RECENCY_WINDOW = 2


def _prompt_context_attr(name: str, fallback: Any) -> Any:
    try:
        from game import prompt_context as prompt_context_module
    except Exception:
        return fallback
    return getattr(prompt_context_module, name, fallback)

def _lead_get(lead: Any, key: str, default: Any = None) -> Any:
    """Read a lead field from a mapping or object without mutating the lead."""
    if isinstance(lead, Mapping):
        return lead.get(key, default)
    return getattr(lead, key, default)


def _lead_status_value(lead: Any) -> str:
    raw = _lead_get(lead, "status")
    if isinstance(raw, LeadStatus):
        return raw.value
    s = str(raw or "").strip().lower()
    return s


def _lead_lifecycle_value(lead: Any) -> str:
    raw = _lead_get(lead, "lifecycle")
    if isinstance(raw, LeadLifecycle):
        return raw.value
    return str(raw or "").strip().lower()


def _lead_int(lead: Any, key: str, *, default: int = 0) -> int:
    v = _lead_get(lead, key, default)
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _lead_type_value(lead: Any) -> str:
    raw = _lead_get(lead, "type")
    if isinstance(raw, LeadType):
        return raw.value
    return str(raw or "").strip().lower()


def _lead_pressure_sort_key(lead: Any, current_turn: int) -> tuple[Any, ...]:
    pres = effective_lead_pressure_score(lead, current_turn)
    lu = _lead_int(lead, "last_updated_turn", default=0)
    lt = _lead_int(lead, "last_touched_turn", default=0)
    title = _lead_get(lead, "title") or ""
    lid = _lead_get(lead, "id") or ""
    tie = str(title).strip() or str(lid).strip() or ""
    return (-pres, -lu, -lt, tie)


def _recent_change_signal_rank(lead: Any, current_turn: int) -> int:
    """Higher = more preferred for recent_lead_changes when inferable from reconciled fields this turn."""
    if current_turn <= 0:
        return 0
    if _lead_int(lead, "escalated_at_turn", default=-1) == current_turn:
        return 4
    lu = _lead_int(lead, "last_updated_turn", default=-1)
    if lu != current_turn:
        return 0
    if str(_lead_get(lead, "unlocked_by_lead_id") or "").strip():
        return 3
    if _lead_status_value(lead) == LeadStatus.STALE.value:
        return 2
    if _lead_lifecycle_value(lead) == LeadLifecycle.OBSOLETE.value:
        return 1
    return 0


def _recent_lead_changes_sort_key(lead: Any, current_turn: int) -> tuple[Any, ...]:
    sig = _recent_change_signal_rank(lead, current_turn)
    lu = _lead_int(lead, "last_updated_turn", default=0)
    pres = effective_lead_pressure_score(lead, current_turn)
    title = _lead_get(lead, "title") or ""
    lid = _lead_get(lead, "id") or ""
    tie = str(title).strip() or str(lid).strip() or ""
    return (-sig, -lu, -pres, tie)


def _compact_lead_row(lead: Any) -> Dict[str, Any]:
    rel_npc = _lead_get(lead, "related_npc_ids")
    if not isinstance(rel_npc, list):
        rel_npc = []
    rel_loc = _lead_get(lead, "related_location_ids")
    if not isinstance(rel_loc, list):
        rel_loc = []
    meta = _lead_get(lead, "metadata")
    meta_map: Mapping[str, Any] = meta if isinstance(meta, Mapping) else {}
    effects_raw = meta_map.get("last_progression_effects")
    last_progression_effects: List[Any] | None
    if isinstance(effects_raw, list):
        last_progression_effects = list(effects_raw)
    else:
        last_progression_effects = None
    return {
        "id": _lead_get(lead, "id"),
        "title": _lead_get(lead, "title"),
        "summary": _lead_get(lead, "summary"),
        "type": _lead_get(lead, "type"),
        "status": _lead_get(lead, "status"),
        "lifecycle": _lead_get(lead, "lifecycle"),
        "confidence": _lead_get(lead, "confidence"),
        "priority": _lead_int(lead, "priority", default=0),
        "next_step": _lead_get(lead, "next_step"),
        "last_updated_turn": _lead_get(lead, "last_updated_turn"),
        "last_touched_turn": _lead_get(lead, "last_touched_turn"),
        "related_npc_ids": rel_npc,
        "related_location_ids": rel_loc,
        "escalation_level": _lead_int(lead, "escalation_level", default=0),
        "escalation_reason": _lead_get(lead, "escalation_reason"),
        "escalated_at_turn": _lead_get(lead, "escalated_at_turn"),
        "unlocked_by_lead_id": _lead_get(lead, "unlocked_by_lead_id"),
        "obsolete_by_lead_id": _lead_get(lead, "obsolete_by_lead_id"),
        "superseded_by": _lead_get(lead, "superseded_by"),
        "stale_after_turns": _lead_get(lead, "stale_after_turns"),
        "last_transition_reason": meta_map.get("last_transition_reason"),
        "last_transition_category": meta_map.get("last_transition_category"),
        "last_transition_turn": meta_map.get("last_transition_turn"),
        "last_transition_from_lifecycle": meta_map.get("last_transition_from_lifecycle"),
        "last_transition_to_lifecycle": meta_map.get("last_transition_to_lifecycle"),
        "last_transition_from_status": meta_map.get("last_transition_from_status"),
        "last_transition_to_status": meta_map.get("last_transition_to_status"),
        "last_progression_effects": last_progression_effects,
    }


def build_authoritative_lead_prompt_context(
    session: Any,
    world: Any,
    public_scene: Any,
    runtime: Any,
    recent_log: Any,
    active_npc_id: str | None = None,
) -> Dict[str, Any]:
    """Deterministic, registry-only lead slice for prompts (read-only; no journal, no session mutation)."""
    _ = (world, public_scene, runtime, recent_log)
    list_session_leads_fn = _prompt_context_attr("list_session_leads", list_session_leads)
    is_lead_terminal_fn = _prompt_context_attr("is_lead_terminal", is_lead_terminal)
    effective_pressure_fn = _prompt_context_attr("effective_lead_pressure_score", effective_lead_pressure_score)
    lead_get = _prompt_context_attr("_lead_get", _lead_get)
    lead_status_value = _prompt_context_attr("_lead_status_value", _lead_status_value)
    lead_lifecycle_value = _prompt_context_attr("_lead_lifecycle_value", _lead_lifecycle_value)
    lead_int = _prompt_context_attr("_lead_int", _lead_int)
    lead_type_value = _prompt_context_attr("_lead_type_value", _lead_type_value)
    lead_pressure_sort_key = _prompt_context_attr("_lead_pressure_sort_key", _lead_pressure_sort_key)
    recent_lead_changes_sort_key = _prompt_context_attr("_recent_lead_changes_sort_key", _recent_lead_changes_sort_key)
    compact_lead_row = _prompt_context_attr("_compact_lead_row", _compact_lead_row)

    if isinstance(session, Mapping):
        leads = list_session_leads_fn(session, include_terminal=True)
    else:
        leads = []

    empty_pressure = {
        "has_pursued": False,
        "has_stale": False,
        "npc_has_relevant": False,
        "has_escalated_threat": False,
        "has_newly_unlocked": False,
        "has_supersession_cleanup": False,
    }
    if not leads:
        return {
            "top_active_leads": [],
            "currently_pursued_lead": None,
            "urgent_or_stale_leads": [],
            "recent_lead_changes": [],
            "npc_relevant_leads": [],
            "follow_up_pressure_from_leads": empty_pressure,
        }

    current_turn = lead_int(session, "turn_counter", default=0) if isinstance(session, Mapping) else 0

    active_vals = (LeadStatus.ACTIVE.value, LeadStatus.PURSUED.value)
    active_like = [
        l
        for l in leads
        if lead_status_value(l) in active_vals and not is_lead_terminal_fn(l)
    ]
    pursued = [
        l
        for l in leads
        if lead_status_value(l) == LeadStatus.PURSUED.value and not is_lead_terminal_fn(l)
    ]
    stale = [l for l in leads if lead_status_value(l) == LeadStatus.STALE.value and not is_lead_terminal_fn(l)]

    active_like_sorted = sorted(active_like, key=lambda l: lead_pressure_sort_key(l, current_turn))
    pursued_sorted = sorted(pursued, key=lambda l: lead_pressure_sort_key(l, current_turn))

    top_active_leads = [compact_lead_row(l) for l in active_like_sorted[:3]]
    currently_pursued_lead = compact_lead_row(pursued_sorted[0]) if pursued_sorted else None

    def _not_recently_touched(lead: Any) -> bool:
        raw = lead_get(lead, "last_touched_turn")
        if raw is None:
            return True
        touched = lead_int(lead, "last_touched_turn", default=-1)
        if touched < 0:
            return True
        return current_turn - touched >= 2

    stale_sorted = sorted(stale, key=lambda l: lead_pressure_sort_key(l, current_turn))
    threat_escalated = [
        l
        for l in leads
        if not is_lead_terminal_fn(l)
        and lead_type_value(l) == LeadType.THREAT.value
        and lead_int(l, "escalation_level", default=0) > 0
    ]
    threat_escalated_sorted = sorted(threat_escalated, key=lambda l: lead_pressure_sort_key(l, current_turn))

    high_pressure_unattended = [
        l
        for l in leads
        if not is_lead_terminal_fn(l)
        and lead_status_value(l) == LeadStatus.ACTIVE.value
        and _not_recently_touched(l)
        and effective_pressure_fn(l, current_turn) >= 1
    ]
    high_pressure_unattended_sorted = sorted(
        high_pressure_unattended, key=lambda l: lead_pressure_sort_key(l, current_turn)
    )

    urgent_or_stale_raw: List[Any] = []
    seen_urgent: set[str] = set()

    def _append_urgent(candidate: Any) -> None:
        if len(urgent_or_stale_raw) >= 3:
            return
        lid = str(lead_get(candidate, "id") or "").strip()
        if lid and lid in seen_urgent:
            return
        urgent_or_stale_raw.append(candidate)
        if lid:
            seen_urgent.add(lid)

    for l in stale_sorted:
        _append_urgent(l)
    for l in threat_escalated_sorted:
        _append_urgent(l)
    for l in high_pressure_unattended_sorted:
        _append_urgent(l)
    urgent_or_stale_leads = [compact_lead_row(l) for l in urgent_or_stale_raw]

    recent_sorted = sorted(leads, key=lambda l: recent_lead_changes_sort_key(l, current_turn))
    recent_lead_changes = [compact_lead_row(l) for l in recent_sorted[:5]]

    npc_relevant_raw: List[Any] = []
    aid = str(active_npc_id or "").strip()
    if aid:
        for l in leads:
            if is_lead_terminal_fn(l):
                continue
            rel = lead_get(l, "related_npc_ids")
            if not isinstance(rel, list):
                continue
            if any(str(x or "").strip() == aid for x in rel):
                npc_relevant_raw.append(l)
        npc_relevant_raw = sorted(
            npc_relevant_raw, key=lambda l: lead_pressure_sort_key(l, current_turn)
        )[:3]
    npc_relevant_leads = [compact_lead_row(l) for l in npc_relevant_raw]

    stale_any = [l for l in leads if lead_status_value(l) == LeadStatus.STALE.value]
    has_escalated_threat = any(
        not is_lead_terminal_fn(l)
        and lead_type_value(l) == LeadType.THREAT.value
        and lead_int(l, "escalation_level", default=0) > 0
        for l in leads
    )
    has_newly_unlocked = any(
        str(lead_get(l, "unlocked_by_lead_id") or "").strip()
        and lead_int(l, "last_updated_turn", default=-1) == current_turn
        for l in leads
    )
    has_supersession_cleanup = any(
        lead_int(l, "last_updated_turn", default=-1) == current_turn
        and lead_lifecycle_value(l) == LeadLifecycle.OBSOLETE.value
        and (
            str(lead_get(l, "obsolete_reason") or "").strip().lower() == "superseded"
            or str(lead_get(l, "superseded_by") or "").strip()
        )
        for l in leads
    )

    return {
        "top_active_leads": top_active_leads,
        "currently_pursued_lead": currently_pursued_lead,
        "urgent_or_stale_leads": urgent_or_stale_leads,
        "recent_lead_changes": recent_lead_changes,
        "npc_relevant_leads": npc_relevant_leads,
        "follow_up_pressure_from_leads": {
            "has_pursued": bool(pursued),
            "has_stale": bool(stale_any),
            "npc_has_relevant": bool(npc_relevant_leads),
            "has_escalated_threat": bool(has_escalated_threat),
            "has_newly_unlocked": bool(has_newly_unlocked),
            "has_supersession_cleanup": bool(has_supersession_cleanup),
        },
    }


def _interlocutor_discussion_sort_key(row: Dict[str, Any]) -> tuple[Any, ...]:
    """Deterministic order for active-NPC lead discussion rows."""
    lead_int = _prompt_context_attr("_lead_int", _lead_int)
    ack = bool(row.get("player_acknowledged"))
    recent = bool(row.get("recently_discussed"))
    last_discussed = lead_int(row, "last_discussed_turn", default=-1)
    disclosure = str(row.get("disclosure_level") or "").strip().lower()
    # Only guarantee explicit beats hinted on disclosure ties.
    disclosure_rank = 0 if disclosure == "explicit" else 1
    title = str(row.get("title") or "").strip().lower()
    lead_id = str(row.get("lead_id") or "").strip().lower()
    return (ack, not recent, -last_discussed, disclosure_rank, title, lead_id)


def _discussion_row_recently_discussed(
    *,
    current_turn: int | None,
    last_discussed_turn: Any,
) -> bool:
    if current_turn is None:
        return False
    try:
        last_discussed = int(last_discussed_turn)
    except (TypeError, ValueError):
        return False
    delta = current_turn - last_discussed
    return 0 <= delta <= INTERLOCUTOR_DISCUSSION_RECENCY_WINDOW


def build_interlocutor_lead_discussion_context(
    session: Any,
    world: Any,
    public_scene: Any,
    recent_log: Any,
    *,
    active_npc_id: str | None,
) -> Dict[str, Any]:
    """Read-only active-NPC lead discussion context from scene runtime Block 1 memory.

    Source of truth: Block 1 npc_lead_discussions joined to get_lead; strict active_npc_id scoping;
    terminal leads only in recent_terminal_reference; missing registry rows skipped. No writes.
    """
    _ = (world, recent_log)
    lead_get = _prompt_context_attr("_lead_get", _lead_get)
    lead_status_value = _prompt_context_attr("_lead_status_value", _lead_status_value)
    discussion_row_recently_discussed = _prompt_context_attr(
        "_discussion_row_recently_discussed", _discussion_row_recently_discussed
    )
    interlocutor_discussion_sort_key = _prompt_context_attr(
        "_interlocutor_discussion_sort_key", _interlocutor_discussion_sort_key
    )
    list_recent_npc_lead_discussions_fn = _prompt_context_attr(
        "list_recent_npc_lead_discussions", list_recent_npc_lead_discussions
    )
    social_turn_counter_fn = _prompt_context_attr("_social_turn_counter", _social_turn_counter)
    get_lead_fn = _prompt_context_attr("get_lead", get_lead)
    is_lead_terminal_fn = _prompt_context_attr("is_lead_terminal", is_lead_terminal)
    neutral: Dict[str, Any] = {
        "active_npc_id": None,
        "introduced_by_npc": [],
        "unacknowledged_from_npc": [],
        "recently_discussed_with_npc": [],
        "recent_terminal_reference": [],
        "repeat_suppression": {
            "has_recent_repeat_risk": False,
            "recent_lead_ids": [],
            "prefer_progress_over_restatement": False,
        },
    }
    npc_id = str(active_npc_id or "").strip()
    if not npc_id:
        return neutral

    scene_id = str(lead_get(public_scene, "id") or "").strip()
    if not scene_id:
        scene_id = str(lead_get(session, "active_scene_id") or "").strip()
    if not scene_id:
        return {**neutral, "active_npc_id": npc_id}

    rows = list_recent_npc_lead_discussions_fn(session, scene_id, npc_id=npc_id, limit=64)
    current_turn = social_turn_counter_fn(session)
    actionable_rows: List[Dict[str, Any]] = []
    terminal_rows: List[Dict[str, Any]] = []
    for rec in rows:
        if not isinstance(rec, dict):
            continue
        lid = str(rec.get("lead_id") or "").strip()
        if not lid:
            continue
        lead_row = get_lead_fn(session, lid)
        if not isinstance(lead_row, dict):
            continue

        title = str(lead_row.get("title") or "").strip()
        status = lead_status_value(lead_row)
        lifecycle = str(lead_row.get("lifecycle") or "").strip().lower()
        merged = {
            "lead_id": lid,
            "title": title,
            "status": status,
            "lifecycle": lifecycle,
            "disclosure_level": str(rec.get("disclosure_level") or "").strip().lower() or "hinted",
            "player_acknowledged": bool(rec.get("player_acknowledged")),
            "player_acknowledged_turn": rec.get("player_acknowledged_turn"),
            "mention_count": int(rec.get("mention_count") or 0),
            "first_discussed_turn": rec.get("first_discussed_turn"),
            "last_discussed_turn": rec.get("last_discussed_turn"),
            "recently_discussed": discussion_row_recently_discussed(
                current_turn=current_turn,
                last_discussed_turn=rec.get("last_discussed_turn"),
            ),
            "last_scene_id": str(rec.get("last_scene_id") or "").strip() or scene_id,
        }
        if is_lead_terminal_fn(lead_row):
            terminal_rows.append(merged)
        else:
            actionable_rows.append(merged)

    actionable_rows = sorted(actionable_rows, key=interlocutor_discussion_sort_key)
    terminal_rows = sorted(terminal_rows, key=interlocutor_discussion_sort_key)
    unack = [r for r in actionable_rows if not bool(r.get("player_acknowledged"))]
    recent = [r for r in actionable_rows if bool(r.get("recently_discussed"))]
    recent_lead_ids = [str(r.get("lead_id") or "").strip() for r in recent if str(r.get("lead_id") or "").strip()]
    has_repeat_risk = bool(recent_lead_ids)
    return {
        "active_npc_id": npc_id,
        "introduced_by_npc": actionable_rows,
        "unacknowledged_from_npc": unack,
        "recently_discussed_with_npc": recent,
        "recent_terminal_reference": terminal_rows[:2],
        "repeat_suppression": {
            "has_recent_repeat_risk": has_repeat_risk,
            "recent_lead_ids": recent_lead_ids,
            "prefer_progress_over_restatement": has_repeat_risk,
        },
    }


def deterministic_interlocutor_lead_behavior_hints(
    interlocutor_lead_context: Mapping[str, Any] | None,
) -> List[str]:
    """Return compact deterministic behavior hints from interlocutor lead context.

    Input is interlocutor_lead_context only—no persistence or new inference; must not affect speaker
    grounding. Tests should assert contract / hint triggers, not exact narration prose.
    """
    if not isinstance(interlocutor_lead_context, Mapping):
        return []

    introduced = interlocutor_lead_context.get("introduced_by_npc")
    unack = interlocutor_lead_context.get("unacknowledged_from_npc")
    recent = interlocutor_lead_context.get("recently_discussed_with_npc")
    terminal_refs = interlocutor_lead_context.get("recent_terminal_reference")
    repeat = interlocutor_lead_context.get("repeat_suppression")

    introduced_rows = introduced if isinstance(introduced, list) else []
    unack_rows = unack if isinstance(unack, list) else []
    recent_rows = recent if isinstance(recent, list) else []
    terminal_rows = terminal_refs if isinstance(terminal_refs, list) else []
    repeat_map = repeat if isinstance(repeat, Mapping) else {}

    has_actionable_rows = bool(introduced_rows or unack_rows or recent_rows)
    if not has_actionable_rows and terminal_rows:
        return []
    if not has_actionable_rows:
        return []

    hints: List[str] = []
    seen: set[str] = set()

    def _append_hint(text: str) -> None:
        hint = str(text or "").strip()
        if not hint or hint in seen:
            return
        seen.add(hint)
        hints.append(hint)

    has_recent_repeat_risk = bool(repeat_map.get("has_recent_repeat_risk"))
    if has_recent_repeat_risk:
        _append_hint(
            "If this NPC discussed a lead recently, prefer advancement, clarification, implication, cost, risk, condition, refusal, or next-step pressure over repetition."
        )

    has_recent_explicit = any(
        str((row or {}).get("disclosure_level") or "").strip().lower() == "explicit"
        for row in recent_rows
        if isinstance(row, Mapping)
    )
    if has_recent_explicit:
        _append_hint(
            "NPC LEAD CONTINUITY (engine): Do not present a lead this NPC already discussed explicitly as brand-new."
        )

    has_hinted_unack = any(
        (not bool((row or {}).get("player_acknowledged")))
        and str((row or {}).get("disclosure_level") or "").strip().lower() == "hinted"
        for row in unack_rows
        if isinstance(row, Mapping)
    )
    if has_hinted_unack:
        _append_hint(
            "If a lead remains hinted and unacknowledged, continued hinting or narrowing is allowed; full disclosure is not required."
        )

    has_acknowledged = any(
        bool((row or {}).get("player_acknowledged"))
        for row in introduced_rows
        if isinstance(row, Mapping)
    )
    if has_acknowledged:
        _append_hint(
            "If the player already acknowledged a lead from this NPC, treat it as shared context and move beyond basic re-introduction."
        )

    return hints

