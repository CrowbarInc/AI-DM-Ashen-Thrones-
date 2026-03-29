"""Authoritative lead schema for the Lead Lifecycle System.

Normalized lead dicts are the single source of truth for shape and defaults.
This module is self-contained; callers integrate elsewhere when ready.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

from game.utils import slugify


class LeadLifecycle(str, Enum):
    HINTED = "hinted"
    DISCOVERED = "discovered"
    COMMITTED = "committed"
    RESOLVED = "resolved"
    OBSOLETE = "obsolete"


class LeadStatus(str, Enum):
    ACTIVE = "active"
    PURSUED = "pursued"
    STALE = "stale"
    RESOLVED = "resolved"


class LeadConfidence(str, Enum):
    RUMOR = "rumor"
    PLAUSIBLE = "plausible"
    CREDIBLE = "credible"
    CONFIRMED = "confirmed"


class LeadType(str, Enum):
    RUMOR = "rumor"
    INVESTIGATION = "investigation"
    OBJECTIVE = "objective"
    THREAT = "threat"
    OPPORTUNITY = "opportunity"
    SOCIAL = "social"
    LOCATION = "location"


_LEAD_LIFECYCLE_VALUES = frozenset(m.value for m in LeadLifecycle)
_LEAD_STATUS_VALUES = frozenset(m.value for m in LeadStatus)
_LEAD_CONFIDENCE_VALUES = frozenset(m.value for m in LeadConfidence)
_LEAD_TYPE_VALUES = frozenset(m.value for m in LeadType)

# Internal ordering for lifecycle: hinted < discovered < committed < resolved < obsolete
_LIFECYCLE_ORDERED_VALUES: tuple[str, ...] = (
    LeadLifecycle.HINTED.value,
    LeadLifecycle.DISCOVERED.value,
    LeadLifecycle.COMMITTED.value,
    LeadLifecycle.RESOLVED.value,
    LeadLifecycle.OBSOLETE.value,
)
_LIFECYCLE_RANK: Dict[str, int] = {v: i for i, v in enumerate(_LIFECYCLE_ORDERED_VALUES)}

# Internal ordering for confidence: rumor < plausible < credible < confirmed
_CONFIDENCE_ORDERED_VALUES: tuple[str, ...] = (
    LeadConfidence.RUMOR.value,
    LeadConfidence.PLAUSIBLE.value,
    LeadConfidence.CREDIBLE.value,
    LeadConfidence.CONFIRMED.value,
)
_CONFIDENCE_RANK: Dict[str, int] = {v: i for i, v in enumerate(_CONFIDENCE_ORDERED_VALUES)}

_LEAD_LIST_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "related_clue_ids",
        "related_npc_ids",
        "related_location_ids",
        "supersedes",
        "unlocks",
        "blocked_by",
    }
)

# Session dict key for the authoritative lead registry (id -> lead dict).
SESSION_LEAD_REGISTRY_KEY = "lead_registry"

_LEAD_SCALAR_DEFAULTS: Dict[str, Any] = {
    "id": "",
    "title": "",
    "summary": "",
    "type": LeadType.RUMOR.value,
    "lifecycle": LeadLifecycle.HINTED.value,
    "status": LeadStatus.ACTIVE.value,
    "confidence": LeadConfidence.RUMOR.value,
    "discovery_source": "",
    "first_discovered_turn": None,
    "last_updated_turn": None,
    "committed_at_turn": None,
    "resolved_at_turn": None,
    "resolution_type": None,
    "resolution_summary": None,
    "obsolete_reason": None,
    "next_step": "",
    "owner_faction_id": None,
    "priority": 0,
    "last_touched_turn": None,
    "stale_after_turns": None,
    "parent_lead_id": None,
    "superseded_by": None,
}


def is_valid_lifecycle(value: Any) -> bool:
    if isinstance(value, LeadLifecycle):
        return True
    s = str(value).strip().lower()
    return s in _LEAD_LIFECYCLE_VALUES


def is_valid_status(value: Any) -> bool:
    if isinstance(value, LeadStatus):
        return True
    s = str(value).strip().lower()
    return s in _LEAD_STATUS_VALUES


def is_valid_confidence(value: Any) -> bool:
    if isinstance(value, LeadConfidence):
        return True
    s = str(value).strip().lower()
    return s in _LEAD_CONFIDENCE_VALUES


def is_valid_type(value: Any) -> bool:
    if isinstance(value, LeadType):
        return True
    s = str(value).strip().lower()
    return s in _LEAD_TYPE_VALUES


def normalize_lead(lead: Any) -> Dict[str, Any]:
    """Backfill missing keys with schema defaults; preserve existing values (including invalid ones).

    Mutates ``lead`` in place when it is a :class:`MutableMapping` (e.g. ``dict``); otherwise
    returns a new dict. List-valued fields get a fresh ``[]`` when absent so templates are not
    shared across records.
    """
    if isinstance(lead, MutableMapping):
        d: MutableMapping[str, Any] = lead
    elif isinstance(lead, Mapping):
        d = dict(lead)
    else:
        d = {}

    for key in _LEAD_LIST_FIELD_NAMES:
        if key not in d:
            d[key] = []

    for key, default in _LEAD_SCALAR_DEFAULTS.items():
        if key not in d:
            d[key] = default

    return d  # type: ignore[return-value]


def _derive_lead_id(lead: Mapping[str, Any]) -> str:
    """Resolve storage id using the same rule as :func:`create_lead` (explicit id or slugified title)."""
    return _as_str(lead.get("id")) or slugify(_as_str(lead.get("title")) or "lead")


def ensure_lead_registry(session: MutableMapping[str, Any]) -> Dict[str, Any]:
    """Ensure ``session`` has a dict registry keyed by lead id; return it without replacing an existing dict."""
    reg = session.get(SESSION_LEAD_REGISTRY_KEY)
    if not isinstance(reg, dict):
        reg = {}
        session[SESSION_LEAD_REGISTRY_KEY] = reg
    return reg


def get_lead(session: MutableMapping[str, Any], lead_id: Any) -> Dict[str, Any] | None:
    """Return the lead dict for ``lead_id``, or ``None`` if missing or not a dict."""
    key = _as_str(lead_id)
    if not key:
        return None
    registry = ensure_lead_registry(session)
    existing = registry.get(key)
    return existing if isinstance(existing, dict) else None


def _debug_dump_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value).strip()


def debug_dump_leads(session: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Return a compact, deterministic snapshot of leads for debugging or tests.

    Reads ``session``'s lead registry only; does not create the registry, modify ``session``,
    or mutate any stored lead dict. Registry keys are iterated in sorted string order; each row
    is a new dict with string fields: id, title, type, lifecycle, status, confidence.
    """
    reg = session.get(SESSION_LEAD_REGISTRY_KEY)
    if not isinstance(reg, dict):
        return []

    rows: List[Dict[str, str]] = []
    for storage_key in sorted(reg.keys(), key=lambda k: str(k)):
        raw = reg[storage_key]
        if not isinstance(raw, dict):
            continue
        sk = _debug_dump_scalar(storage_key)
        lid = _debug_dump_scalar(raw.get("id")) or sk
        rows.append(
            {
                "id": lid,
                "title": _debug_dump_scalar(raw.get("title")),
                "type": _debug_dump_scalar(raw.get("type")),
                "lifecycle": _debug_dump_scalar(raw.get("lifecycle")),
                "status": _debug_dump_scalar(raw.get("status")),
                "confidence": _debug_dump_scalar(raw.get("confidence")),
            }
        )
    return rows


