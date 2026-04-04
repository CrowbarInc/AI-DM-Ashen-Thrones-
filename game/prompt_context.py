"""Prompt compression layer for GPT narration.

Builds a concise, structured context from full game state before constructing
the narration prompt. Reduces token usage and keeps narration coherent by
including only relevant elements.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping
import re

from game.leads import (
    effective_lead_pressure_score,
    filter_pending_leads_for_active_follow_surface,
    get_lead,
    is_lead_terminal,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    list_session_leads,
)
from game.social import (
    _social_turn_counter,
    explicit_player_topic_anchor_state,
    list_recent_npc_lead_discussions,
)
from game.storage import get_scene_state
from game.world import get_world_npc_by_id

# Configurable limits for deterministic, inspectable compression
MAX_RECENT_LOG = 5
MAX_RECENT_EVENTS = 5
MAX_GM_GUIDANCE = 3
MAX_WORLD_PRESSURES = 3
MAX_LOG_ENTRY_SNIPPET = 200
MAX_FOLLOW_UP_TOPIC_TOKENS = 6
MAX_RECENT_CONTEXTUAL_LEADS = 4
INTERLOCUTOR_DISCUSSION_RECENCY_WINDOW = 2

SOCIAL_REPLY_KINDS = frozenset({
    'question',
    'persuade',
    'intimidate',
    'deceive',
    'barter',
    'recruit',
    'social_probe',
})
NPC_REPLY_KIND_VALUES = frozenset({'answer', 'explanation', 'reaction', 'refusal'})

# Single source of truth for narration-rule precedence. Prompting and
# deterministic enforcement both read this so conflicts resolve the same way.
RESPONSE_RULE_PRIORITY: tuple[tuple[str, str], ...] = (
    ("must_answer", "ANSWER THE PLAYER"),
    ("forbid_state_invention", "DO NOT CONTRADICT AUTHORITATIVE STATE"),
    ("forbid_secret_leak", "DO NOT LEAK HIDDEN FACTS / SECRETS"),
    ("allow_partial_answer", "IF FULL CERTAINTY IS UNAVAILABLE, GIVE A BOUNDED PARTIAL ANSWER"),
    ("diegetic_only", "MAINTAIN DIEGETIC VOICE (no validator/system voice)"),
    ("prefer_scene_momentum", "PRESERVE SCENE MOMENTUM"),
    ("prefer_specificity", "ADD SPECIFICITY / FLAVOR / POLISH"),
)

RULE_PRIORITY_COMPACT_INSTRUCTION = (
    "When rules conflict, resolve them in this order: answer the player; preserve authoritative "
    "state; avoid leaking hidden facts; if certainty is incomplete, give a bounded partial answer; "
    "remain diegetic; maintain scene momentum; then add specificity."
)
NO_VALIDATOR_VOICE_RULE = (
    "Never speak as a validator, analyst, referee of canon, or system. Do not mention what is or "
    "is not established, available to the model, visible to tools, or answerable by the system. "
    "If uncertainty exists, express it as in-world uncertainty from people, circumstances, clues, "
    "distance, darkness, rumor, missing access, or incomplete observation."
)
NO_VALIDATOR_VOICE_PROHIBITIONS: tuple[str, ...] = (
    "canon_validation",
    "evidence_review",
    "system_limitation",
    "tool_access",
    "model_identity",
    "rules_explanation_outside_oc_or_adjudication",
)
UNCERTAINTY_CATEGORIES: tuple[str, ...] = (
    "unknown_identity",
    "unknown_location",
    "unknown_motive",
    "unknown_method",
    "unknown_quantity",
    "unknown_feasibility",
)
UNCERTAINTY_SOURCES: tuple[str, ...] = (
    "npc_ignorance",
    "scene_ambiguity",
    "procedural_insufficiency",
)
UNCERTAINTY_ANSWER_SHAPE: tuple[str, ...] = (
    "known_edge",
    "unknown_edge",
    "next_lead",
)

_TOPIC_TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z']{2,}")
_TOPIC_STOPWORDS = frozenset({
    "what", "where", "when", "why", "how", "who", "which",
    "tell", "said", "says", "know", "knew", "think", "heard",
    "about", "again", "still", "really", "actually", "just",
    "there", "here", "them", "they", "their", "then", "than",
    "with", "from", "into", "onto", "over", "under", "near",
    "this", "that", "these", "those", "your", "you're", "youre",
    "have", "has", "had", "can", "could", "would", "should",
    "does", "did", "is", "are", "was", "were", "will",
})
_FOLLOW_UP_PRESS_TOKENS: tuple[str, ...] = (
    "again",
    "still",
    "okay but",
    "ok but",
    "but",
    "be specific",
    "details",
    "name",
    "names",
    "where exactly",
    "who exactly",
)

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

    if isinstance(session, Mapping):
        leads = list_session_leads(session, include_terminal=True)
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

    current_turn = _lead_int(session, "turn_counter", default=0) if isinstance(session, Mapping) else 0

    active_vals = (LeadStatus.ACTIVE.value, LeadStatus.PURSUED.value)
    active_like = [
        l
        for l in leads
        if _lead_status_value(l) in active_vals and not is_lead_terminal(l)
    ]
    pursued = [
        l
        for l in leads
        if _lead_status_value(l) == LeadStatus.PURSUED.value and not is_lead_terminal(l)
    ]
    stale = [l for l in leads if _lead_status_value(l) == LeadStatus.STALE.value and not is_lead_terminal(l)]

    active_like_sorted = sorted(active_like, key=lambda l: _lead_pressure_sort_key(l, current_turn))
    pursued_sorted = sorted(pursued, key=lambda l: _lead_pressure_sort_key(l, current_turn))

    top_active_leads = [_compact_lead_row(l) for l in active_like_sorted[:3]]
    currently_pursued_lead = _compact_lead_row(pursued_sorted[0]) if pursued_sorted else None

    def _not_recently_touched(lead: Any) -> bool:
        raw = _lead_get(lead, "last_touched_turn")
        if raw is None:
            return True
        touched = _lead_int(lead, "last_touched_turn", default=-1)
        if touched < 0:
            return True
        return current_turn - touched >= 2

    stale_sorted = sorted(stale, key=lambda l: _lead_pressure_sort_key(l, current_turn))
    threat_escalated = [
        l
        for l in leads
        if not is_lead_terminal(l)
        and _lead_type_value(l) == LeadType.THREAT.value
        and _lead_int(l, "escalation_level", default=0) > 0
    ]
    threat_escalated_sorted = sorted(threat_escalated, key=lambda l: _lead_pressure_sort_key(l, current_turn))

    high_pressure_unattended = [
        l
        for l in leads
        if not is_lead_terminal(l)
        and _lead_status_value(l) == LeadStatus.ACTIVE.value
        and _not_recently_touched(l)
        and effective_lead_pressure_score(l, current_turn) >= 1
    ]
    high_pressure_unattended_sorted = sorted(
        high_pressure_unattended, key=lambda l: _lead_pressure_sort_key(l, current_turn)
    )

    urgent_or_stale_raw: List[Any] = []
    seen_urgent: set[str] = set()

    def _append_urgent(candidate: Any) -> None:
        if len(urgent_or_stale_raw) >= 3:
            return
        lid = str(_lead_get(candidate, "id") or "").strip()
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
    urgent_or_stale_leads = [_compact_lead_row(l) for l in urgent_or_stale_raw]

    recent_sorted = sorted(leads, key=lambda l: _recent_lead_changes_sort_key(l, current_turn))
    recent_lead_changes = [_compact_lead_row(l) for l in recent_sorted[:5]]

    npc_relevant_raw: List[Any] = []
    aid = str(active_npc_id or "").strip()
    if aid:
        for l in leads:
            if is_lead_terminal(l):
                continue
            rel = _lead_get(l, "related_npc_ids")
            if not isinstance(rel, list):
                continue
            if any(str(x or "").strip() == aid for x in rel):
                npc_relevant_raw.append(l)
        npc_relevant_raw = sorted(
            npc_relevant_raw, key=lambda l: _lead_pressure_sort_key(l, current_turn)
        )[:3]
    npc_relevant_leads = [_compact_lead_row(l) for l in npc_relevant_raw]

    stale_any = [l for l in leads if _lead_status_value(l) == LeadStatus.STALE.value]
    has_escalated_threat = any(
        not is_lead_terminal(l)
        and _lead_type_value(l) == LeadType.THREAT.value
        and _lead_int(l, "escalation_level", default=0) > 0
        for l in leads
    )
    has_newly_unlocked = any(
        str(_lead_get(l, "unlocked_by_lead_id") or "").strip()
        and _lead_int(l, "last_updated_turn", default=-1) == current_turn
        for l in leads
    )
    has_supersession_cleanup = any(
        _lead_int(l, "last_updated_turn", default=-1) == current_turn
        and _lead_lifecycle_value(l) == LeadLifecycle.OBSOLETE.value
        and (
            str(_lead_get(l, "obsolete_reason") or "").strip().lower() == "superseded"
            or str(_lead_get(l, "superseded_by") or "").strip()
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
    ack = bool(row.get("player_acknowledged"))
    recent = bool(row.get("recently_discussed"))
    last_discussed = _lead_int(row, "last_discussed_turn", default=-1)
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

    scene_id = str(_lead_get(public_scene, "id") or "").strip()
    if not scene_id:
        scene_id = str(_lead_get(session, "active_scene_id") or "").strip()
    if not scene_id:
        return {**neutral, "active_npc_id": npc_id}

    rows = list_recent_npc_lead_discussions(session, scene_id, npc_id=npc_id, limit=64)
    current_turn = _social_turn_counter(session)
    actionable_rows: List[Dict[str, Any]] = []
    terminal_rows: List[Dict[str, Any]] = []
    for rec in rows:
        if not isinstance(rec, dict):
            continue
        lid = str(rec.get("lead_id") or "").strip()
        if not lid:
            continue
        lead_row = get_lead(session, lid)
        if not isinstance(lead_row, dict):
            continue

        title = str(lead_row.get("title") or "").strip()
        status = _lead_status_value(lead_row)
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
            "recently_discussed": _discussion_row_recently_discussed(
                current_turn=current_turn,
                last_discussed_turn=rec.get("last_discussed_turn"),
            ),
            "last_scene_id": str(rec.get("last_scene_id") or "").strip() or scene_id,
        }
        if is_lead_terminal(lead_row):
            terminal_rows.append(merged)
        else:
            actionable_rows.append(merged)

    actionable_rows = sorted(actionable_rows, key=_interlocutor_discussion_sort_key)
    terminal_rows = sorted(terminal_rows, key=_interlocutor_discussion_sort_key)
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


def _topic_tokens(text: str) -> List[str]:
    low = " ".join(str(text or "").strip().lower().split())
    if not low:
        return []
    toks = [t for t in _TOPIC_TOKEN_PATTERN.findall(low) if len(t) >= 4 and t not in _TOPIC_STOPWORDS]
    seen: set[str] = set()
    out: List[str] = []
    for t in toks:
        if t in seen:
            continue
        out.append(t)
        seen.add(t)
        if len(out) >= MAX_FOLLOW_UP_TOPIC_TOKENS:
            break
    return out


def _overlap_ratio(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    inter = len(sa & sb)
    denom = min(len(sa), len(sb))
    return float(inter) / float(denom or 1)


def _compute_follow_up_pressure(recent_log_compact: List[Dict[str, Any]], user_text: str) -> Dict[str, Any] | None:
    """Detect when the player is pressing the same topic over consecutive turns.

    This is intentionally lightweight and prompt-scoped: it uses only the recent
    log slice already passed to the model (no new persistence/memory subsystem).
    """
    if not recent_log_compact:
        return None
    last = recent_log_compact[-1] if isinstance(recent_log_compact[-1], dict) else {}
    prev_player = str(last.get("player_input") or "").strip()
    prev_gm = str(last.get("gm_snippet") or "").strip()
    if not prev_player or not prev_gm:
        return None

    cur = str(user_text or "").strip()
    if not cur:
        return None

    cur_low = cur.lower()
    press_marker = any(tok in cur_low for tok in _FOLLOW_UP_PRESS_TOKENS)
    cur_tokens = _topic_tokens(cur)
    prev_tokens = _topic_tokens(prev_player)
    overlap = _overlap_ratio(cur_tokens, prev_tokens)

    pressed = (overlap >= 0.55 and len(cur_tokens) >= 2) or (press_marker and overlap >= 0.35 and len(cur_tokens) >= 1)
    if not pressed:
        return None

    press_depth = 1
    for entry in reversed(recent_log_compact[:-1]):
        if not isinstance(entry, dict):
            break
        txt = str(entry.get("player_input") or "").strip()
        if not txt:
            break
        if _overlap_ratio(cur_tokens, _topic_tokens(txt)) < 0.35:
            break
        press_depth += 1
        if press_depth >= 3:
            break

    return {
        "pressed": True,
        "press_depth": press_depth,
        "topic_tokens": cur_tokens,
        "previous_player_input": prev_player[:240],
        "previous_answer_snippet": prev_gm[:240],
        "overlap_ratio": round(overlap, 3),
    }


def build_response_policy(*, narration_obligations: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build the inspectable response policy for the current turn.

    This keeps the precedence ladder explicit in one place so prompt assembly
    and post-generation enforcement can share it instead of re-encoding order.
    """
    obligations = narration_obligations if isinstance(narration_obligations, dict) else {}
    suppress = bool(obligations.get("suppress_non_social_emitters"))
    return {
        "rule_priority_order": [label for _, label in RESPONSE_RULE_PRIORITY],
        "must_answer": True,
        "forbid_state_invention": True,
        "forbid_secret_leak": True,
        "allow_partial_answer": True,
        "diegetic_only": True,
        "prefer_scene_momentum": not suppress,
        "prefer_specificity": True,
        "no_validator_voice": {
            "enabled": True,
            "applies_to": "standard_narration",
            "rule": NO_VALIDATOR_VOICE_RULE,
            "prohibited_perspectives": list(NO_VALIDATOR_VOICE_PROHIBITIONS),
            "rules_explanation_only_in": ["oc", "adjudication"],
        },
        "scene_momentum_due": False if suppress else bool(obligations.get("scene_momentum_due")),
        "uncertainty": {
            "enabled": not suppress,
            "categories": list(UNCERTAINTY_CATEGORIES),
            "sources": list(UNCERTAINTY_SOURCES),
            "answer_shape": list(UNCERTAINTY_ANSWER_SHAPE),
            "context_inputs": ["turn_context", "speaker", "scene_snapshot"],
        },
    }


