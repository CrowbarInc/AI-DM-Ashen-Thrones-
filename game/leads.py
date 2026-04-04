"""Authoritative lead schema for the Lead Lifecycle System.

Normalized lead dicts are the single source of truth for shape and defaults.
This module is self-contained; callers integrate elsewhere when ready.
"""
from __future__ import annotations

import copy
from enum import Enum
from typing import AbstractSet, Any, Dict, Iterable, List, Literal, Mapping, MutableMapping, Sequence, TypedDict

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
        "related_faction_ids",
        "related_scene_ids",
        "tags",
        "evidence_clue_ids",
        "consequence_ids",
    }
)

# Id-like / tag lists normalized with :func:`_normalize_id_list` (not lead-to-lead relation buckets).
_LEAD_NORMALIZED_ID_LIST_FIELDS: frozenset[str] = frozenset(
    {
        "related_faction_ids",
        "related_scene_ids",
        "tags",
        "evidence_clue_ids",
        "consequence_ids",
    }
)

# Lead-local relation buckets (not a generic graph engine; see relation helpers below).
LEAD_RELATION_LIST_FIELDS: frozenset[str] = frozenset(
    {
        "related_clue_ids",
        "related_npc_ids",
        "related_location_ids",
        "supersedes",
        "unlocks",
        "blocked_by",
    }
)
LEAD_RELATION_SCALAR_FIELDS: frozenset[str] = frozenset({"parent_lead_id", "superseded_by"})
# Directional relations that may participate in inverse maintenance (subset actually wired in code).
LEAD_RELATION_INVERSE_CAPABLE_DIRECTIONAL: frozenset[str] = frozenset({"supersedes", "parent_lead_id"})

_LEAD_TO_LEAD_LIST_RELATIONS: frozenset[str] = frozenset({"supersedes", "unlocks", "blocked_by"})
_LEAD_RELATION_MUTABLE: frozenset[str] = LEAD_RELATION_LIST_FIELDS | frozenset({"parent_lead_id"})

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
    "commitment_source": None,
    "commitment_strength": None,
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
    "escalation_level": 0,
    "escalation_reason": None,
    "escalated_at_turn": None,
    "unlocked_by_lead_id": None,
    "obsolete_by_lead_id": None,
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
    shared across records. Faction/scene/tag/evidence id lists are always passed through
    :func:`_normalize_id_list`; ``metadata`` is a fresh shallow copy or ``{}`` if missing/invalid.
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

    for key in _LEAD_NORMALIZED_ID_LIST_FIELDS:
        d[key] = _normalize_id_list(d.get(key))

    d["metadata"] = _normalize_metadata(d.get("metadata"))

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


def pending_lead_surfaces_as_active_follow_opportunity(
    session: MutableMapping[str, Any], pending: Mapping[str, Any]
) -> bool:
    """Return whether a scene-runtime ``pending_leads`` row may surface as a live follow opportunity.

    Rows without ``authoritative_lead_id`` keep legacy behavior (True — caller decides structural validity).

    When ``authoritative_lead_id`` is set: require a registry row (fail closed if missing) and exclude
    terminal lifecycles via :func:`is_lead_terminal`.
    """
    aid = _normalize_optional_id(pending.get("authoritative_lead_id"))
    if aid is None:
        return True
    row = get_lead(session, aid)
    if row is None:
        return False
    return not is_lead_terminal(row)


def filter_pending_leads_for_active_follow_surface(
    session: MutableMapping[str, Any], pending: Iterable[Any]
) -> List[Dict[str, Any]]:
    """Deterministic filter: drop pending rows that must not appear as active follow opportunities."""
    out: List[Dict[str, Any]] = []
    for p in pending:
        if not isinstance(p, dict):
            continue
        if pending_lead_surfaces_as_active_follow_opportunity(session, p):
            out.append(p)
    return out


def is_lead_terminal(lead: Any) -> bool:
    """Return whether the lead's lifecycle is terminal (resolved or obsolete).

    The snapshot is evaluated on a shallow copy passed through :func:`normalize_lead` so registry
    rows are not mutated and list fields get schema defaults before reading ``lifecycle``.
    """
    if isinstance(lead, Mapping):
        snap = normalize_lead(dict(lead))
    else:
        snap = normalize_lead({})
    lc = _coerce_lifecycle_str(snap.get("lifecycle"))
    if lc is None:
        return False
    return lc in (LeadLifecycle.RESOLVED.value, LeadLifecycle.OBSOLETE.value)


def list_session_leads(session: Mapping[str, Any], *, include_terminal: bool = True) -> List[Dict[str, Any]]:
    """Return normalized lead dict copies from the session registry, sorted by derived lead id.

    Does not create or mutate ``session`` or stored rows. Skips non-dict registry values.
    When ``include_terminal`` is false, excludes leads whose normalized lifecycle is resolved or obsolete.
    """
    reg = session.get(SESSION_LEAD_REGISTRY_KEY)
    if not isinstance(reg, dict):
        return []

    items: List[tuple[str, Dict[str, Any]]] = []
    for _storage_key, raw in reg.items():
        if not isinstance(raw, dict):
            continue
        c = copy.deepcopy(raw)
        normalize_lead(c)
        sort_id = _derive_lead_id(c)
        items.append((sort_id, c))
    items.sort(key=lambda t: t[0])

    out: List[Dict[str, Any]] = []
    for _, c in items:
        if include_terminal or not is_lead_terminal(c):
            out.append(c)
    return out


def list_active_session_leads(session: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Return non-terminal leads only; equivalent to ``list_session_leads(..., include_terminal=False)``."""
    return list_session_leads(session, include_terminal=False)


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
    is a new dict with string fields: id, title, type, lifecycle, status, confidence, plus terminal
    metadata (``resolved_at_turn``, ``resolution_type``, ``obsolete_reason``) and a comma-separated
    ``consequence_ids`` field when non-empty after normalization.
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
        snap = normalize_lead(dict(raw))
        lid = _debug_dump_scalar(snap.get("id")) or sk
        rat = _as_optional_int(snap.get("resolved_at_turn"))
        cq = _normalize_id_list(snap.get("consequence_ids"))
        rows.append(
            {
                "id": lid,
                "title": _debug_dump_scalar(snap.get("title")),
                "type": _debug_dump_scalar(snap.get("type")),
                "lifecycle": _debug_dump_scalar(snap.get("lifecycle")),
                "status": _debug_dump_scalar(snap.get("status")),
                "confidence": _debug_dump_scalar(snap.get("confidence")),
                "resolved_at_turn": "" if rat is None else str(rat),
                "resolution_type": _debug_dump_scalar(snap.get("resolution_type")),
                "obsolete_reason": _debug_dump_scalar(snap.get("obsolete_reason")),
                "consequence_ids": ",".join(cq),
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


def _normalize_optional_id(value: Any) -> str | None:
    """Strip and validate a single relation id; drop blanks and non-coercible junk."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, Enum):
        s = str(value.value).strip()
        return s if s else None
    if isinstance(value, (int, float)):
        s = str(value).strip()
        return s if s else None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    if isinstance(value, bytes):
        try:
            s = value.decode("utf-8").strip()
        except (UnicodeDecodeError, ValueError):
            return None
        return s if s else None
    if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)):
        return None
    s = str(value).strip()
    return s if s else None


def _normalize_id_list(values: Any) -> List[str]:
    """Normalize id lists: strip, drop blanks/junk, dedupe, preserve first-seen order."""
    if values is None:
        return []
    if isinstance(values, Mapping):
        return []
    if isinstance(values, str):
        one = _normalize_optional_id(values)
        return [one] if one else []
    if isinstance(values, bytes):
        one = _normalize_optional_id(values)
        return [one] if one else []
    if not isinstance(values, Iterable):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for item in values:
        nid = _normalize_optional_id(item)
        if nid is None or nid in seen:
            continue
        seen.add(nid)
        out.append(nid)
    return out