def upsert_lead(session: MutableMapping[str, Any], lead: Any) -> Dict[str, Any]:
    """Insert or update a lead in the session registry by derived id.

    Incoming records are passed through :func:`normalize_lead` before merge. Keys not present on the
    incoming mapping are left unchanged on an existing record; keys that are present overwrite from
    the normalized incoming values.
    """
    registry = ensure_lead_registry(session)
    incoming: Mapping[str, Any] = lead if isinstance(lead, Mapping) else {}
    normalized = normalize_lead(dict(incoming))
    lead_id = _derive_lead_id(normalized)
    normalized["id"] = lead_id

    stored = registry.get(lead_id)
    if not isinstance(stored, dict):
        registry[lead_id] = normalized
        return normalized

    merged: Dict[str, Any] = dict(stored)
    for key in incoming:
        merged[key] = normalized[key]
    merged["id"] = lead_id
    registry[lead_id] = merged
    return merged


def _as_str(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _as_optional_str(value: Any) -> str | None:
    s = _as_str(value)
    return s if s else None


def _as_optional_int(value: Any) -> int | None:
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


def _as_priority(value: Any) -> int:
    n = _as_optional_int(value)
    return 0 if n is None else n


def _as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, str)):
        return []
    out: List[str] = []
    for item in value:
        s = _as_str(item)
        if s:
            out.append(s)
    return out