def canonical_interaction_target_npc_id(session: Dict[str, Any] | None, raw_target_id: str | None) -> str:
    """Map session interaction target to promoted world NPC id when ``promoted_actor_npc_map`` binds it."""
    raw = str(raw_target_id or "").strip()
    if not raw or not isinstance(session, dict):
        return raw
    st = get_scene_state(session)
    pmap = st.get("promoted_actor_npc_map")
    if not isinstance(pmap, dict):
        return raw
    mapped = pmap.get(raw)
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw


def _resolve_active_interaction_target_name(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
    *,
    npc_id: str | None = None,
) -> str | None:
    """Resolve interaction target (or explicit *npc_id*) to a display name; prefers world row, then in-scene match."""
    tid = str(npc_id or "").strip()
    if not tid:
        interaction_ctx = session.get('interaction_context') or {}
        if not isinstance(interaction_ctx, dict):
            return None
        tid = str(interaction_ctx.get('active_interaction_target_id') or '').strip()
    if not tid:
        return None

    w = world if isinstance(world, dict) else {}
    row = get_world_npc_by_id(w, tid)
    if isinstance(row, dict):
        nm = str(row.get("name") or "").strip()
        if nm:
            return nm

    scene_id = str(public_scene.get('id') or '').strip()
    npcs = w.get('npcs') or []
    if not isinstance(npcs, list):
        return None

    target_id_low = tid.lower()
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get('id') or '').strip()
        if not nid or nid.lower() != target_id_low:
            continue
        npc_loc = str(npc.get('location') or npc.get('scene_id') or '').strip()
        if scene_id and npc_loc != scene_id:
            continue
        npc_name = str(npc.get('name') or '').strip()
        return npc_name or None
    return None


