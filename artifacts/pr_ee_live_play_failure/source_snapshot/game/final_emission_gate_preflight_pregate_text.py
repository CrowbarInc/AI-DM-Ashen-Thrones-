"""Pre-gate text normalization and tag-list construction for gate entry/preflight (Cycle BN9).

Read-only setup for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact normalized text and tag-list values; does not mutate ``out``.
"""
from __future__ import annotations

from typing import Any, Dict, List, NamedTuple

from game.final_emission_text_formatting import _normalize_text


class GatePreflightPregateText(NamedTuple):
    """Normalized pre-gate player text and string tag list."""

    pre_gate_text: str
    tag_list: List[str]


def resolve_gate_preflight_pregate_text(out: Dict[str, Any]) -> GatePreflightPregateText:
    """Normalize ``player_facing_text`` and build the string tag list from ``out``."""
    pre_gate_text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    return GatePreflightPregateText(pre_gate_text=pre_gate_text, tag_list=tag_list)