def _normalize_lifecycle(value: Any) -> str:
    raw = _as_str(value).lower()
    if raw in _LEAD_LIFECYCLE_VALUES:
        return raw
    return LeadLifecycle.HINTED.value


def _normalize_status(value: Any) -> str:
    raw = _as_str(value).lower()
    if raw in _LEAD_STATUS_VALUES:
        return raw
    return LeadStatus.ACTIVE.value


def _normalize_confidence(value: Any) -> str:
    raw = _as_str(value).lower()
    if raw in _LEAD_CONFIDENCE_VALUES:
        return raw
    return LeadConfidence.RUMOR.value


def _normalize_type(value: Any) -> str:
    raw = _as_str(value).lower()
    if raw in _LEAD_TYPE_VALUES:
        return raw
    return LeadType.RUMOR.value


# --- Lead lifecycle invariants (internal; no mutation API here) ---


def _coerce_lifecycle_str(value: Any) -> str | None:
    if isinstance(value, LeadLifecycle):
        return value.value
    s = str(value).strip().lower()
    return s if s in _LEAD_LIFECYCLE_VALUES else None


def _coerce_status_str(value: Any) -> str | None:
    if isinstance(value, LeadStatus):
        return value.value
    s = str(value).strip().lower()
    return s if s in _LEAD_STATUS_VALUES else None


def _coerce_confidence_str(value: Any) -> str | None:
    if isinstance(value, LeadConfidence):
        return value.value
    s = str(value).strip().lower()
    return s if s in _LEAD_CONFIDENCE_VALUES else None


def _lifecycle_rank(value: Any) -> int | None:
    s = _coerce_lifecycle_str(value)
    return _LIFECYCLE_RANK.get(s) if s is not None else None


def _confidence_rank(value: Any) -> int | None:
    s = _coerce_confidence_str(value)
    return _CONFIDENCE_RANK.get(s) if s is not None else None


def _compare_lifecycle_order(a: Any, b: Any) -> int | None:
    """Return ``<0`` if ``a`` precedes ``b``, ``0`` if equal, ``>0`` if ``a`` follows ``b``; ``None`` if either is invalid."""
    ra = _lifecycle_rank(a)
    rb = _lifecycle_rank(b)
    if ra is None or rb is None:
        return None
    return ra - rb


def _compare_confidence_order(a: Any, b: Any) -> int | None:
    """Return ``<0`` if ``a`` is weaker than ``b``, ``0`` if equal, ``>0`` if stronger; ``None`` if either is invalid."""
    ra = _confidence_rank(a)
    rb = _confidence_rank(b)
    if ra is None or rb is None:
        return None
    return ra - rb


def _is_legal_lifecycle_transition(from_lifecycle: Any, to_lifecycle: Any) -> bool:
    """Lifecycle moves are forward-only (non-decreasing rank); invalid endpoints are illegal."""
    rf = _lifecycle_rank(from_lifecycle)
    rt = _lifecycle_rank(to_lifecycle)
    if rf is None or rt is None:
        return False
    return rt >= rf


def _is_legal_confidence_transition(from_confidence: Any, to_confidence: Any) -> bool:
    """Confidence never decreases unless a future bypass flag exists; invalid endpoints are illegal."""
    r_from = _confidence_rank(from_confidence)
    r_to = _confidence_rank(to_confidence)
    if r_from is None or r_to is None:
        return False
    return r_to >= r_from


def _is_status_compatible_with_lifecycle(status: Any, lifecycle: Any) -> bool:
    """Status must match lifecycle rules: resolved lifecycle requires resolved status; obsolete cannot stay pursued."""
    lc = _coerce_lifecycle_str(lifecycle)
    st = _coerce_status_str(status)
    if lc is None or st is None:
        return False
    if lc == LeadLifecycle.RESOLVED.value:
        return st == LeadStatus.RESOLVED.value
    if lc == LeadLifecycle.OBSOLETE.value:
        return st != LeadStatus.PURSUED.value
    return True