def build_active_interlocutor_export(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> Dict[str, Any] | None:
    """Engine-authored active speaker profile for prompts (canonical ``npc_id`` when promoted)."""
    if not isinstance(session, dict):
        return None
    ic = session.get("interaction_context") or {}
    if not isinstance(ic, dict):
        return None
    raw = str(ic.get("active_interaction_target_id") or "").strip()
    if not raw:
        return None
    npc_id = canonical_interaction_target_npc_id(session, raw)
    w = world if isinstance(world, dict) else {}
    npc = get_world_npc_by_id(w, npc_id)
    name = _resolve_active_interaction_target_name(session, w, public_scene, npc_id=npc_id) or ""
    base: Dict[str, Any] = {
        "npc_id": npc_id,
        "raw_interaction_target_id": raw,
        "display_name": name,
    }
    if not isinstance(npc, dict):
        return {**base, "origin_kind": None, "stance_toward_player": None, "knowledge_scope": [],
                "information_reliability": None, "affiliation": None, "current_agenda": None,
                "promoted_from_actor_id": None}
    return {
        **base,
        "origin_kind": str(npc.get("origin_kind") or "").strip() or None,
        "stance_toward_player": str(npc.get("stance_toward_player") or "").strip() or None,
        "knowledge_scope": list(npc.get("knowledge_scope") or []) if isinstance(npc.get("knowledge_scope"), list) else [],
        "information_reliability": str(npc.get("information_reliability") or "").strip() or None,
        "affiliation": str(npc.get("affiliation") or "").strip() or None,
        "current_agenda": str(npc.get("current_agenda") or "").strip() or None,
        "promoted_from_actor_id": str(npc.get("promoted_from_actor_id") or "").strip() or None,
    }


def build_social_interlocutor_profile(interlocutor: Dict[str, Any] | None) -> Dict[str, Any]:
    """Deterministic ``social_context.interlocutor_profile`` payload (engine fields only)."""
    if not isinstance(interlocutor, dict) or not str(interlocutor.get("npc_id") or "").strip():
        return {
            "npc_is_promoted": False,
            "stance": None,
            "reliability": None,
            "knowledge_scope": [],
            "agenda": None,
            "affiliation": None,
        }
    pfa = str(interlocutor.get("promoted_from_actor_id") or "").strip()
    ks = interlocutor.get("knowledge_scope")
    scope_list = [str(x).strip() for x in ks if isinstance(x, str) and str(x).strip()] if isinstance(ks, list) else []
    return {
        "npc_is_promoted": bool(pfa),
        "stance": interlocutor.get("stance_toward_player"),
        "reliability": interlocutor.get("information_reliability"),
        "knowledge_scope": scope_list,
        "agenda": interlocutor.get("current_agenda"),
        "affiliation": interlocutor.get("affiliation"),
    }


def deterministic_interlocutor_answer_style_hints(
    interlocutor: Dict[str, Any] | None,
    *,
    scene_id: str,
) -> List[str]:
    """Fixed strings derived only from engine reliability + knowledge_scope (+ scene id)."""
    if not isinstance(interlocutor, dict) or not str(interlocutor.get("npc_id") or "").strip():
        return []
    rel = str(interlocutor.get("information_reliability") or "").strip().lower()
    if rel not in ("truthful", "partial", "misleading"):
        rel = "partial"
    ks_raw = interlocutor.get("knowledge_scope")
    scopes = sorted(
        {str(x).strip() for x in ks_raw if isinstance(x, str) and str(x).strip()}
        if isinstance(ks_raw, list)
        else set()
    )
    sid = str(scene_id or "").strip()
    scope_note = (
        f"Engine knowledge_scope tokens (direct professional/local anchors): {', '.join(scopes)}."
        if scopes
        else "Engine knowledge_scope is empty: treat direct private knowledge as narrow unless grounded in visible role, scene, or prior established exchanges."
    )
    out = [
        "INTERLOCUTOR KNOWLEDGE GATE (engine): Answer as this specific NPC. "
        "Use knowledge_scope as the boundary for what they know firsthand. "
        "Topics outside those anchors must be hearsay, uncertainty, deflection, or an honest 'I don't know'—not omniscient facts.",
        scope_note,
    ]
    if sid:
        needle = f"scene:{sid.lower()}"
        if any(s.lower() == needle for s in scopes):
            out.append(
                f"This NPC's scope includes the current scene token ({needle}): patrol layout, gate procedures, and crowd-level "
                "local knowledge may be stated directly when consistent with reliability."
            )
    if rel == "truthful":
        out.append(
            "INFORMATION_RELIABILITY truthful (engine): Within knowledge_scope, state what they know directly and clearly; "
            "do not add hidden omniscient details outside scope."
        )
    elif rel == "partial":
        out.append(
            "INFORMATION_RELIABILITY partial (engine): Within knowledge_scope, answers are incomplete, selective, or hedged; "
            "do not present full certainty or insider completeness they would not have."
        )
    else:
        out.append(
            "INFORMATION_RELIABILITY misleading (engine): Within knowledge_scope, replies may distort, omit, or deflect; "
            "lies stay plausible for this person—never omniscient fabrication or perfect hidden plots."
        )
    ok_origin = str(interlocutor.get("origin_kind") or "").strip().lower() in {"scene_actor", "crowd_actor"}
    has_pfa = bool(str(interlocutor.get("promoted_from_actor_id") or "").strip())
    if ok_origin and not has_pfa:
        out.append(
            "INCIDENTAL SCENE ACTOR (engine row without promotion linkage): keep characterization to this scene's role; "
            "do not invent a recurring named persona, secret dossier, or stable off-screen biography unless engine state already provides it."
        )
    return out


def _compress_campaign(campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize campaign to essential narration context. No hidden/secret fields."""
    if not campaign or not isinstance(campaign, dict):
        return {'title': '', 'premise': '', 'character_role': '', 'gm_guidance': [], 'world_pressures': []}

    gm_guidance = campaign.get('gm_guidance') or []
    if isinstance(gm_guidance, list):
        gm_guidance = gm_guidance[:MAX_GM_GUIDANCE]
    else:
        gm_guidance = []

    world_pressures = campaign.get('world_pressures') or []
    if isinstance(world_pressures, list):
        world_pressures = world_pressures[:MAX_WORLD_PRESSURES]
    else:
        world_pressures = []

    return {
        'title': str(campaign.get('title', '') or '')[:200],
        'premise': str(campaign.get('premise', '') or '')[:500],
        'tone': str(campaign.get('tone', '') or '')[:200],
        'character_role': str(campaign.get('character_role', '') or '')[:300],
        'gm_guidance': gm_guidance,
        'world_pressures': world_pressures,
        'magic_style': str(campaign.get('magic_style', '') or '')[:300],
    }


def _compress_world(world: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize world: world_state + recent events + faction names. No full dumps."""
    if not world or not isinstance(world, dict):
        return {'world_state': {'flags': {}, 'counters': {}, 'clocks_summary': []}, 'recent_events': [], 'faction_names': []}

    ws = world.get('world_state') or {}
    if not isinstance(ws, dict):
        ws = {}
    flags = {k: v for k, v in (ws.get('flags') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    counters = {k: v for k, v in (ws.get('counters') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    clocks_raw = ws.get('clocks') or {}
    clocks_summary = [
        f"{k}: {int(c.get('progress', 0))}/{int(c.get('max', 10))}"
        for k, c in clocks_raw.items()
        if isinstance(k, str) and not k.startswith('_') and isinstance(c, dict)
    ]
    world_state_view = {'flags': flags, 'counters': counters, 'clocks_summary': clocks_summary}

    event_log = world.get('event_log') or []
    recent_events: List[str] = []
    if isinstance(event_log, list):
        for entry in event_log[-MAX_RECENT_EVENTS:]:
            if isinstance(entry, dict) and isinstance(entry.get('text'), str):
                recent_events.append(entry['text'][:200])
            elif isinstance(entry, str):
                recent_events.append(entry[:200])

    factions = world.get('factions') or []
    faction_names: List[str] = []
    if isinstance(factions, list):
        for f in factions[:10]:
            if isinstance(f, dict) and isinstance(f.get('name'), str):
                faction_names.append(f['name'])

    return {
        'world_state': world_state_view,
        'recent_events': recent_events,
        'faction_names': faction_names,
    }


def _compress_session(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> Dict[str, Any]:
    """Summarize session to minimal fields. No chat_history, debug_traces, etc."""
    if not session or not isinstance(session, dict):
        return {'active_scene_id': '', 'response_mode': 'standard', 'turn_counter': 0}

    visited = session.get('visited_scene_ids') or []
    visited_count = len(visited) if isinstance(visited, list) else 0
    interaction_ctx = session.get('interaction_context') or {}
    if not isinstance(interaction_ctx, dict):
        interaction_ctx = {}

    active_target = interaction_ctx.get('active_interaction_target_id')
    raw_tgt = str(active_target).strip() if isinstance(active_target, str) and active_target.strip() else None
    canonical_tgt = canonical_interaction_target_npc_id(session, raw_tgt) if raw_tgt else None
    eff_tgt = canonical_tgt or raw_tgt
    active_kind = interaction_ctx.get('active_interaction_kind')
    interaction_mode = interaction_ctx.get('interaction_mode')
    engagement_level = interaction_ctx.get('engagement_level')
    convo_privacy = interaction_ctx.get('conversation_privacy')
    position_ctx = interaction_ctx.get('player_position_context')

    return {
        'active_scene_id': str(session.get('active_scene_id', '') or ''),
        'response_mode': str(session.get('response_mode', 'standard') or 'standard'),
        'turn_counter': int(session.get('turn_counter', 0) or 0),
        'visited_scene_count': visited_count,
        'active_interaction_target_id': eff_tgt,
        'active_interaction_target_name': _resolve_active_interaction_target_name(session, world, public_scene, npc_id=eff_tgt) if eff_tgt else None,
        'active_interaction_kind': str(active_kind).strip() if isinstance(active_kind, str) and active_kind.strip() else None,
        'interaction_mode': str(interaction_mode).strip() if isinstance(interaction_mode, str) and interaction_mode.strip() else 'none',
        'engagement_level': str(engagement_level).strip() if isinstance(engagement_level, str) and engagement_level.strip() else 'none',
        'conversation_privacy': str(convo_privacy).strip() if isinstance(convo_privacy, str) and convo_privacy.strip() else None,
        'player_position_context': str(position_ctx).strip() if isinstance(position_ctx, str) and position_ctx.strip() else None,
    }


def _compress_recent_log(recent_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Trim log entries to player input + short GM snippet. Take last N only."""
    if not recent_log or not isinstance(recent_log, list):
        return []

    trimmed: List[Dict[str, Any]] = []
    for entry in recent_log[-MAX_RECENT_LOG:]:
        if not isinstance(entry, dict):
            continue
        log_meta = entry.get('log_meta') or {}
        player_input = str(log_meta.get('player_input', '') or entry.get('request', {}).get('chat', '') or '')[:300]
        gm_output = entry.get('gm_output') or {}
        gm_text = gm_output.get('player_facing_text', '') if isinstance(gm_output, dict) else ''
        if isinstance(gm_text, str):
            gm_snippet = gm_text[:MAX_LOG_ENTRY_SNIPPET]
        else:
            gm_snippet = ''
        trimmed.append({'player_input': player_input, 'gm_snippet': gm_snippet})
    return trimmed


def _compress_combat(combat: Dict[str, Any]) -> Dict[str, Any] | None:
    """Include combat only when active; otherwise minimal/null."""
    if not combat or not isinstance(combat, dict):
        return None
    if not combat.get('in_combat'):
        return {'in_combat': False}
    return combat


def _compress_scene_runtime(runtime: Dict[str, Any], session: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Keep only essential runtime fields to avoid bloat."""
    if not runtime or not isinstance(runtime, dict):
        return {}
    recent_contextual_leads: List[Dict[str, Any]] = []
    raw_leads = runtime.get("recent_contextual_leads")
    if isinstance(raw_leads, list):
        for item in raw_leads[-MAX_RECENT_CONTEXTUAL_LEADS:]:
            if not isinstance(item, dict):
                continue
            subject = str(item.get("subject") or "").strip()
            key = str(item.get("key") or "").strip()
            if not subject or not key:
                continue
            recent_contextual_leads.append(
                {
                    "key": key,
                    "kind": str(item.get("kind") or "").strip(),
                    "subject": subject,
                    "position": str(item.get("position") or "").strip(),
                    "named": bool(item.get("named")),
                    "mentions": int(item.get("mentions", 1) or 1),
                    "last_turn": int(item.get("last_turn", 0) or 0),
                }
            )
    raw_pending = list(runtime.get('pending_leads', []) or [])
    pending_view = (
        filter_pending_leads_for_active_follow_surface(session, raw_pending)
        if isinstance(session, dict)
        else raw_pending
    )
    return {
        'discovered_clues': list(runtime.get('discovered_clues', []) or [])[:20],
        'pending_leads': pending_view,
        'recent_contextual_leads': recent_contextual_leads,
        'repeated_action_count': runtime.get('repeated_action_count', 0) or 0,
        'last_exploration_action_key': runtime.get('last_exploration_action_key'),
        'momentum_exchanges_since': int(runtime.get('momentum_exchanges_since', 0) or 0),
        'momentum_next_due_in': int(runtime.get('momentum_next_due_in', 2) or 2),
        'momentum_last_kind': runtime.get('momentum_last_kind'),
    }


def derive_narration_obligations(
    session_view: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
    recent_log_for_prompt: List[Dict[str, Any]] | None,
    scene_runtime: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Derive compact, engine-owned narration obligations for this turn."""
    turn_counter = int(session_view.get('turn_counter', 0) or 0)
    visited_scene_count = int(session_view.get('visited_scene_count', 0) or 0)
    recent_turns = len(recent_log_for_prompt or [])
    is_opening_scene = (
        turn_counter <= 1
        or (turn_counter == 0 and visited_scene_count <= 1 and recent_turns == 0)
    )

    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip().lower()
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_transition_occurred = bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred"))
    arrived_at_scene = bool(state_changes.get("arrived_at_scene"))
    new_scene_context_available = bool(state_changes.get("new_scene_context_available"))
    must_advance_scene = bool(scene_transition_occurred or arrived_at_scene or new_scene_context_available)

    active_target_id = str(session_view.get('active_interaction_target_id') or '').strip()
    active_kind = str(session_view.get('active_interaction_kind') or '').strip().lower()
    interaction_mode = str(session_view.get('interaction_mode') or '').strip().lower()
    has_active_target = bool(active_target_id)
    should_answer_active_npc = has_active_target and (
        interaction_mode == 'social'
        or active_kind in SOCIAL_REPLY_KINDS
        or active_kind == 'social'
    )

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels_low = {str(label).strip().lower() for label in labels if isinstance(label, str) and label.strip()}
    has_social_resolution = isinstance(res.get('social'), dict) or res_kind in SOCIAL_REPLY_KINDS
    social_payload = res.get('social') if isinstance(res.get('social'), dict) else {}
    explicit_reply_expected = social_payload.get('npc_reply_expected') if isinstance(social_payload.get('npc_reply_expected'), bool) else None
    explicit_reply_kind_raw = str(social_payload.get('reply_kind') or '').strip().lower()
    explicit_reply_kind = explicit_reply_kind_raw if explicit_reply_kind_raw in NPC_REPLY_KIND_VALUES else None

    has_pending_check_prompt = bool(
        res.get('requires_check')
        and not isinstance(res.get('skill_check'), dict)
        and isinstance(res.get('check_request'), dict)
    )
    # Ongoing social exchange (engine-established target + social mode) expects an NPC reply
    # even when this turn has no structured resolution.social (e.g. chat/wait while engaged).
    active_npc_reply_expected_fallback = should_answer_active_npc and (
        has_social_resolution
        or 'social_probe' in labels_low
        or interaction_mode == 'social'
    )
    # Authoritative social mode: always expect an NPC reply unless a check prompt blocks narration.
    if interaction_mode == 'social' and has_active_target:
        active_npc_reply_expected = not has_pending_check_prompt
    else:
        active_npc_reply_expected = (
            False
            if has_pending_check_prompt
            else (explicit_reply_expected if explicit_reply_expected is not None else active_npc_reply_expected_fallback)
        )
    active_npc_reply_kind = explicit_reply_kind
    if active_npc_reply_expected and active_npc_reply_kind is None:
        if res_kind in {'persuade', 'intimidate', 'deceive', 'barter', 'recruit'}:
            active_npc_reply_kind = 'reaction'
        elif res_kind in {'question', 'social_probe'}:
            active_npc_reply_kind = 'answer'
        else:
            active_npc_reply_kind = 'reaction'
    if not active_npc_reply_expected:
        active_npc_reply_kind = None

    rt = scene_runtime if isinstance(scene_runtime, dict) else {}
    exchanges_since = int(rt.get("momentum_exchanges_since", 0) or 0)
    next_due_in = int(rt.get("momentum_next_due_in", 2) or 2)
    if next_due_in not in (2, 3):
        next_due_in = 2
    # If last momentum was 1 exchange ago and next_due_in=2, momentum is due now.
    # This ensures a strict "every 2–3 exchanges" cadence with a hard ceiling of 3.
    due_threshold = (next_due_in - 1)
    if due_threshold < 1:
        due_threshold = 1
    if due_threshold > 2:
        due_threshold = 2
    suppress_non_social_emitters = interaction_mode == 'social' and has_active_target
    scene_momentum_due = False if suppress_non_social_emitters else (exchanges_since >= due_threshold)

    return {
        'is_opening_scene': bool(is_opening_scene),
        'must_advance_scene': bool(must_advance_scene),
        'should_answer_active_npc': bool(should_answer_active_npc),
        'avoid_input_echo': True,
        'avoid_player_action_restatement': True,
        'prefer_structured_turn_summary': True,
        'active_npc_reply_expected': bool(active_npc_reply_expected),
        'active_npc_reply_kind': active_npc_reply_kind,
        'scene_momentum_due': bool(scene_momentum_due),
        'scene_momentum_exchanges_since': exchanges_since,
        'scene_momentum_next_due_in': next_due_in,
        'suppress_non_social_emitters': bool(suppress_non_social_emitters),
    }


def _build_turn_summary(
    user_text: str,
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Build a compact, structured summary of this turn for narration anchoring."""
    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip()
    res_label = str(res.get('label') or '').strip()
    res_action_id = str(res.get('action_id') or '').strip()
    res_prompt = str(res.get('prompt') or '').strip()

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels = [str(label).strip() for label in labels if isinstance(label, str) and str(label).strip()]

    if res_kind:
        descriptor = res_label or res_kind.replace('_', ' ')
    elif labels:
        descriptor = labels[0].replace('_', ' ')
    else:
        descriptor = 'general_action'

    return {
        'action_descriptor': descriptor,
        'resolution_kind': res_kind or None,
        'action_id': res_action_id or None,
        'resolved_prompt': res_prompt or None,
        'intent_labels': labels,
        'raw_player_input': str(user_text or ''),
        'raw_player_input_usage': (
            'Retain for exact wording and disambiguation only. '
            'Prefer action_descriptor + resolution_kind + mechanical_resolution for narration framing.'
        ),
    }


def build_narration_context(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compressed narration context payload for GPT.

    Caller must precompute scene layers (public_scene, clues, hidden, etc.)
    and pass them in. This avoids duplicating _scene_layers logic and ensures
    hidden facts stay in gm_only only.

    Returns a dict suitable for JSON serialization as the user message content.
    """
    # Interlocutor lead contract (maintenance): interlocutor_lead_context is the NPC-scoped export from
    # discussion tracking + authoritative lead rows; interlocutor_lead_behavior_hints are derived only
    # from that dict. Keep both separate from lead_context and pending_leads. Synthetic regression targets
    # this export for continuity / repeat suppression—not fixed narration wording.
    active_pending_leads = (
        filter_pending_leads_for_active_follow_surface(session, pending_leads)
        if isinstance(session, dict)
        else list(pending_leads or [])
    )
    runtime = _compress_scene_runtime(scene_runtime or {}, session=session if isinstance(session, dict) else None)
    session_view = _compress_session(session, world, public_scene)
    narration_obligations = derive_narration_obligations(
        session_view=session_view,
        resolution=resolution,
        intent=intent,
        recent_log_for_prompt=recent_log_for_prompt,
        scene_runtime=runtime,
    )
    social_authority = bool(narration_obligations.get("suppress_non_social_emitters"))
    eff_uncertainty_hint = None if social_authority else uncertainty_hint
    response_policy = build_response_policy(narration_obligations=narration_obligations)
    res = resolution if isinstance(resolution, dict) else {}
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_advancement = {
        "scene_transition_occurred": bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred")),
        "arrived_at_scene": bool(state_changes.get("arrived_at_scene")),
        "new_scene_context_available": bool(state_changes.get("new_scene_context_available")),
    }
    has_scene_change_context = any(bool(v) for v in scene_advancement.values())
    interaction_continuity = {
        'active_interaction_target_id': session_view.get('active_interaction_target_id'),
        'active_interaction_target_name': session_view.get('active_interaction_target_name'),
        'active_interaction_kind': session_view.get('active_interaction_kind'),
        'interaction_mode': session_view.get('interaction_mode'),
        'engagement_level': session_view.get('engagement_level'),
        'conversation_privacy': session_view.get('conversation_privacy'),
        'player_position_context': session_view.get('player_position_context'),
    }
    has_active_interlocutor = bool(str(interaction_continuity.get('active_interaction_target_id') or '').strip())
    scene_pub_id = str((public_scene or {}).get("id") or "").strip()
    interlocutor_export = build_active_interlocutor_export(session, world, public_scene)
    answer_style_hints_list = deterministic_interlocutor_answer_style_hints(
        interlocutor_export, scene_id=scene_pub_id
    )

    clue_records_all: List[Dict[str, Any]] = list(discovered_clue_records) + list(undiscovered_clue_records)
    clue_visibility = {
        'implicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'implicit'],
        'explicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'explicit'],
        'actionable': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'actionable'],
    }

    instructions: List[str] = (
        [
            'Prioritize the active conversation over general scene recap.',
            'Do not fall back to base scene description unless the location materially changes, a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat.',
        ]
        if has_active_interlocutor
        else []
    ) + [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        'Always answer the player. Prefer partial truth over refusal. Never output meta explanations.',
        NO_VALIDATOR_VOICE_RULE,
        'Follow response_policy.rule_priority_order strictly. Higher-priority rules override later ones.',
        'Treat response_policy.no_validator_voice as a hard narration-lane rule for standard narration.',
        (
            "SCENE MOMENTUM RULE (HARD RULE): Every 2–3 exchanges, you MUST introduce exactly one of: "
            "new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity. "
            "When you do, include exactly one tag in tags: "
            "scene_momentum:<kind> where kind is one of those five identifiers. "
            "If narration_obligations.scene_momentum_due is true, this turn MUST include a momentum beat and MUST include that tag."
        ),
        'Use campaign and world state to keep political and strategic continuity.',
        'Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.',
        'Forbidden generic phrases are disallowed: "In this city...", "Times are tough...", "Trust is hard to come by...", "You\'ll need to prove yourself..." — rewrite into specific names/locations/events.',
        'QUESTION RESOLUTION RULE (HARD RULE): Every direct player question MUST be answered explicitly before any additional dialogue. Structure: (1) Direct answer (first sentence), (2) Optional elaboration, (3) Optional hook. The GM/NPC MUST NOT deflect, generalize, or ask a new question before answering.',
        'If certainty is incomplete, classify the uncertainty with response_policy.uncertainty.categories and response_policy.uncertainty.sources, then compose it from response_policy.uncertainty.answer_shape: known_edge, unknown_edge, next_lead.',
        'Ground uncertainty with response_policy.uncertainty.context_inputs: uncertainty_hint.turn_context, uncertainty_hint.speaker, and uncertainty_hint.scene_snapshot.',
        'If uncertainty_hint.speaker.role is npc, keep the reply attributable to that NPC and limited to what they could plausibly know, hear, point to, or direct the player toward.',
        'If there is no active NPC speaker, keep uncertainty in diegetic narrator voice but anchor it to visible scene circumstances rather than generic omniscient wording.',
        'If social_intent_class remains social_exchange on an NPC-directed question, keep uncertainty speaker-grounded (npc_ignorance) instead of drifting into scene ambiguity.',
        'Frame uncertainty as world-facing limits only: who knows, what can be seen, what distance, darkness, rumor, missing witnesses, or incomplete clues prevent right now.',
        'Vary sentence count and cadence naturally; do not stamp the same three-sentence rhythm onto every uncertain answer.',
        'If no strong next lead exists, choose the strongest visible handle already in scene rather than giving generic investigative advice.',
        'PERCEPTION / INTENT ADJUDICATION RULE (HARD RULE): When the player asks for behavioral insight (e.g., nervous, lying, controlled), choose ONE dominant state (not mixed), give 1–2 concrete observable tells, and optionally map to a skill interpretation (Sense Motive, etc.). Failure: "mix of"/"seems like both" or pure emotional summary with no cues.',
        'If the player meaningfully moves to a new location, you may provide a new_scene_draft and/or activate_scene_id.',
        'If the player meaningfully changes the world, you may provide world_updates.',
        'If the player text implies a clear mechanical action, suggested_action may be filled for UI assistance, but narration remains primary.',
        'When interaction_continuity has an active target, treat that NPC as the default conversational counterpart.',
        'Non-addressed NPCs should not casually interject; if they interrupt, present it as a notable event with scene justification.',
        'If conversation_privacy or player_position_context implies private exchange (for example lowered_voice), reduce casual eavesdropping/interjection unless scene facts justify otherwise.',
        'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
        'Treat player input as an action declaration: default to third-person phrasing and preserve the user\'s expression format instead of rewriting it.',
        'Quoted in-character dialogue is valid inside an action declaration (for example: Galinor says, "Keep your voice down."); do not treat the quote alone as the entire action when surrounding action context exists.',
        'Follow narration_obligations as output requirements only: they shape wording and focus, but never grant authority to mutate state or decide mechanics.',
        'If narration_obligations.is_opening_scene is true, establish immediate environment plus actionable social/world hooks the player can engage now.',
        'If narration_obligations.must_advance_scene is true, do not stop at movement text alone; narrate arrival, changed state, and at least one concrete opportunity or pressure in the destination context.',
        'If narration_obligations.active_npc_reply_expected is true, complete the active NPC\'s substantive in-turn reply now unless a pending engine check prompt already takes precedence, or authoritative state indicates refusal/evasion/interruption/inability.',
        'If narration_obligations.should_answer_active_npc is true, prioritize the active interlocutor\'s reply and the immediate exchange over general scene recap.',
        'Use narration_obligations.active_npc_reply_kind as a compact reply-shape hint (answer, explanation, reaction, refusal).',
        'If narration_obligations.active_npc_reply_kind is refusal, make it substantive (clear boundary, brief reason, redirect, or consequence) rather than empty stalling.',
        'If the player asks a direct question, answer concretely (name, place, fact, or direction); if certainty is incomplete, provide the best grounded partial answer and state uncertainty in-character through witnesses, conditions, rumor, access, or incomplete observation; do not repeat prior information.',
        'NPC response contract: when an NPC is asked a question, include at least one of: (a) a specific person/place/faction, (b) a concrete next step the player can take, (c) directly usable info (time/location/condition/requirement). If the NPC lacks full information, give partial specifics or direct the player to a concrete source.',
        'When answering a player question, give a direct answer first. Do not replace the answer with narrative description.',
        'Use turn_summary and mechanical_resolution as primary narration anchors; treat player_input as supporting evidence for disambiguation, not as the sentence structure to mirror.',
        "Do not restate or paraphrase the player's input. Always continue forward with new information.",
        "Do not repeat the player's spoken line. React to it instead.",
        'If narration_obligations.avoid_input_echo or narration_obligations.avoid_player_action_restatement is true, do not restate or lightly paraphrase player_input (for example, "Galinor asks...") unless wording is required to disambiguate the target, quote, or procedural request.',
        'If narration_obligations.prefer_structured_turn_summary is true, continue from resolved world state, scene advancement, and NPC intent/reply obligations rather than narrating that "the player asks/says X."',
        'Keep the narration to 1-4 concise paragraphs.',
        mode_instruction,
    ]
    if has_scene_change_context:
        instructions.append(
            'When transitioning scenes, include a brief bridge from the prior location before describing the new one.'
        )

    if social_authority:
        _skip_instr = (
            "SCENE MOMENTUM RULE",
            "uncertainty_hint",
            "response_policy.uncertainty",
            "classify the uncertainty",
            "Ground uncertainty with",
            "Frame uncertainty as",
            "If uncertainty_hint",
        )
        instructions = [line for line in instructions if not any(m in line for m in _skip_instr)]
        instructions.append(
            "SOCIAL INTERACTION LOCK: Do not use ambient scene narration, scene-wide uncertainty pools, or momentum/pressure "
            "beats as the main voice. The active interlocutor must carry this turn (substantive reply, reaction, or refusal)."
        )

    recent_log_compact = _compress_recent_log(recent_log_for_prompt) if recent_log_for_prompt else []
    follow_up_log_pressure = _compute_follow_up_pressure(recent_log_compact, user_text)
    if social_authority:
        follow_up_log_pressure = None

    active_topic_anchor = explicit_player_topic_anchor_state(str(user_text or ""))

    active_npc_id: str | None = None
    if isinstance(public_scene, Mapping):
        if isinstance(interlocutor_export, dict):
            _nid = str(interlocutor_export.get("npc_id") or "").strip()
            if _nid:
                active_npc_id = _nid
        if active_npc_id is None:
            _tid = session_view.get("active_interaction_target_id")
            if _tid and str(_tid).strip():
                active_npc_id = str(_tid).strip()

    lead_context = build_authoritative_lead_prompt_context(
        session=session,
        world=world,
        public_scene=public_scene,
        runtime=runtime,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_context = build_interlocutor_lead_discussion_context(
        session=session,
        world=world,
        public_scene=public_scene,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_behavior_hints = deterministic_interlocutor_lead_behavior_hints(
        interlocutor_lead_context
    )
    from_leads_pressure = lead_context.get("follow_up_pressure_from_leads")
    if not isinstance(from_leads_pressure, dict):
        from_leads_pressure = {
            "has_pursued": False,
            "has_stale": False,
            "npc_has_relevant": False,
            "has_escalated_threat": False,
            "has_newly_unlocked": False,
            "has_supersession_cleanup": False,
        }

    if follow_up_log_pressure:
        instructions = list(instructions) + [
            (
                "FOLLOW-UP ESCALATION RULE (HARD RULE): The player is pressing the same topic again (see follow_up_pressure). "
                "Do NOT recycle the same core lead from the previous answer. Escalate by doing AT LEAST TWO of the following: "
                "(1) add one new concrete detail (time, place, condition, count, or observable), "
                "(2) introduce a named person/place/faction/witness tied to the topic (with an in-world source), "
                "(3) narrow the boundary of the unknown (what is ruled out; what is now most likely; what would confirm it), "
                "(4) produce a more actionable immediate next step that uses the new detail. "
                "Preserve uncertainty, but uncertainty must evolve. Preserve speaker grounding."
            ),
            "Allowed repetition: one short anchor clause for continuity. Not allowed: re-stating the same underlying lead as the whole answer.",
        ]

    lead_instr: List[str] = [
        "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
        "Turn compact rows into light, actionable nudges (what could matter next), not recap.",
        "When the player is clearly continuing an existing investigation thread, prefer lead_context.currently_pursued_lead as the primary thread anchor when it is non-null.",
        "When interaction_continuity names an active NPC, use lead_context.npc_relevant_leads to tie the exchange to registry-linked threads that list that NPC—without fabricating details beyond those rows.",
        "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
        "Use lead_context.recent_lead_changes for continuity with the latest registry state shifts (status, next_step, touches)—do not restate full buckets or dump all leads.",
        "follow_up_pressure.from_leads is boolean-only: has_pursued, has_stale, npc_has_relevant, has_escalated_threat, has_newly_unlocked, has_supersession_cleanup. Do not treat it as prose; use the matching lead_context lists/objects for specifics.",
        "If follow_up_pressure.from_leads.has_pursued is true, bias narration toward continuing that pursued thread when it fits the player's action.",
        "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
        "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
        "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
        "If follow_up_pressure.from_leads.has_newly_unlocked is true, you may acknowledge a thread becoming available or unblocked when it fits the scene—grounded in unlocked_by_lead_id / recent_lead_changes only.",
        "If follow_up_pressure.from_leads.has_supersession_cleanup is true, avoid treating superseded obsoleted threads as primary pressure unless the player returns to them; prefer current non-terminal rows.",
    ]
    instructions = list(instructions) + lead_instr

    if social_authority and active_topic_anchor.get("active"):
        instructions = list(instructions) + [
            "ACTIVE TOPIC ANCHOR (HARD RULE): The player explicitly corrected or narrowed the conversational subject "
            "this turn. Answer that subject first in the active interlocutor's voice. Do not pivot back to "
            "lead_context.currently_pursued_lead, urgent_or_stale_leads, or unrelated registry mystery threads "
            "for convenience. Registry salience alone is not sufficient to override the clarified subject. "
            "A redirect is allowed only after a substantive answer—or honest refusal, evasion, or ignorance—on the "
            "asked subject.",
        ]

    if social_authority:
        follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    elif follow_up_log_pressure is not None:
        follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
    elif any(from_leads_pressure.values()):
        follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    else:
        follow_up_pressure = None

    if interlocutor_export and str(interlocutor_export.get("npc_id") or "").strip():
        nid = str(interlocutor_export.get("npc_id") or "").strip()
        dn = str(interlocutor_export.get("display_name") or "").strip()
        naming_line = (
            f"NAMING CONTINUITY (engine): Active interlocutor canonical id is {nid!r}"
            + (f", display name {dn!r}" if dn else "")
            + ". Keep this name/title stable across turns unless engine state changes it; "
            "do not regress to generic unnamed incidental-crowd wording for this id."
        )
        instructions = list(instructions) + list(answer_style_hints_list) + [naming_line]

    soc_profile = build_social_interlocutor_profile(interlocutor_export)

    payload: Dict[str, Any] = {
        'instructions': instructions,
        'active_topic_anchor': active_topic_anchor,
        'interaction_continuity': interaction_continuity,
        'active_interlocutor': interlocutor_export,
        'social_context': {
            'interlocutor_profile': soc_profile,
            'answer_style_hints': list(answer_style_hints_list),
        },
        'turn_summary': _build_turn_summary(user_text, resolution, intent),
        'recent_log': recent_log_compact,
        'player_input': str(user_text or ''),
        'follow_up_pressure': follow_up_pressure,
        'lead_context': lead_context,
        'interlocutor_lead_context': interlocutor_lead_context,
        'interlocutor_lead_behavior_hints': interlocutor_lead_behavior_hints,
        'response_policy': response_policy,
        'uncertainty_hint': eff_uncertainty_hint,
        'narration_obligations': narration_obligations,
        'mechanical_resolution': resolution,
        'scene_advancement': scene_advancement,
        'session': session_view,
        'character': {
            'name': str(character.get('name', '') or ''),
            'role': str(campaign.get('character_role', '') or ''),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'conditions': character.get('conditions', []),
            'attacks': character.get('attacks', []),
            'spells': character.get('spells', {}),
            'skills': character.get('skills', {}),
        }
        if character and isinstance(character, dict)
        else {'name': '', 'role': '', 'hp': {}, 'ac': {}, 'conditions': [], 'attacks': [], 'spells': {}, 'skills': {}},
        'combat': _compress_combat(combat),
        'world_state': world_state_view,
        'world': _compress_world(world),
        'campaign': _compress_campaign(campaign),
        'scene': {
            'public': public_scene,
            'discoverable_clues': discoverable_clues,
            'gm_only': {
                'hidden_facts': gm_only_hidden_facts,
                'discoverable_clues_locked': gm_only_discoverable_locked,
            },
            'clue_records': {'discovered': discovered_clue_records, 'undiscovered': undiscovered_clue_records},
            'visible_clues': discovered_clue_records,
            'discovered_clues': discovered_clue_records,
            'clue_visibility': clue_visibility,
            'pending_leads': active_pending_leads,
            'runtime': runtime,
            'intent': intent,
            'layering_rules': {
                'visible_facts': 'Narrate freely.',
                'discoverable_clues': 'Reveal only when player investigates/searches/questions/observes closely.',
                'hidden_facts': 'Never reveal directly; use only for implications, NPC behavior, atmosphere, indirect clues.',
            },
        },
        'player_expression_contract': {
            'default_action_style': 'third_person',
            'quoted_speech_allowed': True,
            'preserve_user_expression_format': True,
            'example': 'Galinor asks, "What changed at the north gate?" while examining the notice board.',
        },
    }
    return payload
