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