def _is_legal_core_field_transition(
    *,
    from_lifecycle: Any,
    to_lifecycle: Any,
    from_confidence: Any,
    to_confidence: Any,
    to_status: Any | None = None,
) -> bool:
    """Single gate for lifecycle forward-only, confidence non-decreasing, and optional status vs target lifecycle."""
    if not _is_legal_lifecycle_transition(from_lifecycle, to_lifecycle):
        return False
    if not _is_legal_confidence_transition(from_confidence, to_confidence):
        return False
    if to_status is not None and not _is_status_compatible_with_lifecycle(to_status, to_lifecycle):
        return False
    return True


def _collect_lead_invariant_violations(lead: Mapping[str, Any]) -> List[str]:
    """Return stable violation codes for a lead snapshot (lifecycle/status/confidence and field presence vs lifecycle)."""
    out: List[str] = []
    lc = _coerce_lifecycle_str(lead.get("lifecycle"))
    if lc is None:
        out.append("invalid_lifecycle")
        return out

    st = _coerce_status_str(lead.get("status"))
    if st is None:
        out.append("invalid_status")
    elif not _is_status_compatible_with_lifecycle(st, lc):
        out.append("status_incompatible_with_lifecycle")

    cf = _coerce_confidence_str(lead.get("confidence"))
    if cf is None:
        out.append("invalid_confidence")

    rank = _LIFECYCLE_RANK[lc]
    committed_rank = _LIFECYCLE_RANK[LeadLifecycle.COMMITTED.value]
    resolved_rank = _LIFECYCLE_RANK[LeadLifecycle.RESOLVED.value]
    obsolete_rank = _LIFECYCLE_RANK[LeadLifecycle.OBSOLETE.value]

    if rank < committed_rank and _as_optional_int(lead.get("committed_at_turn")) is not None:
        out.append("committed_at_turn_before_committed")

    if rank < resolved_rank:
        if _as_optional_int(lead.get("resolved_at_turn")) is not None:
            out.append("resolved_at_turn_before_resolved")
        if _as_optional_str(lead.get("resolution_type")) is not None:
            out.append("resolution_type_before_resolved")
        if _as_optional_str(lead.get("resolution_summary")) is not None:
            out.append("resolution_summary_before_resolved")

    if rank < obsolete_rank and _as_optional_str(lead.get("obsolete_reason")) is not None:
        out.append("obsolete_reason_before_obsolete")

    return out


def _lead_invariants_hold(lead: Mapping[str, Any]) -> bool:
    return not _collect_lead_invariant_violations(lead)


def _ensure_invariants_after_mutation(lead: Mapping[str, Any]) -> None:
    violations = _collect_lead_invariant_violations(lead)
    if violations:
        raise RuntimeError(
            "lead invariants violated after mutation: " + ", ".join(violations)
        )


def _stamp_turn_metadata(
    lead: MutableMapping[str, Any],
    turn: Any,
    *,
    mutated: bool,
    touched: bool = False,
) -> None:
    if not mutated or turn is None:
        return
    t = _as_optional_int(turn)
    if t is None:
        return
    lead["last_updated_turn"] = t
    if touched:
        lead["last_touched_turn"] = t


# --- Public lead lifecycle mutations (legality via internal helpers; illegal ops raise ValueError) ---


def advance_lead_lifecycle(lead: Any, lifecycle: LeadLifecycle | str, *, turn: Any = None) -> Dict[str, Any]:
    """Move ``lead`` forward along the lifecycle axis only; adjust status when required for invariants.

    Raises :class:`ValueError` for backward targets, invalid endpoints, or incompatible snapshots.
    """
    d = normalize_lead(lead)

    from_lc = _coerce_lifecycle_str(d.get("lifecycle"))
    to_lc = lifecycle.value if isinstance(lifecycle, LeadLifecycle) else _coerce_lifecycle_str(lifecycle)
    if from_lc is None:
        raise ValueError("lead has invalid lifecycle; cannot advance")
    if to_lc is None:
        raise ValueError("invalid target lifecycle")

    if from_lc == to_lc:
        return d  # type: ignore[return-value]

    if not _is_legal_lifecycle_transition(from_lc, to_lc):
        raise ValueError(f"illegal lifecycle transition: {from_lc!r} -> {to_lc!r}")

    from_cf = _coerce_confidence_str(d.get("confidence"))
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot advance lifecycle")

    st_before = _coerce_status_str(d.get("status"))
    if st_before is None:
        raise ValueError("lead has invalid status; cannot advance lifecycle")

    st_after = st_before
    if to_lc == LeadLifecycle.RESOLVED.value:
        st_after = LeadStatus.RESOLVED.value
    elif to_lc == LeadLifecycle.OBSOLETE.value and st_before == LeadStatus.PURSUED.value:
        st_after = LeadStatus.ACTIVE.value

    if not _is_legal_core_field_transition(
        from_lifecycle=from_lc,
        to_lifecycle=to_lc,
        from_confidence=from_cf,
        to_confidence=from_cf,
        to_status=st_after,
    ):
        raise ValueError("lifecycle advance rejected: confidence or status incompatible with target lifecycle")

    d["lifecycle"] = to_lc
    d["status"] = st_after
    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=True, touched=False)
    return d  # type: ignore[return-value]


