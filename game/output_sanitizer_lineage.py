"""Sanitizer lineage construction and producer attribution.

This module owns sanitizer lineage construction and producer attribution. It does
**not** modify player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict

from game.attribution_read_views import (
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
)
from game.final_emission_meta import (
    PRODUCER_REPAIR_KIND_FIELD,
    PRODUCER_REPAIR_KIND_SANITIZER_EMPTY_OUTPUT,
)
from game.ownership_projection_views import (
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    normalize_sanitizer_trace_owner_to_lineage_owner,
)

SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE = "legacy_sentence_rewrite"


def _log_sanitizer_event(context: Dict[str, Any], event: str, sentence: str) -> None:
    if not isinstance(context, dict):
        return
    debug_log = context.setdefault("sanitizer_debug", [])
    if isinstance(debug_log, list):
        debug_log.append({"event": event, "sentence": sentence[:240]})
    _record_sanitizer_lineage_event(context, event)


def _ensure_sanitizer_lineage_trace(context: Dict[str, Any], *, mode: str | None) -> Dict[str, Any] | None:
    if not isinstance(context, dict):
        return None
    trace = context.setdefault("sanitizer_trace", {})
    if not isinstance(trace, dict):
        return None
    normalized_mode = str(mode or "").strip().lower() or "strip_only"
    trace["sanitizer_boundary_mode"] = normalized_mode
    trace["sanitizer_lineage_mode"] = normalized_mode
    trace["sanitizer_lineage_legacy_rewrite_active"] = normalized_mode == SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE
    trace.setdefault("sanitizer_lineage_changed_count", 0)
    trace.setdefault("sanitizer_lineage_dropped_count", 0)
    trace.setdefault("sanitizer_lineage_empty_fallback_used", False)
    return trace


def _record_sanitizer_lineage_event(context: Dict[str, Any], event: str) -> None:
    trace = _ensure_sanitizer_lineage_trace(
        context,
        mode=str(context.get("sanitizer_boundary_mode") or "").strip().lower() or "strip_only",
    )
    if not isinstance(trace, dict):
        return
    event_s = str(event or "").strip().lower()
    if any(token in event_s for token in ("dropped", "drop", "rewritten", "rewrite", "strip")):
        trace["sanitizer_lineage_changed_count"] = int(trace.get("sanitizer_lineage_changed_count") or 0) + 1
    if "dropped" in event_s or "drop" in event_s:
        trace["sanitizer_lineage_dropped_count"] = int(trace.get("sanitizer_lineage_dropped_count") or 0) + 1


def _stamp_sanitizer_producer_attribution(
    context: Dict[str, Any],
    *,
    repair_kind: str,
    owner_bucket: str | None = None,
) -> None:
    trace = context.setdefault("sanitizer_trace", {})
    if not isinstance(trace, dict):
        return
    kind = str(repair_kind or "").strip()
    if kind:
        trace[PRODUCER_REPAIR_KIND_FIELD] = kind
    bucket = str(owner_bucket or "").strip()
    if bucket:
        trace["sealed_fallback_owner_bucket"] = bucket


def _mark_sanitizer_empty_fallback(
    context: Dict[str, Any],
    *,
    used: bool,
    source: str | None = None,
    owner: str = SANITIZER_TRACE_SELECTION_OWNER_SHORT,
) -> None:
    trace = context.setdefault("sanitizer_trace", {})
    if not isinstance(trace, dict):
        return
    trace["sanitizer_empty_fallback_used"] = bool(used)
    trace["sanitizer_empty_fallback_source"] = source
    trace["sanitizer_empty_fallback_owner"] = normalize_sanitizer_trace_owner_to_lineage_owner(
        owner,
        default=SANITIZER_FALLBACK_SELECTION_OWNER,
    )
    trace[SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD] = SANITIZER_TRACE_SELECTION_OWNER_SHORT
    trace["sanitizer_lineage_empty_fallback_used"] = bool(used)
    if used:
        _stamp_sanitizer_producer_attribution(
            context,
            repair_kind=PRODUCER_REPAIR_KIND_SANITIZER_EMPTY_OUTPUT,
            owner_bucket=SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
        )


def _mark_sanitizer_strict_social_fallback(
    context: Dict[str, Any],
    *,
    used: bool,
    source: str | None = None,
) -> None:
    trace = context.setdefault("sanitizer_trace", {})
    if not isinstance(trace, dict):
        return
    trace["sanitizer_strict_social_fallback_used"] = bool(used)
    trace["sanitizer_strict_social_selection_owner"] = normalize_sanitizer_trace_owner_to_lineage_owner(
        SANITIZER_TRACE_SELECTION_OWNER_SHORT,
        default=SANITIZER_FALLBACK_SELECTION_OWNER,
    )
    trace["sanitizer_strict_social_prose_owner"] = normalize_sanitizer_trace_owner_to_lineage_owner(
        SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
        default=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    )
    trace[SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD] = SANITIZER_TRACE_SELECTION_OWNER_SHORT
    trace[SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD] = SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT
    trace["sanitizer_strict_social_source"] = source
    if used:
        _stamp_sanitizer_producer_attribution(
            context,
            repair_kind=PRODUCER_REPAIR_KIND_SANITIZER_EMPTY_OUTPUT,
            owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
        )
