"""Helpers for picking the per-turn compact debug trace among trailing ``state_mutation`` rows."""
from __future__ import annotations

from typing import Any, Dict, List


def latest_compact_debug_trace_entry(traces: Any) -> Dict[str, Any]:
    """Return the newest trace entry that carries ``turn_trace`` / routing fields, not a late ``state_mutation``-only row."""
    dt: List[Any] = traces if isinstance(traces, list) else []
    for entry in reversed(dt):
        if isinstance(entry, dict) and entry.get("turn_trace") is not None:
            return entry
    for entry in reversed(dt):
        if isinstance(entry, dict) and entry.get("canonical_entry_path") is not None:
            return entry
    for entry in reversed(dt):
        if isinstance(entry, dict) and entry.get("kind") != "state_mutation":
            return entry
    return dt[-1] if dt and isinstance(dt[-1], dict) else {}