def set_lead_status(lead: Any, status: LeadStatus | str, *, turn: Any = None) -> Dict[str, Any]:
    """Set ``status`` on ``lead`` if it is compatible with the current lifecycle (non-decreasing rules N/A)."""
    d = normalize_lead(lead)

    lc = _coerce_lifecycle_str(d.get("lifecycle"))
    st = status.value if isinstance(status, LeadStatus) else _coerce_status_str(status)
    if lc is None:
        raise ValueError("lead has invalid lifecycle; cannot set status")
    if st is None:
        raise ValueError("invalid target status")

    if not _is_status_compatible_with_lifecycle(st, lc):
        raise ValueError(f"status {st!r} is incompatible with lifecycle {lc!r}")

    prev = _coerce_status_str(d.get("status"))
    if prev == st:
        return d  # type: ignore[return-value]

    d["status"] = st
    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=True, touched=True)
    return d  # type: ignore[return-value]


def refresh_lead_touch(lead: Any, *, turn: Any = None) -> Dict[str, Any]:
    """Update ``last_touched_turn`` when a usable ``turn`` is given and the value changes.

    Does not modify ``last_updated_turn``. Raises :class:`ValueError` for invalid lifecycle or status
    on the snapshot, matching other public mutations.
    """
    d = normalize_lead(lead)

    lc = _coerce_lifecycle_str(d.get("lifecycle"))
    st = _coerce_status_str(d.get("status"))
    if lc is None:
        raise ValueError("lead has invalid lifecycle; cannot refresh touch")
    if st is None:
        raise ValueError("lead has invalid status; cannot refresh touch")

    t = _as_optional_int(turn)
    if t is None:
        return d  # type: ignore[return-value]

    if _as_optional_int(d.get("last_touched_turn")) == t:
        return d  # type: ignore[return-value]

    d["last_touched_turn"] = t
    _ensure_invariants_after_mutation(d)
    return d  # type: ignore[return-value]


def is_lead_stale(lead: Any, *, current_turn: Any = None) -> bool:
    """Return whether ``current_turn`` exceeds the configured stale threshold after ``last_touched_turn``.

    Conservative when data is missing or core fields are invalid. Never true for resolved or obsolete
    lifecycle, resolved status, or pursued leads.
    """
    d = normalize_lead(lead)

    lc = _coerce_lifecycle_str(d.get("lifecycle"))
    st = _coerce_status_str(d.get("status"))
    if lc is None or st is None:
        return False
    if lc in (LeadLifecycle.RESOLVED.value, LeadLifecycle.OBSOLETE.value):
        return False
    if st in (LeadStatus.RESOLVED.value, LeadStatus.PURSUED.value):
        return False

    touched = _as_optional_int(d.get("last_touched_turn"))
    threshold = _as_optional_int(d.get("stale_after_turns"))
    now = _as_optional_int(current_turn)
    if touched is None or threshold is None or now is None:
        return False
    if threshold < 0:
        return False

    return (now - touched) > threshold


def update_lead_staleness(lead: Any, *, current_turn: Any = None) -> Dict[str, Any]:
    """Set status to stale when :func:`is_lead_stale` applies; otherwise no-op.

    Uses :func:`set_lead_status` for real status changes so turn metadata and invariants stay consistent.
    Does not change lifecycle. No-op when already stale or when staleness does not apply.
    """
    d = normalize_lead(lead)

    if not is_lead_stale(d, current_turn=current_turn):
        return d  # type: ignore[return-value]

    st = _coerce_status_str(d.get("status"))
    if st == LeadStatus.STALE.value:
        return d  # type: ignore[return-value]

    return set_lead_status(d, LeadStatus.STALE, turn=current_turn)