def _normalize_metadata(value: Any) -> Dict[str, Any]:
    """Return a fresh dict; shallow-copy mapping values, else ``{}`` for non-mappings."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


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


def _is_lead_resolved_or_obsolete_lifecycle(row: Mapping[str, Any]) -> bool:
    lc = _coerce_lifecycle_str(row.get("lifecycle"))
    return lc in (LeadLifecycle.RESOLVED.value, LeadLifecycle.OBSOLETE.value)


def _validate_relation_shapes(lead: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    for field in LEAD_RELATION_LIST_FIELDS:
        v = lead.get(field)
        if not isinstance(v, list):
            out.append(f"relation_list_not_list:{field}")
            continue
        bad = False
        for item in v:
            if item is None or not isinstance(item, str):
                out.append(f"relation_list_bad_element:{field}")
                bad = True
                break
        if bad:
            continue
    for field in LEAD_RELATION_SCALAR_FIELDS:
        v = lead.get(field)
        if v is not None and not isinstance(v, str):
            out.append(f"relation_scalar_not_str_or_none:{field}")
    return out


def _validate_no_self_links(lead: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    sid = _derive_lead_id(lead)
    if not sid:
        return out
    for field in ("supersedes", "blocked_by", "unlocks"):
        raw = lead.get(field)
        if not isinstance(raw, list):
            continue
        if sid in raw:
            out.append(f"relation_self_link:{field}")
    p = lead.get("parent_lead_id")
    if isinstance(p, str) and p == sid:
        out.append("relation_self_parent")
    return out


def _validate_inverse_consistency(lead: Mapping[str, Any], registry: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    sid = _derive_lead_id(lead)
    if not sid:
        return out
    sup = lead.get("supersedes")
    if not isinstance(sup, list):
        return out
    for b in sup:
        if not isinstance(b, str):
            continue
        other = registry.get(b)
        if not isinstance(other, Mapping):
            continue
        if _as_optional_str(other.get("superseded_by")) != sid:
            out.append("inverse_supersedes_mismatch")
            break
    return out


def _validate_reference_existence(lead: Mapping[str, Any], registry: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    sid = _derive_lead_id(lead)
    sb = lead.get("superseded_by")
    if isinstance(sb, str) and sb:
        row = registry.get(sb)
        if not isinstance(row, Mapping):
            out.append("superseded_by_target_missing")

    pl = lead.get("parent_lead_id")
    if isinstance(pl, str) and pl:
        row = registry.get(pl)
        if not isinstance(row, Mapping):
            out.append("parent_lead_missing")

    for field in _LEAD_TO_LEAD_LIST_RELATIONS:
        raw = lead.get(field)
        if not isinstance(raw, list):
            continue
        for tid in raw:
            if not isinstance(tid, str):
                continue
            tgt = registry.get(tid)
            if not isinstance(tgt, Mapping):
                out.append(f"relation_target_missing:{field}")
                break
    return out


def _validate_no_parent_cycle(lead: Mapping[str, Any], registry: Mapping[str, Any]) -> List[str]:
    start = _derive_lead_id(lead)
    if not start or start not in registry:
        return []
    seen: set[str] = set()
    cur: str | None = start
    while cur is not None:
        if cur in seen:
            return ["parent_cycle"]
        seen.add(cur)
        row = registry.get(cur)
        if not isinstance(row, Mapping):
            break
        cur = _as_optional_str(row.get("parent_lead_id"))
    return []


def _validate_no_supersedes_cycle(lead: Mapping[str, Any], registry: Mapping[str, Any]) -> List[str]:
    start = _derive_lead_id(lead)
    if not start:
        return []
    row0 = registry.get(start)
    if not isinstance(row0, Mapping):
        return []

    def reaches_start_again(u: str, stack: set[str]) -> bool:
        row = registry.get(u)
        if not isinstance(row, Mapping):
            return False
        subs = row.get("supersedes")
        if not isinstance(subs, list):
            return False
        for v in subs:
            if not isinstance(v, str):
                continue
            if v == start:
                return True
            if v in stack:
                continue
            stack.add(v)
            if reaches_start_again(v, stack):
                return True
            stack.remove(v)
        return False

    subs0 = row0.get("supersedes")
    if not isinstance(subs0, list):
        return []
    stack: set[str] = {start}
    for v in subs0:
        if not isinstance(v, str):
            continue
        if v == start:
            return ["supersedes_cycle"]
        if v in stack:
            continue
        stack.add(v)
        if reaches_start_again(v, stack):
            return ["supersedes_cycle"]
        stack.remove(v)
    return []


def _validate_blocked_by_unlocks_list_constraints(lead: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    for field in ("blocked_by", "unlocks"):
        raw = lead.get(field)
        if not isinstance(raw, list):
            continue
        seen: set[str] = set()
        for x in raw:
            if not isinstance(x, str):
                continue
            if x in seen:
                out.append(f"relation_duplicate_in_{field}")
            seen.add(x)
    return out


def _collect_directional_relation_violations(
    lead: Mapping[str, Any], registry: Mapping[str, Any] | None
) -> List[str]:
    out: List[str] = []
    out.extend(_validate_relation_shapes(lead))
    out.extend(_validate_no_self_links(lead))
    out.extend(_validate_blocked_by_unlocks_list_constraints(lead))
    if registry is None:
        return out
    out.extend(_validate_reference_existence(lead, registry))
    out.extend(_validate_inverse_consistency(lead, registry))
    out.extend(_validate_no_parent_cycle(lead, registry))
    out.extend(_validate_no_supersedes_cycle(lead, registry))
    return out


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


def _ensure_invariants_after_mutation(
    lead: Mapping[str, Any],
    *,
    registry: Mapping[str, Any] | None = None,
    legally_new_parent_id: str | None = None,
    legally_new_supersedes_targets: AbstractSet[str] | None = None,
) -> None:
    if registry is not None and legally_new_parent_id:
        parent_row = registry.get(legally_new_parent_id)
        if isinstance(parent_row, Mapping) and _is_lead_resolved_or_obsolete_lifecycle(parent_row):
            raise ValueError("cannot assign new parent: parent lead is resolved or obsolete")

    if registry is not None and legally_new_supersedes_targets:
        if any(legally_new_supersedes_targets) and isinstance(lead, Mapping):
            if _is_lead_resolved_or_obsolete_lifecycle(lead):
                raise ValueError("cannot add supersedes: source lead is resolved or obsolete")

    violations = _collect_lead_invariant_violations(lead)
    violations.extend(_collect_directional_relation_violations(lead, registry))
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


def _normalize_resolution_type_token(value: Any) -> str:
    """Normalize resolution_type: strip and lowercase; reject blank input."""
    s = _as_str(value).lower()
    if not s:
        raise ValueError("resolution_type is required and cannot be blank")
    return s


def _normalize_obsolete_reason_token(value: Any) -> str:
    """Strip obsolete_reason free text; reject blank."""
    s = _as_str(value).strip()
    if not s:
        raise ValueError("obsolete_reason is required and cannot be blank")
    return s


def _resolution_type_token_or_none(value: Any) -> str | None:
    """Lowercase resolution_type for comparison; ``None`` if missing or blank."""
    s = _as_optional_str(value)
    return s.lower() if s is not None else None


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
    resolution_type: Any,
    resolution_summary: Any = "",
    turn: Any = None,
    consequence_ids: Any | None = None,
    clear_obsolete_reason: bool = True,
) -> Dict[str, Any]:
    """Move ``lead`` to resolved lifecycle and status; stamp resolution metadata and optional consequence ids.

    ``resolution_type`` is required (non-blank), normalized to stripped lowercase. Blank
    ``resolution_summary`` becomes ``None``. By default clears ``obsolete_reason``.
    Idempotent when the lead is already resolved and the effective payload matches.
    """
    rt_token = _normalize_resolution_type_token(resolution_type)
    rs_norm = _as_optional_str(resolution_summary)

    d = normalize_lead(lead)

    from_lc = _coerce_lifecycle_str(d.get("lifecycle"))
    to_lc = LeadLifecycle.RESOLVED.value
    if from_lc is None:
        raise ValueError("lead has invalid lifecycle; cannot resolve")

    if from_lc == LeadLifecycle.OBSOLETE.value:
        raise ValueError("cannot resolve lead in obsolete lifecycle")

    from_cf = _coerce_confidence_str(d.get("confidence"))
    if from_cf is None:
        raise ValueError("lead has invalid confidence; cannot resolve")

    st_now = _coerce_status_str(d.get("status"))
    if st_now is None:
        raise ValueError("lead has invalid status; cannot resolve")

    to_st = LeadStatus.RESOLVED.value

    if not _is_legal_lifecycle_transition(from_lc, to_lc):
        raise ValueError(f"illegal lifecycle transition: {from_lc!r} -> {to_lc!r}")

    if not _is_legal_core_field_transition(
        from_lifecycle=from_lc,
        to_lifecycle=to_lc,
        from_confidence=from_cf,
        to_confidence=from_cf,
        to_status=to_st,
    ):
        raise ValueError("resolve rejected: status incompatible with resolved lifecycle")

    cq_target = _normalize_id_list(consequence_ids) if consequence_ids is not None else _normalize_id_list(d.get("consequence_ids"))

    obsolete_ok = _as_optional_str(d.get("obsolete_reason")) is None
    if from_lc == LeadLifecycle.RESOLVED.value:
        cur_rt = _resolution_type_token_or_none(d.get("resolution_type"))
        cur_rs = _as_optional_str(d.get("resolution_summary"))
        cur_cq = _normalize_id_list(d.get("consequence_ids"))
        if (
            obsolete_ok
            and cur_rt == rt_token
            and cur_rs == rs_norm
            and cur_cq == cq_target
            and d.get("lifecycle") == to_lc
            and d.get("status") == to_st
        ):
            _ensure_invariants_after_mutation(d)
            _stamp_turn_metadata(d, turn, mutated=False, touched=False)
            return d  # type: ignore[return-value]

    if not clear_obsolete_reason and _as_optional_str(d.get("obsolete_reason")) is not None:
        raise ValueError(
            "cannot resolve while obsolete_reason is set; pass clear_obsolete_reason=True to clear it"
        )

    mutated = False
    entering_resolved = from_lc != LeadLifecycle.RESOLVED.value

    if d.get("lifecycle") != to_lc:
        d["lifecycle"] = to_lc
        mutated = True
    if d.get("status") != to_st:
        d["status"] = to_st
        mutated = True

    if d.get("resolution_type") != rt_token:
        d["resolution_type"] = rt_token
        mutated = True
    if d.get("resolution_summary") != rs_norm:
        d["resolution_summary"] = rs_norm
        mutated = True

    if consequence_ids is not None:
        if _normalize_id_list(d.get("consequence_ids")) != cq_target:
            d["consequence_ids"] = cq_target
            mutated = True

    if clear_obsolete_reason and _as_optional_str(d.get("obsolete_reason")) is not None:
        d["obsolete_reason"] = None
        mutated = True

    if entering_resolved:
        t = _as_optional_int(turn)
        if t is not None and d.get("resolved_at_turn") != t:
            d["resolved_at_turn"] = t
            mutated = True

    _ensure_invariants_after_mutation(d)
    _stamp_turn_metadata(d, turn, mutated=mutated, touched=False)
    return d  # type: ignore[return-value]


def obsolete_lead(
    lead: Any,
    *,
    obsolete_reason: Any,
    turn: Any = None,
    consequence_ids: Any | None = None,
    clear_resolution_fields: bool = False,
) -> Dict[str, Any]:
    """Move ``lead`` to obsolete lifecycle; never leaves status as pursued.

    ``obsolete_reason`` is required (non-blank after strip). By default resolution metadata is left
    unchanged (``clear_resolution_fields=False``), which stays invariant-safe. Idempotent when
    already obsolete with the same effective payload.
    """
    reason_token = _normalize_obsolete_reason_token(obsolete_reason)

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

    cq_target = _normalize_id_list(consequence_ids) if consequence_ids is not None else _normalize_id_list(d.get("consequence_ids"))

    def _resolution_fields_cleared() -> bool:
        return (
            _as_optional_int(d.get("resolved_at_turn")) is None
            and _as_optional_str(d.get("resolution_type")) is None
            and _as_optional_str(d.get("resolution_summary")) is None
        )

    if from_lc == LeadLifecycle.OBSOLETE.value:
        cur_reason = _as_str(d.get("obsolete_reason")).strip()
        cur_cq = _normalize_id_list(d.get("consequence_ids"))
        res_ok = (not clear_resolution_fields) or _resolution_fields_cleared()
        if (
            res_ok
            and cur_reason == reason_token
            and cur_cq == cq_target
            and d.get("lifecycle") == to_lc
            and d.get("status") == st_after
        ):
            _ensure_invariants_after_mutation(d)
            _stamp_turn_metadata(d, turn, mutated=False, touched=False)
            return d  # type: ignore[return-value]

    mutated = False
    if d.get("lifecycle") != to_lc:
        d["lifecycle"] = to_lc
        mutated = True
    if st_before != st_after:
        d["status"] = st_after
        mutated = True

    if _as_str(d.get("obsolete_reason")).strip() != reason_token:
        d["obsolete_reason"] = reason_token
        mutated = True

    if consequence_ids is not None:
        if _normalize_id_list(d.get("consequence_ids")) != cq_target:
            d["consequence_ids"] = cq_target
            mutated = True

    if clear_resolution_fields:
        if _as_optional_int(d.get("resolved_at_turn")) is not None:
            d["resolved_at_turn"] = None
            mutated = True
        if _as_optional_str(d.get("resolution_type")) is not None:
            d["resolution_type"] = None
            mutated = True
        if _as_optional_str(d.get("resolution_summary")) is not None:
            d["resolution_summary"] = None
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


def commit_session_lead_with_context(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    turn: Any = None,
    commitment_source: Any = None,
    commitment_strength: Any = None,
    next_step: Any = None,
) -> Dict[str, Any] | None:
    """Apply explicit player commitment to a stored lead: :func:`commit_lead`, status ``pursued``, optional context.

    Uses :func:`commit_lead` and :func:`set_lead_status` only for lifecycle/status; does not downgrade or
    touch resolved/obsolete leads. ``commitment_source`` / ``commitment_strength`` update only when those
    keyword arguments are not ``None``. ``next_step`` updates only when provided and non-blank after strip.
    """
    d = get_lead(session, lead_id)
    if d is None:
        return None
    normalize_lead(d)
    if _is_lead_resolved_or_obsolete_lifecycle(d):
        return d

    commit_lead(d, turn=turn)
    set_lead_status(d, LeadStatus.PURSUED, turn=turn)

    meta_mut = False
    if commitment_source is not None:
        val = _as_optional_str(commitment_source)
        if d.get("commitment_source") != val:
            d["commitment_source"] = val
            meta_mut = True
    if commitment_strength is not None:
        val = _as_optional_int(commitment_strength)
        if d.get("commitment_strength") != val:
            d["commitment_strength"] = val
            meta_mut = True
    if next_step is not None:
        ns = _as_str(next_step)
        if ns and d.get("next_step") != ns:
            d["next_step"] = ns
            meta_mut = True

    if meta_mut:
        _ensure_invariants_after_mutation(d)
        _stamp_turn_metadata(d, turn, mutated=True, touched=True)

    return d


def resolve_session_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    resolution_type: Any,
    resolution_summary: Any = "",
    turn: Any = None,
    consequence_ids: Any | None = None,
) -> Dict[str, Any]:
    """Resolve the registry lead for ``lead_id`` in place via :func:`resolve_lead`.

    Raises :class:`ValueError` when ``lead_id`` is missing/blank or no lead exists for that id.
    """
    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    d = get_lead(session, sid)
    if d is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    out = resolve_lead(
        d,
        resolution_type=resolution_type,
        resolution_summary=resolution_summary,
        turn=turn,
        consequence_ids=consequence_ids,
    )
    reg = ensure_lead_registry(session)
    _ensure_invariants_after_mutation(out, registry=reg)
    return out


def obsolete_session_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    obsolete_reason: Any,
    turn: Any = None,
    consequence_ids: Any | None = None,
) -> Dict[str, Any]:
    """Mark the registry lead for ``lead_id`` obsolete in place via :func:`obsolete_lead`.

    Raises :class:`ValueError` when ``lead_id`` is missing/blank or no lead exists for that id.
    """
    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    d = get_lead(session, sid)
    if d is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    out = obsolete_lead(
        d,
        obsolete_reason=obsolete_reason,
        turn=turn,
        consequence_ids=consequence_ids,
    )
    reg = ensure_lead_registry(session)
    _ensure_invariants_after_mutation(out, registry=reg)
    return out


def obsolete_superseded_lead(
    session: MutableMapping[str, Any],
    lead_id: Any,
    *,
    replaced_by_lead_id: Any = None,
    turn: Any = None,
    consequence_ids: Any | None = None,
) -> Dict[str, Any]:
    """Mark ``lead_id`` obsolete with reason ``superseded``; optionally wire ``replaced_by_lead_id`` via ``supersedes``.

    Validates existence of the target lead. When ``replaced_by_lead_id`` is set, the replacer must
    exist and the target's existing ``superseded_by`` must be absent or already equal to it; then
    :func:`add_lead_relation` ensures ``supersedes`` / ``superseded_by`` without duplicating edges.
    Uses :func:`obsolete_session_lead` with default resolution-field preservation (Block 1 semantics).
    """
    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    target = get_lead(session, sid)
    if target is None:
        raise ValueError(f"lead does not exist: {sid!r}")

    rid: str | None = None
    if replaced_by_lead_id is not None:
        rid = _normalize_optional_id(replaced_by_lead_id)
        if rid is None:
            raise ValueError("replaced_by_lead_id is required when provided")
        if rid == sid:
            raise ValueError("replaced_by_lead_id cannot equal lead_id")
        if get_lead(session, rid) is None:
            raise ValueError(f"target lead does not exist: {rid!r}")
        normalize_lead(target)
        existing_sb = _as_optional_str(target.get("superseded_by"))
        if existing_sb is not None and existing_sb != rid:
            raise ValueError(
                f"lead {sid!r} already superseded_by {existing_sb!r}; incompatible with replaced_by_lead_id {rid!r}"
            )

    out = obsolete_session_lead(
        session,
        sid,
        obsolete_reason="superseded",
        turn=turn,
        consequence_ids=consequence_ids,
    )
    if rid is not None:
        add_lead_relation(session, rid, "supersedes", sid, turn=turn)
    return out


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


# --- Lead-local relationship helpers (authoritative registry; not a generic graph engine) ---


def add_lead_relation(
    session: MutableMapping[str, Any],
    lead_id: Any,
    relation: str,
    target_id: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any]:
    """Add one relation target on a stored lead (lead-local fields only; not a generic edge store).

    Validates registry membership for lead-to-lead edges. Maintains ``superseded_by`` when using
    ``supersedes``. Stamps ``last_updated_turn`` / ``last_touched_turn`` only when something changes.
    """
    rel = _as_str(relation)
    if rel not in _LEAD_RELATION_MUTABLE:
        raise ValueError(f"unsupported relation field: {relation!r}")

    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)
    reg = ensure_lead_registry(session)

    tid = _normalize_optional_id(target_id)
    if tid is None:
        raise ValueError("target_id is required")

    target_lead: Dict[str, Any] | None = None
    if rel in _LEAD_TO_LEAD_LIST_RELATIONS or rel == "parent_lead_id":
        if tid == sid:
            raise ValueError("lead cannot relate to itself")
        target_lead = get_lead(session, tid)
        if target_lead is None:
            raise ValueError(f"target lead does not exist: {tid!r}")
        normalize_lead(target_lead)

    if rel == "parent_lead_id":
        assert target_lead is not None
        prev = _as_optional_str(source.get("parent_lead_id"))
        if prev == tid:
            return source
        source["parent_lead_id"] = tid
        _ensure_invariants_after_mutation(
            source,
            registry=reg,
            legally_new_parent_id=tid,
        )
        _stamp_turn_metadata(source, turn, mutated=True, touched=True)
        return source

    assert rel in LEAD_RELATION_LIST_FIELDS
    cur = _normalize_id_list(source.get(rel))
    if tid in cur:
        return source

    new_sup: frozenset[str] | None = None
    if rel == "supersedes":
        new_sup = frozenset({tid})

    target_touched = False
    if rel == "supersedes":
        assert target_lead is not None
        if _as_optional_str(target_lead.get("superseded_by")) != sid:
            target_lead["superseded_by"] = sid
            _ensure_invariants_after_mutation(target_lead, registry=reg)
            target_touched = True

    source[rel] = cur + [tid]
    _ensure_invariants_after_mutation(
        source,
        registry=reg,
        legally_new_supersedes_targets=new_sup,
    )
    _stamp_turn_metadata(source, turn, mutated=True, touched=True)

    if rel == "supersedes" and target_touched:
        assert target_lead is not None
        _stamp_turn_metadata(target_lead, turn, mutated=True, touched=True)

    return source


def remove_lead_relation(
    session: MutableMapping[str, Any],
    lead_id: Any,
    relation: str,
    target_id: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any]:
    """Remove one relation target; no-op when absent. Keeps ``superseded_by`` consistent for ``supersedes``."""
    rel = _as_str(relation)
    if rel not in _LEAD_RELATION_MUTABLE:
        raise ValueError(f"unsupported relation field: {relation!r}")

    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)
    reg = ensure_lead_registry(session)

    tid = _normalize_optional_id(target_id)
    if tid is None:
        return source

    if rel == "parent_lead_id":
        prev = _as_optional_str(source.get("parent_lead_id"))
        if prev != tid:
            return source
        source["parent_lead_id"] = None
        _ensure_invariants_after_mutation(source, registry=reg)
        _stamp_turn_metadata(source, turn, mutated=True, touched=True)
        return source

    assert rel in LEAD_RELATION_LIST_FIELDS
    cur = _normalize_id_list(source.get(rel))
    if tid not in cur:
        return source

    source[rel] = [x for x in cur if x != tid]
    _ensure_invariants_after_mutation(source, registry=reg)
    _stamp_turn_metadata(source, turn, mutated=True, touched=True)

    if rel == "supersedes":
        other = get_lead(session, tid)
        if other is not None and _as_optional_str(other.get("superseded_by")) == sid:
            other["superseded_by"] = None
            _ensure_invariants_after_mutation(other, registry=reg)
            _stamp_turn_metadata(other, turn, mutated=True, touched=True)

    return source


def replace_lead_relations(
    session: MutableMapping[str, Any],
    lead_id: Any,
    relation: str,
    target_ids: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any]:
    """Replace an entire list relation or the sole ``parent_lead_id``; normalizes and validates like add."""
    rel = _as_str(relation)
    if rel not in _LEAD_RELATION_MUTABLE:
        raise ValueError(f"unsupported relation field: {relation!r}")

    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)
    reg = ensure_lead_registry(session)

    new_list = _normalize_id_list(target_ids)

    if rel == "parent_lead_id":
        if len(new_list) > 1:
            raise ValueError("parent_lead_id accepts at most one target id")
        new_parent = new_list[0] if new_list else None
        if new_parent is not None:
            if new_parent == sid:
                raise ValueError("lead cannot relate to itself")
            if get_lead(session, new_parent) is None:
                raise ValueError(f"target lead does not exist: {new_parent!r}")
        prev = _as_optional_str(source.get("parent_lead_id"))
        if prev == new_parent:
            return source
        source["parent_lead_id"] = new_parent
        _ensure_invariants_after_mutation(
            source,
            registry=reg,
            legally_new_parent_id=new_parent if new_parent else None,
        )
        _stamp_turn_metadata(source, turn, mutated=True, touched=True)
        return source

    if rel == "supersedes":
        for tid in new_list:
            if tid == sid:
                raise ValueError("lead cannot relate to itself")
            if get_lead(session, tid) is None:
                raise ValueError(f"target lead does not exist: {tid!r}")
        old_list = _normalize_id_list(source.get("supersedes"))
        if old_list == new_list:
            return source
        old_set, new_set = set(old_list), set(new_list)
        touched: Dict[int, MutableMapping[str, Any]] = {}
        for bid in old_set - new_set:
            other = get_lead(session, bid)
            if other is None:
                continue
            normalize_lead(other)
            if _as_optional_str(other.get("superseded_by")) == sid:
                other["superseded_by"] = None
                touched[id(other)] = other
        for bid in new_set:
            other = get_lead(session, bid)
            assert other is not None
            normalize_lead(other)
            if _as_optional_str(other.get("superseded_by")) != sid:
                other["superseded_by"] = sid
                touched[id(other)] = other
        source["supersedes"] = new_list
        touched[id(source)] = source
        new_edges = frozenset(new_set - old_set)
        for L in touched.values():
            _ensure_invariants_after_mutation(
                L,
                registry=reg,
                legally_new_supersedes_targets=new_edges if L is source else None,
            )
        for L in touched.values():
            _stamp_turn_metadata(L, turn, mutated=True, touched=True)
        return source

    assert rel in LEAD_RELATION_LIST_FIELDS
    if rel in _LEAD_TO_LEAD_LIST_RELATIONS:
        for tid in new_list:
            if tid == sid:
                raise ValueError("lead cannot relate to itself")
            if get_lead(session, tid) is None:
                raise ValueError(f"target lead does not exist: {tid!r}")

    old_list = _normalize_id_list(source.get(rel))
    if old_list == new_list:
        return source
    source[rel] = new_list
    _ensure_invariants_after_mutation(source, registry=reg)
    _stamp_turn_metadata(source, turn, mutated=True, touched=True)
    return source


def get_related_lead_ids(
    session: MutableMapping[str, Any],
    lead_id: Any,
    relation: str,
) -> List[str]:
    """Return normalized lead ids for a lead-to-lead relation (lists or ``parent_lead_id``)."""
    rel = _as_str(relation)
    if rel not in _LEAD_TO_LEAD_LIST_RELATIONS and rel != "parent_lead_id":
        raise ValueError(f"not a lead-to-lead relation field: {relation!r}")

    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)

    if rel == "parent_lead_id":
        p = _as_optional_str(source.get("parent_lead_id"))
        return [p] if p else []
    return _normalize_id_list(source.get(rel))


def add_lead_tag(
    session: MutableMapping[str, Any],
    lead_id: Any,
    tag: Any,
    *,
    turn: Any = None,
) -> Dict[str, Any]:
    """Append one normalized tag when absent; no-op for blank tags or duplicates."""
    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)
    reg = ensure_lead_registry(session)

    t = _normalize_optional_id(tag)
    if t is None:
        return source
    cur = _normalize_id_list(source.get("tags"))
    if t in cur:
        return source
    source["tags"] = cur + [t]
    _ensure_invariants_after_mutation(source, registry=reg)
    _stamp_turn_metadata(source, turn, mutated=True, touched=True)
    return source


def get_lead_tags(session: MutableMapping[str, Any], lead_id: Any) -> List[str]:
    """Return a normalized, deduped tag list (fresh list object)."""
    sid = _normalize_optional_id(lead_id)
    if sid is None:
        raise ValueError("lead_id is required")
    source = get_lead(session, sid)
    if source is None:
        raise ValueError(f"lead does not exist: {sid!r}")
    normalize_lead(source)
    return _normalize_id_list(source.get("tags"))


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
    commitment_source: str | None = None,
    commitment_strength: int | None = None,
    resolved_at_turn: int | None = None,
    resolution_type: str | None = None,
    resolution_summary: str | None = None,
    obsolete_reason: str | None = None,
    escalation_level: int = 0,
    escalation_reason: str | None = None,
    escalated_at_turn: int | None = None,
    unlocked_by_lead_id: str | None = None,
    obsolete_by_lead_id: str | None = None,
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
    related_faction_ids: Iterable[str] | None = None,
    related_scene_ids: Iterable[str] | None = None,
    tags: Iterable[str] | None = None,
    evidence_clue_ids: Iterable[str] | None = None,
    consequence_ids: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
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
        "commitment_source": _as_optional_str(commitment_source),
        "commitment_strength": _as_optional_int(commitment_strength),
        "resolved_at_turn": _as_optional_int(resolved_at_turn),
        "resolution_type": _as_optional_str(resolution_type),
        "resolution_summary": _as_optional_str(resolution_summary),
        "obsolete_reason": _as_optional_str(obsolete_reason),
        "escalation_level": _as_priority(escalation_level),
        "escalation_reason": _as_optional_str(escalation_reason),
        "escalated_at_turn": _as_optional_int(escalated_at_turn),
        "unlocked_by_lead_id": _as_optional_str(unlocked_by_lead_id),
        "obsolete_by_lead_id": _as_optional_str(obsolete_by_lead_id),
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
        "related_faction_ids": _normalize_id_list(related_faction_ids),
        "related_scene_ids": _normalize_id_list(related_scene_ids),
        "tags": _normalize_id_list(tags),
        "evidence_clue_ids": _normalize_id_list(evidence_clue_ids),
        "consequence_ids": _normalize_id_list(consequence_ids),
        "metadata": _normalize_metadata(metadata),
    }


# --- Lead progression reconciliation (deterministic; no narration) ---


def lead_reference_turn(lead: Any) -> int | None:
    """Reference turn for staleness / unattended age: first present in priority order."""
    d = lead if isinstance(lead, Mapping) else {}
    for key in ("last_touched_turn", "last_updated_turn", "committed_at_turn", "first_discovered_turn"):
        t = _as_optional_int(d.get(key))
        if t is not None:
            return t
    return None


def lead_staleness_age(current_turn: Any, lead: Any) -> int | None:
    """``current_turn - reference_turn`` when both are usable; otherwise ``None``."""
    now = _as_optional_int(current_turn)
    ref = lead_reference_turn(lead)
    if now is None or ref is None:
        return None
    return now - ref


def should_decay_lead_to_stale(lead: Any, current_turn: Any) -> bool:
    """Whether an active/pursued non-terminal lead has aged past ``stale_after_turns`` (positive int)."""
    if is_lead_terminal(lead):
        return False
    d = normalize_lead(dict(lead)) if isinstance(lead, Mapping) else normalize_lead({})
    st = _coerce_status_str(d.get("status"))
    if st not in (LeadStatus.ACTIVE.value, LeadStatus.PURSUED.value):
        return False
    thresh = _as_optional_int(d.get("stale_after_turns"))
    if thresh is None or thresh <= 0:
        return False
    age = lead_staleness_age(current_turn, d)
    if age is None:
        return False
    return age >= thresh


def compute_threat_escalation_level(lead: Any, current_turn: Any) -> int:
    """Unattended threat tier from reference age (v1); non-threat and terminal leads => 0."""
    d = normalize_lead(dict(lead)) if isinstance(lead, Mapping) else normalize_lead({})
    if _normalize_type(d.get("type")) != LeadType.THREAT.value:
        return 0
    if is_lead_terminal(d):
        return 0
    age = lead_staleness_age(current_turn, d)
    if age is None:
        return 0
    if age < 0:
        age = 0
    if age < 2:
        tier = 0
    elif age <= 3:
        tier = 1
    elif age <= 5:
        tier = 2
    else:
        tier = 3
    return max(0, min(3, tier))


def _reconcile_turn_int(current_turn: Any) -> int:
    t = _as_optional_int(current_turn)
    return 0 if t is None else t


def _sorted_registry_storage_keys(registry: Mapping[str, Any]) -> List[Any]:
    """Storage keys for dict rows, ordered by derived lead id then key string."""
    pairs: List[tuple[str, str, Any]] = []
    for sk, raw in registry.items():
        if not isinstance(raw, dict):
            continue
        snap = normalize_lead(dict(raw))
        did = _derive_lead_id(snap)
        pairs.append((did, str(sk), sk))
    pairs.sort(key=lambda x: (x[0], x[1]))
    return [p[2] for p in pairs]


def _reconcile_lead_stale_and_threat_escalation_inplace(
    row: MutableMapping[str, Any],
    registry: Mapping[str, Any],
    current_turn: int,
) -> tuple[List[str], tuple[int, int] | None]:
    """Apply stale decay and threat escalation to one stored row; return ``(codes, esc_from_to)``."""
    normalize_lead(row)
    codes: List[str] = []
    esc_pair: tuple[int, int] | None = None

    if should_decay_lead_to_stale(row, current_turn):
        st = _coerce_status_str(row.get("status"))
        if st in (LeadStatus.ACTIVE.value, LeadStatus.PURSUED.value):
            row["status"] = LeadStatus.STALE.value
            row["last_updated_turn"] = current_turn
            codes.append("staled")
            _ensure_invariants_after_mutation(row, registry=registry)

    ty = _normalize_type(row.get("type"))
    if ty == LeadType.THREAT.value and not is_lead_terminal(row):
        new_lvl = compute_threat_escalation_level(row, current_turn)
        old_lvl = max(0, min(3, _as_priority(row.get("escalation_level"))))
        cur_reason = _as_optional_str(row.get("escalation_reason"))
        if new_lvl == 0:
            need_esc = (
                old_lvl != new_lvl
                or cur_reason is not None
                or _as_optional_int(row.get("escalated_at_turn")) is not None
            )
        else:
            need_esc = old_lvl != new_lvl or cur_reason != "unattended_threat"
        if need_esc:
            row["escalation_level"] = new_lvl
            if new_lvl == 0:
                row["escalation_reason"] = None
                row["escalated_at_turn"] = None
            else:
                row["escalation_reason"] = "unattended_threat"
                if new_lvl > old_lvl:
                    row["escalated_at_turn"] = current_turn
            if old_lvl != new_lvl:
                esc_pair = (old_lvl, new_lvl)
            codes.append("escalated")
            _ensure_invariants_after_mutation(row, registry=registry)

    return codes, esc_pair


def reconcile_single_lead_progression(
    lead: Any,
    registry: Mapping[str, Any],
    current_turn: Any,
) -> tuple[Dict[str, Any], List[str]]:
    """Apply deterministic stale decay and threat escalation to a copy of ``lead`` (local transitions only)."""
    d = normalize_lead(copy.deepcopy(lead if isinstance(lead, Mapping) else {}))
    codes, _ = _reconcile_lead_stale_and_threat_escalation_inplace(
        d, registry, _reconcile_turn_int(current_turn)
    )
    return d, codes


def effective_lead_pressure_score(lead: Any, current_turn: Any) -> int:
    """Deterministic pressure score for downstream prompt use (not wired here). ``current_turn`` reserved."""
    _ = current_turn
    d = normalize_lead(dict(lead)) if isinstance(lead, Mapping) else normalize_lead({})
    score = _as_priority(d.get("priority"))
    score += max(0, min(3, _as_priority(d.get("escalation_level")))) * 2
    st = _coerce_status_str(d.get("status"))
    if st == LeadStatus.PURSUED.value:
        score += 2
    if st == LeadStatus.STALE.value:
        score += 1
    return score


def _pick_superseding_lead_id(registry: Mapping[str, Any], b_id: str, b_row: Mapping[str, Any]) -> str | None:
    """Smallest valid superseder id: ``B.superseded_by`` target and/or any ``A`` with ``B in A.supersedes``."""
    cands: set[str] = set()
    sb = _as_optional_str(b_row.get("superseded_by"))
    if sb:
        a_row = registry.get(sb)
        if isinstance(a_row, dict):
            cands.add(sb)
    for raw in registry.values():
        if not isinstance(raw, dict):
            continue
        aid = _derive_lead_id(normalize_lead(dict(raw)))
        sup = _normalize_id_list(raw.get("supersedes"))
        if b_id in sup:
            cands.add(aid)
    valid: List[str] = []
    for aid in cands:
        if aid == b_id:
            continue
        a_row = registry.get(aid)
        if not isinstance(a_row, dict):
            continue
        if is_lead_terminal(a_row):
            continue
        valid.append(aid)
    return min(valid) if valid else None


def _apply_unlocks_from_resolved_sources(
    registry: MutableMapping[str, Any],
    current_turn: int,
) -> List[Dict[str, str]]:
    unlocked: List[Dict[str, str]] = []
    for sk in _sorted_registry_storage_keys(registry):
        source = registry.get(sk)
        if not isinstance(source, dict):
            continue
        normalize_lead(source)
        sid = _derive_lead_id(source)
        if _coerce_lifecycle_str(source.get("lifecycle")) != LeadLifecycle.RESOLVED.value:
            continue
        for tid in sorted(_normalize_id_list(source.get("unlocks"))):
            target = registry.get(tid)
            if not isinstance(target, dict):
                continue
            normalize_lead(target)
            if is_lead_terminal(target):
                continue
            changed = False
            lc = _coerce_lifecycle_str(target.get("lifecycle"))
            if lc == LeadLifecycle.HINTED.value:
                advance_lead_lifecycle(target, LeadLifecycle.DISCOVERED, turn=current_turn)
                changed = True
            st = _coerce_status_str(target.get("status"))
            if st == LeadStatus.STALE.value:
                target["status"] = LeadStatus.ACTIVE.value
                _ensure_invariants_after_mutation(target, registry=registry)
                changed = True
            if _as_optional_int(target.get("first_discovered_turn")) is None:
                target["first_discovered_turn"] = current_turn
                changed = True
            if not _as_str(target.get("discovery_source")):
                target["discovery_source"] = f"unlocked_by:{sid}"
                changed = True
            if not _as_optional_str(target.get("unlocked_by_lead_id")):
                target["unlocked_by_lead_id"] = sid
                changed = True
            if changed:
                target["last_updated_turn"] = current_turn
                _ensure_invariants_after_mutation(target, registry=registry)
                unlocked.append({"source_lead_id": sid, "target_lead_id": tid})
    return unlocked


def _apply_supersession_retirement(
    registry: MutableMapping[str, Any],
    current_turn: int,
) -> List[Dict[str, str]]:
    obsoleted: List[Dict[str, str]] = []
    for sk in _sorted_registry_storage_keys(registry):
        b = registry.get(sk)
        if not isinstance(b, dict):
            continue
        normalize_lead(b)
        b_id = _derive_lead_id(b)
        lc_b = _coerce_lifecycle_str(b.get("lifecycle"))
        if lc_b == LeadLifecycle.RESOLVED.value:
            continue
        if is_lead_terminal(b):
            continue
        a_id = _pick_superseding_lead_id(registry, b_id, b)
        if a_id is None:
            continue
        a_row = registry.get(a_id)
        if not isinstance(a_row, dict) or is_lead_terminal(a_row):
            continue
        prev_st = _coerce_status_str(b.get("status"))
        b["lifecycle"] = LeadLifecycle.OBSOLETE.value
        st_after = LeadStatus.ACTIVE.value if prev_st == LeadStatus.PURSUED.value else prev_st
        if st_after is not None:
            b["status"] = st_after
        b["obsolete_reason"] = "superseded"
        if not _as_optional_str(b.get("superseded_by")):
            b["superseded_by"] = a_id
        b["obsolete_by_lead_id"] = a_id
        b["last_updated_turn"] = current_turn
        _ensure_invariants_after_mutation(b, registry=registry)
        obsoleted.append({"source_lead_id": a_id, "target_lead_id": b_id})
    return obsoleted


def reconcile_session_lead_progression(
    session: MutableMapping[str, Any],
    *,
    turn: Any = None,
) -> Dict[str, Any]:
    """One deterministic reconciliation pass: stale decay, threat escalation, unlocks, supersession retirement."""
    reg = ensure_lead_registry(session)
    if turn is not None:
        current_turn = _reconcile_turn_int(turn)
    else:
        current_turn = _reconcile_turn_int(session.get("turn_counter"))

    staled: List[str] = []
    escalated: List[Dict[str, Any]] = []

    for sk in _sorted_registry_storage_keys(reg):
        row = reg.get(sk)
        if not isinstance(row, dict):
            continue
        lid_before = _derive_lead_id(normalize_lead(dict(row)))
        codes, esc_pair = _reconcile_lead_stale_and_threat_escalation_inplace(row, reg, current_turn)
        if "staled" in codes:
            staled.append(lid_before)
        if esc_pair is not None:
            f, to = esc_pair
            escalated.append({"lead_id": lid_before, "from": f, "to": to})

    unlocked = _apply_unlocks_from_resolved_sources(reg, current_turn)
    obsoleted = _apply_supersession_retirement(reg, current_turn)

    return {
        "current_turn": current_turn,
        "staled": staled,
        "escalated": escalated,
        "unlocked": unlocked,
        "obsoleted": obsoleted,
    }


# --- Engine-owned authoritative lead signal (normalized inputs; wraps registry + create/upsert) ---

ENGINE_PRESENTATION_LEVELS: tuple[str, ...] = ("implicit", "explicit", "actionable")


class EngineLeadSignalResult(TypedDict):
    status: Literal["created", "updated", "unchanged"]
    lead_id: str
    promotion_applied: bool
    changed_fields: List[str]
    compat_pending_lead_needed: bool


def _normalize_engine_presentation(value: Any, *, default: str = "implicit") -> str:
    raw = _as_str(value).lower()
    if raw in ENGINE_PRESENTATION_LEVELS:
        return raw
    return default


def _engine_presentation_rank(level: str) -> int:
    return ENGINE_PRESENTATION_LEVELS.index(_normalize_engine_presentation(level))


def _normalize_engine_source_kind(value: Any) -> str:
    raw = _as_str(value).lower()
    aliases: Dict[str, str] = {
        "explicit_clue": "clue_explicit",
        "clue": "clue_explicit",
        "discovery": "clue_explicit",
        "clue_discovery": "clue_explicit",
        "inference": "clue_inference",
        "inferred": "clue_inference",
        "clue_infer": "clue_inference",
        "social_disclosure": "social",
    }
    if raw in aliases:
        return aliases[raw]
    if raw in ("clue_explicit", "clue_inference", "social"):
        return raw
    return "other"


def _engine_signal_floors(source_kind: Any, presentation_level: Any) -> tuple[str, str]:
    """Return ``(lifecycle_floor, confidence_floor)`` implied by this signal (before optional user confidence)."""
    sk = _normalize_engine_source_kind(source_kind)
    pr = _normalize_engine_presentation(
        presentation_level if presentation_level is not None else "implicit",
        default="implicit",
    )
    rank = _engine_presentation_rank(pr)

    if sk == "clue_inference":
        return LeadLifecycle.HINTED.value, LeadConfidence.RUMOR.value
    if sk == "social":
        return LeadLifecycle.DISCOVERED.value, LeadConfidence.PLAUSIBLE.value
    if sk == "clue_explicit":
        if rank >= _engine_presentation_rank("explicit"):
            return LeadLifecycle.DISCOVERED.value, LeadConfidence.PLAUSIBLE.value
        return LeadLifecycle.HINTED.value, LeadConfidence.RUMOR.value
    return LeadLifecycle.HINTED.value, LeadConfidence.RUMOR.value


def _merge_ordered_unique_ids(*parts: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for seq in parts:
        if seq is None:
            continue
        for item in seq:
            nid = _normalize_optional_id(item)
            if nid is None or nid in seen:
                continue
            seen.add(nid)
            out.append(nid)
    return out


def _merge_discovery_source(existing: Any, incoming: Any) -> str:
    e = _as_str(existing)
    i = _as_str(incoming)
    if not i:
        return e
    if not e:
        return i
    if i in e:
        return e
    return f"{e}; {i}"


def _metadata_merge_engine(existing: Mapping[str, Any], incoming: Mapping[str, Any]) -> Dict[str, Any]:
    base = _normalize_metadata(existing)
    out = dict(base)
    for k, v in incoming.items():
        out[str(k)] = v
    return out


def _confidence_bump_one(confidence: Any) -> str:
    s = _coerce_confidence_str(confidence)
    if s is None:
        return LeadConfidence.RUMOR.value
    r = _confidence_rank(s)
    if r is None:
        return LeadConfidence.RUMOR.value
    if r >= len(_CONFIDENCE_ORDERED_VALUES) - 1:
        return _CONFIDENCE_ORDERED_VALUES[-1]
    return _CONFIDENCE_ORDERED_VALUES[r + 1]


def _max_lifecycle(a: Any, b: Any) -> str:
    ra = _lifecycle_rank(a)
    rb = _lifecycle_rank(b)
    if ra is None and rb is None:
        return LeadLifecycle.HINTED.value
    if ra is None:
        return _coerce_lifecycle_str(b) or LeadLifecycle.HINTED.value
    if rb is None:
        return _coerce_lifecycle_str(a) or LeadLifecycle.HINTED.value
    return _LIFECYCLE_ORDERED_VALUES[max(ra, rb)]


def _max_confidence(a: Any, b: Any) -> str:
    ra = _confidence_rank(a)
    rb = _confidence_rank(b)
    if ra is None and rb is None:
        return LeadConfidence.RUMOR.value
    if ra is None:
        return _coerce_confidence_str(b) or LeadConfidence.RUMOR.value
    if rb is None:
        return _coerce_confidence_str(a) or LeadConfidence.RUMOR.value
    return _CONFIDENCE_ORDERED_VALUES[max(ra, rb)]


def _lead_row_effective_field_diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[str]:
    """Stable field names that differ between two normalized snapshots (core + merged engine fields)."""
    keys = (
        "title",
        "summary",
        "type",
        "lifecycle",
        "status",
        "confidence",
        "discovery_source",
        "next_step",
        "related_clue_ids",
        "related_npc_ids",
        "related_location_ids",
        "related_faction_ids",
        "related_scene_ids",
        "tags",
        "evidence_clue_ids",
        "metadata",
        "first_discovered_turn",
        "last_updated_turn",
        "last_touched_turn",
        "committed_at_turn",
        "commitment_source",
        "commitment_strength",
    )
    changed: List[str] = []
    for k in keys:
        if before.get(k) != after.get(k):
            changed.append(k)
    return changed


def apply_engine_lead_signal(
    session: MutableMapping[str, Any],
    *,
    lead_id: Any,
    title: Any = "",
    summary: Any = "",
    lead_type: Any = LeadType.RUMOR.value,
    source_kind: Any = "other",
    source_scene_id: Any = None,
    source_npc_id: Any = None,
    target_scene_id: Any = None,
    target_npc_id: Any = None,
    rumor_text: Any = None,
    trigger_clue_id: Any = None,
    presentation_level: Any = None,
    confidence: Any = None,
    metadata: Mapping[str, Any] | None = None,
    tags: Iterable[Any] | None = None,
    turn: Any = None,
) -> EngineLeadSignalResult:
    """Apply one engine-originated lead write: monotonic lifecycle/confidence, merged lists, registry upsert.

    Uses :func:`ensure_lead_registry`, :func:`get_lead`, :func:`create_lead`, and :func:`upsert_lead` only
    (no parallel registry). Weaker signals never downgrade an existing lead; identical replays are unchanged.
    """
    ensure_lead_registry(session)

    title_clean = _as_str(title)
    sid = _normalize_optional_id(lead_id) or slugify(title_clean or "lead")
    if not sid:
        sid = "lead"

    lc_floor, cf_floor = _engine_signal_floors(source_kind, presentation_level)
    cf_user = _coerce_confidence_str(confidence)
    if cf_user is not None:
        cf_floor = _max_confidence(cf_floor, cf_user)

    scene_additions = _merge_ordered_unique_ids(
        [source_scene_id] if source_scene_id is not None else [],
        [target_scene_id] if target_scene_id is not None else [],
    )
    npc_additions = _merge_ordered_unique_ids(
        [source_npc_id] if source_npc_id is not None else [],
        [target_npc_id] if target_npc_id is not None else [],
    )
    trigger_norm = _normalize_optional_id(trigger_clue_id)
    evidence_additions: List[str] = [trigger_norm] if trigger_norm else []

    tag_additions = _normalize_id_list(tags) if tags is not None else []

    meta_incoming: Dict[str, Any] = dict(metadata) if isinstance(metadata, Mapping) else {}
    rumor_s = _as_str(rumor_text)
    if rumor_s:
        meta_incoming = {**meta_incoming, "rumor_text": rumor_s}

    sk_label = _normalize_engine_source_kind(source_kind)
    compat_pending = _normalize_optional_id(target_scene_id) is not None

    existing = get_lead(session, sid)
    created = existing is None

    if created:
        merged_scenes = _merge_ordered_unique_ids([], scene_additions)
        merged_npcs = _merge_ordered_unique_ids([], npc_additions)
        merged_evidence = _merge_ordered_unique_ids([], evidence_additions)
        merged_tags = _merge_ordered_unique_ids(tag_additions, [])

        row = create_lead(
            title=title_clean or sid,
            summary=_as_str(summary),
            id=sid,
            type=lead_type,
            lifecycle=lc_floor,
            confidence=cf_floor,
            discovery_source=sk_label,
            related_scene_ids=merged_scenes,
            related_npc_ids=merged_npcs,
            evidence_clue_ids=merged_evidence,
            tags=merged_tags,
            metadata=meta_incoming,
        )
        row["type"] = _normalize_type(row.get("type"))
        t = _as_optional_int(turn)
        if t is not None:
            row["first_discovered_turn"] = t
            row["last_updated_turn"] = t
            row["last_touched_turn"] = t

        blank = normalize_lead({"id": sid})
        changed_fields = _lead_row_effective_field_diff(blank, row)
        promotion_applied = True
        _ensure_invariants_after_mutation(row)
        upsert_lead(session, row)
        return {
            "status": "created",
            "lead_id": sid,
            "promotion_applied": promotion_applied,
            "changed_fields": changed_fields,
            "compat_pending_lead_needed": compat_pending,
        }

    before_snap = normalize_lead(copy.deepcopy(existing))

    prev_evidence = _normalize_id_list(before_snap.get("evidence_clue_ids"))
    evidence_grew = False
    if trigger_norm and trigger_norm not in set(prev_evidence):
        evidence_grew = True

    merged_scenes = _merge_ordered_unique_ids(_normalize_id_list(before_snap.get("related_scene_ids")), scene_additions)
    merged_npcs = _merge_ordered_unique_ids(
        [_as_str(x) for x in (before_snap.get("related_npc_ids") or []) if _as_str(x)],
        npc_additions,
    )

    merged_evidence = _merge_ordered_unique_ids(prev_evidence, evidence_additions)
    merged_tags = _merge_ordered_unique_ids(_normalize_id_list(before_snap.get("tags")), tag_additions)

    prev_lc = before_snap.get("lifecycle")
    prev_cf = before_snap.get("confidence")
    new_lc = _max_lifecycle(prev_lc, lc_floor)
    new_cf = _max_confidence(prev_cf, cf_floor)
    if evidence_grew:
        new_cf = _max_confidence(new_cf, _confidence_bump_one(prev_cf))

    after_row = normalize_lead(copy.deepcopy(before_snap))
    if title_clean:
        after_row["title"] = title_clean
    summ = _as_str(summary)
    if summ:
        after_row["summary"] = summ
    if _as_str(lead_type):
        after_row["type"] = _normalize_type(lead_type)

    after_row["lifecycle"] = new_lc
    after_row["confidence"] = new_cf
    after_row["discovery_source"] = _merge_discovery_source(before_snap.get("discovery_source"), sk_label)
    after_row["related_scene_ids"] = merged_scenes
    after_row["related_npc_ids"] = merged_npcs
    after_row["evidence_clue_ids"] = merged_evidence
    after_row["tags"] = merged_tags
    after_row["metadata"] = _metadata_merge_engine(before_snap.get("metadata") or {}, meta_incoming)

    changed_fields = _lead_row_effective_field_diff(before_snap, after_row)
    substantive = [f for f in changed_fields if f not in ("last_updated_turn", "last_touched_turn")]
    promotion_applied = (_lifecycle_rank(new_lc) or 0) > (_lifecycle_rank(prev_lc) or 0) or (
        _confidence_rank(new_cf) or 0
    ) > (_confidence_rank(prev_cf) or 0)

    if not substantive:
        return {
            "status": "unchanged",
            "lead_id": sid,
            "promotion_applied": False,
            "changed_fields": [],
            "compat_pending_lead_needed": compat_pending,
        }

    t = _as_optional_int(turn)
    if t is not None:
        after_row["last_updated_turn"] = t
        after_row["last_touched_turn"] = t

    changed_fields = _lead_row_effective_field_diff(before_snap, after_row)

    _ensure_invariants_after_mutation(after_row)
    upsert_lead(session, after_row)
    return {
        "status": "updated",
        "lead_id": sid,
        "promotion_applied": promotion_applied,
        "changed_fields": changed_fields,
        "compat_pending_lead_needed": compat_pending,
    }