def promote_lead_confidence(lead: Any, confidence: LeadConfidence | str, *, turn: Any = None) -> Dict[str, Any]:
    """Raise ``lead`` confidence without decreasing rank."""
    d = normalize_lead(lead)

    from_cf = _coerce_confidence_str(d.get("confidence"))
    to_cf = confidence.value if isinstance(confidence, LeadConfidence) else _coerce_confidence_str(confidence)
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot promote")
    if to_cf is None:
        raise ValueError("invalid target confidence")

    if from_cf == to_cf:
        return d  # type: ignore[return-value]

    if not _is_legal_confidence_transition(from_cf, to_cf):
        raise ValueError(f"illegal confidence transition: {from_cf!r} -> {to_cf!r}")

    d["confidence"] = to_cf
    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=True, touched=True)
    return d  # type: ignore[return-value]


def commit_lead(lead: Any, *, turn: Any = None) -> Dict[str, Any]:
    """Ensure lifecycle is at least committed; normalize stale commitment to active; stamp first commit turn."""
    d = normalize_lead(lead)

    from_lc = _coerce_lifecycle_str(d.get("lifecycle"))
    if from_lc is None:
        raise ValueError("lead has invalid lifecycle; cannot commit")

    from_cf = _coerce_confidence_str(d.get("confidence"))
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot commit")

    committed_val = LeadLifecycle.COMMITTED.value
    to_lc = committed_val if _lifecycle_rank(from_lc) < _LIFECYCLE_RANK[committed_val] else from_lc

    if from_lc != to_lc and not _is_legal_lifecycle_transition(from_lc, to_lc):
        raise ValueError(f"illegal lifecycle transition: {from_lc!r} -> {to_lc!r}")

    st = _coerce_status_str(d.get("status"))
    if st is None:
        raise ValueError("lead has invalid status; cannot commit")

    rank_before = _lifecycle_rank(from_lc)
    committed_rank = _LIFECYCLE_RANK[committed_val]
    crossing_into_committed = rank_before is not None and rank_before < committed_rank

    st_after = st
    if to_lc == committed_val:
        if st == LeadStatus.STALE.value or (
            crossing_into_committed
            and st not in (LeadStatus.ACTIVE.value, LeadStatus.PURSUED.value)
        ):
            st_after = LeadStatus.ACTIVE.value

    if not _is_legal_core_field_transition(
        from_lifecycle=from_lc,
        to_lifecycle=to_lc,
        from_confidence=from_cf,
        to_confidence=from_cf,
        to_status=st_after,
    ):
        raise ValueError("commit rejected: target lifecycle/status/confidence combination is illegal")

    mutated = False
    if from_lc != to_lc:
        d["lifecycle"] = to_lc
        mutated = True
    if st != st_after:
        d["status"] = st_after
        mutated = True

    if rank_before is not None and rank_before < committed_rank and turn is not None:
        t = _as_optional_int(turn)
        if t is not None and d.get("committed_at_turn") is None:
            d["committed_at_turn"] = t
            mutated = True

    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=mutated, touched=mutated)
    return d  # type: ignore[return-value]


def resolve_lead(
    lead: Any,
    *,
    turn: Any = None,
    resolution_type: Any = None,
    resolution_summary: Any = None,
) -> Dict[str, Any]:
    """Move ``lead`` to resolved lifecycle and status; optional resolution metadata and turn stamps."""
    d = normalize_lead(lead)

    from_lc = _coerce_lifecycle_str(d.get("lifecycle"))
    to_lc = LeadLifecycle.RESOLVED.value
    if from_lc is None:
        raise ValueError("lead has invalid lifecycle; cannot resolve")

    from_cf = _coerce_confidence_str(d.get("confidence"))
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot resolve")

    if not _is_legal_lifecycle_transition(from_lc, to_lc):
        raise ValueError(f"illegal lifecycle transition: {from_lc!r} -> {to_lc!r}")

    to_st = LeadStatus.RESOLVED.value
    if not _is_legal_core_field_transition(
        from_lifecycle=from_lc,
        to_lifecycle=to_lc,
        from_confidence=from_cf,
        to_confidence=from_cf,
        to_status=to_st,
    ):
        raise ValueError("resolve rejected: status incompatible with resolved lifecycle")

    mutated = False
    if d.get("lifecycle") != to_lc:
        d["lifecycle"] = to_lc
        mutated = True
    if d.get("status") != to_st:
        d["status"] = to_st
        mutated = True

    if turn is not None:
        t = _as_optional_int(turn)
        if t is not None and d.get("resolved_at_turn") != t:
            d["resolved_at_turn"] = t
            mutated = True

    if resolution_type is not None:
        rt = _as_optional_str(resolution_type)
        if d.get("resolution_type") != rt:
            d["resolution_type"] = rt
            mutated = True

    if resolution_summary is not None:
        rs = _as_optional_str(resolution_summary)
        if d.get("resolution_summary") != rs:
            d["resolution_summary"] = rs
            mutated = True

    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=mutated, touched=mutated)
    return d  # type: ignore[return-value]


def obsolete_lead(lead: Any, *, turn: Any = None, obsolete_reason: Any = None) -> Dict[str, Any]:
    """Move ``lead`` to obsolete lifecycle; never leaves status as pursued; optional reason."""
    d = normalize_lead(lead)

    from_lc = _coerce_lifecycle_str(d.get("lifecycle"))
    to_lc = LeadLifecycle.OBSOLETE.value
    if from_lc is None:
        raise ValueError("lead has invalid lifecycle; cannot obsolete")

    from_cf = _coerce_confidence_str(d.get("confidence"))
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot obsolete")

    st_before = _coerce_status_str(d.get("status"))
    if st_before is None:
        raise ValueError("lead has invalid status; cannot obsolete")

    st_after = LeadStatus.ACTIVE.value if st_before == LeadStatus.PURSUED.value else st_before

    if not _is_legal_lifecycle_transition(from_lc, to_lc):
        raise ValueError(f"illegal lifecycle transition: {from_lc!r} -> {to_lc!r}")

    if not _is_legal_core_field_transition(
        from_lifecycle=from_lc,
        to_lifecycle=to_lc,
        from_confidence=from_cf,
        to_confidence=from_cf,
        to_status=st_after,
    ):
        raise ValueError("obsolete rejected: status incompatible with obsolete lifecycle")

    mutated = False
    if d.get("lifecycle") != to_lc:
        d["lifecycle"] = to_lc
        mutated = True
    if st_before != st_after:
        d["status"] = st_after
        mutated = True

    if obsolete_reason is not None:
        reason = _as_optional_str(obsolete_reason)
        if d.get("obsolete_reason") != reason:
            d["obsolete_reason"] = reason
            mutated = True

    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=mutated, touched=False)
    return d  # type: ignore[return-value]


# --- Session registry mutation wrappers (by lead id; missing id returns None) ---


def advance_session_lead_lifecycle(
    session: MutableMapping[str, Any],
    lead_id: Any,
    lifecycle: LeadLifecycle | str,
    *,
    turn: Any = None,
) -> Dict[str, Any] | None:
    """Advance the registry lead for ``lead_id`` via :func:`advance_lead_lifecycle`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return advance_lead_lifecycle(d, lifecycle, turn=turn)


def set_session_lead_status(
    session: MutableMapping[str, Any],
    lead_id: Any,
    status: LeadStatus | str,
    *,
    turn: Any = None,
) -> Dict[str, Any] | None:
    """Set status on the registry lead for ``lead_id`` via :func:`set_lead_status`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return set_lead_status(d, status, turn=turn)


def promote_session_lead_confidence(
    session: MutableMapping[str, Any],
    lead_id: Any,
    confidence: LeadConfidence | str,
    *,
    turn: Any = None,
) -> Dict[str, Any] | None:
    """Promote confidence on the registry lead for ``lead_id`` via :func:`promote_lead_confidence`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return promote_lead_confidence(d, confidence, turn=turn)


def commit_session_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any] | None:
    """Commit the registry lead for ``lead_id`` via :func:`commit_lead`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return commit_lead(d, turn=turn)


def resolve_session_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    turn: Any = None,
    resolution_type: Any = None,
    resolution_summary: Any = None,
) -> Dict[str, Any] | None:
    """Resolve the registry lead for ``lead_id`` via :func:`resolve_lead`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return resolve_lead(
        d,
        turn=turn,
        resolution_type=resolution_type,
        resolution_summary=resolution_summary,
    )


def obsolete_session_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    turn: Any = None,
    obsolete_reason: Any = None,
) -> Dict[str, Any] | None:
    """Mark the registry lead for ``lead_id`` obsolete via :func:`obsolete_lead`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return obsolete_lead(d, turn=turn, obsolete_reason=obsolete_reason)


def refresh_session_lead_touch(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any] | None:
    """Refresh touch metadata on the registry lead for ``lead_id`` via :func:`refresh_lead_touch`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return refresh_lead_touch(d, turn=turn)


def update_session_lead_staleness(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    current_turn: Any = None,
) -> Dict[str, Any] | None:
    """Update staleness on the registry lead for ``lead_id`` via :func:`update_lead_staleness`; ``None`` if absent."""
    d = get_lead(session, lead_id)
    if d is None:
        return None
    return update_lead_staleness(d, current_turn=current_turn)


def create_lead(
    *,
    title: str,
    summary: str,
    id: str | None = None,
    type: LeadType | str = LeadType.RUMOR,
    lifecycle: LeadLifecycle | str = LeadLifecycle.HINTED,
    status: LeadStatus | str = LeadStatus.ACTIVE,
    confidence: LeadConfidence | str = LeadConfidence.RUMOR,
    discovery_source: str = "",
    first_discovered_turn: int | None = None,
    last_updated_turn: int | None = None,
    committed_at_turn: int | None = None,
    resolved_at_turn: int | None = None,
    resolution_type: str | None = None,
    resolution_summary: str | None = None,
    obsolete_reason: str | None = None,
    next_step: str = "",
    related_clue_ids: Iterable[str] | None = None,
    related_npc_ids: Iterable[str] | None = None,
    related_location_ids: Iterable[str] | None = None,
    owner_faction_id: str | None = None,
    priority: int = 0,
    last_touched_turn: int | None = None,
    stale_after_turns: int | None = None,
    parent_lead_id: str | None = None,
    supersedes: Iterable[str] | None = None,
    superseded_by: str | None = None,
    unlocks: Iterable[str] | None = None,
    blocked_by: Iterable[str] | None = None,
) -> Dict[str, Any]:
    """Build a structurally complete normalized lead dict with stable field names.

    String inputs for enum-like fields are normalized to lowercase known values;
    unknown values fall back to lifecycle defaults (hinted / active / rumor / rumor type).
    """
    title_clean = _as_str(title)
    summary_clean = _as_str(summary)
    lead_id = _as_str(id) or slugify(title_clean or "lead")

    lifecycle_val = lifecycle.value if isinstance(lifecycle, LeadLifecycle) else _normalize_lifecycle(lifecycle)
    status_val = status.value if isinstance(status, LeadStatus) else _normalize_status(status)
    confidence_val = confidence.value if isinstance(confidence, LeadConfidence) else _normalize_confidence(confidence)
    type_val = type.value if isinstance(type, LeadType) else _normalize_type(type)

    return {
        "id": lead_id,
        "title": title_clean or lead_id,
        "summary": summary_clean,
        "type": type_val,
        "lifecycle": lifecycle_val,
        "status": status_val,
        "confidence": confidence_val,
        "discovery_source": _as_str(discovery_source),
        "first_discovered_turn": _as_optional_int(first_discovered_turn),
        "last_updated_turn": _as_optional_int(last_updated_turn),
        "committed_at_turn": _as_optional_int(committed_at_turn),
        "resolved_at_turn": _as_optional_int(resolved_at_turn),
        "resolution_type": _as_optional_str(resolution_type),
        "resolution_summary": _as_optional_str(resolution_summary),
        "obsolete_reason": _as_optional_str(obsolete_reason),
        "next_step": _as_str(next_step),
        "related_clue_ids": _as_str_list(related_clue_ids),
        "related_npc_ids": _as_str_list(related_npc_ids),
        "related_location_ids": _as_str_list(related_location_ids),
        "owner_faction_id": _as_optional_str(owner_faction_id),
        "priority": _as_priority(priority),
        "last_touched_turn": _as_optional_int(last_touched_turn),
        "stale_after_turns": _as_optional_int(stale_after_turns),
        "parent_lead_id": _as_optional_str(parent_lead_id),
        "supersedes": _as_str_list(supersedes),
        "superseded_by": _as_optional_str(superseded_by),
        "unlocks": _as_str_list(unlocks),
        "blocked_by": _as_str_list(blocked_by),
    }
